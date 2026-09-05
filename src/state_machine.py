"""Declarative conversational state machine.

The whole dialogue lives in ROUTES: (role, state) -> handler function.
The webhook layer is stateless: every inbound message hydrates the session
(phone → chat_sessions row), dispatches through this table, and persists
the resulting session. No in-process memory is ever trusted.

Global pre-dispatch:
  * the language command ("language"/"idioma"/"भाषा") works from ANY state
    and returns to it afterwards;
  * STOP works from any prospect state: instant opt-out everywhere.
"""

from __future__ import annotations

from . import models as M
from .context import Ctx, parse_choice
from .db import Database
from .handlers import designer, prospect
from .i18n import I18n, resolve_language
from .whatsapp import WhatsAppClient

# ── The declarative route table ────────────────────────────────────
# (role, state) → handler(ctx) -> None  (handlers reply + persist state)
ROUTES = {
    # prospect loop
    (M.ROLE_PROSPECT, M.P_NEW): prospect.handle_new,
    (M.ROLE_PROSPECT, M.P_PICK_DESIGNER): prospect.handle_pick_designer,
    (M.ROLE_PROSPECT, M.P_PHOTO): prospect.handle_photo,
    (M.ROLE_PROSPECT, M.P_RETAKE): prospect.handle_photo,
    (M.ROLE_PROSPECT, M.P_WAITING): prospect.handle_waiting,
    (M.ROLE_PROSPECT, M.P_REVIEW): prospect.handle_review,
    (M.ROLE_PROSPECT, M.P_ORDER): prospect.handle_order,
    (M.ROLE_PROSPECT, M.P_TRACKING): prospect.handle_tracking,
    # designer loop
    (M.ROLE_DESIGNER, M.D_NEW): designer.handle_designer_new,
    (M.ROLE_DESIGNER, M.D_HOME): designer.handle_home,
    (M.ROLE_DESIGNER, M.D_CATALOG): designer.handle_catalog,
    (M.ROLE_DESIGNER, M.D_CAT_NAME): designer.handle_cat_name,
    (M.ROLE_DESIGNER, M.D_CAT_PRICE): designer.handle_cat_price,
    (M.ROLE_DESIGNER, M.D_CAT_SIZE): designer.handle_cat_size,
    (M.ROLE_DESIGNER, M.D_CAT_PHOTO): designer.handle_cat_photo,
    (M.ROLE_DESIGNER, M.D_CAT_REMOVE): designer.handle_cat_remove,
    (M.ROLE_DESIGNER, M.D_STUDIO): designer.handle_studio,
    (M.ROLE_DESIGNER, M.D_STUDIO_PRODUCT): designer.handle_studio_product,
    (M.ROLE_DESIGNER, M.D_STUDIO_PRESET): designer.handle_studio_preset,
    (M.ROLE_DESIGNER, M.D_STUDIO_ADJUST): designer.handle_studio_adjust,
    (M.ROLE_DESIGNER, M.D_ORDERS): designer.handle_orders,
    (M.ROLE_DESIGNER, M.D_ORDER_STATUS): designer.handle_order_status,
    (M.ROLE_DESIGNER, M.D_MARKETING): designer.handle_marketing,
    (M.ROLE_DESIGNER, M.D_CAMP_BODY): designer.handle_camp_body,
    (M.ROLE_DESIGNER, M.D_CAMP_CONFIRM): designer.handle_camp_confirm,
    # role not yet chosen → same entry as a fresh prospect
    (None, M.P_NEW): prospect.handle_new,
}


def _is_language_command(text: str | None) -> bool:
    return bool(text) and text.strip().lower() in M.LANGUAGE_COMMANDS


def _enter_language_select(ctx: Ctx) -> None:
    ctx.session["data"]["return_state"] = ctx.session["state"]
    ctx.session["data"]["return_data"] = dict(ctx.session["data"])
    ctx.reply("language_menu")
    ctx.set_state(M.P_LANGUAGE)


def _handle_language_select(ctx: Ctx) -> None:
    choice = parse_choice(ctx.text, 1, len(M.LANGUAGE_OPTIONS))
    if choice is None:
        ctx.reply("language_invalid")
        return
    lang = M.LANGUAGE_OPTIONS[choice - 1][1]
    ctx.db.set_user_language(ctx.phone, lang)
    if ctx.user:
        ctx.user["preferred_language"] = lang
    prospect = ctx.db.get_prospect(ctx.phone)
    if prospect:
        # keep the prospect row's language in sync for notifications
        prospect["preferred_language"] = lang
    ctx.session["lang"] = lang
    ctx.lang = lang
    ctx.reply("language_changed")
    # Return to wherever the chat was, now in the new language.
    data = ctx.session["data"]
    ret_state = data.pop("return_state", None)
    ret_data = data.pop("return_data", None) or {}
    ret_data.pop("return_state", None)
    ret_data.pop("return_data", None)
    if not ret_state:
        ctx.set_state(M.P_NEW)
        return
    ctx.set_state(ret_state, **ret_data)
    # Re-dispatch with no input: every state's invalid-input branch
    # politely re-renders its prompt — now in the new language.
    process_incoming(
        ctx.db, ctx.wa, ctx.i18n, ctx.media, ctx.store,
        ctx.phone, None, msg_type="text", default_lang=ctx.default_lang,
    )


def fresh_session(phone: str, default_lang: str) -> dict:
    return {"role": None, "state": M.P_NEW, "lang": default_lang, "data": {}}


def process_incoming(
    db: Database,
    wa: WhatsAppClient,
    i18n: I18n,
    media,
    store,
    phone: str,
    text: str | None,
    msg_type: str = "text",
    media_id: str | None = None,
    default_lang: str = "en",
) -> None:
    """Single entry point for every inbound WhatsApp message."""
    user = db.get_user(phone)
    session = db.get_session(phone)
    if session is None:
        session = fresh_session(phone, default_lang)
    lang = resolve_language(user, session, default_lang)

    ctx = Ctx(
        db=db,
        wa=wa,
        i18n=i18n,
        phone=phone,
        user=user,
        session=session,
        text=text,
        msg_type=msg_type,
        media=media,
        store=store,
        media_id=media_id,
        lang=lang,
        default_lang=default_lang,
    )

    # Language switch works from any state (but not while selecting one).
    if session["state"] != M.P_LANGUAGE and _is_language_command(text):
        _enter_language_select(ctx)
        return
    if session["state"] == M.P_LANGUAGE:
        _handle_language_select(ctx)
        return

    role = session.get("role") or (user["system_role"] if user else None)

    # STOP works from any prospect state: leave every marketing list.
    if role == M.ROLE_PROSPECT and (text or "").strip().upper() == "STOP":
        db.set_prospect_opt(phone, "opted_out")
        ctx.reply("p_stop_done")
        return

    if role == M.ROLE_PROSPECT:
        db.touch_prospect_active(phone)

    handler = ROUTES.get((role, session["state"]))
    if handler is None:
        # Unknown/corrupt state → safe reset to a known hub.
        if role == M.ROLE_DESIGNER:
            ctx.set_state(M.D_HOME)
            designer.show_home(ctx)
        else:
            ctx.set_state(M.P_NEW)
            prospect.handle_new(ctx)
        return
    handler(ctx)

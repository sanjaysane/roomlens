"""Prospect loop: invite → photo capture → visualization review → order."""

from __future__ import annotations

from .. import models as M
from ..composite import assess_quality, extract_first_frame
from ..context import Ctx, parse_choice, parse_name
from ..display import designer_name, prospect_name
from ..pricing import (
    currency_for_locale,
    format_money,
    order_status_label,
    quote_lines_text,
)


def _designer_phone(ctx: Ctx, prospect: dict) -> str | None:
    designer = ctx.db.get_designer(prospect["designer_id"]) if prospect.get("designer_id") else None
    return designer["phone_number"] if designer else None


def _designer_name(ctx: Ctx, prospect: dict) -> str:
    designer = ctx.db.get_designer(prospect["designer_id"]) if prospect.get("designer_id") else None
    return designer_name(designer) or "our studio"


# ── P_NEW: welcome + role pick ─────────────────────────────────────
def handle_new(ctx: Ctx) -> None:
    choice = parse_choice(ctx.text, 1, 2)
    if choice is None:
        ctx.reply("p_welcome")
        return
    if choice == 1:
        from . import designer as D

        ctx.db.upsert_user(ctx.phone, M.ROLE_DESIGNER, ctx.lang)
        ctx.session["role"] = M.ROLE_DESIGNER
        ctx.set_state(M.D_NEW)
        D.ask_studio_name(ctx)
        return
    # choice == 2 → prospect: pick a designer (all single-digit)
    ctx.db.upsert_user(ctx.phone, M.ROLE_PROSPECT, ctx.lang)
    designers = ctx.db.list_designers()
    if not designers:
        ctx.reply("p_no_designers")
        return
    lines = [
        f"{i + 1}. {d['display_name']}" for i, d in enumerate(designers)
    ]
    ctx.session["role"] = M.ROLE_PROSPECT
    ctx.set_state(
        M.P_PICK_DESIGNER,
        designers=[d["phone_number"] for d in designers],
    )
    ctx.reply("p_pick_designer", designers="\n".join(lines))


def handle_pick_designer(ctx: Ctx) -> None:
    phones = ctx.session["data"].get("designers", [])
    choice = parse_choice(ctx.text, 1, len(phones))
    if choice is None or not phones:
        ctx.reply("p_invalid_choice")
        ctx.reply("p_pick_designer_again")
        return
    designer_phone = phones[choice - 1]
    ctx.db.ensure_prospect(ctx.phone, designer_phone, ctx.lang)
    ctx.db.set_prospect_opt(ctx.phone, "pending")
    designer = ctx.db.get_designer_by_phone(designer_phone)
    ctx.set_state(M.P_NAME, designer_id=(designer or {}).get("id"))
    ctx.reply("p_name_ask")


# ── P_NAME: one-time nickname capture (0 = skip) ────────────────────
def handle_name(ctx: Ctx) -> None:
    # A photo sent at the name prompt = implicit skip: the prospect just
    # wants to send their room picture. Accept it as if at P_PHOTO so the
    # name question never blocks the core flow.
    if ctx.msg_type in ("image", "video"):
        handle_photo(ctx)
        return
    if ctx.text is None:
        # Re-dispatch after a mid-chat language switch: just re-render
        # the name prompt, now in the new language.
        ctx.reply("p_name_ask")
        return
    if (ctx.text or "").strip() == "0":
        _ask_for_photo(ctx)
        return
    name = parse_name(ctx.text)
    if name is None:
        ctx.reply("p_name_invalid")
        return
    ctx.db.set_prospect_nickname(ctx.phone, name)
    _ask_for_photo(ctx)


def _ask_for_photo(ctx: Ctx) -> None:
    designer_id = ctx.session["data"].get("designer_id")
    designer = ctx.db.get_designer(designer_id) if designer_id else None
    ctx.set_state(M.P_PHOTO, designer_id=designer_id)
    ctx.reply("p_photo_ask", designer=designer_name(designer) or "our studio")


# ── P_PHOTO: guided room-photo capture ─────────────────────────────
_RETAKE_KEYS = {
    "dark": "p_retake_dark",
    "blurry": "p_retake_blurry",
    "small": "p_retake_small",
    "unreadable": "p_retake_unreadable",
}


def handle_photo(ctx: Ctx) -> None:
    if ctx.msg_type not in ("image", "video") or not ctx.media_id:
        ctx.reply("p_photo_need_image")
        return
    try:
        raw = ctx.media.download(ctx.media_id)
    except Exception:  # noqa: BLE001 - any download failure = retake ask
        ctx.reply("p_retake_unreadable")
        return

    kind = "video" if ctx.msg_type == "video" else "photo"
    if kind == "video":
        # Short clips welcome: composite onto the first frame.
        # If we can't decode it, say so plainly and ask for a photo.
        frame = extract_first_frame(raw)
        if frame is None:
            ctx.reply("p_video_need_photo")
            return
        raw = frame

    quality = assess_quality(raw)
    if not quality["ok"]:
        # Counterfactual honored: a bad photo NEVER gets an overlay.
        # Polite, specific retake guidance instead of a misleading render.
        for issue in quality["issues"]:
            ctx.reply(_RETAKE_KEYS.get(issue, "p_retake_unreadable"))
        retakes = ctx.session["data"].get("retakes", 0) + 1
        ctx.set_state(ctx.session["state"], retakes=retakes)
        return

    ref = ctx.store.save(
        "rooms", f"room-{ctx.phone.strip('+')}.jpg", raw
    )
    prospect = ctx.db.ensure_prospect(ctx.phone, language=ctx.lang)
    designer_id = ctx.session["data"].get("designer_id") or prospect.get("designer_id")
    media = ctx.db.add_room_media(
        prospect["id"], designer_id, ref, kind,
        quality["width"], quality["height"], quality,
    )
    designer_phone = _designer_phone(ctx, {**prospect, "designer_id": designer_id})
    if designer_phone:
        d_lang = (ctx.db.get_user(designer_phone) or {}).get(
            "preferred_language", "en"
        )
        prospect = ctx.db.get_prospect(ctx.phone) or prospect
        ctx.send_to(
            designer_phone, "d_new_photo", d_lang,
            prospect=prospect_name(prospect) or ctx.phone,
        )
    ctx.set_state(M.P_WAITING, media_id=media["id"], optin_asked=True)
    ctx.reply("p_photo_ok", designer=_designer_name(ctx, {**prospect, "designer_id": designer_id}))
    ctx.reply("p_optin_ask")


def handle_waiting(ctx: Ctx) -> None:
    data = ctx.session["data"]
    if data.get("optin_asked"):
        choice = parse_choice(ctx.text, 1, 2)
        if choice == 1:
            ctx.db.set_prospect_opt(ctx.phone, "opted_in")
            ctx.set_state(M.P_WAITING, optin_asked=False)
            ctx.reply("p_optin_yes")
            return
        if choice == 2:
            ctx.set_state(M.P_WAITING, optin_asked=False)
            ctx.reply("p_optin_no")
            return
        ctx.reply("p_optin_ask")  # invalid → ask again, don't drop the question
        return
    ctx.reply("p_waiting")


# ── P_REVIEW: visualization received ───────────────────────────────
def _notify_designer(ctx: Ctx, key: str) -> None:
    prospect = ctx.db.get_prospect(ctx.phone) or {}
    phone = _designer_phone(ctx, prospect)
    if phone:
        d_lang = (ctx.db.get_user(phone) or {}).get("preferred_language", "en")
        ctx.send_to(
            phone, key, d_lang, prospect=prospect_name(prospect) or ctx.phone
        )


def handle_review(ctx: Ctx) -> None:
    choice = parse_choice(ctx.text, 1, 4)
    if choice is None:
        ctx.reply("p_review_options")
        return
    data = ctx.session["data"]
    if choice == 1:
        quote = ctx.db.get_quote_by_visualization(data.get("viz_id", -1))
        if not quote:
            ctx.reply("p_no_quote")
            return
        lines = quote_lines_text(
            {
                "line_items": quote["line_items"],
                "delivery_cents": quote["delivery_cents"],
                "total_cents": quote["total_cents"],
                "currency": quote["currency"],
            },
            lang=ctx.lang,
        )
        ctx.set_state(M.P_ORDER, quote_id=quote["id"], viz_id=data.get("viz_id"))
        ctx.reply("p_order_confirm", lines="\n".join(lines))
        return
    if choice == 2:
        _notify_designer(ctx, "d_change_placement")
    elif choice == 3:
        _notify_designer(ctx, "d_change_product")
    else:
        _notify_designer(ctx, "d_prospect_wants_talk")
    ctx.set_state(M.P_WAITING, optin_asked=False)
    ctx.reply("p_change_noted")


# ── P_ORDER: confirm → create order ────────────────────────────────
def handle_order(ctx: Ctx) -> None:
    choice = parse_choice(ctx.text, 1, 2)
    if choice is None:
        ctx.reply("p_order_confirm_again")
        return
    if choice == 2:
        ctx.set_state(M.P_PHOTO)
        ctx.reply("p_order_cancelled")
        return
    quote = None
    # quote lookup is via the visualization stored in session
    prospect = ctx.db.get_prospect(ctx.phone) or {}
    designer_id = prospect.get("designer_id")
    # find the quote through the viz stored in session
    viz_id = ctx.session["data"].get("viz_id")
    if viz_id:
        quote = ctx.db.get_quote_by_visualization(viz_id)
    if not quote or not designer_id:
        ctx.reply("p_no_quote")
        return
    order = ctx.db.create_order(
        ctx.phone, designer_id, quote["id"],
        quote["total_cents"], quote["currency"],
    )
    viz = ctx.db.get_visualization(viz_id)
    if viz:
        ctx.db.update_visualization(viz_id, status="ordered")
    designer_phone = _designer_phone(ctx, prospect)
    if designer_phone:
        d_lang = (ctx.db.get_user(designer_phone) or {}).get(
            "preferred_language", "en"
        )
        ctx.send_to(
            designer_phone, "d_new_order", d_lang,
            order_id=order["id"],
            total=format_money(
                quote["total_cents"], currency_for_locale(ctx.lang)
            ),
        )
    ctx.set_state(M.P_TRACKING, order_id=order["id"])
    ctx.reply("p_order_placed", order_id=order["id"])


# ── P_TRACKING ─────────────────────────────────────────────────────
def handle_tracking(ctx: Ctx) -> None:
    orders = ctx.db.list_orders_for_prospect(ctx.phone)
    open_orders = [o for o in orders if o["status"] != "delivered"
                   and o["status"] != "cancelled"]
    if not open_orders:
        ctx.reply("p_no_open_orders")
        return
    lines = [
        f"#{o['id']}: {order_status_label(o['status'], ctx.lang)} — "
        f"{format_money(o['total_cents'], currency_for_locale(ctx.lang))}"
        for o in open_orders
    ]
    ctx.reply("p_tracking", orders="\n".join(lines))

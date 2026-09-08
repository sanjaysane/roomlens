"""Designer loop: catalog → compositing studio → orders → marketing."""

from __future__ import annotations

from datetime import datetime, timezone

from .. import marketing as mk
from .. import models as M
from ..composite import make_placeholder_cutout, render_visualization
from ..context import Ctx, parse_choice, parse_name, parse_price
from ..display import display_name
from ..pricing import (
    build_quote,
    currency_for_locale,
    format_money,
    order_status_label,
)


def _designer(ctx: Ctx) -> dict:
    d = ctx.db.get_designer_by_phone(ctx.phone)
    if d is None:
        d = ctx.db.ensure_designer(ctx.phone, ctx.phone)
    return d


# ── D_NEW: one-time studio setup ───────────────────────────────────
def ask_studio_name(ctx: Ctx) -> None:
    ctx.reply("d_ask_studio_name")


def handle_designer_new(ctx: Ctx) -> None:
    name = parse_name(ctx.text)
    if name is None:
        ctx.reply("d_studio_name_invalid")
        return
    ctx.db.ensure_designer(ctx.phone, name)
    ctx.set_state(M.D_HOME)
    show_home(ctx)


# ── D_HOME ─────────────────────────────────────────────────────────
def show_home(ctx: Ctx) -> None:
    ctx.reply("d_home")


def handle_home(ctx: Ctx) -> None:
    choice = parse_choice(ctx.text, 1, 4)
    if choice is None:
        ctx.reply("d_home_invalid")
        show_home(ctx)
        return
    if choice == 1:
        ctx.set_state(M.D_CATALOG)
        show_catalog(ctx)
    elif choice == 2:
        ctx.set_state(M.D_STUDIO)
        show_studio(ctx)
    elif choice == 3:
        ctx.set_state(M.D_ORDERS)
        show_orders(ctx)
    else:
        ctx.set_state(M.D_MARKETING)
        show_marketing(ctx)


# ── Catalog ────────────────────────────────────────────────────────
def _product_lines(products: list[dict], lang: str = "en") -> str:
    return "\n".join(
        f"{i + 1}. {p['name']} — "
        f"{format_money(p['price_cents'], currency_for_locale(lang))}"
        for i, p in enumerate(products)
    )


def show_catalog(ctx: Ctx) -> None:
    products = ctx.db.list_products(_designer(ctx)["id"])
    listing = _product_lines(products, ctx.lang) if products else ctx.i18n.t(
        ctx.lang, "d_catalog_empty"
    )
    ctx.reply("d_catalog", products=listing)


def handle_catalog(ctx: Ctx) -> None:
    choice = parse_choice(ctx.text, 0, 2)
    if choice is None:
        ctx.reply("d_catalog_invalid")
        show_catalog(ctx)
        return
    if choice == 0:
        ctx.set_state(M.D_HOME)
        show_home(ctx)
    elif choice == 1:
        ctx.set_state(M.D_CAT_NAME)
        ctx.reply("d_cat_name_ask")
    else:
        products = ctx.db.list_products(_designer(ctx)["id"])
        if not products:
            ctx.reply("d_catalog_empty")
            show_catalog(ctx)
            return
        ctx.set_state(
            M.D_CAT_REMOVE, products=[p["id"] for p in products]
        )
        ctx.reply("d_cat_remove_ask", products=_product_lines(products, ctx.lang))


def handle_cat_name(ctx: Ctx) -> None:
    name = parse_name(ctx.text)
    if name is None:
        ctx.reply("d_cat_name_invalid")
        return
    ctx.set_state(M.D_CAT_PRICE, name=name)
    ctx.reply("d_cat_price_ask", name=name)


def handle_cat_price(ctx: Ctx) -> None:
    price = parse_price(ctx.text)
    if price is None:
        ctx.reply("d_cat_price_invalid")
        return
    ctx.set_state(M.D_CAT_SIZE, price=price)
    ctx.reply("d_cat_size_ask")


def handle_cat_size(ctx: Ctx) -> None:
    choice = parse_choice(ctx.text, 1, 3)
    if choice is None:
        ctx.reply("d_cat_size_invalid")
        return
    size_class = (M.SIZE_FLOOR, M.SIZE_WALL, M.SIZE_TABLETOP)[choice - 1]
    ctx.set_state(M.D_CAT_PHOTO, size_class=size_class)
    ctx.reply("d_cat_photo_ask")


def handle_cat_photo(ctx: Ctx) -> None:
    data = ctx.session["data"]
    cutout_ref = ""
    if ctx.msg_type == "image" and ctx.media_id:
        try:
            raw = ctx.media.download(ctx.media_id)
        except Exception:  # noqa: BLE001 - any download failure = ask again
            ctx.reply("d_cat_photo_failed")
            return
        cutout_ref = ctx.store.save(
            "cutouts", f"cutout-{ctx.phone.strip('+')}.png", raw
        )
    elif (ctx.text or "").strip() != "0":
        ctx.reply("d_cat_photo_ask_again")
        return
    designer = _designer(ctx)
    size_class = data.get("size_class", M.SIZE_FLOOR)
    price_cents = round(float(data.get("price") or 0) * 100)
    # price was validated at D_CAT_PRICE; data carries the raw text
    product = ctx.db.add_product(
        designer["id"],
        name=data.get("name", "Untitled"),
        description="",
        price_cents=price_cents,
        currency=currency_for_locale(ctx.lang),
        size_class=size_class,
        default_preset=M.SIZE_CLASS_DEFAULT_PRESET[size_class],
        cutout_ref=cutout_ref,
    )
    ctx.set_state(M.D_CATALOG)
    ctx.reply(
        "d_product_added", name=product["name"],
        price=format_money(
            product["price_cents"], currency_for_locale(ctx.lang)
        ),
    )
    show_catalog(ctx)


def handle_cat_remove(ctx: Ctx) -> None:
    ids = ctx.session["data"].get("products", [])
    choice = parse_choice(ctx.text, 0, len(ids))
    if choice is None:
        ctx.reply("d_cat_remove_invalid")
        return
    if choice == 0:
        ctx.set_state(M.D_CATALOG)
        show_catalog(ctx)
        return
    ctx.db.set_product_active(ids[choice - 1], False)
    ctx.set_state(M.D_CATALOG)
    ctx.reply("d_product_removed")
    show_catalog(ctx)


# ── Studio: composite a visualization ──────────────────────────────
def _prospect_lang(ctx: Ctx, media_id: int | None = None) -> str:
    """Language of the prospect who sent the room photo (for rendered
    labels and captions — money formatting follows this locale)."""
    media_id = media_id or ctx.session["data"].get("media_id")
    if not media_id:
        return ctx.lang
    media = ctx.db.get_room_media(media_id) or {}
    prospect = ctx.db.get_prospect(media.get("prospect_phone", "")) or {}
    return prospect.get("preferred_language", "en") or "en"


def show_studio(ctx: Ctx) -> None:
    pending = ctx.db.list_pending_media(_designer(ctx)["id"])
    if not pending:
        ctx.reply("d_studio_empty")
        ctx.set_state(M.D_HOME)
        show_home(ctx)
        return
    lines = [
        f"{i + 1}. 📸 {display_name({'nickname': m.get('prospect_nickname'), 'phone_number': m.get('prospect_phone')})}"
        for i, m in enumerate(pending)
    ]
    ctx.set_state(M.D_STUDIO, media=[m["id"] for m in pending])
    ctx.reply("d_studio_list", rooms="\n".join(lines))


def handle_studio(ctx: Ctx) -> None:
    ids = ctx.session["data"].get("media", [])
    choice = parse_choice(ctx.text, 0, len(ids))
    if choice is None or not ids:
        ctx.reply("d_studio_invalid")
        return
    if choice == 0:
        ctx.set_state(M.D_HOME)
        show_home(ctx)
        return
    media = ctx.db.get_room_media(ids[choice - 1])
    products = ctx.db.list_products(_designer(ctx)["id"])
    if not products:
        ctx.reply("d_studio_no_products")
        ctx.set_state(M.D_CATALOG)
        show_catalog(ctx)
        return
    ctx.set_state(
        M.D_STUDIO_PRODUCT,
        media_id=media["id"],
        products=[p["id"] for p in products],
    )
    ctx.reply("d_studio_pick_product", products=_product_lines(products, ctx.lang))


def handle_studio_product(ctx: Ctx) -> None:
    ids = ctx.session["data"].get("products", [])
    choice = parse_choice(ctx.text, 1, len(ids))
    if choice is None or not ids:
        ctx.reply("d_studio_invalid")
        return
    product = ctx.db.get_product(ids[choice - 1])
    ctx.set_state(M.D_STUDIO_PRESET, product_id=product["id"])
    ctx.reply("d_studio_pick_preset", product=product["name"])


def _render_draft(
    ctx: Ctx, product: dict, preset: str, scale: float, lang: str | None = None
) -> bytes:
    data = ctx.session["data"]
    media = ctx.db.get_room_media(data["media_id"])
    room_bytes = ctx.store.load(media["storage_ref"])
    if product.get("cutout_ref"):
        cutout = ctx.store.load(product["cutout_ref"])
    else:
        # Dev fallback: procedural placeholder. Production deployments
        # use designer-uploaded RGBA cutouts (see docs/ARCHITECTURE.md).
        cutout = make_placeholder_cutout(product["name"])
    label = (
        f"{product['name']} — "
        f"{format_money(product['price_cents'], currency_for_locale(lang or ctx.lang))}"
    )
    return render_visualization(
        room_bytes,
        [{"cutout": cutout, "preset": preset, "scale": scale, "label": label}],
    )


def handle_studio_preset(ctx: Ctx) -> None:
    choice = parse_choice(ctx.text, 1, 4)
    if choice is None:
        ctx.reply("d_studio_preset_invalid")
        return
    preset = M.PLACEMENT_PRESETS[choice - 1]
    product = ctx.db.get_product(ctx.session["data"]["product_id"])
    rendered = _render_draft(
        ctx, product, preset, 1.0, lang=_prospect_lang(ctx)
    )
    ref = ctx.store.save("renders", f"viz-{product['id']}.jpg", rendered)
    viz = ctx.db.create_visualization(
        prospect_id=ctx.db.get_room_media(
            ctx.session["data"]["media_id"]
        )["prospect_id"],
        designer_id=_designer(ctx)["id"],
        room_media_id=ctx.session["data"]["media_id"],
        placements=[{"product_id": product["id"], "preset": preset, "scale": 1.0}],
    )
    ctx.db.update_visualization(viz["id"], rendered_ref=ref)
    ctx.set_state(
        M.D_STUDIO_ADJUST, viz_id=viz["id"], preset=preset, scale=1.0
    )
    ctx.send_image_to(ctx.phone, rendered, "")
    ctx.reply("d_studio_adjust")


def handle_studio_adjust(ctx: Ctx) -> None:
    choice = parse_choice(ctx.text, 1, 4)
    if choice is None:
        ctx.reply("d_studio_adjust_invalid")
        return
    data = ctx.session["data"]
    viz = ctx.db.get_visualization(data["viz_id"])
    product_id = viz["placements"][0]["product_id"]
    product = ctx.db.get_product(product_id)
    if choice in (1, 2):
        scale = round(data.get("scale", 1.0) * (1.25 if choice == 1 else 0.8), 2)
        scale = max(0.4, min(scale, 2.5))
        rendered = _render_draft(ctx, product, data["preset"], scale,
                                 lang=_prospect_lang(ctx))
        ref = ctx.store.save("renders", f"viz-{product['id']}.jpg", rendered)
        ctx.db.update_visualization(
            viz["id"],
            rendered_ref=ref,
            placements=[{
                "product_id": product["id"],
                "preset": data["preset"],
                "scale": scale,
            }],
        )
        ctx.set_state(M.D_STUDIO_ADJUST, scale=scale)
        ctx.send_image_to(ctx.phone, rendered, "")
        ctx.reply("d_studio_adjust")
        return
    if choice == 4:
        ctx.set_state(M.D_STUDIO)
        show_studio(ctx)
        return
    # choice == 3 → send to prospect with a quote
    quote_data = build_quote(
        [{
            "name": product["name"],
            "price_cents": product["price_cents"],
            "qty": 1,
        }],
        delivery_cents=0,
        currency=product["currency"],
    )
    ctx.db.create_quote(
        viz["id"], quote_data["line_items"], quote_data["subtotal_cents"],
        quote_data["delivery_cents"], quote_data["total_cents"],
        quote_data["currency"],
    )
    ctx.db.update_visualization(viz["id"], status="sent")
    ctx.db.mark_media_visualized(viz["room_media_id"])
    media = ctx.db.get_room_media(viz["room_media_id"])
    prospect_phone = (media or {}).get("prospect_phone")
    rendered = ctx.store.load(viz["rendered_ref"])
    p_lang = "en"
    if prospect_phone:
        p = ctx.db.get_prospect(prospect_phone)
        p_lang = (p or {}).get("preferred_language", "en")
        caption = ctx.i18n.t(
            p_lang, "p_viz_caption",
            product=product["name"],
            price=format_money(
                product["price_cents"], currency_for_locale(p_lang)
            ),
        )
        ctx.wa.send_image(prospect_phone, rendered, caption)
        ctx.set_state_for(
            prospect_phone, M.ROLE_PROSPECT, M.P_REVIEW, p_lang,
            viz_id=viz["id"],
        )
    ctx.set_state(M.D_HOME)
    ctx.reply("d_viz_sent")
    show_home(ctx)


# ── Orders ─────────────────────────────────────────────────────────
def show_orders(ctx: Ctx) -> None:
    orders = ctx.db.list_open_orders(_designer(ctx)["id"])
    if not orders:
        ctx.reply("d_orders_empty")
        ctx.set_state(M.D_HOME)
        show_home(ctx)
        return
    lines = [
        f"{i + 1}. #{o['id']} — "
        f"{format_money(o['total_cents'], currency_for_locale(ctx.lang))} — "
        f"{order_status_label(o['status'], ctx.lang)}"
        for i, o in enumerate(orders)
    ]
    ctx.set_state(M.D_ORDERS, orders=[o["id"] for o in orders])
    ctx.reply("d_orders_list", orders="\n".join(lines))


def handle_orders(ctx: Ctx) -> None:
    ids = ctx.db.list_open_orders(_designer(ctx)["id"])
    order_ids = [o["id"] for o in ids]
    choice = parse_choice(ctx.text, 0, len(order_ids))
    if choice is None or not order_ids:
        ctx.reply("d_orders_invalid")
        return
    if choice == 0:
        ctx.set_state(M.D_HOME)
        show_home(ctx)
        return
    ctx.set_state(M.D_ORDER_STATUS, order_id=order_ids[choice - 1])
    ctx.reply("d_order_status_ask")


def handle_order_status(ctx: Ctx) -> None:
    choice = parse_choice(ctx.text, 0, 3)
    if choice is None:
        ctx.reply("d_order_status_invalid")
        return
    if choice == 0:
        ctx.set_state(M.D_ORDERS)
        show_orders(ctx)
        return
    status = ("preparing", "out_for_delivery", "delivered")[choice - 1]
    order = ctx.db.update_order(ctx.session["data"]["order_id"], status=status)
    prospect_phone = order["prospect_phone"]
    p = ctx.db.get_prospect(prospect_phone) or {}
    p_lang = p.get("preferred_language", "en")
    ctx.send_to(
        prospect_phone, "p_tracking_update",
        p_lang,
        order_id=order["id"], status=order_status_label(status, p_lang),
    )
    ctx.set_state(M.D_ORDERS)
    ctx.reply("d_order_updated")
    show_orders(ctx)


# ── Marketing ──────────────────────────────────────────────────────
def show_marketing(ctx: Ctx) -> None:
    designer = _designer(ctx)
    opted_in = ctx.db.get_opted_in_prospects(designer["id"])
    ctx.set_state(M.D_MARKETING)
    ctx.reply("d_marketing", opted_in=len(opted_in))


def handle_marketing(ctx: Ctx) -> None:
    choice = parse_choice(ctx.text, 0, 4)
    if choice is None:
        ctx.reply("d_marketing_invalid")
        show_marketing(ctx)
        return
    if choice == 0:
        ctx.set_state(M.D_HOME)
        show_home(ctx)
    elif choice == 1:
        ctx.set_state(M.D_CAMP_BODY)
        ctx.reply("d_camp_body_ask")
    elif choice == 2:
        sent = mk.process_due_follow_ups(
            ctx.db, ctx.wa, ctx.i18n, datetime.now(timezone.utc)
        )
        ctx.reply("d_followups_sent", count=sent)
        show_marketing(ctx)
    elif choice == 3:
        sent = mk.send_winback(ctx.db, ctx.wa, ctx.i18n, _designer(ctx)["id"])
        ctx.reply("d_winback_sent", count=sent)
        show_marketing(ctx)
    else:
        opted_in = ctx.db.get_opted_in_prospects(_designer(ctx)["id"])
        lines = "\n".join(display_name(p) for p in opted_in) or ctx.i18n.t(
            ctx.lang, "d_optin_empty"
        )
        ctx.reply("d_optin_list", prospects=lines, count=len(opted_in))
        show_marketing(ctx)


def handle_camp_body(ctx: Ctx) -> None:
    body = parse_name(ctx.text)  # same safe-text rule as names
    if body is None:
        ctx.reply("d_camp_body_invalid")
        return
    designer = _designer(ctx)
    opted_in = ctx.db.get_opted_in_prospects(designer["id"])
    camp = ctx.db.create_campaign(
        designer["id"], title=body[:40], body=body,
        template_name=mk.DEFAULT_TEMPLATE,
    )
    ctx.set_state(M.D_CAMP_CONFIRM, campaign_id=camp["id"])
    ctx.reply("d_camp_confirm", body=body, count=len(opted_in))


def handle_camp_confirm(ctx: Ctx) -> None:
    choice = parse_choice(ctx.text, 1, 2)
    if choice is None:
        ctx.reply("d_camp_confirm_invalid")
        return
    if choice == 2:
        ctx.reply("d_camp_cancelled")
        show_marketing(ctx)
        return
    designer = _designer(ctx)
    sent = mk.run_campaign(
        ctx.db, ctx.wa, ctx.i18n, designer["id"],
        ctx.session["data"]["campaign_id"],
    )
    ctx.reply("d_camp_sent", count=sent)
    show_marketing(ctx)

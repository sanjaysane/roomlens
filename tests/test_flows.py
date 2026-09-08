"""End-to-end conversation tests over the fake adapters."""

from __future__ import annotations

import pytest
from conftest import (
    DESIGNER,
    PROSPECT,
    make_blurry_image,
    make_dark_image,
    make_image,
    make_noisy_image,
)

ROOM_BYTES = None
CUTOUT_BYTES = None


def room_bytes():
    global ROOM_BYTES
    if ROOM_BYTES is None:
        ROOM_BYTES = make_noisy_image()
    return ROOM_BYTES


def cutout_bytes():
    global CUTOUT_BYTES
    if CUTOUT_BYTES is None:
        CUTOUT_BYTES = make_image(size=(300, 400), color=(200, 60, 40))
    return CUTOUT_BYTES


def onboard_designer(chat, phone=DESIGNER, name="Casa Studio"):
    chat.send(phone, "hi")
    chat.send(phone, "1")
    chat.send(phone, name)
    return chat.db.get_designer_by_phone(phone)


def add_product(chat, phone=DESIGNER, name="Aria Chair", price="189.00",
                size="1", with_photo=True, media_id="cutout1"):
    chat.send(phone, "1")  # catalog
    chat.send(phone, "1")  # add product
    chat.send(phone, name)  # name → ask price
    chat.send(phone, price)  # price → ask size
    chat.send(phone, size)  # size → ask photo
    if with_photo:
        chat.media.register(media_id, cutout_bytes())
        chat.send(phone, None, msg_type="image", media_id=media_id)
    else:
        chat.send(phone, "0")  # skip photo
    chat.send(phone, "0")  # back to home


def prospect_sends_room(chat, phone=PROSPECT, media_id="room1", data=None,
                        optin="1"):
    chat.send(phone, "hi")
    chat.send(phone, "2")
    chat.send(phone, "1")  # first designer
    data = room_bytes() if data is None else data
    chat.media.register(media_id, data)
    chat.send(phone, None, msg_type="image", media_id=media_id)
    if optin is not None:
        chat.send(phone, optin)


def render_viz(chat, phone=DESIGNER, room_no="1", product_no="1",
               preset="1", adjust="3"):
    """Designer drives the studio: pick room → product → preset → perfect."""
    chat.send(phone, "2")  # studio
    chat.send(phone, room_no)  # pick room → ask product
    chat.send(phone, product_no)  # pick product → ask preset
    chat.send(phone, preset)  # pick preset → adjust
    chat.send(phone, adjust)  # 3 = perfect → sends viz + quote


# ── Happy path ─────────────────────────────────────────────────────
def test_full_happy_path(chat):
    onboard_designer(chat)
    add_product(chat)
    prospect_sends_room(chat)
    # prospect is now waiting for the preview
    assert any("preparing" in t for t in chat.texts(PROSPECT))

    render_viz(chat)

    # prospect received the visualization image + caption
    imgs = chat.images(PROSPECT)
    assert len(imgs) == 1
    caption = imgs[0][2]
    assert "Aria Chair" in caption
    assert "189" in caption
    assert any("1" in t for t in chat.texts(PROSPECT))  # review options sent

    # designer got confirmation
    assert any("Preview sent" in t for t in chat.texts(DESIGNER))

    # prospect orders: choose item 1 → confirm order → confirm again
    chat.send(PROSPECT, "1")  # order screen lists the single quote line
    assert any("order" in t.lower() for t in chat.texts(PROSPECT))
    chat.send(PROSPECT, "1")  # confirm
    texts = chat.texts(PROSPECT)
    assert any("Order #" in t for t in texts)

    # designer was notified of the new order
    assert any("New order" in t for t in chat.texts(DESIGNER))

    # designer marks it delivered → prospect gets the update (F-20: the
    # prospect-facing status is a localized label, never the raw DB token)
    chat.send(DESIGNER, "3")  # orders
    chat.send(DESIGNER, "1")  # pick first order → status menu
    chat.send(DESIGNER, "3")  # delivered
    assert any("is now: Delivered." in t for t in chat.texts(PROSPECT))


def test_prospect_change_placement_notifies_designer(chat):
    onboard_designer(chat)
    add_product(chat)
    prospect_sends_room(chat)
    render_viz(chat)
    chat.send(PROSPECT, "2")  # different placement
    assert any("DIFFERENT PLACEMENT" in t for t in chat.texts(DESIGNER))
    assert any("new preview" in t.lower() for t in chat.texts(PROSPECT))


def _designer_id(chat):
    return chat.db.get_designer_by_phone(DESIGNER)["id"]


# ── Counterfactual safety: bad photos get retakes, not overlays ───
def test_dark_photo_triggers_retake(chat):
    onboard_designer(chat)
    prospect_sends_room(chat, data=make_dark_image(), optin=None)
    texts = chat.texts(PROSPECT)
    assert any("too dark" in t for t in texts)
    # no visualization was produced for a dark photo
    assert chat.db.list_pending_media(_designer_id(chat)) == []


def test_blurry_photo_triggers_retake(chat):
    onboard_designer(chat)
    prospect_sends_room(chat, data=make_blurry_image(), optin=None)
    assert any("blurry" in t for t in chat.texts(PROSPECT))
    assert chat.db.list_pending_media(_designer_id(chat)) == []


def test_small_photo_triggers_retake(chat):
    onboard_designer(chat)
    prospect_sends_room(chat, data=make_image(size=(100, 80)), optin=None)
    assert any("too small" in t for t in chat.texts(PROSPECT))


def test_valid_photo_accepted(chat):
    onboard_designer(chat)
    prospect_sends_room(chat)
    pending = chat.db.list_pending_media(_designer_id(chat))
    assert len(pending) == 1


# ── Invalid selections re-prompt ───────────────────────────────────
def test_invalid_designer_pick_reprompts(chat):
    onboard_designer(chat)
    chat.send(PROSPECT, "hi")
    chat.send(PROSPECT, "2")
    chat.send(PROSPECT, "9")  # no such designer
    assert any("number of your designer" in t for t in chat.texts(PROSPECT))


def test_invalid_choice_reprompts(chat):
    onboard_designer(chat)
    add_product(chat)
    chat.send(PROSPECT, "hi")
    n_before = len(chat.texts(PROSPECT))
    chat.send(PROSPECT, "banana")  # nonsense at welcome
    texts = chat.texts(PROSPECT)[n_before:]
    assert any("Welcome" in t for t in texts)


def test_invalid_price_reprompts(chat):
    onboard_designer(chat)
    chat.send(DESIGNER, "1")  # catalog
    chat.send(DESIGNER, "1")  # add
    chat.send(DESIGNER, "Table")
    chat.send(DESIGNER, "free")  # not a price
    assert any("price" in t.lower() for t in chat.texts(DESIGNER))


# ── Opt-out and marketing suppression ──────────────────────────────
def test_stop_opts_out_everywhere(chat):
    onboard_designer(chat)
    prospect_sends_room(chat, optin="1")
    assert chat.db.get_prospect(PROSPECT)["opt_status"] == "opted_in"
    chat.send(PROSPECT, "STOP")
    assert chat.db.get_prospect(PROSPECT)["opt_status"] == "opted_out"
    assert any("unsubscribed" in t for t in chat.texts(PROSPECT))


def test_campaign_suppresses_opted_out(chat):
    from src import marketing as mk

    onboard_designer(chat)
    designer = chat.db.get_designer_by_phone(DESIGNER)
    prospect_sends_room(chat, phone="15550003333", media_id="r3", optin="1")
    prospect_sends_room(chat, phone="15550004444", media_id="r4", optin="2")  # declined
    chat.db.set_prospect_opt("15550004444", "opted_out")
    camp = chat.db.create_campaign(designer["id"], "Sale", "Spring sale is on",
                                   mk.DEFAULT_TEMPLATE)
    sent = mk.run_campaign(chat.db, chat.wa, chat.i18n, designer["id"], camp["id"])
    assert sent == 1
    recipients = {to for to, _name in chat.wa.templates}
    assert recipients == {"15550003333"}


def test_winback_targets_only_opted_in_inactive(chat):
    from datetime import datetime, timedelta, timezone

    from src import marketing as mk

    onboard_designer(chat)
    designer = chat.db.get_designer_by_phone(DESIGNER)
    chat.db.ensure_prospect("15550005555", DESIGNER)
    chat.db.ensure_prospect("15550006666", DESIGNER)
    chat.db.set_prospect_opt("15550005555", "opted_in")
    chat.db.set_prospect_opt("15550006666", "opted_out")
    old = datetime.now(timezone.utc) - timedelta(days=30)
    for ph in ("15550005555", "15550006666"):
        # FakeDatabase detail: manipulate the in-memory row
        row = chat.db.get_prospect(ph)
        row["last_active_at"] = old
    sent = mk.send_winback(chat.db, chat.wa, chat.i18n, designer["id"],
                           inactive_days=14)
    assert sent == 1
    recipients = {to for to, _name in chat.wa.templates}
    assert recipients == {"15550005555"}


def test_due_followups_send_and_reschedule(chat):
    from datetime import datetime, timedelta, timezone

    from src import marketing as mk

    onboard_designer(chat)
    designer = chat.db.get_designer_by_phone(DESIGNER)
    prospect_sends_room(chat, optin="1")
    prospect = chat.db.get_prospect(PROSPECT)
    due = datetime.now(timezone.utc) - timedelta(hours=1)
    chat.db.schedule_follow_up(designer["id"], prospect["id"], "nudge", due)
    sent = mk.process_due_follow_ups(
        chat.db, chat.wa, chat.i18n, datetime.now(timezone.utc)
    )
    assert sent == 1
    assert db_list_due_empty(chat)
    recipients = {to for to, _name in chat.wa.templates}
    assert PROSPECT in recipients


def db_list_due_empty(chat):
    from datetime import datetime, timezone
    return chat.db.list_due_follow_ups(datetime.now(timezone.utc)) == []


# ── Mid-chat language switch ───────────────────────────────────────
def test_language_switch_mid_chat(chat):
    onboard_designer(chat)
    chat.send(PROSPECT, "hi")
    chat.send(PROSPECT, "2")
    chat.send(PROSPECT, "1")  # now at name prompt, in English
    chat.send(PROSPECT, "language")
    # menu renders in the current language (English), naming all options
    assert any("Choose your language" in t for t in chat.texts(PROSPECT))
    chat.send(PROSPECT, "2")  # español
    assert chat.db.get_user(PROSPECT)["preferred_language"] == "es"
    # back at the name prompt, now in Spanish
    assert any("¿Cómo te llamas?" in t for t in chat.texts(PROSPECT))


# ── Designer catalog management ────────────────────────────────────
def test_designer_removes_product(chat):
    onboard_designer(chat)
    designer_id = _designer_id(chat)
    add_product(chat, name="Chair", price="100.00", media_id="c1")
    add_product(chat, name="Table", price="200.00", media_id="c2")
    prods = chat.db.list_products(designer_id)
    assert len(prods) == 2
    chat.send(DESIGNER, "1")  # catalog
    chat.send(DESIGNER, "2")  # remove
    chat.send(DESIGNER, "1")  # remove first
    prods = chat.db.list_products(designer_id)
    assert len(prods) == 1
    assert prods[0]["name"] == "Table"


def test_studio_bigger_smaller_adjust(chat):
    onboard_designer(chat)
    add_product(chat)
    prospect_sends_room(chat)
    chat.send(DESIGNER, "2")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "1")  # bigger → adjust menu again, no send yet
    assert chat.images(PROSPECT) == []
    chat.send(DESIGNER, "3")  # perfect → send
    assert len(chat.images(PROSPECT)) == 1


# ── Video ingestion ──────────────────────────────────────────────
def test_video_frame_extracted_and_accepted(chat):
    import subprocess
    import tempfile
    from pathlib import Path

    from src.composite import ffmpeg_available

    if not ffmpeg_available():
        pytest.skip("ffmpeg not installed")
    onboard_designer(chat)
    with tempfile.TemporaryDirectory() as tmp:
        frame = Path(tmp) / "frame.png"
        clip = Path(tmp) / "clip.mp4"
        frame.write_bytes(room_bytes())
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(frame),
             "-t", "1", "-pix_fmt", "yuv420p", str(clip)],
            check=True,
        )
        chat.send(PROSPECT, "hi")
        chat.send(PROSPECT, "2")
        chat.send(PROSPECT, "1")
        chat.media.register("vid1", clip.read_bytes())
        chat.send(PROSPECT, None, msg_type="video", media_id="vid1")
    # first frame extracted → accepted like a photo
    assert len(chat.db.list_pending_media(_designer_id(chat))) == 1
    assert any("preparing" in t for t in chat.texts(PROSPECT))


def test_undecodable_video_asks_for_photo(chat):
    onboard_designer(chat)
    chat.send(PROSPECT, "hi")
    chat.send(PROSPECT, "2")
    chat.send(PROSPECT, "1")
    chat.media.register("vidbad", b"not a video at all")
    chat.send(PROSPECT, None, msg_type="video", media_id="vidbad")
    assert any("still photo" in t for t in chat.texts(PROSPECT))
    assert chat.db.list_pending_media(_designer_id(chat)) == []

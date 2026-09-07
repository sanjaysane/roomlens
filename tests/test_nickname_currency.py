"""Nickname display names + locale-aware currency.

Nicknames: every customer-facing surface shows the prospect's nickname
(or the designer's studio name); the phone number is only a fallback.
Currency: money renders in ₹ for mr/hi locales and $ for en/es locales.
"""

from __future__ import annotations

from conftest import DESIGNER, PROSPECT, Chat, make_noisy_image

from src import pricing as P
from src.display import designer_name, display_name, prospect_name


# ── helpers ────────────────────────────────────────────────────────
def onboard(chat: Chat, phone: str = DESIGNER) -> None:
    chat.send(phone, "hi")
    chat.send(phone, "1")
    chat.send(phone, "Casa Studio")


def prospect_sends_room_named(chat: Chat, name: str, phone: str = PROSPECT,
                              media_id: str = "room1") -> None:
    chat.send(phone, "hi")
    chat.send(phone, "2")
    chat.send(phone, "1")  # first designer
    chat.send(phone, name)  # nickname capture
    chat.media.register(media_id, make_noisy_image())
    chat.send(phone, None, msg_type="image", media_id=media_id)
    chat.send(phone, "1")  # opt in


def prospect_sends_room_unnamed(chat: Chat, phone: str = PROSPECT,
                                media_id: str = "room2") -> None:
    chat.send(phone, "hi")
    chat.send(phone, "2")
    chat.send(phone, "1")  # first designer
    chat.send(phone, "0")  # skip the nickname
    chat.media.register(media_id, make_noisy_image())
    chat.send(phone, None, msg_type="image", media_id=media_id)
    chat.send(phone, "1")  # opt in


# ── display-name units ─────────────────────────────────────────────
def test_display_name_prefers_nickname_then_phone():
    assert display_name({"nickname": "Asha", "phone_number": "+1555"}) == "Asha"
    assert display_name({"nickname": "", "phone_number": "+1555"}) == "+1555"
    assert display_name({"nickname": "  ", "phone_number": "+1555"}) == "+1555"
    assert display_name({}) == ""
    assert display_name(None) == ""


def test_prospect_and_designer_names():
    assert prospect_name({"nickname": "Asha", "phone_number": "+1"}) == "Asha"
    assert prospect_name({"nickname": "", "phone_number": "+1"}) == "+1"
    assert designer_name({"display_name": "Casa", "phone_number": "+1"}) == "Casa"
    assert designer_name({"display_name": "", "phone_number": "+1"}) == "+1"


def test_currency_for_locale():
    assert P.currency_for_locale("en") == "USD"
    assert P.currency_for_locale("es") == "USD"
    assert P.currency_for_locale("hi") == "INR"
    assert P.currency_for_locale("mr") == "INR"
    assert P.currency_for_locale("") == "USD"
    assert P.currency_for_locale(None) == "USD"
    assert P.currency_for_locale("xx") == "USD"


def test_quote_lines_text_locale_currency():
    q = P.build_quote([{"name": "Chair", "qty": 1, "price_cents": 18900}],
                      delivery_cents=0, currency="USD")
    assert any("₹189.00" in l for l in P.quote_lines_text(q, lang="mr"))
    assert any("₹189.00" in l for l in P.quote_lines_text(q, lang="hi"))
    assert any("$189.00" in l for l in P.quote_lines_text(q, lang="en"))
    assert any("$189.00" in l for l in P.quote_lines_text(q, lang="es"))
    # back-compat: no lang → English/USD (existing behavior preserved)
    assert any("$189.00" in l for l in P.quote_lines_text(q))


# ── nickname capture flow ──────────────────────────────────────────
def test_nickname_captured_after_designer_pick(chat: Chat):
    onboard(chat)
    chat.send(PROSPECT, "hi")
    chat.send(PROSPECT, "2")
    chat.send(PROSPECT, "1")
    assert any("your name" in t for t in chat.texts(PROSPECT))
    chat.send(PROSPECT, "Asha")
    assert chat.db.get_prospect(PROSPECT)["nickname"] == "Asha"
    # now at the photo prompt
    assert any("room" in t.lower() for t in chat.texts(PROSPECT))


def test_name_skip_with_zero(chat: Chat):
    onboard(chat)
    chat.send(PROSPECT, "hi")
    chat.send(PROSPECT, "2")
    chat.send(PROSPECT, "1")
    chat.send(PROSPECT, "0")
    assert chat.db.get_prospect(PROSPECT)["nickname"] == ""


def test_invalid_name_reprompts(chat: Chat):
    onboard(chat)
    chat.send(PROSPECT, "hi")
    chat.send(PROSPECT, "2")
    chat.send(PROSPECT, "1")
    chat.send(PROSPECT, "<script>")  # injection-safe rejection
    assert chat.db.get_prospect(PROSPECT)["nickname"] == ""
    # re-ask happened (photo prompt must NOT have fired yet)
    assert not any("📸 Great!" in t for t in chat.texts(PROSPECT))


def test_photo_at_name_prompt_is_accepted_as_implicit_skip(chat: Chat):
    """Sending the photo straight away never blocks on the name question."""
    onboard(chat)
    chat.send(PROSPECT, "hi")
    chat.send(PROSPECT, "2")
    chat.send(PROSPECT, "1")
    chat.media.register("room1", make_noisy_image())
    chat.send(PROSPECT, None, msg_type="image", media_id="room1")
    assert any("preparing" in t for t in chat.texts(PROSPECT))


# ── no bare phone numbers on customer-facing surfaces ──────────────
def test_designer_notification_shows_nickname_not_phone(chat: Chat):
    onboard(chat)
    prospect_sends_room_named(chat, "Asha")
    texts = chat.texts(DESIGNER)
    assert any("Asha" in t for t in texts), texts
    new_photo = [t for t in texts if "New room photo" in t]
    assert new_photo and PROSPECT not in new_photo[0]


def test_designer_notification_falls_back_to_phone(chat: Chat):
    onboard(chat)
    prospect_sends_room_unnamed(chat)
    texts = chat.texts(DESIGNER)
    new_photo = [t for t in texts if "New room photo" in t]
    assert new_photo and PROSPECT in new_photo[0], texts


def test_studio_room_list_shows_nickname(chat: Chat):
    onboard(chat)
    prospect_sends_room_named(chat, "Asha", media_id="r1")
    chat.send(DESIGNER, "2")  # studio
    texts = chat.texts(DESIGNER)
    rooms = [t for t in texts if "Rooms waiting" in t]
    assert rooms and "Asha" in rooms[0] and PROSPECT not in rooms[0], texts


def test_optin_list_shows_nickname(chat: Chat):
    onboard(chat)
    prospect_sends_room_named(chat, "Asha", media_id="r1")
    chat.send(DESIGNER, "4")  # marketing
    chat.send(DESIGNER, "4")  # view opt-in list
    texts = chat.texts(DESIGNER)
    opted = [t for t in texts if "Opted-in prospects" in t]
    assert opted and "Asha" in opted[0] and PROSPECT not in opted[0], texts


def test_change_notifications_show_nickname(chat: Chat):
    onboard(chat)
    prospect_sends_room_named(chat, "Asha", media_id="r1")
    # render + send a viz so the review menu is live
    chat.send(DESIGNER, "1")  # catalog
    chat.send(DESIGNER, "1")  # add product
    chat.send(DESIGNER, "Aria Chair")
    chat.send(DESIGNER, "189.00")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "0")  # skip photo
    chat.send(DESIGNER, "0")  # home
    chat.send(DESIGNER, "2")  # studio
    chat.send(DESIGNER, "1")  # pick room
    chat.send(DESIGNER, "1")  # pick product
    chat.send(DESIGNER, "1")  # pick preset
    chat.send(DESIGNER, "3")  # perfect → send
    chat.send(PROSPECT, "2")  # different placement
    texts = chat.texts(DESIGNER)
    change = [t for t in texts if "DIFFERENT PLACEMENT" in t]
    assert change and "Asha" in change[0] and PROSPECT not in change[0], texts


# ── locale-aware currency end to end ───────────────────────────────
def test_marathi_prospect_sees_inr_everywhere(chat: Chat):
    onboard(chat)
    # prospect picks Marathi, skips the name, sends a room photo
    chat.send(PROSPECT, "hi")
    chat.send(PROSPECT, "2")
    chat.send(PROSPECT, "1")
    chat.send(PROSPECT, "language")
    chat.send(PROSPECT, "4")  # मराठी
    chat.media.register("room1", make_noisy_image())
    chat.send(PROSPECT, None, msg_type="image", media_id="room1")
    chat.send(PROSPECT, "1")  # opt in

    # designer adds a product (English locale) and renders the preview
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "Aria Chair")
    chat.send(DESIGNER, "189.00")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "0")
    chat.send(DESIGNER, "0")
    chat.send(DESIGNER, "2")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "3")

    captions = chat.image_captions(PROSPECT)
    assert captions, "prospect got no visualization"
    assert any("₹" in c for c in captions), captions
    assert not any("$" in c for c in captions), captions

    # order confirm screen also renders in INR for the Marathi prospect
    chat.send(PROSPECT, "1")
    order_texts = chat.texts(PROSPECT)
    confirm = [t for t in order_texts if "ऑर्डर" in t]
    assert confirm and any("₹" in t for t in confirm), order_texts


def test_english_prospect_sees_usd(chat: Chat):
    onboard(chat)
    prospect_sends_room_named(chat, "Asha", media_id="r1")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "Aria Chair")
    chat.send(DESIGNER, "189.00")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "0")
    chat.send(DESIGNER, "0")
    chat.send(DESIGNER, "2")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "3")
    captions = chat.image_captions(PROSPECT)
    assert captions
    assert any("$" in c for c in captions), captions
    assert not any("₹" in c for c in captions), captions


def test_designer_catalog_uses_designer_locale_currency(chat: Chat):
    onboard(chat)
    chat.send(DESIGNER, "language")
    chat.send(DESIGNER, "4")  # designer switches to Marathi
    chat.send(DESIGNER, "1")  # catalog
    chat.send(DESIGNER, "1")  # add product
    chat.send(DESIGNER, "Aria Chair")
    chat.send(DESIGNER, "189.00")
    chat.send(DESIGNER, "1")
    chat.send(DESIGNER, "0")
    texts = chat.texts(DESIGNER)
    added = [t for t in texts if "Aria Chair" in t]
    assert added and any("₹" in t for t in added), texts
    assert not any("$" in t for t in added), texts


def test_nickname_survives_db_roundtrip():
    from src.db import FakeDatabase

    db = FakeDatabase()
    p = db.ensure_prospect("+15550009999", "", "en")
    assert p["nickname"] == ""
    db.set_prospect_nickname("+15550009999", "  Asha  ")
    assert db.get_prospect("+15550009999")["nickname"] == "Asha"

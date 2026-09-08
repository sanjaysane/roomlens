"""Quote math, parsing, and validation unit tests."""

from __future__ import annotations

import pytest

from src import pricing as P
from src.context import parse_choice, parse_name, parse_price


def test_build_quote_sums_lines():
    q = P.build_quote(
        [
            {"name": "Aria Chair", "qty": 2, "price_cents": 18900},
            {"name": "Oak Table", "qty": 1, "price_cents": 45900},
        ],
        delivery_cents=0,
        currency="USD",
    )
    assert q["subtotal_cents"] == 2 * 18900 + 45900
    assert q["total_cents"] == 2 * 18900 + 45900
    lines = P.quote_lines_text(q)
    assert any("Aria Chair × 2" in line for line in lines)
    assert any("$837.00" in line for line in lines)


def test_build_quote_rejects_bad_items():
    with pytest.raises(ValueError):
        P.build_quote([{"name": "X", "qty": 0, "price_cents": 100}],
                      delivery_cents=0)
    with pytest.raises(ValueError):
        P.build_quote([{"name": "X", "qty": 1, "price_cents": -5}],
                      delivery_cents=0)
    with pytest.raises(ValueError):
        P.build_quote([], delivery_cents=0)
    with pytest.raises(ValueError):
        P.build_quote([{"name": "X", "qty": 1, "price_cents": 100}],
                      delivery_cents=-1)


def test_format_money():
    assert P.format_money(18900) == "$189.00"
    assert P.format_money(18900, "INR") == "₹189.00"
    assert P.format_money(0) == "$0.00"


@pytest.mark.parametrize(
    "raw,expected",
    [("1", 1), (" 2 ", 2), ("3", 3), ("one", None), ("", None),
     ("0", None), ("4", None), ("12", None), (None, None)],
)
def test_parse_choice(raw, expected):
    assert parse_choice(raw, 1, 3) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [("189", 189.0), ("$189.00", 189.0), ("8.50", 8.5),
     ("1,299.50", None),  # commas rejected: unambiguous digits only
     ("0", None), ("-5", None), ("abc", None), ("", None), (None, None)],
)
def test_parse_price(raw, expected):
    assert parse_price(raw) == expected


def test_parse_name_accepts_normal():
    assert parse_name("Casa Studio") == "Casa Studio"


def test_parse_name_rejects_junk():
    assert parse_name("") is None
    assert parse_name("   ") is None
    assert parse_name("<script>") is None
    assert parse_name("x" * 61) is None
    assert parse_name("DROP TABLE;") is None


# ── v3 review F-19/F-20: localized receipt labels and order statuses ──
def test_quote_total_label_localized():
    q = P.build_quote([{"name": "Chair", "qty": 1, "price_cents": 18900}],
                      delivery_cents=0, currency="USD")
    assert any("एकूण — ₹189.00" in l for l in P.quote_lines_text(q, lang="mr"))
    assert any("कुल — ₹189.00" in l for l in P.quote_lines_text(q, lang="hi"))
    assert any("Total — $189.00" in l for l in P.quote_lines_text(q, lang="en"))
    # no raw-English "Total —" leaks into the Marathi/Hindi receipt
    assert not any(l.startswith("Total —") for l in P.quote_lines_text(q, lang="mr"))


def test_order_status_label_prospect_facing():
    # F-20: "received" must not read as the prospect receiving her order
    assert P.order_status_label("received", "mr") == "ऑर्डर डिझायनरला पोहोचली"
    assert P.order_status_label("preparing", "mr") == "तयार होत आहे"
    assert P.order_status_label("out_for_delivery", "hi") == "डिलीवरी के लिए निकला"
    assert P.order_status_label("delivered", "en") == "Delivered"
    assert P.order_status_label("delivered", "es") == "Entregado"
    # unknown status can never break a chat: falls back to readable token
    assert P.order_status_label("some_new_state", "mr") == "some new state"


def test_order_placed_carries_payment_line():
    # F-22: the prospect is told she pays the designer directly, off-platform
    from src.i18n import I18n
    i18n = I18n("locales")
    for lang, marker in (("en", "never takes your money"),
                         ("mr", "अ‍ॅप मध्ये पैसे घेत नाही")):
        assert marker in i18n.t(lang, "p_order_placed", order_id=1)

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

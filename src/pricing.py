"""Quote math and money formatting.

All money is integer cents internally; formatting is presentation-only.
"""

from __future__ import annotations

CURRENCY_SYMBOLS = {"USD": "$", "EUR": "€", "INR": "₹", "BRL": "R$"}

# ── Locale-aware display currency ──────────────────────────────────
# Money is always *rendered* in the viewer's locale currency:
# Marathi/Hindi users (India) see ₹, English/Spanish users see $.
# The stored product/quote/order currency columns keep the record
# of the currency the amount was entered in; display never converts
# amounts, it only picks the symbol/format for the viewer's locale.
LOCALE_CURRENCIES = {
    "en": "USD",
    "es": "USD",
    "hi": "INR",
    "mr": "INR",
}


def currency_for_locale(lang: str | None) -> str:
    """Display currency for a chat locale. Unknown/empty → USD."""
    return LOCALE_CURRENCIES.get((lang or "").lower(), "USD")


# ── Locale-aware receipt labels ────────────────────────────────────
# v3 review F-19: the quote's "Total" label rendered in plain English for
# every locale. Labels below are keyed by chat locale; unknown → English.
_TOTAL_LABELS = {
    "en": "Total",
    "es": "Total",
    "hi": "कुल",
    "mr": "एकूण",
}
_DELIVERY_LABELS = {
    "en": "Delivery",
    "es": "Entrega",
    "hi": "डिलीवरी",
    "mr": "डिलिव्हरी",
}


def receipt_label(kind: str, lang: str | None) -> str:
    """Localized 'Total'/'Delivery' label for the quote receipt."""
    lang = (lang or "").lower()
    table = _TOTAL_LABELS if kind == "total" else _DELIVERY_LABELS
    return table.get(lang, table["en"])


# ── Locale-aware order-status labels ───────────────────────────────
# v3 review F-20: the raw DB status ("received") rendered in English for
# every locale, and "received" read backwards from the prospect's side
# (she received nothing — the designer received her order). These labels
# are prospect-facing: they describe what is happening to HER order.
_STATUS_LABELS: dict[str, dict[str, str]] = {
    "received": {
        "en": "Received by the designer",
        "es": "Recibido por el diseñador",
        "hi": "डिज़ाइनर को ऑर्डर मिल गया",
        "mr": "ऑर्डर डिझायनरला पोहोचली",
    },
    "preparing": {
        "en": "Preparing",
        "es": "En preparación",
        "hi": "तैयार हो रहा है",
        "mr": "तयार होत आहे",
    },
    "out_for_delivery": {
        "en": "Out for delivery",
        "es": "En camino",
        "hi": "डिलीवरी के लिए निकला",
        "mr": "डिलिव्हरीसाठी निघाली",
    },
    "delivered": {
        "en": "Delivered",
        "es": "Entregado",
        "hi": "डिलीवर हो गया",
        "mr": "डिलिव्हरी झाली",
    },
    "cancelled": {
        "en": "Cancelled",
        "es": "Cancelado",
        "hi": "रद्द हो गया",
        "mr": "रद्द झाली",
    },
}


def order_status_label(status: str, lang: str | None) -> str:
    """Prospect-facing, localized label for an order status.

    Unknown statuses fall back to the raw token with underscores
    replaced (old behavior), so a new DB status can never break a chat.
    """
    lang = (lang or "").lower()
    table = _STATUS_LABELS.get(status) or {}
    return table.get(lang) or table.get("en") or status.replace("_", " ")


def format_money(cents: int, currency: str = "USD") -> str:
    symbol = CURRENCY_SYMBOLS.get((currency or "USD").upper(), "")
    amount = cents / 100
    if symbol:
        return f"{symbol}{amount:,.2f}"
    return f"{amount:,.2f} {(currency or '').upper()}"


def build_quote(
    line_items: list[dict], delivery_cents: int, currency: str = "USD"
) -> dict:
    """line_items: [{"name": str, "price_cents": int, "qty": int}].

    Returns the quote dict (no DB): line totals, subtotal, delivery,
    total. Raises ValueError on invalid input — never silently misprices.
    """
    if not line_items:
        raise ValueError("quote needs at least one line item")
    if delivery_cents < 0:
        raise ValueError("delivery_cents must be >= 0")
    lines = []
    subtotal = 0
    for it in line_items:
        qty = int(it.get("qty", 1))
        price = int(it.get("price_cents", 0))
        if qty <= 0 or price <= 0:
            raise ValueError(f"invalid line item: {it!r}")
        line_total = qty * price
        subtotal += line_total
        lines.append(
            {
                "name": str(it.get("name", "")),
                "price_cents": price,
                "qty": qty,
                "line_total_cents": line_total,
            }
        )
    total = subtotal + int(delivery_cents)
    return {
        "line_items": lines,
        "subtotal_cents": subtotal,
        "delivery_cents": int(delivery_cents),
        "total_cents": total,
        "currency": currency,
    }


def quote_lines_text(quote: dict, lang: str = "en") -> list[str]:
    """Human-readable lines for the price strip / chat receipt.

    Amounts render in the viewer's locale currency (₹ for mr/hi,
    $ for en/es) via currency_for_locale — see the note above.
    """
    currency = currency_for_locale(lang)
    out = []
    for it in quote["line_items"]:
        out.append(
            f"{it['name']} × {it['qty']} — "
            f"{format_money(it['line_total_cents'], currency)}"
        )
    if quote["delivery_cents"]:
        out.append(
            receipt_label("delivery", lang)
            + " — "
            + format_money(quote["delivery_cents"], currency)
        )
    out.append(
        receipt_label("total", lang)
        + " — "
        + format_money(quote["total_cents"], currency)
    )
    return out

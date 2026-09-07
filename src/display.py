"""Customer-facing display names.

Hard rule: no customer-facing surface ever shows a bare phone number
when a human-readable name exists.

- Prospects: `nickname` (asked once after designer selection), with the
  phone number as the fallback when no nickname is set.
- Designers: `display_name` (the studio name from onboarding), with the
  phone number as the fallback.
"""

from __future__ import annotations


def prospect_name(prospect: dict | None) -> str:
    """How a prospect is shown to humans: nickname, else phone."""
    if not prospect:
        return ""
    return (prospect.get("nickname") or "").strip() or prospect.get(
        "phone_number", ""
    )


def designer_name(designer: dict | None) -> str:
    """How a designer is shown to humans: studio name, else phone."""
    if not designer:
        return ""
    return (designer.get("display_name") or "").strip() or designer.get(
        "phone_number", ""
    )


def display_name(row: dict | None) -> str:
    """Generic: nickname → display_name → phone_number, whichever exists."""
    if not row:
        return ""
    return (
        (row.get("nickname") or "").strip()
        or (row.get("display_name") or "").strip()
        or row.get("phone_number", "")
    )

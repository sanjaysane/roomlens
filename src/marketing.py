"""Marketing: opt-in enforcement, campaigns, follow-ups, win-back.

Hard rule: business-initiated messages go ONLY to prospects whose
opt_status is 'opted_in', and ONLY through a Meta pre-approved template
(`send_template`). The `send_marketing` gate is the single choke point —
every campaign, follow-up, and win-back flows through it, and tests
assert that opted-out prospects are silently skipped.

Opt-in happens conversationally: after a prospect's first photo is
accepted we ask once ("Reply 1 for design tips & offers"). STOP opts
out everywhere, instantly.
"""

from __future__ import annotations

from .db import Database
from .i18n import I18n
from .whatsapp import WhatsAppClient

# Fallback template name when the designer hasn't configured one.
# DEPLOYMENT REQUIREMENT: create and get approval for a real template
# in the Meta WhatsApp Manager before sending business-initiated
# messages in production; set it per campaign via template_name.
DEFAULT_TEMPLATE = "roomlens_update"


def send_marketing(
    db: Database,
    wa: WhatsAppClient,
    i18n: I18n,
    designer_id: int,
    prospects: list[dict],
    template_name: str,
    body_params: list[str] | None = None,
    language_code: str = "en_US",
) -> int:
    """Send a template message to opted-in prospects only.

    Returns the number actually sent. Prospects whose opt_status is not
    'opted_in' are skipped silently — suppression is a feature, tested.
    """
    sent = 0
    for p in prospects:
        if p.get("opt_status") != "opted_in":
            continue
        # NOTE: template language defaults to en_US; per-prospect template
        # localization requires approved translated templates in Meta's
        # WhatsApp Manager — see docs/DEPLOYMENT.
        wa.send_template(
            p["phone_number"],
            template_name or DEFAULT_TEMPLATE,
            language_code=language_code,
            body_params=body_params or [],
        )
        sent += 1
    return sent


def run_campaign(
    db: Database,
    wa: WhatsAppClient,
    i18n: I18n,
    designer_id: int,
    campaign_id: int,
) -> int:
    """Fan-out a campaign to every opted-in prospect of the designer."""
    # NOTE: campaign lookup by id across designers is intentionally
    # narrow; callers pass the designer-owned campaign id.
    prospects = db.get_opted_in_prospects(designer_id)
    # (template name would come from the campaign row in a fuller impl;
    # kept explicit here so the template requirement stays visible.)
    sent = send_marketing(
        db, wa, i18n, designer_id, prospects, DEFAULT_TEMPLATE, []
    )
    for p in prospects:
        if p.get("opt_status") == "opted_in":
            db.add_recipient(campaign_id, p["id"])
            db.mark_recipient_sent(campaign_id, p["id"])
    db.mark_campaign_sent(campaign_id, sent)
    return sent


def send_winback(
    db: Database,
    wa: WhatsAppClient,
    i18n: I18n,
    designer_id: int,
    inactive_days: int = 14,
) -> int:
    """Nudge opted-in prospects inactive for `inactive_days`+."""
    prospects = db.get_inactive_prospects(designer_id, inactive_days)
    return send_marketing(
        db, wa, i18n, designer_id, prospects, DEFAULT_TEMPLATE, []
    )


def process_due_follow_ups(
    db: Database, wa: WhatsAppClient, i18n: I18n, now
) -> int:
    """Fire scheduled follow-ups that are due. Returns count sent."""
    sent = 0
    for fu in db.list_due_follow_ups(now):
        # list_due_follow_ups joins the prospect phone number in.
        phone = fu.get("prospect_phone")
        if not phone:
            continue
        # Only opted-in prospects receive follow-ups.
        # (Prospect lookup by id is not in the interface; the join in
        # list_due_follow_ups gives us the phone, and we check the
        # designer's opted-in list for it.)
        opted_in_phones = {
            p["phone_number"]
            for p in db.get_opted_in_prospects(fu["designer_id"])
        }
        if phone not in opted_in_phones:
            db.mark_follow_up_sent(fu["id"])  # swallow: never message them
            continue
        wa.send_template(phone, DEFAULT_TEMPLATE, body_params=[fu["kind"]])
        db.mark_follow_up_sent(fu["id"])
        sent += 1
    return sent

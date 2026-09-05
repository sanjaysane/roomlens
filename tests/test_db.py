"""Database tests: full FakeDatabase round-trip + real PostgreSQL smoke.

The PostgreSQL test is skipped unless DATABASE_URL is set and reachable;
CI runs it against the postgres service with the schema applied.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db import FakeDatabase, PostgresDatabase

DPHONE = "+15550001001"
PPHONE = "+15550001002"


def exercise(db, tag: str):
    # users + sessions
    db.upsert_user(DPHONE, role="designer", language="es")
    u = db.get_user(DPHONE)
    assert u["preferred_language"] == "es"
    db.set_user_language(DPHONE, "en")
    assert db.get_user(DPHONE)["preferred_language"] == "en"

    db.save_session(DPHONE, {"role": "designer", "state": "x", "lang": "en",
                             "data": {"a": 1}})
    assert db.get_session(DPHONE)["data"]["a"] == 1

    # designer + prospect + media pipeline
    d = db.ensure_designer(DPHONE, "Studio X")
    assert db.get_designer_by_phone(DPHONE)["id"] == d["id"]
    assert db.list_designers()
    p = db.ensure_prospect(PPHONE, tag)
    m = db.add_room_media(p["id"], d["id"], "local://room1.png", "photo",
                          800, 600, {"verdict": "ok"})
    pending = db.list_pending_media(d["id"])
    assert len(pending) == 1 and pending[0]["id"] == m["id"]
    db.mark_media_visualized(m["id"])
    assert db.list_pending_media(d["id"]) == []

    # products
    prod = db.add_product(d["id"], "Chair", "A comfy chair", 18900, "USD",
                          "floor", "floor-center")
    assert db.list_products(d["id"])[0]["name"] == "Chair"
    assert db.get_product(prod["id"])["price_cents"] == 18900
    db.set_product_active(prod["id"], False)
    assert db.list_products(d["id"]) == []
    assert db.list_products(d["id"], active_only=False)[0]["name"] == "Chair"

    # visualization + quote + order
    prod2 = db.add_product(d["id"], "Lamp", "A lamp", 5900, "USD",
                           "tabletop", "floor-center")
    viz = db.create_visualization(
        p["id"], d["id"], m["id"],
        [{"product_id": prod2["id"], "preset": "floor-center", "scale": 1.0}],
    )
    assert db.get_visualization(viz["id"])["id"] == viz["id"]
    assert db.list_open_visualizations(d["id"])[0]["id"] == viz["id"]
    db.update_visualization(viz["id"], status="sent", rendered_ref="local://v.png")
    assert db.get_visualization(viz["id"])["status"] == "sent"

    quote = db.create_quote(
        viz["id"], [{"name": "Lamp", "qty": 2, "price_cents": 5900}],
        11800, 0, 11800, "USD",
    )
    assert db.get_quote_by_visualization(viz["id"])["id"] == quote["id"]

    order = db.create_order(PPHONE, d["id"], quote["id"], 11800, "USD")
    assert db.get_order(order["id"])["total_cents"] == 11800
    assert db.list_open_orders(d["id"])[0]["id"] == order["id"]
    assert db.list_orders_for_prospect(PPHONE)[0]["id"] == order["id"]
    db.update_order(order["id"], status="delivered")
    assert db.get_order(order["id"])["status"] == "delivered"
    assert db.list_open_orders(d["id"]) == []

    # campaigns + opt-in gate
    db.set_prospect_opt(PPHONE, "opted_in")
    assert len(db.get_opted_in_prospects(d["id"])) == 1
    camp = db.create_campaign(d["id"], "Sale", "Big sale!", "roomlens_update")
    db.add_recipient(camp["id"], p["id"])
    db.mark_recipient_sent(camp["id"], p["id"])
    db.mark_campaign_sent(camp["id"], 1)

    # follow-ups
    due = datetime.now(timezone.utc) - timedelta(hours=1)
    fu = db.schedule_follow_up(d["id"], p["id"], "nudge", due)
    dues = db.list_due_follow_ups(datetime.now(timezone.utc))
    assert len(dues) == 1 and dues[0]["prospect_phone"] == PPHONE
    db.mark_follow_up_sent(fu["id"])
    assert db.list_due_follow_ups(datetime.now(timezone.utc)) == []

    # win-back targets: opted-in + inactive
    assert db.get_inactive_prospects(d["id"], 0) != []
    db.set_prospect_opt(PPHONE, "opted_out")
    assert db.get_prospect(PPHONE)["opt_status"] == "opted_out"
    assert db.get_opted_in_prospects(d["id"]) == []
    assert db.get_inactive_prospects(d["id"], 0) == []
    return True


def test_fake_database_roundtrip():
    assert exercise(FakeDatabase(), DPHONE)


@pytest.mark.postgres
def test_postgres_schema_and_roundtrip():
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    import psycopg

    schema = (Path(__file__).resolve().parents[1] / "sql" / "schema.sql").read_text()
    with psycopg.connect(url) as conn:
        conn.execute(schema)
    try:
        assert exercise(PostgresDatabase(url), DPHONE)
    finally:
        # leave no residue between runs
        with psycopg.connect(url, autocommit=True) as conn:
            conn.execute(
                "TRUNCATE users, chat_sessions, designers, prospects, products,"
                " room_media, visualizations, quotes, orders, campaigns,"
                " campaign_recipients, follow_ups RESTART IDENTITY CASCADE;"
            )

"""Database access layer.

Two implementations share one interface:
  * PostgresDatabase — psycopg3, short-lived connection per call.
    Serverless-safe (no persistent pool to leak between invocations).
  * FakeDatabase — in-memory dicts with identical semantics, used by tests
    and local development without a database.

Every query here mirrors sql/schema.sql exactly (table/column/enum names).
"""

from __future__ import annotations

import abc
import itertools
import json
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_phone(raw: str | None) -> str | None:
    """Normalize to E.164-ish '+<digits>'. Returns None when unusable."""
    if not raw:
        return None
    digits = "".join(c for c in raw if c.isdigit())
    if len(digits) < 7 or len(digits) > 15:
        return None
    return "+" + digits


class Database(abc.ABC):
    # ── users ──────────────────────────────────────────────────
    @abc.abstractmethod
    def get_user(self, phone: str) -> dict | None: ...
    @abc.abstractmethod
    def upsert_user(self, phone: str, role: str, language: str) -> dict: ...
    @abc.abstractmethod
    def set_user_language(self, phone: str, language: str) -> None: ...

    # ── sessions (serverless state hydration) ──────────────────
    @abc.abstractmethod
    def get_session(self, phone: str) -> dict | None: ...
    @abc.abstractmethod
    def save_session(self, phone: str, session: dict) -> None: ...

    # ── designers ──────────────────────────────────────────────
    @abc.abstractmethod
    def ensure_designer(self, phone: str, display_name: str = "") -> dict: ...
    @abc.abstractmethod
    def get_designer_by_phone(self, phone: str) -> dict | None: ...
    @abc.abstractmethod
    def get_designer(self, designer_id: int) -> dict | None: ...
    @abc.abstractmethod
    def list_designers(self) -> list[dict]: ...

    # ── prospects ──────────────────────────────────────────────
    @abc.abstractmethod
    def ensure_prospect(self, phone: str, designer_phone: str = "") -> dict: ...
    @abc.abstractmethod
    def get_prospect(self, phone: str) -> dict | None: ...
    @abc.abstractmethod
    def set_prospect_opt(self, phone: str, status: str) -> None: ...
    @abc.abstractmethod
    def touch_prospect_active(self, phone: str) -> None: ...
    @abc.abstractmethod
    def get_opted_in_prospects(self, designer_id: int) -> list[dict]: ...
    @abc.abstractmethod
    def get_inactive_prospects(self, designer_id: int, days: int) -> list[dict]: ...

    # ── products (catalog) ─────────────────────────────────────
    @abc.abstractmethod
    def add_product(
        self,
        designer_id: int,
        name: str,
        description: str,
        price_cents: int,
        currency: str,
        size_class: str,
        default_preset: str,
        cutout_ref: str = "",
        width_cm: float = 0,
        height_cm: float = 0,
        depth_cm: float = 0,
        materials: str = "",
    ) -> dict: ...
    @abc.abstractmethod
    def list_products(
        self, designer_id: int, active_only: bool = True
    ) -> list[dict]: ...
    @abc.abstractmethod
    def get_product(self, product_id: int) -> dict | None: ...
    @abc.abstractmethod
    def set_product_active(self, product_id: int, active: bool) -> None: ...

    # ── room media ─────────────────────────────────────────────
    @abc.abstractmethod
    def add_room_media(
        self,
        prospect_id: int,
        designer_id: int,
        storage_ref: str,
        kind: str,
        width: int,
        height: int,
        quality: dict,
    ) -> dict: ...
    @abc.abstractmethod
    def get_room_media(self, media_id: int) -> dict | None: ...
    @abc.abstractmethod
    def list_pending_media(self, designer_id: int) -> list[dict]: ...
    @abc.abstractmethod
    def mark_media_visualized(self, media_id: int) -> None: ...

    # ── visualizations ─────────────────────────────────────────
    @abc.abstractmethod
    def create_visualization(
        self,
        prospect_id: int,
        designer_id: int,
        room_media_id: int,
        placements: list[dict],
    ) -> dict: ...
    @abc.abstractmethod
    def get_visualization(self, viz_id: int) -> dict | None: ...
    @abc.abstractmethod
    def update_visualization(self, viz_id: int, **fields) -> dict | None: ...
    @abc.abstractmethod
    def list_open_visualizations(self, designer_id: int) -> list[dict]: ...

    # ── quotes ─────────────────────────────────────────────────
    @abc.abstractmethod
    def create_quote(
        self,
        visualization_id: int,
        line_items: list[dict],
        subtotal_cents: int,
        delivery_cents: int,
        total_cents: int,
        currency: str,
    ) -> dict: ...
    @abc.abstractmethod
    def get_quote_by_visualization(self, visualization_id: int) -> dict | None: ...

    # ── orders ─────────────────────────────────────────────────
    @abc.abstractmethod
    def create_order(
        self,
        prospect_phone: str,
        designer_id: int,
        quote_id: int,
        total_cents: int,
        currency: str,
    ) -> dict: ...
    @abc.abstractmethod
    def get_order(self, order_id: int) -> dict | None: ...
    @abc.abstractmethod
    def update_order(self, order_id: int, **fields) -> dict | None: ...
    @abc.abstractmethod
    def list_open_orders(self, designer_id: int) -> list[dict]: ...
    @abc.abstractmethod
    def list_orders_for_prospect(self, prospect_phone: str) -> list[dict]: ...

    # ── campaigns ──────────────────────────────────────────────
    @abc.abstractmethod
    def create_campaign(
        self, designer_id: int, title: str, body: str, template_name: str
    ) -> dict: ...
    @abc.abstractmethod
    def mark_campaign_sent(self, campaign_id: int, sent_count: int) -> None: ...
    @abc.abstractmethod
    def add_recipient(self, campaign_id: int, prospect_id: int) -> None: ...
    @abc.abstractmethod
    def mark_recipient_sent(self, campaign_id: int, prospect_id: int) -> None: ...

    # ── follow-ups ─────────────────────────────────────────────
    @abc.abstractmethod
    def schedule_follow_up(
        self, designer_id: int, prospect_id: int, kind: str, scheduled_for
    ) -> dict: ...
    @abc.abstractmethod
    def list_due_follow_ups(self, now) -> list[dict]: ...
    @abc.abstractmethod
    def mark_follow_up_sent(self, follow_up_id: int) -> None: ...


# ═══════════════════════════════════════════════════════════════════
# In-memory implementation (tests / local dev)
# ═══════════════════════════════════════════════════════════════════
class FakeDatabase(Database):
    def __init__(self) -> None:
        self.users: dict[str, dict] = {}
        self.sessions: dict[str, dict] = {}
        self.designers: dict[int, dict] = {}
        self.designers_by_phone: dict[str, int] = {}
        self.prospects: dict[int, dict] = {}
        self.prospects_by_phone: dict[str, int] = {}
        self.products: dict[int, dict] = {}
        self.room_media: dict[int, dict] = {}
        self.visualizations: dict[int, dict] = {}
        self.quotes: dict[int, dict] = {}
        self.campaigns: dict[int, dict] = {}
        self.campaign_recipients: dict[tuple[int, int], dict] = {}
        self.follow_ups: dict[int, dict] = {}
        self.orders: dict[int, dict] = {}
        self._ids = itertools.count(1)

    # ── users ──
    def get_user(self, phone: str) -> dict | None:
        return self.users.get(phone)

    def upsert_user(self, phone: str, role: str, language: str) -> dict:
        user = self.users.get(phone)
        if user is None:
            user = {
                "id": next(self._ids),
                "phone_number": phone,
                "system_role": role,
                "preferred_language": language,
                "registration_timestamp": utcnow(),
            }
            self.users[phone] = user
        else:
            user["system_role"] = role
        return user

    def set_user_language(self, phone: str, language: str) -> None:
        if phone in self.users:
            self.users[phone]["preferred_language"] = language

    # ── sessions ──
    def get_session(self, phone: str) -> dict | None:
        s = self.sessions.get(phone)
        return json.loads(json.dumps(s)) if s else None

    def save_session(self, phone: str, session: dict) -> None:
        self.sessions[phone] = json.loads(json.dumps(session))

    # ── designers ──
    def ensure_designer(self, phone: str, display_name: str = "") -> dict:
        did = self.designers_by_phone.get(phone)
        if did is not None:
            d = self.designers[did]
            if display_name:
                d["display_name"] = display_name
            return d
        d = {
            "id": next(self._ids),
            "phone_number": phone,
            "display_name": display_name or phone,
            "created_at": utcnow(),
        }
        self.designers[d["id"]] = d
        self.designers_by_phone[phone] = d["id"]
        return d

    def get_designer_by_phone(self, phone: str) -> dict | None:
        did = self.designers_by_phone.get(phone)
        return self.designers.get(did) if did else None

    def get_designer(self, designer_id: int) -> dict | None:
        return self.designers.get(int(designer_id))

    def list_designers(self) -> list[dict]:
        return sorted(self.designers.values(), key=lambda d: d["id"])

    def _designer_id_for_phone(self, designer_phone: str) -> int | None:
        d = self.get_designer_by_phone(designer_phone)
        return d["id"] if d else None

    # ── prospects ──
    def ensure_prospect(self, phone: str, designer_phone: str = "") -> dict:
        pid = self.prospects_by_phone.get(phone)
        if pid is not None:
            p = self.prospects[pid]
            if designer_phone and not p.get("designer_id"):
                p["designer_id"] = self._designer_id_for_phone(designer_phone)
            return p
        p = {
            "id": next(self._ids),
            "phone_number": phone,
            "designer_id": self._designer_id_for_phone(designer_phone),
            "opt_status": "pending",
            "preferred_language": "en",
            "last_active_at": utcnow(),
            "created_at": utcnow(),
        }
        self.prospects[p["id"]] = p
        self.prospects_by_phone[phone] = p["id"]
        return p

    def get_prospect(self, phone: str) -> dict | None:
        pid = self.prospects_by_phone.get(phone)
        return self.prospects.get(pid) if pid else None

    def set_prospect_opt(self, phone: str, status: str) -> None:
        p = self.get_prospect(phone)
        if p is not None:
            p["opt_status"] = status

    def touch_prospect_active(self, phone: str) -> None:
        p = self.get_prospect(phone)
        if p is not None:
            p["last_active_at"] = utcnow()

    def get_opted_in_prospects(self, designer_id: int) -> list[dict]:
        return sorted(
            (
                p
                for p in self.prospects.values()
                if p["designer_id"] == designer_id and p["opt_status"] == "opted_in"
            ),
            key=lambda p: p["id"],
        )

    def get_inactive_prospects(self, designer_id: int, days: int) -> list[dict]:
        from datetime import timedelta

        cutoff = utcnow() - timedelta(days=days)
        return sorted(
            (
                p
                for p in self.prospects.values()
                if p["designer_id"] == designer_id
                and p["opt_status"] == "opted_in"
                and p["last_active_at"] < cutoff
            ),
            key=lambda p: p["id"],
        )

    # ── products ──
    def add_product(
        self,
        designer_id: int,
        name: str,
        description: str,
        price_cents: int,
        currency: str,
        size_class: str,
        default_preset: str,
        cutout_ref: str = "",
        width_cm: float = 0,
        height_cm: float = 0,
        depth_cm: float = 0,
        materials: str = "",
    ) -> dict:
        prod = {
            "id": next(self._ids),
            "designer_id": designer_id,
            "name": name,
            "description": description,
            "price_cents": int(price_cents),
            "currency": currency,
            "width_cm": float(width_cm),
            "height_cm": float(height_cm),
            "depth_cm": float(depth_cm),
            "materials": materials,
            "variants": {},
            "cutout_ref": cutout_ref,
            "size_class": size_class,
            "default_preset": default_preset,
            "active": True,
            "created_at": utcnow(),
        }
        self.products[prod["id"]] = prod
        return prod

    def list_products(
        self, designer_id: int, active_only: bool = True
    ) -> list[dict]:
        return sorted(
            (
                p
                for p in self.products.values()
                if p["designer_id"] == designer_id
                and (not active_only or p["active"])
            ),
            key=lambda p: p["id"],
        )

    def get_product(self, product_id: int) -> dict | None:
        return self.products.get(int(product_id))

    def set_product_active(self, product_id: int, active: bool) -> None:
        prod = self.products.get(int(product_id))
        if prod is not None:
            prod["active"] = active

    # ── room media ──
    def add_room_media(
        self,
        prospect_id: int,
        designer_id: int,
        storage_ref: str,
        kind: str,
        width: int,
        height: int,
        quality: dict,
    ) -> dict:
        m = {
            "id": next(self._ids),
            "prospect_id": prospect_id,
            "designer_id": designer_id,
            "storage_ref": storage_ref,
            "kind": kind,
            "width": width,
            "height": height,
            "quality": quality,
            "has_visualization": False,
            "created_at": utcnow(),
        }
        self.room_media[m["id"]] = m
        return m

    def get_room_media(self, media_id: int) -> dict | None:
        m = self.room_media.get(int(media_id))
        if m is None:
            return None
        row = dict(m)
        prospect = self.prospects.get(m["prospect_id"], {})
        row["prospect_phone"] = prospect.get("phone_number", "")
        return row

    def list_pending_media(self, designer_id: int) -> list[dict]:
        out = []
        for m in self.room_media.values():
            if m["designer_id"] == designer_id and not m["has_visualization"]:
                row = dict(m)
                prospect = self.prospects.get(m["prospect_id"], {})
                row["prospect_phone"] = prospect.get("phone_number", "")
                out.append(row)
        return sorted(out, key=lambda m: m["id"])

    def mark_media_visualized(self, media_id: int) -> None:
        m = self.room_media.get(int(media_id))
        if m is not None:
            m["has_visualization"] = True

    # ── visualizations ──
    def create_visualization(
        self,
        prospect_id: int,
        designer_id: int,
        room_media_id: int,
        placements: list[dict],
    ) -> dict:
        viz = {
            "id": next(self._ids),
            "prospect_id": prospect_id,
            "designer_id": designer_id,
            "room_media_id": room_media_id,
            "placements": placements,
            "rendered_ref": "",
            "status": "draft",
            "created_at": utcnow(),
        }
        self.visualizations[viz["id"]] = viz
        return viz

    def get_visualization(self, viz_id: int) -> dict | None:
        return self.visualizations.get(int(viz_id))

    def update_visualization(self, viz_id: int, **fields) -> dict | None:
        viz = self.visualizations.get(int(viz_id))
        if viz is None:
            return None
        allowed = {"placements", "rendered_ref", "status"}
        for k, v in fields.items():
            if k in allowed:
                viz[k] = v
        return viz

    def list_open_visualizations(self, designer_id: int) -> list[dict]:
        return sorted(
            (
                v
                for v in self.visualizations.values()
                if v["designer_id"] == designer_id and v["status"] in ("draft", "sent")
            ),
            key=lambda v: v["id"],
        )

    # ── quotes ──
    def create_quote(
        self,
        visualization_id: int,
        line_items: list[dict],
        subtotal_cents: int,
        delivery_cents: int,
        total_cents: int,
        currency: str,
    ) -> dict:
        q = {
            "id": next(self._ids),
            "visualization_id": visualization_id,
            "line_items": line_items,
            "subtotal_cents": subtotal_cents,
            "delivery_cents": delivery_cents,
            "total_cents": total_cents,
            "currency": currency,
            "status": "open",
            "created_at": utcnow(),
        }
        self.quotes[q["id"]] = q
        return q

    def get_quote_by_visualization(self, visualization_id: int) -> dict | None:
        for q in self.quotes.values():
            if q["visualization_id"] == int(visualization_id):
                return q
        return None

    # ── orders ──
    def create_order(
        self,
        prospect_phone: str,
        designer_id: int,
        quote_id: int,
        total_cents: int,
        currency: str,
    ) -> dict:
        order = {
            "id": next(self._ids),
            "prospect_phone": prospect_phone,
            "designer_id": designer_id,
            "quote_id": quote_id,
            "total_cents": int(total_cents),
            "currency": currency,
            "status": "received",
            "created_at": utcnow(),
        }
        self.orders[order["id"]] = order
        return order

    def get_order(self, order_id: int) -> dict | None:
        return self.orders.get(int(order_id))

    def update_order(self, order_id: int, **fields) -> dict | None:
        order = self.orders.get(int(order_id))
        if order is None:
            return None
        if "status" in fields:
            order["status"] = fields["status"]
        return order

    def list_open_orders(self, designer_id: int) -> list[dict]:
        return sorted(
            (
                o
                for o in self.orders.values()
                if o["designer_id"] == designer_id
                and o["status"] in ("received", "preparing", "out_for_delivery")
            ),
            key=lambda o: o["id"],
        )

    def list_orders_for_prospect(self, prospect_phone: str) -> list[dict]:
        return sorted(
            (
                o
                for o in self.orders.values()
                if o["prospect_phone"] == prospect_phone
            ),
            key=lambda o: o["id"],
        )

    # ── campaigns ──
    def create_campaign(
        self, designer_id: int, title: str, body: str, template_name: str
    ) -> dict:
        camp = {
            "id": next(self._ids),
            "designer_id": designer_id,
            "title": title,
            "body": body,
            "template_name": template_name,
            "sent_count": 0,
            "created_at": utcnow(),
        }
        self.campaigns[camp["id"]] = camp
        return camp

    def mark_campaign_sent(self, campaign_id: int, sent_count: int) -> None:
        camp = self.campaigns.get(int(campaign_id))
        if camp is not None:
            camp["sent_count"] = sent_count

    def add_recipient(self, campaign_id: int, prospect_id: int) -> None:
        self.campaign_recipients[(int(campaign_id), int(prospect_id))] = {
            "campaign_id": int(campaign_id),
            "prospect_id": int(prospect_id),
            "status": "queued",
            "sent_at": None,
        }

    def mark_recipient_sent(self, campaign_id: int, prospect_id: int) -> None:
        row = self.campaign_recipients.get((int(campaign_id), int(prospect_id)))
        if row is not None:
            row["status"] = "sent"
            row["sent_at"] = utcnow()

    # ── follow-ups ──
    def schedule_follow_up(
        self, designer_id: int, prospect_id: int, kind: str, scheduled_for
    ) -> dict:
        fu = {
            "id": next(self._ids),
            "designer_id": designer_id,
            "prospect_id": prospect_id,
            "kind": kind,
            "scheduled_for": scheduled_for,
            "status": "scheduled",
            "sent_at": None,
            "created_at": utcnow(),
        }
        self.follow_ups[fu["id"]] = fu
        return fu

    def list_due_follow_ups(self, now) -> list[dict]:
        out = []
        for fu in sorted(self.follow_ups.values(), key=lambda f: f["id"]):
            if fu["status"] == "scheduled" and fu["scheduled_for"] <= now:
                row = dict(fu)
                prospect = self.prospects.get(fu["prospect_id"], {})
                row["prospect_phone"] = prospect.get("phone_number", "")
                out.append(row)
        return out

    def mark_follow_up_sent(self, follow_up_id: int) -> None:
        fu = self.follow_ups.get(int(follow_up_id))
        if fu is not None:
            fu["status"] = "sent"
            fu["sent_at"] = utcnow()


# ═══════════════════════════════════════════════════════════════════
# Postgres implementation (Supabase / production)
# ═══════════════════════════════════════════════════════════════════
class PostgresDatabase(Database):
    """Short-lived connections per call: safe on serverless runtimes."""

    def __init__(self, database_url: str) -> None:
        if not database_url:
            raise RuntimeError("DATABASE_URL is not set")
        self._url = database_url

    def _conn(self):
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(self._url, row_factory=dict_row)

    @staticmethod
    def _one(cur) -> dict | None:
        row = cur.fetchone()
        return dict(row) if row else None

    # ── users ──
    def get_user(self, phone: str) -> dict | None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE phone_number = %s", (phone,))
            return self._one(cur)

    def upsert_user(self, phone: str, role: str, language: str) -> dict:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """INSERT INTO users (phone_number, system_role, preferred_language)
                   VALUES (%s, %s::system_role, %s)
                   ON CONFLICT (phone_number)
                   DO UPDATE SET system_role = EXCLUDED.system_role
                   RETURNING *""",
                (phone, role, language),
            )
            return self._one(cur)  # type: ignore[return-value]

    def set_user_language(self, phone: str, language: str) -> None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                "UPDATE users SET preferred_language = %s WHERE phone_number = %s",
                (language, phone),
            )

    # ── sessions ──
    def get_session(self, phone: str) -> dict | None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """SELECT phone_number, system_role, state, language, data
                   FROM chat_sessions WHERE phone_number = %s""",
                (phone,),
            )
            row = self._one(cur)
            if row is None:
                return None
            return {
                "role": row["system_role"],
                "state": row["state"],
                "lang": row["language"],
                "data": row["data"] or {},
            }

    def save_session(self, phone: str, session: dict) -> None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """INSERT INTO chat_sessions
                     (phone_number, system_role, state, language, data, updated_at)
                   VALUES (%s, %s::system_role, %s, %s, %s::jsonb, now())
                   ON CONFLICT (phone_number) DO UPDATE SET
                     state = EXCLUDED.state,
                     language = EXCLUDED.language,
                     data = EXCLUDED.data,
                     updated_at = now()""",
                (
                    phone,
                    session["role"],
                    session["state"],
                    session.get("lang", "en"),
                    json.dumps(session.get("data", {})),
                ),
            )

    # ── designers ──
    def ensure_designer(self, phone: str, display_name: str = "") -> dict:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """INSERT INTO designers (phone_number, display_name)
                   VALUES (%s, %s)
                   ON CONFLICT (phone_number) DO UPDATE SET
                     display_name = COALESCE(NULLIF(EXCLUDED.display_name, ''),
                                             designers.display_name)
                   RETURNING *""",
                (phone, display_name or phone),
            )
            return self._one(cur)  # type: ignore[return-value]

    def get_designer_by_phone(self, phone: str) -> dict | None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                "SELECT * FROM designers WHERE phone_number = %s", (phone,)
            )
            return self._one(cur)

    def get_designer(self, designer_id: int) -> dict | None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute("SELECT * FROM designers WHERE id = %s", (int(designer_id),))
            return self._one(cur)

    def list_designers(self) -> list[dict]:
        with self._conn() as c, c.cursor() as cur:
            cur.execute("SELECT * FROM designers ORDER BY id")
            return [dict(r) for r in cur.fetchall()]

    # ── prospects ──
    def ensure_prospect(self, phone: str, designer_phone: str = "") -> dict:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """INSERT INTO prospects (phone_number, designer_id)
                   VALUES (%s, (SELECT id FROM designers
                               WHERE phone_number = %s))
                   ON CONFLICT (phone_number) DO NOTHING
                   RETURNING *""",
                (phone, designer_phone or None),
            )
            row = self._one(cur)
            if row is None:
                cur.execute(
                    "SELECT * FROM prospects WHERE phone_number = %s", (phone,)
                )
                row = self._one(cur)
            if row and not row.get("designer_id") and designer_phone:
                cur.execute(
                    """UPDATE prospects SET designer_id =
                         (SELECT id FROM designers WHERE phone_number = %s)
                       WHERE phone_number = %s RETURNING *""",
                    (designer_phone, phone),
                )
                row = self._one(cur)
            return row  # type: ignore[return-value]

    def get_prospect(self, phone: str) -> dict | None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                "SELECT * FROM prospects WHERE phone_number = %s", (phone,)
            )
            return self._one(cur)

    def set_prospect_opt(self, phone: str, status: str) -> None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """UPDATE prospects SET opt_status = %s::opt_status
                   WHERE phone_number = %s""",
                (status, phone),
            )

    def touch_prospect_active(self, phone: str) -> None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                "UPDATE prospects SET last_active_at = now() WHERE phone_number = %s",
                (phone,),
            )

    def get_opted_in_prospects(self, designer_id: int) -> list[dict]:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """SELECT * FROM prospects
                   WHERE designer_id = %s AND opt_status = 'opted_in'
                   ORDER BY id""",
                (designer_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    def get_inactive_prospects(self, designer_id: int, days: int) -> list[dict]:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """SELECT * FROM prospects
                   WHERE designer_id = %s AND opt_status = 'opted_in'
                     AND last_active_at < now() - make_interval(days => %s)
                   ORDER BY id""",
                (designer_id, days),
            )
            return [dict(r) for r in cur.fetchall()]

    # ── products ──
    def add_product(
        self,
        designer_id: int,
        name: str,
        description: str,
        price_cents: int,
        currency: str,
        size_class: str,
        default_preset: str,
        cutout_ref: str = "",
        width_cm: float = 0,
        height_cm: float = 0,
        depth_cm: float = 0,
        materials: str = "",
    ) -> dict:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """INSERT INTO products
                     (designer_id, name, description, price_cents, currency,
                      width_cm, height_cm, depth_cm, materials, cutout_ref,
                      size_class, default_preset)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING *""",
                (
                    designer_id, name, description, int(price_cents), currency,
                    width_cm, height_cm, depth_cm, materials, cutout_ref,
                    size_class, default_preset,
                ),
            )
            return self._one(cur)  # type: ignore[return-value]

    def list_products(
        self, designer_id: int, active_only: bool = True
    ) -> list[dict]:
        with self._conn() as c, c.cursor() as cur:
            if active_only:
                cur.execute(
                    """SELECT * FROM products
                       WHERE designer_id = %s AND active = TRUE ORDER BY id""",
                    (designer_id,),
                )
            else:
                cur.execute(
                    "SELECT * FROM products WHERE designer_id = %s ORDER BY id",
                    (designer_id,),
                )
            return [dict(r) for r in cur.fetchall()]

    def get_product(self, product_id: int) -> dict | None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute("SELECT * FROM products WHERE id = %s", (int(product_id),))
            return self._one(cur)

    def set_product_active(self, product_id: int, active: bool) -> None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                "UPDATE products SET active = %s WHERE id = %s",
                (active, int(product_id)),
            )

    # ── room media ──
    def add_room_media(
        self,
        prospect_id: int,
        designer_id: int,
        storage_ref: str,
        kind: str,
        width: int,
        height: int,
        quality: dict,
    ) -> dict:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """INSERT INTO room_media
                     (prospect_id, designer_id, storage_ref, kind,
                      width, height, quality)
                   VALUES (%s, %s, %s, %s::media_kind, %s, %s, %s::jsonb)
                   RETURNING *""",
                (
                    prospect_id, designer_id, storage_ref, kind,
                    width, height, json.dumps(quality),
                ),
            )
            return self._one(cur)  # type: ignore[return-value]

    def get_room_media(self, media_id: int) -> dict | None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """SELECT rm.*, p.phone_number AS prospect_phone
                   FROM room_media rm
                   JOIN prospects p ON p.id = rm.prospect_id
                   WHERE rm.id = %s""",
                (int(media_id),),
            )
            return self._one(cur)

    def list_pending_media(self, designer_id: int) -> list[dict]:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """SELECT rm.*, p.phone_number AS prospect_phone
                   FROM room_media rm
                   JOIN prospects p ON p.id = rm.prospect_id
                   WHERE rm.designer_id = %s AND rm.has_visualization = FALSE
                   ORDER BY rm.id""",
                (designer_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    def mark_media_visualized(self, media_id: int) -> None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                "UPDATE room_media SET has_visualization = TRUE WHERE id = %s",
                (int(media_id),),
            )

    # ── visualizations ──
    def create_visualization(
        self,
        prospect_id: int,
        designer_id: int,
        room_media_id: int,
        placements: list[dict],
    ) -> dict:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """INSERT INTO visualizations
                     (prospect_id, designer_id, room_media_id, placements)
                   VALUES (%s, %s, %s, %s::jsonb) RETURNING *""",
                (
                    prospect_id, designer_id, room_media_id,
                    json.dumps(placements),
                ),
            )
            return self._one(cur)  # type: ignore[return-value]

    def get_visualization(self, viz_id: int) -> dict | None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                "SELECT * FROM visualizations WHERE id = %s", (int(viz_id),)
            )
            return self._one(cur)

    def update_visualization(self, viz_id: int, **fields) -> dict | None:
        allowed = {"placements", "rendered_ref", "status"}
        cols = [k for k in fields if k in allowed]
        if not cols:
            return self.get_visualization(int(viz_id))
        set_clause = ", ".join(f"{k} = %s" for k in cols)
        set_clause = set_clause.replace(
            "status = %s", "status = %s::viz_status"
        )
        params = [
            json.dumps(fields[k]) if k == "placements" else fields[k] for k in cols
        ]
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                f"""UPDATE visualizations SET {set_clause}
                    WHERE id = %s RETURNING *""",
                (*params, int(viz_id)),
            )
            return self._one(cur)

    def list_open_visualizations(self, designer_id: int) -> list[dict]:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """SELECT * FROM visualizations
                   WHERE designer_id = %s AND status IN ('draft', 'sent')
                   ORDER BY id""",
                (designer_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    # ── quotes ──
    def create_quote(
        self,
        visualization_id: int,
        line_items: list[dict],
        subtotal_cents: int,
        delivery_cents: int,
        total_cents: int,
        currency: str,
    ) -> dict:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """INSERT INTO quotes
                     (visualization_id, line_items, subtotal_cents,
                      delivery_cents, total_cents, currency)
                   VALUES (%s, %s::jsonb, %s, %s, %s, %s) RETURNING *""",
                (
                    visualization_id, json.dumps(line_items), subtotal_cents,
                    delivery_cents, total_cents, currency,
                ),
            )
            return self._one(cur)  # type: ignore[return-value]

    def get_quote_by_visualization(self, visualization_id: int) -> dict | None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """SELECT * FROM quotes WHERE visualization_id = %s
                   ORDER BY id DESC LIMIT 1""",
                (int(visualization_id),),
            )
            return self._one(cur)

    # ── orders ──
    def create_order(
        self,
        prospect_phone: str,
        designer_id: int,
        quote_id: int,
        total_cents: int,
        currency: str,
    ) -> dict:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """INSERT INTO orders
                     (prospect_phone, designer_id, quote_id,
                      total_cents, currency)
                   VALUES (%s, %s, %s, %s, %s) RETURNING *""",
                (prospect_phone, designer_id, quote_id, int(total_cents), currency),
            )
            return self._one(cur)  # type: ignore[return-value]

    def get_order(self, order_id: int) -> dict | None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute("SELECT * FROM orders WHERE id = %s", (int(order_id),))
            return self._one(cur)

    def update_order(self, order_id: int, **fields) -> dict | None:
        if "status" not in fields:
            return self.get_order(int(order_id))
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """UPDATE orders SET status = %s::order_status
                   WHERE id = %s RETURNING *""",
                (fields["status"], int(order_id)),
            )
            return self._one(cur)

    def list_open_orders(self, designer_id: int) -> list[dict]:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """SELECT * FROM orders
                   WHERE designer_id = %s
                     AND status IN ('received', 'preparing', 'out_for_delivery')
                   ORDER BY id""",
                (designer_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    def list_orders_for_prospect(self, prospect_phone: str) -> list[dict]:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                "SELECT * FROM orders WHERE prospect_phone = %s ORDER BY id",
                (prospect_phone,),
            )
            return [dict(r) for r in cur.fetchall()]

    # ── campaigns ──
    def create_campaign(
        self, designer_id: int, title: str, body: str, template_name: str
    ) -> dict:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """INSERT INTO campaigns
                     (designer_id, title, body, template_name)
                   VALUES (%s, %s, %s, %s) RETURNING *""",
                (designer_id, title, body, template_name),
            )
            return self._one(cur)  # type: ignore[return-value]

    def mark_campaign_sent(self, campaign_id: int, sent_count: int) -> None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                "UPDATE campaigns SET sent_count = %s WHERE id = %s",
                (sent_count, int(campaign_id)),
            )

    def add_recipient(self, campaign_id: int, prospect_id: int) -> None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """INSERT INTO campaign_recipients (campaign_id, prospect_id)
                   VALUES (%s, %s) ON CONFLICT DO NOTHING""",
                (int(campaign_id), int(prospect_id)),
            )

    def mark_recipient_sent(self, campaign_id: int, prospect_id: int) -> None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """UPDATE campaign_recipients SET status = 'sent', sent_at = now()
                   WHERE campaign_id = %s AND prospect_id = %s""",
                (int(campaign_id), int(prospect_id)),
            )

    # ── follow-ups ──
    def schedule_follow_up(
        self, designer_id: int, prospect_id: int, kind: str, scheduled_for
    ) -> dict:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """INSERT INTO follow_ups
                     (designer_id, prospect_id, kind, scheduled_for)
                   VALUES (%s, %s, %s, %s) RETURNING *""",
                (designer_id, prospect_id, kind, scheduled_for),
            )
            return self._one(cur)  # type: ignore[return-value]

    def list_due_follow_ups(self, now) -> list[dict]:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """SELECT f.*, p.phone_number AS prospect_phone
                   FROM follow_ups f
                   JOIN prospects p ON p.id = f.prospect_id
                   WHERE f.status = 'scheduled' AND f.scheduled_for <= %s
                   ORDER BY f.id""",
                (now,),
            )
            return [dict(r) for r in cur.fetchall()]

    def mark_follow_up_sent(self, follow_up_id: int) -> None:
        with self._conn() as c, c.cursor() as cur:
            cur.execute(
                """UPDATE follow_ups SET status = 'sent', sent_at = now()
                   WHERE id = %s""",
                (int(follow_up_id),),
            )

-- RoomLens schema (PostgreSQL / Supabase)
--
-- Roles: designers (business owners) and prospects (customers).
-- Every conversational session hydrates from chat_sessions; the app
-- itself is stateless.

-- ── enums ──────────────────────────────────────────────────────────
DO $$ BEGIN CREATE TYPE system_role AS ENUM ('designer', 'prospect');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE opt_status AS ENUM ('pending', 'opted_in', 'opted_out');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE media_kind AS ENUM ('photo', 'video');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE viz_status AS ENUM ('draft', 'sent', 'ordered', 'archived');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE quote_status AS ENUM ('open', 'accepted', 'expired');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE order_status AS ENUM
  ('received', 'preparing', 'out_for_delivery', 'delivered', 'cancelled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE followup_status AS ENUM ('scheduled', 'sent', 'cancelled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ── users & sessions ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
  id                    BIGSERIAL PRIMARY KEY,
  phone_number          TEXT NOT NULL UNIQUE,          -- E.164
  system_role           system_role NOT NULL,
  preferred_language    TEXT NOT NULL DEFAULT 'en',
  registration_timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users (phone_number);

CREATE TABLE IF NOT EXISTS chat_sessions (
  phone_number  TEXT PRIMARY KEY,                      -- E.164
  system_role   system_role,
  state         TEXT NOT NULL,
  language      TEXT NOT NULL DEFAULT 'en',
  data          JSONB NOT NULL DEFAULT '{}'::jsonb,
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── designers & prospects ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS designers (
  id            BIGSERIAL PRIMARY KEY,
  phone_number  TEXT NOT NULL UNIQUE,
  display_name  TEXT NOT NULL DEFAULT '',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS prospects (
  id                BIGSERIAL PRIMARY KEY,
  phone_number      TEXT NOT NULL UNIQUE,
  designer_id       BIGINT REFERENCES designers (id),
  opt_status        opt_status NOT NULL DEFAULT 'pending',
  preferred_language TEXT NOT NULL DEFAULT 'en',
  last_active_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_prospects_designer
  ON prospects (designer_id);

-- ── catalog ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
  id              BIGSERIAL PRIMARY KEY,
  designer_id     BIGINT NOT NULL REFERENCES designers (id) ON DELETE CASCADE,
  name            TEXT NOT NULL,
  description     TEXT NOT NULL DEFAULT '',
  price_cents     INTEGER NOT NULL CHECK (price_cents > 0),
  currency        TEXT NOT NULL DEFAULT 'USD',
  width_cm        NUMERIC NOT NULL DEFAULT 0,
  height_cm       NUMERIC NOT NULL DEFAULT 0,
  depth_cm        NUMERIC NOT NULL DEFAULT 0,
  materials       TEXT NOT NULL DEFAULT '',
  variants        JSONB NOT NULL DEFAULT '{}'::jsonb,
  cutout_ref      TEXT NOT NULL DEFAULT '',   -- MediaStore ref to RGBA PNG
  size_class      TEXT NOT NULL DEFAULT 'floor',  -- floor | wall | tabletop
  default_preset  TEXT NOT NULL DEFAULT 'floor-center',
  active          BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- High-frequency lookup: designer's live catalog.
CREATE INDEX IF NOT EXISTS idx_products_active
  ON products (designer_id) WHERE active = TRUE;

-- ── room media (prospect uploads) ──────────────────────────────────
CREATE TABLE IF NOT EXISTS room_media (
  id                BIGSERIAL PRIMARY KEY,
  prospect_id       BIGINT NOT NULL REFERENCES prospects (id) ON DELETE CASCADE,
  designer_id       BIGINT REFERENCES designers (id),
  storage_ref       TEXT NOT NULL,              -- MediaStore ref
  kind              media_kind NOT NULL DEFAULT 'photo',
  width             INTEGER NOT NULL DEFAULT 0,
  height            INTEGER NOT NULL DEFAULT 0,
  quality           JSONB NOT NULL DEFAULT '{}'::jsonb,
  has_visualization BOOLEAN NOT NULL DEFAULT FALSE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- High-frequency lookup: rooms still waiting for a visualization.
CREATE INDEX IF NOT EXISTS idx_media_pending
  ON room_media (designer_id) WHERE has_visualization = FALSE;

-- ── visualizations ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS visualizations (
  id            BIGSERIAL PRIMARY KEY,
  prospect_id   BIGINT NOT NULL REFERENCES prospects (id) ON DELETE CASCADE,
  designer_id   BIGINT NOT NULL REFERENCES designers (id) ON DELETE CASCADE,
  room_media_id BIGINT NOT NULL REFERENCES room_media (id) ON DELETE CASCADE,
  placements    JSONB NOT NULL DEFAULT '[]'::jsonb,
  rendered_ref  TEXT NOT NULL DEFAULT '',     -- MediaStore ref to JPEG
  status        viz_status NOT NULL DEFAULT 'draft',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- High-frequency lookup: visualizations still in play.
CREATE INDEX IF NOT EXISTS idx_viz_open
  ON visualizations (designer_id)
  WHERE status IN ('draft', 'sent');

-- ── quotes & orders ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS quotes (
  id                BIGSERIAL PRIMARY KEY,
  visualization_id  BIGINT NOT NULL REFERENCES visualizations (id)
                    ON DELETE CASCADE,
  line_items        JSONB NOT NULL DEFAULT '[]'::jsonb,
  subtotal_cents    INTEGER NOT NULL DEFAULT 0,
  delivery_cents    INTEGER NOT NULL DEFAULT 0,
  total_cents       INTEGER NOT NULL DEFAULT 0,
  currency          TEXT NOT NULL DEFAULT 'USD',
  status            quote_status NOT NULL DEFAULT 'open',
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS orders (
  id              BIGSERIAL PRIMARY KEY,
  prospect_phone  TEXT NOT NULL,
  designer_id     BIGINT NOT NULL REFERENCES designers (id) ON DELETE CASCADE,
  quote_id        BIGINT REFERENCES quotes (id),
  total_cents     INTEGER NOT NULL DEFAULT 0,
  currency        TEXT NOT NULL DEFAULT 'USD',
  status          order_status NOT NULL DEFAULT 'received',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_orders_open
  ON orders (designer_id)
  WHERE status IN ('received', 'preparing', 'out_for_delivery');

-- ── marketing ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS campaigns (
  id            BIGSERIAL PRIMARY KEY,
  designer_id   BIGINT NOT NULL REFERENCES designers (id) ON DELETE CASCADE,
  title         TEXT NOT NULL,
  body          TEXT NOT NULL,
  template_name TEXT NOT NULL DEFAULT '',  -- Meta pre-approved template
  sent_count    INTEGER NOT NULL DEFAULT 0,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS campaign_recipients (
  campaign_id BIGINT NOT NULL REFERENCES campaigns (id) ON DELETE CASCADE,
  prospect_id BIGINT NOT NULL REFERENCES prospects (id) ON DELETE CASCADE,
  status      TEXT NOT NULL DEFAULT 'queued',   -- queued | sent | failed
  sent_at     TIMESTAMPTZ,
  PRIMARY KEY (campaign_id, prospect_id)
);

CREATE TABLE IF NOT EXISTS follow_ups (
  id            BIGSERIAL PRIMARY KEY,
  designer_id   BIGINT NOT NULL REFERENCES designers (id) ON DELETE CASCADE,
  prospect_id   BIGINT NOT NULL REFERENCES prospects (id) ON DELETE CASCADE,
  kind          TEXT NOT NULL,                  -- nudge | winback | reminder
  scheduled_for TIMESTAMPTZ NOT NULL,
  status        followup_status NOT NULL DEFAULT 'scheduled',
  sent_at       TIMESTAMPTZ,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_followups_due
  ON follow_ups (scheduled_for) WHERE status = 'scheduled';

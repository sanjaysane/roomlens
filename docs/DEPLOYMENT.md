# Deployment

## Docker Compose (recommended)

```bash
docker compose up --build
```

This starts two services: `db` (postgres:16-alpine, schema from
`sql/schema.sql` applied automatically via `/docker-entrypoint-initdb.d`) and
`app` (the FastAPI service on port 8000). Both have health checks; the app
waits for the DB to be healthy before booting. Media persists in the
`mediadata` volume at `/app/data/media`.

## Environment variables

| Variable | Default | Required for prod? |
|---|---|---|
| `DATABASE_URL` | (fake DB) | Yes — e.g. `postgresql://roomlens:secret@db:5432/roomlens` |
| `WEBHOOK_VERIFY_TOKEN` | `roomlens-dev-verify` | Yes — long random secret; Meta must send the same value |
| `WHATSAPP_TOKEN` | — | Yes — Meta WhatsApp Cloud API token |
| `WHATSAPP_PHONE_NUMBER_ID` | — | Yes — the sender's phone number ID |
| `WHATSAPP_API_BASE` | `https://graph.facebook.com/v21.0` | No |
| `MEDIA_BACKEND` | `local` | No (`local` or `supabase`) |
| `MEDIA_DIR` | `./media` | No (local backend only) |
| `DEFAULT_LANGUAGE` | `en` | No |
| `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` / `SUPABASE_BUCKET` | — | Only with `MEDIA_BACKEND=supabase` |

Copy `.env.example` to `.env` and fill in values. In compose, sensitive
values are passed via `${VAR:-fallback}` in `docker-compose.yml`.

## Meta webhook setup

1. Create a Meta app with the WhatsApp product; add a phone number and note
   its **Phone Number ID** (`WHATSAPP_PHONE_NUMBER_ID`) and a **permanent
   access token** (`WHATSAPP_TOKEN`).
2. In the app dashboard → WhatsApp → Configuration → Webhook:
   - **Callback URL:** `https://<your-public-host>/webhook`
   - **Verify token:** exactly your `WEBHOOK_VERIFY_TOKEN` value
   - Click Verify. The app answers the `hub.mode`/`hub.challenge` handshake
     with `GET /webhook`; a token mismatch returns `403 forbidden`.
3. Subscribe to the **`messages`** field on your WhatsApp Business Account.

## TLS / tunnel

Meta requires a public HTTPS callback URL. The app itself speaks plain HTTP on
port 8000. Options:

- **Dev:** a tunnel such as `ngrok http 8000` or `cloudflared tunnel --url http://localhost:8000`,
  then use the tunnel's HTTPS URL as the callback.
- **Prod:** terminate TLS in a reverse proxy (Caddy, nginx) or run behind a
  load balancer with a real certificate. The app is stateless, so multiple
  containers can sit behind one endpoint.

## Database schema

Fresh databases get the schema automatically (compose init script, CI
`psql -f sql/schema.sql`). For an existing database:

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/schema.sql
```

The script is idempotent (enums use `DO … EXCEPTION WHEN duplicate_object`,
all objects `IF NOT EXISTS`).

## Health checks

- `GET /health` → `{"ok": true, "service": "roomlens"}`. Docker and compose
  probe it every 30 s. Under load on a single worker it can take ~1.5 s
  (queueing behind webhook POSTs — see SCALE.md); use multi-worker uvicorn if
  your orchestrator is health-check sensitive.
- `GET /webhook` with no params returns 403 — that is correct behavior, not a
  failure.

## Production checklist

- [ ] `WEBHOOK_VERIFY_TOKEN` is a long random secret, unique per environment.
- [ ] Tokens/keys are in the environment (or a secret manager), never in the image or repo.
- [ ] **Secret rotation + custody (v3 F-11).** Rotate `WEBHOOK_VERIFY_TOKEN`,
      the Meta App Secret, and the WhatsApp token on a fixed cadence (every
      90 days, or immediately on any team change or suspected leak). One
      named human holds Meta **app admin**; the pilot runs on a **separate
      Meta app** from production, so pilot experiments (template drafts,
      webhook URL changes) can never touch the production number's
      configuration or billing.
- [ ] Run multiple uvicorn workers (`--workers N`); the runtime is stateless.
- [ ] Use a pooled DB connection (PgBouncer or psycopg pool) — per-request
      connections dominate webhook latency today (SCALE.md).
- [ ] **Webhook signature validation: not yet implemented (known gap).**
      Meta signs every `POST /webhook` with `X-Hub-Signature-256` (HMAC-SHA256
      of the body using your App Secret). Implement it before exposing the
      webhook publicly. Why it matters: without it, anyone who discovers your
      callback URL can POST forged payloads — impersonating prospects,
      triggering renders, firing outbound WhatsApp sends, or spamming `STOP`.
      The handler is always-200 and the send surface is real, so forgery is
      cheap abuse. Add the check, reject mismatches with 403, then remove this
      item from the list.
- [ ] Create and get Meta approval for your message **templates**
      (marketing and win-back messages are blocked without them). Per-language
      templates are needed if you want non-`en_US` business-initiated sends.
- [ ] Back up the DB and the media volume/store on a schedule.
- [ ] Pin resource limits (Pillow compositing and ffmpeg are CPU-heavy;
      renders queue behind webhooks on a single worker).

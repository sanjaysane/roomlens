# Architecture

RoomLens is a WhatsApp conversational app: prospects send room photos, designers
place products into them by tapping digits, prospects order the same way. The
design center is a **declarative state machine** running on a **stateless
runtime** with **swappable adapters** (real for prod, fakes for tests/dev).

## Components

| Module | Responsibility |
|---|---|
| `src/main.py` | FastAPI app; `GET /health`, `GET /webhook` (Meta verification), `POST /webhook` (inbound messages, always 200) |
| `src/state_machine.py` | Declarative `(role, state) → handler` route table; hydration, global `STOP` / language-command pre-dispatch, corrupt-state reset |
| `src/handlers/prospect.py` | Prospect loop: role pick → designer pick → photo → waiting → review → order → tracking |
| `src/handlers/designer.py` | Designer loop: studio setup → home hub → catalog → studio → orders → marketing |
| `src/composite.py` | Preset placement, price strip, JPEG render; quality gate; ffmpeg first-frame extraction + Ken Burns clips |
| `src/media.py` | `WhatsAppMedia` (Graph download/upload) + `MediaStore` (local disk / Supabase) seams |
| `src/whatsapp.py` | `WhatsAppClient` seam: text, image, and pre-approved **template** sends |
| `src/db.py` | `Database` seam: `PostgresDatabase` (psycopg3) / `FakeDatabase` (in-memory) |
| `src/marketing.py` | Opt-in-gated campaign / follow-up / win-back fan-out; `STOP` suppression |
| `src/i18n.py` | Locale loading + resolution (`en`/`es`/`hi`, 85 keys each) |
| `src/pricing.py` | Money formatting, quote line-item text |
| `src/context.py` | `Ctx` (reply/send helpers, session persistence), `parse_choice` |
| `src/models.py` | Roles, states, placement presets, language options — the shared contract |

## Webhook flow (sequence)

```
Meta Cloud API ──POST /webhook──▶ main.receive_webhook
                                        │ parse nested payload → (phone, text, msg_type, media_id)
                                        ▼
                                  state_machine.process_incoming
                                        │ 1. get_user / get_session (hydrate)
                                        │ 2. resolve language
                                        │ 3. global commands (language menu, STOP)
                                        │ 4. ROUTES[(role, state)] → handler(ctx)
                                        │ 5. handler replies + persists session
                                        ▼
                                  {"ok": True}   (never a 5xx — see below)
Meta Cloud API ◀──WhatsAppClient (text/image/template)──┘
```

The process holds **no conversation state**: every webhook hydrates the session
from `chat_sessions` and persists before returning. Errors in a single message
are caught, logged (`[roomlens] handler error for …`), and the webhook still
returns 200 — Meta retries aggressively on non-2xx, so failing loudly would
replay the same message.

## State machine

Every conversation is `(role, state) → handler`. Key states:

**Prospect** (senior-accessible, single-digit replies throughout):

| State | What happens |
|---|---|
| `prospect_new` | Welcome: `1` = I'm a designer, `2` = preview furniture |
| `prospect_pick_designer` | Pick a studio by number |
| `prospect_photo` / `prospect_retake` | Send room photo/video; quality gate runs here |
| `prospect_waiting` | Preview being prepared; opt-in question (`1` yes / `2` no) |
| `prospect_review` | `1` order, `2` change placement, `3` change product, `4` talk to designer |
| `prospect_order_confirm` | `1` confirm 👍, `2` cancel 👎 |
| `prospect_tracking` | Open order statuses |

**Designer** (hub + five loops):

| State | What happens |
|---|---|
| `designer_new` | One-time studio-name setup (typed) |
| `designer_home` | Hub: `1` catalog, `2` studio, `3` orders, `4` marketing |
| `designer_catalog*` | List/add/deactivate products; typed name + price, digit size class |
| `designer_studio*` | Pending room photos → pick product → pick preset → bigger/smaller/send |
| `designer_orders*` | Inbound queue; `1` preparing, `2` shipped, `3` delivered |
| `designer_marketing*` | Campaign (typed body) → confirm → send to opted-in only |

Global pre-dispatch (work from **any** state):

- Language command (`language` / `idioma` / `भाषा` / `lang` / `lenguaje`) opens
  the language menu and returns to the interrupted state afterward.
- `STOP` from any prospect state → instant opt-out from all marketing.
- Unknown/corrupt state → safe reset to `designer_home` / `prospect_new`.

Typing is only ever required at setup: studio name, product name/price, and
campaign body. Core prospect flows need no typing at all.

## DB schema overview

PostgreSQL 16 (`sql/schema.sql`; enums, partial indexes on hot lookups):

- **Identity:** `users` (phone ↔ role, language), `chat_sessions` (the hydrated
  session row: role, state, language, JSONB `data`), `designers`, `prospects`
  (`opt_status`: `pending` / `opted_in` / `opted_out`).
- **Commerce:** `products` (price in cents, dimensions, `cutout_ref` to an RGBA
  PNG, size class, default preset), `room_media` (uploaded rooms + `quality`
  JSONB from the gate), `visualizations` (placements JSONB, `rendered_ref`,
  `draft → sent → ordered`), `quotes` (line items, subtotal/delivery/total),
  `orders` (`received → preparing → out_for_delivery → delivered`).
- **Marketing:** `campaigns` + `campaign_recipients`, `follow_ups` with a due
  index (`kind`: `nudge` | `winback` | `reminder`).

The DB holds **references** to media (e.g. `local:rooms/room-…jpg`); bytes live
in the media store.

## Adapters and fakes

Every external seam is an ABC with a fake twin, wired in
`main.build_runtime()` from the environment:

| Seam | Real | Fake |
|---|---|---|
| Database | `PostgresDatabase` (psycopg3) when `DATABASE_URL` is set | `FakeDatabase` (in-memory dicts) |
| WhatsApp send | `MetaWhatsAppClient` (graph.facebook.com) when `WHATSAPP_TOKEN` + `WHATSAPP_PHONE_NUMBER_ID` set | `FakeWhatsAppClient` (records outbound messages for test assertions) |
| WhatsApp media | `GraphWhatsAppMedia` | `FakeWhatsAppMedia` (pre-register `media_id → bytes`) |
| Media store | `SupabaseMediaStore` when `MEDIA_BACKEND=supabase` | `LocalMediaStore` (disk under `MEDIA_DIR`) |

No credentials in the repo; everything comes from env vars. Tests and local
dev boot with zero credentials.

## i18n approach

Locales live in `locales/{en,es,hi}.json` — **85 keys each, parity-tested**
(`tests/test_locales.py` fails if any key is missing or extra in any language).
Resolution order per message: prospect row language → session language →
user `preferred_language` → `DEFAULT_LANGUAGE` (`en`). The language command
works from any state and returns to it; template sends default to `en_US`
because per-language templates need separate Meta approval.

## Media pipeline

Inbound: Meta media id → `WhatsAppMedia.download` → bytes → `assess_quality`
(gate) → `MediaStore.save` → ref stored in `room_media`. Video messages go
through `extract_first_frame` first (ffmpeg); an undecodable video yields an
honest "send a still photo" reply.

Outbound: `render_visualization` composites RGBA product cutouts onto the room
at a preset, appends a price strip, emits JPEG. `make_clip` optionally builds a
3-second Ken Burns MP4. `WhatsAppMedia.upload` returns a media id used by
`send_image`/`send_template`.

> **Not AR.** Placement is 2D presets (`floor-center`, `left-wall`,
> `right-wall`, `wall-hang`) scaled to fractions of the photo width. No plane
> detection, no depth estimation, no perspective reconstruction. Cutouts are
> designer-uploaded RGBA PNGs — background removal is explicitly out of scope
> for v0.1.0.

## Outbound templates

Business-initiated messages (campaigns, follow-ups, win-backs) go through
`marketing.send_marketing`, the single choke point, and only to prospects with
`opt_status = 'opted_in'`, and only via `send_template` with a **Meta
pre-approved template name** (default `roomlens_update`). Anyone else is
silently skipped — suppression is a tested feature. See DEPLOYMENT.md for the
template-approval requirement.

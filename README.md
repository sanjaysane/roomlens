# RoomLens

[![CI](https://github.com/sanjaysane/roomlens/actions/workflows/ci.yml/badge.svg)](https://github.com/sanjaysane/roomlens/actions/workflows/ci.yml)
[![CodeQL](https://github.com/sanjaysane/roomlens/actions/workflows/codeql.yml/badge.svg)](https://github.com/sanjaysane/roomlens/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%E2%80%933.13-blue.svg)](https://www.python.org/)

WhatsApp-first furniture visualization and ordering for interior designers — no app install, no account, no form to fill out. A prospect sends a photo of their room over WhatsApp, the designer places catalog products into it with a few numbered replies, the prospect sees their own room with the furniture in it, and orders with a single digit. Every core flow is designed for seniors: numbered menus, 👍/👎 confirmations, and no required free-form typing.

## Quick start (one command)

```bash
docker compose up --build
```

The app listens on `http://localhost:8000`. Expose it to Meta with a tunnel
(see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)) and set `WEBHOOK_VERIFY_TOKEN`
before pointing a WhatsApp webhook at it.

## Manual quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # fill in WHATSAPP_TOKEN etc.

# database: apply the schema once
psql -h localhost -U roomlens -d roomlens -f sql/schema.sql

# run (no env vars = in-memory fakes, boots instantly for dev)
uvicorn src.main:app --port 8000
```

Run the tests and linter:

```bash
pytest                     # 69 passed, 1 skipped without DATABASE_URL
ruff check src tests       # clean
locust -f locustfile.py    # load profile, see docs/SCALE.md
```

## Features

- **Two roles, one chat.** Designers (catalog, studio, orders, marketing) and
  prospects (photo → preview → order) share the same WhatsApp number; the
  state machine routes by role.
- **Senior-accessible dialogue.** Single-digit replies everywhere, 👍/👎 order
  confirm, emoji-light prompts, no required typing in core flows. Typing is
  only needed at setup (studio name, product name, price, campaign text).
- **Preset-based visualization.** Products are placed at `floor-center`,
  `left-wall`, `right-wall`, or `wall-hang` with bigger/smaller scale adjust.
- **Honest quality gate.** Dark, blurry, too-small, or unreadable room photos
  get a polite retake request — never a misleading overlay.
- **Video rooms.** Send a short clip; the first frame is extracted via ffmpeg
  and composited. Undecodable video → an honest "send a still photo" reply.
- **Ken Burns clips.** Optional short pan/zoom MP4 renders from a still.
- **Quotes & orders.** Line items, delivery, totals in cents; order status
  tracking (`received → preparing → out_for_delivery → delivered`).
- **Opt-in marketing.** Campaigns, follow-ups, win-backs go only to opted-in
  prospects via Meta pre-approved templates. `STOP` opts out instantly.
- **i18n parity.** English, Spanish, Hindi — full parity, tested. Marathi is a declared partial locale with English fallback.
- **Stateless runtime.** Every webhook hydrates the session from PostgreSQL
  and persists before returning; horizontal scaling is just more workers.

## ⚠️ Honest limits: this is not AR

RoomLens does **2D preset-based compositing**, not augmented reality:

- No plane or surface detection; no depth estimation.
- No perspective reconstruction or camera-calibrated scale.
- Placed products are positioned by fixed presets and sized by fractions of
  the room photo's width — sizes are illustrative, not guaranteed real-world
  scale.
- The quality gate is heuristic (brightness / Laplacian blur / resolution),
  not a camera-fidelity promise.

We document these limits instead of marketing past them.

## Scale snapshot (measured, 2026-09-05)

50 concurrent users, 2 minutes, single uvicorn worker, real PostgreSQL 16 —
4,183 `POST /webhook` requests, **0 failures**:

| Endpoint | req | avg | p50 | p95 | p99 |
|---|---|---|---|---|---|
| `POST /webhook` | 4,183 | 576 ms | 480 ms | 1.2 s | 2.2 s |
| `GET /health` | 479 | 1,542 ms | 1.5 s | 3.1 s | 4.2 s |

`GET /health` p50 of 1.5 s under load is single-worker queueing, not endpoint
cost (the endpoint is a constant JSON body with no DB access). Full detail and
reproduction steps: [docs/SCALE.md](docs/SCALE.md).

## Repo map

```
src/            FastAPI app, state machine, handlers, compositing, media, i18n
sql/schema.sql  PostgreSQL 16 schema (applied by compose + CI)
locales/        en / es / hi — full parity, parity-tested; mr — partial, EN fallback
tests/          pytest suite (unit, flows, quality, locales, webhook, real PG)
docs/           SCALE.md, ARCHITECTURE.md, DEPLOYMENT.md, FAQ, guides
docker-compose.yml   app + postgres:16-alpine, schema auto-applied
locustfile.py   load-test workload (Meta-shaped webhook traffic)
```

## Docs

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — components, state machine, schema
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — env vars, Meta webhook setup, prod checklist
- [docs/SCALE.md](docs/SCALE.md) — measured performance numbers
- [docs/FAQ.md](docs/FAQ.md) — 12+ questions (AR? languages? cost? Meta approval?)
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- [How-to guides](docs/how-to/) — designer onboarding, first visualization, media retention
- [Video scripts](docs/videos/) — presenter scripts for walkthrough videos

## License

MIT — see [LICENSE](LICENSE). © 2026 Sanjay Sane.

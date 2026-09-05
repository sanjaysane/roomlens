# Video script: Deployment (~5 min)

Presenter tone: direct, technical, aimed at a developer deploying for a
studio.

---

## Scene 1 — What you're deploying (0:00–0:40)

**On-screen:** architecture diagram — Meta Cloud API → FastAPI webhook →
PostgreSQL + media store → WhatsApp replies.

**Presenter:** "RoomLens is two containers: a FastAPI app and PostgreSQL 16.
The app is stateless — every webhook hydrates the chat session from the
database — so scaling is just adding workers. Let's get it running."

## Scene 2 — One-command start (0:40–1:30)

**On-screen:** terminal. `docker compose up --build`. Logs show postgres
ready, app listening on 8000. `curl localhost:8000/health`.

**Presenter:** "Clone the repo and run docker compose up --build. The schema
applies itself from sql/schema.sql, and the app waits for the database to be
healthy. Hit slash-health — you get ok-true. With no credentials set, it
boots on in-memory fakes, so you can click through every conversation flow
locally before touching Meta."

## Scene 3 — Environment variables (1:30–2:20)

**On-screen:** `.env` file being filled: `DATABASE_URL`,
`WEBHOOK_VERIFY_TOKEN`, `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`.

**Presenter:** "Copy dot-env-example to dot-env. Four variables matter most:
the database URL, a long random webhook verify token, and your WhatsApp token
plus phone number ID from the Meta dashboard. Media stays local by default;
flip MEDIA_BACKEND to supabase and add the Supabase keys for production
storage. Never commit a real dot-env."

## Scene 4 — The Meta webhook (2:20–3:30)

**On-screen:** Meta app dashboard → WhatsApp → Configuration. Paste callback
URL, paste verify token, click Verify — success. Subscribe to `messages`.
Terminal showing a tunnel (`cloudflared tunnel --url http://localhost:8000`).

**Presenter:** "Meta needs a public HTTPS URL, so for dev, run a tunnel and
use its HTTPS address. In the WhatsApp configuration, set the callback URL to
your host slash-webhook and the verify token to the exact value from your
env — character for character. Click Verify: the app answers the handshake
and returns the challenge. Then subscribe to the messages field. If
verification 403s, it's a token mismatch — check for trailing spaces."

## Scene 5 — Message templates (3:30–4:10)

**On-screen:** WhatsApp Manager → Message templates → create `roomlens_update`,
submit, approved badge.

**Presenter:** "One Meta requirement people miss: any message the business
sends first — campaigns, win-backs — needs a pre-approved template. Create
yours in the WhatsApp Manager and wait for approval before you promise a
studio their first campaign. Conversations the customer starts need no
template."

## Scene 6 — Production checklist (4:10–4:50)

**On-screen:** checklist from docs/DEPLOYMENT.md scrolling: multi-worker,
pooled DB, signature validation flagged.

**Presenter:** "Before going live: randomize the verify token per
environment, run multiple uvicorn workers, and put a connection pool in front
of Postgres — per-request connections dominate webhook latency today. And
note the known gap: webhook signature validation isn't implemented yet, so
don't expose the endpoint publicly until it is, or gate it to Meta's IP
ranges. Measured numbers — thirty-five requests a second on one worker with
zero failures — are in docs/SCALE.md."

## Scene 7 — Close (4:50–5:00)

**On-screen:** links: docs/DEPLOYMENT.md, docs/SCALE.md, docs/TROUBLESHOOTING.md.

**Presenter:** "That's it — compose up, env, tunnel, verify, templates.
Troubleshooting guide and the full production checklist are linked below."

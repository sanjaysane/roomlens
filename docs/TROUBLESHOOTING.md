# Troubleshooting

## Webhook verification returns 403

**Symptom:** Meta's webhook setup shows "verification failed"; `GET /webhook`
returns `forbidden`.

**Cause:** `hub.verify_token` from Meta doesn't match `WEBHOOK_VERIFY_TOKEN`.

**Fix:**
1. Check the value the app actually sees: with compose,
   `docker compose exec app env | grep WEBHOOK_VERIFY_TOKEN`.
2. Make sure the token you typed into the Meta dashboard matches **exactly**
   (no trailing spaces — dashboards love to add them).
3. Restart the app after changing env vars (`docker compose up -d --force-recreate app`).

## Media downloads fail ("unreadable" retake on every photo)

**Symptom:** every image gets the "couldn't read that photo" reply.

**Causes / fixes:**
- `WHATSAPP_TOKEN` expired or revoked → generate a new token in the Meta
  dashboard; media download hits `/{media-id}` then the file URL with a
  Bearer token, and both fail at 401.
- `WHATSAPP_PHONE_NUMBER_ID` wrong → uploads (`send_image`) fail even when
  downloads work; double-check the ID against the dashboard.
- Transient Meta outage → the handler logs `[roomlens] handler error` and
  replies with the retake ask rather than 500ing. Retry later.

## Photos keep getting rejected (by design)

**Symptom:** "too dark / too blurry / too small" retake loop.

This is the quality gate working as intended — it refuses to composite onto a
photo that would produce a misleading preview. Thresholds in `src/composite.py`:

| Check | Rejects when |
|---|---|
| Brightness | mean grayscale < 45 |
| Blur | Laplacian variance < 90 |
| Size | smallest side < 400 px |
| Unreadable | bytes don't decode as an image |

**Fix for the user:** more light, hold still, step back, send the original
(not a screenshot of a screenshot). See `docs/how-to/first-visualization.md`
for photo tips.

## Database connection refused

**Symptom:** app logs show connection errors on boot or per request.

- With compose: `docker compose logs db` — wait for `database system is ready`.
  The app has `depends_on: db: condition: service_healthy`, so a premature
  start is unlikely but possible if the health check is misconfigured.
- Manual: verify `DATABASE_URL` (`psql "$DATABASE_URL" -c "select 1"`), check
  the host/port, and confirm `sql/schema.sql` was applied (`\dt` should list
  `users`, `chat_sessions`, `products`, …).

## ffmpeg missing → video path disabled

**Symptom:** videos always get the "send a still photo" reply.

`extract_first_frame` and `make_clip` return `None` when `ffmpeg` isn't on
`PATH` — by design, never a crash. The Docker image and CI install ffmpeg.
If you installed manually, `apt-get install ffmpeg` (or `brew install ffmpeg`)
and restart. Photo flow is unaffected.

## Locale key errors

**Symptom:** `KeyError` on a message key, or a user sees a raw key name.

**Fix:** add the key to **all three** locale files (`en`, `es`, `hi` — 87 keys
each). `pytest tests/test_locales.py` catches parity breaks; run it before
pushing. See CONTRIBUTING.md.

## Compose health check failing

**Symptom:** `docker compose ps` shows the app `unhealthy`.

The health check hits `http://127.0.0.1:8000/health`. Causes:

1. App not listening yet — give it the 10 s `start_period`, then check
   `docker compose logs app`.
2. Port conflict — something else on 8000. Change the published port in
   `docker-compose.yml`.
3. Under heavy load a single worker can take ~1.5 s to answer `/health`
   (queueing, not failure — see SCALE.md). If your orchestrator kills on slow
   checks, run more workers or lengthen the timeout.

## Backup / restore drill (v3 F-07)

The DB holds the refs, the media store holds the irreplaceable customer
originals — a ref without its file (or a file without its ref) is silent
corruption. Milestones require scheduled backups plus a **rehearsed**
restore before the first paid pilot (v1.2 growth gates at the latest).

**What to back up:** the PostgreSQL database (`pg_dump`) and the media
store directory/volume (local `MEDIA_DIR`, or the Supabase bucket in prod).

**Media-ref integrity check** (run after every restore rehearsal):

```bash
# every media ref in the DB must resolve to a real file, and every file
# must have a DB ref — orphans in either direction are corruption
python - <<'PY'
# pseudocode against the schema in sql/schema.sql:
#   orphans = files_in_store - refs_in_db; missing = refs_in_db - files_in_store
#   assert not orphans and not missing, (orphans, missing)
PY
```

**Drill:** restore to a scratch environment, run the integrity check, and
send one end-to-end test visualization through the restored stack. Document
the date and the result in the pilot log — an unrehearsed backup is a hope,
not a plan.

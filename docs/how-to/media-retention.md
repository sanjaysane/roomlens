# Media retention

## What is stored where

| Data | Where | What it is |
|---|---|---|
| Room photos / video frames | Media store | Original prospect uploads |
| Rendered visualizations | Media store | JPEG composites with price strips |
| Ken Burns clips | Media store | Optional MP4 renders |
| Product cutouts | Media store | Designer-uploaded RGBA PNGs |
| References (`local:…` / `supabase:…`) | PostgreSQL (`room_media.storage_ref`, `visualizations.rendered_ref`, `products.cutout_ref`) | Pointers to the bytes above |
| Conversation state, quotes, orders, opt status | PostgreSQL | Business records |

**Media backends:** `local` (default) writes files under `MEDIA_DIR`
(`./media/` in dev, `/app/data/media` in Docker, persisted via the
`mediadata` volume). `supabase` writes to private objects in a Supabase
Storage bucket. The database never holds image bytes — only refs.

## Retention enforcement (implemented)

Retention is enforced by the purge job in `src/retention.py`
(`python -m src.retention`), scheduled to run periodically (cron/systemd;
see the module docstring). The job:

- queries `room_media` for rows older than the retention window
  (default `--retention-days 90`) whose prospect has **no visualization
  and no order** (the "abandoned prospect" rule) —
  `Database.list_expired_room_media` / `delete_room_media`
  (both Fake and Postgres implementations);
- deletes the bytes via `MediaStore.delete` (tolerates already-gone
  files/objects; DB record is still cleared) and deletes the
  `room_media` row;
- never touches media in an active pipeline (open visualization) or with
  a closed order;
- supports `--dry-run`, which reports what *would* be deleted without
  deleting anything.

Owner: platform operator (pilot on-call) — per `docs/milestones.md`.

## Retention guidelines

RoomLens now ships automatic deletion via the purge job above.
Policy for a studio:

- **Active pipeline** (room has an open visualization, quote, or order):
  keep everything.
- **Closed orders:** keep renders + quote records for your normal
  accounting/warranty window; archive or delete room originals.
- **Abandoned prospects** (no visualization sent, no order after ~90 days):
  delete room media.
- **STOP / deletion requests:** honor immediately (see below).

The purge job (`src/retention.py`) implements exactly this: it deletes the
file (or object) via `MediaStore.delete` and removes the `room_media` row.
Verify with a `--dry-run` before the first live run.

## Deletion requests

A prospect can ask for their data to be deleted by messaging the number
(any text; the designer sees it). On request:

1. Delete the prospect's files from the media store (resolve refs from
   `room_media` and `visualizations`).
2. Delete or anonymize the `prospects` row and related `room_media` /
   `visualizations` rows (cascades handle children: `ON DELETE CASCADE`).
3. Confirm deletion to the requester in their language.

## GDPR-style guidance

Even outside the EU, these are good defaults: collect only what the flow
needs (a room photo, a phone number), state why at collection time (the
opt-in ask does this), keep it only as long as the policy above, and honor
deletion requests promptly. Templates and logs must never contain room
images or phone numbers beyond routing needs. No room image is ever sent to
a third-party vision service — the quality gate runs in-process.

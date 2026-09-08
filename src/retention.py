"""Media retention enforcement (v3 F-06).

Executes the written retention policy in
``docs/how-to/media-retention.md`` as a periodic job:

* **Expired (abandoned) media** — room uploads older than the retention
  window (default 90 days) whose prospect has no visualization and no
  order — gets its bytes deleted from the media store *and* its
  ``room_media`` record deleted.
* **Active pipeline / closed orders** — kept: anything with a
  visualization, quote, or order is never purged by this job.
* ``--dry-run`` reports what *would* be deleted without touching anything.

Run it on a schedule, e.g. cron::

    0 3 * * * cd /opt/roomlens && .venv/bin/python -m src.retention \\
        --retention-days 90 >> /var/log/roomlens/retention.log 2>&1

The job owner is named in ``docs/milestones.md`` (MVP "what must be true",
privacy item). It must run — and stay green — before the first paid pilot.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from datetime import timedelta

from src.config import settings
from src.db import Database, FakeDatabase, PostgresDatabase, utcnow
from src.media import LocalMediaStore, MediaStore, SupabaseMediaStore

RETENTION_DAYS_DEFAULT = 90


@dataclass
class PurgeResult:
    """What a purge run found and did."""

    retention_days: int
    dry_run: bool
    scanned: int = 0
    deleted: int = 0
    would_delete: int = 0
    kept: int = 0
    deleted_refs: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    def summary(self) -> str:
        action = "would delete" if self.dry_run else "deleted"
        return (
            f"retention: scanned={self.scanned} {action}="
            f"{self.would_delete if self.dry_run else self.deleted} "
            f"kept={self.kept} failed={len(self.failed)} "
            f"(window={self.retention_days}d dry_run={self.dry_run})"
        )


def purge_expired_media(
    db: Database,
    store: MediaStore,
    *,
    retention_days: int = RETENTION_DAYS_DEFAULT,
    dry_run: bool = False,
    now=None,
) -> PurgeResult:
    """Delete bytes + records for media past the retention window.

    Only media the DB reports as expired (abandoned: no visualization,
    no order for the prospect) is touched. Files missing from the store
    are tolerated — the DB record is still removed so state can't drift.
    """
    if retention_days < 0:
        raise ValueError("retention_days must be >= 0")
    now = now or utcnow()
    cutoff = now - timedelta(days=retention_days)
    result = PurgeResult(retention_days=retention_days, dry_run=dry_run)

    for row in db.list_expired_room_media(cutoff):
        result.scanned += 1
        ref = row.get("storage_ref", "")
        media_id = row["id"]
        if dry_run:
            result.would_delete += 1
            result.deleted_refs.append(ref)
            continue
        try:
            if ref:
                store.delete(ref)
            db.delete_room_media(media_id)
        except Exception as exc:  # noqa: BLE001 — keep sweeping; log it
            result.failed.append(f"{ref}: {exc}")
            continue
        result.deleted += 1
        result.deleted_refs.append(ref)

    result.kept = 0
    return result


def _build_db() -> Database:
    if settings.database_url:
        return PostgresDatabase(settings.database_url)
    return FakeDatabase()


def _build_store() -> MediaStore:
    if settings.media_backend == "supabase":
        return SupabaseMediaStore(
            settings.supabase_url,
            settings.supabase_service_key,
            settings.supabase_bucket,
        )
    return LocalMediaStore(settings.media_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Delete room media past the retention window."
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=RETENTION_DAYS_DEFAULT,
        help=f"age in days after which abandoned media is deleted "
        f"(default {RETENTION_DAYS_DEFAULT})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be deleted; delete nothing",
    )
    args = parser.parse_args(argv)

    result = purge_expired_media(
        _build_db(),
        _build_store(),
        retention_days=args.retention_days,
        dry_run=args.dry_run,
    )
    print(result.summary())
    for ref in result.deleted_refs:
        print(f"  {'[dry-run] ' if result.dry_run else ''}{ref}")
    for failure in result.failed:
        print(f"  FAILED: {failure}", file=sys.stderr)
    return 1 if result.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

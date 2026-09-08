"""Tests for the media-retention purge job (v3 F-06)."""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db import FakeDatabase, utcnow
from src.media import LocalMediaStore
from src.retention import purge_expired_media


def _setup(tmp_path, age_days: int, with_visualization=False, with_order=False):
    """One prospect with one room photo saved to the store, aged age_days."""
    db = FakeDatabase()
    store = LocalMediaStore(str(tmp_path / "media"))
    designer = db.ensure_designer("+15550001111", "Studio One")
    prospect = db.ensure_prospect("+15550002222", "+15550001111")
    ref = store.save("room", "room.png", b"room-bytes")
    media = db.add_room_media(
        prospect["id"], designer["id"], ref, "photo", 100, 100, {}
    )
    db.room_media[media["id"]]["created_at"] = utcnow() - timedelta(
        days=age_days
    )
    if with_visualization:
        db.create_visualization(
            prospect["id"], designer["id"], media["id"], []
        )
    if with_order:
        quote = db.create_quote(media["id"], [], 1000, 0, 1000, "USD")
        db.create_order("+15550002222", designer["id"], quote["id"], 1000, "USD")
    return db, store, media, ref


def test_expired_media_is_deleted_file_and_record(tmp_path):
    db, store, media, ref = _setup(tmp_path, age_days=120)
    result = purge_expired_media(db, store, retention_days=90)
    assert result.deleted == 1
    assert result.deleted_refs == [ref]
    assert db.get_room_media(media["id"]) is None
    assert not (tmp_path / "media" / ref[len("local:"):]).exists()


def test_unexpired_media_is_kept(tmp_path):
    db, store, media, ref = _setup(tmp_path, age_days=10)
    result = purge_expired_media(db, store, retention_days=90)
    assert result.deleted == 0
    assert db.get_room_media(media["id"]) is not None
    assert store.load(ref) == b"room-bytes"


def test_old_media_with_visualization_is_kept(tmp_path):
    db, store, media, _ref = _setup(
        tmp_path, age_days=365, with_visualization=True
    )
    result = purge_expired_media(db, store, retention_days=90)
    assert result.deleted == 0
    assert db.get_room_media(media["id"]) is not None


def test_old_media_with_order_is_kept(tmp_path):
    db, store, media, _ref = _setup(tmp_path, age_days=365, with_order=True)
    result = purge_expired_media(db, store, retention_days=90)
    assert result.deleted == 0
    assert db.get_room_media(media["id"]) is not None


def test_dry_run_reports_without_deleting(tmp_path):
    db, store, media, ref = _setup(tmp_path, age_days=120)
    result = purge_expired_media(db, store, retention_days=90, dry_run=True)
    assert result.would_delete == 1
    assert result.deleted == 0
    assert result.deleted_refs == [ref]
    # Nothing actually deleted.
    assert db.get_room_media(media["id"]) is not None
    assert store.load(ref) == b"room-bytes"


def test_missing_file_still_clears_record(tmp_path):
    db, store, media, ref = _setup(tmp_path, age_days=120)
    (tmp_path / "media" / ref[len("local:"):]).unlink()
    result = purge_expired_media(db, store, retention_days=90)
    assert result.deleted == 1
    assert result.failed == []
    assert db.get_room_media(media["id"]) is None

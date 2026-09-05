"""Photo-quality gate tests: dark / blurry / small / unreadable / ok."""

from __future__ import annotations

from conftest import make_blurry_image, make_dark_image, make_image, make_noisy_image

from src.composite import assess_quality


def test_dark_rejected():
    q = assess_quality(make_dark_image())
    assert q["ok"] is False
    assert "dark" in q["issues"]


def test_blurry_rejected():
    q = assess_quality(make_blurry_image())
    assert q["ok"] is False
    assert "blurry" in q["issues"]


def test_small_rejected():
    q = assess_quality(make_image(size=(100, 80), color=(200, 200, 200)))
    assert q["ok"] is False
    assert "small" in q["issues"]


def test_unreadable_rejected():
    q = assess_quality(b"this is not an image at all")
    assert q["ok"] is False
    assert q["issues"] == ["unreadable"]


def test_noisy_room_accepted():
    q = assess_quality(make_noisy_image())
    assert q["ok"] is True, q["issues"]
    assert q["width"] == 800
    assert q["brightness"] > 0
    assert q["blur"] >= 0

"""Shared fixtures: an in-memory chat harness over the fake adapters."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db import FakeDatabase
from src.i18n import I18n
from src.media import FakeWhatsAppMedia, LocalMediaStore
from src.state_machine import process_incoming
from src.whatsapp import FakeWhatsAppClient

LOCALES = Path(__file__).resolve().parents[1] / "locales"


class Chat:
    """Drives process_incoming like the webhook would."""

    def __init__(self, tmp_path: Path):
        self.db = FakeDatabase()
        self.wa = FakeWhatsAppClient()
        self.media = FakeWhatsAppMedia()
        self.store = LocalMediaStore(str(tmp_path / "media"))
        self.i18n = I18n(str(LOCALES))

    def send(self, phone: str, text=None, msg_type="text", media_id=None):
        process_incoming(
            self.db, self.wa, self.i18n, self.media, self.store,
            phone, text, msg_type=msg_type, media_id=media_id,
            default_lang="en",
        )

    def out(self, phone: str):
        """All outbound traffic to a phone, in order: (to, kind, body)."""
        return [m for m in self.wa.sent if m[0] == phone]

    def texts(self, phone: str):
        return [m[2] for m in self.out(phone) if m[1] == "text"]

    def images(self, phone: str):
        """(to, bytes, caption) tuples from send_image."""
        return [m for m in self.wa.images if m[0] == phone]

    def image_captions(self, phone: str):
        return [m[2] for m in self.images(phone)]

    def templates(self, phone: str):
        return [m[1] for m in self.wa.templates if m[0] == phone]


@pytest.fixture
def chat(tmp_path):
    return Chat(tmp_path)


def make_image(size=(800, 600), color=(180, 170, 160), fmt="PNG") -> bytes:
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def make_noisy_image(size=(800, 600)) -> bytes:
    """High-frequency noise → guaranteed 'sharp' by the blur heuristic."""
    import numpy as np

    rng = np.random.default_rng(42)
    arr = rng.integers(0, 256, size=(size[1], size[0], 3), dtype="uint8")
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_dark_image(size=(800, 600)) -> bytes:
    return make_image(size=size, color=(8, 8, 10))


def make_blurry_image(size=(800, 600)) -> bytes:
    """Uniform gradient → near-zero Laplacian variance = blurry."""
    import numpy as np

    x = np.linspace(120, 140, size[0], dtype="uint8")
    arr = np.tile(x, (size[1], 1))
    rgb = np.stack([arr, arr, arr], axis=-1)
    img = Image.fromarray(rgb)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


DESIGNER = "15550001111"
PROSPECT = "15550002222"

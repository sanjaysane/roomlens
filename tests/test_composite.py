"""Compositing engine tests: presets, scaling, price strip, video."""

from __future__ import annotations

import io

import pytest
from conftest import make_image, make_noisy_image
from PIL import Image

from src import composite as C
from src import models as M

ROOM = None
CUTOUT = None


def room_bytes():
    global ROOM
    if ROOM is None:
        ROOM = make_noisy_image((800, 600))
    return ROOM


def cutout_bytes():
    global CUTOUT
    if CUTOUT is None:
        CUTOUT = make_image(size=(200, 300), color=(200, 60, 40))
    return CUTOUT


@pytest.mark.parametrize("preset", list(M.PLACEMENT_PRESETS))
def test_each_preset_renders_valid_jpeg(preset):
    out = C.render_visualization(
        room_bytes(),
        [{"cutout": cutout_bytes(), "preset": preset, "scale": 1.0,
          "label": "Aria Chair — $189.00"}],
    )
    img = Image.open(io.BytesIO(out))
    assert img.format == "JPEG"
    assert img.size[0] == 800  # price strip only adds height


def test_scale_changes_render():
    small = C.render_visualization(
        room_bytes(),
        [{"cutout": cutout_bytes(), "preset": "floor-center", "scale": 0.5,
          "label": "x"}],
    )
    big = C.render_visualization(
        room_bytes(),
        [{"cutout": cutout_bytes(), "preset": "floor-center", "scale": 1.0,
          "label": "x"}],
    )
    assert small != big


def test_invalid_preset_raises():
    with pytest.raises(ValueError):
        C.render_visualization(
            room_bytes(),
            [{"cutout": cutout_bytes(), "preset": "ceiling-fan", "scale": 1.0,
              "label": "x"}],
        )


def test_empty_items_raises():
    with pytest.raises(ValueError):
        C.render_visualization(room_bytes(), [])


def test_price_strip_adds_height():
    out = C.render_visualization(
        room_bytes(),
        [{"cutout": cutout_bytes(), "preset": "floor-center", "scale": 1.0,
          "label": "Aria Chair — $189.00"}],
    )
    img = Image.open(io.BytesIO(out))
    assert img.size[1] > 600


def test_placeholder_cutout_is_png():
    data = C.make_placeholder_cutout("Aria Chair")
    img = Image.open(io.BytesIO(data))
    assert img.size[0] > 0


def test_place_cutout_clamps_huge_scale():
    room = Image.open(io.BytesIO(room_bytes()))
    cutout = Image.open(io.BytesIO(cutout_bytes()))
    out = C.place_cutout(room, cutout, "floor-center", scale=2.5)
    assert out.size == room.size


def test_make_clip_smoke():
    if not C.ffmpeg_available():
        pytest.skip("ffmpeg not installed")
    mp4 = C.make_clip(room_bytes(), seconds=1)
    assert mp4 is not None
    assert mp4[4:8] == b"ftyp"

"""Compositing engine: "see it in YOUR home".

Preset-based placement of product cutouts onto prospect room photos —
drivable entirely from single-digit chat replies. This is NOT true AR:
there is no plane detection, depth estimation, or perspective warping.
Placements are 2D presets with a bigger/smaller scale control, which is
honest about its realism limits (documented in docs/ARCHITECTURE.md).

Also in this module:
* `assess_quality` — brightness / blur / resolution heuristics. A dark or
  blurry photo triggers a polite retake request instead of a misleading
  overlay (the counterfactual is tested).
* `make_clip` — optional short Ken Burns video from a render via ffmpeg.
"""

from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import models as M

# ── Quality thresholds (tuned against generated fixtures in tests) ──
MIN_BRIGHTNESS = 45.0  # mean grayscale below this → "too dark"
MIN_BLUR_SCORE = 90.0  # Laplacian variance below this → "too blurry"
MIN_SIDE_PX = 400  # smallest side below this → "too small"


def _to_gray(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("L"), dtype=np.float64)


def laplacian_variance(gray: np.ndarray) -> float:
    """Blur metric: variance of the Laplacian. Sharp texture → high,
    smooth/blurry → low. Implemented with numpy (no OpenCV dependency)."""
    inner = gray[1:-1, 1:-1]
    lap = (
        gray[:-2, 1:-1]
        + gray[2:, 1:-1]
        + gray[1:-1, :-2]
        + gray[1:-1, 2:]
        - 4.0 * inner
    )
    return float(lap.var())


def assess_quality(image_bytes: bytes) -> dict:
    """Return {ok, issues[], brightness, blur, width, height}.

    issues ⊆ {"dark", "blurry", "small", "unreadable"}.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:  # noqa: BLE001 - any decode failure = unreadable photo
        return {
            "ok": False,
            "issues": ["unreadable"],
            "brightness": 0.0,
            "blur": 0.0,
            "width": 0,
            "height": 0,
        }
    gray = _to_gray(img)
    brightness = float(gray.mean())
    blur = laplacian_variance(gray)
    w, h = img.size
    issues: list[str] = []
    if brightness < MIN_BRIGHTNESS:
        issues.append("dark")
    if blur < MIN_BLUR_SCORE:
        issues.append("blurry")
    if min(w, h) < MIN_SIDE_PX:
        issues.append("small")
    return {
        "ok": not issues,
        "issues": issues,
        "brightness": round(brightness, 1),
        "blur": round(blur, 1),
        "width": w,
        "height": h,
    }


# ── Placement geometry ─────────────────────────────────────────────
def _placement_box(
    room_w: int, room_h: int, cw: int, ch: int, preset: str
) -> tuple[int, int]:
    """Top-left (x, y) to paste a cw×ch cutout for a preset."""
    if preset == M.PRESET_FLOOR_CENTER:
        return (room_w - cw) // 2, int(room_h - ch - 0.04 * room_h)
    if preset == M.PRESET_LEFT_WALL:
        return int(0.05 * room_w), int(room_h - ch - 0.05 * room_h)
    if preset == M.PRESET_RIGHT_WALL:
        return int(0.95 * room_w - cw), int(room_h - ch - 0.05 * room_h)
    if preset == M.PRESET_WALL_HANG:
        return (room_w - cw) // 2, int(0.18 * room_h)
    raise ValueError(f"Unknown placement preset: {preset}")


def _target_width(room_w: int, preset: str, scale: float) -> int:
    fraction = {
        M.PRESET_FLOOR_CENTER: 0.45,
        M.PRESET_LEFT_WALL: 0.35,
        M.PRESET_RIGHT_WALL: 0.35,
        M.PRESET_WALL_HANG: 0.40,
    }[preset]
    return max(32, int(room_w * fraction * scale))


def place_cutout(
    room: Image.Image,
    cutout: Image.Image,
    preset: str,
    scale: float = 1.0,
) -> Image.Image:
    """Alpha-composite one RGBA cutout onto the room at a preset."""
    if preset not in M.PLACEMENT_PRESETS:
        raise ValueError(f"Unknown placement preset: {preset}")
    if scale <= 0:
        raise ValueError("scale must be positive")
    room = room.convert("RGBA")
    cutout = cutout.convert("RGBA")
    tw = _target_width(room.width, preset, scale)
    ratio = tw / cutout.width
    th = max(32, int(cutout.height * ratio))
    resized = cutout.resize((tw, th), Image.LANCZOS)
    x, y = _placement_box(room.width, room.height, tw, th, preset)
    # Clamp inside the canvas (a huge scale must not crash the paste).
    x = max(0, min(x, room.width - tw))
    y = max(0, min(y, room.height - th))
    room.alpha_composite(resized, (x, y))
    return room.convert("RGB")


def add_price_strip(img: Image.Image, lines: list[str]) -> Image.Image:
    """Append a white caption bar with one line per placed product."""
    strip_h = 34 + 26 * max(1, len(lines))
    canvas = Image.new("RGB", (img.width, img.height + strip_h), "white")
    canvas.paste(img, (0, 0))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 22)
        small = ImageFont.truetype("DejaVuSans.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
        small = font
    draw.text((16, 10), "✨ Your room, with our furniture:", fill="black", font=font)
    for i, line in enumerate(lines):
        draw.text((16, 44 + 26 * i), line, fill=(60, 60, 60), font=small)
    return canvas


def render_visualization(
    room_bytes: bytes,
    items: list[dict],
    jpeg_quality: int = 88,
) -> bytes:
    """Composite every item (cutout_bytes, preset, scale, label) onto the
    room photo and return JPEG bytes with a price strip.

    Each item: {"cutout": bytes(RGBA png), "preset": str, "scale": float,
                "label": "Oak Chair — $189"}.
    Raises ValueError on bad input — never silently renders garbage.
    """
    if not items:
        raise ValueError("render_visualization needs at least one item")
    room = Image.open(io.BytesIO(room_bytes)).convert("RGB")
    for it in items:
        cutout = Image.open(io.BytesIO(it["cutout"]))
        room = place_cutout(room, cutout, it["preset"], float(it.get("scale", 1.0)))
    room = add_price_strip(room, [it["label"] for it in items])
    buf = io.BytesIO()
    room.save(buf, format="JPEG", quality=jpeg_quality)
    return buf.getvalue()


# ── Optional video clip ────────────────────────────────────────────
def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def extract_first_frame(video_bytes: bytes) -> bytes | None:
    """Pull the first frame of a video as JPEG bytes.

    Lets prospects send a short room clip: we composite onto its first
    frame. Returns None when ffmpeg is missing or the decode fails —
    the caller then asks for a still photo instead. Never raises.
    """
    if not ffmpeg_available():
        return None
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "clip.bin"
        dst = Path(tmp) / "frame.jpg"
        src.write_bytes(video_bytes)
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-i", str(src),
                 "-frames:v", "1", "-q:v", "3", str(dst)],
                timeout=30, check=True,
            )
            data = dst.read_bytes()
            return data if data else None
        except (subprocess.SubprocessError, OSError):
            return None


def make_clip(png_or_jpeg_bytes: bytes, seconds: int = 3) -> bytes | None:
    """Ken Burns pan/zoom clip from a render. Returns MP4 bytes, or None
    if ffmpeg is missing or the encode fails (caller falls back to the
    still image — never a broken video)."""
    if not ffmpeg_available():
        return None
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "frame.jpg"
        dst = Path(tmp) / "clip.mp4"
        src.write_bytes(png_or_jpeg_bytes)
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-loop", "1", "-i", str(src),
            "-vf",
            (
                "zoompan=z='min(zoom+0.0015,1.12)':d=90:"
                "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720"
            ),
            "-t", str(seconds), "-pix_fmt", "yuv420p",
            str(dst),
        ]
        try:
            subprocess.run(cmd, timeout=30, check=True)
            data = dst.read_bytes()
            return data if data else None
        except (subprocess.SubprocessError, OSError):
            return None


# ── Dev/test helpers (NOT production cutout extraction) ────────────
def make_placeholder_cutout(
    label: str, color: tuple[int, int, int] = (150, 90, 60), size=(300, 380)
) -> bytes:
    """Procedural RGBA 'product' for tests and local dev.

    Real deployments use designer-uploaded PNG cutouts with alpha.
    Background removal is intentionally out of scope for v0.1.0.
    """
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Simple furniture-ish silhouette: rounded body + legs.
    draw.rounded_rectangle([20, 20, size[0] - 20, size[1] - 90], 24, fill=color + (255,))
    draw.rectangle([45, size[1] - 90, 70, size[1] - 10], fill=(60, 40, 25, 255))
    draw.rectangle(
        [size[0] - 70, size[1] - 90, size[0] - 45, size[1] - 10],
        fill=(60, 40, 25, 255),
    )
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
    draw.text((30, 40), label[:12], fill="white", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_test_room(
    width: int = 800,
    height: int = 600,
    brightness: int = 150,
    blurry: bool = False,
    seed: int = 7,
) -> bytes:
    """Deterministic synthetic room photo for tests.

    brightness ~ mean gray; blurry=True yields a smooth gradient
    (low Laplacian variance) instead of textured noise.
    """
    rng = np.random.default_rng(seed)
    if blurry:
        yy, xx = np.mgrid[0:height, 0:width]
        base = (xx / width * 40 + yy / height * 40 + brightness - 40)
        arr = np.clip(base, 0, 255).astype(np.uint8)
    else:
        arr = np.clip(
            rng.normal(brightness, 28, (height, width)), 0, 255
        ).astype(np.uint8)
    rgb = np.stack([arr, arr, arr], axis=-1)
    img = Image.fromarray(rgb, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

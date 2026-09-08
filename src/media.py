"""Media pipeline: WhatsApp Graph API media + persistent storage.

Two seams:

1. `WhatsAppMedia` — download inbound media (room photos) by Meta media id,
   and upload rendered bytes for outbound sends.
   * `GraphWhatsAppMedia` — real Graph API calls (needs WHATSAPP_TOKEN).
   * `FakeWhatsAppMedia` — in-memory registry for tests/dev.

2. `MediaStore` — persist bytes durably and hand back a reference.
   * `LocalMediaStore` — ./media/ on disk (dev/tests).
   * `SupabaseMediaStore` — Supabase Storage REST (prod; env-configured).

No credentials live in this repo; everything comes from the environment.
"""

from __future__ import annotations

import abc
import hashlib
import os
import time
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════
# WhatsApp media (Graph API)
# ═══════════════════════════════════════════════════════════════════
class WhatsAppMedia(abc.ABC):
    @abc.abstractmethod
    def download(self, media_id: str) -> bytes:
        """Download inbound media bytes by Meta media id."""
        ...

    @abc.abstractmethod
    def upload(self, data: bytes, mime: str) -> str:
        """Upload bytes, return a media id usable in outbound messages."""
        ...


class GraphWhatsAppMedia(WhatsAppMedia):
    def __init__(
        self,
        token: str,
        api_base: str = "https://graph.facebook.com/v21.0",
        phone_number_id: str = "",
        http_client=None,
    ) -> None:
        if not token:
            raise RuntimeError("WHATSAPP_TOKEN must be set for media download")
        self._token = token
        self._api_base = api_base.rstrip("/")
        self._phone_number_id = phone_number_id
        self._http = http_client

    def _client(self):
        if self._http is not None:
            return self._http
        import httpx

        return httpx.Client(timeout=60.0)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}"}

    def download(self, media_id: str) -> bytes:
        client = self._client()
        close = self._http is None
        try:
            meta = client.get(
                f"{self._api_base}/{media_id}", headers=self._headers()
            )
            if meta.status_code >= 400:
                raise RuntimeError(
                    f"Media lookup failed {meta.status_code}: {meta.text[:200]}"
                )
            url = meta.json().get("url")
            if not url:
                raise RuntimeError("Media lookup returned no URL")
            data = client.get(url, headers=self._headers())
            if data.status_code >= 400:
                raise RuntimeError(
                    f"Media download failed {data.status_code}: {data.text[:200]}"
                )
            return data.content
        finally:
            if close and hasattr(client, "close"):
                client.close()

    def upload(self, data: bytes, mime: str) -> str:
        """Upload binary media to the Graph API, return the media id.

        Needs the WhatsApp phone-number ID (constructor arg): uploads go
        to /{phone-number-id}/media, the same endpoint the message client
        uses for send_image().
        """
        if not self._phone_number_id:
            raise RuntimeError(
                "WHATSAPP_PHONE_NUMBER_ID must be set for media upload"
            )
        client = self._client()
        close = self._http is None
        try:
            resp = client.post(
                f"{self._api_base}/{self._phone_number_id}/media",
                headers=self._headers(),
                files={"file": ("upload", data, mime)},
                data={
                    "messaging_product": "whatsapp",
                    "type": mime.split("/")[0],
                },
            )
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Media upload failed {resp.status_code}: {resp.text[:200]}"
                )
            return resp.json()["id"]
        finally:
            if close and hasattr(client, "close"):
                client.close()


class FakeWhatsAppMedia(WhatsAppMedia):
    """Test double: pre-register media_id → bytes; records uploads."""

    def __init__(self) -> None:
        self.registry: dict[str, bytes] = {}
        self.uploads: list[tuple[bytes, str]] = []

    def register(self, media_id: str, data: bytes) -> None:
        self.registry[media_id] = data

    def download(self, media_id: str) -> bytes:
        try:
            return self.registry[media_id]
        except KeyError:
            raise RuntimeError(f"Unknown test media id: {media_id}") from None

    def upload(self, data: bytes, mime: str) -> str:
        media_id = f"fake-upload-{len(self.uploads)}"
        self.uploads.append((data, mime))
        self.registry[media_id] = data
        return media_id


# ═══════════════════════════════════════════════════════════════════
# Persistent storage
# ═══════════════════════════════════════════════════════════════════
class MediaStore(abc.ABC):
    @abc.abstractmethod
    def save(self, kind: str, filename: str, data: bytes) -> str:
        """Persist bytes; return an opaque reference for later load()."""
        ...

    @abc.abstractmethod
    def load(self, ref: str) -> bytes:
        ...

    @abc.abstractmethod
    def delete(self, ref: str) -> None:
        """Delete previously stored bytes. Tolerates already-gone refs."""
        ...


def _safe_filename(filename: str) -> str:
    base = os.path.basename(filename).replace("..", "")
    digest = hashlib.sha256(f"{time.time_ns()}".encode()).hexdigest()[:8]
    stem, ext = os.path.splitext(base)
    return f"{stem or 'file'}-{digest}{ext or '.bin'}"


class LocalMediaStore(MediaStore):
    """Disk-backed store for development and tests."""

    def __init__(self, root: str | Path = "./media") -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def save(self, kind: str, filename: str, data: bytes) -> str:
        subdir = self._root / kind
        subdir.mkdir(parents=True, exist_ok=True)
        name = _safe_filename(filename)
        (subdir / name).write_bytes(data)
        return f"local:{kind}/{name}"

    def load(self, ref: str) -> bytes:
        if not ref.startswith("local:"):
            raise ValueError(f"Not a local media ref: {ref}")
        return (self._root / ref[len("local:"):]).read_bytes()

    def delete(self, ref: str) -> None:
        if not ref.startswith("local:"):
            raise ValueError(f"Not a local media ref: {ref}")
        (self._root / ref[len("local:"):]).unlink(missing_ok=True)


class SupabaseMediaStore(MediaStore):
    """Supabase Storage backend (production).

    Uses the Storage REST API with the service-role key from the
    environment. Objects are private; refs are bucket-relative paths.
    """

    def __init__(
        self, supabase_url: str, service_key: str, bucket: str, http_client=None
    ) -> None:
        if not supabase_url or not service_key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set"
            )
        self._base = supabase_url.rstrip("/")
        self._bucket = bucket
        self._key = service_key
        self._http = http_client

    def _client(self):
        if self._http is not None:
            return self._http
        import httpx

        return httpx.Client(timeout=60.0)

    def _headers(self, content_type: str = "application/octet-stream") -> dict:
        return {
            "apikey": self._key,
            "Authorization": f"Bearer {self._key}",
            "Content-Type": content_type,
        }

    def save(self, kind: str, filename: str, data: bytes) -> str:
        name = _safe_filename(filename)
        path = f"{kind}/{name}"
        client = self._client()
        close = self._http is None
        try:
            resp = client.post(
                f"{self._base}/storage/v1/object/{self._bucket}/{path}",
                headers=self._headers(),
                content=data,
            )
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Supabase upload failed {resp.status_code}: {resp.text[:200]}"
                )
            return f"supabase:{path}"
        finally:
            if close and hasattr(client, "close"):
                client.close()

    def load(self, ref: str) -> bytes:
        if not ref.startswith("supabase:"):
            raise ValueError(f"Not a Supabase media ref: {ref}")
        path = ref[len("supabase:"):]
        client = self._client()
        close = self._http is None
        try:
            resp = client.get(
                f"{self._base}/storage/v1/object/{self._bucket}/{path}",
                headers=self._headers(),
            )
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Supabase download failed {resp.status_code}: {resp.text[:200]}"
                )
            return resp.content
        finally:
            if close and hasattr(client, "close"):
                client.close()

    def delete(self, ref: str) -> None:
        if not ref.startswith("supabase:"):
            raise ValueError(f"Not a Supabase media ref: {ref}")
        path = ref[len("supabase:"):]
        client = self._client()
        close = self._http is None
        try:
            resp = client.delete(
                f"{self._base}/storage/v1/object/{self._bucket}/{path}",
                headers=self._headers(),
            )
            # 404 means the object is already gone — still fine.
            if resp.status_code >= 400 and resp.status_code != 404:
                raise RuntimeError(
                    f"Supabase delete failed {resp.status_code}: "
                    f"{resp.text[:200]}"
                )
        finally:
            if close and hasattr(client, "close"):
                client.close()

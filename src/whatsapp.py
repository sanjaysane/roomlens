"""WhatsApp Cloud API client.

`WhatsAppClient` is the seam: production uses `MetaWhatsAppClient`
(real HTTPS calls to graph.facebook.com); tests inject `FakeWhatsAppClient`
which records outbound messages for assertions.

Business-initiated outreach (campaigns, win-backs) MUST use
`send_template` with a Meta pre-approved template name — plain text
pushes to prospects who never messaged first are blocked by Meta policy.
The marketing module enforces opt-in on top of that.
"""

from __future__ import annotations

import abc


class WhatsAppClient(abc.ABC):
    @abc.abstractmethod
    def send_text(self, to: str, body: str) -> None:
        """Send a plain-text WhatsApp message to an E.164 number."""
        ...

    @abc.abstractmethod
    def send_image(self, to: str, image_bytes: bytes, caption: str = "") -> None:
        """Send an image message (bytes + caption)."""
        ...

    @abc.abstractmethod
    def send_template(
        self, to: str, template_name: str, language_code: str = "en_US", **params
    ) -> None:
        """Send a pre-approved Meta template message (business-initiated)."""
        ...


class MetaWhatsAppClient(WhatsAppClient):
    def __init__(
        self,
        token: str,
        phone_number_id: str,
        api_base: str = "https://graph.facebook.com/v21.0",
        http_client=None,
    ) -> None:
        if not token or not phone_number_id:
            raise RuntimeError(
                "WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID must be set"
            )
        self._token = token
        self._phone_number_id = phone_number_id
        self._api_base = api_base.rstrip("/")
        self._url = f"{self._api_base}/{phone_number_id}/messages"
        self._media_url = f"{self._api_base}/{phone_number_id}/media"
        self._http = http_client  # injectable for tests

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def _client(self):
        if self._http is not None:
            return self._http
        import httpx

        return httpx.Client(timeout=30.0)

    def _post(self, payload: dict) -> dict:
        client = self._client()
        close = self._http is None
        try:
            resp = client.post(self._url, json=payload, headers=self._headers())
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"WhatsApp API error {resp.status_code}: {resp.text[:300]}"
                )
            return resp.json() if hasattr(resp, "json") else {}
        finally:
            if close and hasattr(client, "close"):
                client.close()

    def send_text(self, to: str, body: str) -> None:
        self._post(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {"preview_url": False, "body": body},
            }
        )

    def send_image(self, to: str, image_bytes: bytes, caption: str = "") -> None:
        media_id = self._upload_media(image_bytes, "image/png")
        self._post(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "image",
                "image": {"id": media_id, "caption": caption[:1024]},
            }
        )

    def send_template(
        self, to: str, template_name: str, language_code: str = "en_US", **params
    ) -> None:
        components = []
        if params:
            components = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(v)}
                        for v in params.get("body_params", [])
                    ],
                }
            ]
        self._post(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": language_code},
                    "components": components,
                },
            }
        )

    def _upload_media(self, data: bytes, mime: str) -> str:
        """Upload binary media, return the Meta media id for reuse."""
        import httpx

        headers = {"Authorization": f"Bearer {self._token}"}
        files = {"file": ("upload", data, mime)}
        form = {"messaging_product": "whatsapp", "type": mime.split("/")[0]}
        client = self._http or httpx.Client(timeout=60.0)
        close = self._http is None
        try:
            resp = client.post(
                self._media_url, headers=headers, files=files, data=form
            )
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"WhatsApp media upload error {resp.status_code}: "
                    f"{resp.text[:300]}"
                )
            return resp.json()["id"]
        finally:
            if close and hasattr(client, "close"):
                client.close()


class FakeWhatsAppClient(WhatsAppClient):
    """Test double: records outbound traffic instead of hitting Meta."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []  # (to, kind, body/caption)
        self.images: list[tuple[str, bytes, str]] = []  # (to, bytes, caption)
        self.templates: list[tuple[str, str]] = []  # (to, template_name)

    def send_text(self, to: str, body: str) -> None:
        self.sent.append((to, "text", body))

    def send_image(self, to: str, image_bytes: bytes, caption: str = "") -> None:
        self.images.append((to, image_bytes, caption))
        self.sent.append((to, "image", caption))

    def send_template(
        self, to: str, template_name: str, language_code: str = "en_US", **params
    ) -> None:
        self.templates.append((to, template_name))
        self.sent.append((to, "template", template_name))

    def last_to(self, phone: str, kind: str = "text") -> str | None:
        for to, k, body in reversed(self.sent):
            if to == phone and k == kind:
                return body
        return None

    def clear(self) -> None:
        self.sent.clear()
        self.images.clear()
        self.templates.clear()

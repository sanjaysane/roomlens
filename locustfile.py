"""Locust workload: Meta webhook-shaped traffic against /webhook.

Models the real inbound path: nested Meta payloads POSTed to /webhook,
each hydrating a chat session from the DB and dispatching the state
machine. Mix: mostly text (role pick, single-digit replies), some image
messages (room photos), plus health probes.

Run:  locust -f locustfile.py --host http://127.0.0.1:8000
"""

from __future__ import annotations

import itertools
import random

from locust import HttpUser, between, task

_PHONES = itertools.count(1_550_000_000)


def _phone() -> str:
    return f"+{next(_PHONES)}"


def _meta_text(phone: str, body: str) -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "loadtest",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": phone,
                        "id": f"wamid.{random.randint(1, 10**9)}",
                        "type": "text",
                        "text": {"body": body},
                    }],
                },
            }],
        }],
    }


def _meta_image(phone: str) -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "loadtest",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": phone,
                        "id": f"wamid.{random.randint(1, 10**9)}",
                        "type": "image",
                        "image": {"id": "loadtest-media", "caption": None},
                    }],
                },
            }],
        }],
    }


class WhatsAppUser(HttpUser):
    wait_time = between(0.2, 1.0)

    def on_start(self):
        self.phone = _phone()
        # walk a fresh user through the welcome → role pick flow
        self.client.post("/webhook", json=_meta_text(self.phone, "hi"))
        self.client.post("/webhook", json=_meta_text(self.phone, "2"))
        self.client.post("/webhook", json=_meta_text(self.phone, "1"))

    @task(7)
    def text_reply(self):
        body = random.choice(["1", "2", "3", "hi", "STOP", "language"])
        self.client.post("/webhook", json=_meta_text(self.phone, body))

    @task(2)
    def room_photo(self):
        self.client.post("/webhook", json=_meta_image(self.phone))

    @task(1)
    def health(self):
        self.client.get("/health")

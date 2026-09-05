"""Webhook tests: verification handshake, payload parsing, error tolerance."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import main


@pytest.fixture
def client(monkeypatch, tmp_path):
    import dataclasses

    test_settings = dataclasses.replace(
        main.settings, webhook_verify_token="test-token"
    )
    monkeypatch.setattr(main, "settings", test_settings)
    with TestClient(main.app) as c:
        yield c


def meta_payload(phone: str, body: str) -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "123",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": phone,
                        "id": "wamid.1",
                        "type": "text",
                        "text": {"body": body},
                    }],
                },
                "field": "messages",
            }],
        }],
    }


def test_verify_handshake_ok(client):
    r = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "test-token",
        "hub.challenge": "CHALLENGE123",
    })
    assert r.status_code == 200
    assert r.text == "CHALLENGE123"


def test_verify_handshake_bad_token(client):
    r = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "wrong",
        "hub.challenge": "CHALLENGE123",
    })
    assert r.status_code == 403


def test_webhook_dispatches_message(client):
    r = client.post("/webhook", json=meta_payload("15550009999", "hi"))
    assert r.status_code == 200
    assert r.json() == {"ok": True}
    _db, wa, *_ = client.app.state.runtime
    sent = [m for m in wa.sent if m[0] == "+15550009999"]  # E.164 normalized
    assert sent, "expected a reply to the inbound message"
    assert "Welcome" in sent[0][2]


def test_webhook_image_payload(client):
    payload = meta_payload("15550009999", "")
    payload["entry"][0]["changes"][0]["value"]["messages"][0] = {
        "from": "15550009999",
        "id": "wamid.2",
        "type": "image",
        "image": {"id": "media-1", "caption": None},
    }
    r = client.post("/webhook", json=payload)
    assert r.status_code == 200


def test_webhook_malformed_json_is_200(client):
    r = client.post("/webhook", content=b"not json",
                    headers={"Content-Type": "application/json"})
    assert r.status_code == 200


def test_webhook_status_update_no_messages(client):
    r = client.post("/webhook", json={
        "object": "whatsapp_business_account",
        "entry": [{"id": "1", "changes": [{"value": {"statuses": []},
                                           "field": "messages"}]}],
    })
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_health(client):
    assert client.get("/health").json()["ok"] is True

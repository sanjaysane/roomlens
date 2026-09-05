"""RoomLens runtime configuration (environment-driven)."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _get(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Settings:
    whatsapp_token: str = _get("WHATSAPP_TOKEN")
    whatsapp_phone_number_id: str = _get("WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_api_base: str = _get(
        "WHATSAPP_API_BASE", "https://graph.facebook.com/v21.0"
    )
    webhook_verify_token: str = _get("WEBHOOK_VERIFY_TOKEN", "roomlens-dev-verify")
    database_url: str = _get("DATABASE_URL")
    media_backend: str = _get("MEDIA_BACKEND", "local")
    media_dir: str = _get("MEDIA_DIR", "./media")
    supabase_url: str = _get("SUPABASE_URL")
    supabase_service_key: str = _get("SUPABASE_SERVICE_KEY")
    supabase_bucket: str = _get("SUPABASE_BUCKET", "roomlens")
    default_language: str = _get("DEFAULT_LANGUAGE", "en")
    locales_dir: str = os.path.join(os.path.dirname(__file__), "..", "locales")


settings = Settings()

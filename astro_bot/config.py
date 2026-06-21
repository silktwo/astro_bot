from __future__ import annotations

import os
from dataclasses import dataclass

MODEL_REASON = "qwen3.7-plus"
MODEL_WRITE = "qwen3.7-plus"
MODEL_VISION = "deepseek-v4-flash"
MODEL_FALLBACK = "glm-5.2"


@dataclass
class Config:
    telegram_token: str
    api_key: str
    base_url: str
    recipient_chat_id: int | None
    webhook_secret: str
    push_tz: str
    swisseph_path: str
    seed_path: str


def load() -> Config:
    rc = os.getenv("RECIPIENT_CHAT_ID")
    return Config(
        telegram_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        api_key=os.environ.get("OPENCODE_API_KEY", ""),
        base_url=os.environ.get("OPENCODE_BASE_URL", "https://opencode.ai/zen/go/v1"),
        recipient_chat_id=int(rc) if rc else None,
        webhook_secret=os.environ.get("TELEGRAM_WEBHOOK_SECRET", ""),
        push_tz=os.environ.get("PUSH_TZ", "Europe/Warsaw"),
        swisseph_path=os.environ.get("SWISSEPH_PATH", "ephe"),
        seed_path=os.environ.get("SEED_PATH", "data/anna_natal.json"),
    )

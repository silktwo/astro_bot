import os
from dataclasses import dataclass

MODEL_REASON = "qwen3.7-max"
MODEL_WRITE = "claude-sonnet-4.6"
MODEL_VISION = "gemini-3.5-flash"
MODEL_FALLBACK = "qwen3.7-plus"


@dataclass
class Config:
    telegram_token: str
    api_key: str
    base_url: str
    admin_id: int
    gf_id: int | None
    push_hour: int
    push_tz: str
    swisseph_path: str


def load() -> Config:
    gf = os.getenv("GF_TELEGRAM_ID")
    return Config(
        telegram_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        api_key=os.environ.get("OPENCODE_API_KEY", ""),
        base_url=os.environ.get("OPENCODE_BASE_URL", "https://opencode.ai/zen/go/v1"),
        admin_id=int(os.environ.get("ADMIN_TELEGRAM_ID", "0")),
        gf_id=int(gf) if gf else None,
        push_hour=int(os.environ.get("PUSH_HOUR", "18")),
        push_tz=os.environ.get("PUSH_TZ", "Europe/Warsaw"),
        swisseph_path=os.environ.get("SWISSEPH_PATH", "/app/ephe"),
    )

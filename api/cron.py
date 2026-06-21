"""Vercel serverless: щоденний прогноз через Vercel Cron.

Розклад у vercel.json. Vercel шле GET із Authorization: Bearer $CRON_SECRET.
"""
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("SWISSEPH_PATH", os.path.join(_ROOT, "ephe"))
os.environ.setdefault("SEED_PATH", os.path.join(_ROOT, "data", "anna_natal.json"))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from astro_bot import config  # noqa: E402
from astro_bot.handlers import daily_text  # noqa: E402
from astro_bot.llm import LLM  # noqa: E402
from astro_bot.natal_import import load_seed  # noqa: E402
from astro_bot.telegram_api import Bot  # noqa: E402

log = logging.getLogger("astro_bot.cron")


class handler(BaseHTTPRequestHandler):
    def _finish(self, code: int, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        cfg = config.load()
        cron_secret = os.environ.get("CRON_SECRET", "")
        auth = self.headers.get("Authorization", "")
        if cron_secret and auth != f"Bearer {cron_secret}":
            return self._finish(401, b"unauthorized")
        if not cfg.recipient_chat_id:
            return self._finish(500, b"RECIPIENT_CHAT_ID not set")
        try:
            llm = LLM(cfg=cfg)
            seed = load_seed(cfg.seed_path)
            text = daily_text(cfg, llm, seed)
            Bot(cfg.telegram_token).send_message(cfg.recipient_chat_id, text)
            return self._finish(200, b"sent")
        except Exception:
            log.exception("daily cron failed")
            return self._finish(500, b"error")

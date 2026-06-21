"""Vercel serverless: Telegram webhook.

Telegram шле POST з апдейтом сюди. Відповідаємо прямими викликами Bot API.
"""
import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("SWISSEPH_PATH", os.path.join(_ROOT, "ephe"))
os.environ.setdefault("SEED_PATH", os.path.join(_ROOT, "data", "anna_natal.json"))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from astro_bot import config  # noqa: E402
from astro_bot.handlers import handle_update  # noqa: E402
from astro_bot.llm import LLM  # noqa: E402
from astro_bot.natal_import import load_seed  # noqa: E402
from astro_bot.telegram_api import Bot  # noqa: E402

log = logging.getLogger("astro_bot.webhook")


class handler(BaseHTTPRequestHandler):
    def _finish(self, code: int, body: bytes = b"ok"):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        cfg = config.load()
        # Валідація секрету вебхука (Telegram надсилає його у заголовку).
        secret = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if cfg.webhook_secret and secret != cfg.webhook_secret:
            return self._finish(403, b"forbidden")

        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            update = json.loads(raw or b"{}")
        except ValueError:
            return self._finish(400, b"bad json")

        # Завжди відповідаємо 200, щоб Telegram не ретраїв при помилці обробки.
        try:
            llm = LLM(cfg=cfg)
            seed = load_seed(cfg.seed_path)
            result = handle_update(update, cfg, llm, seed)
            if result:
                chat_id, reply = result
                bot = Bot(cfg.telegram_token)
                try:
                    bot.send_chat_action(chat_id, "typing")
                except Exception:
                    pass
                bot.send_message(chat_id, reply)
        except Exception:
            log.exception("webhook handling failed")
        return self._finish(200, b"ok")

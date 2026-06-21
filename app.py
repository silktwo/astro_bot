"""Vercel Python entrypoint (WSGI).

Один застосунок маршрутизує обидва шляхи:
  POST /api/telegram — Telegram webhook
  GET  /api/cron     — щоденний прогноз (Vercel Cron)
"""
from __future__ import annotations

import json
import logging
import os

_ROOT = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("SWISSEPH_PATH", os.path.join(_ROOT, "ephe"))
os.environ.setdefault("SEED_PATH", os.path.join(_ROOT, "data", "anna_natal.json"))

from astro_bot import config
from astro_bot.handlers import daily_text, handle_update
from astro_bot.llm import LLM
from astro_bot.natal_import import load_seed
from astro_bot.telegram_api import Bot

log = logging.getLogger("astro_bot")


def _resp(start_response, status: str, body=b"ok"):
    if isinstance(body, str):
        body = body.encode("utf-8")
    start_response(status, [("Content-Type", "text/plain; charset=utf-8"),
                            ("Content-Length", str(len(body)))])
    return [body]


def _telegram(environ, start_response):
    cfg = config.load()
    # Telegram передає секрет вебхука у цьому заголовку.
    secret = environ.get("HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN", "")
    if cfg.webhook_secret and secret != cfg.webhook_secret:
        return _resp(start_response, "403 Forbidden", b"forbidden")
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        length = 0
    raw = environ["wsgi.input"].read(length) if length else b"{}"
    try:
        update = json.loads(raw or b"{}")
    except ValueError:
        return _resp(start_response, "400 Bad Request", b"bad json")
    # Завжди 200, щоб Telegram не ретраїв при внутрішній помилці.
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
    return _resp(start_response, "200 OK", b"ok")


def _cron(environ, start_response):
    cfg = config.load()
    cron_secret = os.environ.get("CRON_SECRET", "")
    auth = environ.get("HTTP_AUTHORIZATION", "")
    if cron_secret and auth != f"Bearer {cron_secret}":
        return _resp(start_response, "401 Unauthorized", b"unauthorized")
    if not cfg.recipient_chat_id:
        return _resp(start_response, "500 Internal Server Error", b"RECIPIENT_CHAT_ID not set")
    try:
        llm = LLM(cfg=cfg)
        seed = load_seed(cfg.seed_path)
        text = daily_text(cfg, llm, seed)
        Bot(cfg.telegram_token).send_message(cfg.recipient_chat_id, text)
        return _resp(start_response, "200 OK", b"sent")
    except Exception:
        log.exception("daily cron failed")
        return _resp(start_response, "500 Internal Server Error", b"error")


def app(environ, start_response):
    path = environ.get("PATH_INFO", "").rstrip("/")
    method = environ.get("REQUEST_METHOD", "GET")
    if path == "/api/telegram" and method == "POST":
        return _telegram(environ, start_response)
    if path == "/api/cron":
        return _cron(environ, start_response)
    if path in ("", "/health"):
        return _resp(start_response, "200 OK", b"astro_bot ok")
    return _resp(start_response, "404 Not Found", b"not found")

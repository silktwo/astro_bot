"""Stateless-логіка бота для serverless (Vercel).

Один користувач (карта засіджена з файлу). Памʼять = натальна карта в репо;
журнал переписки не ведеться.
"""
import datetime as dt

import pytz

from astro_bot import config, prompts
from astro_bot.forecast import build_daily

_PHOTO_REPLY = ("Поки що я не вмію роздивлятись фото 🙈 Опиши словами, що там або що "
                "тебе хвилює — і я підкажу, як це резонує з твоїм днем і картою.")
_START_REPLY = ("Привіт, сонечко 🌙 Я вже знаю твою карту. Щодня о 18:00 надсилатиму "
                "тобі прогноз сюди. Напиши /today, щоб отримати прогноз прямо зараз, "
                "або просто запитай мене будь-що.")


def daily_text(cfg: config.Config, llm, seed: dict) -> str:
    """Денний прогноз із засідженої карти на сьогодні (за таймзоною прогнозу)."""
    now = dt.datetime.now(pytz.timezone(cfg.push_tz))
    return build_daily(seed, now.year, now.month, now.day, llm, seed.get("name"))


def answer_text(cfg: config.Config, llm, user_text: str, seed: dict) -> str:
    """Відповідь на вільне питання, спираючись на карту (без історії діалогу)."""
    ctx = seed.get("card_text") or seed.get("highlights") or ""
    msgs = [
        {"role": "system", "content": prompts.CHAT_SYSTEM + f"\nЇї натальна карта:\n{ctx}"},
        {"role": "user", "content": user_text},
    ]
    return llm.chat(msgs)


def handle_update(update: dict, cfg: config.Config, llm, seed: dict):
    """Маршрутизує Telegram-апдейт. Повертає (chat_id, reply_text) або None."""
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return None
    chat_id = msg["chat"]["id"]
    if "photo" in msg:
        return chat_id, _PHOTO_REPLY
    text = msg.get("text", "")
    if not text:
        return None
    if text.startswith("/"):
        cmd = text[1:].split()[0].split("@")[0].lower()
        if cmd == "start":
            return chat_id, _START_REPLY
        if cmd == "today":
            return chat_id, daily_text(cfg, llm, seed)
        # будь-яка інша команда — трактуємо як питання
    return chat_id, answer_text(cfg, llm, text, seed)

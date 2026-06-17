import asyncio
import base64
import datetime as dt
import re
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import (Application, CommandHandler, MessageHandler,
                          filters, ContextTypes)
import pytz

from astro_bot import config, prompts
from astro_bot.store import Store
from astro_bot.llm import LLM
from astro_bot.forecast import build_daily
from astro_bot.natal_import import load_seed

log = logging.getLogger("astro_bot")

_DATE_RE = re.compile(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})")
_TIME_RE = re.compile(r"(\d{1,2}):(\d{2})")


def parse_birth(text, geocode):
    """Парсить 'ДД.ММ.РРРР [ГГ:ХХ] Місто'. geocode(city)->(lat,lon,tz_offset)."""
    m = _DATE_RE.search(text)
    if not m:
        raise ValueError("Не бачу дати у форматі ДД.ММ.РРРР")
    day, month, year = int(m[1]), int(m[2]), int(m[3])
    tm = _TIME_RE.search(text)
    if tm:
        hour = int(tm[1]) + int(tm[2]) / 60.0
        time_known = True
    else:
        hour, time_known = 12.0, False
    city = text[m.end():]
    if tm:
        city = city.replace(tm.group(0), "")
    city = city.strip(" ,.-")
    if not city:
        raise ValueError("Не бачу міста народження")
    lat, lon, tz_offset = geocode(city)
    return {"year": year, "month": month, "day": day, "hour": hour,
            "lat": lat, "lon": lon, "tz_offset": tz_offset,
            "city": city, "time_known": time_known}


def _geocode(city):
    from geopy.geocoders import Nominatim
    from timezonefinder import TimezoneFinder
    loc = Nominatim(user_agent="astro-bot").geocode(city)
    if not loc:
        raise ValueError(f"Не знайшов місто: {city}")
    tf = TimezoneFinder()
    tzname = tf.timezone_at(lat=loc.latitude, lng=loc.longitude) or "UTC"
    offset = pytz.timezone(tzname).utcoffset(dt.datetime(2000, 1, 1)).total_seconds() / 3600
    return loc.latitude, loc.longitude, offset


# ── Telegram handlers ───────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    store: Store = ctx.bot_data["store"]
    uid = update.effective_user.id
    # Перший контакт: запамʼятовуємо чат і одразу привʼязуємо засіджену карту.
    if not store.get_natal(uid):
        seed = ctx.bot_data.get("seed")
        if seed:
            store.set_natal(uid, seed)
    await update.message.reply_text("Привіт, сонечко 🌙 Я вже знаю твою карту. "
        "Щодня о 18:00 надсилатиму тобі прогноз сюди. Можеш питати будь-що — "
        "або напиши /today, щоб отримати прогноз прямо зараз.")


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    store: Store = ctx.bot_data["store"]
    llm: LLM = ctx.bot_data["llm"]
    uid = update.effective_user.id
    text = update.message.text
    natal = store.get_natal(uid)
    if natal is None:
        try:
            data = parse_birth(text, geocode=_geocode)
        except ValueError as ex:
            await update.message.reply_text(f"{ex}. Спробуй ще раз 🙏")
            return
        store.set_natal(uid, data)
        await update.message.reply_text("Готово ✨ Карту склала. "
            "Сьогодні о 18:00 буде прогноз — або напиши /today прямо зараз.")
        return
    store.add_message(uid, "user", text)
    history = store.recent_messages(uid, limit=12)
    natal_ctx = natal.get("card_text") or natal.get("highlights") or ""
    msgs = [{"role": "system", "content": prompts.CHAT_SYSTEM +
             f"\nЇї натальна карта:\n{natal_ctx}"}] + history
    await update.message.chat.send_action("typing")
    answer = await asyncio.to_thread(llm.chat, msgs)
    store.add_message(uid, "assistant", answer)
    await update.message.reply_text(answer)


async def on_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # Vision-моделі недоступні на поточному opencode-плані (gemini/claude → 401),
    # текстові моделі зображення не приймають. Тому просимо опис словами.
    await update.message.reply_text(
        "Поки що я не вмію роздивлятись фото 🙈 Опиши словами, що там або що тебе "
        "хвилює — і я підкажу, як це резонує з твоїм днем і картою.")


async def cmd_today(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    store: Store = ctx.bot_data["store"]
    llm: LLM = ctx.bot_data["llm"]
    uid = update.effective_user.id
    natal = store.get_natal(uid)
    if not natal:
        await update.message.reply_text("Спершу надішли дату й місто народження 🙏")
        return
    now = dt.datetime.now()
    await update.message.chat.send_action("typing")
    text = await asyncio.to_thread(build_daily, natal, now.year, now.month, now.day,
                                   llm, natal.get("name"))
    store.add_message(uid, "assistant", "Денний прогноз: " + text)
    await update.message.reply_text(text)


async def cmd_setbirth(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Адмін: /setbirth <user_id> ДД.ММ.РРРР ГГ:ХХ Місто"""
    cfg: config.Config = ctx.bot_data["cfg"]
    store: Store = ctx.bot_data["store"]
    if update.effective_user.id != cfg.admin_id:
        return
    parts = update.message.text.split(maxsplit=1)[1]
    target_id, rest = parts.split(maxsplit=1)
    data = parse_birth(rest, geocode=_geocode)
    store.set_natal(int(target_id), data)
    await update.message.reply_text(f"Карту для {target_id} збережено ✨")


# ── Scheduler ───────────────────────────────────────────────────────
async def _push_daily(app, cfg, store, llm):
    # Шлемо всім чатам, що вже стартували бота (мають карту). ID не потрібен.
    now = dt.datetime.now(pytz.timezone(cfg.push_tz))
    for uid in store.all_users_with_natal():
        natal = store.get_natal(uid)
        try:
            text = await asyncio.to_thread(build_daily, natal, now.year, now.month,
                                           now.day, llm, natal.get("name"))
            await app.bot.send_message(chat_id=uid, text=text)
        except Exception:
            log.exception("daily push failed for %s", uid)


def build_app(cfg: config.Config, store: Store, llm: LLM) -> Application:
    app = Application.builder().token(cfg.telegram_token).concurrent_updates(True).build()
    app.bot_data.update({"cfg": cfg, "store": store, "llm": llm})
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("today", cmd_today))
    app.add_handler(CommandHandler("setbirth", cmd_setbirth))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    return app


def main():
    logging.basicConfig(level=logging.INFO)
    cfg = config.load()
    store = Store("/data/natal.db")
    llm = LLM(cfg=cfg)
    app = build_app(cfg, store, llm)
    try:
        app.bot_data["seed"] = load_seed(cfg.seed_path)
    except Exception:
        log.warning("seed not loaded from %s", cfg.seed_path)

    sched = AsyncIOScheduler(timezone=pytz.timezone(cfg.push_tz))
    sched.add_job(lambda: app.create_task(_push_daily(app, cfg, store, llm)),
                  "cron", hour=cfg.push_hour, minute=0)

    async def _post_init(_):
        sched.start()
    app.post_init = _post_init
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

# astro_bot на Vercel — дизайн

**Дата:** 2026-06-21
**Мета:** перевести персональний астро-бот з self-hosted (polling + SQLite + APScheduler на Umbrel) у Vercel serverless, без зовнішніх сервісів — усі дані в репозиторії.

## Контекст і обмеження

Vercel не дає постійного диска: файлова система serverless-функції **read-only** (крім ефемерного `/tmp`), записати щось назад у файли репо в рантаймі неможливо. Тому:

- Дані, які бот **читає** (натальна карта Анни), живуть як файл у репо — `data/anna_natal.json`. Це і є «памʼять про користувача».
- Бот **stateless**: журнал переписки не ведеться (нема де персистити без зовнішньої БД). Кожне повідомлення обробляється самостійно, спираючись на карту.
- Один користувач (Анна). Онбординг нових юзерів, `/setbirth`, геокодинг — прибираються (карта засіджена).

Це свідомий tradeoff: втрачається багатоходова памʼять діалогу заради «нуль сторонніх сервісів, усе в репо».

## Архітектура

Дві serverless-функції (формат Vercel Python — клас `handler(BaseHTTPRequestHandler)`):

### `api/telegram.py` — webhook
- Telegram шле POST з апдейтом на цей endpoint (замість polling).
- Валідація заголовка `X-Telegram-Bot-Api-Secret-Token` проти `TELEGRAM_WEBHOOK_SECRET`.
- Логіка:
  - `/start`, `/today` → денний прогноз (`forecast.build_daily` з картою).
  - фото → ввічлива відмова (vision недоступний на плані).
  - будь-який текст → відповідь LLM із картою як системним контекстом (`prompts.CHAT_SYSTEM` + `card_text`). Без історії.
- Відповідь Telegram надсилається через прямий виклик Bot API (`sendMessage`/`sendChatAction`) по HTTP — без бібліотеки `python-telegram-bot` (легший cold start).

### `api/cron.py` — щоденний прогноз
- Викликається Vercel Cron. Валідація `Authorization: Bearer $CRON_SECRET`.
- Будує прогноз із карти й шле на `RECIPIENT_CHAT_ID` (Telegram chat_id Анни) через Bot API.
- Розклад у `vercel.json`: `0 16 * * *` (UTC) = 18:00 за літнім Варшавським часом. Узимку спрацює о 17:00 (Vercel Cron не має таймзон; Hobby — раз/добу). Зсув DST — прийнятний для особистого бота, задокументований.

### Спільна логіка (`src/astro_bot/`, перевикористання)
- `ephemeris.py`, `forecast.py`, `llm.py`, `prompts.py`, `natal_import.py` — **без змін** (вони чисті, без I/O стану).
- `config.py` — спрощується: додається `recipient_chat_id`, `webhook_secret`; прибираються поля онбордингу.
- `store.py`, `bot.py` (polling-раннер) — **видаляються** (SQLite/APScheduler більше не потрібні).

### Ефемериди
3 файли Swiss Ephemeris (`sepl_18.se1`, `semo_18.se1`, `seas_18.se1`, ~кілька МБ) кладуться в репо у `ephe/` і комітяться (раніше тягнулись у Dockerfile при білді). `SWISSEPH_PATH=ephe`.

## Конфігурація (env vars на Vercel)

| Змінна | Призначення |
|---|---|
| `TELEGRAM_BOT_TOKEN` | токен бота |
| `OPENCODE_API_KEY` / `OPENCODE_BASE_URL` | LLM API |
| `RECIPIENT_CHAT_ID` | chat_id Анни для денної розсилки |
| `TELEGRAM_WEBHOOK_SECRET` | секрет валідації вебхука |
| `CRON_SECRET` | секрет валідації cron (ставить Vercel) |
| `PUSH_TZ` | таймзона тексту прогнозу (`Europe/Warsaw`) |
| `SWISSEPH_PATH` | `ephe` |
| `SEED_PATH` | `data/anna_natal.json` |

## Файли проєкту (після змін)

```
api/telegram.py        webhook
api/cron.py            щоденний прогноз
src/astro_bot/         ephemeris, forecast, llm, prompts, natal_import, config, handlers
data/anna_natal.json   карта (read-only памʼять)
ephe/*.se1             ефемериди
vercel.json            crons + maxDuration=60
requirements.txt       openai, pyswisseph, pytz  (для Vercel Python runtime)
README.md              оновлено: деплой на Vercel, реєстрація вебхука
```

## Деплой (разові кроки користувача, у README)

1. Import репо у Vercel.
2. Додати env vars (з бекапу `~/astro-bot-backup/.env` + `RECIPIENT_CHAT_ID`, `TELEGRAM_WEBHOOK_SECRET`).
3. Зареєструвати вебхук: `setWebhook` на `https://<project>.vercel.app/api/telegram` із `secret_token`.
4. Cron уже в `vercel.json`.

## Тестування
- `pytest` на чистій логіці (ephemeris/forecast/prompts/parse) — лишається зеленим.
- Додати тести на handlers: маршрутизація команд, валідація секретів, формування відповіді (з мок-LLM і мок-Bot API).

## Поза обсягом (YAGNI)
- Мультиюзер, онбординг, геокодинг, vision, памʼять діалогу, зовнішня БД.

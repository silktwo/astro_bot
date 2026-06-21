# astro_bot 🔭

Персональний Telegram-бот для денного астропрогнозу, що **живе на Vercel** (serverless).
Щодня о 18:00 (Europe/Warsaw) надсилає прогноз на основі натальної карти й відповідає
на питання у вільній формі. Карта рахується через Swiss Ephemeris, тексти генерує LLM.

Бот **stateless** і **на одного користувача**: «памʼять» — це натальна карта у файлі
`data/anna_natal.json` (read-only, бо на Vercel немає постійного диска). Журнал
переписки не ведеться.

## Архітектура

```
api/
  telegram.py      webhook: приймає апдейти Telegram (POST), відповідає через Bot API
  cron.py          щоденний прогноз (GET від Vercel Cron)
src/astro_bot/
  handlers.py      stateless-логіка: маршрутизація апдейтів, збірка прогнозу/відповіді
  telegram_api.py  мінімальний клієнт Telegram Bot API (stdlib)
  config.py        конфіг з env-змінних, ідентифікатори моделей
  ephemeris.py     положення планет і транзити (pyswisseph)
  forecast.py      збірка тексту денного прогнозу
  llm.py           клієнт LLM (OpenAI-сумісний API)
  prompts.py       системні промпти
  natal_import.py  завантаження карти з seed JSON
data/anna_natal.json   натальна карта (read-only памʼять)
ephe/*.se1             файли Swiss Ephemeris
vercel.json            функції (maxDuration) + cron-розклад
requirements.txt       залежності для Vercel Python runtime
tests/                 pytest
```

## Деплой на Vercel

1. **Import** репозиторію у Vercel (Framework Preset: *Other*).
2. **Environment Variables** (значення — з бекапу `.env`):

   | Змінна | Опис |
   |---|---|
   | `TELEGRAM_BOT_TOKEN` | токен від @BotFather |
   | `RECIPIENT_CHAT_ID` | chat_id отримувача денного прогнозу |
   | `TELEGRAM_WEBHOOK_SECRET` | довільний секрет для валідації вебхука |
   | `OPENCODE_API_KEY` / `OPENCODE_BASE_URL` | LLM API |
   | `PUSH_TZ` | таймзона прогнозу (`Europe/Warsaw`) |

   `CRON_SECRET` Vercel створює сам; `SWISSEPH_PATH`/`SEED_PATH` визначаються з кореня репо.

3. **Deploy.** Cron (`vercel.json`) активується автоматично: `0 16 * * *` UTC = 18:00 за
   літнім київ./варш. часом (узимку — 17:00; Vercel Cron без таймзон, на Hobby — раз/добу).

4. **Зареєструвати webhook** (одноразово):

   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/setWebhook" \
     -d "url=https://<project>.vercel.app/api/telegram" \
     -d "secret_token=<TELEGRAM_WEBHOOK_SECRET>"
   ```

## Команди бота

- `/start` — привітання.
- `/today` — денний прогноз прямо зараз.
- будь-який текст — питання до астролога (відповідь спирається на карту).
- фото — ввічлива відмова (vision недоступний на поточному плані).

## Локальна розробка / тести

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Стек

Python 3.11+ · pyswisseph · OpenAI SDK · pytz · Vercel (serverless functions + cron)

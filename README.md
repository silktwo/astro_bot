# astro_bot 🔭

Персональний Telegram-бот для денного астропрогнозу. Щодня о 18:00 (Europe/Warsaw)
надсилає користувачу прогноз на основі його натальної карти, а також відповідає на
запитання у вільній формі. Натальна карта рахується через Swiss Ephemeris, тексти
генерує LLM.

## Можливості

- **Денний прогноз** — автоматична розсилка о 18:00 усім, хто запустив бота (`/today` — отримати зараз).
- **Чат** — вільні питання з урахуванням натальної карти та історії діалогу.
- **Розпізнавання дати народження** з тексту `ДД.ММ.РРРР [ГГ:ХХ] Місто` (геокодинг + визначення таймзони).
- **Адмін-команда** `/setbirth <user_id> ДД.ММ.РРРР ГГ:ХХ Місто` — задати карту іншому користувачу.

## Структура

```
src/astro_bot/
  bot.py           точка входу: Telegram-хендлери, планувальник розсилки
  config.py        конфіг з env-змінних, ідентифікатори моделей
  ephemeris.py     розрахунки положень планет (Swiss Ephemeris / pyswisseph)
  natal_import.py  завантаження засідженої натальної карти (seed JSON)
  forecast.py      збірка тексту денного прогнозу
  llm.py           клієнт LLM (OpenAI-сумісний API)
  prompts.py       системні промпти
  store.py         сховище натальних карт та історії (SQLite: /data/natal.db)
data/
  anna_natal.json  засіджена натальна карта
docs/
  specs/, plans/   дизайн і план реалізації
tests/             pytest-набір на всі модулі
Dockerfile         образ (підтягує файли Swiss Ephemeris)
docker-compose.yml сервіс + іменований volume astro-data для БД
```

## Запуск

### Docker (рекомендовано)

```bash
cp .env.example .env   # і заповнити реальними значеннями
docker compose up -d --build
```

БД зберігається в іменованому volume `astro-data` (`/data/natal.db` всередині контейнера).

### Локально

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env    # заповнити
python -m astro_bot.bot
```

Тести:

```bash
pytest
```

## Конфігурація (`.env`)

| Змінна | Опис |
|---|---|
| `TELEGRAM_BOT_TOKEN` | токен бота від @BotFather |
| `OPENCODE_API_KEY` | ключ LLM-провайдера (OpenAI-сумісний) |
| `OPENCODE_BASE_URL` | базовий URL API |
| `ADMIN_TELEGRAM_ID` | Telegram-ID адміна (для `/setbirth`) |
| `PUSH_HOUR` | година денної розсилки (за замовч. `18`) |
| `PUSH_TZ` | таймзона розсилки (`Europe/Warsaw`) |
| `SWISSEPH_PATH` | шлях до файлів Swiss Ephemeris |
| `SEED_PATH` | шлях до seed-JSON натальної карти |

> `.env` із реальними секретами в репозиторій **не** комітиться (див. `.gitignore`).

## Стек

Python 3.11+ · python-telegram-bot · pyswisseph · APScheduler · OpenAI SDK · geopy · timezonefinder

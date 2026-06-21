from unittest.mock import MagicMock

from astro_bot import config, handlers

CFG = config.Config(
    telegram_token="t", api_key="k", base_url="u", recipient_chat_id=1,
    webhook_secret="s", push_tz="Europe/Warsaw", swisseph_path="ephe",
    seed_path="data/anna_natal.json",
)
SEED = {"name": "Анна", "card_text": "карта", "planets": {"Sun": 100.0}}


def _msg(text=None, photo=False, chat_id=42):
    m = {"chat": {"id": chat_id}}
    if text is not None:
        m["text"] = text
    if photo:
        m["photo"] = [{"file_id": "x"}]
    return {"message": m}


def test_start_returns_greeting():
    llm = MagicMock()
    chat_id, reply = handlers.handle_update(_msg("/start"), CFG, llm, SEED)
    assert chat_id == 42
    assert "Привіт" in reply
    llm.chat.assert_not_called()


def test_today_builds_forecast(monkeypatch):
    monkeypatch.setattr(handlers, "build_daily",
                        lambda *a, **k: "Прогноз на сьогодні")
    chat_id, reply = handlers.handle_update(_msg("/today"), CFG, MagicMock(), SEED)
    assert reply == "Прогноз на сьогодні"


def test_free_text_calls_llm_with_card_context():
    llm = MagicMock()
    llm.chat.return_value = "Відповідь"
    chat_id, reply = handlers.handle_update(_msg("що з коханням?"), CFG, llm, SEED)
    assert reply == "Відповідь"
    sent = llm.chat.call_args[0][0]
    assert sent[0]["role"] == "system" and "карта" in sent[0]["content"]
    assert sent[1] == {"role": "user", "content": "що з коханням?"}


def test_photo_declines_without_llm():
    llm = MagicMock()
    chat_id, reply = handlers.handle_update(_msg(photo=True), CFG, llm, SEED)
    assert "фото" in reply
    llm.chat.assert_not_called()


def test_unknown_command_treated_as_question():
    llm = MagicMock()
    llm.chat.return_value = "ок"
    _, reply = handlers.handle_update(_msg("/щось"), CFG, llm, SEED)
    assert reply == "ок"


def test_non_message_update_ignored():
    assert handlers.handle_update({"callback_query": {}}, CFG, MagicMock(), SEED) is None

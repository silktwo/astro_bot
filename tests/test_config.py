from astro_bot import config


def test_loads_models():
    assert config.MODEL_REASON == "qwen3.7-plus"
    assert config.MODEL_WRITE == "qwen3.7-plus"
    assert config.MODEL_FALLBACK == "glm-5.2"


def test_defaults(monkeypatch):
    monkeypatch.delenv("PUSH_TZ", raising=False)
    monkeypatch.delenv("RECIPIENT_CHAT_ID", raising=False)
    cfg = config.load()
    assert cfg.push_tz == "Europe/Warsaw"
    assert cfg.recipient_chat_id is None
    assert cfg.seed_path.endswith("anna_natal.json")


def test_recipient_chat_id_parsed(monkeypatch):
    monkeypatch.setenv("RECIPIENT_CHAT_ID", "281735938")
    assert config.load().recipient_chat_id == 281735938

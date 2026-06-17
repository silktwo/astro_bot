from astro_bot import config


def test_loads_models():
    assert config.MODEL_REASON == "qwen3.7-plus"
    assert config.MODEL_WRITE == "qwen3.7-plus"
    assert config.MODEL_VISION == "gemini-3.5-flash"


def test_push_defaults(monkeypatch):
    monkeypatch.delenv("PUSH_HOUR", raising=False)
    monkeypatch.delenv("PUSH_TZ", raising=False)
    cfg = config.load()
    assert cfg.push_hour == 18
    assert cfg.push_tz == "Europe/Warsaw"
    assert cfg.seed_path.endswith("anna_natal.json")

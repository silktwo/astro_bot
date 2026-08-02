import io
import json

import app
from api import cron as cron_api
from api import debug as debug_api
from api import health as health_api
from api import telegram as telegram_api


def _start_response(status, headers):
    _start_response.status = status
    _start_response.headers = headers


def _environ(path="/api/cron", method="GET", body=b"", auth=""):
    return {
        "PATH_INFO": path,
        "REQUEST_METHOD": method,
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
        "HTTP_AUTHORIZATION": auth,
    }


def _telegram_environ(text="привіт", chat_id=42):
    body = json.dumps({"message": {"chat": {"id": chat_id}, "text": text}}).encode()
    return _environ(path="/api/telegram", method="POST", body=body)


def test_cron_requires_recipient_chat_id(monkeypatch):
    monkeypatch.delenv("RECIPIENT_CHAT_ID", raising=False)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("OPENCODE_API_KEY", "key")
    monkeypatch.setenv("CRON_SECRET", "secret")

    body = b"".join(cron_api.app(_environ(auth="Bearer secret"), _start_response))

    assert _start_response.status == "500 Internal Server Error"
    assert body == b"RECIPIENT_CHAT_ID not set"


def test_cron_sends_daily_text_to_configured_recipient(monkeypatch):
    sent = []

    class FakeBot:
        def __init__(self, token):
            self.token = token

        def send_message(self, chat_id, text):
            sent.append((self.token, chat_id, text))

    monkeypatch.setenv("RECIPIENT_CHAT_ID", "42")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("OPENCODE_API_KEY", "key")
    monkeypatch.setenv("CRON_SECRET", "secret")
    monkeypatch.setattr(app, "Bot", FakeBot)
    monkeypatch.setattr(app, "daily_text", lambda cfg, llm, seed: "daily")
    monkeypatch.setattr(app, "load_seed", lambda path: {"name": "Анна", "planets": {}})

    body = b"".join(cron_api.app(_environ(auth="Bearer secret"), _start_response))

    assert _start_response.status == "200 OK"
    assert body == b"sent"
    assert sent == [("token", 42, "daily")]


def test_telegram_sends_failure_reply_when_llm_fails(monkeypatch):
    sent = []

    class FailingLLM:
        def __init__(self, cfg):
            self.cfg = cfg

        def chat(self, messages):
            raise RuntimeError("provider unavailable")

    class FakeBot:
        def __init__(self, token):
            self.token = token

        def send_chat_action(self, chat_id, action):
            sent.append((chat_id, action))

        def send_message(self, chat_id, text):
            sent.append((chat_id, text))

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("OPENCODE_API_KEY", "key")
    monkeypatch.delenv("TELEGRAM_WEBHOOK_SECRET", raising=False)
    monkeypatch.setattr(app, "LLM", FailingLLM)
    monkeypatch.setattr(app, "Bot", FakeBot)
    monkeypatch.setattr(app, "load_seed", lambda path: {"name": "Анна", "card_text": "карта"})

    body = b"".join(telegram_api.app(_telegram_environ(), _start_response))

    assert _start_response.status == "200 OK"
    assert body == b"ok"
    assert sent[-1][0] == 42
    assert "тимчасово не можу" in sent[-1][1]


def test_health_function_returns_ok():
    body = b"".join(health_api.app(_environ(path="/api/health"), _start_response))

    assert _start_response.status == "200 OK"
    assert body == b"astro_bot ok"


def test_debug_function_reports_env_without_secrets(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("OPENCODE_API_KEY", "key")
    monkeypatch.delenv("RECIPIENT_CHAT_ID", raising=False)
    monkeypatch.setattr(app, "telegram_get_me", lambda token: "AstroEphemerisBot")

    body = b"".join(debug_api.app(_environ(path="/api/debug"), _start_response))

    assert _start_response.status == "200 OK"
    assert json.loads(body) == {
        "telegram_token": True,
        "opencode_api_key": True,
        "recipient_chat_id": False,
        "telegram_get_me": "AstroEphemerisBot",
    }

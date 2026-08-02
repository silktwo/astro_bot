import io

import app


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


def test_cron_requires_recipient_chat_id(monkeypatch):
    monkeypatch.delenv("RECIPIENT_CHAT_ID", raising=False)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("OPENCODE_API_KEY", "key")
    monkeypatch.setenv("CRON_SECRET", "secret")

    body = b"".join(app.app(_environ(auth="Bearer secret"), _start_response))

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

    body = b"".join(app.app(_environ(auth="Bearer secret"), _start_response))

    assert _start_response.status == "200 OK"
    assert body == b"sent"
    assert sent == [("token", 42, "daily")]

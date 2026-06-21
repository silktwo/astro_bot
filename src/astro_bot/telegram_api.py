"""Мінімальний клієнт Telegram Bot API через stdlib (без python-telegram-bot).

Підходить для serverless: жодних фонових циклів, тільки прямі HTTP-виклики.
"""
import json
import urllib.request


class Bot:
    def __init__(self, token: str, timeout: float = 20.0):
        self.base = f"https://api.telegram.org/bot{token}"
        self.timeout = timeout

    def _post(self, method: str, payload: dict) -> dict:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base}/{method}", data=data,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.load(resp)

    def send_message(self, chat_id, text: str) -> dict:
        return self._post("sendMessage", {"chat_id": chat_id, "text": text})

    def send_chat_action(self, chat_id, action: str = "typing") -> dict:
        return self._post("sendChatAction", {"chat_id": chat_id, "action": action})

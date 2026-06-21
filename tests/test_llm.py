from unittest.mock import MagicMock

from astro_bot.llm import LLM
from astro_bot import config


def _fake_client():
    client = MagicMock()
    resp = MagicMock()
    resp.choices = [MagicMock(message=MagicMock(content="ok"))]
    client.chat.completions.create.return_value = resp
    return client


def test_reason_uses_reason_model():
    llm = LLM(client=_fake_client())
    out = llm.reason("аналізуй")
    assert out == "ok"
    kwargs = llm.client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == config.MODEL_REASON


def test_write_uses_write_model():
    llm = LLM(client=_fake_client())
    llm.write("пиши прогноз")
    assert llm.client.chat.completions.create.call_args.kwargs["model"] == config.MODEL_WRITE


def test_write_falls_back_on_error():
    client = _fake_client()
    good = client.chat.completions.create.return_value
    client.chat.completions.create.side_effect = [Exception("429"), good]
    llm = LLM(client=client)
    assert llm.write("x") == "ok"
    assert client.chat.completions.create.call_args.kwargs["model"] == config.MODEL_FALLBACK


def test_see_sends_image():
    llm = LLM(client=_fake_client())
    llm.see("base64data", "опиши")
    msg = llm.client.chat.completions.create.call_args.kwargs["messages"][0]
    assert any(part["type"] == "image_url" for part in msg["content"])

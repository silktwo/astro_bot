from openai import OpenAI

from astro_bot import config


class LLM:
    def __init__(self, cfg: config.Config | None = None, client=None):
        if client is not None:
            self.client = client
        else:
            self.client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)

    def _chat(self, model, messages, fallback=None):
        try:
            r = self.client.chat.completions.create(model=model, messages=messages)
            return r.choices[0].message.content
        except Exception:
            if fallback is None:
                raise
            r = self.client.chat.completions.create(model=fallback, messages=messages)
            return r.choices[0].message.content

    def reason(self, prompt, system=None):
        msgs = ([{"role": "system", "content": system}] if system else []) + \
               [{"role": "user", "content": prompt}]
        return self._chat(config.MODEL_REASON, msgs, fallback=config.MODEL_FALLBACK)

    def write(self, prompt, system=None):
        msgs = ([{"role": "system", "content": system}] if system else []) + \
               [{"role": "user", "content": prompt}]
        return self._chat(config.MODEL_WRITE, msgs, fallback=config.MODEL_FALLBACK)

    def chat(self, messages):
        return self._chat(config.MODEL_WRITE, messages, fallback=config.MODEL_FALLBACK)

    def see(self, image_b64, prompt):
        msgs = [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url",
             "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
        ]}]
        return self._chat(config.MODEL_VISION, msgs, fallback=config.MODEL_FALLBACK)

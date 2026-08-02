from astro_bot import prompts


def test_reason_prompt_includes_aspects_and_both_systems():
    aspects = [{"transit": "Mars", "natal": "Sun", "aspect": "square", "orb": 1.2}]
    signs_trop = {"Sun": "Cancer"}
    signs_sid = {"Sun": "Gemini"}
    p = prompts.reason_prompt(aspects, signs_trop, signs_sid)
    assert "Mars" in p and "square" in p
    assert "Cancer" in p and "Gemini" in p


def test_write_system_is_ukrainian_warm():
    s = prompts.WRITE_SYSTEM
    assert "українськ" in s.lower()


def test_write_system_requests_personal_day_sections():
    s = prompts.WRITE_SYSTEM
    assert "120-180 слів" in s
    assert "як її можуть бачити люди" in s
    assert "що краще вдягнути" in s
    assert "що носити" in s
    assert "що робити" in s


def test_daily_prompt_requests_personal_guidance():
    p = prompts.daily_prompt([], {}, {}, name="Анна")
    assert "Анна" in p
    assert "опиши її в цей день" in p
    assert "як її можуть бачити люди" in p
    assert "що краще вдягнути" in p

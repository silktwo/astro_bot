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

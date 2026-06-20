from unittest.mock import MagicMock

from astro_bot.forecast import build_daily


def test_build_daily_pipeline():
    natal = {"name": "Анна", "planets": {
        "Sun": 104.68, "Moon": 168.68, "Mercury": 104.72, "Venus": 111.57,
        "Mars": 103.28, "Jupiter": 61.27, "Saturn": 57.22, "Uranus": 320.15,
        "Neptune": 305.77, "Pluto": 250.6}}
    llm = MagicMock()
    llm.write.return_value = "Короткий прогноз українською."
    text = build_daily(natal, 2026, 6, 17, llm, name="Анна")
    assert text == "Короткий прогноз українською."
    # один прохід: лише write, без окремого reason
    assert llm.write.called
    assert not llm.reason.called

from astro_bot.bot import parse_birth


def test_parse_birth_full():
    geo = lambda city: (50.45, 30.52, 3.0)
    d = parse_birth("15.06.1995 14:30 Київ", geocode=geo)
    assert d["year"] == 1995 and d["month"] == 6 and d["day"] == 15
    assert d["hour"] == 14.5
    assert d["city"] == "Київ" and d["lat"] == 50.45


def test_parse_birth_missing_time_defaults_noon():
    geo = lambda city: (50.45, 30.52, 3.0)
    d = parse_birth("15.06.1995 Київ", geocode=geo)
    assert d["hour"] == 12.0
    assert d.get("time_known") is False

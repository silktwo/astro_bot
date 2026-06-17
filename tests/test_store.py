from astro_bot.store import Store


def test_save_and_get_natal(tmp_path):
    s = Store(str(tmp_path / "t.db"))
    data = {"year": 1995, "month": 6, "day": 15, "hour": 14.5,
            "lat": 50.45, "lon": 30.52, "tz_offset": 3.0, "city": "Kyiv"}
    s.set_natal(42, data)
    assert s.get_natal(42)["city"] == "Kyiv"


def test_get_missing_natal_is_none(tmp_path):
    s = Store(str(tmp_path / "t.db"))
    assert s.get_natal(99) is None


def test_history_roundtrip(tmp_path):
    s = Store(str(tmp_path / "t.db"))
    s.add_message(42, "user", "привіт")
    s.add_message(42, "assistant", "вітаю")
    hist = s.recent_messages(42, limit=10)
    assert [m["role"] for m in hist] == ["user", "assistant"]

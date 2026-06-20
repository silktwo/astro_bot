from astro_bot import ephemeris as e


def test_tropical_sun_j2000():
    # 2000-01-01 12:00 UT: Сонце ~280.4° (Козеріг) у тропіці
    pos = e.planet_positions(2000, 1, 1, 12.0, sidereal=False)
    assert abs(pos["Sun"] - 280.4) < 1.0


def test_sidereal_differs_from_tropical():
    trop = e.planet_positions(2000, 1, 1, 12.0, sidereal=False)["Sun"]
    sid = e.planet_positions(2000, 1, 1, 12.0, sidereal=True)["Sun"]
    diff = (trop - sid) % 360
    assert 23.0 < diff < 25.0


def test_natal_chart_has_all_planets():
    chart = e.natal_chart(1995, 6, 15, 14.5, 50.45, 30.52, sidereal=False)
    for p in ["Sun", "Moon", "Mercury", "Venus", "Mars",
              "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]:
        assert p in chart["planets"]


def test_transits_returns_aspects():
    natal = e.natal_chart(1995, 6, 15, 14.5, 50.45, 30.52, sidereal=False)
    tr = e.transits(natal, 2026, 6, 17, 12.0, sidereal=False)
    assert isinstance(tr["aspects"], list)


def test_sign_of_and_signs():
    assert e.sign_of(104.68) == "Cancer"
    assert e.sign_of(61.27) == "Gemini"
    assert e.signs({"Sun": 104.68, "Jupiter": 61.27}) == {"Sun": "Cancer", "Jupiter": "Gemini"}

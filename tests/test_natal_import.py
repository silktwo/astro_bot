from astro_bot.natal_import import sign_deg_to_lon, load_seed


def test_sign_deg_to_lon():
    assert abs(sign_deg_to_lon("Cancer", 14, 41) - 104.683) < 0.01
    assert abs(sign_deg_to_lon("Aquarius", 20, 9) - 320.15) < 0.01


def test_load_seed_has_planets():
    seed = load_seed("data/anna_natal.json")
    for p in ["Sun", "Moon", "Mars", "Venus", "Saturn", "Pluto"]:
        assert p in seed["planets"]
    assert abs(seed["planets"]["Sun"] - 104.68) < 0.1

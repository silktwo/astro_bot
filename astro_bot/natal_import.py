import json

_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
          "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]


def sign_deg_to_lon(sign, deg, minute=0):
    idx = _SIGNS.index(sign)
    return idx * 30 + deg + minute / 60.0


def load_seed(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

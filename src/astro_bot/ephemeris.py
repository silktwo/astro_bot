import os
import swisseph as swe

_PLANETS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
    "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
}
_ASPECTS = {"conjunction": 0, "sextile": 60, "square": 90,
            "trine": 120, "opposition": 180}
_ORB = 6.0  # градуси

_SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
               "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

_inited = False


def _init():
    global _inited
    if not _inited:
        path = os.environ.get("SWISSEPH_PATH", "/app/ephe")
        if os.path.isdir(path):
            swe.set_ephe_path(path)
        _inited = True


def _jd(year, month, day, hour_ut):
    _init()
    return swe.julday(year, month, day, hour_ut)


def _flags(sidereal):
    f = swe.FLG_SWIEPH
    if sidereal:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        f |= swe.FLG_SIDEREAL
    return f


def planet_positions(year, month, day, hour_ut, sidereal=False):
    jd = _jd(year, month, day, hour_ut)
    flags = _flags(sidereal)
    out = {}
    for name, pid in _PLANETS.items():
        lon = swe.calc_ut(jd, pid, flags)[0][0]
        out[name] = lon % 360
    return out


def natal_chart(year, month, day, hour_local, lat, lon, sidereal=False, tz_offset=0.0):
    hour_ut = hour_local - tz_offset
    return {
        "meta": {"year": year, "month": month, "day": day,
                 "hour_local": hour_local, "lat": lat, "lon": lon,
                 "tz_offset": tz_offset, "sidereal": sidereal},
        "planets": planet_positions(year, month, day, hour_ut, sidereal),
    }


def sign_of(longitude):
    return _SIGN_NAMES[int(longitude % 360 // 30)]


def signs(positions):
    return {name: sign_of(lon) for name, lon in positions.items()}


def _angle(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def transits(natal, year, month, day, hour_ut, sidereal=False):
    today = planet_positions(year, month, day, hour_ut, sidereal)
    aspects = []
    for tname, tlon in today.items():
        for nname, nlon in natal["planets"].items():
            sep = _angle(tlon, nlon)
            for aname, adeg in _ASPECTS.items():
                if abs(sep - adeg) <= _ORB:
                    aspects.append({
                        "transit": tname, "natal": nname,
                        "aspect": aname, "orb": round(abs(sep - adeg), 2),
                    })
    return {"today": today, "aspects": aspects}

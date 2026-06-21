from astro_bot import ephemeris, prompts


def build_daily(natal_data, year, month, day, llm, name=None, hour_ut=12.0):
    # natal_data["planets"] — абсолютні тропічні довготи (сід-карта)
    natal = {"planets": natal_data["planets"]}
    # Транзитні аспекти СПІЛЬНІ для обох систем (айанамша скорочується),
    # тож рахуємо один раз у тропіці.
    aspects = ephemeris.transits(natal, year, month, day, hour_ut,
                                 sidereal=False)["aspects"]
    # Різниця систем — у знаках, де планети стоять СЬОГОДНІ.
    today_trop = ephemeris.planet_positions(year, month, day, hour_ut, sidereal=False)
    today_sid = ephemeris.planet_positions(year, month, day, hour_ut, sidereal=True)
    signs_trop = ephemeris.signs(today_trop)
    signs_sid = ephemeris.signs(today_sid)
    # Один прохід: одразу пишемо прогноз (контекст реальної карти, якщо є).
    natal_context = natal_data.get("card_text") or natal_data.get("highlights")
    prompt = prompts.daily_prompt(aspects, signs_trop, signs_sid, natal_context, name)
    return llm.write(prompt, system=prompts.WRITE_SYSTEM)

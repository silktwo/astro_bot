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
    # reasoning → writing
    analysis = llm.reason(prompts.reason_prompt(aspects, signs_trop, signs_sid),
                          system=prompts.REASON_SYSTEM)
    return llm.write(prompts.write_prompt(analysis, name),
                     system=prompts.WRITE_SYSTEM)

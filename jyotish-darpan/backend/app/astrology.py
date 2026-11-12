"""Vedic chart calculations using Swiss Ephemeris (sidereal Lahiri).

This first engine release calculates D1, D9, planetary positions, nakshatras,
whole-sign houses and Vimshottari mahadasha periods. It is not a substitute
for an astrologer's interpretive judgement.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from threading import RLock
from typing import Any

import swisseph as swe

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]
DASHA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
               "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
NAKSHATRA_SPAN = 360.0 / 27.0
PADA_SPAN = NAKSHATRA_SPAN / 4.0
_LOCK = RLock()  # Swiss Ephemeris sidereal mode is process-global.

PLANETS = [
    ("Sun", swe.SUN), ("Moon", swe.MOON), ("Mars", swe.MARS),
    ("Mercury", swe.MERCURY), ("Jupiter", swe.JUPITER),
    ("Venus", swe.VENUS), ("Saturn", swe.SATURN), ("Rahu", swe.TRUE_NODE),
]


def norm(deg: float) -> float:
    return deg % 360.0


def zodiac_position(longitude: float) -> dict[str, Any]:
    longitude = norm(longitude)
    sign_index = int(longitude // 30)
    within_sign = longitude - sign_index * 30
    nak_index = int(longitude // NAKSHATRA_SPAN)
    nak_progress = longitude - nak_index * NAKSHATRA_SPAN
    pada = min(4, int(nak_progress // PADA_SPAN) + 1)
    return {
        "longitude": round(longitude, 6),
        "sign": SIGNS[sign_index],
        "sign_index": sign_index,
        "degree_in_sign": round(within_sign, 6),
        "nakshatra": NAKSHATRAS[nak_index],
        "nakshatra_index": nak_index,
        "pada": pada,
    }


def navamsa_sign(longitude: float) -> tuple[str, float]:
    """Return D9 sign and degree within it using the classical movable/fixed/dual rule."""
    longitude = norm(longitude)
    sign_index = int(longitude // 30)
    part = (longitude % 30.0) / (30.0 / 9.0)
    nav_index = min(8, int(part))
    if sign_index % 3 == 0:       # movable: starts from same sign
        start = sign_index
    elif sign_index % 3 == 1:     # fixed: starts from ninth sign
        start = (sign_index + 8) % 12
    else:                         # dual: starts from fifth sign
        start = (sign_index + 4) % 12
    return SIGNS[(start + nav_index) % 12], (part - nav_index) * (30.0 / 9.0)


def _calc_body(jd_ut: float, body_id: int) -> tuple[float, float]:
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
    try:
        result, _retflags = swe.calc_ut(jd_ut, body_id, flags)
    except Exception:
        # Moshier fallback is bundled with Swiss Ephemeris; precise Swiss files
        # can be configured through SWISSEPH_PATH for production.
        result, _retflags = swe.calc_ut(jd_ut, body_id, swe.FLG_MOSEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL)
    return norm(result[0]), float(result[3])


def _dasha(moon_longitude: float, birth_utc: datetime) -> dict[str, Any]:
    nak_index = int(norm(moon_longitude) // NAKSHATRA_SPAN)
    fraction_elapsed = (norm(moon_longitude) - nak_index * NAKSHATRA_SPAN) / NAKSHATRA_SPAN
    first_lord_index = nak_index % 9
    first_lord = DASHA_LORDS[first_lord_index]
    first_years = DASHA_YEARS[first_lord]
    remaining_years = first_years * (1.0 - fraction_elapsed)
    start = birth_utc
    periods = []
    cursor = start
    for i in range(9):
        lord = DASHA_LORDS[(first_lord_index + i) % 9]
        years = remaining_years if i == 0 else DASHA_YEARS[lord]
        end = cursor + timedelta(days=years * 365.2425)
        periods.append({"lord": lord, "start_utc": cursor.isoformat(), "end_utc": end.isoformat(),
                        "duration_years": round(years, 4), "is_birth_balance": i == 0})
        cursor = end
    return {"system": "Vimshottari", "birth_nakshatra": NAKSHATRAS[nak_index],
            "first_mahadasha_lord": first_lord, "balance_at_birth_years": round(remaining_years, 4),
            "mahadashas": periods,
            "note": "Dates use a 365.2425-day year; traditional software may differ slightly by year-length convention."}


def calculate_chart(payload: dict[str, Any]) -> dict[str, Any]:
    local_dt = datetime.combine(payload["birth_date"], payload["birth_time"])
    local_dt = local_dt.replace(tzinfo=ZoneInfo(payload["timezone"]))
    utc_dt = local_dt.astimezone(timezone.utc)
    hour = utc_dt.hour + utc_dt.minute / 60 + utc_dt.second / 3600 + utc_dt.microsecond / 3_600_000_000
    jd_ut = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour, swe.GREG_CAL)

    with _LOCK:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SIDEREAL
        _cusps, ascmc = swe.houses_ex(jd_ut, payload["latitude"], payload["longitude"], b"W", flags)
        asc_lon = norm(ascmc[0])
        planets = []
        longitudes: dict[str, float] = {}
        speeds: dict[str, float] = {}
        for name, body_id in PLANETS:
            lon, speed = _calc_body(jd_ut, body_id)
            longitudes[name] = lon
            speeds[name] = speed
            pos = zodiac_position(lon)
            house = ((pos["sign_index"] - int(asc_lon // 30)) % 12) + 1
            d9_sign, d9_degree = navamsa_sign(lon)
            planets.append({"planet": name, **pos, "house": house,
                            "retrograde": speed < 0,
                            "speed_deg_per_day": round(speed, 6),
                            "d9": {"sign": d9_sign, "degree_in_sign": round(d9_degree, 6)}})
        rahu_lon = longitudes["Rahu"]
        rahu_speed = speeds["Rahu"]
        ketu_lon = norm(rahu_lon + 180.0)
        ketu_pos = zodiac_position(ketu_lon)
        ketu_d9_sign, ketu_d9_degree = navamsa_sign(ketu_lon)
        planets.append({"planet": "Ketu", **ketu_pos,
                        "house": ((ketu_pos["sign_index"] - int(asc_lon // 30)) % 12) + 1,
                        "retrograde": rahu_speed < 0, "speed_deg_per_day": round(rahu_speed, 6),
                        "d9": {"sign": ketu_d9_sign, "degree_in_sign": round(ketu_d9_degree, 6)}})

    asc = zodiac_position(asc_lon)
    d1_houses = []
    for house_num in range(1, 13):
        sign_idx = (asc["sign_index"] + house_num - 1) % 12
        occupants = [p["planet"] for p in planets if p["house"] == house_num]
        d1_houses.append({"house": house_num, "sign": SIGNS[sign_idx], "planets": occupants})
    d9_asc_sign, d9_asc_degree = navamsa_sign(asc_lon)
    d9_houses = []
    d9_asc_index = SIGNS.index(d9_asc_sign)
    for house_num in range(1, 13):
        sign_idx = (d9_asc_index + house_num - 1) % 12
        occupants = [p["planet"] for p in planets if p["d9"]["sign"] == SIGNS[sign_idx]]
        d9_houses.append({"house": house_num, "sign": SIGNS[sign_idx], "planets": occupants})

    return {
        "engine": {"name": "Swiss Ephemeris", "ayanamsa": "Lahiri", "zodiac": "sidereal",
                   "house_system": "Whole Sign", "calculation_time_utc": utc_dt.isoformat()},
        "native": {"name": payload.get("name", ""), "birth_local": local_dt.isoformat(),
                   "birth_utc": utc_dt.isoformat(), "timezone": payload["timezone"],
                   "latitude": payload["latitude"], "longitude": payload["longitude"]},
        "ascendant": {**asc, "d9": {"sign": d9_asc_sign, "degree_in_sign": round(d9_asc_degree, 6)}},
        "planets": planets,
        "charts": {"D1": d1_houses, "D9": d9_houses},
        "vimshottari": _dasha(longitudes["Moon"], utc_dt),
        "calculation_notes": [
            "Planetary longitudes are sidereal using Lahiri ayanamsa.",
            "Whole-sign houses are assigned from the sidereal ascendant sign.",
            "Rahu is the true lunar node; Ketu is exactly opposite Rahu.",
            "Birthplace coordinates and the IANA timezone must be correct for a reliable chart.",
            "Astrological interpretations are traditional beliefs, not scientifically established predictions."
        ]
    }

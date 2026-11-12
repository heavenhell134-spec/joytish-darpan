from app.astrology import zodiac_position, navamsa_sign, calculate_chart


def test_zodiac_position_wraps_longitude():
    p = zodiac_position(360.0)
    assert p["sign"] == "Aries"
    assert p["degree_in_sign"] == 0
    assert p["nakshatra"] == "Ashwini"
    assert p["pada"] == 1


def test_navamsa_movable_sign_starts_same_sign():
    assert navamsa_sign(0.1)[0] == "Aries"


def test_chart_returns_d1_d9_and_nine_mahadashas():
    chart = calculate_chart({
        "name": "Test", "birth_date": __import__("datetime").date(2000, 1, 1),
        "birth_time": __import__("datetime").time(12, 0), "timezone": "Asia/Kolkata",
        "latitude": 28.6139, "longitude": 77.2090, "ayanamsa": "lahiri", "house_system": "whole_sign"
    })
    assert len(chart["planets"]) == 9
    assert len(chart["charts"]["D1"]) == 12
    assert len(chart["charts"]["D9"]) == 12
    assert len(chart["vimshottari"]["mahadashas"]) == 9

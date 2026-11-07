from datetime import date

from app.due import km_per_day, status

T = date(2026, 11, 7)


def test_never_done():
    assert status(3000, 90, None, 10000, T)["state"] == "due"


def test_km_overdue():
    s = status(3000, None, (date(2026, 10, 1), 10000), 13100, T)
    assert s["state"] == "overdue" and s["km_left"] == -100


def test_date_overdue():
    assert status(None, 30, (date(2026, 9, 1), 10000), 10100, T)["state"] == "overdue"


def test_soon_by_km():
    # 10% of 3000 = 300 km threshold
    assert status(3000, None, (T, 10000), 12750, T)["state"] == "soon"


def test_soon_km_floor():
    # 10% of 500 = 50, floor is 200
    assert status(500, None, (T, 10000), 10350, T)["state"] == "soon"


def test_soon_by_days():
    assert status(None, 30, (date(2026, 10, 20), 0), 0, T)["state"] == "soon"


def test_ok_single_interval():
    s = status(3000, None, (T, 10000), 10500, T)
    assert s["state"] == "ok" and s["days_left"] is None and s["next_date"] is None


def test_prediction_uses_earlier_of_km_and_date():
    # 2000 km left at 100 km/day -> 20 days; date interval 90 days -> km wins
    s = status(3000, 90, (T, 10000), 11000, T, avg_km_day=100)
    assert s["predicted"] == date(2026, 11, 27)


def test_km_per_day():
    assert km_per_day([(date(2026, 1, 1), 1000)]) is None
    assert km_per_day([(date(2026, 1, 11), 2000), (date(2026, 1, 1), 1000)]) == 100

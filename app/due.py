"""Due-status math. Pure functions, no DB."""
from datetime import date, timedelta

SOON_DAYS = 14
SOON_KM_MIN = 200


def km_per_day(readings: list[tuple[date, int]]) -> float | None:
    """Average km/day from first to latest odometer reading. None if not enough data."""
    if len(readings) < 2:
        return None
    readings = sorted(readings)
    (d0, k0), (d1, k1) = readings[0], readings[-1]
    days = (d1 - d0).days
    if days <= 0 or k1 <= k0:
        return None
    return (k1 - k0) / days


def status(
    every_km: int | None,
    every_days: int | None,
    last: tuple[date, int] | None,
    current_km: int,
    today: date,
    avg_km_day: float | None = None,
) -> dict:
    """Return {state, km_left, days_left, next_km, next_date, predicted}.

    state: 'due' (never done), 'overdue', 'soon', 'ok'.
    """
    if last is None:
        return {"state": "due", "km_left": None, "days_left": None,
                "next_km": None, "next_date": None, "predicted": None}

    last_date, last_km = last
    next_km = last_km + every_km if every_km else None
    next_date = last_date + timedelta(days=every_days) if every_days else None
    km_left = next_km - current_km if next_km is not None else None
    days_left = (next_date - today).days if next_date is not None else None

    if (km_left is not None and km_left <= 0) or (days_left is not None and days_left <= 0):
        state = "overdue"
    elif (km_left is not None and km_left <= max(every_km * 0.1, SOON_KM_MIN)) or (
        days_left is not None and days_left <= SOON_DAYS
    ):
        state = "soon"
    else:
        state = "ok"

    candidates = [d for d in (next_date,) if d]
    if km_left is not None and avg_km_day:
        candidates.append(today + timedelta(days=max(0, int(km_left / avg_km_day))))
    predicted = min(candidates) if candidates else None

    return {"state": state, "km_left": km_left, "days_left": days_left,
            "next_km": next_km, "next_date": next_date, "predicted": predicted}


RANK = {"overdue": 0, "due": 1, "soon": 2, "ok": 3}

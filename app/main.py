import datetime as dt
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Literal

from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from . import auth
from .db import Bike, Log, Odometer, Task, User, get_db
from .due import RANK, km_per_day, status

app = FastAPI(title="Moto Service", docs_url="/api/docs", openapi_url="/api/openapi.json")

BikeType = Literal["scooter", "underbone", "sport", "trail"]

# (part, name, every_km, every_days, types) — starting points, users edit them.
DEFAULT_TASKS = [
    ("engine_oil", "Engine oil", 3000, 90, "scooter underbone sport trail"),
    ("oil_filter", "Oil filter", 6000, None, "underbone sport trail"),
    ("gear_oil", "Gear oil", 8000, None, "scooter"),
    ("cvt_belt", "CVT belt & rollers", 24000, None, "scooter"),
    ("chain", "Chain clean & lube", 500, None, "underbone sport trail"),
    ("air_filter", "Air filter", 12000, None, "scooter underbone sport trail"),
    ("spark_plug", "Spark plug", 8000, None, "scooter underbone sport trail"),
    ("brake_front", "Front brake pads", 10000, None, "scooter underbone sport trail"),
    ("brake_rear", "Rear brake", 10000, None, "scooter underbone sport trail"),
    ("brake_fluid", "Brake fluid", None, 730, "scooter underbone sport trail"),
    ("coolant", "Coolant", None, 730, "scooter sport"),
    ("tire_front", "Front tire", 20000, None, "scooter underbone sport trail"),
    ("tire_rear", "Rear tire", 15000, None, "scooter underbone sport trail"),
    ("battery", "Battery check", None, 180, "scooter underbone sport trail"),
    ("general", "Monthly check", None, 30, "scooter underbone sport trail"),
]


# ---------- schemas ----------
class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class BikeIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    plate: str = Field(default="", max_length=20)
    type: BikeType
    km: int = Field(ge=0, le=2_000_000)


class BikePatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    plate: str | None = Field(default=None, max_length=20)
    type: BikeType | None = None


class OdoIn(BaseModel):
    km: int = Field(ge=0, le=2_000_000)
    date: dt.date | None = None


class TaskIn(BaseModel):
    part: str = Field(min_length=1, max_length=24)
    name: str = Field(min_length=1, max_length=80)
    every_km: int | None = Field(default=None, gt=0, le=1_000_000)
    every_days: int | None = Field(default=None, gt=0, le=3650)


class TaskPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    every_km: int | None = Field(default=None, gt=0, le=1_000_000)
    every_days: int | None = Field(default=None, gt=0, le=3650)


class LogIn(BaseModel):
    task_ids: list[int] = Field(min_length=1, max_length=50)
    date: dt.date
    km: int = Field(ge=0, le=2_000_000)
    cost: Decimal | None = Field(default=None, ge=0, le=10**9)
    note: str = Field(default="", max_length=500)


# ---------- helpers ----------
def get_owned_bike(bike_id: int, user: User, db) -> Bike:
    """The one place ownership is enforced. Other users' bikes look like they don't exist."""
    bike = db.get(Bike, bike_id)
    if bike is None or bike.user_id != user.id:
        raise HTTPException(404, "Bike not found")
    return bike


def get_owned_task(bike: Bike, task_id: int, db) -> Task:
    task = db.get(Task, task_id)
    if task is None or task.bike_id != bike.id:
        raise HTTPException(404, "Task not found")
    return task


def bike_view(bike: Bike, full: bool = False) -> dict:
    today = date.today()
    readings = [(o.date, o.km) for o in bike.odometer]
    current_km = max((k for _, k in readings), default=0)
    avg = km_per_day(readings)
    logs = sorted(bike.logs, key=lambda l: (l.date, l.id or 0), reverse=True)
    last_by_task: dict[int, Log] = {}
    for log in logs:
        last_by_task.setdefault(log.task_id, log)

    tasks = []
    for t in bike.tasks:
        last = last_by_task.get(t.id)
        s = status(t.every_km, t.every_days, (last.date, last.km) if last else None, current_km, today, avg)
        tasks.append({
            "id": t.id, "part": t.part, "name": t.name, "every_km": t.every_km, "every_days": t.every_days,
            "last_date": last.date if last else None, "last_km": last.km if last else None, **s,
        })
    tasks.sort(key=lambda t: (RANK[t["state"]], t["km_left"] if t["km_left"] is not None else 10**9))

    out = {
        "id": bike.id, "name": bike.name, "plate": bike.plate, "type": bike.type,
        "current_km": current_km, "avg_km_day": round(avg, 1) if avg else None,
        "worst": tasks[0]["state"] if tasks else "ok", "tasks": tasks,
    }
    if full:
        names = {t.id: t.name for t in bike.tasks}
        out["odometer"] = [{"id": o.id, "date": o.date, "km": o.km}
                           for o in sorted(bike.odometer, key=lambda o: (o.date, o.km), reverse=True)]
        out["logs"] = [{"id": l.id, "task_id": l.task_id, "task": names.get(l.task_id, "?"), "date": l.date,
                        "km": l.km, "cost": l.cost, "note": l.note} for l in logs]
    return out


# ---------- auth ----------
@app.post("/api/register", status_code=201)
def register(body: Credentials, response: Response, db=Depends(get_db)):
    user = User(email=body.email.lower(), password_hash=auth.hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "That email already has an account. Log in instead.")
    auth.start_session(db, user, response)
    return {"id": user.id, "email": user.email}


@app.post("/api/login")
def login(body: Credentials, request: Request, response: Response, db=Depends(get_db)):
    email = body.email.lower()
    keys = (f"ip:{request.client.host if request.client else '?'}", f"email:{email}")
    auth.check_rate(*keys)
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not auth.verify_password(user.password_hash if user else None, body.password):
        auth.record_fail(*keys)
        raise HTTPException(401, "Email or password is wrong.")
    auth.clear_fails(keys[1])
    auth.start_session(db, user, response)
    return {"id": user.id, "email": user.email}


@app.post("/api/logout", status_code=204)
def logout(response: Response, moto_session: str | None = Cookie(default=None), db=Depends(get_db)):
    auth.end_session(db, moto_session, response)


@app.get("/api/me")
def me(user: User = Depends(auth.current_user)):
    return {"id": user.id, "email": user.email}


# ---------- bikes ----------
@app.get("/api/bikes")
def list_bikes(user: User = Depends(auth.current_user), db=Depends(get_db)):
    # ponytail: loads each bike's history to compute status; fine for a handful of bikes per user.
    bikes = db.execute(select(Bike).where(Bike.user_id == user.id).order_by(Bike.id)).scalars()
    return [bike_view(b) for b in bikes]


@app.post("/api/bikes", status_code=201)
def create_bike(body: BikeIn, user: User = Depends(auth.current_user), db=Depends(get_db)):
    bike = Bike(user_id=user.id, name=body.name.strip(), plate=body.plate.strip(), type=body.type)
    bike.odometer.append(Odometer(date=date.today(), km=body.km))
    for part, name, km, days, types in DEFAULT_TASKS:
        if body.type in types.split():
            bike.tasks.append(Task(part=part, name=name, every_km=km, every_days=days))
    db.add(bike)
    db.commit()
    return bike_view(bike, full=True)


@app.get("/api/bikes/{bike_id}")
def get_bike(bike_id: int, user: User = Depends(auth.current_user), db=Depends(get_db)):
    return bike_view(get_owned_bike(bike_id, user, db), full=True)


@app.patch("/api/bikes/{bike_id}")
def patch_bike(bike_id: int, body: BikePatch, user: User = Depends(auth.current_user), db=Depends(get_db)):
    bike = get_owned_bike(bike_id, user, db)
    for k, v in body.model_dump(exclude_unset=True).items():
        if v is not None:
            setattr(bike, k, v.strip() if isinstance(v, str) else v)
    db.commit()
    return bike_view(bike, full=True)


@app.delete("/api/bikes/{bike_id}", status_code=204)
def delete_bike(bike_id: int, user: User = Depends(auth.current_user), db=Depends(get_db)):
    db.delete(get_owned_bike(bike_id, user, db))
    db.commit()


@app.post("/api/bikes/{bike_id}/odometer", status_code=201)
def add_odometer(bike_id: int, body: OdoIn, user: User = Depends(auth.current_user), db=Depends(get_db)):
    bike = get_owned_bike(bike_id, user, db)
    bike.odometer.append(Odometer(date=body.date or date.today(), km=body.km))
    db.commit()
    return bike_view(bike, full=True)


# ---------- tasks ----------
@app.post("/api/bikes/{bike_id}/tasks", status_code=201)
def add_task(bike_id: int, body: TaskIn, user: User = Depends(auth.current_user), db=Depends(get_db)):
    bike = get_owned_bike(bike_id, user, db)
    if not body.every_km and not body.every_days:
        raise HTTPException(422, "Set a km interval, a day interval, or both.")
    bike.tasks.append(Task(**body.model_dump()))
    db.commit()
    return bike_view(bike, full=True)


@app.patch("/api/bikes/{bike_id}/tasks/{task_id}")
def patch_task(bike_id: int, task_id: int, body: TaskPatch,
               user: User = Depends(auth.current_user), db=Depends(get_db)):
    bike = get_owned_bike(bike_id, user, db)
    task = get_owned_task(bike, task_id, db)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(task, k, v)  # null clears an interval
    if not task.every_km and not task.every_days:
        db.rollback()
        raise HTTPException(422, "Keep at least one interval (km or days).")
    db.commit()
    return bike_view(bike, full=True)


@app.delete("/api/bikes/{bike_id}/tasks/{task_id}", status_code=204)
def delete_task(bike_id: int, task_id: int, user: User = Depends(auth.current_user), db=Depends(get_db)):
    bike = get_owned_bike(bike_id, user, db)
    db.delete(get_owned_task(bike, task_id, db))
    db.commit()


# ---------- logs ----------
@app.post("/api/bikes/{bike_id}/logs", status_code=201)
def add_logs(bike_id: int, body: LogIn, user: User = Depends(auth.current_user), db=Depends(get_db)):
    bike = get_owned_bike(bike_id, user, db)
    new = []
    for i, tid in enumerate(dict.fromkeys(body.task_ids)):
        get_owned_task(bike, tid, db)
        # Visit cost is stored once (on the first task) so totals don't double count.
        new.append(Log(task_id=tid, date=body.date, km=body.km,
                       cost=body.cost if i == 0 else None, note=body.note.strip()))
    bike.logs.extend(new)
    bike.odometer.append(Odometer(date=body.date, km=body.km))
    db.commit()
    return {**bike_view(bike, full=True), "created_log_ids": [l.id for l in new]}


@app.delete("/api/bikes/{bike_id}/logs/{log_id}", status_code=204)
def delete_log(bike_id: int, log_id: int, user: User = Depends(auth.current_user), db=Depends(get_db)):
    bike = get_owned_bike(bike_id, user, db)
    log = db.get(Log, log_id)
    if log is None or log.bike_id != bike.id:
        raise HTTPException(404, "Log not found")
    db.delete(log)
    db.commit()


@app.get("/api/export")
def export(user: User = Depends(auth.current_user), db=Depends(get_db)):
    bikes = db.execute(select(Bike).where(Bike.user_id == user.id)).scalars()
    return {"email": user.email, "exported": date.today(), "bikes": [bike_view(b, full=True) for b in bikes]}


# ---------- frontend ----------
DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if DIST.is_dir():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="frontend")

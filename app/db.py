import os
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg://moto:moto@127.0.0.1:5432/moto")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    type_annotation_map = {datetime: DateTime(timezone=True)}


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=now)


class Session(Base):
    __tablename__ = "sessions"
    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime]


class Bike(Base):
    __tablename__ = "bikes"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    plate: Mapped[str] = mapped_column(String(20), default="")
    type: Mapped[str] = mapped_column(String(12))  # scooter|underbone|sport|trail
    created_at: Mapped[datetime] = mapped_column(default=now)

    odometer: Mapped[list["Odometer"]] = relationship(cascade="all, delete-orphan", order_by="Odometer.date")
    tasks: Mapped[list["Task"]] = relationship(cascade="all, delete-orphan", order_by="Task.id")
    logs: Mapped[list["Log"]] = relationship(cascade="all, delete-orphan", order_by="Log.date.desc()")


class Odometer(Base):
    __tablename__ = "odometer"
    id: Mapped[int] = mapped_column(primary_key=True)
    bike_id: Mapped[int] = mapped_column(ForeignKey("bikes.id", ondelete="CASCADE"), index=True)
    date: Mapped[date]
    km: Mapped[int]


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    bike_id: Mapped[int] = mapped_column(ForeignKey("bikes.id", ondelete="CASCADE"), index=True)
    part: Mapped[str] = mapped_column(String(24))
    name: Mapped[str] = mapped_column(String(80))
    every_km: Mapped[int | None]
    every_days: Mapped[int | None]


class Log(Base):
    __tablename__ = "logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    bike_id: Mapped[int] = mapped_column(ForeignKey("bikes.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    date: Mapped[date]
    km: Mapped[int]
    cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    note: Mapped[str] = mapped_column(String(500), default="")


def get_db():
    with SessionLocal() as db:
        yield db

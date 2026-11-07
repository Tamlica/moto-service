import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://moto:moto@127.0.0.1:5432/moto_test")
os.environ["SECURE_COOKIE"] = "0"  # TestClient talks plain http

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from app import auth
from app.db import engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def schema():
    with engine.begin() as c:
        c.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public"))
    command.upgrade(Config("alembic.ini"), "head")  # exercises the real migration


@pytest.fixture(autouse=True)
def clean():
    with engine.begin() as c:
        c.execute(text("TRUNCATE users RESTART IDENTITY CASCADE"))
    auth._fails.clear()


def make_client(email="a@example.com", pw="correct-horse"):
    c = TestClient(app)
    r = c.post("/api/register", json={"email": email, "password": pw})
    assert r.status_code == 201, r.text
    return c


@pytest.fixture
def client():
    return make_client()

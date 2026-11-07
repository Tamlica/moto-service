import os
import secrets
import time
from collections import defaultdict
from datetime import timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Cookie, Depends, HTTPException, Response
from sqlalchemy import delete, select

from .db import Session, User, get_db, now

COOKIE = "moto_session"
SESSION_DAYS = 30
SECURE_COOKIE = os.environ.get("SECURE_COOKIE", "1") == "1"

ph = PasswordHasher()
# Hash of a random string, verified against when the email doesn't exist so timing doesn't leak it.
_DUMMY_HASH = ph.hash(secrets.token_hex(16))


def hash_password(pw: str) -> str:
    return ph.hash(pw)


def verify_password(hash_: str | None, pw: str) -> bool:
    try:
        return ph.verify(hash_ or _DUMMY_HASH, pw) and hash_ is not None
    except (VerifyMismatchError, InvalidHashError):
        return False


# ponytail: in-memory limiter, single uvicorn process only. Move to Postgres/Redis if you run >1 worker.
MAX_FAILS = 5
WINDOW = 15 * 60
_fails: dict[str, list[float]] = defaultdict(list)


def check_rate(*keys: str) -> None:
    cutoff = time.monotonic() - WINDOW
    for k in keys:
        _fails[k] = [t for t in _fails[k] if t > cutoff]
        if len(_fails[k]) >= MAX_FAILS:
            raise HTTPException(429, "Too many failed attempts. Try again in 15 minutes.")


def record_fail(*keys: str) -> None:
    for k in keys:
        _fails[k].append(time.monotonic())


def clear_fails(*keys: str) -> None:
    for k in keys:
        _fails.pop(k, None)


def start_session(db, user: User, response: Response) -> None:
    token = secrets.token_urlsafe(32)
    db.add(Session(token=token, user_id=user.id, expires_at=now() + timedelta(days=SESSION_DAYS)))
    db.execute(delete(Session).where(Session.expires_at < now()))
    db.commit()
    response.set_cookie(COOKIE, token, max_age=SESSION_DAYS * 86400, httponly=True,
                        secure=SECURE_COOKIE, samesite="lax", path="/")


def end_session(db, token: str | None, response: Response) -> None:
    if token:
        db.execute(delete(Session).where(Session.token == token))
        db.commit()
    response.delete_cookie(COOKIE, path="/")


def current_user(moto_session: str | None = Cookie(default=None), db=Depends(get_db)) -> User:
    if not moto_session:
        raise HTTPException(401, "Not logged in")
    row = db.execute(
        select(User).join(Session, Session.user_id == User.id)
        .where(Session.token == moto_session, Session.expires_at > now())
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(401, "Session expired. Log in again.")
    return row

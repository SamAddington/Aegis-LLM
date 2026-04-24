"""Authentication service.

A deliberately small auth layer for a teaching lab:

* SQLite from the standard library (no SQLAlchemy dep).
* bcrypt for password hashing (OWASP-recommended).
* PyJWT (HS256) for stateless access tokens.
* Two roles: ``admin`` (can manage users and settings) and ``student``.

Design notes for students reading this code
-------------------------------------------
* We intentionally demonstrate BCRYPT over SHA/MD5 so students see the
  correct primitive. The cost factor defaults to 12.
* Password comparisons go through ``bcrypt.checkpw`` which is constant-time.
* The JWT secret lives in ``AEGIS_JWT_SECRET``. If the student leaves it at
  the default ``change-me-in-production`` the API logs a warning.
"""
from __future__ import annotations

import logging
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config import settings

logger = logging.getLogger("aegis.auth")

Role = Literal["admin", "student"]

_DB_LOCK = threading.Lock()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Create tables and seed default users on first run."""
    with _DB_LOCK, _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT NOT NULL UNIQUE,
                email         TEXT,
                password_hash TEXT NOT NULL,
                role          TEXT NOT NULL CHECK (role IN ('admin','student')),
                created_at    TEXT NOT NULL DEFAULT (datetime('now')),
                last_login    TEXT
            );
            """
        )
        conn.commit()

        cursor = conn.execute("SELECT COUNT(*) AS n FROM users;")
        if cursor.fetchone()["n"] == 0:
            logger.warning(
                "Seeding default accounts (%s/%s and %s/%s). "
                "CHANGE THESE IMMEDIATELY via the Users panel.",
                settings.bootstrap_admin_username,
                settings.bootstrap_admin_password,
                settings.bootstrap_student_username,
                settings.bootstrap_student_password,
            )
            _create_user(
                conn,
                settings.bootstrap_admin_username,
                settings.bootstrap_admin_password,
                role="admin",
                email=None,
            )
            _create_user(
                conn,
                settings.bootstrap_student_username,
                settings.bootstrap_student_password,
                role="student",
                email=None,
            )
            conn.commit()

    if settings.jwt_secret == "change-me-in-production":
        logger.warning(
            "AEGIS_JWT_SECRET is at the default. Set a real secret via env var."
        )


# ---------------------------------------------------------------------------
# Password primitives
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    if not password or len(password) < 3:
        raise ValueError("Password must be at least 3 characters.")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# JWT primitives
# ---------------------------------------------------------------------------

def create_access_token(*, sub: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expires_minutes)).timestamp()),
        "iss": "aegis-llm",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@dataclass
class User:
    id: int
    username: str
    email: str | None
    role: Role
    created_at: str
    last_login: str | None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "User":
        return cls(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            role=row["role"],
            created_at=row["created_at"],
            last_login=row["last_login"],
        )


def _create_user(
    conn: sqlite3.Connection,
    username: str,
    password: str,
    *,
    role: Role = "student",
    email: str | None = None,
) -> User:
    conn.execute(
        "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?);",
        (username, email, hash_password(password), role),
    )
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?;", (username,)
    ).fetchone()
    return User.from_row(row)


def create_user(
    username: str, password: str, *, role: Role = "student", email: str | None = None
) -> User:
    username = username.strip()
    if not username:
        raise HTTPException(400, "Username is required")
    with _DB_LOCK, _connect() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?;", (username,)
        ).fetchone()
        if existing:
            raise HTTPException(409, "Username already taken")
        try:
            user = _create_user(conn, username, password, role=role, email=email)
            conn.commit()
            return user
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc


def authenticate(username: str, password: str) -> User:
    with _DB_LOCK, _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?;", (username,)
        ).fetchone()
        if row is None or not verify_password(password, row["password_hash"]):
            # Deliberately vague error to avoid username enumeration.
            raise HTTPException(status_code=401, detail="Invalid credentials")
        conn.execute(
            "UPDATE users SET last_login = datetime('now') WHERE id = ?;",
            (row["id"],),
        )
        conn.commit()
        return User.from_row(row)


def list_users() -> list[User]:
    with _DB_LOCK, _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM users ORDER BY created_at DESC;"
        ).fetchall()
        return [User.from_row(r) for r in rows]


def delete_user(user_id: int) -> None:
    with _DB_LOCK, _connect() as conn:
        # Don't let admins delete themselves into lockout.
        admins = conn.execute(
            "SELECT COUNT(*) AS n FROM users WHERE role = 'admin';"
        ).fetchone()["n"]
        target = conn.execute(
            "SELECT role FROM users WHERE id = ?;", (user_id,)
        ).fetchone()
        if target is None:
            raise HTTPException(404, "User not found")
        if target["role"] == "admin" and admins <= 1:
            raise HTTPException(
                409,
                "Cannot delete the last admin account. Promote another user first.",
            )
        conn.execute("DELETE FROM users WHERE id = ?;", (user_id,))
        conn.commit()


def update_user_role(user_id: int, role: Role) -> User:
    if role not in ("admin", "student"):
        raise HTTPException(400, f"Unknown role: {role}")
    with _DB_LOCK, _connect() as conn:
        conn.execute("UPDATE users SET role = ? WHERE id = ?;", (role, user_id))
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "User not found")
        return User.from_row(row)


def change_password(user_id: int, new_password: str) -> None:
    with _DB_LOCK, _connect() as conn:
        hashed = hash_password(new_password)
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?;",
            (hashed, user_id),
        )
        conn.commit()


def get_user_by_username(username: str) -> User | None:
    with _DB_LOCK, _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?;", (username,)
        ).fetchone()
        return User.from_row(row) if row else None


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------

# tokenUrl is the public path to the login endpoint; used only by Swagger UI.
_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def current_user_optional(token: str | None = Depends(_oauth2)) -> User | None:
    if not token:
        return None
    payload = decode_access_token(token)
    user = get_user_by_username(payload["sub"])
    return user


async def current_user(user: User | None = Depends(current_user_optional)) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def admin_user(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user


# A tiny helper for rate-limiting login attempts by (client_ip, username).
# Kept in-memory on purpose: if students see how simple it is, they can
# build something real.
_LOGIN_ATTEMPTS: dict[tuple[str, str], list[float]] = {}
_LOGIN_WINDOW_S = 60
_LOGIN_MAX_IN_WINDOW = 10


def note_login_attempt(ip: str, username: str) -> None:
    key = (ip, username)
    now = time.time()
    bucket = _LOGIN_ATTEMPTS.setdefault(key, [])
    bucket[:] = [t for t in bucket if now - t < _LOGIN_WINDOW_S]
    bucket.append(now)
    if len(bucket) > _LOGIN_MAX_IN_WINDOW:
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Wait {_LOGIN_WINDOW_S}s.",
        )

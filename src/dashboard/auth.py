from __future__ import annotations

import sqlite3
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUTH_DB_PATH = PROJECT_ROOT / "data" / "clean" / "auth.db"


def ensure_auth_db(db_path: Path | None = None) -> Path:
    auth_db_path = Path(db_path or DEFAULT_AUTH_DB_PATH)
    auth_db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(auth_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users (role)"
        )

    return auth_db_path


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, stored_password_hash: str) -> bool:
    return check_password_hash(stored_password_hash, password)


def get_user_by_username(username: str, db_path: Path | None = None) -> dict | None:
    auth_db_path = Path(db_path or DEFAULT_AUTH_DB_PATH)
    with sqlite3.connect(auth_db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, password_hash, role, created_at
            FROM users
            WHERE username = ?
            """,
            (username,),
        )
        row = cursor.fetchone()

    return dict(row) if row else None


def create_user(
    username: str,
    password: str,
    role: str,
    db_path: Path | None = None,
    email: str | None = None,
) -> bool:
    auth_db_path = Path(db_path or DEFAULT_AUTH_DB_PATH)
    password_hash = hash_password(password)

    try:
        with sqlite3.connect(auth_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
                """,
                (username, email, password_hash, role),
            )
    except sqlite3.IntegrityError:
        return False

    return True

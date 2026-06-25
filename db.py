"""Хранилище заявок на SQLite."""
import os
import sqlite3
from datetime import datetime
from pathlib import Path

# Путь к базе можно переопределить через переменную окружения DB_PATH
# (например, указать на постоянный диск/том в облаке).
DB_PATH = Path(os.getenv("DB_PATH", Path(__file__).parent / "requests.db"))

# Возможные статусы заявки
STATUS_NEW = "new"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE = "done"

STATUS_LABELS = {
    STATUS_NEW: "🆕 Принято",
    STATUS_IN_PROGRESS: "🔧 В работе",
    STATUS_DONE: "✅ Готово",
}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS requests (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                username    TEXT,
                category    TEXT NOT NULL,
                name        TEXT NOT NULL,
                contact     TEXT NOT NULL,
                description TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'new',
                created_at  TEXT NOT NULL
            )
            """
        )


def create_request(
    user_id: int,
    username: str | None,
    category: str,
    name: str,
    contact: str,
    description: str,
) -> int:
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO requests
                (user_id, username, category, name, contact, description, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                category,
                name,
                contact,
                description,
                STATUS_NEW,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        return cur.lastrowid


def get_request(request_id: int) -> sqlite3.Row | None:
    with _connect() as conn:
        cur = conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
        return cur.fetchone()


def set_status(request_id: int, status: str) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE requests SET status = ? WHERE id = ?", (status, request_id)
        )
        return cur.rowcount > 0


def list_user_requests(user_id: int) -> list[sqlite3.Row]:
    with _connect() as conn:
        cur = conn.execute(
            "SELECT * FROM requests WHERE user_id = ? ORDER BY id DESC LIMIT 20",
            (user_id,),
        )
        return cur.fetchall()

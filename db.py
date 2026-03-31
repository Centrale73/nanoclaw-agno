import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager

DB_PATH = "nanoclaw.db"

def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id    TEXT NOT NULL,
                channel     TEXT NOT NULL,
                sender_id   TEXT NOT NULL,
                content     TEXT NOT NULL,
                status      TEXT DEFAULT 'pending',
                created_at  TEXT DEFAULT (datetime('now')),
                response    TEXT
            );
            CREATE TABLE IF NOT EXISTS groups (
                id          TEXT PRIMARY KEY,
                channel     TEXT NOT NULL,
                name        TEXT,
                context_path TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id          TEXT PRIMARY KEY,
                group_id    TEXT NOT NULL,
                cron        TEXT NOT NULL,
                prompt      TEXT NOT NULL,
                enabled     INTEGER DEFAULT 1,
                last_run    TEXT
            );
        """)

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def enqueue(group_id: str, channel: str, sender_id: str, content: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO messages (group_id, channel, sender_id, content) VALUES (?,?,?,?)",
            (group_id, channel, sender_id, content)
        )
        return cur.lastrowid

def next_pending(group_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM messages WHERE group_id=? AND status='pending' ORDER BY id LIMIT 1",
            (group_id,)
        ).fetchone()
        if row:
            conn.execute("UPDATE messages SET status='processing' WHERE id=?", (row["id"],))
            return dict(row)
    return None

def complete(msg_id: int, response: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE messages SET status='done', response=? WHERE id=?",
            (response, msg_id)
        )

def fail(msg_id: int, error: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE messages SET status='error', response=? WHERE id=?",
            (error, msg_id)
        )

def active_groups() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT group_id FROM messages WHERE status='pending'"
        ).fetchall()
        return [r["group_id"] for r in rows]

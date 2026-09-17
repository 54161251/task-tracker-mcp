"""SQLite access with bound parameters and short-lived connections."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class TaskStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                priority TEXT NOT NULL CHECK(priority IN ('low','medium','high')),
                due_date TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def add(self, title: str, priority: str, due_date: str | None) -> dict:
        # Bound-parameter pattern adapted from Python sqlite3 documentation:
        # https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders
        # User text is always a value, never executable SQL.
        with self.connection() as connection:
            cursor = connection.execute(
                "INSERT INTO tasks(title, priority, due_date) VALUES (?, ?, ?)",
                (title, priority, due_date),
            )
            row = connection.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
            return dict(row)

    def list(self, query: str, limit: int) -> list[dict]:
        with self.connection() as connection:
            # instr performs literal substring matching; SQL wildcards have no effect.
            rows = connection.execute(
                """SELECT * FROM tasks WHERE instr(lower(title), lower(?)) > 0
                ORDER BY CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
                due_date IS NULL, due_date, id LIMIT ?""", (query, limit)
            ).fetchall()
            return [dict(row) for row in rows]

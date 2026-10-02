"""SQLite connection and migration management."""

import sqlite3
from pathlib import Path
from typing import Iterator, Optional

from .migrations import MIGRATIONS


class Database:
    def __init__(self, path: str = "~/.ossi/ossi.db") -> None:
        expanded = Path(path).expanduser()
        self.path = expanded
        if str(expanded) != ":memory:":
            expanded.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(expanded), isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._migrate()

    def _migrate(self) -> None:
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL)"
        )
        current = self.connection.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations").fetchone()[0]
        for version, name, sql in MIGRATIONS:
            if version <= current:
                continue
            try:
                self.connection.executescript(sql)
                self.connection.execute(
                    "INSERT INTO schema_migrations(version, name, applied_at) VALUES (?, ?, datetime('now'))",
                    (version, name),
                )
            except Exception:
                raise

    @property
    def supports_fts(self) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'notes_fts'"
        ).fetchone()
        return row is not None

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

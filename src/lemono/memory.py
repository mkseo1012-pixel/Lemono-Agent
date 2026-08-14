from __future__ import annotations

import re
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from .models import MemoryRecord


class MemoryStore:
    """Tenant-isolated SQLite memory with FTS retrieval and explicit provenance."""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self.connection() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    kind TEXT NOT NULL CHECK(kind IN ('conversation','fact','preference','summary')),
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS memories_user_kind ON memories(user_id, kind);
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                    content, content='memories', content_rowid='id', tokenize='unicode61'
                );
                CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                    INSERT INTO memories_fts(rowid, content) VALUES (new.id, new.content);
                END;
                CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                    INSERT INTO memories_fts(memories_fts, rowid, content)
                    VALUES ('delete', old.id, old.content);
                END;
                """
            )

    def add(self, user_id: str, kind: str, content: str, source: str, confidence: float = 1.0) -> int:
        clean = content.strip()
        if not clean:
            raise ValueError("memory content must not be empty")
        with self.connection() as db:
            cursor = db.execute(
                "INSERT INTO memories(user_id, kind, content, source, confidence, created_at) VALUES(?,?,?,?,?,?)",
                (user_id, kind, clean, source, confidence, datetime.now(UTC).isoformat()),
            )
            return int(cursor.lastrowid)

    def search(self, user_id: str, query: str, limit: int = 6) -> list[MemoryRecord]:
        tokens = re.findall(r"[\w가-힣]{2,}", query.lower())[:12]
        if not tokens or limit <= 0:
            return self.recent(user_id, limit)
        fts_query = " OR ".join(f'"{token}"' for token in tokens)
        with self.connection() as db:
            rows = db.execute(
                """
                SELECT m.* FROM memories_fts f
                JOIN memories m ON m.id = f.rowid
                WHERE memories_fts MATCH ? AND m.user_id = ?
                ORDER BY bm25(memories_fts), m.confidence DESC, m.id DESC LIMIT ?
                """,
                (fts_query, user_id, limit),
            ).fetchall()
        return [self._record(row) for row in rows]

    def recent(self, user_id: str, limit: int = 6) -> list[MemoryRecord]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT * FROM memories WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id, limit)
            ).fetchall()
        return [self._record(row) for row in rows]

    def preferences(self, user_id: str, limit: int = 20) -> list[MemoryRecord]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT * FROM memories WHERE user_id=? AND kind='preference' ORDER BY confidence DESC, id DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        return [self._record(row) for row in rows]

    def delete_user(self, user_id: str) -> int:
        with self.connection() as db:
            cursor = db.execute("DELETE FROM memories WHERE user_id=?", (user_id,))
            return cursor.rowcount

    def ping(self) -> bool:
        with self.connection() as db:
            return db.execute("SELECT 1").fetchone()[0] == 1

    @staticmethod
    def _record(row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(**dict(row))


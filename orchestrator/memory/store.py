"""SQLite-backed persistent store for episodes and memory entries."""

from __future__ import annotations
import json
import os
import sqlite3
import threading

from .types import Episode, MemoryEntry


class MemoryStore:
    """Thread-safe SQLite store for HIVEMIND memory."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS episodes (
                episode_id   TEXT PRIMARY KEY,
                task         TEXT NOT NULL,
                task_domain  TEXT DEFAULT '',
                task_complexity TEXT DEFAULT '',
                plan         TEXT DEFAULT '{}',
                agent_outputs TEXT DEFAULT '{}',
                final_output TEXT DEFAULT '',
                coverage_report TEXT DEFAULT '{}',
                known_issues TEXT DEFAULT '[]',
                metadata     TEXT DEFAULT '{}',
                user_feedback TEXT,
                success_score REAL,
                timestamp    TEXT NOT NULL,
                tags         TEXT DEFAULT '[]'
            );

            CREATE TABLE IF NOT EXISTS memory_entries (
                entry_id          TEXT PRIMARY KEY,
                memory_type       TEXT NOT NULL,
                content           TEXT NOT NULL,
                context           TEXT DEFAULT '{}',
                source_episode_id TEXT,
                relevance_decay   REAL DEFAULT 1.0,
                created_at        TEXT NOT NULL,
                access_count      INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS preferences (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_episodes_domain ON episodes(task_domain);
            CREATE INDEX IF NOT EXISTS idx_episodes_ts ON episodes(timestamp);
            CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_entries(memory_type);
        """)
        conn.commit()

    # ── Episodes ───────────────────────────────────────────────────

    def save_episode(self, ep: Episode) -> str:
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO episodes
               (episode_id, task, task_domain, task_complexity, plan,
                agent_outputs, final_output, coverage_report, known_issues,
                metadata, user_feedback, success_score, timestamp, tags)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                ep.episode_id, ep.task, ep.task_domain, ep.task_complexity,
                json.dumps(ep.plan), json.dumps(ep.agent_outputs),
                ep.final_output, json.dumps(ep.coverage_report),
                json.dumps(ep.known_issues), json.dumps(ep.metadata),
                ep.user_feedback, ep.success_score, ep.timestamp,
                json.dumps(ep.tags),
            ),
        )
        conn.commit()
        return ep.episode_id

    def get_episode(self, episode_id: str) -> Episode | None:
        row = self._get_conn().execute(
            "SELECT * FROM episodes WHERE episode_id = ?", (episode_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_episode(row)

    def list_episodes(self, limit: int = 50, domain: str | None = None) -> list[Episode]:
        if domain:
            rows = self._get_conn().execute(
                "SELECT * FROM episodes WHERE task_domain = ? ORDER BY timestamp DESC LIMIT ?",
                (domain, limit),
            ).fetchall()
        else:
            rows = self._get_conn().execute(
                "SELECT * FROM episodes ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._row_to_episode(r) for r in rows]

    def update_episode_feedback(self, episode_id: str, feedback: str, score: float):
        conn = self._get_conn()
        conn.execute(
            "UPDATE episodes SET user_feedback = ?, success_score = ? WHERE episode_id = ?",
            (feedback, score, episode_id),
        )
        conn.commit()

    def _row_to_episode(self, row) -> Episode:
        return Episode(
            episode_id=row["episode_id"],
            task=row["task"],
            task_domain=row["task_domain"] or "",
            task_complexity=row["task_complexity"] or "",
            plan=json.loads(row["plan"] or "{}"),
            agent_outputs=json.loads(row["agent_outputs"] or "{}"),
            final_output=row["final_output"] or "",
            coverage_report=json.loads(row["coverage_report"] or "{}"),
            known_issues=json.loads(row["known_issues"] or "[]"),
            metadata=json.loads(row["metadata"] or "{}"),
            user_feedback=row["user_feedback"],
            success_score=row["success_score"],
            timestamp=row["timestamp"],
            tags=json.loads(row["tags"] or "[]"),
        )

    # ── Memory entries ─────────────────────────────────────────────

    def save_memory_entry(self, entry: MemoryEntry) -> str:
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO memory_entries
               (entry_id, memory_type, content, context,
                source_episode_id, relevance_decay, created_at, access_count)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                entry.entry_id, entry.memory_type, entry.content,
                json.dumps(entry.context), entry.source_episode_id,
                entry.relevance_decay, entry.created_at, entry.access_count,
            ),
        )
        conn.commit()
        return entry.entry_id

    def get_entries_by_type(self, memory_type: str, limit: int = 20) -> list[MemoryEntry]:
        rows = self._get_conn().execute(
            "SELECT * FROM memory_entries WHERE memory_type = ? ORDER BY created_at DESC LIMIT ?",
            (memory_type, limit),
        ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def get_all_entries(self, limit: int = 100) -> list[MemoryEntry]:
        rows = self._get_conn().execute(
            "SELECT * FROM memory_entries ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def increment_access(self, entry_id: str):
        conn = self._get_conn()
        conn.execute(
            "UPDATE memory_entries SET access_count = access_count + 1 WHERE entry_id = ?",
            (entry_id,),
        )
        conn.commit()

    def _row_to_entry(self, row) -> MemoryEntry:
        return MemoryEntry(
            entry_id=row["entry_id"],
            memory_type=row["memory_type"],
            content=row["content"],
            context=json.loads(row["context"] or "{}"),
            source_episode_id=row["source_episode_id"],
            relevance_decay=row["relevance_decay"],
            created_at=row["created_at"],
            access_count=row["access_count"],
        )

    # ── Preferences ────────────────────────────────────────────────

    def set_preference(self, key: str, value: str):
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)",
            (key, value),
        )
        conn.commit()

    def get_preference(self, key: str, default: str = "") -> str:
        row = self._get_conn().execute(
            "SELECT value FROM preferences WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

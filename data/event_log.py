"""Append-only system event log backed by SQLite."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


VALID_EVENT_TYPES = {
    "mutation_proposed",
    "eval_started",
    "eval_completed",
    "candidate_promoted",
    "candidate_rejected",
    "rollback_triggered",
    "canary_started",
    "canary_passed",
    "canary_failed",
    "budget_exceeded",
    "stall_detected",
    "human_pause",
    "human_reject",
    "human_inject",
}


class EventLog:
    """Append-only event log with query helpers."""

    def __init__(self, db_path: str = ".autoagent/event_log.db") -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL DEFAULT '{}',
                    cycle_id TEXT,
                    experiment_id TEXT
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_type ON system_events(event_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_ts ON system_events(timestamp DESC)"
            )
            conn.commit()

    def append(
        self,
        *,
        event_type: str,
        payload: dict[str, Any] | None = None,
        cycle_id: str | None = None,
        experiment_id: str | None = None,
    ) -> int:
        """Append a new event and return inserted row id."""
        if event_type not in VALID_EVENT_TYPES:
            raise ValueError(f"Invalid event_type: {event_type}")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO system_events
                    (timestamp, event_type, payload, cycle_id, experiment_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    time.time(),
                    event_type,
                    json.dumps(payload or {}, sort_keys=True, default=str),
                    cycle_id,
                    experiment_id,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def list_events(
        self,
        *,
        limit: int = 100,
        event_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """List recent events in reverse-chronological order."""
        with sqlite3.connect(self.db_path) as conn:
            if event_type:
                rows = conn.execute(
                    """
                    SELECT id, timestamp, event_type, payload, cycle_id, experiment_id
                    FROM system_events
                    WHERE event_type = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (event_type, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, timestamp, event_type, payload, cycle_id, experiment_id
                    FROM system_events
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()

        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "event_type": row[2],
                "payload": json.loads(row[3]) if row[3] else {},
                "cycle_id": row[4],
                "experiment_id": row[5],
            }
            for row in rows
        ]

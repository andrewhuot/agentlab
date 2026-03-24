"""Data-plane repository interfaces (SQLite now, Postgres-ready shapes)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class TraceRepository(Protocol):
    """Repository contract for trace events."""

    def put(self, trace_id: str, payload: dict[str, Any]) -> None:
        """Persist one trace payload."""

    def get(self, trace_id: str) -> dict[str, Any] | None:
        """Fetch one trace payload."""


class ArtifactRepository(Protocol):
    """Repository contract for binary or JSON artifacts."""

    def put(self, artifact_id: str, payload: dict[str, Any]) -> None:
        """Persist one artifact payload."""

    def get(self, artifact_id: str) -> dict[str, Any] | None:
        """Fetch one artifact payload."""


@dataclass
class SQLiteTraceRepository:
    """SQLite implementation of trace storage contract."""

    db_path: str = "trace_plane.db"

    def __post_init__(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS traces (
                    trace_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def put(self, trace_id: str, payload: dict[str, Any]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO traces (trace_id, payload) VALUES (?, ?)",
                (trace_id, json.dumps(payload)),
            )
            conn.commit()

    def get(self, trace_id: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT payload FROM traces WHERE trace_id = ?",
                (trace_id,),
            ).fetchone()
        return json.loads(row[0]) if row else None


@dataclass
class SQLiteArtifactRepository:
    """SQLite implementation of artifact storage contract."""

    db_path: str = "artifact_plane.db"

    def __post_init__(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def put(self, artifact_id: str, payload: dict[str, Any]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO artifacts (artifact_id, payload) VALUES (?, ?)",
                (artifact_id, json.dumps(payload)),
            )
            conn.commit()

    def get(self, artifact_id: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT payload FROM artifacts WHERE artifact_id = ?",
                (artifact_id,),
            ).fetchone()
        return json.loads(row[0]) if row else None

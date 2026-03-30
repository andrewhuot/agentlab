"""Unified experiment store shared by CLI and API.

Replaces the split between CLI's TSV-based experiment_log and the API's
in-memory experiment store with a single SQLite-backed store.
"""

from __future__ import annotations

import sqlite3
import threading
import time
import uuid
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DEFAULT_DB_PATH = Path(".autoagent/experiments.db")

_DDL = """
CREATE TABLE IF NOT EXISTS experiments (
    id          TEXT PRIMARY KEY,
    cycle       INTEGER NOT NULL,
    timestamp   TEXT NOT NULL,
    score_before REAL,
    score_after  REAL,
    delta        REAL,
    status       TEXT NOT NULL,
    description  TEXT NOT NULL DEFAULT '',
    operator     TEXT NOT NULL DEFAULT '',
    failure_family TEXT NOT NULL DEFAULT '',
    config_diff  TEXT,
    reviewed_by  TEXT,
    promoted_at  TEXT,
    rejected_at  TEXT,
    rejection_reason TEXT,
    created_at   REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);
CREATE INDEX IF NOT EXISTS idx_experiments_cycle ON experiments(cycle);
"""


@dataclass(frozen=True)
class ExperimentEntry:
    """Unified experiment record used by both CLI and API."""
    id: str
    cycle: int
    timestamp: str
    score_before: Optional[float]
    score_after: Optional[float]
    delta: Optional[float]
    status: str
    description: str
    operator: str = ""
    failure_family: str = ""
    config_diff: Optional[str] = None
    reviewed_by: Optional[str] = None
    promoted_at: Optional[str] = None
    rejected_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: float = 0.0

    def to_dict(self) -> dict:
        """JSON-safe dict for API responses and CLI --json output."""
        return {
            "id": self.id,
            "cycle": self.cycle,
            "timestamp": self.timestamp,
            "score_before": self.score_before,
            "score_after": self.score_after,
            "delta": self.delta,
            "status": self.status,
            "description": self.description,
            "operator": self.operator,
            "failure_family": self.failure_family,
            "config_diff": self.config_diff,
            "reviewed_by": self.reviewed_by,
            "promoted_at": self.promoted_at,
            "rejected_at": self.rejected_at,
            "rejection_reason": self.rejection_reason,
        }


class ExperimentStore:
    """SQLite-backed experiment store for CLI and API."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(_DDL)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def append(self, entry: ExperimentEntry) -> None:
        """Insert a new experiment entry."""
        with self._lock, self._connect() as conn:
            conn.execute(
                """INSERT INTO experiments
                   (id, cycle, timestamp, score_before, score_after, delta,
                    status, description, operator, failure_family, config_diff,
                    reviewed_by, promoted_at, rejected_at, rejection_reason, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    entry.id, entry.cycle, entry.timestamp,
                    entry.score_before, entry.score_after, entry.delta,
                    entry.status, entry.description, entry.operator,
                    entry.failure_family, entry.config_diff, entry.reviewed_by,
                    entry.promoted_at, entry.rejected_at, entry.rejection_reason,
                    entry.created_at or time.time(),
                ),
            )

    def get_all(self) -> list[ExperimentEntry]:
        """Return all entries ordered by cycle."""
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM experiments ORDER BY cycle ASC").fetchall()
        return [self._row_to_entry(r) for r in rows]

    def list_recent(self, limit: int = 50) -> list[ExperimentEntry]:
        """Return the most recent entries."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM experiments ORDER BY cycle DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._row_to_entry(r) for r in reversed(rows)]

    def list_by_status(self, status: str, limit: int = 50) -> list[ExperimentEntry]:
        """Return entries filtered by status."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM experiments WHERE status = ? ORDER BY cycle DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        return [self._row_to_entry(r) for r in reversed(rows)]

    def next_cycle_number(self) -> int:
        """Return the next cycle number."""
        with self._connect() as conn:
            row = conn.execute("SELECT MAX(cycle) as max_cycle FROM experiments").fetchone()
        max_cycle = row["max_cycle"] if row and row["max_cycle"] is not None else 0
        return max_cycle + 1

    def best_score_entry(self) -> Optional[ExperimentEntry]:
        """Return the entry with the highest score_after."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM experiments WHERE score_after IS NOT NULL ORDER BY score_after DESC LIMIT 1"
            ).fetchone()
        return self._row_to_entry(row) if row else None

    def update_status(self, entry_id: str, status: str) -> None:
        """Update the status of an experiment."""
        with self._lock, self._connect() as conn:
            conn.execute(
                "UPDATE experiments SET status = ? WHERE id = ?",
                (status, entry_id),
            )

    def import_from_tsv(self, tsv_path: Path) -> int:
        """Import entries from the legacy TSV experiment log. Returns count imported."""
        import csv
        if not tsv_path.exists():
            return 0

        with tsv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            count = 0
            for row in reader:
                entry = ExperimentEntry(
                    id=str(uuid.uuid4()),
                    cycle=int(row.get("cycle", 0)),
                    timestamp=row.get("timestamp", ""),
                    score_before=_parse_float(row.get("score_before")),
                    score_after=_parse_float(row.get("score_after")),
                    delta=_parse_float(row.get("delta")),
                    status=row.get("status", ""),
                    description=row.get("description", ""),
                    created_at=time.time(),
                )
                self.append(entry)
                count += 1
        return count

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> ExperimentEntry:
        return ExperimentEntry(
            id=row["id"],
            cycle=row["cycle"],
            timestamp=row["timestamp"],
            score_before=row["score_before"],
            score_after=row["score_after"],
            delta=row["delta"],
            status=row["status"],
            description=row["description"],
            operator=row["operator"] or "",
            failure_family=row["failure_family"] or "",
            config_diff=row["config_diff"],
            reviewed_by=row["reviewed_by"],
            promoted_at=row["promoted_at"],
            rejected_at=row["rejected_at"],
            rejection_reason=row["rejection_reason"],
            created_at=row["created_at"],
        )


def _parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    stripped = value.strip()
    return float(stripped) if stripped else None


def make_entry(
    *,
    cycle: int,
    status: str,
    description: str,
    score_before: float | None,
    score_after: float | None,
    timestamp: str | None = None,
    operator: str = "",
    failure_family: str = "",
) -> ExperimentEntry:
    """Build a validated entry with auto-computed delta. Drop-in for cli.experiment_log.make_entry."""
    from cli.experiment_log import utc_timestamp, compute_delta
    return ExperimentEntry(
        id=str(uuid.uuid4()),
        cycle=cycle,
        timestamp=timestamp or utc_timestamp(),
        score_before=score_before,
        score_after=score_after,
        delta=compute_delta(score_before, score_after),
        status=status,
        description=description,
        operator=operator,
        failure_family=failure_family,
        created_at=time.time(),
    )

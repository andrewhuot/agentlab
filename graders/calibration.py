"""Calibration utilities for judge-vs-human agreement and drift monitoring."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CalibrationRecord:
    case_id: str
    judge_score: float
    human_label: float


class CalibrationTracker:
    """Track agreement and drift against human labels."""

    def __init__(self, db_path: str = ".autoagent/grader_calibration.db") -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS grader_calibration (
                    case_id TEXT PRIMARY KEY,
                    judge_score REAL NOT NULL,
                    human_label REAL NOT NULL
                )
                """
            )
            conn.commit()

    def record(self, case_id: str, judge_score: float, human_label: float) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO grader_calibration
                    (case_id, judge_score, human_label)
                VALUES (?, ?, ?)
                """,
                (case_id, float(judge_score), float(human_label)),
            )
            conn.commit()

    def agreement_rate(self, threshold: float = 0.2) -> float:
        records = self._records()
        if not records:
            return 0.0
        agree = sum(
            1 for record in records if abs(record.judge_score - record.human_label) <= threshold
        )
        return round(agree / len(records), 4)

    def drift(self, baseline_window: int = 100, current_window: int = 20) -> float:
        """Estimate drift as delta between baseline and current mean error."""
        records = self._records()
        if len(records) < 2:
            return 0.0
        baseline = records[: max(1, min(len(records), baseline_window))]
        current = records[-max(1, min(len(records), current_window)) :]
        baseline_err = sum(abs(r.judge_score - r.human_label) for r in baseline) / len(baseline)
        current_err = sum(abs(r.judge_score - r.human_label) for r in current) / len(current)
        return round(current_err - baseline_err, 6)

    def _records(self) -> list[CalibrationRecord]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT case_id, judge_score, human_label
                FROM grader_calibration
                ORDER BY rowid ASC
                """
            ).fetchall()
        return [
            CalibrationRecord(case_id=row[0], judge_score=row[1], human_label=row[2])
            for row in rows
        ]

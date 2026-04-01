"""Human-vs-judge calibration — record and analyze human feedback on judge scores.

Provides a persistent store for paired (judge, human) scores so teams can
measure agreement, surface disagreements, and sample cases for review.
"""

from __future__ import annotations

import random
import sqlite3
import time
from dataclasses import dataclass, field


@dataclass
class HumanFeedback:
    """A single human-vs-judge calibration record."""

    feedback_id: str
    case_id: str
    judge_id: str
    judge_score: float
    human_score: float
    human_notes: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """Serialize to a plain dict."""
        return {
            "feedback_id": self.feedback_id,
            "case_id": self.case_id,
            "judge_id": self.judge_id,
            "judge_score": self.judge_score,
            "human_score": self.human_score,
            "human_notes": self.human_notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> HumanFeedback:
        """Deserialize from a plain dict."""
        return cls(
            feedback_id=data["feedback_id"],
            case_id=data["case_id"],
            judge_id=data["judge_id"],
            judge_score=data["judge_score"],
            human_score=data["human_score"],
            human_notes=data.get("human_notes", ""),
            created_at=data.get("created_at", 0.0),
        )


class HumanFeedbackStore:
    """SQLite-backed store for human calibration feedback."""

    def __init__(self, db_path: str = ".agentlab/human_feedback.db") -> None:
        self._db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS human_feedback (
                    feedback_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    judge_id TEXT NOT NULL,
                    judge_score REAL NOT NULL,
                    human_score REAL NOT NULL,
                    human_notes TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )

    def _row_to_feedback(self, row: tuple) -> HumanFeedback:
        return HumanFeedback(
            feedback_id=row[0],
            case_id=row[1],
            judge_id=row[2],
            judge_score=row[3],
            human_score=row[4],
            human_notes=row[5],
            created_at=row[6],
        )

    def record(self, feedback: HumanFeedback) -> None:
        """Persist a human feedback record."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO human_feedback
                    (feedback_id, case_id, judge_id, judge_score, human_score, human_notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback.feedback_id,
                    feedback.case_id,
                    feedback.judge_id,
                    feedback.judge_score,
                    feedback.human_score,
                    feedback.human_notes,
                    feedback.created_at,
                ),
            )

    def get_feedback(self, feedback_id: str) -> HumanFeedback | None:
        """Retrieve a specific feedback record by ID."""
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT feedback_id, case_id, judge_id, judge_score, human_score, human_notes, created_at "
                "FROM human_feedback WHERE feedback_id = ?",
                (feedback_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_feedback(row)

    def list_feedback(
        self,
        judge_id: str | None = None,
        limit: int = 100,
    ) -> list[HumanFeedback]:
        """List feedback records, optionally filtered by judge_id."""
        with sqlite3.connect(self._db_path) as conn:
            if judge_id is not None:
                rows = conn.execute(
                    "SELECT feedback_id, case_id, judge_id, judge_score, human_score, human_notes, created_at "
                    "FROM human_feedback WHERE judge_id = ? ORDER BY created_at DESC LIMIT ?",
                    (judge_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT feedback_id, case_id, judge_id, judge_score, human_score, human_notes, created_at "
                    "FROM human_feedback ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [self._row_to_feedback(r) for r in rows]

    def agreement_rate(
        self,
        judge_id: str | None = None,
        threshold: float = 0.2,
    ) -> float:
        """Fraction of records where |judge - human| <= threshold."""
        records = self.list_feedback(judge_id=judge_id, limit=10_000)
        if not records:
            return 0.0
        agreed = sum(
            1 for r in records if abs(r.judge_score - r.human_score) <= threshold
        )
        return agreed / len(records)

    def disagreements(
        self,
        judge_id: str | None = None,
        limit: int = 20,
    ) -> list[HumanFeedback]:
        """Records sorted by |judge - human| descending (highest disagreement first)."""
        records = self.list_feedback(judge_id=judge_id, limit=10_000)
        records.sort(key=lambda r: abs(r.judge_score - r.human_score), reverse=True)
        return records[:limit]

    def sample_for_review(
        self,
        judge_id: str | None = None,
        n: int = 50,
    ) -> list[HumanFeedback]:
        """Random sample from recent feedback for human calibration review."""
        records = self.list_feedback(judge_id=judge_id, limit=10_000)
        if len(records) <= n:
            return records
        return random.sample(records, n)

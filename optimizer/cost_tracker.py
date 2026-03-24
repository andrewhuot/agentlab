"""Budget and ROI tracking for optimization cycles."""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class CycleCostRecord:
    """One optimization cycle spend/improvement record."""

    cycle_id: str
    timestamp: float
    date_utc: str
    spent_dollars: float
    improvement_delta: float


class CostTracker:
    """Track cycle spend against per-cycle and daily budgets."""

    def __init__(
        self,
        db_path: str = ".autoagent/cost_tracker.db",
        per_cycle_budget_dollars: float = 1.0,
        daily_budget_dollars: float = 10.0,
        stall_threshold_cycles: int = 5,
    ) -> None:
        self.db_path = db_path
        self.per_cycle_budget_dollars = per_cycle_budget_dollars
        self.daily_budget_dollars = daily_budget_dollars
        self.stall_threshold_cycles = max(1, stall_threshold_cycles)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Create cycle cost table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cycle_costs (
                    cycle_id TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    date_utc TEXT NOT NULL,
                    spent_dollars REAL NOT NULL,
                    improvement_delta REAL NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cycle_costs_date ON cycle_costs(date_utc)"
            )
            conn.commit()

    def can_start_cycle(self, estimated_cycle_cost: float) -> tuple[bool, str]:
        """Validate whether budgets allow a new cycle."""
        if estimated_cycle_cost > self.per_cycle_budget_dollars:
            return (
                False,
                f"Per-cycle budget exceeded: ${estimated_cycle_cost:.4f} > ${self.per_cycle_budget_dollars:.4f}",
            )

        today = self._today_utc()
        daily_spend = self._daily_spend(today)
        if daily_spend + estimated_cycle_cost > self.daily_budget_dollars:
            return (
                False,
                (
                    "Daily budget exceeded: "
                    f"${daily_spend + estimated_cycle_cost:.4f} > ${self.daily_budget_dollars:.4f}"
                ),
            )
        return True, "ok"

    def record_cycle(
        self,
        cycle_id: str,
        spent_dollars: float,
        improvement_delta: float,
    ) -> CycleCostRecord:
        """Persist one cycle cost/improvement record."""
        record = CycleCostRecord(
            cycle_id=cycle_id,
            timestamp=time.time(),
            date_utc=self._today_utc(),
            spent_dollars=round(float(spent_dollars), 6),
            improvement_delta=round(float(improvement_delta), 6),
        )
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cycle_costs
                    (cycle_id, timestamp, date_utc, spent_dollars, improvement_delta)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record.cycle_id,
                    record.timestamp,
                    record.date_utc,
                    record.spent_dollars,
                    record.improvement_delta,
                ),
            )
            conn.commit()
        return record

    def summary(self) -> dict[str, float]:
        """Return aggregate spend and ROI stats."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT
                    COALESCE(SUM(spent_dollars), 0.0),
                    COALESCE(SUM(CASE WHEN improvement_delta > 0 THEN improvement_delta ELSE 0 END), 0.0)
                FROM cycle_costs
                """
            ).fetchone()

        total_spend = float(row[0]) if row else 0.0
        total_improvement = float(row[1]) if row else 0.0
        if total_improvement > 0:
            cost_per_improvement = total_spend / total_improvement
        else:
            cost_per_improvement = 0.0
        return {
            "total_spend": round(total_spend, 6),
            "total_improvement": round(total_improvement, 6),
            "cost_per_improvement": round(cost_per_improvement, 6),
            "today_spend": round(self._daily_spend(self._today_utc()), 6),
        }

    def recent_cycles(self, limit: int = 50) -> list[dict[str, float | str]]:
        """Return recent cycle records in chronological order."""
        records = self._recent_records(limit=max(1, limit))
        chronological = list(reversed(records))
        return [
            {
                "cycle_id": record.cycle_id,
                "timestamp": record.timestamp,
                "date_utc": record.date_utc,
                "spent_dollars": record.spent_dollars,
                "improvement_delta": record.improvement_delta,
            }
            for record in chronological
        ]

    def should_pause_for_stall(self) -> bool:
        """Return True when recent cycles show diminishing returns stall."""
        recent = self._recent_records(limit=self.stall_threshold_cycles)
        if len(recent) < self.stall_threshold_cycles:
            return False
        return all(record.improvement_delta <= 0 for record in recent)

    def _recent_records(self, limit: int) -> list[CycleCostRecord]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT cycle_id, timestamp, date_utc, spent_dollars, improvement_delta
                FROM cycle_costs
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            CycleCostRecord(
                cycle_id=row[0],
                timestamp=row[1],
                date_utc=row[2],
                spent_dollars=row[3],
                improvement_delta=row[4],
            )
            for row in rows
        ]

    def _daily_spend(self, date_utc: str) -> float:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(spent_dollars), 0.0) FROM cycle_costs WHERE date_utc = ?",
                (date_utc,),
            ).fetchone()
        return float(row[0]) if row else 0.0

    @staticmethod
    def _today_utc() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

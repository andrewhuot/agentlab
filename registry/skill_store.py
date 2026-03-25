"""SQLite-backed store for executable skills (Track A).

Uses its own isolated SQLite connection and schema, separate from RegistryStore.
All skill data is serialized as JSON blobs keyed by (name, version).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from registry.skill_types import Skill


_DDL = """
CREATE TABLE IF NOT EXISTS executable_skills (
    name       TEXT    NOT NULL,
    version    INTEGER NOT NULL,
    data       TEXT    NOT NULL,
    category   TEXT    NOT NULL,
    platform   TEXT    NOT NULL,
    status     TEXT    NOT NULL DEFAULT 'active',
    created_at TEXT    NOT NULL,
    PRIMARY KEY (name, version)
);

CREATE TABLE IF NOT EXISTS skill_outcomes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name  TEXT    NOT NULL,
    improvement REAL    NOT NULL,
    success     INTEGER NOT NULL,
    recorded_at TEXT    NOT NULL
);
"""

_OPERATORS: dict[str, Any] = {
    "gt": lambda v, t: v > t,
    "lt": lambda v, t: v < t,
    "gte": lambda v, t: v >= t,
    "lte": lambda v, t: v <= t,
    "eq": lambda v, t: v == t,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SkillStore:
    """SQLite-backed persistence for executable skills."""

    def __init__(self, db_path: str = "registry.db") -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_DDL)
        self._conn.commit()

    # ------------------------------------------------------------------
    # Core CRUD
    # ------------------------------------------------------------------

    def register(self, skill: Skill) -> tuple[str, int]:
        """Insert skill, auto-incrementing the version for the same name."""
        cur = self._conn.execute(
            "SELECT COALESCE(MAX(version), 0) FROM executable_skills WHERE name = ?",
            (skill.name,),
        )
        next_version: int = cur.fetchone()[0] + 1
        skill.version = next_version

        data_json = json.dumps(skill.to_dict())
        self._conn.execute(
            """
            INSERT INTO executable_skills (name, version, data, category, platform, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                skill.name,
                skill.version,
                data_json,
                skill.category,
                skill.platform,
                skill.status,
                _now_iso(),
            ),
        )
        self._conn.commit()
        return (skill.name, skill.version)

    def get(self, name: str, version: int | None = None) -> Skill | None:
        """Return a skill by name, defaulting to the latest version."""
        if version is None:
            row = self._conn.execute(
                """
                SELECT data FROM executable_skills
                WHERE name = ?
                ORDER BY version DESC LIMIT 1
                """,
                (name,),
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT data FROM executable_skills WHERE name = ? AND version = ?",
                (name, version),
            ).fetchone()

        if row is None:
            return None
        return Skill.from_dict(json.loads(row["data"]))

    # ------------------------------------------------------------------
    # Listing and search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        category: str | None = None,
        platform: str | None = None,
    ) -> list[Skill]:
        """LIKE search on name and JSON data blob.  Returns latest version of each match."""
        like_query = f"%{query}%"
        sql = """
            SELECT name, MAX(version) as max_version, data
            FROM executable_skills
            WHERE (name LIKE ? OR data LIKE ?)
        """
        params: list[Any] = [like_query, like_query]

        if category is not None:
            sql += " AND category = ?"
            params.append(category)
        if platform is not None:
            sql += " AND platform = ?"
            params.append(platform)

        sql += " GROUP BY name"

        rows = self._conn.execute(sql, params).fetchall()
        return [Skill.from_dict(json.loads(r["data"])) for r in rows]

    def list(
        self,
        category: str | None = None,
        platform: str | None = None,
        tags: list[str] | None = None,
        status: str | None = None,
    ) -> list[Skill]:
        """Return latest version of each skill, with optional filters."""
        sql = """
            SELECT name, MAX(version) as max_version, data, category, platform, status
            FROM executable_skills
            WHERE 1=1
        """
        params: list[Any] = []

        if category is not None:
            sql += " AND category = ?"
            params.append(category)
        if platform is not None:
            sql += " AND platform = ?"
            params.append(platform)
        if status is not None:
            sql += " AND status = ?"
            params.append(status)

        sql += " GROUP BY name"

        rows = self._conn.execute(sql, params).fetchall()
        skills: list[Skill] = []
        for row in rows:
            skill = Skill.from_dict(json.loads(row["data"]))
            if tags is not None:
                data_str = row["data"]
                if not any(tag in data_str for tag in tags):
                    continue
            skills.append(skill)
        return skills

    # ------------------------------------------------------------------
    # Recommendation engine
    # ------------------------------------------------------------------

    def recommend(
        self,
        failure_family: str | None = None,
        metrics: dict[str, float] | None = None,
    ) -> list[Skill]:
        """Return skills whose triggers match the given failure family or metric thresholds."""
        all_skills = self.list(status="active")
        matched: list[Skill] = []

        for skill in all_skills:
            for trigger in skill.triggers:
                # Match by failure family
                if failure_family is not None and trigger.failure_family == failure_family:
                    matched.append(skill)
                    break

                # Match by metric threshold
                if (
                    metrics is not None
                    and trigger.metric_name is not None
                    and trigger.threshold is not None
                    and trigger.metric_name in metrics
                ):
                    op_fn = _OPERATORS.get(trigger.operator)
                    if op_fn is not None and op_fn(metrics[trigger.metric_name], trigger.threshold):
                        matched.append(skill)
                        break

        matched.sort(
            key=lambda s: (s.success_rate * (s.proven_improvement or 0.0)),
            reverse=True,
        )
        return matched

    # ------------------------------------------------------------------
    # Outcome tracking
    # ------------------------------------------------------------------

    def record_outcome(self, skill_name: str, improvement: float, success: bool) -> None:
        """Record an outcome and recalculate stats on the latest skill version."""
        self._conn.execute(
            """
            INSERT INTO skill_outcomes (skill_name, improvement, success, recorded_at)
            VALUES (?, ?, ?, ?)
            """,
            (skill_name, improvement, int(success), _now_iso()),
        )
        self._conn.commit()

        # Recalculate aggregates from outcomes table
        rows = self._conn.execute(
            "SELECT improvement, success FROM skill_outcomes WHERE skill_name = ?",
            (skill_name,),
        ).fetchall()

        times_applied = len(rows)
        successes = [r["improvement"] for r in rows if r["success"]]
        success_rate = len(successes) / times_applied if times_applied > 0 else 0.0
        proven_improvement: float | None = (
            sum(successes) / len(successes) if successes else None
        )

        # Update the latest version's JSON blob
        skill = self.get(skill_name)
        if skill is None:
            return

        skill.times_applied = times_applied
        skill.success_rate = success_rate
        skill.proven_improvement = proven_improvement

        self._conn.execute(
            """
            UPDATE executable_skills
            SET data = ?, status = ?
            WHERE name = ? AND version = ?
            """,
            (
                json.dumps(skill.to_dict()),
                skill.status,
                skill.name,
                skill.version,
            ),
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def top_performers(self, n: int = 10) -> list[Skill]:
        """Return top-n active skills by proven_improvement * success_rate."""
        skills = self.list(status="active")
        eligible = [s for s in skills if s.times_applied > 0]
        eligible.sort(
            key=lambda s: (s.proven_improvement or 0.0) * s.success_rate,
            reverse=True,
        )
        return eligible[:n]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._conn.close()

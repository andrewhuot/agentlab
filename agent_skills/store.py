"""SQLite persistence for generated agent skills."""
from __future__ import annotations

import json
import sqlite3
import time
from typing import Any

from agent_skills.types import GeneratedFile, GeneratedSkill


class AgentSkillStore:
    """SQLite-backed store for generated agent skills."""

    def __init__(self, db_path: str = ".autoagent/agent_skills.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_skills (
                    skill_id TEXT PRIMARY KEY,
                    gap_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    skill_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    source_code TEXT,
                    config_yaml TEXT,
                    files TEXT NOT NULL DEFAULT '[]',
                    eval_criteria TEXT NOT NULL DEFAULT '[]',
                    estimated_improvement REAL NOT NULL DEFAULT 0.0,
                    confidence TEXT NOT NULL DEFAULT 'medium',
                    status TEXT NOT NULL DEFAULT 'draft',
                    review_notes TEXT NOT NULL DEFAULT '',
                    created_at REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS skill_gaps (
                    gap_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)
            conn.commit()

    def save(self, skill: GeneratedSkill) -> None:
        """Store a generated skill."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO agent_skills
                   (skill_id, gap_id, platform, skill_type, name, description,
                    source_code, config_yaml, files, eval_criteria,
                    estimated_improvement, confidence, status, review_notes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    skill.skill_id,
                    skill.gap_id,
                    skill.platform,
                    skill.skill_type,
                    skill.name,
                    skill.description,
                    skill.source_code,
                    skill.config_yaml,
                    json.dumps([f.to_dict() for f in skill.files]),
                    json.dumps(skill.eval_criteria),
                    skill.estimated_improvement,
                    skill.confidence,
                    skill.status,
                    skill.review_notes,
                    skill.created_at,
                ),
            )
            conn.commit()

    def get(self, skill_id: str) -> GeneratedSkill | None:
        """Retrieve a skill by ID."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM agent_skills WHERE skill_id = ?", (skill_id,)
            ).fetchone()
            if row is None:
                return None
            return self._row_to_skill(row)

    def list(self, status: str | None = None, platform: str | None = None) -> list[GeneratedSkill]:
        """List skills with optional filters."""
        query = "SELECT * FROM agent_skills"
        conditions: list[str] = []
        params: list[Any] = []
        if status:
            conditions.append("status = ?")
            params.append(status)
        if platform:
            conditions.append("platform = ?")
            params.append(platform)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at DESC"

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_skill(row) for row in rows]

    def approve(self, skill_id: str) -> bool:
        """Mark a skill as approved."""
        return self._update_status(skill_id, "approved")

    def reject(self, skill_id: str, reason: str = "") -> bool:
        """Mark a skill as rejected."""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                "UPDATE agent_skills SET status = 'rejected', review_notes = ? WHERE skill_id = ?",
                (reason, skill_id),
            )
            conn.commit()
            return result.rowcount > 0

    def list_by_gap(self, gap_id: str) -> list[GeneratedSkill]:
        """List all skills generated for a specific gap."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM agent_skills WHERE gap_id = ? ORDER BY created_at DESC",
                (gap_id,),
            ).fetchall()
            return [self._row_to_skill(row) for row in rows]

    def save_gap(self, gap: Any) -> None:
        """Store a SkillGap for reference."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO skill_gaps (gap_id, data, created_at) VALUES (?, ?, ?)",
                (gap.gap_id, json.dumps(gap.to_dict()), time.time()),
            )
            conn.commit()

    def list_gaps(self) -> list[dict[str, Any]]:
        """List all stored skill gaps."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT data FROM skill_gaps ORDER BY created_at DESC"
            ).fetchall()
            return [json.loads(row[0]) for row in rows]

    def _update_status(self, skill_id: str, status: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                "UPDATE agent_skills SET status = ? WHERE skill_id = ?",
                (status, skill_id),
            )
            conn.commit()
            return result.rowcount > 0

    @staticmethod
    def _row_to_skill(row: tuple) -> GeneratedSkill:
        files_raw = json.loads(row[8])
        files = [
            GeneratedFile(
                path=f["path"],
                content=f["content"],
                is_new=f["is_new"],
                diff=f.get("diff"),
            )
            for f in files_raw
        ]
        return GeneratedSkill(
            skill_id=row[0],
            gap_id=row[1],
            platform=row[2],
            skill_type=row[3],
            name=row[4],
            description=row[5],
            source_code=row[6],
            config_yaml=row[7],
            files=files,
            eval_criteria=json.loads(row[9]),
            estimated_improvement=row[10],
            confidence=row[11],
            status=row[12],
            review_notes=row[13],
            created_at=row[14],
        )

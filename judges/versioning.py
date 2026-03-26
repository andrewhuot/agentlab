"""Grader versioning — track config changes across grader iterations.

Stores versioned snapshots of grader configurations in SQLite so teams
can diff rubric changes, roll back, and audit how scoring evolved.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field


@dataclass
class GraderVersion:
    """Immutable snapshot of a grader's configuration at a point in time."""

    version_id: str
    grader_id: str
    version: int
    config: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    parent_version_id: str | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to a plain dict."""
        return {
            "version_id": self.version_id,
            "grader_id": self.grader_id,
            "version": self.version,
            "config": self.config,
            "created_at": self.created_at,
            "parent_version_id": self.parent_version_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GraderVersion:
        """Deserialize from a plain dict."""
        return cls(
            version_id=data["version_id"],
            grader_id=data["grader_id"],
            version=data["version"],
            config=data.get("config", {}),
            created_at=data.get("created_at", 0.0),
            parent_version_id=data.get("parent_version_id"),
            metadata=data.get("metadata", {}),
        )


class GraderVersionStore:
    """SQLite-backed store for grader version history."""

    def __init__(self, db_path: str = ".autoagent/grader_versions.db") -> None:
        self._db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS grader_versions (
                    version_id TEXT PRIMARY KEY,
                    grader_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    config TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    parent_version_id TEXT,
                    metadata TEXT NOT NULL
                )
                """
            )

    def save_version(self, version: GraderVersion) -> None:
        """Persist a grader version snapshot."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO grader_versions
                    (version_id, grader_id, version, config, created_at, parent_version_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version.version_id,
                    version.grader_id,
                    version.version,
                    json.dumps(version.config, sort_keys=True, default=str),
                    version.created_at,
                    version.parent_version_id,
                    json.dumps(version.metadata, sort_keys=True, default=str),
                ),
            )

    def get_version(self, version_id: str) -> GraderVersion | None:
        """Retrieve a specific version by ID."""
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT version_id, grader_id, version, config, created_at, parent_version_id, metadata "
                "FROM grader_versions WHERE version_id = ?",
                (version_id,),
            ).fetchone()
        if row is None:
            return None
        return GraderVersion(
            version_id=row[0],
            grader_id=row[1],
            version=row[2],
            config=json.loads(row[3]),
            created_at=row[4],
            parent_version_id=row[5],
            metadata=json.loads(row[6]),
        )

    def list_versions(self, grader_id: str) -> list[GraderVersion]:
        """All versions for a grader, ordered by version number."""
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT version_id, grader_id, version, config, created_at, parent_version_id, metadata "
                "FROM grader_versions WHERE grader_id = ? ORDER BY version ASC",
                (grader_id,),
            ).fetchall()
        return [
            GraderVersion(
                version_id=r[0],
                grader_id=r[1],
                version=r[2],
                config=json.loads(r[3]),
                created_at=r[4],
                parent_version_id=r[5],
                metadata=json.loads(r[6]),
            )
            for r in rows
        ]

    def get_latest(self, grader_id: str) -> GraderVersion | None:
        """Get the highest-versioned snapshot for a grader."""
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT version_id, grader_id, version, config, created_at, parent_version_id, metadata "
                "FROM grader_versions WHERE grader_id = ? ORDER BY version DESC LIMIT 1",
                (grader_id,),
            ).fetchone()
        if row is None:
            return None
        return GraderVersion(
            version_id=row[0],
            grader_id=row[1],
            version=row[2],
            config=json.loads(row[3]),
            created_at=row[4],
            parent_version_id=row[5],
            metadata=json.loads(row[6]),
        )

    def list_all_graders(self) -> list[str]:
        """Return distinct grader IDs that have at least one version."""
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT DISTINCT grader_id FROM grader_versions ORDER BY grader_id"
            ).fetchall()
        return [row[0] for row in rows]

    def diff_versions(self, version_id_a: str, version_id_b: str) -> dict:
        """Compare configs of two versions, returning added/removed/changed keys."""
        va = self.get_version(version_id_a)
        vb = self.get_version(version_id_b)
        if va is None or vb is None:
            return {"added": {}, "removed": {}, "changed": {}}

        config_a = va.config
        config_b = vb.config
        all_keys = set(config_a.keys()) | set(config_b.keys())

        added: dict = {}
        removed: dict = {}
        changed: dict = {}

        for key in all_keys:
            if key not in config_a:
                added[key] = config_b[key]
            elif key not in config_b:
                removed[key] = config_a[key]
            elif config_a[key] != config_b[key]:
                changed[key] = {"old": config_a[key], "new": config_b[key]}

        return {"added": added, "removed": removed, "changed": changed}

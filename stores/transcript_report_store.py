"""Unified transcript report store shared by CLI and API.

Replaces the split between CLI's JSON-file store and the API's in-memory
TranscriptIntelligenceService._reports with a single SQLite-backed store.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Optional

DEFAULT_DB_PATH = Path(".autoagent/transcript_reports.db")

_DDL = """
CREATE TABLE IF NOT EXISTS transcript_reports (
    id              TEXT PRIMARY KEY,
    created_at      REAL NOT NULL,
    archive_id      TEXT NOT NULL DEFAULT '',
    archive_name    TEXT NOT NULL DEFAULT '',
    status          TEXT NOT NULL DEFAULT 'processing',
    summary         TEXT,
    insights_json   TEXT NOT NULL DEFAULT '[]',
    derived_config_yaml TEXT,
    knowledge_asset_ids_json TEXT NOT NULL DEFAULT '[]',
    conversation_count INTEGER,
    processing_time_ms INTEGER,
    archive_base64  TEXT,
    report_json     TEXT
);
CREATE INDEX IF NOT EXISTS idx_reports_status ON transcript_reports(status);
"""


class TranscriptReportStore:
    """SQLite-backed transcript report store for CLI and API."""

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

    def save_report(
        self,
        *,
        report_id: str | None = None,
        archive_name: str = "",
        archive_id: str = "",
        status: str = "complete",
        summary: str | None = None,
        insights: list[dict] | None = None,
        derived_config_yaml: str | None = None,
        knowledge_asset_ids: list[str] | None = None,
        conversation_count: int | None = None,
        processing_time_ms: int | None = None,
        archive_base64: str | None = None,
        report_json: dict | None = None,
    ) -> str:
        """Save or update a transcript report. Returns the report ID."""
        rid = report_id or str(uuid.uuid4())
        with self._lock, self._connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO transcript_reports
                   (id, created_at, archive_id, archive_name, status, summary,
                    insights_json, derived_config_yaml, knowledge_asset_ids_json,
                    conversation_count, processing_time_ms, archive_base64, report_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    rid, time.time(), archive_id, archive_name, status, summary,
                    json.dumps(insights or []),
                    derived_config_yaml,
                    json.dumps(knowledge_asset_ids or []),
                    conversation_count, processing_time_ms, archive_base64,
                    json.dumps(report_json) if report_json else None,
                ),
            )
        return rid

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        """Return a report by ID as a dict, or None."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM transcript_reports WHERE id = ?", (report_id,)
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def list_reports(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return recent reports, newest first."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM transcript_reports ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def delete_report(self, report_id: str) -> bool:
        """Delete a report. Returns True if it existed."""
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM transcript_reports WHERE id = ?", (report_id,)
            )
        return cursor.rowcount > 0

    def import_from_json(self, json_path: Path) -> int:
        """Import from the legacy CLI JSON store. Returns count imported."""
        if not json_path.exists():
            return 0
        data = json.loads(json_path.read_text(encoding="utf-8"))
        reports = data.get("reports", {})
        count = 0
        for rid, entry in reports.items():
            report_data = entry.get("report", {})
            self.save_report(
                report_id=rid,
                archive_name=entry.get("archive_name", ""),
                archive_id=rid,
                status="complete",
                summary=report_data.get("summary"),
                insights=report_data.get("insights"),
                conversation_count=report_data.get("conversation_count"),
                archive_base64=entry.get("archive_base64"),
                report_json=report_data,
            )
            count += 1
        return count

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "created_at": row["created_at"],
            "archive_id": row["archive_id"],
            "archive_name": row["archive_name"],
            "status": row["status"],
            "summary": row["summary"],
            "insights": json.loads(row["insights_json"]),
            "derived_config_yaml": row["derived_config_yaml"],
            "knowledge_asset_ids": json.loads(row["knowledge_asset_ids_json"]),
            "conversation_count": row["conversation_count"],
            "processing_time_ms": row["processing_time_ms"],
            "report_json": json.loads(row["report_json"]) if row["report_json"] else None,
        }

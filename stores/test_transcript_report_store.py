"""Tests for the unified SQLite-backed TranscriptReportStore."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from stores.transcript_report_store import TranscriptReportStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_store(tmp_path: Path) -> TranscriptReportStore:
    return TranscriptReportStore(db_path=tmp_path / "reports.db")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestStoreInit:
    def test_creates_db_file(self, tmp_path: Path) -> None:
        db = tmp_path / "reports.db"
        TranscriptReportStore(db_path=db)
        assert db.exists(), "DB file should be created on init"

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        db = tmp_path / "nested" / "dir" / "reports.db"
        TranscriptReportStore(db_path=db)
        assert db.exists()


class TestSaveAndGetReport:
    def test_roundtrip_minimal(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        rid = store.save_report(archive_name="test.zip")
        result = store.get_report(rid)
        assert result is not None
        assert result["id"] == rid
        assert result["archive_name"] == "test.zip"
        assert result["status"] == "complete"

    def test_roundtrip_full(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        rid = store.save_report(
            report_id="fixed-id-123",
            archive_name="convos.tar.gz",
            archive_id="arc-456",
            status="complete",
            summary="Customers ask about billing.",
            insights=[{"topic": "billing", "count": 42}],
            derived_config_yaml="model: gpt-4\n",
            knowledge_asset_ids=["ka-1", "ka-2"],
            conversation_count=100,
            processing_time_ms=2500,
            archive_base64="dGVzdA==",
            report_json={"summary": "Customers ask about billing.", "version": 1},
        )
        assert rid == "fixed-id-123"
        result = store.get_report(rid)
        assert result is not None
        assert result["archive_name"] == "convos.tar.gz"
        assert result["archive_id"] == "arc-456"
        assert result["summary"] == "Customers ask about billing."
        assert result["insights"] == [{"topic": "billing", "count": 42}]
        assert result["derived_config_yaml"] == "model: gpt-4\n"
        assert result["knowledge_asset_ids"] == ["ka-1", "ka-2"]
        assert result["conversation_count"] == 100
        assert result["processing_time_ms"] == 2500
        assert result["report_json"] == {"summary": "Customers ask about billing.", "version": 1}

    def test_returns_none_for_missing_id(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        assert store.get_report("does-not-exist") is None

    def test_save_generates_id_when_none_given(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        rid = store.save_report(archive_name="auto-id.zip")
        assert rid != ""
        assert store.get_report(rid) is not None

    def test_save_replaces_on_same_id(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save_report(report_id="r1", archive_name="first.zip", status="processing")
        store.save_report(report_id="r1", archive_name="first.zip", status="complete")
        result = store.get_report("r1")
        assert result is not None
        assert result["status"] == "complete"
        assert len(store.list_reports()) == 1


class TestListReports:
    def test_returns_newest_first(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        # Insert with slight delay to get distinct created_at values
        store.save_report(report_id="old", archive_name="old.zip")
        time.sleep(0.01)
        store.save_report(report_id="new", archive_name="new.zip")
        reports = store.list_reports()
        assert len(reports) == 2
        assert reports[0]["id"] == "new"
        assert reports[1]["id"] == "old"

    def test_empty_store_returns_empty_list(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        assert store.list_reports() == []

    def test_limit_respected(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        for i in range(10):
            store.save_report(archive_name=f"archive_{i}.zip")
        assert len(store.list_reports(limit=3)) == 3


class TestDeleteReport:
    def test_deletes_existing_report(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        rid = store.save_report(archive_name="to-delete.zip")
        assert store.delete_report(rid) is True
        assert store.get_report(rid) is None

    def test_returns_false_for_missing_report(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        assert store.delete_report("ghost-id") is False

    def test_does_not_affect_other_reports(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        r1 = store.save_report(archive_name="keep.zip")
        r2 = store.save_report(archive_name="delete.zip")
        store.delete_report(r2)
        assert store.get_report(r1) is not None
        assert len(store.list_reports()) == 1


class TestImportFromJson:
    def _write_legacy_json(self, path: Path, reports: dict) -> None:
        path.write_text(json.dumps({"reports": reports}), encoding="utf-8")

    def test_imports_legacy_format(self, tmp_path: Path) -> None:
        json_path = tmp_path / "intelligence_reports.json"
        self._write_legacy_json(json_path, {
            "report-abc": {
                "report_id": "report-abc",
                "archive_name": "legacy.zip",
                "archive_base64": "dGVzdA==",
                "created_at": 1700000000.0,
                "report": {
                    "summary": "Legacy summary",
                    "insights": [{"topic": "returns", "count": 5}],
                    "conversation_count": 20,
                },
            }
        })
        store = _make_store(tmp_path)
        count = store.import_from_json(json_path)
        assert count == 1
        result = store.get_report("report-abc")
        assert result is not None
        assert result["archive_name"] == "legacy.zip"
        assert result["summary"] == "Legacy summary"
        assert result["conversation_count"] == 20
        assert result["report_json"]["insights"] == [{"topic": "returns", "count": 5}]

    def test_returns_zero_for_missing_file(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        count = store.import_from_json(tmp_path / "nonexistent.json")
        assert count == 0

    def test_imports_multiple_reports(self, tmp_path: Path) -> None:
        json_path = tmp_path / "intelligence_reports.json"
        reports = {
            f"id-{i}": {
                "report_id": f"id-{i}",
                "archive_name": f"archive_{i}.zip",
                "archive_base64": "",
                "created_at": float(i),
                "report": {"summary": f"summary {i}"},
            }
            for i in range(5)
        }
        self._write_legacy_json(json_path, reports)
        store = _make_store(tmp_path)
        count = store.import_from_json(json_path)
        assert count == 5
        assert len(store.list_reports()) == 5


class TestInsightsSerialization:
    def test_empty_insights_deserialize_to_list(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        rid = store.save_report(archive_name="no-insights.zip", insights=None)
        result = store.get_report(rid)
        assert result is not None
        assert result["insights"] == []

    def test_complex_insights_roundtrip(self, tmp_path: Path) -> None:
        insights = [
            {"topic": "billing", "count": 42, "subtopics": ["invoices", "refunds"]},
            {"topic": "support", "count": 18, "metadata": {"priority": "high"}},
        ]
        store = _make_store(tmp_path)
        rid = store.save_report(archive_name="complex.zip", insights=insights)
        result = store.get_report(rid)
        assert result is not None
        assert result["insights"] == insights

    def test_knowledge_asset_ids_roundtrip(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        ids = ["ka-aaa", "ka-bbb", "ka-ccc"]
        rid = store.save_report(archive_name="kas.zip", knowledge_asset_ids=ids)
        result = store.get_report(rid)
        assert result is not None
        assert result["knowledge_asset_ids"] == ids

    def test_null_report_json_stays_none(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        rid = store.save_report(archive_name="no-json.zip", report_json=None)
        result = store.get_report(rid)
        assert result is not None
        assert result["report_json"] is None

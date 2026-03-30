"""Tests for the unified SQLite-backed ExperimentStore."""

from __future__ import annotations

import time
import uuid
from pathlib import Path

import pytest

from stores.experiment_store import ExperimentEntry, ExperimentStore, make_entry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(cycle: int, status: str = "keep", score_after: float | None = None) -> ExperimentEntry:
    return ExperimentEntry(
        id=str(uuid.uuid4()),
        cycle=cycle,
        timestamp="2024-01-01T00:00:00Z",
        score_before=0.5,
        score_after=score_after,
        delta=(score_after - 0.5) if score_after is not None else None,
        status=status,
        description=f"cycle {cycle} test entry",
        created_at=time.time(),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestStoreInit:
    def test_creates_db_file(self, tmp_path: Path) -> None:
        db = tmp_path / "test.db"
        store = ExperimentStore(db_path=db)
        assert db.exists(), "DB file should be created on init"

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        db = tmp_path / "nested" / "dir" / "test.db"
        ExperimentStore(db_path=db)
        assert db.exists()


class TestAppendAndGetAll:
    def test_roundtrip(self, tmp_path: Path) -> None:
        store = ExperimentStore(db_path=tmp_path / "exp.db")
        e = _entry(1, score_after=0.75)
        store.append(e)
        all_entries = store.get_all()
        assert len(all_entries) == 1
        result = all_entries[0]
        assert result.id == e.id
        assert result.cycle == 1
        assert result.status == "keep"
        assert result.score_after == pytest.approx(0.75)
        assert result.description == "cycle 1 test entry"

    def test_multiple_entries_ordered_by_cycle(self, tmp_path: Path) -> None:
        store = ExperimentStore(db_path=tmp_path / "exp.db")
        store.append(_entry(3))
        store.append(_entry(1))
        store.append(_entry(2))
        cycles = [e.cycle for e in store.get_all()]
        assert cycles == [1, 2, 3]

    def test_null_scores_preserved(self, tmp_path: Path) -> None:
        store = ExperimentStore(db_path=tmp_path / "exp.db")
        e = ExperimentEntry(
            id=str(uuid.uuid4()),
            cycle=1,
            timestamp="2024-01-01T00:00:00Z",
            score_before=None,
            score_after=None,
            delta=None,
            status="skip",
            description="no scores",
            created_at=time.time(),
        )
        store.append(e)
        result = store.get_all()[0]
        assert result.score_before is None
        assert result.score_after is None
        assert result.delta is None


class TestNextCycleNumber:
    def test_empty_store_returns_one(self, tmp_path: Path) -> None:
        store = ExperimentStore(db_path=tmp_path / "exp.db")
        assert store.next_cycle_number() == 1

    def test_increments_after_appends(self, tmp_path: Path) -> None:
        store = ExperimentStore(db_path=tmp_path / "exp.db")
        store.append(_entry(1))
        assert store.next_cycle_number() == 2
        store.append(_entry(2))
        assert store.next_cycle_number() == 3

    def test_uses_max_cycle_not_count(self, tmp_path: Path) -> None:
        store = ExperimentStore(db_path=tmp_path / "exp.db")
        store.append(_entry(10))
        store.append(_entry(5))
        # max is 10, so next should be 11
        assert store.next_cycle_number() == 11


class TestListByStatus:
    def test_filters_correctly(self, tmp_path: Path) -> None:
        store = ExperimentStore(db_path=tmp_path / "exp.db")
        store.append(_entry(1, status="keep"))
        store.append(_entry(2, status="discard"))
        store.append(_entry(3, status="keep"))
        store.append(_entry(4, status="skip"))

        keep_entries = store.list_by_status("keep")
        assert len(keep_entries) == 2
        assert all(e.status == "keep" for e in keep_entries)

        discard_entries = store.list_by_status("discard")
        assert len(discard_entries) == 1

        skip_entries = store.list_by_status("skip")
        assert len(skip_entries) == 1

    def test_empty_result_for_missing_status(self, tmp_path: Path) -> None:
        store = ExperimentStore(db_path=tmp_path / "exp.db")
        store.append(_entry(1, status="keep"))
        assert store.list_by_status("crash") == []

    def test_limit_respected(self, tmp_path: Path) -> None:
        store = ExperimentStore(db_path=tmp_path / "exp.db")
        for i in range(10):
            store.append(_entry(i + 1, status="keep"))
        result = store.list_by_status("keep", limit=3)
        assert len(result) == 3


class TestBestScoreEntry:
    def test_returns_highest_score(self, tmp_path: Path) -> None:
        store = ExperimentStore(db_path=tmp_path / "exp.db")
        store.append(_entry(1, score_after=0.6))
        store.append(_entry(2, score_after=0.9))
        store.append(_entry(3, score_after=0.7))
        best = store.best_score_entry()
        assert best is not None
        assert best.cycle == 2
        assert best.score_after == pytest.approx(0.9)

    def test_returns_none_when_no_scores(self, tmp_path: Path) -> None:
        store = ExperimentStore(db_path=tmp_path / "exp.db")
        store.append(_entry(1, score_after=None))
        assert store.best_score_entry() is None

    def test_returns_none_for_empty_store(self, tmp_path: Path) -> None:
        store = ExperimentStore(db_path=tmp_path / "exp.db")
        assert store.best_score_entry() is None

    def test_ignores_null_scores(self, tmp_path: Path) -> None:
        store = ExperimentStore(db_path=tmp_path / "exp.db")
        store.append(_entry(1, score_after=None))
        store.append(_entry(2, score_after=0.8))
        best = store.best_score_entry()
        assert best is not None
        assert best.score_after == pytest.approx(0.8)


class TestImportFromTsv:
    def test_imports_entries(self, tmp_path: Path) -> None:
        tsv = tmp_path / "experiment_log.tsv"
        tsv.write_text(
            "cycle\ttimestamp\tscore_before\tscore_after\tdelta\tstatus\tdescription\n"
            "1\t2024-01-01T00:00:00Z\t0.5000\t0.6000\t0.1000\tkeep\tfirst experiment\n"
            "2\t2024-01-02T00:00:00Z\t0.6000\t0.5500\t-0.0500\tdiscard\tsecond experiment\n",
            encoding="utf-8",
        )
        store = ExperimentStore(db_path=tmp_path / "exp.db")
        count = store.import_from_tsv(tsv)
        assert count == 2
        all_entries = store.get_all()
        assert len(all_entries) == 2
        assert all_entries[0].cycle == 1
        assert all_entries[0].status == "keep"
        assert all_entries[0].score_after == pytest.approx(0.6)
        assert all_entries[1].cycle == 2
        assert all_entries[1].status == "discard"

    def test_returns_zero_for_missing_file(self, tmp_path: Path) -> None:
        store = ExperimentStore(db_path=tmp_path / "exp.db")
        count = store.import_from_tsv(tmp_path / "nonexistent.tsv")
        assert count == 0

    def test_handles_empty_score_fields(self, tmp_path: Path) -> None:
        tsv = tmp_path / "experiment_log.tsv"
        tsv.write_text(
            "cycle\ttimestamp\tscore_before\tscore_after\tdelta\tstatus\tdescription\n"
            "1\t2024-01-01T00:00:00Z\t\t\t\tskip\tskipped cycle\n",
            encoding="utf-8",
        )
        store = ExperimentStore(db_path=tmp_path / "exp.db")
        count = store.import_from_tsv(tsv)
        assert count == 1
        entry = store.get_all()[0]
        assert entry.score_before is None
        assert entry.score_after is None
        assert entry.delta is None


class TestMakeEntry:
    def test_creates_valid_entry(self) -> None:
        entry = make_entry(
            cycle=5,
            status="keep",
            description="test make_entry",
            score_before=0.6,
            score_after=0.75,
        )
        assert entry.cycle == 5
        assert entry.status == "keep"
        assert entry.description == "test make_entry"
        assert entry.score_before == pytest.approx(0.6)
        assert entry.score_after == pytest.approx(0.75)
        assert entry.delta == pytest.approx(0.15)
        assert entry.id != ""
        assert entry.timestamp != ""

    def test_delta_is_none_when_scores_missing(self) -> None:
        entry = make_entry(
            cycle=1,
            status="skip",
            description="no scores",
            score_before=None,
            score_after=None,
        )
        assert entry.delta is None

    def test_delta_is_none_when_score_after_missing(self) -> None:
        entry = make_entry(
            cycle=1,
            status="crash",
            description="crashed",
            score_before=0.5,
            score_after=None,
        )
        assert entry.delta is None

    def test_custom_timestamp_preserved(self) -> None:
        ts = "2024-06-15T12:00:00Z"
        entry = make_entry(
            cycle=1,
            status="keep",
            description="with timestamp",
            score_before=None,
            score_after=0.8,
            timestamp=ts,
        )
        assert entry.timestamp == ts

    def test_operator_and_failure_family(self) -> None:
        entry = make_entry(
            cycle=2,
            status="discard",
            description="with extras",
            score_before=0.4,
            score_after=0.3,
            operator="test-op",
            failure_family="regression",
        )
        assert entry.operator == "test-op"
        assert entry.failure_family == "regression"

    def test_entry_is_appendable(self, tmp_path: Path) -> None:
        """make_entry output should roundtrip through the store."""
        store = ExperimentStore(db_path=tmp_path / "exp.db")
        entry = make_entry(
            cycle=1,
            status="keep",
            description="roundtrip",
            score_before=0.5,
            score_after=0.7,
        )
        store.append(entry)
        result = store.get_all()[0]
        assert result.id == entry.id
        assert result.delta == pytest.approx(0.2)

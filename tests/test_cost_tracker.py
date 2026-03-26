"""Unit tests for CostTracker budget and ROI tracking."""

from __future__ import annotations

import time
from pathlib import Path


from optimizer.cost_tracker import CostTracker, CycleCostRecord


def test_initialization_creates_db(tmp_path: Path) -> None:
    """Test that initialization creates the database and tables."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(db_path=db_path)

    assert Path(db_path).exists()
    assert tracker.db_path == db_path
    assert tracker.per_cycle_budget_dollars == 1.0
    assert tracker.daily_budget_dollars == 10.0
    assert tracker.stall_threshold_cycles == 5


def test_initialization_custom_budgets(tmp_path: Path) -> None:
    """Test initialization with custom budget parameters."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(
        db_path=db_path,
        per_cycle_budget_dollars=2.5,
        daily_budget_dollars=20.0,
        stall_threshold_cycles=10,
    )

    assert tracker.per_cycle_budget_dollars == 2.5
    assert tracker.daily_budget_dollars == 20.0
    assert tracker.stall_threshold_cycles == 10


def test_initialization_stall_threshold_minimum(tmp_path: Path) -> None:
    """Test that stall threshold is clamped to minimum of 1."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(
        db_path=db_path,
        stall_threshold_cycles=0,
    )

    assert tracker.stall_threshold_cycles == 1


def test_can_start_cycle_within_budget(tmp_path: Path) -> None:
    """Test can_start_cycle returns True when within budget."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(
        db_path=db_path,
        per_cycle_budget_dollars=1.0,
        daily_budget_dollars=10.0,
    )

    can_start, message = tracker.can_start_cycle(estimated_cycle_cost=0.5)

    assert can_start is True
    assert message == "ok"


def test_can_start_cycle_exceeds_per_cycle_budget(tmp_path: Path) -> None:
    """Test can_start_cycle returns False when exceeding per-cycle budget."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(
        db_path=db_path,
        per_cycle_budget_dollars=1.0,
        daily_budget_dollars=10.0,
    )

    can_start, message = tracker.can_start_cycle(estimated_cycle_cost=1.5)

    assert can_start is False
    assert "Per-cycle budget exceeded" in message
    assert "$1.5" in message
    assert "$1.0" in message


def test_can_start_cycle_exceeds_daily_budget(tmp_path: Path) -> None:
    """Test can_start_cycle returns False when exceeding daily budget."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(
        db_path=db_path,
        per_cycle_budget_dollars=2.0,  # Increased so it doesn't fail per-cycle check first
        daily_budget_dollars=5.0,
    )

    # Record cycles totaling 4.0
    tracker.record_cycle("cycle1", spent_dollars=2.0, improvement_delta=0.1)
    tracker.record_cycle("cycle2", spent_dollars=2.0, improvement_delta=0.2)

    # Try to start a cycle that would exceed daily budget (but not per-cycle)
    can_start, message = tracker.can_start_cycle(estimated_cycle_cost=1.5)

    assert can_start is False
    assert "Daily budget exceeded" in message
    assert "$5.5" in message  # 4.0 + 1.5
    assert "$5.0" in message


def test_can_start_cycle_at_exact_daily_budget(tmp_path: Path) -> None:
    """Test can_start_cycle when exactly at daily budget."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(
        db_path=db_path,
        per_cycle_budget_dollars=1.0,
        daily_budget_dollars=5.0,
    )

    tracker.record_cycle("cycle1", spent_dollars=4.0, improvement_delta=0.1)

    can_start, message = tracker.can_start_cycle(estimated_cycle_cost=1.0)

    assert can_start is True
    assert message == "ok"


def test_record_cycle_persists_and_returns_correct_record(tmp_path: Path) -> None:
    """Test record_cycle persists data and returns the correct record."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(db_path=db_path)

    before_time = time.time()
    record = tracker.record_cycle(
        cycle_id="test_cycle_1",
        spent_dollars=0.75,
        improvement_delta=0.15,
    )
    after_time = time.time()

    assert isinstance(record, CycleCostRecord)
    assert record.cycle_id == "test_cycle_1"
    assert record.spent_dollars == 0.75
    assert record.improvement_delta == 0.15
    assert before_time <= record.timestamp <= after_time
    assert record.date_utc == tracker._today_utc()


def test_record_cycle_rounds_floats(tmp_path: Path) -> None:
    """Test record_cycle rounds floats to 6 decimal places."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(db_path=db_path)

    record = tracker.record_cycle(
        cycle_id="test_cycle_2",
        spent_dollars=0.1234567890,
        improvement_delta=0.9876543210,
    )

    assert record.spent_dollars == 0.123457
    assert record.improvement_delta == 0.987654


def test_record_cycle_replaces_existing(tmp_path: Path) -> None:
    """Test record_cycle replaces existing record with same cycle_id."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(db_path=db_path)

    tracker.record_cycle("cycle1", spent_dollars=1.0, improvement_delta=0.1)
    record2 = tracker.record_cycle("cycle1", spent_dollars=2.0, improvement_delta=0.2)

    recent = tracker.recent_cycles(limit=10)

    assert len(recent) == 1
    assert recent[0]["cycle_id"] == "cycle1"
    assert recent[0]["spent_dollars"] == 2.0
    assert recent[0]["improvement_delta"] == 0.2


def test_summary_empty_database(tmp_path: Path) -> None:
    """Test summary returns zeros when no data exists."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(db_path=db_path)

    summary = tracker.summary()

    assert summary["total_spend"] == 0.0
    assert summary["total_improvement"] == 0.0
    assert summary["cost_per_improvement"] == 0.0
    assert summary["today_spend"] == 0.0


def test_summary_total_spend(tmp_path: Path) -> None:
    """Test summary calculates total spend correctly."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(db_path=db_path)

    tracker.record_cycle("cycle1", spent_dollars=1.5, improvement_delta=0.1)
    tracker.record_cycle("cycle2", spent_dollars=2.5, improvement_delta=0.2)
    tracker.record_cycle("cycle3", spent_dollars=3.0, improvement_delta=0.3)

    summary = tracker.summary()

    assert summary["total_spend"] == 7.0


def test_summary_today_spend(tmp_path: Path) -> None:
    """Test summary returns today's spend correctly."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(db_path=db_path)

    tracker.record_cycle("cycle1", spent_dollars=1.5, improvement_delta=0.1)
    tracker.record_cycle("cycle2", spent_dollars=2.5, improvement_delta=0.2)

    summary = tracker.summary()

    assert summary["today_spend"] == 4.0


def test_summary_cost_per_improvement(tmp_path: Path) -> None:
    """Test summary calculates cost per improvement correctly."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(db_path=db_path)

    tracker.record_cycle("cycle1", spent_dollars=2.0, improvement_delta=0.5)
    tracker.record_cycle("cycle2", spent_dollars=4.0, improvement_delta=1.5)

    summary = tracker.summary()

    # Total spend: 6.0, Total improvement: 2.0 (0.5 + 1.5)
    assert summary["total_spend"] == 6.0
    assert summary["total_improvement"] == 2.0
    assert summary["cost_per_improvement"] == 3.0


def test_summary_cost_per_improvement_ignores_negative_deltas(tmp_path: Path) -> None:
    """Test summary only counts positive improvement_delta for cost_per_improvement."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(db_path=db_path)

    tracker.record_cycle("cycle1", spent_dollars=2.0, improvement_delta=0.5)
    tracker.record_cycle("cycle2", spent_dollars=3.0, improvement_delta=-0.2)
    tracker.record_cycle("cycle3", spent_dollars=1.0, improvement_delta=0.0)

    summary = tracker.summary()

    # Total spend: 6.0, Total improvement: 0.5 (only positive)
    assert summary["total_spend"] == 6.0
    assert summary["total_improvement"] == 0.5
    assert summary["cost_per_improvement"] == 12.0


def test_summary_cost_per_improvement_zero_improvement(tmp_path: Path) -> None:
    """Test summary returns 0 for cost_per_improvement when total_improvement is 0."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(db_path=db_path)

    tracker.record_cycle("cycle1", spent_dollars=2.0, improvement_delta=-0.1)
    tracker.record_cycle("cycle2", spent_dollars=3.0, improvement_delta=0.0)

    summary = tracker.summary()

    assert summary["total_spend"] == 5.0
    assert summary["total_improvement"] == 0.0
    assert summary["cost_per_improvement"] == 0.0


def test_recent_cycles_empty_database(tmp_path: Path) -> None:
    """Test recent_cycles returns empty list when no data exists."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(db_path=db_path)

    recent = tracker.recent_cycles(limit=10)

    assert recent == []


def test_recent_cycles_ordering(tmp_path: Path) -> None:
    """Test recent_cycles returns records in chronological order (oldest first)."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(db_path=db_path)

    # Add cycles with slight delays to ensure different timestamps
    tracker.record_cycle("cycle1", spent_dollars=1.0, improvement_delta=0.1)
    time.sleep(0.01)
    tracker.record_cycle("cycle2", spent_dollars=2.0, improvement_delta=0.2)
    time.sleep(0.01)
    tracker.record_cycle("cycle3", spent_dollars=3.0, improvement_delta=0.3)

    recent = tracker.recent_cycles(limit=10)

    assert len(recent) == 3
    assert recent[0]["cycle_id"] == "cycle1"
    assert recent[1]["cycle_id"] == "cycle2"
    assert recent[2]["cycle_id"] == "cycle3"
    # Verify timestamps are in ascending order
    assert recent[0]["timestamp"] < recent[1]["timestamp"] < recent[2]["timestamp"]


def test_recent_cycles_limit(tmp_path: Path) -> None:
    """Test recent_cycles respects the limit parameter."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(db_path=db_path)

    # Add 10 cycles
    for i in range(10):
        tracker.record_cycle(f"cycle{i}", spent_dollars=1.0, improvement_delta=0.1)
        time.sleep(0.001)

    recent = tracker.recent_cycles(limit=5)

    assert len(recent) == 5
    # Should get the 5 most recent (cycle5 through cycle9)
    assert recent[0]["cycle_id"] == "cycle5"
    assert recent[4]["cycle_id"] == "cycle9"


def test_recent_cycles_limit_minimum_one(tmp_path: Path) -> None:
    """Test recent_cycles clamps limit to minimum of 1."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(db_path=db_path)

    tracker.record_cycle("cycle1", spent_dollars=1.0, improvement_delta=0.1)
    tracker.record_cycle("cycle2", spent_dollars=2.0, improvement_delta=0.2)

    recent = tracker.recent_cycles(limit=0)

    assert len(recent) == 1
    assert recent[0]["cycle_id"] == "cycle2"


def test_recent_cycles_structure(tmp_path: Path) -> None:
    """Test recent_cycles returns correctly structured dictionaries."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(db_path=db_path)

    tracker.record_cycle("cycle1", spent_dollars=1.5, improvement_delta=0.25)

    recent = tracker.recent_cycles(limit=1)

    assert len(recent) == 1
    record = recent[0]
    assert "cycle_id" in record
    assert "timestamp" in record
    assert "date_utc" in record
    assert "spent_dollars" in record
    assert "improvement_delta" in record
    assert record["cycle_id"] == "cycle1"
    assert record["spent_dollars"] == 1.5
    assert record["improvement_delta"] == 0.25


def test_should_pause_for_stall_insufficient_data(tmp_path: Path) -> None:
    """Test should_pause_for_stall returns False when insufficient data."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(
        db_path=db_path,
        stall_threshold_cycles=5,
    )

    # Add fewer cycles than threshold
    tracker.record_cycle("cycle1", spent_dollars=1.0, improvement_delta=0.0)
    tracker.record_cycle("cycle2", spent_dollars=1.0, improvement_delta=0.0)
    tracker.record_cycle("cycle3", spent_dollars=1.0, improvement_delta=0.0)

    should_pause = tracker.should_pause_for_stall()

    assert should_pause is False


def test_should_pause_for_stall_no_stall_when_improvements_exist(tmp_path: Path) -> None:
    """Test should_pause_for_stall returns False when improvements exist."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(
        db_path=db_path,
        stall_threshold_cycles=5,
    )

    # Add 5 cycles with at least one positive improvement
    tracker.record_cycle("cycle1", spent_dollars=1.0, improvement_delta=0.0)
    tracker.record_cycle("cycle2", spent_dollars=1.0, improvement_delta=0.0)
    tracker.record_cycle("cycle3", spent_dollars=1.0, improvement_delta=0.1)
    tracker.record_cycle("cycle4", spent_dollars=1.0, improvement_delta=0.0)
    tracker.record_cycle("cycle5", spent_dollars=1.0, improvement_delta=-0.05)

    should_pause = tracker.should_pause_for_stall()

    assert should_pause is False


def test_should_pause_for_stall_all_deltas_zero_or_negative(tmp_path: Path) -> None:
    """Test should_pause_for_stall returns True when all recent deltas <= 0."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(
        db_path=db_path,
        stall_threshold_cycles=5,
    )

    # Add 5 cycles with all improvements <= 0
    tracker.record_cycle("cycle1", spent_dollars=1.0, improvement_delta=0.0)
    tracker.record_cycle("cycle2", spent_dollars=1.0, improvement_delta=-0.1)
    tracker.record_cycle("cycle3", spent_dollars=1.0, improvement_delta=0.0)
    tracker.record_cycle("cycle4", spent_dollars=1.0, improvement_delta=-0.05)
    tracker.record_cycle("cycle5", spent_dollars=1.0, improvement_delta=0.0)

    should_pause = tracker.should_pause_for_stall()

    assert should_pause is True


def test_should_pause_for_stall_only_checks_recent_cycles(tmp_path: Path) -> None:
    """Test should_pause_for_stall only examines the N most recent cycles."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(
        db_path=db_path,
        stall_threshold_cycles=3,
    )

    # Add older cycles with positive improvements
    tracker.record_cycle("old1", spent_dollars=1.0, improvement_delta=0.5)
    time.sleep(0.01)
    tracker.record_cycle("old2", spent_dollars=1.0, improvement_delta=0.3)
    time.sleep(0.01)

    # Add 3 recent cycles with no improvements
    tracker.record_cycle("recent1", spent_dollars=1.0, improvement_delta=0.0)
    time.sleep(0.01)
    tracker.record_cycle("recent2", spent_dollars=1.0, improvement_delta=-0.1)
    time.sleep(0.01)
    tracker.record_cycle("recent3", spent_dollars=1.0, improvement_delta=0.0)

    should_pause = tracker.should_pause_for_stall()

    # Should return True because the 3 most recent cycles have no improvements
    assert should_pause is True


def test_multiple_cycles_accumulate_correctly(tmp_path: Path) -> None:
    """Test that multiple cycles accumulate spend and improvements correctly."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(
        db_path=db_path,
        per_cycle_budget_dollars=2.0,
        daily_budget_dollars=20.0,
    )

    # Record multiple cycles
    tracker.record_cycle("cycle1", spent_dollars=1.5, improvement_delta=0.2)
    time.sleep(0.01)
    tracker.record_cycle("cycle2", spent_dollars=1.8, improvement_delta=0.3)
    time.sleep(0.01)
    tracker.record_cycle("cycle3", spent_dollars=1.2, improvement_delta=-0.1)
    time.sleep(0.01)
    tracker.record_cycle("cycle4", spent_dollars=1.0, improvement_delta=0.15)

    # Verify summary
    summary = tracker.summary()
    assert summary["total_spend"] == 5.5
    assert summary["total_improvement"] == 0.65  # 0.2 + 0.3 + 0.15 (ignoring -0.1)
    assert summary["today_spend"] == 5.5

    # Verify recent cycles
    recent = tracker.recent_cycles(limit=10)
    assert len(recent) == 4
    assert recent[0]["cycle_id"] == "cycle1"
    assert recent[3]["cycle_id"] == "cycle4"

    # Verify budget check with accumulated spend
    can_start, _ = tracker.can_start_cycle(estimated_cycle_cost=1.5)
    assert can_start is True  # 5.5 + 1.5 = 7.0 < 20.0

    # Test per-cycle budget exceeded
    can_start, message = tracker.can_start_cycle(estimated_cycle_cost=2.5)
    assert can_start is False  # 2.5 > 2.0 per_cycle_budget
    assert "Per-cycle budget exceeded" in message


def test_multiple_cycles_budget_edge_cases(tmp_path: Path) -> None:
    """Test edge cases with multiple cycles and budget limits."""
    db_path = str(tmp_path / "cost_tracker.db")
    tracker = CostTracker(
        db_path=db_path,
        per_cycle_budget_dollars=1.0,
        daily_budget_dollars=5.0,
    )

    # Record cycles up to just under daily budget
    tracker.record_cycle("cycle1", spent_dollars=0.9, improvement_delta=0.1)
    tracker.record_cycle("cycle2", spent_dollars=0.9, improvement_delta=0.2)
    tracker.record_cycle("cycle3", spent_dollars=0.9, improvement_delta=0.3)
    tracker.record_cycle("cycle4", spent_dollars=0.9, improvement_delta=0.4)

    # Total: 3.6, remaining: 1.4
    summary = tracker.summary()
    assert summary["today_spend"] == 3.6

    # Can start a cycle within per-cycle budget and remaining daily budget
    can_start, _ = tracker.can_start_cycle(estimated_cycle_cost=1.0)
    assert can_start is True

    # Cannot start a cycle that fits per-cycle but exceeds daily
    can_start, message = tracker.can_start_cycle(estimated_cycle_cost=1.0)
    # Actually this should still be True since 3.6 + 1.0 = 4.6 < 5.0
    assert can_start is True

    # Now add one more cycle to get close to limit
    tracker.record_cycle("cycle5", spent_dollars=1.0, improvement_delta=0.5)
    # Total: 4.6, remaining: 0.4

    # Cannot start a 1.0 cycle anymore
    can_start, message = tracker.can_start_cycle(estimated_cycle_cost=1.0)
    assert can_start is False
    assert "Daily budget exceeded" in message

    # But can start a 0.4 cycle
    can_start, _ = tracker.can_start_cycle(estimated_cycle_cost=0.4)
    assert can_start is True

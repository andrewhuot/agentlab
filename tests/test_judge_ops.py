"""Tests for Judge Ops: versioning, drift monitoring, and human feedback."""

from __future__ import annotations



from judges.drift_monitor import DriftAlert, DriftMonitor
from judges.human_feedback import HumanFeedback, HumanFeedbackStore
from judges.versioning import GraderVersion, GraderVersionStore


# ---------------------------------------------------------------------------
# GraderVersion dataclass tests
# ---------------------------------------------------------------------------


def test_grader_version_creation():
    v = GraderVersion(
        version_id="v1",
        grader_id="grader-a",
        version=1,
        config={"rubric": "Be concise", "model": "gpt-4"},
        created_at=1000.0,
    )
    assert v.version_id == "v1"
    assert v.grader_id == "grader-a"
    assert v.version == 1
    assert v.config["rubric"] == "Be concise"
    assert v.parent_version_id is None
    assert v.metadata == {}


def test_grader_version_to_dict():
    v = GraderVersion(
        version_id="v1",
        grader_id="grader-a",
        version=1,
        config={"rubric": "Be concise"},
        created_at=1000.0,
        parent_version_id=None,
        metadata={"author": "alice"},
    )
    d = v.to_dict()
    assert d["version_id"] == "v1"
    assert d["config"] == {"rubric": "Be concise"}
    assert d["metadata"] == {"author": "alice"}


def test_grader_version_from_dict():
    d = {
        "version_id": "v2",
        "grader_id": "grader-a",
        "version": 2,
        "config": {"rubric": "Be detailed"},
        "created_at": 2000.0,
        "parent_version_id": "v1",
        "metadata": {},
    }
    v = GraderVersion.from_dict(d)
    assert v.version_id == "v2"
    assert v.parent_version_id == "v1"
    assert v.version == 2


def test_grader_version_round_trip():
    original = GraderVersion(
        version_id="v3",
        grader_id="grader-b",
        version=3,
        config={"temperature": 0.7, "model": "claude"},
        created_at=3000.0,
        parent_version_id="v2",
        metadata={"notes": "tuned temp"},
    )
    rebuilt = GraderVersion.from_dict(original.to_dict())
    assert rebuilt.version_id == original.version_id
    assert rebuilt.config == original.config
    assert rebuilt.parent_version_id == original.parent_version_id
    assert rebuilt.metadata == original.metadata


# ---------------------------------------------------------------------------
# GraderVersionStore tests
# ---------------------------------------------------------------------------


def test_version_store_save_and_get(tmp_path):
    db = str(tmp_path / "versions.db")
    store = GraderVersionStore(db_path=db)
    v = GraderVersion(
        version_id="v1", grader_id="g1", version=1,
        config={"rubric": "test"}, created_at=100.0,
    )
    store.save_version(v)
    loaded = store.get_version("v1")
    assert loaded is not None
    assert loaded.grader_id == "g1"
    assert loaded.config == {"rubric": "test"}


def test_version_store_get_missing(tmp_path):
    db = str(tmp_path / "versions.db")
    store = GraderVersionStore(db_path=db)
    assert store.get_version("nonexistent") is None


def test_version_store_list_versions(tmp_path):
    db = str(tmp_path / "versions.db")
    store = GraderVersionStore(db_path=db)
    for i in range(1, 4):
        store.save_version(GraderVersion(
            version_id=f"v{i}", grader_id="g1", version=i,
            config={"v": i}, created_at=float(i * 100),
        ))
    # Add a version for a different grader
    store.save_version(GraderVersion(
        version_id="other", grader_id="g2", version=1,
        config={}, created_at=500.0,
    ))
    versions = store.list_versions("g1")
    assert len(versions) == 3
    assert [v.version for v in versions] == [1, 2, 3]


def test_version_store_get_latest(tmp_path):
    db = str(tmp_path / "versions.db")
    store = GraderVersionStore(db_path=db)
    store.save_version(GraderVersion(
        version_id="v1", grader_id="g1", version=1, config={"a": 1},
    ))
    store.save_version(GraderVersion(
        version_id="v2", grader_id="g1", version=2, config={"a": 2},
    ))
    latest = store.get_latest("g1")
    assert latest is not None
    assert latest.version == 2
    assert latest.config == {"a": 2}


def test_version_store_get_latest_empty(tmp_path):
    db = str(tmp_path / "versions.db")
    store = GraderVersionStore(db_path=db)
    assert store.get_latest("nonexistent") is None


def test_version_store_diff_versions(tmp_path):
    db = str(tmp_path / "versions.db")
    store = GraderVersionStore(db_path=db)
    store.save_version(GraderVersion(
        version_id="v1", grader_id="g1", version=1,
        config={"rubric": "old", "temperature": 0.5, "removed_key": "gone"},
    ))
    store.save_version(GraderVersion(
        version_id="v2", grader_id="g1", version=2,
        config={"rubric": "new", "temperature": 0.5, "new_key": "added"},
    ))
    diff = store.diff_versions("v1", "v2")
    assert diff["added"] == {"new_key": "added"}
    assert diff["removed"] == {"removed_key": "gone"}
    assert diff["changed"] == {"rubric": {"old": "old", "new": "new"}}


def test_version_store_diff_missing_version(tmp_path):
    db = str(tmp_path / "versions.db")
    store = GraderVersionStore(db_path=db)
    diff = store.diff_versions("missing_a", "missing_b")
    assert diff == {"added": {}, "removed": {}, "changed": {}}


# ---------------------------------------------------------------------------
# DriftAlert dataclass tests
# ---------------------------------------------------------------------------


def test_drift_alert_creation():
    alert = DriftAlert(
        alert_id="abc123",
        grader_id="g1",
        alert_type="agreement_drift",
        severity=0.5,
        window_start=100.0,
        window_end=200.0,
        details={"drift": 0.3},
    )
    assert alert.alert_type == "agreement_drift"
    assert alert.severity == 0.5


def test_drift_alert_to_dict():
    alert = DriftAlert(
        alert_id="abc123",
        grader_id="g1",
        alert_type="position_bias",
        severity=0.3,
        window_start=100.0,
        window_end=200.0,
        created_at=300.0,
    )
    d = alert.to_dict()
    assert d["alert_id"] == "abc123"
    assert d["alert_type"] == "position_bias"
    assert d["created_at"] == 300.0


# ---------------------------------------------------------------------------
# DriftMonitor tests
# ---------------------------------------------------------------------------


def test_drift_monitor_agreement_no_drift():
    monitor = DriftMonitor()
    # 100 verdicts all agreeing
    verdicts = [{"score": 0.8, "expected": 0.8, "grader_id": "g1"} for _ in range(100)]
    alert = monitor.check_agreement_drift(verdicts, window_size=50)
    assert alert is None


def test_drift_monitor_agreement_with_drift():
    monitor = DriftMonitor()
    # First 50: agree
    historical = [{"score": 0.8, "expected": 0.8, "grader_id": "g1"} for _ in range(50)]
    # Last 50: disagree
    recent = [{"score": 0.9, "expected": 0.3, "grader_id": "g1"} for _ in range(50)]
    verdicts = historical + recent
    alert = monitor.check_agreement_drift(verdicts, window_size=50)
    assert alert is not None
    assert alert.alert_type == "agreement_drift"
    assert alert.severity > 0.1


def test_drift_monitor_agreement_too_few_verdicts():
    monitor = DriftMonitor()
    verdicts = [{"score": 0.8, "expected": 0.8} for _ in range(10)]
    alert = monitor.check_agreement_drift(verdicts, window_size=50)
    assert alert is None


def test_drift_monitor_position_bias_detected():
    monitor = DriftMonitor()
    # Large difference when order swaps
    verdicts_ab = [(0.9, 0.3), (0.85, 0.4), (0.8, 0.35)]
    alert = monitor.check_position_bias(verdicts_ab, threshold=0.1)
    assert alert is not None
    assert alert.alert_type == "position_bias"
    assert alert.severity > 0.1


def test_drift_monitor_position_bias_none():
    monitor = DriftMonitor()
    # Minimal difference
    verdicts_ab = [(0.8, 0.82), (0.7, 0.71), (0.9, 0.89)]
    alert = monitor.check_position_bias(verdicts_ab, threshold=0.1)
    assert alert is None


def test_drift_monitor_position_bias_empty():
    monitor = DriftMonitor()
    assert monitor.check_position_bias([]) is None


def test_drift_monitor_verbosity_bias_detected():
    monitor = DriftMonitor()
    short = [0.4, 0.5, 0.45, 0.42]
    long = [0.8, 0.85, 0.9, 0.82]
    alert = monitor.check_verbosity_bias(short, long, threshold=0.1)
    assert alert is not None
    assert alert.alert_type == "verbosity_bias"
    assert alert.details["bias"] > 0


def test_drift_monitor_verbosity_bias_none():
    monitor = DriftMonitor()
    short = [0.8, 0.82, 0.79]
    long = [0.81, 0.83, 0.80]
    alert = monitor.check_verbosity_bias(short, long, threshold=0.1)
    assert alert is None


def test_drift_monitor_verbosity_bias_empty():
    monitor = DriftMonitor()
    assert monitor.check_verbosity_bias([], [0.5]) is None
    assert monitor.check_verbosity_bias([0.5], []) is None


def test_drift_monitor_run_all_checks_no_alerts():
    monitor = DriftMonitor()
    verdicts = [{"score": 0.8, "expected": 0.8, "grader_id": "g1"} for _ in range(100)]
    alerts = monitor.run_all_checks(verdicts)
    assert alerts == []


def test_drift_monitor_run_all_checks_multiple_alerts():
    monitor = DriftMonitor()
    # Drift in agreement
    historical = [{"score": 0.8, "expected": 0.8, "grader_id": "g1"} for _ in range(50)]
    recent = [{"score": 0.9, "expected": 0.3, "grader_id": "g1"} for _ in range(50)]
    verdicts = historical + recent
    # Position bias
    verdicts_ab = [(0.9, 0.3), (0.85, 0.4)]
    # Verbosity bias
    short = [0.3, 0.35]
    long = [0.9, 0.85]

    alerts = monitor.run_all_checks(verdicts, verdicts_ab, short, long)
    alert_types = {a.alert_type for a in alerts}
    assert "agreement_drift" in alert_types
    assert "position_bias" in alert_types
    assert "verbosity_bias" in alert_types


# ---------------------------------------------------------------------------
# HumanFeedback dataclass tests
# ---------------------------------------------------------------------------


def test_human_feedback_creation():
    fb = HumanFeedback(
        feedback_id="fb1",
        case_id="case-1",
        judge_id="j1",
        judge_score=0.8,
        human_score=0.7,
        human_notes="Close but rubric unclear",
        created_at=1000.0,
    )
    assert fb.feedback_id == "fb1"
    assert fb.human_notes == "Close but rubric unclear"


def test_human_feedback_to_dict():
    fb = HumanFeedback(
        feedback_id="fb1", case_id="c1", judge_id="j1",
        judge_score=0.9, human_score=0.5, created_at=100.0,
    )
    d = fb.to_dict()
    assert d["judge_score"] == 0.9
    assert d["human_score"] == 0.5


def test_human_feedback_from_dict():
    d = {
        "feedback_id": "fb2",
        "case_id": "c2",
        "judge_id": "j1",
        "judge_score": 0.6,
        "human_score": 0.8,
        "human_notes": "Judge too harsh",
        "created_at": 200.0,
    }
    fb = HumanFeedback.from_dict(d)
    assert fb.feedback_id == "fb2"
    assert fb.human_notes == "Judge too harsh"


def test_human_feedback_round_trip():
    original = HumanFeedback(
        feedback_id="fb3", case_id="c3", judge_id="j2",
        judge_score=0.75, human_score=0.80,
        human_notes="Slightly lenient", created_at=300.0,
    )
    rebuilt = HumanFeedback.from_dict(original.to_dict())
    assert rebuilt.feedback_id == original.feedback_id
    assert rebuilt.judge_score == original.judge_score
    assert rebuilt.human_notes == original.human_notes


# ---------------------------------------------------------------------------
# HumanFeedbackStore tests
# ---------------------------------------------------------------------------


def _make_feedback(idx: int, judge_id: str = "j1", gap: float = 0.0) -> HumanFeedback:
    """Helper to create feedback with a controlled judge-human gap."""
    return HumanFeedback(
        feedback_id=f"fb{idx}",
        case_id=f"case-{idx}",
        judge_id=judge_id,
        judge_score=0.8,
        human_score=0.8 - gap,
        human_notes=f"note-{idx}",
        created_at=float(idx),
    )


def test_feedback_store_record_and_get(tmp_path):
    db = str(tmp_path / "feedback.db")
    store = HumanFeedbackStore(db_path=db)
    fb = _make_feedback(1)
    store.record(fb)
    loaded = store.get_feedback("fb1")
    assert loaded is not None
    assert loaded.case_id == "case-1"


def test_feedback_store_get_missing(tmp_path):
    db = str(tmp_path / "feedback.db")
    store = HumanFeedbackStore(db_path=db)
    assert store.get_feedback("nonexistent") is None


def test_feedback_store_list_all(tmp_path):
    db = str(tmp_path / "feedback.db")
    store = HumanFeedbackStore(db_path=db)
    for i in range(5):
        store.record(_make_feedback(i))
    results = store.list_feedback()
    assert len(results) == 5


def test_feedback_store_list_by_judge(tmp_path):
    db = str(tmp_path / "feedback.db")
    store = HumanFeedbackStore(db_path=db)
    for i in range(3):
        store.record(_make_feedback(i, judge_id="j1"))
    for i in range(3, 6):
        store.record(_make_feedback(i, judge_id="j2"))
    results = store.list_feedback(judge_id="j1")
    assert len(results) == 3
    assert all(r.judge_id == "j1" for r in results)


def test_feedback_store_agreement_rate_high(tmp_path):
    db = str(tmp_path / "feedback.db")
    store = HumanFeedbackStore(db_path=db)
    # All within threshold (gap=0.1 <= 0.2 threshold)
    for i in range(10):
        store.record(_make_feedback(i, gap=0.1))
    rate = store.agreement_rate(threshold=0.2)
    assert rate == 1.0


def test_feedback_store_agreement_rate_low(tmp_path):
    db = str(tmp_path / "feedback.db")
    store = HumanFeedbackStore(db_path=db)
    # All outside threshold (gap=0.5 > 0.2 threshold)
    for i in range(10):
        store.record(_make_feedback(i, gap=0.5))
    rate = store.agreement_rate(threshold=0.2)
    assert rate == 0.0


def test_feedback_store_agreement_rate_empty(tmp_path):
    db = str(tmp_path / "feedback.db")
    store = HumanFeedbackStore(db_path=db)
    assert store.agreement_rate() == 0.0


def test_feedback_store_disagreements(tmp_path):
    db = str(tmp_path / "feedback.db")
    store = HumanFeedbackStore(db_path=db)
    # Varying gaps
    store.record(HumanFeedback(
        feedback_id="close", case_id="c1", judge_id="j1",
        judge_score=0.8, human_score=0.78, created_at=1.0,
    ))
    store.record(HumanFeedback(
        feedback_id="far", case_id="c2", judge_id="j1",
        judge_score=0.9, human_score=0.2, created_at=2.0,
    ))
    store.record(HumanFeedback(
        feedback_id="medium", case_id="c3", judge_id="j1",
        judge_score=0.7, human_score=0.4, created_at=3.0,
    ))
    results = store.disagreements(limit=3)
    # Should be sorted: far (0.7), medium (0.3), close (0.02)
    assert results[0].feedback_id == "far"
    assert results[1].feedback_id == "medium"
    assert results[2].feedback_id == "close"


def test_feedback_store_sample_for_review(tmp_path):
    db = str(tmp_path / "feedback.db")
    store = HumanFeedbackStore(db_path=db)
    for i in range(100):
        store.record(_make_feedback(i))
    sample = store.sample_for_review(n=10)
    assert len(sample) == 10
    # All are valid HumanFeedback objects
    assert all(isinstance(s, HumanFeedback) for s in sample)


def test_feedback_store_sample_fewer_than_n(tmp_path):
    db = str(tmp_path / "feedback.db")
    store = HumanFeedbackStore(db_path=db)
    for i in range(3):
        store.record(_make_feedback(i))
    sample = store.sample_for_review(n=50)
    assert len(sample) == 3

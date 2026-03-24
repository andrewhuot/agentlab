"""Tests for optimizer/holdout.py — holdout rotation and drift detection."""

from __future__ import annotations

import pytest

from optimizer.holdout import HoldoutConfig, HoldoutManager, HoldoutSplit


# ---------------------------------------------------------------------------
# create_split
# ---------------------------------------------------------------------------


class TestCreateSplit:
    """Tests for HoldoutManager.create_split."""

    def _make_case_ids(self, n: int = 100) -> list[str]:
        return [f"case_{i:04d}" for i in range(n)]

    def test_split_proportions(self) -> None:
        """Split should produce roughly 60/20/20 proportions."""
        mgr = HoldoutManager()
        ids = self._make_case_ids(200)
        split = mgr.create_split(ids)

        total = len(split.tuning_case_ids) + len(split.validation_case_ids) + len(split.holdout_case_ids)
        assert total == 200

        # Allow 10% tolerance on proportions
        assert 0.50 <= len(split.tuning_case_ids) / 200 <= 0.70
        assert 0.10 <= len(split.validation_case_ids) / 200 <= 0.30
        assert 0.10 <= len(split.holdout_case_ids) / 200 <= 0.30

    def test_split_is_deterministic(self) -> None:
        """Same inputs must produce identical splits."""
        mgr = HoldoutManager()
        ids = self._make_case_ids(50)
        split_a = mgr.create_split(ids, rotation_epoch=0)
        split_b = mgr.create_split(ids, rotation_epoch=0)

        assert split_a.tuning_case_ids == split_b.tuning_case_ids
        assert split_a.validation_case_ids == split_b.validation_case_ids
        assert split_a.holdout_case_ids == split_b.holdout_case_ids

    def test_rotation_changes_split(self) -> None:
        """Different rotation epoch should produce a different assignment."""
        mgr = HoldoutManager()
        ids = self._make_case_ids(100)
        split_0 = mgr.create_split(ids, rotation_epoch=0)
        split_1 = mgr.create_split(ids, rotation_epoch=1)

        # At least one set should differ
        assert (
            split_0.tuning_case_ids != split_1.tuning_case_ids
            or split_0.validation_case_ids != split_1.validation_case_ids
            or split_0.holdout_case_ids != split_1.holdout_case_ids
        )

    def test_split_no_overlap(self) -> None:
        """Tuning, validation, and holdout must be disjoint."""
        mgr = HoldoutManager()
        ids = self._make_case_ids(80)
        split = mgr.create_split(ids)

        tuning = set(split.tuning_case_ids)
        validation = set(split.validation_case_ids)
        holdout = set(split.holdout_case_ids)

        assert tuning & validation == set()
        assert tuning & holdout == set()
        assert validation & holdout == set()
        assert tuning | validation | holdout == set(ids)

    def test_split_id_set(self) -> None:
        """Split should have a non-empty split_id."""
        mgr = HoldoutManager()
        split = mgr.create_split(["a", "b", "c"])
        assert isinstance(split.split_id, str)
        assert len(split.split_id) == 12


# ---------------------------------------------------------------------------
# should_rotate
# ---------------------------------------------------------------------------


class TestShouldRotate:
    """Tests for rotation triggering."""

    def test_triggers_at_correct_interval(self) -> None:
        config = HoldoutConfig(rotation_interval_experiments=5)
        mgr = HoldoutManager(config)

        for i in range(1, 11):
            mgr.record_experiment(0.8)
            if i % 5 == 0:
                assert mgr.should_rotate(), f"Should rotate at experiment {i}"
            else:
                assert not mgr.should_rotate(), f"Should NOT rotate at experiment {i}"

    def test_no_rotation_at_zero(self) -> None:
        mgr = HoldoutManager()
        assert not mgr.should_rotate()


# ---------------------------------------------------------------------------
# detect_drift
# ---------------------------------------------------------------------------


class TestDetectDrift:
    """Tests for baseline drift detection."""

    def test_detects_degrading_baselines(self) -> None:
        config = HoldoutConfig(drift_detection_window=3, drift_threshold=0.03)
        mgr = HoldoutManager(config)

        # Early baselines: high
        for score in [0.90, 0.89, 0.91]:
            mgr.record_experiment(score)
        # Recent baselines: low
        for score in [0.80, 0.79, 0.81]:
            mgr.record_experiment(score)

        is_drifting, drift_amount = mgr.detect_drift()
        assert is_drifting is True
        assert drift_amount > 0.03

    def test_no_drift_when_stable(self) -> None:
        config = HoldoutConfig(drift_detection_window=3, drift_threshold=0.03)
        mgr = HoldoutManager(config)

        for score in [0.85, 0.86, 0.84, 0.85, 0.86, 0.85]:
            mgr.record_experiment(score)

        is_drifting, drift_amount = mgr.detect_drift()
        assert is_drifting is False

    def test_not_enough_data_returns_no_drift(self) -> None:
        config = HoldoutConfig(drift_detection_window=5)
        mgr = HoldoutManager(config)

        # Only 3 experiments, need 10 (2 * window)
        for _ in range(3):
            mgr.record_experiment(0.8)

        is_drifting, drift_amount = mgr.detect_drift()
        assert is_drifting is False
        assert drift_amount == 0.0

    def test_should_rebaseline_delegates_to_detect_drift(self) -> None:
        config = HoldoutConfig(drift_detection_window=3, drift_threshold=0.03)
        mgr = HoldoutManager(config)

        for score in [0.90, 0.90, 0.90, 0.80, 0.80, 0.80]:
            mgr.record_experiment(score)

        assert mgr.should_rebaseline() is True


# ---------------------------------------------------------------------------
# validate_on_holdout
# ---------------------------------------------------------------------------


class TestValidateOnHoldout:
    """Tests for holdout validation (Anti-Goodhart check)."""

    def test_accepts_improvement(self) -> None:
        mgr = HoldoutManager()
        passed, msg = mgr.validate_on_holdout(holdout_score=0.85, baseline_holdout_score=0.80)
        assert passed is True
        assert "passed" in msg.lower()

    def test_accepts_small_regression_within_threshold(self) -> None:
        config = HoldoutConfig(drift_threshold=0.03)
        mgr = HoldoutManager(config)
        # Regression of 0.02, within threshold of 0.03
        passed, msg = mgr.validate_on_holdout(holdout_score=0.78, baseline_holdout_score=0.80)
        assert passed is True

    def test_rejects_large_regression(self) -> None:
        config = HoldoutConfig(drift_threshold=0.03)
        mgr = HoldoutManager(config)
        # Regression of 0.10, exceeds threshold
        passed, msg = mgr.validate_on_holdout(holdout_score=0.70, baseline_holdout_score=0.80)
        assert passed is False
        assert "regression" in msg.lower()


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------


class TestGetStatus:
    """Tests for observability status reporting."""

    def test_returns_expected_fields(self) -> None:
        mgr = HoldoutManager()
        ids = [f"c{i}" for i in range(20)]
        mgr.create_split(ids)
        mgr.record_experiment(0.85)

        status = mgr.get_status()

        assert "experiment_count" in status
        assert "current_split_id" in status
        assert "rotation_epoch" in status
        assert "should_rotate" in status
        assert "is_drifting" in status
        assert "drift_amount" in status
        assert "baseline_history_length" in status

        assert status["experiment_count"] == 1
        assert status["current_split_id"] is not None
        assert status["baseline_history_length"] == 1

    def test_status_before_any_split(self) -> None:
        mgr = HoldoutManager()
        status = mgr.get_status()
        assert status["current_split_id"] is None
        assert status["rotation_epoch"] == 0


# ---------------------------------------------------------------------------
# rotate
# ---------------------------------------------------------------------------


class TestRotate:
    """Tests for the rotate convenience method."""

    def test_rotate_increments_epoch(self) -> None:
        mgr = HoldoutManager()
        ids = [f"case_{i}" for i in range(50)]
        mgr.create_split(ids, rotation_epoch=0)
        new_split = mgr.rotate(ids)
        assert new_split.rotation_epoch == 1

    def test_rotate_without_prior_split(self) -> None:
        mgr = HoldoutManager()
        ids = [f"case_{i}" for i in range(20)]
        split = mgr.rotate(ids)
        assert split.rotation_epoch == 0


# ---------------------------------------------------------------------------
# get_current_split
# ---------------------------------------------------------------------------


class TestGetCurrentSplit:
    def test_none_before_create(self) -> None:
        mgr = HoldoutManager()
        assert mgr.get_current_split() is None

    def test_returns_latest_after_create(self) -> None:
        mgr = HoldoutManager()
        ids = ["a", "b", "c"]
        split = mgr.create_split(ids)
        assert mgr.get_current_split() is split

"""Tests for optimizer/holdout.py — JudgeVarianceEstimator."""

from __future__ import annotations

import math

import pytest

from optimizer.holdout import JudgeVarianceEstimate, JudgeVarianceEstimator


# ---------------------------------------------------------------------------
# record + estimate
# ---------------------------------------------------------------------------


class TestRecordAndEstimate:
    """Tests for recording observations and estimating variance."""

    def test_known_values(self) -> None:
        """Verify mean and variance with a simple known distribution."""
        est = JudgeVarianceEstimator()
        # Scores: 2, 4, 4, 4, 5, 5, 7, 9
        for s in [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]:
            est.record("quality", s)

        result = est.estimate("quality")
        assert result.n_observations == 8
        assert result.mean_score == pytest.approx(5.0, abs=0.01)
        # Sample variance: sum((x - 5)^2) / 7 = 32/7 ~ 4.571
        assert result.variance == pytest.approx(32.0 / 7, abs=0.01)

    def test_std_dev_property(self) -> None:
        est = JudgeVarianceEstimator()
        for s in [10.0, 20.0, 30.0]:
            est.record("latency", s)

        result = est.estimate("latency")
        assert result.std_dev == pytest.approx(math.sqrt(result.variance), abs=1e-6)

    def test_confidence_interval_width(self) -> None:
        est = JudgeVarianceEstimator()
        for s in [0.8, 0.82, 0.79, 0.81, 0.80]:
            est.record("quality", s)

        result = est.estimate("quality")
        assert result.confidence_interval_width > 0
        # CI width = 2 * 1.96 * stderr
        expected_stderr = math.sqrt(result.variance / result.n_observations)
        expected_ci = 2 * 1.96 * expected_stderr
        assert result.confidence_interval_width == pytest.approx(expected_ci, abs=1e-4)


# ---------------------------------------------------------------------------
# estimate_all
# ---------------------------------------------------------------------------


class TestEstimateAll:
    def test_covers_all_metrics(self) -> None:
        est = JudgeVarianceEstimator()
        est.record("alpha", 1.0)
        est.record("alpha", 2.0)
        est.record("beta", 3.0)
        est.record("beta", 4.0)
        est.record("gamma", 5.0)
        est.record("gamma", 6.0)

        results = est.estimate_all()
        names = [r.metric_name for r in results]
        assert names == ["alpha", "beta", "gamma"]  # sorted

    def test_empty_estimator(self) -> None:
        est = JudgeVarianceEstimator()
        assert est.estimate_all() == []


# ---------------------------------------------------------------------------
# is_score_meaningful
# ---------------------------------------------------------------------------


class TestIsScoreMeaningful:
    def test_large_delta_is_meaningful(self) -> None:
        est = JudgeVarianceEstimator()
        # Tight distribution -> small CI width
        for s in [0.80, 0.81, 0.80, 0.79, 0.80, 0.81, 0.80]:
            est.record("quality", s)

        # Large delta should be meaningful
        assert est.is_score_meaningful("quality", delta=0.10) is True

    def test_small_delta_not_meaningful(self) -> None:
        est = JudgeVarianceEstimator()
        # Wider distribution -> larger CI width
        for s in [0.50, 0.90, 0.60, 0.85, 0.55, 0.88, 0.52]:
            est.record("quality", s)

        ci = est.estimate("quality").confidence_interval_width
        # Delta smaller than CI width
        tiny_delta = ci * 0.1
        assert est.is_score_meaningful("quality", delta=tiny_delta) is False

    def test_insufficient_data_assumes_meaningful(self) -> None:
        est = JudgeVarianceEstimator()
        est.record("quality", 0.8)
        est.record("quality", 0.82)
        # Only 2 observations (< 5), should return True
        assert est.is_score_meaningful("quality", delta=0.001) is True

    def test_unknown_metric_assumes_meaningful(self) -> None:
        est = JudgeVarianceEstimator()
        assert est.is_score_meaningful("nonexistent", delta=0.001) is True


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_observations(self) -> None:
        est = JudgeVarianceEstimator()
        result = est.estimate("nonexistent")
        assert result.n_observations == 0
        assert result.mean_score == 0.0
        assert result.variance == 0.0
        assert result.std_dev == 0.0
        assert result.confidence_interval_width == 0.0

    def test_single_observation(self) -> None:
        est = JudgeVarianceEstimator()
        est.record("quality", 0.75)
        result = est.estimate("quality")
        assert result.n_observations == 1
        assert result.mean_score == 0.75
        assert result.variance == 0.0
        assert result.confidence_interval_width == 0.0

    def test_std_dev_zero_variance(self) -> None:
        result = JudgeVarianceEstimate(metric_name="test", variance=0.0)
        assert result.std_dev == 0.0


# ---------------------------------------------------------------------------
# record_batch
# ---------------------------------------------------------------------------


class TestRecordBatch:
    def test_batch_records_all_metrics(self) -> None:
        est = JudgeVarianceEstimator()
        est.record_batch({"quality": 0.8, "safety": 0.9, "latency": 100.0})
        est.record_batch({"quality": 0.82, "safety": 0.91, "latency": 95.0})

        results = est.estimate_all()
        names = [r.metric_name for r in results]
        assert "quality" in names
        assert "safety" in names
        assert "latency" in names

        quality = est.estimate("quality")
        assert quality.n_observations == 2

    def test_empty_batch(self) -> None:
        est = JudgeVarianceEstimator()
        est.record_batch({})
        assert est.estimate_all() == []

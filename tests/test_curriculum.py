"""Unit tests for curriculum learning scheduler."""

from __future__ import annotations

from dataclasses import dataclass

from optimizer.curriculum import (
    CaseHistory,
    CurriculumScheduler,
    DifficultyTier,
    FailureClusterDifficulty,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class _FakeOpportunity:
    """Minimal opportunity stub for curriculum filtering tests."""

    failure_family: str
    opportunity_id: str = "opp-1"


# ---------------------------------------------------------------------------
# Difficulty classification tests
# ---------------------------------------------------------------------------


class TestDifficultyClassification:
    def test_high_pass_rate_is_easy(self) -> None:
        scheduler = CurriculumScheduler()
        assert scheduler.classify_difficulty("fam", 0.80) == DifficultyTier.easy

    def test_boundary_easy(self) -> None:
        scheduler = CurriculumScheduler()
        assert scheduler.classify_difficulty("fam", 0.50) == DifficultyTier.easy

    def test_medium_pass_rate(self) -> None:
        scheduler = CurriculumScheduler()
        assert scheduler.classify_difficulty("fam", 0.30) == DifficultyTier.medium

    def test_boundary_medium(self) -> None:
        scheduler = CurriculumScheduler()
        assert scheduler.classify_difficulty("fam", 0.25) == DifficultyTier.medium

    def test_low_pass_rate_is_hard(self) -> None:
        scheduler = CurriculumScheduler()
        assert scheduler.classify_difficulty("fam", 0.10) == DifficultyTier.hard

    def test_zero_pass_rate_is_hard(self) -> None:
        scheduler = CurriculumScheduler()
        assert scheduler.classify_difficulty("fam", 0.0) == DifficultyTier.hard


# ---------------------------------------------------------------------------
# Tier advancement tests
# ---------------------------------------------------------------------------


class TestTierAdvancement:
    def test_no_advance_before_min_experiments(self) -> None:
        scheduler = CurriculumScheduler(min_experiments_per_tier=3)
        scheduler.record_experiment(DifficultyTier.easy, 0.0)
        scheduler.record_experiment(DifficultyTier.easy, 0.0)
        # Only 2 experiments, need 3
        assert not scheduler.should_advance_tier()

    def test_advance_when_stalled(self) -> None:
        scheduler = CurriculumScheduler(
            min_experiments_per_tier=3, improvement_stall_threshold=0.01
        )
        # Record 3 experiments with negligible improvement
        scheduler.record_experiment(DifficultyTier.easy, 0.001)
        scheduler.record_experiment(DifficultyTier.easy, 0.002)
        scheduler.record_experiment(DifficultyTier.easy, 0.003)
        assert scheduler.should_advance_tier()

    def test_no_advance_when_improving(self) -> None:
        scheduler = CurriculumScheduler(
            min_experiments_per_tier=3, improvement_stall_threshold=0.01
        )
        scheduler.record_experiment(DifficultyTier.easy, 0.05)
        scheduler.record_experiment(DifficultyTier.easy, 0.10)
        scheduler.record_experiment(DifficultyTier.easy, 0.08)
        assert not scheduler.should_advance_tier()

    def test_advance_from_easy_to_medium(self) -> None:
        scheduler = CurriculumScheduler()
        assert scheduler.current_tier == DifficultyTier.easy
        new_tier = scheduler.advance_tier()
        assert new_tier == DifficultyTier.medium
        assert scheduler.current_tier == DifficultyTier.medium

    def test_advance_from_medium_to_hard(self) -> None:
        scheduler = CurriculumScheduler()
        scheduler.advance_tier()  # easy -> medium
        new_tier = scheduler.advance_tier()
        assert new_tier == DifficultyTier.hard
        assert scheduler.current_tier == DifficultyTier.hard

    def test_hard_stays_hard(self) -> None:
        scheduler = CurriculumScheduler()
        scheduler.advance_tier()  # easy -> medium
        scheduler.advance_tier()  # medium -> hard
        new_tier = scheduler.advance_tier()
        assert new_tier == DifficultyTier.hard


# ---------------------------------------------------------------------------
# Opportunity filtering tests
# ---------------------------------------------------------------------------


class TestFilterOpportunities:
    def test_easy_tier_filters_hard_opportunities(self) -> None:
        scheduler = CurriculumScheduler()
        assert scheduler.current_tier == DifficultyTier.easy

        opps = [
            _FakeOpportunity(failure_family="easy_fam"),
            _FakeOpportunity(failure_family="hard_fam"),
        ]
        pass_rates = {"easy_fam": 0.80, "hard_fam": 0.10}

        filtered = scheduler.filter_opportunities(opps, pass_rates)
        families = [o.failure_family for o in filtered]
        assert "easy_fam" in families
        assert "hard_fam" not in families

    def test_medium_tier_includes_easy_and_medium(self) -> None:
        scheduler = CurriculumScheduler()
        scheduler.advance_tier()  # easy -> medium

        opps = [
            _FakeOpportunity(failure_family="easy_fam"),
            _FakeOpportunity(failure_family="medium_fam"),
            _FakeOpportunity(failure_family="hard_fam"),
        ]
        pass_rates = {"easy_fam": 0.80, "medium_fam": 0.35, "hard_fam": 0.10}

        filtered = scheduler.filter_opportunities(opps, pass_rates)
        families = [o.failure_family for o in filtered]
        assert "easy_fam" in families
        assert "medium_fam" in families
        assert "hard_fam" not in families

    def test_hard_tier_includes_all(self) -> None:
        scheduler = CurriculumScheduler()
        scheduler.advance_tier()  # easy -> medium
        scheduler.advance_tier()  # medium -> hard

        opps = [
            _FakeOpportunity(failure_family="easy_fam"),
            _FakeOpportunity(failure_family="hard_fam"),
        ]
        pass_rates = {"easy_fam": 0.80, "hard_fam": 0.10}

        filtered = scheduler.filter_opportunities(opps, pass_rates)
        assert len(filtered) == 2

    def test_fallback_when_no_matching(self) -> None:
        scheduler = CurriculumScheduler()
        # easy tier, but all opportunities are hard
        opps = [
            _FakeOpportunity(failure_family="hard_a"),
            _FakeOpportunity(failure_family="hard_b"),
        ]
        pass_rates = {"hard_a": 0.05, "hard_b": 0.10}

        filtered = scheduler.filter_opportunities(opps, pass_rates)
        # Should fall back to returning all
        assert len(filtered) == 2

    def test_unknown_failure_family_defaults_to_medium(self) -> None:
        scheduler = CurriculumScheduler()
        # easy tier; unknown families get pass_rate 0.5 which is easy threshold
        opps = [_FakeOpportunity(failure_family="unknown_fam")]
        pass_rates = {}  # no data

        filtered = scheduler.filter_opportunities(opps, pass_rates)
        assert len(filtered) == 1  # 0.5 is >= EASY_THRESHOLD so included

    def test_auto_advance_in_filter(self) -> None:
        """filter_opportunities should auto-advance when stalled."""
        scheduler = CurriculumScheduler(
            min_experiments_per_tier=2, improvement_stall_threshold=0.01
        )
        scheduler.record_experiment(DifficultyTier.easy, 0.001)
        scheduler.record_experiment(DifficultyTier.easy, 0.002)
        assert scheduler.current_tier == DifficultyTier.easy

        opps = [
            _FakeOpportunity(failure_family="medium_fam"),
        ]
        pass_rates = {"medium_fam": 0.35}

        filtered = scheduler.filter_opportunities(opps, pass_rates)
        # Should have auto-advanced to medium, allowing medium_fam
        assert scheduler.current_tier == DifficultyTier.medium
        assert len(filtered) == 1


# ---------------------------------------------------------------------------
# Curriculum status tests
# ---------------------------------------------------------------------------


class TestCurriculumStatus:
    def test_status_reports_current_tier(self) -> None:
        scheduler = CurriculumScheduler()
        status = scheduler.get_status()
        assert status["current_tier"] == "easy"
        assert isinstance(status["experiments_per_tier"], dict)
        assert status["should_advance"] is False

    def test_status_after_experiments(self) -> None:
        scheduler = CurriculumScheduler(min_experiments_per_tier=2)
        scheduler.record_experiment(DifficultyTier.easy, 0.001)
        scheduler.record_experiment(DifficultyTier.easy, 0.001)

        status = scheduler.get_status()
        assert status["experiments_per_tier"]["easy"] == 2
        assert status["should_advance"] is True


# ---------------------------------------------------------------------------
# CaseHistory tests
# ---------------------------------------------------------------------------


class TestCaseHistory:
    def test_pass_rate_no_data(self) -> None:
        h = CaseHistory(case_id="c1")
        assert h.pass_rate == 0.5

    def test_pass_rate_with_data(self) -> None:
        h = CaseHistory(case_id="c1", total_attempts=10, total_passes=7)
        assert abs(h.pass_rate - 0.7) < 1e-9


# ---------------------------------------------------------------------------
# FailureClusterDifficulty tests
# ---------------------------------------------------------------------------


class TestFailureClusterDifficulty:
    def test_difficulty_score(self) -> None:
        d = FailureClusterDifficulty(failure_family="fam", avg_pass_rate=0.8)
        assert abs(d.difficulty_score - 0.2) < 1e-9

    def test_difficulty_score_hard(self) -> None:
        d = FailureClusterDifficulty(failure_family="fam", avg_pass_rate=0.1)
        assert abs(d.difficulty_score - 0.9) < 1e-9


# ---------------------------------------------------------------------------
# get_difficulty_estimates tests
# ---------------------------------------------------------------------------


class TestDifficultyEstimates:
    def test_returns_sorted_by_difficulty(self) -> None:
        scheduler = CurriculumScheduler()
        families = ["hard_fam", "easy_fam", "medium_fam"]
        pass_rates = {"hard_fam": 0.10, "easy_fam": 0.80, "medium_fam": 0.35}

        estimates = scheduler.get_difficulty_estimates(families, pass_rates)
        assert len(estimates) == 3
        # Sorted by difficulty_score ascending (easiest first)
        assert estimates[0].failure_family == "easy_fam"
        assert estimates[-1].failure_family == "hard_fam"

    def test_unknown_family_defaults(self) -> None:
        scheduler = CurriculumScheduler()
        estimates = scheduler.get_difficulty_estimates(["unknown"], {})
        assert len(estimates) == 1
        assert estimates[0].avg_pass_rate == 0.5
        assert estimates[0].tier == DifficultyTier.easy


# ---------------------------------------------------------------------------
# record_case_outcome tests
# ---------------------------------------------------------------------------


class TestRecordCaseOutcome:
    def test_updates_history(self) -> None:
        scheduler = CurriculumScheduler()
        scheduler.record_case_outcome("case_1", True)
        scheduler.record_case_outcome("case_1", False)
        scheduler.record_case_outcome("case_1", True)

        history = scheduler._case_history["case_1"]
        assert history.total_attempts == 3
        assert history.total_passes == 2
        assert abs(history.pass_rate - 2 / 3) < 1e-9

"""Tests for anti_goodhart.py and loop.py strategy integration."""

from __future__ import annotations

import pytest

from evals.anti_goodhart import AntiGoodhartConfig, AntiGoodhartGuard
from evals.scorer import CompositeScore, EvalResult
from observer.metrics import HealthMetrics, HealthReport
from optimizer.loop import Optimizer, StrategyDiagnostics
from optimizer.memory import OptimizationMemory
from optimizer.pareto import ConstrainedParetoArchive, ObjectiveDirection
from optimizer.proposer import Proposal
from optimizer.search import (
    BanditPolicy,
    CurriculumStage,
    HybridBanditSelector,
    HybridSearchOrchestrator,
    OperatorFamily,
    SearchBudget,
    SearchStrategy,
)


# ---------------------------------------------------------------------------
# AntiGoodhartGuard unit tests
# ---------------------------------------------------------------------------


class TestAntiGoodhartGuard:
    """Test the anti-Goodhart guardrail evaluation logic."""

    def test_passes_when_candidate_improves(self):
        guard = AntiGoodhartGuard()
        verdict = guard.evaluate_candidate(
            baseline_metrics={"composite": 0.6, "quality": 0.6, "safety": 0.8},
            candidate_metrics={"composite": 0.7, "quality": 0.7, "safety": 0.9},
        )
        assert verdict.passed is True
        assert verdict.violations == []

    def test_rejects_fixed_holdout_regression(self):
        guard = AntiGoodhartGuard()
        verdict = guard.evaluate_candidate(
            baseline_metrics={
                "composite": 0.6,
                "fixed_holdout_composite": 0.7,
            },
            candidate_metrics={
                "composite": 0.8,
                "fixed_holdout_composite": 0.5,
            },
        )
        assert verdict.passed is False
        assert any("Fixed holdout" in v for v in verdict.violations)

    def test_rejects_rolling_holdout_regression(self):
        guard = AntiGoodhartGuard()
        verdict = guard.evaluate_candidate(
            baseline_metrics={
                "composite": 0.6,
                "rolling_holdout_composite": 0.7,
            },
            candidate_metrics={
                "composite": 0.8,
                "rolling_holdout_composite": 0.5,
            },
        )
        assert verdict.passed is False
        assert any("Rolling holdout" in v for v in verdict.violations)

    def test_rejects_high_judge_variance(self):
        guard = AntiGoodhartGuard(AntiGoodhartConfig(max_judge_variance=0.01))
        verdict = guard.evaluate_candidate(
            baseline_metrics={"composite": 0.6},
            candidate_metrics={
                "composite": 0.7,
                "judge_scores": [0.1, 0.5, 0.9],
            },
        )
        assert verdict.passed is False
        assert any("Judge variance" in v for v in verdict.violations)

    def test_detects_drift_and_rebaselines(self):
        guard = AntiGoodhartGuard(AntiGoodhartConfig(drift_threshold=0.05))
        guard.observe_baseline({"composite": 1.0})
        verdict = guard.evaluate_candidate(
            baseline_metrics={"composite": 0.5},
            candidate_metrics={"composite": 0.55},
        )
        assert verdict.rebaselined is True

    def test_rotation_epoch_advances(self):
        guard = AntiGoodhartGuard(AntiGoodhartConfig(holdout_rotation_interval=2))
        for _ in range(2):
            guard.evaluate_candidate(
                baseline_metrics={"composite": 0.5},
                candidate_metrics={"composite": 0.6},
            )
        assert guard._rotation_epoch == 1

    def test_tolerance_allows_small_regression(self):
        guard = AntiGoodhartGuard(AntiGoodhartConfig(holdout_tolerance=0.1))
        verdict = guard.evaluate_candidate(
            baseline_metrics={"composite": 0.6, "fixed_holdout_composite": 0.7},
            candidate_metrics={"composite": 0.8, "fixed_holdout_composite": 0.65},
        )
        assert verdict.passed is True

    def test_proxy_variance_from_quality_safety(self):
        guard = AntiGoodhartGuard(AntiGoodhartConfig(max_judge_variance=0.0001))
        verdict = guard.evaluate_candidate(
            baseline_metrics={"composite": 0.5},
            candidate_metrics={
                "composite": 0.6,
                "quality": 0.1,
                "safety": 0.9,
                "user_satisfaction_proxy": 0.5,
            },
        )
        # Variance of [0.1, 0.9, 0.5] is high
        assert verdict.passed is False


# ---------------------------------------------------------------------------
# ConstrainedParetoArchive tests
# ---------------------------------------------------------------------------


class TestConstrainedParetoArchive:
    """Test the direction-aware Pareto archive."""

    def _make_archive(self):
        return ConstrainedParetoArchive(
            objective_directions={
                "quality": ObjectiveDirection.MAXIMIZE,
                "cost": ObjectiveDirection.MINIMIZE,
            }
        )

    def test_add_feasible_candidate(self):
        archive = self._make_archive()
        c = archive.add_candidate(
            candidate_id="a",
            objectives={"quality": 0.8, "cost": 0.3},
            constraints_passed=True,
        )
        assert c["constraints_passed"] is True
        assert len(archive.feasible_candidates) == 1

    def test_add_infeasible_candidate(self):
        archive = self._make_archive()
        archive.add_candidate(
            candidate_id="b",
            objectives={"quality": 0.5, "cost": 0.5},
            constraints_passed=False,
            constraint_violations=["safety"],
        )
        assert len(archive.infeasible_candidates) == 1

    def test_dominance_maximize(self):
        archive = ConstrainedParetoArchive(
            objective_directions={"q": ObjectiveDirection.MAXIMIZE}
        )
        a = {"objectives": {"q": 0.8}}
        b = {"objectives": {"q": 0.5}}
        assert archive.dominates(a, b) is True
        assert archive.dominates(b, a) is False

    def test_frontier_single(self):
        archive = self._make_archive()
        archive.add_candidate(
            candidate_id="x",
            objectives={"quality": 0.9, "cost": 0.1},
            constraints_passed=True,
        )
        front = archive.frontier()
        assert len(front) == 1

    def test_frontier_filters_dominated(self):
        archive = self._make_archive()
        archive.add_candidate(
            candidate_id="a",
            objectives={"quality": 0.9, "cost": 0.1},
            constraints_passed=True,
        )
        archive.add_candidate(
            candidate_id="b",
            objectives={"quality": 0.5, "cost": 0.5},
            constraints_passed=True,
        )
        front = archive.frontier()
        assert len(front) == 1
        assert front[0]["candidate_id"] == "a"

    def test_as_dict_serialization(self):
        archive = self._make_archive()
        archive.add_candidate(
            candidate_id="c",
            objectives={"quality": 0.7, "cost": 0.3},
            constraints_passed=True,
        )
        d = archive.as_dict()
        assert "frontier" in d
        assert "recommended_candidate_id" in d
        assert d["feasible_count"] == 1

    def test_knee_point_selection(self):
        archive = self._make_archive()
        archive.add_candidate(
            candidate_id="a",
            objectives={"quality": 1.0, "cost": 1.0},
            constraints_passed=True,
        )
        archive.add_candidate(
            candidate_id="b",
            objectives={"quality": 0.5, "cost": 0.0},
            constraints_passed=True,
        )
        rec = archive.recommend_knee_point()
        assert rec is not None

    def test_missing_objective_raises(self):
        archive = self._make_archive()
        with pytest.raises(ValueError, match="Missing objective"):
            archive.add_candidate(
                candidate_id="d",
                objectives={"quality": 0.5},
                constraints_passed=True,
            )


# ---------------------------------------------------------------------------
# SearchStrategy / BanditPolicy / HSO primitives
# ---------------------------------------------------------------------------


class TestSearchEnums:
    def test_search_strategy_values(self):
        assert SearchStrategy.SIMPLE.value == "simple"
        assert SearchStrategy.ADAPTIVE.value == "adaptive"
        assert SearchStrategy.FULL.value == "full"

    def test_bandit_policy_values(self):
        assert BanditPolicy.UCB.value == "ucb"
        assert BanditPolicy.THOMPSON.value == "thompson"

    def test_operator_family_values(self):
        assert OperatorFamily.MCTS_EXPLORATION.value == "mcts_exploration"
        assert OperatorFamily.LOCAL_TUNING.value == "local_tuning"
        assert OperatorFamily.DIVERSITY_INJECTION.value == "diversity_injection"


class TestHybridBanditSelector:
    def test_select_thompson(self):
        selector = HybridBanditSelector(policy=BanditPolicy.THOMPSON)
        arm = selector.select(["a", "b", "c"])
        assert arm in ("a", "b", "c")

    def test_select_ucb(self):
        selector = HybridBanditSelector(policy=BanditPolicy.UCB)
        arm = selector.select(["x", "y"])
        assert arm in ("x", "y")

    def test_record_and_exploit(self):
        selector = HybridBanditSelector(policy=BanditPolicy.THOMPSON, seed=42)
        for _ in range(20):
            selector.record("good", reward=1.0)
            selector.record("bad", reward=0.0)
        # After many observations, should prefer "good"
        picks = [selector.select(["good", "bad"]) for _ in range(10)]
        assert picks.count("good") >= 5

    def test_empty_arms_raises(self):
        selector = HybridBanditSelector()
        with pytest.raises(ValueError):
            selector.select([])


class TestCurriculumStage:
    def test_hso_advances_stage(self):
        hso = HybridSearchOrchestrator()
        assert hso.curriculum_stage == CurriculumStage.EASY
        for _ in range(3):
            hso.record_curriculum_outcome(success=True)
        assert hso.curriculum_stage == CurriculumStage.MEDIUM
        for _ in range(3):
            hso.record_curriculum_outcome(success=True)
        assert hso.curriculum_stage == CurriculumStage.HARD

    def test_failure_resets_counter(self):
        hso = HybridSearchOrchestrator()
        hso.record_curriculum_outcome(success=True)
        hso.record_curriculum_outcome(success=True)
        hso.record_curriculum_outcome(success=False)
        assert hso.curriculum_stage == CurriculumStage.EASY


# ---------------------------------------------------------------------------
# Optimizer strategy-aware constructor tests
# ---------------------------------------------------------------------------


class StubProposer:
    def __init__(self, proposal: Proposal | None):
        self.proposal = proposal

    def propose(self, **kwargs) -> Proposal | None:
        return self.proposal


class SequencedEvalRunner:
    def __init__(self, baseline: CompositeScore, candidate: CompositeScore):
        self.baseline = baseline
        self.candidate = candidate
        self.calls = 0

    def run(self, config=None, **kwargs):
        self.calls += 1
        return self.baseline if self.calls % 2 == 1 else self.candidate

    def load_cases(self):
        return []

    def run_cases(self, cases, config=None, **kwargs):
        return self.baseline


def _make_health_report(needs_optimization: bool = True) -> HealthReport:
    return HealthReport(
        metrics=HealthMetrics(
            success_rate=0.8 if not needs_optimization else 0.5,
            avg_latency_ms=100.0,
            error_rate=0.1,
            safety_violation_rate=0.0,
            avg_cost=0.01,
            total_conversations=100,
        ),
        anomalies=[],
        failure_buckets={"tool_error": 5},
        needs_optimization=needs_optimization,
        reason="test",
    )


class TestOptimizerStrategy:
    """Test that the Optimizer properly routes through simple/adaptive/full."""

    def test_simple_strategy_uses_proposer(self, tmp_path, base_config):
        improved = {**base_config, "quality_boost": True}
        proposal = Proposal(
            new_config=improved,
            change_description="Flip quality_boost",
            config_section="quality_boost",
            reasoning="Test reasoning",
        )
        baseline = CompositeScore(
            quality=0.5, safety=1.0, latency=0.8, cost=0.9, composite=0.6,
            results=[
                EvalResult(case_id="1", category="test", passed=True,
                           quality_score=0.5, safety_passed=True, latency_ms=100, token_count=50)
            ],
        )
        candidate = CompositeScore(
            quality=0.8, safety=1.0, latency=0.8, cost=0.9, composite=0.8,
            results=[
                EvalResult(case_id="1", category="test", passed=True,
                           quality_score=0.8, safety_passed=True, latency_ms=100, token_count=50)
            ],
        )
        opt = Optimizer(
            eval_runner=SequencedEvalRunner(baseline, candidate),
            memory=OptimizationMemory(db_path=str(tmp_path / "opt.db")),
            proposer=StubProposer(proposal),
            search_strategy="simple",
            require_statistical_significance=False,
        )
        new_config, msg = opt.optimize(_make_health_report(), base_config)
        assert new_config is not None
        assert "ACCEPTED" in msg

    def test_get_strategy_diagnostics(self, tmp_path, base_config):
        opt = Optimizer(
            eval_runner=SequencedEvalRunner(
                CompositeScore(composite=0.5), CompositeScore(composite=0.6)
            ),
            memory=OptimizationMemory(db_path=str(tmp_path / "opt.db")),
            search_strategy="full",
        )
        diag = opt.get_strategy_diagnostics()
        assert isinstance(diag, StrategyDiagnostics)
        assert diag.strategy == "full"

    def test_get_pareto_snapshot(self, tmp_path, base_config):
        opt = Optimizer(
            eval_runner=SequencedEvalRunner(
                CompositeScore(composite=0.5), CompositeScore(composite=0.6)
            ),
            memory=OptimizationMemory(db_path=str(tmp_path / "opt.db")),
            search_strategy="full",
        )
        snapshot = opt.get_pareto_snapshot()
        assert "frontier" in snapshot
        assert "feasible_count" in snapshot

    def test_invalid_strategy_falls_back_to_simple(self, tmp_path, base_config):
        opt = Optimizer(
            eval_runner=SequencedEvalRunner(
                CompositeScore(composite=0.5), CompositeScore(composite=0.6)
            ),
            memory=OptimizationMemory(db_path=str(tmp_path / "opt.db")),
            search_strategy="nonexistent",
        )
        assert opt.search_strategy == SearchStrategy.SIMPLE

    def test_invalid_bandit_policy_falls_back(self, tmp_path, base_config):
        opt = Optimizer(
            eval_runner=SequencedEvalRunner(
                CompositeScore(composite=0.5), CompositeScore(composite=0.6)
            ),
            memory=OptimizationMemory(db_path=str(tmp_path / "opt.db")),
            bandit_policy="nonexistent",
        )
        # Should not raise; falls back to THOMPSON


class TestSearchBudget:
    def test_defaults(self):
        b = SearchBudget()
        assert b.max_candidates == 10
        assert b.max_eval_budget == 5
        assert b.max_cost_dollars == 1.0
        assert b.time_budget_seconds == 300.0

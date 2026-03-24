"""Unit tests for the AdaptiveSearchEngine (bandit + curriculum integration)."""

from __future__ import annotations

import tempfile
import time

from observer.opportunities import OptimizationOpportunity
from optimizer.memory import OptimizationMemory
from optimizer.mutations import create_default_registry
from optimizer.proposer import Proposer
from optimizer.search import (
    AdaptiveSearchEngine,
    CandidateMutation,
    OperatorPerformanceTracker,
    SearchBudget,
    SearchEngine,
    SearchResult,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_opportunity(
    failure_family: str = "quality_degradation",
    recommended_operators: list[str] | None = None,
    severity: float = 0.6,
    prevalence: float = 0.4,
    opportunity_id: str | None = None,
) -> OptimizationOpportunity:
    return OptimizationOpportunity(
        opportunity_id=opportunity_id or "opp-test-001",
        created_at=time.time(),
        cluster_id="cluster-1",
        failure_family=failure_family,
        affected_agent_path="root",
        affected_surface_candidates=["system_instructions"],
        severity=severity,
        prevalence=prevalence,
        recency=1.0,
        business_impact=0.5,
        sample_trace_ids=["t1", "t2"],
        recommended_operator_families=recommended_operators
        or ["instruction_rewrite", "few_shot_edit"],
        priority_score=0.7,
        status="open",
        resolution_experiment_id=None,
    )


def _make_memory() -> OptimizationMemory:
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = f.name
    f.close()
    return OptimizationMemory(db_path=db_path)


def _make_adaptive_engine(
    strategy: str = "simple",
    bandit_policy: str = "ucb1",
    budget: SearchBudget | None = None,
    tracker: OperatorPerformanceTracker | None = None,
) -> AdaptiveSearchEngine:
    registry = create_default_registry()
    mem = _make_memory()
    proposer = Proposer(use_mock=True)
    return AdaptiveSearchEngine(
        registry=registry,
        memory=mem,
        proposer=proposer,
        performance_tracker=tracker,
        budget=budget,
        search_strategy=strategy,
        bandit_policy=bandit_policy,
    )


def _simple_eval_fn(config: dict) -> dict[str, float]:
    base = 0.5
    if config.get("quality_boost"):
        base += 0.1
    if config.get("prompts", {}).get("root", ""):
        base += 0.05
    return {"quality": base, "safety": 0.9}


# ---------------------------------------------------------------------------
# Backward compatibility tests
# ---------------------------------------------------------------------------


class TestSimpleStrategyBackwardCompat:
    def test_simple_strategy_is_subclass_of_search_engine(self) -> None:
        engine = _make_adaptive_engine(strategy="simple")
        assert isinstance(engine, SearchEngine)

    def test_simple_strategy_generates_candidates(self) -> None:
        engine = _make_adaptive_engine(strategy="simple")
        opp = _make_opportunity()
        candidates = engine.generate_candidates([opp], {}, {}, {})
        assert len(candidates) > 0
        assert all(isinstance(c, CandidateMutation) for c in candidates)

    def test_simple_strategy_no_bandit(self) -> None:
        engine = _make_adaptive_engine(strategy="simple")
        assert engine.bandit is None
        assert engine.curriculum is None

    def test_simple_strategy_search_cycle(self) -> None:
        engine = _make_adaptive_engine(strategy="simple")
        opp = _make_opportunity()
        result = engine.search_cycle([opp], {}, _simple_eval_fn, {}, {})
        assert isinstance(result, SearchResult)
        assert result.candidates_generated > 0


# ---------------------------------------------------------------------------
# Adaptive strategy tests (bandit only, no curriculum)
# ---------------------------------------------------------------------------


class TestAdaptiveStrategy:
    def test_adaptive_has_bandit_no_curriculum(self) -> None:
        engine = _make_adaptive_engine(strategy="adaptive")
        assert engine.bandit is not None
        assert engine.curriculum is None

    def test_adaptive_generates_candidates(self) -> None:
        engine = _make_adaptive_engine(strategy="adaptive")
        opp = _make_opportunity()
        candidates = engine.generate_candidates([opp], {}, {}, {})
        assert len(candidates) > 0
        assert all(isinstance(c, CandidateMutation) for c in candidates)

    def test_adaptive_candidates_are_sorted(self) -> None:
        engine = _make_adaptive_engine(strategy="adaptive")
        opp = _make_opportunity()
        candidates = engine.generate_candidates([opp], {}, {}, {})
        scores = [c.combined_score for c in candidates]
        assert scores == sorted(scores, reverse=True)

    def test_adaptive_search_cycle(self) -> None:
        engine = _make_adaptive_engine(strategy="adaptive")
        opp = _make_opportunity()
        result = engine.search_cycle([opp], {}, _simple_eval_fn, {}, {})
        assert isinstance(result, SearchResult)
        assert result.candidates_generated > 0

    def test_adaptive_with_thompson_sampling(self) -> None:
        engine = _make_adaptive_engine(strategy="adaptive", bandit_policy="thompson")
        opp = _make_opportunity()
        candidates = engine.generate_candidates([opp], {}, {}, {})
        assert len(candidates) > 0

    def test_adaptive_empty_opportunities_returns_empty(self) -> None:
        engine = _make_adaptive_engine(strategy="adaptive")
        candidates = engine.generate_candidates([], {}, {}, {})
        assert len(candidates) == 0

    def test_adaptive_unknown_operators_fallback(self) -> None:
        """When all recommended operators are unknown, falls back to parent."""
        engine = _make_adaptive_engine(strategy="adaptive")
        opp = _make_opportunity(recommended_operators=["nonexistent_op"])
        candidates = engine.generate_candidates([opp], {}, {}, {})
        # Parent also returns 0 for unknown operators
        assert len(candidates) == 0


# ---------------------------------------------------------------------------
# Full strategy tests (bandit + curriculum)
# ---------------------------------------------------------------------------


class TestFullStrategy:
    def test_full_has_bandit_and_curriculum(self) -> None:
        engine = _make_adaptive_engine(strategy="full")
        assert engine.bandit is not None
        assert engine.curriculum is not None

    def test_full_generates_candidates(self) -> None:
        engine = _make_adaptive_engine(strategy="full")
        opp = _make_opportunity()
        candidates = engine.generate_candidates(
            [opp], {}, {}, {"quality_degradation": 5}
        )
        assert len(candidates) > 0

    def test_full_filters_by_curriculum(self) -> None:
        """Full strategy should respect curriculum tier filtering."""
        engine = _make_adaptive_engine(strategy="full")
        assert engine.curriculum is not None
        assert engine.curriculum.current_tier.value == "easy"

        # Create easy and hard opportunities
        easy_opp = _make_opportunity(
            failure_family="easy_fam",
            opportunity_id="opp-easy",
            recommended_operators=["instruction_rewrite"],
        )
        hard_opp = _make_opportunity(
            failure_family="hard_fam",
            opportunity_id="opp-hard",
            recommended_operators=["instruction_rewrite"],
        )

        # Failure buckets: easy_fam is 10% failures, hard_fam is 90% failures
        failure_buckets = {"easy_fam": 1, "hard_fam": 9}

        candidates = engine.generate_candidates(
            [easy_opp, hard_opp], {}, {}, failure_buckets
        )
        # With easy tier, easy_fam (pass rate 0.9) should be included
        # hard_fam (pass rate 0.1) should be filtered out
        families = {c.hypothesis.split("address ")[1].split(" ")[0] for c in candidates}
        assert "easy_fam" in families

    def test_full_search_cycle(self) -> None:
        engine = _make_adaptive_engine(strategy="full")
        opp = _make_opportunity()
        result = engine.search_cycle(
            [opp], {}, _simple_eval_fn, {}, {"quality_degradation": 3}
        )
        assert isinstance(result, SearchResult)

    def test_full_budget_caps_candidates(self) -> None:
        budget = SearchBudget(max_candidates=1)
        engine = _make_adaptive_engine(strategy="full", budget=budget)
        opps = [
            _make_opportunity(
                opportunity_id=f"opp-{i}",
                recommended_operators=["instruction_rewrite"],
            )
            for i in range(5)
        ]
        candidates = engine.generate_candidates(opps, {}, {}, {})
        assert len(candidates) <= 1


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


class TestValidation:
    def test_invalid_strategy_raises(self) -> None:
        try:
            _make_adaptive_engine(strategy="invalid")
            assert False, "Expected ValueError"
        except ValueError as e:
            assert "invalid" in str(e).lower()

    def test_invalid_bandit_policy_raises(self) -> None:
        try:
            _make_adaptive_engine(strategy="adaptive", bandit_policy="invalid")
            assert False, "Expected ValueError"
        except ValueError:
            pass


# ---------------------------------------------------------------------------
# Pass rate estimation tests
# ---------------------------------------------------------------------------


class TestEstimatePassRates:
    def test_estimate_pass_rates(self) -> None:
        engine = _make_adaptive_engine(strategy="adaptive")
        rates = engine._estimate_pass_rates({"fam_a": 3, "fam_b": 7})
        assert abs(rates["fam_a"] - 0.7) < 1e-9
        assert abs(rates["fam_b"] - 0.3) < 1e-9

    def test_estimate_pass_rates_empty(self) -> None:
        engine = _make_adaptive_engine(strategy="adaptive")
        rates = engine._estimate_pass_rates({})
        assert rates == {}

    def test_estimate_pass_rates_single(self) -> None:
        engine = _make_adaptive_engine(strategy="adaptive")
        rates = engine._estimate_pass_rates({"fam_a": 10})
        assert abs(rates["fam_a"] - 0.0) < 1e-9  # 10/10 = 100% failure = 0% pass

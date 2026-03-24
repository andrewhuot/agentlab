"""Unit tests for the EnhancedScorer, DimensionScores, and PerAgentScores."""

from __future__ import annotations

from evals.scorer import (
    CompositeScorer,
    ConstrainedScorer,
    DimensionScores,
    EnhancedScorer,
    EvalResult,
    PerAgentScores,
)


def _result(
    case_id: str = "c1",
    category: str = "happy_path",
    passed: bool = True,
    quality_score: float = 0.8,
    safety_passed: bool = True,
    latency_ms: float = 100.0,
    token_count: int = 200,
    tool_use_accuracy: float = 1.0,
    routing_correct: bool = True,
    handoff_context_preserved: bool = True,
    satisfaction_proxy: float = 1.0,
) -> EvalResult:
    """Build a minimal EvalResult with v4 fields."""
    return EvalResult(
        case_id=case_id,
        category=category,
        passed=passed,
        quality_score=quality_score,
        safety_passed=safety_passed,
        latency_ms=latency_ms,
        token_count=token_count,
        tool_use_accuracy=tool_use_accuracy,
        routing_correct=routing_correct,
        handoff_context_preserved=handoff_context_preserved,
        satisfaction_proxy=satisfaction_proxy,
    )


# ── DimensionScores ──────────────────────────────────────────────────


def test_dimension_scores_to_dict() -> None:
    """to_dict should return all 11 dimension keys."""
    ds = DimensionScores(task_success_rate=0.9, response_quality=0.8)
    d = ds.to_dict()
    assert d["task_success_rate"] == 0.9
    assert d["response_quality"] == 0.8
    assert len(d) == 11


def test_dimension_scores_to_objective_vector() -> None:
    """to_objective_vector should return a list of 11 floats."""
    ds = DimensionScores(
        task_success_rate=1.0,
        response_quality=0.9,
        safety_compliance=1.0,
        latency_p50=0.8,
        latency_p95=0.7,
        latency_p99=0.6,
        token_cost=0.5,
        tool_correctness=0.4,
        routing_accuracy=0.3,
        handoff_fidelity=0.2,
        user_satisfaction_proxy=0.1,
    )
    vec = ds.to_objective_vector()
    assert len(vec) == 11
    assert vec[0] == 1.0  # task_success_rate
    assert vec[-1] == 0.1  # user_satisfaction_proxy


# ── PerAgentScores ───────────────────────────────────────────────────


def test_per_agent_scores_defaults() -> None:
    """PerAgentScores should have sensible defaults."""
    pa = PerAgentScores(agent_path="happy_path")
    assert pa.unit_success == 0.0
    assert pa.agent_path == "happy_path"


# ── EnhancedScorer dimension computation ─────────────────────────────


def test_enhanced_scorer_computes_dimensions() -> None:
    """EnhancedScorer should populate dimensions on the CompositeScore."""
    scorer = EnhancedScorer(mode="constrained")
    results = [
        _result(case_id="c1", passed=True, quality_score=0.9, latency_ms=100.0),
        _result(case_id="c2", passed=False, quality_score=0.7, latency_ms=300.0),
    ]
    score = scorer.score(results)

    assert score.dimensions is not None
    assert score.dimensions.task_success_rate == 0.5  # 1/2
    assert score.dimensions.response_quality == 0.8  # (0.9+0.7)/2
    assert score.dimensions.safety_compliance == 1.0  # both safe


def test_enhanced_scorer_latency_percentiles() -> None:
    """Latency p50/p95/p99 should be computed and normalized."""
    scorer = EnhancedScorer(mode="constrained")
    # 10 results with increasing latency 100..1000
    results = [
        _result(case_id=f"c{i}", latency_ms=float(i * 100))
        for i in range(1, 11)
    ]
    score = scorer.score(results)
    dims = score.dimensions
    assert dims is not None
    # p50 should be lower latency than p95 which is lower than p99
    # After normalization (higher = better), p50 norm > p95 norm > p99 norm
    assert dims.latency_p50 >= dims.latency_p95
    assert dims.latency_p95 >= dims.latency_p99


def test_enhanced_scorer_routing_and_handoff() -> None:
    """G7 and G8 dimensions should reflect routing/handoff correctness."""
    scorer = EnhancedScorer(mode="constrained")
    results = [
        _result(case_id="c1", routing_correct=True, handoff_context_preserved=True),
        _result(case_id="c2", routing_correct=False, handoff_context_preserved=True),
        _result(case_id="c3", routing_correct=True, handoff_context_preserved=False),
        _result(case_id="c4", routing_correct=False, handoff_context_preserved=False),
    ]
    score = scorer.score(results)
    assert score.dimensions is not None
    assert score.dimensions.routing_accuracy == 0.5   # 2/4
    assert score.dimensions.handoff_fidelity == 0.5   # 2/4


def test_enhanced_scorer_satisfaction_proxy() -> None:
    """G9 should be the mean of satisfaction_proxy values."""
    scorer = EnhancedScorer(mode="constrained")
    results = [
        _result(case_id="c1", satisfaction_proxy=0.8),
        _result(case_id="c2", satisfaction_proxy=0.6),
    ]
    score = scorer.score(results)
    assert score.dimensions is not None
    assert score.dimensions.user_satisfaction_proxy == 0.7


def test_enhanced_scorer_empty_results() -> None:
    """EnhancedScorer should handle empty results without error."""
    scorer = EnhancedScorer(mode="constrained")
    score = scorer.score([])
    assert score.dimensions is not None
    assert score.dimensions.task_success_rate == 0.0
    assert score.per_agent_scores == []


# ── Per-agent grouping ───────────────────────────────────────────────


def test_enhanced_scorer_per_agent_grouping() -> None:
    """Per-agent scores should group by category."""
    scorer = EnhancedScorer(mode="constrained")
    results = [
        _result(case_id="c1", category="happy_path", passed=True),
        _result(case_id="c2", category="happy_path", passed=False),
        _result(case_id="c3", category="safety", passed=True),
    ]
    score = scorer.score(results)
    assert len(score.per_agent_scores) == 2
    paths = {pa.agent_path for pa in score.per_agent_scores}
    assert paths == {"happy_path", "safety"}

    hp = next(pa for pa in score.per_agent_scores if pa.agent_path == "happy_path")
    assert hp.unit_success == 0.5  # 1/2


# ── Backward compatibility ───────────────────────────────────────────


def test_enhanced_scorer_backward_compat_weighted() -> None:
    """In weighted mode, composite should match ConstrainedScorer(weighted)."""
    results = [
        _result(case_id="c1", quality_score=0.8, latency_ms=100.0, token_count=200),
        _result(case_id="c2", quality_score=0.6, latency_ms=300.0, token_count=400),
    ]

    constrained = ConstrainedScorer(mode="weighted")
    enhanced = EnhancedScorer(mode="weighted")

    cs = constrained.score(results)
    es = enhanced.score(results)

    assert es.composite == cs.composite
    assert es.quality == cs.quality
    assert es.safety == cs.safety
    assert es.latency == cs.latency
    assert es.cost == cs.cost


def test_enhanced_scorer_backward_compat_constrained() -> None:
    """In constrained mode, composite should match ConstrainedScorer(constrained)."""
    results = [
        _result(case_id="c1", quality_score=0.9, latency_ms=100.0, token_count=100),
        _result(case_id="c2", quality_score=0.7, latency_ms=200.0, token_count=300),
    ]

    constrained = ConstrainedScorer(mode="constrained")
    enhanced = EnhancedScorer(mode="constrained")

    cs = constrained.score(results)
    es = enhanced.score(results)

    assert es.composite == cs.composite
    assert es.constraints_passed == cs.constraints_passed


# ── EvalResult backward compatibility ────────────────────────────────


def test_eval_result_new_fields_have_defaults() -> None:
    """New v4 fields on EvalResult should not break existing constructors."""
    r = EvalResult(
        case_id="c1",
        category="happy_path",
        passed=True,
        quality_score=0.8,
        safety_passed=True,
        latency_ms=100.0,
        token_count=200,
    )
    assert r.routing_correct is True
    assert r.handoff_context_preserved is True
    assert r.satisfaction_proxy == 1.0


def test_composite_score_new_fields_have_defaults() -> None:
    """New v4 fields on CompositeScore should not break existing constructors."""
    scorer = CompositeScorer()
    results = [
        _result(case_id="c1"),
    ]
    score = scorer.score(results)
    assert score.dimensions is None
    assert score.per_agent_scores == []

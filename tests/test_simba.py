"""Tests for SIMBA — Simulation-Based Prompt Optimization."""

from __future__ import annotations

from typing import Any

import pytest

from evals.runner import TestCase
from evals.scorer import CompositeScore
from optimizer.prompt_opt.simba import SIMBA
from optimizer.prompt_opt.types import OptimizationResult, ProConfig, PromptCandidate
from optimizer.providers import LLMRequest, LLMResponse


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------


def _make_score(composite: float) -> CompositeScore:
    return CompositeScore(
        quality=composite,
        safety=1.0,
        latency=0.8,
        cost=0.9,
        composite=composite,
        total_cases=5,
        passed_cases=4,
    )


def _make_llm_response(text: str = "Improved instruction") -> LLMResponse:
    return LLMResponse(
        provider="mock",
        model="mock-model",
        text=text,
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        latency_ms=5.0,
    )


class StubEvalRunner:
    """Returns pre-configured scores in order."""

    def __init__(self, scores: list[CompositeScore]) -> None:
        self._scores = scores
        self._call_idx = 0
        self.run_configs: list[dict | None] = []

    def run(self, config: dict | None = None, **kwargs: Any) -> CompositeScore:
        self.run_configs.append(config)
        score = self._scores[min(self._call_idx, len(self._scores) - 1)]
        self._call_idx += 1
        return score

    def load_cases(self) -> list[TestCase]:
        return []


class StubLLMRouter:
    """Returns predetermined LLM responses and tracks calls."""

    def __init__(
        self,
        responses: list[LLMResponse] | None = None,
        cost: float = 0.0,
    ) -> None:
        self._responses = responses or [_make_llm_response()]
        self._call_idx = 0
        self._cost = cost
        self.requests: list[LLMRequest] = []

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        resp = self._responses[min(self._call_idx, len(self._responses) - 1)]
        self._call_idx += 1
        return resp

    def cost_summary(self) -> dict[str, dict[str, float | int]]:
        return {"mock:mock-model": {"total_cost": self._cost, "requests": self._call_idx}}


class FailingLLMRouter(StubLLMRouter):
    """LLM router that always raises on generate()."""

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        raise RuntimeError("LLM call failed")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_simba_returns_optimization_result() -> None:
    """SIMBA.optimize() returns an OptimizationResult with algorithm='simba'."""
    scores = [_make_score(0.5)] * 50
    eval_runner = StubEvalRunner(scores=scores)
    llm_router = StubLLMRouter()
    config = ProConfig(budget_dollars=100.0)

    simba = SIMBA(llm_router, eval_runner, config, variants_per_round=3, rounds=1)
    result = simba.optimize({"system_prompt": "Be helpful."})

    assert isinstance(result, OptimizationResult)
    assert result.algorithm == "simba"
    assert result.baseline_score == 0.5


def test_simba_finds_improvement() -> None:
    """When a variant scores higher than baseline, SIMBA returns it."""
    # baseline=0.5, then variants score 0.8
    scores = [_make_score(0.5)] + [_make_score(0.8)] * 20
    eval_runner = StubEvalRunner(scores=scores)
    llm_router = StubLLMRouter()
    config = ProConfig(budget_dollars=100.0)

    simba = SIMBA(llm_router, eval_runner, config, variants_per_round=3, top_k=2, rounds=2)
    result = simba.optimize({"system_prompt": "Be helpful."})

    assert result.improved is True
    assert result.best_candidate is not None
    assert result.best_score == 0.8
    assert result.improvement == pytest.approx(0.3)


def test_simba_no_improvement_returns_none_candidate() -> None:
    """When no variant beats baseline, best_candidate is None."""
    scores = [_make_score(0.5)] * 50
    eval_runner = StubEvalRunner(scores=scores)
    llm_router = StubLLMRouter()
    config = ProConfig(budget_dollars=100.0)

    simba = SIMBA(llm_router, eval_runner, config, variants_per_round=3, rounds=1)
    result = simba.optimize({"system_prompt": "Be helpful."})

    assert result.improved is False
    assert result.best_candidate is None


def test_simba_reward_scoring() -> None:
    """SIMBA uses eval composite score as reward, picking the highest."""
    # baseline=0.3, then variants: 0.4, 0.7, 0.5
    scores = [_make_score(0.3), _make_score(0.4), _make_score(0.7), _make_score(0.5)]
    eval_runner = StubEvalRunner(scores=scores)
    llm_router = StubLLMRouter()
    config = ProConfig(budget_dollars=100.0)

    simba = SIMBA(llm_router, eval_runner, config, variants_per_round=3, top_k=1, rounds=1)
    result = simba.optimize({"system_prompt": "test"})

    assert result.best_score == 0.7
    assert result.best_candidate is not None


def test_simba_keeps_top_k_as_seeds() -> None:
    """After scoring, top-k variants become seeds for the next round."""
    # baseline=0.3, round1: 0.5, 0.8, 0.6, round2: 0.9 (from top-k seed)
    scores = [
        _make_score(0.3),   # baseline
        _make_score(0.5),   # r1 variant 1
        _make_score(0.8),   # r1 variant 2
        _make_score(0.6),   # r1 variant 3
        _make_score(0.9),   # r2 variant from top-1 seed
        _make_score(0.85),  # r2 variant
        _make_score(0.7),   # r2 variant
    ]
    eval_runner = StubEvalRunner(scores=scores)
    llm_router = StubLLMRouter()
    config = ProConfig(budget_dollars=100.0)

    simba = SIMBA(llm_router, eval_runner, config, variants_per_round=3, top_k=1, rounds=2)
    result = simba.optimize({"system_prompt": "test"})

    # Best-ever should be 0.9 from round 2
    assert result.best_score == 0.9


def test_simba_budget_enforcement() -> None:
    """SIMBA stops early when budget is exceeded."""
    scores = [_make_score(0.5)] * 50
    eval_runner = StubEvalRunner(scores=scores)
    llm_router = StubLLMRouter(cost=100.0)  # Over budget immediately
    config = ProConfig(budget_dollars=0.01)

    simba = SIMBA(llm_router, eval_runner, config, variants_per_round=6, rounds=4)
    result = simba.optimize({"system_prompt": "test"})

    # Should stop very early due to budget
    assert result.total_eval_rounds <= 2


def test_simba_handles_llm_failure() -> None:
    """When LLM calls fail, SIMBA falls back gracefully."""
    scores = [_make_score(0.5)] * 50
    eval_runner = StubEvalRunner(scores=scores)
    llm_router = FailingLLMRouter()
    config = ProConfig(budget_dollars=100.0)

    simba = SIMBA(llm_router, eval_runner, config, variants_per_round=3, rounds=1)
    result = simba.optimize({"system_prompt": "test"})

    assert isinstance(result, OptimizationResult)
    assert result.algorithm == "simba"


def test_simba_perturbation_calls_llm() -> None:
    """Perturbation sends the instruction to LLM for rephrasing."""
    llm_router = StubLLMRouter(responses=[_make_llm_response("better prompt")])
    simba = SIMBA(llm_router, StubEvalRunner([_make_score(0.5)]), ProConfig())

    result = simba._perturb("Original prompt")

    assert result == "better prompt"
    assert len(llm_router.requests) == 1
    assert "Original prompt" in llm_router.requests[0].prompt


def test_simba_result_has_correct_metadata() -> None:
    """When improvement is found, result metadata includes algorithm details."""
    scores = [_make_score(0.3)] + [_make_score(0.9)] * 20
    eval_runner = StubEvalRunner(scores=scores)
    llm_router = StubLLMRouter()
    config = ProConfig(budget_dollars=100.0)

    simba = SIMBA(llm_router, eval_runner, config, variants_per_round=3, top_k=2, rounds=1)
    result = simba.optimize({"system_prompt": "test"})

    assert result.best_candidate is not None
    assert result.best_candidate.metadata["algorithm"] == "simba"
    assert result.best_candidate.metadata["mutation"] == "simulation_perturbation"
    assert result.best_candidate.metadata["top_k"] == 2


def test_simba_hill_climbing_tracks_best_ever() -> None:
    """Best-ever is tracked across rounds, not just the last round."""
    # baseline=0.3, r1: 0.9 (best), r2: 0.5 (worse)
    scores = [
        _make_score(0.3),   # baseline
        _make_score(0.9),   # r1 variant (best ever)
        _make_score(0.4),   # r1 variant
        _make_score(0.5),   # r2 variant
        _make_score(0.5),   # r2 variant
    ]
    eval_runner = StubEvalRunner(scores=scores)
    llm_router = StubLLMRouter()
    config = ProConfig(budget_dollars=100.0)

    simba = SIMBA(llm_router, eval_runner, config, variants_per_round=2, top_k=1, rounds=2)
    result = simba.optimize({"system_prompt": "test"})

    # Best-ever should be 0.9 from round 1, not 0.5 from round 2
    assert result.best_score == 0.9

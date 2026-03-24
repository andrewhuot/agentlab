"""Tests for GEPA — Gradient-free Evolutionary Prompt Adaptation."""

from __future__ import annotations

import random
from typing import Any

import pytest

from evals.runner import TestCase
from evals.scorer import CompositeScore
from optimizer.prompt_opt.gepa import GEPA
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


def test_gepa_returns_optimization_result() -> None:
    """GEPA.optimize() returns an OptimizationResult with algorithm='gepa'."""
    scores = [_make_score(0.5)] * 50
    eval_runner = StubEvalRunner(scores=scores)
    llm_router = StubLLMRouter()
    config = ProConfig(budget_dollars=100.0)

    gepa = GEPA(llm_router, eval_runner, config, population_size=3, generations=1)
    result = gepa.optimize({"system_prompt": "Be helpful."})

    assert isinstance(result, OptimizationResult)
    assert result.algorithm == "gepa"
    assert result.baseline_score == 0.5


def test_gepa_finds_improvement() -> None:
    """When a variant scores higher than baseline, GEPA returns it."""
    # pop_size=3, gen=1: baseline + 3 initial evals + 1 offspring eval = 5 evals
    # Make the offspring eval (index 4) score higher than baseline
    scores = [
        _make_score(0.5),   # baseline
        _make_score(0.5),   # initial pop member 0
        _make_score(0.5),   # initial pop member 1
        _make_score(0.5),   # initial pop member 2
        _make_score(0.8),   # offspring (improvement!)
    ]
    eval_runner = StubEvalRunner(scores=scores)
    llm_router = StubLLMRouter()
    config = ProConfig(budget_dollars=100.0)

    gepa = GEPA(llm_router, eval_runner, config, population_size=3, generations=1,
                rng=random.Random(42))
    result = gepa.optimize({"system_prompt": "Be helpful."})

    assert result.improved is True
    assert result.best_candidate is not None
    assert result.best_score == 0.8
    assert result.improvement == pytest.approx(0.3)


def test_gepa_no_improvement_returns_none_candidate() -> None:
    """When no variant beats baseline, best_candidate is None."""
    # All scores equal to baseline
    scores = [_make_score(0.5)] * 50
    eval_runner = StubEvalRunner(scores=scores)
    llm_router = StubLLMRouter()
    config = ProConfig(budget_dollars=100.0)

    gepa = GEPA(llm_router, eval_runner, config, population_size=3, generations=1,
                rng=random.Random(42))
    result = gepa.optimize({"system_prompt": "Be helpful."})

    assert result.improved is False
    assert result.best_candidate is None


def test_gepa_population_evolution() -> None:
    """Population evolves: LLM is called for mutation and crossover."""
    scores = [_make_score(0.5)] * 50
    eval_runner = StubEvalRunner(scores=scores)
    llm_router = StubLLMRouter()
    config = ProConfig(budget_dollars=100.0)

    gepa = GEPA(llm_router, eval_runner, config, population_size=4, generations=2,
                rng=random.Random(42))
    gepa.optimize({"system_prompt": "Be helpful."})

    # LLM called for: initial population mutations (3) + per-generation crossover+mutation
    assert len(llm_router.requests) > 3


def test_gepa_tournament_selection_picks_fitter() -> None:
    """Tournament selection always returns the fitter of two random picks."""
    gepa = GEPA(
        StubLLMRouter(), StubEvalRunner([_make_score(0.5)]),
        ProConfig(), rng=random.Random(0),
    )
    population = ["low", "high"]
    fitness = [0.2, 0.9]

    # Run many tournaments — "high" should win at least as often
    results = [gepa._tournament_select(population, fitness) for _ in range(100)]
    assert results.count("high") >= results.count("low")


def test_gepa_crossover_calls_llm() -> None:
    """Crossover sends both parents to the LLM."""
    llm_router = StubLLMRouter(responses=[_make_llm_response("merged")])
    gepa = GEPA(llm_router, StubEvalRunner([_make_score(0.5)]), ProConfig())

    result = gepa._crossover("Prompt A", "Prompt B")

    assert result == "merged"
    assert len(llm_router.requests) == 1
    assert "Prompt A" in llm_router.requests[0].prompt
    assert "Prompt B" in llm_router.requests[0].prompt


def test_gepa_mutation_calls_llm() -> None:
    """Mutation sends the prompt to the LLM for rephrasing."""
    llm_router = StubLLMRouter(responses=[_make_llm_response("mutated")])
    gepa = GEPA(llm_router, StubEvalRunner([_make_score(0.5)]), ProConfig())

    result = gepa._mutate("Original prompt")

    assert result == "mutated"
    assert len(llm_router.requests) == 1
    assert "Original prompt" in llm_router.requests[0].prompt


def test_gepa_budget_enforcement() -> None:
    """GEPA stops early when budget is exceeded."""
    scores = [_make_score(0.5)] * 50
    eval_runner = StubEvalRunner(scores=scores)
    llm_router = StubLLMRouter(cost=100.0)  # Over budget immediately
    config = ProConfig(budget_dollars=0.01)

    gepa = GEPA(llm_router, eval_runner, config, population_size=6, generations=5)
    result = gepa.optimize({"system_prompt": "test"})

    # Should stop very early due to budget
    assert result.total_eval_rounds <= 3


def test_gepa_handles_llm_failure() -> None:
    """When LLM calls fail, GEPA falls back gracefully without crashing."""
    scores = [_make_score(0.5)] * 50
    eval_runner = StubEvalRunner(scores=scores)
    llm_router = FailingLLMRouter()
    config = ProConfig(budget_dollars=100.0)

    gepa = GEPA(llm_router, eval_runner, config, population_size=3, generations=1,
                rng=random.Random(42))
    result = gepa.optimize({"system_prompt": "test"})

    # Should not crash; returns a valid result
    assert isinstance(result, OptimizationResult)
    assert result.algorithm == "gepa"


def test_gepa_result_has_correct_metadata() -> None:
    """When improvement is found, result metadata includes algorithm details."""
    # pop_size=3, gen=1: baseline + 3 initial + 1 offspring = 5 evals
    scores = [
        _make_score(0.3),   # baseline
        _make_score(0.3),   # initial pop 0
        _make_score(0.3),   # initial pop 1
        _make_score(0.3),   # initial pop 2
        _make_score(0.9),   # offspring (improvement)
    ]
    eval_runner = StubEvalRunner(scores=scores)
    llm_router = StubLLMRouter()
    config = ProConfig(budget_dollars=100.0)

    gepa = GEPA(llm_router, eval_runner, config, population_size=3, generations=1,
                rng=random.Random(42))
    result = gepa.optimize({"system_prompt": "test"})

    assert result.best_candidate is not None
    assert result.best_candidate.metadata["algorithm"] == "gepa"
    assert result.best_candidate.metadata["mutation"] == "evolutionary"
    assert result.best_candidate.metadata["population_size"] == 3

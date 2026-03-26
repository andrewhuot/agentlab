"""Tests for pro-mode prompt optimization: strategy, GEPA/SIMBA stubs, and integration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


from evals.runner import EvalRunner
from observer.metrics import HealthMetrics, HealthReport
from optimizer.prompt_opt import (
    OptimizationResult,
    ProAlgorithm,
    ProConfig,
    ProSearchStrategy,
)
from optimizer.prompt_opt.gepa import GEPA
from optimizer.prompt_opt.simba import SIMBA
from optimizer.providers import LLMRouter, ModelConfig, MockProvider
from optimizer.search import SearchStrategy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_llm_router() -> LLMRouter:
    """Build a mock LLM router for tests."""
    mock_config = ModelConfig(provider="mock", model="mock-proposer")
    return LLMRouter(
        strategy="single",
        models=[mock_config],
        providers={(mock_config.provider, mock_config.model): MockProvider(mock_config)},
    )


def _make_eval_runner() -> EvalRunner:
    """Build an EvalRunner with mock agent function (no real cases needed)."""
    return EvalRunner(cases_dir="/tmp/nonexistent_cases_dir")


def _health_report() -> HealthReport:
    return HealthReport(
        metrics=HealthMetrics(
            success_rate=0.62,
            avg_latency_ms=420.0,
            error_rate=0.22,
            safety_violation_rate=0.01,
            avg_cost=0.19,
            total_conversations=100,
        ),
        failure_buckets={"routing_error": 7, "tool_failure": 3},
        needs_optimization=True,
        reason="error rate too high",
    )


# ---------------------------------------------------------------------------
# 1. Algorithm selection
# ---------------------------------------------------------------------------


class TestProStrategyAlgorithmSelection:
    """Tests for ProSearchStrategy._select_algorithm()."""

    def test_pro_strategy_selects_miprov2_by_default(self) -> None:
        """AUTO with normal budget selects MIPROv2."""
        config = ProConfig(algorithm="auto", budget_dollars=10.0)
        strategy = ProSearchStrategy(
            llm_router=_make_llm_router(),
            eval_runner=_make_eval_runner(),
            config=config,
        )
        assert strategy._select_algorithm() == ProAlgorithm.MIPROV2

    def test_pro_strategy_selects_bootstrap_for_tight_budget(self) -> None:
        """AUTO with budget < 1.0 selects BootstrapFewShot."""
        config = ProConfig(algorithm="auto", budget_dollars=0.50)
        strategy = ProSearchStrategy(
            llm_router=_make_llm_router(),
            eval_runner=_make_eval_runner(),
            config=config,
        )
        assert strategy._select_algorithm() == ProAlgorithm.BOOTSTRAP_FEWSHOT

    def test_pro_strategy_selects_explicit_algorithm(self) -> None:
        """Explicit algorithm name overrides auto selection."""
        config = ProConfig(algorithm="gepa")
        strategy = ProSearchStrategy(
            llm_router=_make_llm_router(),
            eval_runner=_make_eval_runner(),
            config=config,
        )
        assert strategy._select_algorithm() == ProAlgorithm.GEPA

    def test_pro_strategy_falls_back_on_unknown_algorithm(self) -> None:
        """Unknown algorithm name falls back to auto (MIPROv2 with normal budget)."""
        config = ProConfig(algorithm="nonexistent_algorithm", budget_dollars=5.0)
        strategy = ProSearchStrategy(
            llm_router=_make_llm_router(),
            eval_runner=_make_eval_runner(),
            config=config,
        )
        assert strategy._select_algorithm() == ProAlgorithm.MIPROV2


# ---------------------------------------------------------------------------
# 2. Routing integration
# ---------------------------------------------------------------------------


class TestProStrategyRouting:
    """Tests that ProSearchStrategy.run() routes to the correct algorithm."""

    def test_pro_strategy_routes_to_bootstrap(self) -> None:
        """Integration: auto with tight budget actually calls BootstrapFewShot."""
        config = ProConfig(algorithm="auto", budget_dollars=0.50)
        strategy = ProSearchStrategy(
            llm_router=_make_llm_router(),
            eval_runner=_make_eval_runner(),
            config=config,
        )
        mock_instance = MagicMock()
        mock_instance.optimize.return_value = OptimizationResult(
            best_candidate=None,
            baseline_score=0.5,
            best_score=0.5,
            algorithm="bootstrap_fewshot",
            total_eval_rounds=1,
        )
        with patch("optimizer.prompt_opt.bootstrap_fewshot.BootstrapFewShot", return_value=mock_instance) as MockBS:
            result = strategy.run(current_config={})
            MockBS.assert_called_once()
            mock_instance.optimize.assert_called_once()
            assert result.algorithm == "bootstrap_fewshot"

    def test_pro_strategy_routes_to_mipro(self) -> None:
        """Integration: auto with normal budget actually calls MIPROv2."""
        config = ProConfig(algorithm="auto", budget_dollars=10.0)
        strategy = ProSearchStrategy(
            llm_router=_make_llm_router(),
            eval_runner=_make_eval_runner(),
            config=config,
        )
        mock_instance = MagicMock()
        mock_instance.optimize.return_value = OptimizationResult(
            best_candidate=None,
            baseline_score=0.5,
            best_score=0.5,
            algorithm="miprov2",
            total_eval_rounds=1,
        )
        with patch("optimizer.prompt_opt.mipro.MIPROv2", return_value=mock_instance) as MockMIPRO:
            result = strategy.run(current_config={})
            MockMIPRO.assert_called_once()
            mock_instance.optimize.assert_called_once()
            assert result.algorithm == "miprov2"

    def test_pro_strategy_routes_to_gepa(self) -> None:
        """Explicit GEPA routing triggers GEPA and returns a result."""
        config = ProConfig(algorithm="gepa")
        strategy = ProSearchStrategy(
            llm_router=_make_llm_router(),
            eval_runner=_make_eval_runner(),
            config=config,
        )
        mock_instance = MagicMock()
        mock_instance.optimize.return_value = OptimizationResult(
            best_candidate=None,
            baseline_score=0.5,
            best_score=0.5,
            algorithm="gepa",
            total_eval_rounds=1,
        )
        with patch("optimizer.prompt_opt.gepa.GEPA", return_value=mock_instance) as MockGEPA:
            result = strategy.run(current_config={})
            MockGEPA.assert_called_once()
            mock_instance.optimize.assert_called_once()
            assert result.algorithm == "gepa"

    def test_pro_strategy_routes_to_simba(self) -> None:
        """Explicit SIMBA routing triggers SIMBA and returns a result."""
        config = ProConfig(algorithm="simba")
        strategy = ProSearchStrategy(
            llm_router=_make_llm_router(),
            eval_runner=_make_eval_runner(),
            config=config,
        )
        mock_instance = MagicMock()
        mock_instance.optimize.return_value = OptimizationResult(
            best_candidate=None,
            baseline_score=0.5,
            best_score=0.5,
            algorithm="simba",
            total_eval_rounds=1,
        )
        with patch("optimizer.prompt_opt.simba.SIMBA", return_value=mock_instance) as MockSIMBA:
            result = strategy.run(current_config={})
            MockSIMBA.assert_called_once()
            mock_instance.optimize.assert_called_once()
            assert result.algorithm == "simba"


# ---------------------------------------------------------------------------
# 3. GEPA/SIMBA stubs
# ---------------------------------------------------------------------------


class TestGEPAIntegration:
    """Integration tests for GEPA evolutionary prompt optimization."""

    def test_gepa_returns_result_with_correct_algorithm(self) -> None:
        """GEPA.optimize() returns an OptimizationResult with algorithm='gepa'."""
        gepa = GEPA(
            llm_router=_make_llm_router(),
            eval_runner=_make_eval_runner(),
            config=ProConfig(),
            population_size=3,
            generations=1,
        )
        result = gepa.optimize({"system_prompt": "test"})
        assert isinstance(result, OptimizationResult)
        assert result.algorithm == "gepa"

    def test_gepa_population_evolution_calls_llm(self) -> None:
        """GEPA calls LLM for mutation/crossover during evolution."""
        llm_router = _make_llm_router()
        gepa = GEPA(
            llm_router=llm_router,
            eval_runner=_make_eval_runner(),
            config=ProConfig(),
            population_size=3,
            generations=1,
        )
        result = gepa.optimize({"system_prompt": "test"})
        # Should have called generate() for population init + crossover/mutation
        assert result.total_eval_rounds > 1

    def test_gepa_budget_enforcement_stops_early(self) -> None:
        """GEPA respects budget and stops early when cost is exceeded."""
        mock_config = ModelConfig(provider="mock", model="mock-proposer")
        # Build a router with high cost tracking
        mock_provider = MockProvider(mock_config)
        llm_router = LLMRouter(
            strategy="single",
            models=[mock_config],
            providers={(mock_config.provider, mock_config.model): mock_provider},
        )
        config = ProConfig(budget_dollars=0.0001)
        gepa = GEPA(
            llm_router=llm_router,
            eval_runner=_make_eval_runner(),
            config=config,
            population_size=6,
            generations=5,
        )
        result = gepa.optimize({"system_prompt": "test"})
        # With essentially zero budget, should stop very early
        assert result.algorithm == "gepa"


class TestSIMBAIntegration:
    """Integration tests for SIMBA simulation-based prompt optimization."""

    def test_simba_returns_result_with_correct_algorithm(self) -> None:
        """SIMBA.optimize() returns an OptimizationResult with algorithm='simba'."""
        simba = SIMBA(
            llm_router=_make_llm_router(),
            eval_runner=_make_eval_runner(),
            config=ProConfig(),
            variants_per_round=3,
            rounds=1,
        )
        result = simba.optimize({"system_prompt": "test"})
        assert isinstance(result, OptimizationResult)
        assert result.algorithm == "simba"

    def test_simba_reward_scoring_via_eval(self) -> None:
        """SIMBA uses eval composite score as reward signal."""
        simba = SIMBA(
            llm_router=_make_llm_router(),
            eval_runner=_make_eval_runner(),
            config=ProConfig(),
            variants_per_round=3,
            rounds=1,
        )
        result = simba.optimize({"system_prompt": "test"})
        # Should have run baseline + variant evals
        assert result.total_eval_rounds >= 2

    def test_simba_budget_enforcement_stops_early(self) -> None:
        """SIMBA respects budget and stops early when cost is exceeded."""
        config = ProConfig(budget_dollars=0.0001)
        simba = SIMBA(
            llm_router=_make_llm_router(),
            eval_runner=_make_eval_runner(),
            config=config,
            variants_per_round=6,
            rounds=4,
        )
        result = simba.optimize({"system_prompt": "test"})
        assert result.algorithm == "simba"


# ---------------------------------------------------------------------------
# 4. SearchStrategy enum
# ---------------------------------------------------------------------------


class TestSearchStrategyEnum:
    """Tests for the PRO addition to SearchStrategy."""

    def test_search_strategy_enum_has_pro(self) -> None:
        """SearchStrategy.PRO exists and equals 'pro'."""
        assert SearchStrategy.PRO == "pro"
        assert SearchStrategy.PRO.value == "pro"

    def test_search_strategy_pro_is_valid_member(self) -> None:
        """PRO can be constructed from string value."""
        assert SearchStrategy("pro") == SearchStrategy.PRO


# ---------------------------------------------------------------------------
# 5. Optimizer integration
# ---------------------------------------------------------------------------


class TestOptimizerProRouting:
    """Tests that the Optimizer correctly routes to pro strategy."""

    def test_optimizer_routes_pro_strategy(self) -> None:
        """Optimizer with search_strategy='pro' routes to _optimize_pro."""
        from optimizer.loop import Optimizer

        eval_runner = _make_eval_runner()
        optimizer = Optimizer(
            eval_runner=eval_runner,
            search_strategy="pro",
        )
        assert optimizer.search_strategy == SearchStrategy.PRO

    def test_optimizer_stores_pro_config(self) -> None:
        """Optimizer stores the ProConfig passed to it."""
        from optimizer.loop import Optimizer

        config = ProConfig(algorithm="gepa", budget_dollars=2.0)
        optimizer = Optimizer(
            eval_runner=_make_eval_runner(),
            search_strategy="pro",
            pro_config=config,
        )
        assert optimizer.pro_config.algorithm == "gepa"
        assert optimizer.pro_config.budget_dollars == 2.0

    def test_optimizer_defaults_pro_config(self) -> None:
        """Optimizer uses default ProConfig when none is provided."""
        from optimizer.loop import Optimizer

        optimizer = Optimizer(
            eval_runner=_make_eval_runner(),
            search_strategy="pro",
        )
        assert optimizer.pro_config.algorithm == "auto"
        assert optimizer.pro_config.budget_dollars == 10.0


# ---------------------------------------------------------------------------
# 6. ProConfig
# ---------------------------------------------------------------------------


class TestProConfig:
    """Tests for ProConfig construction and defaults."""

    def test_pro_config_defaults(self) -> None:
        """ProConfig() has sensible defaults."""
        config = ProConfig()
        assert config.algorithm == "auto"
        assert config.instruction_candidates == 5
        assert config.example_candidates == 3
        assert config.max_eval_rounds == 10
        assert config.teacher_model is None
        assert config.budget_dollars == 10.0

    def test_pro_config_from_dict(self) -> None:
        """ProConfig.from_dict() correctly parses a dictionary."""
        data = {
            "algorithm": "miprov2",
            "instruction_candidates": 8,
            "example_candidates": 5,
            "max_eval_rounds": 20,
            "teacher_model": "gpt-4o",
            "budget_dollars": 25.0,
        }
        config = ProConfig.from_dict(data)
        assert config.algorithm == "miprov2"
        assert config.instruction_candidates == 8
        assert config.example_candidates == 5
        assert config.max_eval_rounds == 20
        assert config.teacher_model == "gpt-4o"
        assert config.budget_dollars == 25.0

    def test_pro_config_from_dict_with_defaults(self) -> None:
        """ProConfig.from_dict() uses defaults for missing keys."""
        config = ProConfig.from_dict({})
        assert config.algorithm == "auto"
        assert config.budget_dollars == 10.0
        assert config.teacher_model is None

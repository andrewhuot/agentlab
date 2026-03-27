"""Adversarial simulation checks for optimizer candidate validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from evals.fixtures.mock_data import mock_agent_response
from simulator.sandbox import SimulationSandbox


@dataclass
class AdversarialSimulationResult:
    """Outcome of comparing baseline and candidate on adversarial simulations."""

    baseline_pass_rate: float
    candidate_pass_rate: float
    pass_rate_delta: float
    passed: bool
    conversations: int
    details: str


@dataclass
class AdversarialSimulationConfig:
    """Runtime knobs for adversarial simulation checks."""

    enabled: bool = True
    conversations: int = 30
    max_allowed_drop: float = 0.05
    domain: str = "customer-support"
    seed: int = 1337
    normal_ratio: float = 0.20
    edge_case_ratio: float = 0.30
    adversarial_ratio: float = 0.50


class AdversarialSimulator:
    """Runs an adversarial simulation A/B check between baseline and candidate.

    WHY: Eval-suite score improvements can hide brittle behavior. A targeted
    adversarial simulation pass adds a second, behavior-focused check that
    stresses edge and adversarial user inputs before promotion.
    """

    def __init__(self, config: AdversarialSimulationConfig | None = None) -> None:
        self.config = config or AdversarialSimulationConfig()

    def evaluate_candidate(
        self,
        *,
        baseline_config: dict[str, Any],
        candidate_config: dict[str, Any],
    ) -> AdversarialSimulationResult:
        """Compare baseline vs candidate on identical synthetic conversations."""
        if not self.config.enabled:
            return AdversarialSimulationResult(
                baseline_pass_rate=0.0,
                candidate_pass_rate=0.0,
                pass_rate_delta=0.0,
                passed=True,
                conversations=0,
                details="adversarial_simulation_disabled",
            )

        generator = SimulationSandbox(rng_seed=self.config.seed)
        conversations = generator.generate_conversations(
            domain=self.config.domain,
            count=self.config.conversations,
            difficulty_distribution={
                "normal": self.config.normal_ratio,
                "edge_case": self.config.edge_case_ratio,
                "adversarial": self.config.adversarial_ratio,
            },
        )

        baseline_runner = SimulationSandbox(
            agent_fn=lambda message: mock_agent_response(message, baseline_config),
        )
        candidate_runner = SimulationSandbox(
            agent_fn=lambda message: mock_agent_response(message, candidate_config),
        )

        baseline_result = baseline_runner.stress_test(
            config=baseline_config,
            conversations=conversations,
            config_id="baseline",
        )
        candidate_result = candidate_runner.stress_test(
            config=candidate_config,
            conversations=conversations,
            config_id="candidate",
        )

        delta = candidate_result.pass_rate - baseline_result.pass_rate
        passed = delta >= -self.config.max_allowed_drop
        details = (
            "adversarial_pass_rate "
            f"{baseline_result.pass_rate:.3f} -> {candidate_result.pass_rate:.3f} "
            f"(delta={delta:+.3f}, allowed_drop={self.config.max_allowed_drop:.3f})"
        )

        return AdversarialSimulationResult(
            baseline_pass_rate=baseline_result.pass_rate,
            candidate_pass_rate=candidate_result.pass_rate,
            pass_rate_delta=delta,
            passed=passed,
            conversations=len(conversations),
            details=details,
        )

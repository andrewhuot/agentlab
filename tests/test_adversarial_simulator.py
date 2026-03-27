"""Tests for adversarial simulation checks in optimization gating."""

from __future__ import annotations

from optimizer.adversarial import (
    AdversarialSimulationConfig,
    AdversarialSimulator,
)


def test_adversarial_simulator_is_deterministic_for_same_inputs() -> None:
    """Same configs and seed should produce identical simulation outcomes."""
    simulator = AdversarialSimulator(
        AdversarialSimulationConfig(
            enabled=True,
            conversations=20,
            seed=2026,
            max_allowed_drop=0.05,
        )
    )

    baseline = {"model": "gemini-2.0-flash", "prompts": {"root": "You are helpful."}}
    candidate = {"model": "gemini-2.0-flash", "prompts": {"root": "You are helpful and concise."}}

    first = simulator.evaluate_candidate(
        baseline_config=baseline,
        candidate_config=candidate,
    )
    second = simulator.evaluate_candidate(
        baseline_config=baseline,
        candidate_config=candidate,
    )

    assert first.conversations == 20
    assert second.conversations == 20
    assert first.baseline_pass_rate == second.baseline_pass_rate
    assert first.candidate_pass_rate == second.candidate_pass_rate
    assert first.pass_rate_delta == second.pass_rate_delta
    assert first.passed == second.passed


def test_adversarial_simulator_can_be_disabled() -> None:
    """Disabled simulation should short-circuit with a pass verdict."""
    simulator = AdversarialSimulator(AdversarialSimulationConfig(enabled=False))
    result = simulator.evaluate_candidate(
        baseline_config={"prompts": {"root": "A"}},
        candidate_config={"prompts": {"root": "B"}},
    )

    assert result.passed is True
    assert result.conversations == 0
    assert result.details == "adversarial_simulation_disabled"

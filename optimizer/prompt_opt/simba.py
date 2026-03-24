"""SIMBA — Simulation-Based Prompt Optimization.

Uses eval-as-reward to score prompt variants, keeps the top-k, and iteratively
generates new variants from the best performers via LLM perturbation.

Algorithm:
1. Generate N prompt variants from the current prompt via LLM perturbation.
2. Score each variant using EvalRunner (composite score as scalar reward).
3. Keep top-k variants.
4. Generate new variants from top-k via LLM perturbation.
5. Repeat for R rounds within budget.
6. Return the best-ever prompt as OptimizationResult (hill-climbing).
"""

from __future__ import annotations

import logging
from typing import Any

from evals.runner import EvalRunner
from evals.scorer import CompositeScore
from optimizer.providers import LLMRequest, LLMRouter

from .types import (
    OptimizationResult,
    ProConfig,
    PromptCandidate,
)

logger = logging.getLogger(__name__)

# Defaults
_DEFAULT_VARIANTS_PER_ROUND = 6
_DEFAULT_TOP_K = 3
_DEFAULT_ROUNDS = 4


class SIMBA:
    """Simulation-Based Prompt Optimization.

    Iterative hill-climbing: generate variants, score via eval, keep top-k,
    repeat. Tracks best-ever across all rounds.
    """

    def __init__(
        self,
        llm_router: LLMRouter,
        eval_runner: EvalRunner,
        config: ProConfig,
        *,
        variants_per_round: int = _DEFAULT_VARIANTS_PER_ROUND,
        top_k: int = _DEFAULT_TOP_K,
        rounds: int = _DEFAULT_ROUNDS,
    ) -> None:
        self.llm_router = llm_router
        self.eval_runner = eval_runner
        self.config = config
        self.variants_per_round = max(1, variants_per_round)
        self.top_k = max(1, top_k)
        self.rounds = max(1, rounds)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def optimize(
        self,
        current_config: dict[str, Any],
        task_description: str = "",
    ) -> OptimizationResult:
        """Run simulation-based prompt optimization.

        Returns:
            OptimizationResult with the best prompt found across all rounds.
        """
        current_instruction = current_config.get(
            "system_prompt", "You are a helpful assistant.",
        )

        # Step 1 — Baseline eval
        baseline_score = self.eval_runner.run(config=current_config)
        baseline_composite = baseline_score.composite
        eval_rounds = 1

        # Track best-ever (hill-climbing)
        best_instruction = current_instruction
        best_score = baseline_composite

        # Seeds for the first round of variant generation
        seeds = [current_instruction]

        for round_idx in range(self.rounds):
            if self._budget_exceeded():
                logger.info("Budget exceeded at round %d; stopping.", round_idx)
                break

            # Step 2 — Generate variants from seeds
            variants: list[str] = []
            for seed in seeds:
                variants_needed = max(
                    1, self.variants_per_round // max(1, len(seeds)),
                )
                for _ in range(variants_needed):
                    if self._budget_exceeded():
                        break
                    variant = self._perturb(seed)
                    variants.append(variant)

            if not variants:
                break

            # Step 3 — Score each variant (eval-as-reward)
            scored: list[tuple[str, float]] = []
            for variant in variants:
                if self._budget_exceeded():
                    break
                reward = self._evaluate(variant, current_config)
                eval_rounds += 1
                scored.append((variant, reward))

                # Track best-ever
                if reward > best_score:
                    best_score = reward
                    best_instruction = variant

            if not scored:
                break

            # Step 4 — Keep top-k
            scored.sort(key=lambda x: x[1], reverse=True)
            top_k_results = scored[: self.top_k]
            seeds = [instruction for instruction, _ in top_k_results]

        # Build result
        improvement = best_score - baseline_composite
        best_candidate: PromptCandidate | None = None
        if best_score > baseline_composite:
            best_candidate = PromptCandidate(
                instruction=best_instruction,
                eval_score=best_score,
                metadata={
                    "algorithm": "simba",
                    "rounds_run": min(round_idx + 1, self.rounds) if self.rounds > 0 else 0,
                    "variants_per_round": self.variants_per_round,
                    "top_k": self.top_k,
                    "mutation": "simulation_perturbation",
                },
            )

        return OptimizationResult(
            best_candidate=best_candidate,
            baseline_score=baseline_composite,
            best_score=best_score,
            algorithm="simba",
            total_eval_rounds=eval_rounds,
            total_cost_dollars=self._total_cost(),
            candidates_evaluated=eval_rounds - 1,
            improvement=improvement,
        )

    # ------------------------------------------------------------------
    # LLM perturbation
    # ------------------------------------------------------------------

    def _perturb(self, instruction: str) -> str:
        """Generate a variant of the instruction via LLM perturbation."""
        prompt = (
            "Rephrase this instruction to be more specific and effective: "
            f"[{instruction}]. Return only the improved instruction."
        )
        request = LLMRequest(
            prompt=prompt,
            system="You are a prompt engineering expert. Return only the instruction text.",
            temperature=0.9,
            max_tokens=500,
        )
        try:
            response = self.llm_router.generate(request)
            return response.text.strip()
        except Exception:
            logger.warning("Perturbation LLM call failed; returning original.")
            return instruction

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def _evaluate(self, instruction: str, base_config: dict[str, Any]) -> float:
        """Score a prompt instruction via EvalRunner composite score (reward)."""
        config = dict(base_config)
        config["system_prompt"] = instruction
        try:
            score = self.eval_runner.run(config=config)
            return score.composite
        except Exception:
            logger.warning("Eval failed for instruction; returning 0.0.")
            return 0.0

    # ------------------------------------------------------------------
    # Budget tracking
    # ------------------------------------------------------------------

    def _budget_exceeded(self) -> bool:
        """Check whether total LLM cost has exceeded the configured budget."""
        return self._total_cost() > self.config.budget_dollars

    def _total_cost(self) -> float:
        """Return the total LLM cost accumulated so far."""
        cost_summary = self.llm_router.cost_summary()
        return sum(
            float(entry.get("total_cost", 0.0))
            for entry in cost_summary.values()
        )

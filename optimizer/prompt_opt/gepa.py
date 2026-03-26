"""GEPA — Gradient-free Evolutionary Prompt Adaptation.

Maintains a population of prompt variants and evolves them via LLM-based
crossover and mutation operators, scored through eval fitness.

Algorithm:
1. Initialize population from the current prompt + LLM-generated variants.
2. Evaluate fitness of each member via EvalRunner.
3. For G generations:
   a. Tournament selection → pick parents.
   b. Crossover → LLM merges two high-scoring prompts.
   c. Mutation → LLM perturbs offspring.
   d. Evaluate offspring fitness.
   e. Replace weakest population members with offspring.
4. Return the best-ever prompt as OptimizationResult.
"""

from __future__ import annotations

import logging
import random
from typing import Any

from evals.runner import EvalRunner
from optimizer.providers import LLMRequest, LLMRouter

from .types import (
    OptimizationResult,
    ProConfig,
    PromptCandidate,
)

logger = logging.getLogger(__name__)

# Defaults
_DEFAULT_POPULATION_SIZE = 6
_DEFAULT_GENERATIONS = 5


class GEPA:
    """Gradient-free Evolutionary Prompt Adaptation.

    Evolves a population of prompt instructions using LLM-driven crossover
    and mutation, scored by eval fitness.
    """

    def __init__(
        self,
        llm_router: LLMRouter,
        eval_runner: EvalRunner,
        config: ProConfig,
        *,
        population_size: int = _DEFAULT_POPULATION_SIZE,
        generations: int = _DEFAULT_GENERATIONS,
        rng: random.Random | None = None,
    ) -> None:
        self.llm_router = llm_router
        self.eval_runner = eval_runner
        self.config = config
        self.population_size = max(2, population_size)
        self.generations = max(1, generations)
        self._rng = rng or random.Random()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def optimize(
        self,
        current_config: dict[str, Any],
        task_description: str = "",
    ) -> OptimizationResult:
        """Run evolutionary prompt optimization.

        Returns:
            OptimizationResult with the best prompt found across all generations.
        """
        current_instruction = current_config.get(
            "system_prompt", "You are a helpful assistant.",
        )

        # Step 1 — Baseline eval
        baseline_score = self.eval_runner.run(config=current_config)
        baseline_composite = baseline_score.composite
        eval_rounds = 1

        # Step 2 — Initialize population
        population = self._initialize_population(current_instruction)

        # Step 3 — Evaluate initial fitness
        fitness: list[float] = []
        for member in population:
            if self._budget_exceeded():
                fitness.append(0.0)
                continue
            score = self._evaluate(member, current_config)
            eval_rounds += 1
            fitness.append(score)

        # Track best-ever
        best_idx = self._argmax(fitness)
        best_instruction = population[best_idx]
        best_score = fitness[best_idx]

        # Step 4 — Evolve for G generations
        for gen in range(self.generations):
            if self._budget_exceeded():
                logger.info("Budget exceeded at generation %d; stopping.", gen)
                break

            offspring: list[str] = []
            offspring_fitness: list[float] = []

            # Produce offspring equal to half the population size
            n_offspring = max(1, self.population_size // 2)
            for _ in range(n_offspring):
                if self._budget_exceeded():
                    break

                # Tournament selection — pick two parents
                parent_a = self._tournament_select(population, fitness)
                parent_b = self._tournament_select(population, fitness)

                # Crossover
                child = self._crossover(parent_a, parent_b)

                # Mutation
                child = self._mutate(child)

                # Evaluate offspring
                child_score = self._evaluate(child, current_config)
                eval_rounds += 1

                offspring.append(child)
                offspring_fitness.append(child_score)

                # Track best-ever
                if child_score > best_score:
                    best_score = child_score
                    best_instruction = child

            # Replace weakest members with offspring
            self._replace_weakest(population, fitness, offspring, offspring_fitness)

        # Build result
        improvement = best_score - baseline_composite
        best_candidate: PromptCandidate | None = None
        if best_score > baseline_composite:
            best_candidate = PromptCandidate(
                instruction=best_instruction,
                eval_score=best_score,
                metadata={
                    "algorithm": "gepa",
                    "generations_run": min(self.generations, self.generations),
                    "population_size": self.population_size,
                    "mutation": "evolutionary",
                },
            )

        return OptimizationResult(
            best_candidate=best_candidate,
            baseline_score=baseline_composite,
            best_score=best_score,
            algorithm="gepa",
            total_eval_rounds=eval_rounds,
            total_cost_dollars=self._total_cost(),
            candidates_evaluated=eval_rounds - 1,
            improvement=improvement,
        )

    # ------------------------------------------------------------------
    # Population initialization
    # ------------------------------------------------------------------

    def _initialize_population(self, seed_instruction: str) -> list[str]:
        """Create initial population from the seed instruction + LLM variants."""
        population = [seed_instruction]

        for _ in range(self.population_size - 1):
            if self._budget_exceeded():
                population.append(seed_instruction)
                continue
            variant = self._mutate(seed_instruction)
            population.append(variant)

        return population

    # ------------------------------------------------------------------
    # Genetic operators
    # ------------------------------------------------------------------

    def _tournament_select(
        self,
        population: list[str],
        fitness: list[float],
    ) -> str:
        """Tournament selection: pick 2 random members, return the fitter one."""
        idx_a = self._rng.randrange(len(population))
        idx_b = self._rng.randrange(len(population))
        if fitness[idx_a] >= fitness[idx_b]:
            return population[idx_a]
        return population[idx_b]

    def _crossover(self, parent_a: str, parent_b: str) -> str:
        """LLM-based crossover: merge two prompts into one."""
        prompt = (
            "Combine the best aspects of these two instructions: "
            f"[A] {parent_a} and [B] {parent_b}. "
            "Return only the combined instruction."
        )
        request = LLMRequest(
            prompt=prompt,
            system="You are a prompt engineering expert. Return only the instruction text.",
            temperature=0.8,
            max_tokens=500,
        )
        try:
            response = self.llm_router.generate(request)
            return response.text.strip()
        except Exception:
            logger.warning("Crossover LLM call failed; returning parent A.")
            return parent_a

    def _mutate(self, instruction: str) -> str:
        """LLM-based mutation: perturb a prompt to be more specific/effective."""
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
            logger.warning("Mutation LLM call failed; returning original.")
            return instruction

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def _evaluate(self, instruction: str, base_config: dict[str, Any]) -> float:
        """Evaluate a prompt instruction via EvalRunner, return composite score."""
        config = dict(base_config)
        config["system_prompt"] = instruction
        try:
            score = self.eval_runner.run(config=config)
            return score.composite
        except Exception:
            logger.warning("Eval failed for instruction; returning 0.0.")
            return 0.0

    # ------------------------------------------------------------------
    # Replacement
    # ------------------------------------------------------------------

    def _replace_weakest(
        self,
        population: list[str],
        fitness: list[float],
        offspring: list[str],
        offspring_fitness: list[float],
    ) -> None:
        """Replace the weakest population members with offspring (in-place)."""
        for child, child_fit in zip(offspring, offspring_fitness):
            worst_idx = self._argmin(fitness)
            if child_fit > fitness[worst_idx]:
                population[worst_idx] = child
                fitness[worst_idx] = child_fit

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _argmax(values: list[float]) -> int:
        """Return index of maximum value."""
        return max(range(len(values)), key=lambda i: values[i])

    @staticmethod
    def _argmin(values: list[float]) -> int:
        """Return index of minimum value."""
        return min(range(len(values)), key=lambda i: values[i])

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

"""Bandit-based experiment selection for adaptive optimization.

Replaces uniform/BFS allocation with principled explore/exploit balancing.
Supports UCB1 and Thompson Sampling policies.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from enum import Enum


class BanditPolicy(Enum):
    ucb1 = "ucb1"
    thompson = "thompson"


@dataclass
class ArmStats:
    """Statistics for one bandit arm (operator, failure_family combo)."""

    arm_id: str
    operator_name: str
    failure_family: str
    attempts: int = 0
    successes: int = 0
    total_reward: float = 0.0  # cumulative improvement delta

    @property
    def mean_reward(self) -> float:
        if self.attempts == 0:
            return 0.0
        return self.total_reward / self.attempts

    @property
    def success_rate(self) -> float:
        if self.attempts == 0:
            return 0.5  # optimistic prior
        return self.successes / self.attempts


class BanditSelector:
    """Multi-armed bandit for selecting which (operator, failure_family) to try next.

    Arms are (operator_name, failure_family) tuples.
    Reward = improvement delta from experiment.
    """

    def __init__(
        self,
        policy: BanditPolicy = BanditPolicy.ucb1,
        exploration_weight: float = 1.41,  # sqrt(2) for UCB1
    ) -> None:
        self.policy = policy
        self.exploration_weight = exploration_weight
        self._arms: dict[str, ArmStats] = {}
        self._total_pulls: int = 0

    def _arm_id(self, operator_name: str, failure_family: str) -> str:
        return f"{operator_name}::{failure_family}"

    def get_or_create_arm(self, operator_name: str, failure_family: str) -> ArmStats:
        arm_id = self._arm_id(operator_name, failure_family)
        if arm_id not in self._arms:
            self._arms[arm_id] = ArmStats(
                arm_id=arm_id,
                operator_name=operator_name,
                failure_family=failure_family,
            )
        return self._arms[arm_id]

    def select(self, candidates: list[tuple[str, str]]) -> tuple[str, str]:
        """Select the best (operator_name, failure_family) to try next.

        candidates: list of (operator_name, failure_family) tuples
        Returns: selected (operator_name, failure_family)
        """
        if not candidates:
            raise ValueError("No candidates to select from")

        if self.policy == BanditPolicy.ucb1:
            return self._select_ucb1(candidates)
        else:
            return self._select_thompson(candidates)

    def _select_ucb1(self, candidates: list[tuple[str, str]]) -> tuple[str, str]:
        """UCB1: mean_reward + c * sqrt(log(T) / n_a)"""
        # First try any unvisited arms
        for op, ff in candidates:
            arm = self.get_or_create_arm(op, ff)
            if arm.attempts == 0:
                return (op, ff)

        best_score = -float("inf")
        best_candidate = candidates[0]

        for op, ff in candidates:
            arm = self.get_or_create_arm(op, ff)
            exploit = arm.mean_reward
            explore = self.exploration_weight * math.sqrt(
                math.log(max(1, self._total_pulls)) / max(1, arm.attempts)
            )
            score = exploit + explore
            if score > best_score:
                best_score = score
                best_candidate = (op, ff)

        return best_candidate

    def _select_thompson(self, candidates: list[tuple[str, str]]) -> tuple[str, str]:
        """Thompson Sampling using Beta distribution."""
        best_sample = -float("inf")
        best_candidate = candidates[0]

        for op, ff in candidates:
            arm = self.get_or_create_arm(op, ff)
            # Beta(alpha, beta) where alpha = successes+1, beta = failures+1
            alpha = arm.successes + 1
            beta_param = (arm.attempts - arm.successes) + 1
            sample = random.betavariate(alpha, beta_param)
            if sample > best_sample:
                best_sample = sample
                best_candidate = (op, ff)

        return best_candidate

    def record_outcome(
        self,
        operator_name: str,
        failure_family: str,
        success: bool,
        reward: float = 0.0,
    ) -> None:
        """Record the outcome of pulling an arm."""
        arm = self.get_or_create_arm(operator_name, failure_family)
        arm.attempts += 1
        self._total_pulls += 1
        if success:
            arm.successes += 1
        arm.total_reward += reward

    def get_arm_stats(self) -> list[ArmStats]:
        """Return all arm statistics for observability."""
        return sorted(self._arms.values(), key=lambda a: a.mean_reward, reverse=True)

    def rank_candidates(
        self,
        candidates: list[tuple[str, str]],
        n: int = 5,
    ) -> list[tuple[str, str, float]]:
        """Rank all candidates by bandit score. Returns (op, ff, score) tuples."""
        scored: list[tuple[str, str, float]] = []
        for op, ff in candidates:
            arm = self.get_or_create_arm(op, ff)
            if self.policy == BanditPolicy.ucb1:
                if arm.attempts == 0:
                    score = float("inf")
                else:
                    score = arm.mean_reward + self.exploration_weight * math.sqrt(
                        math.log(max(1, self._total_pulls)) / max(1, arm.attempts)
                    )
            else:
                alpha = arm.successes + 1
                beta_param = (arm.attempts - arm.successes) + 1
                score = alpha / (alpha + beta_param)  # use mean for ranking, not sample
            scored.append((op, ff, score))
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:n]

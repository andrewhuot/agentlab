"""Curriculum learning for staged optimization.

Starts with easy failure clusters for cheap early wins,
then graduates to harder problems as optimization budget allows.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DifficultyTier(Enum):
    easy = "easy"  # top 50% pass rate
    medium = "medium"  # 25-75% pass rate
    hard = "hard"  # bottom 25% pass rate


@dataclass
class CaseHistory:
    """Track historical pass rates for difficulty estimation."""

    case_id: str
    total_attempts: int = 0
    total_passes: int = 0

    @property
    def pass_rate(self) -> float:
        if self.total_attempts == 0:
            return 0.5  # assume medium difficulty
        return self.total_passes / self.total_attempts


@dataclass
class FailureClusterDifficulty:
    """Difficulty estimate for a failure cluster/family."""

    failure_family: str
    avg_pass_rate: float = 0.5
    case_count: int = 0
    tier: DifficultyTier = DifficultyTier.medium

    @property
    def difficulty_score(self) -> float:
        """0 = easiest, 1 = hardest."""
        return 1.0 - self.avg_pass_rate


class CurriculumScheduler:
    """Manages curriculum-based optimization scheduling.

    Phase 1 (easy): Focus on high-pass-rate failure clusters
    Phase 2 (medium): Graduate to medium-difficulty clusters
    Phase 3 (hard): Tackle the hardest failure clusters

    Transition criteria: improvement rate drops below threshold for current tier.
    """

    EASY_THRESHOLD = 0.50  # pass rate > 50% = easy
    HARD_THRESHOLD = 0.25  # pass rate < 25% = hard

    def __init__(
        self,
        min_experiments_per_tier: int = 3,
        improvement_stall_threshold: float = 0.01,
    ) -> None:
        self.current_tier = DifficultyTier.easy
        self.min_experiments_per_tier = min_experiments_per_tier
        self.improvement_stall_threshold = improvement_stall_threshold
        self._case_history: dict[str, CaseHistory] = {}
        self._tier_experiments: dict[DifficultyTier, int] = {
            DifficultyTier.easy: 0,
            DifficultyTier.medium: 0,
            DifficultyTier.hard: 0,
        }
        self._tier_improvements: dict[DifficultyTier, list[float]] = {
            DifficultyTier.easy: [],
            DifficultyTier.medium: [],
            DifficultyTier.hard: [],
        }

    def classify_difficulty(self, failure_family: str, pass_rate: float) -> DifficultyTier:
        """Classify a failure family into a difficulty tier."""
        if pass_rate >= self.EASY_THRESHOLD:
            return DifficultyTier.easy
        elif pass_rate >= self.HARD_THRESHOLD:
            return DifficultyTier.medium
        else:
            return DifficultyTier.hard

    def record_case_outcome(self, case_id: str, passed: bool) -> None:
        """Update case pass rate history."""
        if case_id not in self._case_history:
            self._case_history[case_id] = CaseHistory(case_id=case_id)
        history = self._case_history[case_id]
        history.total_attempts += 1
        if passed:
            history.total_passes += 1

    def record_experiment(self, tier: DifficultyTier, improvement_delta: float) -> None:
        """Record an experiment outcome for tier progression tracking."""
        self._tier_experiments[tier] += 1
        self._tier_improvements[tier].append(improvement_delta)

    def should_advance_tier(self) -> bool:
        """Check if we should advance to the next difficulty tier."""
        experiments = self._tier_experiments[self.current_tier]
        if experiments < self.min_experiments_per_tier:
            return False

        improvements = self._tier_improvements[self.current_tier]
        if not improvements:
            return False

        # Check if recent improvements have stalled
        recent = improvements[-self.min_experiments_per_tier :]
        avg_improvement = sum(recent) / len(recent)
        return avg_improvement < self.improvement_stall_threshold

    def advance_tier(self) -> DifficultyTier:
        """Advance to next difficulty tier. Returns the new tier."""
        if self.current_tier == DifficultyTier.easy:
            self.current_tier = DifficultyTier.medium
        elif self.current_tier == DifficultyTier.medium:
            self.current_tier = DifficultyTier.hard
        # hard stays hard
        return self.current_tier

    def filter_opportunities(
        self,
        opportunities: list,  # list[OptimizationOpportunity]
        pass_rates: dict[str, float],  # failure_family -> pass_rate
    ) -> list:
        """Filter opportunities to match current curriculum tier.

        Returns opportunities whose difficulty matches the current tier.
        Falls back to all opportunities if no matches for current tier.
        """
        # Auto-advance if stalled
        if self.should_advance_tier():
            self.advance_tier()

        tier = self.current_tier
        matching = []
        for opp in opportunities:
            rate = pass_rates.get(opp.failure_family, 0.5)
            opp_tier = self.classify_difficulty(opp.failure_family, rate)
            if self._tier_eligible(opp_tier, tier):
                matching.append(opp)

        # Fallback: if no matching opportunities, include all
        if not matching:
            return list(opportunities)
        return matching

    def _tier_eligible(
        self, opp_tier: DifficultyTier, current_tier: DifficultyTier
    ) -> bool:
        """Check if opportunity tier is eligible given current curriculum tier."""
        order = {DifficultyTier.easy: 0, DifficultyTier.medium: 1, DifficultyTier.hard: 2}
        return order[opp_tier] <= order[current_tier]

    def get_difficulty_estimates(
        self, failure_families: list[str], pass_rates: dict[str, float]
    ) -> list[FailureClusterDifficulty]:
        """Return difficulty estimates for all failure families."""
        estimates = []
        for ff in failure_families:
            rate = pass_rates.get(ff, 0.5)
            tier = self.classify_difficulty(ff, rate)
            estimates.append(
                FailureClusterDifficulty(
                    failure_family=ff,
                    avg_pass_rate=rate,
                    tier=tier,
                )
            )
        estimates.sort(key=lambda e: e.difficulty_score)
        return estimates

    def get_status(self) -> dict:
        """Return curriculum status for observability."""
        return {
            "current_tier": self.current_tier.value,
            "experiments_per_tier": {
                t.value: c for t, c in self._tier_experiments.items()
            },
            "should_advance": self.should_advance_tier(),
        }

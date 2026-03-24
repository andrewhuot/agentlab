"""Anti-Goodhart safeguards for evaluation-driven optimization loops."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AntiGoodhartConfig:
    """Configuration knobs for guardrail checks."""

    holdout_tolerance: float = 0.0
    max_judge_variance: float = 0.03
    drift_threshold: float = 0.12
    holdout_rotation_interval: int = 5


@dataclass
class AntiGoodhartVerdict:
    """Outcome of evaluating one candidate with anti-Goodhart checks."""

    passed: bool
    violations: list[str] = field(default_factory=list)
    estimated_judge_variance: float = 0.0
    rotation_epoch: int = 0
    rebaselined: bool = False


class AntiGoodhartGuard:
    """Stateful guard for holdouts, drift, and judge-variance controls."""

    def __init__(self, config: AntiGoodhartConfig | None = None) -> None:
        self.config = config or AntiGoodhartConfig()
        self._evaluation_count = 0
        self._rotation_epoch = 0
        self._baseline_anchor: float | None = None

    def observe_baseline(self, baseline_metrics: dict[str, Any]) -> None:
        """Update baseline anchor from externally observed baseline metrics."""
        composite = self._as_float(baseline_metrics.get("composite"), default=0.0)
        self._baseline_anchor = composite

    def evaluate_candidate(
        self,
        baseline_metrics: dict[str, Any],
        candidate_metrics: dict[str, Any],
    ) -> AntiGoodhartVerdict:
        """Evaluate candidate against anti-Goodhart guardrails.

        Required keys for strict holdout checks:
        - fixed_holdout_composite
        - rolling_holdout_composite

        If keys are missing they default to main composite metrics.
        """
        violations: list[str] = []
        rebaselined = False

        baseline_composite = self._as_float(baseline_metrics.get("composite"), default=0.0)
        candidate_composite = self._as_float(candidate_metrics.get("composite"), default=0.0)

        baseline_fixed = self._as_float(
            baseline_metrics.get("fixed_holdout_composite"),
            default=baseline_composite,
        )
        candidate_fixed = self._as_float(
            candidate_metrics.get("fixed_holdout_composite"),
            default=candidate_composite,
        )
        baseline_rolling = self._as_float(
            baseline_metrics.get("rolling_holdout_composite"),
            default=baseline_composite,
        )
        candidate_rolling = self._as_float(
            candidate_metrics.get("rolling_holdout_composite"),
            default=candidate_composite,
        )

        tolerance = self.config.holdout_tolerance
        if candidate_fixed + tolerance < baseline_fixed:
            violations.append(
                f"Fixed holdout regressed ({candidate_fixed:.4f} < {baseline_fixed:.4f})"
            )
        if candidate_rolling + tolerance < baseline_rolling:
            violations.append(
                f"Rolling holdout regressed ({candidate_rolling:.4f} < {baseline_rolling:.4f})"
            )

        variance = self._estimate_judge_variance(candidate_metrics)
        if variance > self.config.max_judge_variance:
            violations.append(
                f"Judge variance too high ({variance:.6f} > {self.config.max_judge_variance:.6f})"
            )

        if self._baseline_anchor is None:
            self._baseline_anchor = baseline_composite
        elif self._baseline_anchor > 0:
            drift = abs(baseline_composite - self._baseline_anchor) / self._baseline_anchor
            if drift > self.config.drift_threshold:
                self._baseline_anchor = baseline_composite
                rebaselined = True

        self._evaluation_count += 1
        if self.config.holdout_rotation_interval > 0 and (
            self._evaluation_count % self.config.holdout_rotation_interval == 0
        ):
            self._rotation_epoch += 1

        return AntiGoodhartVerdict(
            passed=len(violations) == 0,
            violations=violations,
            estimated_judge_variance=variance,
            rotation_epoch=self._rotation_epoch,
            rebaselined=rebaselined,
        )

    @staticmethod
    def _as_float(value: Any, default: float) -> float:
        """Convert mixed values to float with fallback."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _estimate_judge_variance(self, metrics: dict[str, Any]) -> float:
        """Estimate judge variance from explicit judge scores or proxy metrics."""
        scores = metrics.get("judge_scores")
        if isinstance(scores, list):
            numeric = [
                self._as_float(item, default=0.0)
                for item in scores
                if isinstance(item, (int, float)) or str(item).strip()
            ]
            if len(numeric) >= 2:
                return float(statistics.pvariance(numeric))

        proxy_values = []
        for key in ("quality", "safety", "user_satisfaction_proxy"):
            if key in metrics:
                proxy_values.append(self._as_float(metrics[key], default=0.0))
        if len(proxy_values) >= 2:
            return float(statistics.pvariance(proxy_values))
        return 0.0

"""Holdout rotation and drift detection for Anti-Goodhart mechanisms.

Prevents optimizer from overfitting to evaluation sets by:
1. Rotating which cases are in holdout vs tuning sets
2. Detecting baseline drift and triggering re-baselining
3. Requiring candidates to pass BOTH fixed AND rolling holdouts
4. Estimating judge variance for confidence calibration
"""

from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass


@dataclass
class HoldoutConfig:
    """Configuration for holdout rotation."""

    tuning_fraction: float = 0.6
    validation_fraction: float = 0.2
    holdout_fraction: float = 0.2
    rotation_interval_experiments: int = 10
    drift_detection_window: int = 5
    drift_threshold: float = 0.03


@dataclass
class HoldoutSplit:
    """A specific split of case IDs into tuning/validation/holdout sets."""

    split_id: str
    created_at: float
    tuning_case_ids: list[str]
    validation_case_ids: list[str]
    holdout_case_ids: list[str]
    rotation_epoch: int = 0


class HoldoutManager:
    """Manages holdout rotation, drift detection, and re-baselining.

    Anti-Goodhart defense: the optimizer never sees holdout scores as feedback.
    Holdout scores are used only for final validation (accept/reject).
    """

    def __init__(self, config: HoldoutConfig | None = None):
        self.config = config or HoldoutConfig()
        self._current_split: HoldoutSplit | None = None
        self._experiment_count: int = 0
        self._baseline_history: list[float] = []
        self._split_history: list[HoldoutSplit] = []

    def create_split(self, case_ids: list[str], rotation_epoch: int = 0) -> HoldoutSplit:
        """Create a deterministic split of cases into tuning/validation/holdout.

        Uses SHA hash of (case_id, rotation_epoch) for deterministic assignment
        so splits are reproducible.
        """
        tuning: list[str] = []
        validation: list[str] = []
        holdout: list[str] = []

        for case_id in sorted(case_ids):
            bucket = self._hash_bucket(case_id, rotation_epoch)
            if bucket < self.config.tuning_fraction:
                tuning.append(case_id)
            elif bucket < self.config.tuning_fraction + self.config.validation_fraction:
                validation.append(case_id)
            else:
                holdout.append(case_id)

        split = HoldoutSplit(
            split_id=hashlib.sha256(
                f"{rotation_epoch}:{','.join(sorted(case_ids))}".encode()
            ).hexdigest()[:12],
            created_at=time.time(),
            tuning_case_ids=tuning,
            validation_case_ids=validation,
            holdout_case_ids=holdout,
            rotation_epoch=rotation_epoch,
        )
        self._current_split = split
        self._split_history.append(split)
        return split

    def get_current_split(self) -> HoldoutSplit | None:
        """Return the current holdout split, or None if not yet created."""
        return self._current_split

    def should_rotate(self) -> bool:
        """Check if it's time to rotate the holdout split."""
        return self._experiment_count > 0 and (
            self._experiment_count % self.config.rotation_interval_experiments == 0
        )

    def rotate(self, case_ids: list[str]) -> HoldoutSplit:
        """Rotate to a new holdout split."""
        new_epoch = (self._current_split.rotation_epoch + 1) if self._current_split else 0
        return self.create_split(case_ids, rotation_epoch=new_epoch)

    def record_experiment(self, baseline_score: float) -> None:
        """Record an experiment for rotation and drift tracking."""
        self._experiment_count += 1
        self._baseline_history.append(baseline_score)

    def detect_drift(self) -> tuple[bool, float]:
        """Detect if baseline scores are drifting (degrading over time).

        Returns (is_drifting, drift_amount).
        Drift = early baseline mean - recent baseline mean > threshold.
        """
        window = self.config.drift_detection_window
        if len(self._baseline_history) < window * 2:
            return False, 0.0

        early = self._baseline_history[:window]
        recent = self._baseline_history[-window:]

        early_mean = sum(early) / len(early)
        recent_mean = sum(recent) / len(recent)
        drift = early_mean - recent_mean

        return drift > self.config.drift_threshold, round(drift, 6)

    def should_rebaseline(self) -> bool:
        """Check if drift warrants re-baselining."""
        is_drifting, _ = self.detect_drift()
        return is_drifting

    def validate_on_holdout(
        self,
        holdout_score: float,
        baseline_holdout_score: float,
    ) -> tuple[bool, str]:
        """Validate candidate passes on holdout set.

        Candidate must not regress vs baseline on holdout.
        This is the Anti-Goodhart check -- optimizer didn't see holdout scores.
        """
        delta = holdout_score - baseline_holdout_score
        if delta < -self.config.drift_threshold:
            return False, f"Holdout regression: {delta:+.4f} (threshold={self.config.drift_threshold})"
        return True, f"Holdout passed: {delta:+.4f}"

    @staticmethod
    def _hash_bucket(case_id: str, epoch: int) -> float:
        """Deterministic hash of case_id + epoch -> [0, 1)."""
        key = f"{case_id}::epoch={epoch}"
        digest = hashlib.sha256(key.encode()).hexdigest()
        return int(digest[:8], 16) / 0xFFFFFFFF

    def get_status(self) -> dict:
        """Return holdout manager status for observability."""
        is_drifting, drift_amount = self.detect_drift()
        return {
            "experiment_count": self._experiment_count,
            "current_split_id": self._current_split.split_id if self._current_split else None,
            "rotation_epoch": self._current_split.rotation_epoch if self._current_split else 0,
            "should_rotate": self.should_rotate(),
            "is_drifting": is_drifting,
            "drift_amount": drift_amount,
            "baseline_history_length": len(self._baseline_history),
        }


@dataclass
class JudgeVarianceEstimate:
    """Estimate of judge (evaluator) variance for confidence calibration."""

    metric_name: str
    mean_score: float = 0.0
    variance: float = 0.0
    n_observations: int = 0
    confidence_interval_width: float = 0.0

    @property
    def std_dev(self) -> float:
        """Standard deviation derived from variance."""
        return self.variance ** 0.5 if self.variance > 0 else 0.0


class JudgeVarianceEstimator:
    """Estimates variance in LLM judge scoring for confidence calibration.

    Tracks score distributions per metric to determine how much
    natural variation exists in evaluation scores, independent of
    actual quality differences.
    """

    def __init__(self) -> None:
        self._observations: dict[str, list[float]] = {}

    def record(self, metric_name: str, score: float) -> None:
        """Record a score observation for variance estimation."""
        if metric_name not in self._observations:
            self._observations[metric_name] = []
        self._observations[metric_name].append(score)

    def record_batch(self, scores: dict[str, float]) -> None:
        """Record multiple metric scores at once."""
        for name, score in scores.items():
            self.record(name, score)

    def estimate(self, metric_name: str) -> JudgeVarianceEstimate:
        """Compute variance estimate for a specific metric."""
        obs = self._observations.get(metric_name, [])
        n = len(obs)
        if n < 2:
            return JudgeVarianceEstimate(
                metric_name=metric_name,
                mean_score=obs[0] if obs else 0.0,
                n_observations=n,
            )

        mean = sum(obs) / n
        variance = sum((x - mean) ** 2 for x in obs) / (n - 1)  # sample variance

        # 95% CI width approximation: 2 * 1.96 * stderr
        stderr = math.sqrt(variance / n)
        ci_width = 2 * 1.96 * stderr

        return JudgeVarianceEstimate(
            metric_name=metric_name,
            mean_score=round(mean, 6),
            variance=round(variance, 6),
            n_observations=n,
            confidence_interval_width=round(ci_width, 6),
        )

    def estimate_all(self) -> list[JudgeVarianceEstimate]:
        """Compute variance estimates for all tracked metrics."""
        return [self.estimate(name) for name in sorted(self._observations.keys())]

    def is_score_meaningful(
        self, metric_name: str, delta: float, confidence: float = 0.95
    ) -> bool:
        """Check if a score delta is larger than judge noise.

        Returns True if delta > CI width (i.e., likely a real difference, not noise).
        """
        est = self.estimate(metric_name)
        if est.n_observations < 5:
            return True  # not enough data to estimate noise; assume meaningful
        return abs(delta) > est.confidence_interval_width

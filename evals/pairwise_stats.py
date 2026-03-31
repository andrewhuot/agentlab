"""Statistical analysis helpers for pairwise eval comparisons."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


@dataclass
class PairwiseAnalysis:
    """User-facing statistical summary for a pairwise comparison run."""

    label_a: str
    label_b: str
    total_cases: int
    mean_score_a: float
    mean_score_b: float
    mean_delta: float
    effect_size: float
    p_value: float
    is_significant: bool
    confidence: float
    winner: str
    win_rates: dict[str, float] = field(default_factory=dict)
    win_rate_confidence_intervals: dict[str, tuple[float, float]] = field(default_factory=dict)
    score_delta_confidence_interval: tuple[float, float] = (0.0, 0.0)
    recommended_additional_cases: int = 0
    target_sample_size: int = 0
    summary_message: str = ""

    def to_dict(self) -> dict[str, object]:
        """Serialize the analysis so it can be persisted and returned by APIs."""
        return {
            "label_a": self.label_a,
            "label_b": self.label_b,
            "total_cases": self.total_cases,
            "mean_score_a": self.mean_score_a,
            "mean_score_b": self.mean_score_b,
            "mean_delta": self.mean_delta,
            "effect_size": self.effect_size,
            "p_value": self.p_value,
            "is_significant": self.is_significant,
            "confidence": self.confidence,
            "winner": self.winner,
            "win_rates": self.win_rates,
            "win_rate_confidence_intervals": {
                key: [bounds[0], bounds[1]]
                for key, bounds in self.win_rate_confidence_intervals.items()
            },
            "score_delta_confidence_interval": [
                self.score_delta_confidence_interval[0],
                self.score_delta_confidence_interval[1],
            ],
            "recommended_additional_cases": self.recommended_additional_cases,
            "target_sample_size": self.target_sample_size,
            "summary_message": self.summary_message,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> PairwiseAnalysis:
        """Rehydrate a persisted pairwise analysis payload."""
        raw_cis = payload.get("win_rate_confidence_intervals", {})
        cis = {}
        if isinstance(raw_cis, dict):
            for key, value in raw_cis.items():
                if isinstance(value, (list, tuple)) and len(value) == 2:
                    cis[str(key)] = (float(value[0]), float(value[1]))
        delta_ci_raw = payload.get("score_delta_confidence_interval", [0.0, 0.0])
        if isinstance(delta_ci_raw, (list, tuple)) and len(delta_ci_raw) == 2:
            delta_ci = (float(delta_ci_raw[0]), float(delta_ci_raw[1]))
        else:
            delta_ci = (0.0, 0.0)
        return cls(
            label_a=str(payload.get("label_a", "A")),
            label_b=str(payload.get("label_b", "B")),
            total_cases=int(payload.get("total_cases", 0)),
            mean_score_a=float(payload.get("mean_score_a", 0.0)),
            mean_score_b=float(payload.get("mean_score_b", 0.0)),
            mean_delta=float(payload.get("mean_delta", 0.0)),
            effect_size=float(payload.get("effect_size", 0.0)),
            p_value=float(payload.get("p_value", 1.0)),
            is_significant=bool(payload.get("is_significant", False)),
            confidence=float(payload.get("confidence", 0.0)),
            winner=str(payload.get("winner", "tie")),
            win_rates={
                str(key): float(value)
                for key, value in (payload.get("win_rates", {}) or {}).items()
            },
            win_rate_confidence_intervals=cis,
            score_delta_confidence_interval=delta_ci,
            recommended_additional_cases=int(payload.get("recommended_additional_cases", 0)),
            target_sample_size=int(payload.get("target_sample_size", 0)),
            summary_message=str(payload.get("summary_message", "")),
        )


def analyze_pairwise_scores(
    *,
    label_a: str,
    label_b: str,
    left_scores: list[float],
    right_scores: list[float],
    outcomes: list[str],
    alpha: float = 0.05,
    iterations: int = 2000,
    seed: int = 7,
) -> PairwiseAnalysis:
    """Analyze per-case pairwise scores and outcome labels."""
    n = min(len(left_scores), len(right_scores))
    if n == 0:
        return PairwiseAnalysis(
            label_a=label_a,
            label_b=label_b,
            total_cases=0,
            mean_score_a=0.0,
            mean_score_b=0.0,
            mean_delta=0.0,
            effect_size=0.0,
            p_value=1.0,
            is_significant=False,
            confidence=0.0,
            winner="tie",
            win_rates={label_a: 0.0, label_b: 0.0, "tie": 0.0},
            win_rate_confidence_intervals={
                label_a: (0.0, 0.0),
                label_b: (0.0, 0.0),
                "tie": (0.0, 0.0),
            },
            score_delta_confidence_interval=(0.0, 0.0),
            recommended_additional_cases=0,
            target_sample_size=0,
            summary_message="No pairwise cases were evaluated.",
        )

    trimmed_left = [float(value) for value in left_scores[:n]]
    trimmed_right = [float(value) for value in right_scores[:n]]
    trimmed_outcomes = list(outcomes[:n]) if outcomes else ["tie"] * n
    diffs = [right - left for left, right in zip(trimmed_left, trimmed_right)]
    mean_score_a = round(sum(trimmed_left) / n, 4)
    mean_score_b = round(sum(trimmed_right) / n, 4)
    mean_delta = round(sum(diffs) / n, 4)
    effect_size = round(_paired_effect_size(diffs), 4)
    p_value = round(_paired_permutation_p_value(diffs, iterations=iterations, seed=seed), 4)
    is_significant = p_value < alpha
    winner = _winner_for_delta(mean_delta, label_a=label_a, label_b=label_b)
    win_rates = _win_rates(trimmed_outcomes, label_a=label_a, label_b=label_b)
    delta_distribution = _bootstrap_delta_distribution(diffs, iterations=iterations, seed=seed)
    delta_ci = _quantile_interval(delta_distribution, alpha=alpha)
    confidence = round(
        _winner_confidence(delta_distribution, winner=winner, label_a=label_a, label_b=label_b),
        4,
    )
    win_rate_cis = _bootstrap_outcome_cis(
        trimmed_outcomes,
        label_a=label_a,
        label_b=label_b,
        iterations=iterations,
        alpha=alpha,
        seed=seed,
    )

    target_sample_size = 0
    additional_cases = 0
    if not is_significant:
        target_sample_size = _estimate_target_sample_size(effect_size=effect_size, alpha=alpha)
        additional_cases = max(1, target_sample_size - n) if target_sample_size > n else 1

    if is_significant and winner != "tie":
        summary_message = (
            f"{winner} leads with {(confidence * 100):.1f}% confidence "
            f"(p={p_value:.4f}, effect size={effect_size:.2f})."
        )
    elif winner == "tie":
        summary_message = "Results are inconclusive; both variants are effectively tied."
    else:
        summary_message = (
            f"Results are inconclusive; collect about {additional_cases} more cases "
            f"to separate {label_a} from {label_b}."
        )

    return PairwiseAnalysis(
        label_a=label_a,
        label_b=label_b,
        total_cases=n,
        mean_score_a=mean_score_a,
        mean_score_b=mean_score_b,
        mean_delta=mean_delta,
        effect_size=effect_size,
        p_value=p_value,
        is_significant=is_significant,
        confidence=confidence,
        winner=winner,
        win_rates=win_rates,
        win_rate_confidence_intervals=win_rate_cis,
        score_delta_confidence_interval=(round(delta_ci[0], 4), round(delta_ci[1], 4)),
        recommended_additional_cases=additional_cases,
        target_sample_size=target_sample_size,
        summary_message=summary_message,
    )


def _winner_for_delta(mean_delta: float, *, label_a: str, label_b: str) -> str:
    """Return the comparison winner for a mean score delta."""
    if abs(mean_delta) < 1e-9:
        return "tie"
    return label_b if mean_delta > 0 else label_a


def _paired_effect_size(diffs: list[float]) -> float:
    """Compute Cohen's d for paired score deltas."""
    if not diffs:
        return 0.0
    n = len(diffs)
    mean_delta = sum(diffs) / n
    if n == 1:
        return 0.0 if abs(mean_delta) < 1e-9 else 10.0
    variance = sum((diff - mean_delta) ** 2 for diff in diffs) / max(1, n - 1)
    std_dev = math.sqrt(max(variance, 0.0))
    if std_dev == 0.0:
        return 0.0 if abs(mean_delta) < 1e-9 else 10.0
    return mean_delta / std_dev


def _paired_permutation_p_value(
    diffs: list[float],
    *,
    iterations: int,
    seed: int,
) -> float:
    """Estimate a two-sided permutation p-value via sign flipping."""
    if not diffs:
        return 1.0
    observed = abs(sum(diffs) / len(diffs))
    if observed < 1e-9:
        return 1.0

    rng = random.Random(seed)
    rounds = max(100, int(iterations))
    exceedances = 0
    for _ in range(rounds):
        sample = [diff if rng.random() >= 0.5 else -diff for diff in diffs]
        sample_mean = abs(sum(sample) / len(sample))
        if sample_mean >= observed:
            exceedances += 1
    return (exceedances + 1) / (rounds + 1)


def _bootstrap_delta_distribution(
    diffs: list[float],
    *,
    iterations: int,
    seed: int,
) -> list[float]:
    """Bootstrap the paired score delta distribution."""
    if not diffs:
        return [0.0]
    rng = random.Random(seed)
    rounds = max(100, int(iterations))
    n = len(diffs)
    deltas: list[float] = []
    for _ in range(rounds):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        deltas.append(sum(sample) / n)
    deltas.sort()
    return deltas


def _quantile_interval(values: list[float], *, alpha: float) -> tuple[float, float]:
    """Return a simple empirical confidence interval from sorted bootstrap samples."""
    if not values:
        return (0.0, 0.0)
    lo_index = max(0, int(len(values) * (alpha / 2)))
    hi_index = min(len(values) - 1, int(len(values) * (1 - alpha / 2)) - 1)
    return (values[lo_index], values[hi_index])


def _winner_confidence(
    delta_distribution: list[float],
    *,
    winner: str,
    label_a: str,
    label_b: str,
) -> float:
    """Estimate the confidence that the declared winner is actually ahead."""
    if not delta_distribution or winner == "tie":
        return 0.5
    if winner == label_b:
        return sum(1 for delta in delta_distribution if delta > 0) / len(delta_distribution)
    if winner == label_a:
        return sum(1 for delta in delta_distribution if delta < 0) / len(delta_distribution)
    return 0.5


def _win_rates(outcomes: list[str], *, label_a: str, label_b: str) -> dict[str, float]:
    """Return normalized win rates for each comparison outcome."""
    total = max(1, len(outcomes))
    counts = {label_a: 0, label_b: 0, "tie": 0}
    for outcome in outcomes:
        if outcome == label_a:
            counts[label_a] += 1
        elif outcome == label_b:
            counts[label_b] += 1
        else:
            counts["tie"] += 1
    return {key: round(value / total, 4) for key, value in counts.items()}


def _bootstrap_outcome_cis(
    outcomes: list[str],
    *,
    label_a: str,
    label_b: str,
    iterations: int,
    alpha: float,
    seed: int,
) -> dict[str, tuple[float, float]]:
    """Bootstrap confidence intervals for label-level win rates."""
    if not outcomes:
        return {label_a: (0.0, 0.0), label_b: (0.0, 0.0), "tie": (0.0, 0.0)}

    rng = random.Random(seed)
    rounds = max(100, int(iterations))
    n = len(outcomes)
    traces = {label_a: [], label_b: [], "tie": []}
    for _ in range(rounds):
        sample = [outcomes[rng.randrange(n)] for _ in range(n)]
        rates = _win_rates(sample, label_a=label_a, label_b=label_b)
        for key, value in rates.items():
            traces[key].append(value)

    intervals = {}
    for key, values in traces.items():
        values.sort()
        intervals[key] = tuple(round(bound, 4) for bound in _quantile_interval(values, alpha=alpha))
    return intervals


def _estimate_target_sample_size(*, effect_size: float, alpha: float) -> int:
    """Estimate a rough paired sample size target for 80% power."""
    magnitude = max(abs(effect_size), 0.05)
    z_alpha = 1.96 if alpha <= 0.05 else 1.64
    z_beta = 0.84  # ~80% power
    estimate = ((z_alpha + z_beta) / magnitude) ** 2
    return int(min(max(8, math.ceil(estimate)), 5000))

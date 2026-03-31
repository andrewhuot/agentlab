"""Tests for pairwise comparison statistical analysis."""

from __future__ import annotations


def test_pairwise_stats_identify_a_significant_winner() -> None:
    """Strong pairwise lifts should register as statistically meaningful."""
    from evals.pairwise_stats import analyze_pairwise_scores

    analysis = analyze_pairwise_scores(
        label_a="v001",
        label_b="v002",
        left_scores=[0.31, 0.34, 0.29, 0.33, 0.32, 0.30, 0.35, 0.31],
        right_scores=[0.82, 0.86, 0.80, 0.84, 0.81, 0.85, 0.87, 0.83],
        outcomes=["v002", "v002", "v002", "v002", "v002", "v002", "v002", "v002"],
        alpha=0.05,
        iterations=800,
        seed=19,
    )

    assert analysis.winner == "v002"
    assert analysis.is_significant is True
    assert analysis.p_value < 0.05
    assert analysis.effect_size > 1.0
    assert analysis.recommended_additional_cases == 0
    assert analysis.win_rate_confidence_intervals["v002"][0] > 0.7


def test_pairwise_stats_recommend_more_samples_when_results_are_inconclusive() -> None:
    """Small deltas should stay honest and request more data."""
    from evals.pairwise_stats import analyze_pairwise_scores

    analysis = analyze_pairwise_scores(
        label_a="v001",
        label_b="v002",
        left_scores=[0.60, 0.61, 0.59, 0.60, 0.61, 0.60, 0.59, 0.60],
        right_scores=[0.61, 0.60, 0.60, 0.60, 0.61, 0.60, 0.60, 0.60],
        outcomes=["v002", "v001", "v002", "tie", "tie", "tie", "v002", "v001"],
        alpha=0.05,
        iterations=800,
        seed=19,
    )

    assert analysis.is_significant is False
    assert analysis.recommended_additional_cases > 0
    assert analysis.summary_message.lower().startswith("results are inconclusive")

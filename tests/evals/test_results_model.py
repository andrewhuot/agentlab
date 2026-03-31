"""Tests for the structured eval results data model."""

from __future__ import annotations

from evals.runner import TestCase as EvalTestCase
from evals.scorer import CompositeScore, EvalResult


def test_result_set_from_score_preserves_examples_and_metric_summaries() -> None:
    """Structured results should keep full example context plus aggregate stats."""
    from evals.results_model import EvalResultSet

    cases = [
        EvalTestCase(
            id="case-orders",
            category="happy_path",
            user_message="Where is my order?",
            expected_specialist="orders",
            expected_behavior="answer",
            expected_keywords=["order"],
        ),
        EvalTestCase(
            id="case-routing",
            category="regression",
            user_message="Connect me with billing",
            expected_specialist="billing",
            expected_behavior="route_correctly",
        ),
    ]
    score = CompositeScore(
        quality=0.7,
        safety=1.0,
        latency=0.92,
        cost=0.88,
        composite=0.83,
        total_cases=2,
        passed_cases=1,
        safety_failures=0,
        results=[
          EvalResult(
              case_id="case-orders",
              category="happy_path",
              passed=True,
              quality_score=0.95,
              safety_passed=True,
              latency_ms=140.0,
              token_count=120,
              details="",
              input_payload={"user_message": "Where is my order?"},
              expected_payload={"expected_specialist": "orders"},
              actual_output={"response": "Your order is on the way.", "specialist_used": "orders"},
              failure_reasons=[],
          ),
          EvalResult(
              case_id="case-routing",
              category="regression",
              passed=False,
              quality_score=0.45,
              safety_passed=True,
              latency_ms=90.0,
              token_count=80,
              details="routing mismatch",
              input_payload={"user_message": "Connect me with billing"},
              expected_payload={"expected_specialist": "billing"},
              actual_output={"response": "Support can help with that.", "specialist_used": "support"},
              failure_reasons=["routing mismatch"],
          ),
        ],
    )

    result_set = EvalResultSet.from_score(
        run_id="run-results-1",
        score=score,
        cases=cases,
        mode="mock",
        config_snapshot={"variant": "v001"},
    )

    assert result_set.run_id == "run-results-1"
    assert result_set.summary.total == 2
    assert result_set.summary.passed == 1
    assert result_set.summary.failed == 1
    assert result_set.examples[0].input["user_message"] == "Where is my order?"
    assert result_set.examples[1].actual["response"] == "Support can help with that."
    assert result_set.examples[1].failure_reasons == ["routing mismatch"]
    assert "quality" in result_set.summary.metrics
    assert len(result_set.summary.metrics["quality"].histogram) == 10

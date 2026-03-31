"""Tests for the canonical eval object model."""

from __future__ import annotations

from core.eval_model import (
    Annotation,
    Dataset,
    Evaluation,
    EvaluationRun,
    Grader,
    GraderKind,
    GraderResult,
    RunResult,
)
from core.types import GraderSpec, GraderType
from evals.runner import TestCase as LegacyTestCase
from evals.scorer_spec import ScorerDimension
from rewards.types import RewardDefinition, RewardSource


def test_dataset_from_test_cases_round_trips_with_versioned_payload() -> None:
    """Legacy TestCase objects should serialize into a versioned Dataset."""

    cases = [
        LegacyTestCase(
            id="case-1",
            category="happy_path",
            user_message="Where is my order?",
            expected_specialist="orders",
            expected_behavior="answer",
            expected_keywords=["order", "status"],
            split="test",
            reference_answer="Your order is in transit.",
        )
    ]

    dataset = Dataset.from_test_cases(
        name="support-regression",
        cases=cases,
        source_ref="evals/cases/support.yaml",
    )
    restored = Dataset.from_dict(dataset.to_dict())

    assert dataset.version
    assert dataset.case_count == 1
    assert restored.dataset_id == dataset.dataset_id
    assert restored.version == dataset.version
    assert restored.cases[0]["case_id"] == "case-1"
    assert restored.cases[0]["task"] == "Where is my order?"
    assert restored.content_hash == dataset.content_hash


def test_grader_from_legacy_wraps_existing_scoring_shapes() -> None:
    """Existing scorer, judge, and reward definitions should map to Grader."""

    grader_spec = GraderSpec(
        grader_type=GraderType.deterministic,
        grader_id="exact_match",
        config={"assertions": {"contains": ["tracking"]}},
        weight=0.8,
        required=True,
    )
    scorer_dimension = ScorerDimension(
        name="quality",
        description="Semantic quality",
        grader_type="similarity",
        grader_config={"threshold": 0.7},
        weight=0.6,
    )
    reward_definition = RewardDefinition(
        name="human-escalation",
        source=RewardSource.human_label,
        hard_gate=True,
        weight=1.2,
    )

    from_spec = Grader.from_legacy(grader_spec)
    from_dimension = Grader.from_legacy(scorer_dimension)
    from_reward = Grader.from_legacy(reward_definition)

    assert from_spec.grader_type == GraderKind.deterministic
    assert from_spec.required is True
    assert from_spec.weight == 0.8

    assert from_dimension.grader_type == GraderKind.similarity
    assert from_dimension.config["threshold"] == 0.7
    assert from_dimension.metadata["source_layer"] == "outcome"

    assert from_reward.grader_type == GraderKind.human
    assert from_reward.required is True
    assert from_reward.weight == 1.2


def test_evaluation_run_round_trip_preserves_results_and_annotations() -> None:
    """Canonical run payloads should keep nested grader results intact."""

    grader = Grader(
        grader_id="routing_accuracy",
        grader_type=GraderKind.classification,
        config={"expected_field": "expected_label", "predicted_field": "predicted_label"},
    )
    evaluation = Evaluation(
        evaluation_id="eval-routing",
        name="Routing regression",
        dataset_ref="dataset-routing",
        dataset_version="v1",
        metrics=["routing_accuracy"],
        graders=[grader],
    )
    grader_result = GraderResult(
        grader_id="routing_accuracy",
        grader_type=GraderKind.classification,
        example_id="case-1",
        score=1.0,
        passed=True,
        reasoning="Predicted label matched the expected specialist.",
        label="orders",
    )
    annotation = Annotation(
        target_id=grader_result.result_id,
        target_type="grader_result",
        author="reviewer@example.com",
        score_override=0.9,
        notes="Human reviewer accepted the automated routing verdict.",
    )
    run_result = RunResult.from_example_results(
        evaluation_id=evaluation.evaluation_id,
        per_example_results=[
            {
                "example_id": "case-1",
                "score": 1.0,
                "passed": True,
                "grader_results": [grader_result],
                "metadata": {"category": "routing"},
            }
        ],
        annotations=[annotation],
        warnings=["manual audit completed"],
    )
    evaluation_run = EvaluationRun(
        run_id="run-routing",
        evaluation_id=evaluation.evaluation_id,
        dataset_ref=evaluation.dataset_ref,
        dataset_version=evaluation.dataset_version,
        config_snapshot={"candidate": "v2"},
        result=run_result,
        mode="live",
    )

    restored = EvaluationRun.from_dict(evaluation_run.to_dict())

    assert restored.run_id == "run-routing"
    assert restored.result.summary_stats["total_examples"] == 1
    assert restored.result.summary_stats["pass_rate"] == 1.0
    assert restored.result.per_example_results[0]["grader_results"][0].reasoning.startswith(
        "Predicted label matched"
    )
    assert restored.result.annotations[0].notes.startswith("Human reviewer accepted")

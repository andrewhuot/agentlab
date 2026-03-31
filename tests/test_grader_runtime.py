"""Tests for the canonical unified grader runtime."""

from __future__ import annotations

import asyncio

from core.eval_model import Grader, GraderKind
from evals.grader_runtime import GraderRuntime


def test_grader_runtime_runs_supported_grader_types() -> None:
    """Each supported grader type should produce a canonical GraderResult."""

    runtime = GraderRuntime()

    deterministic = runtime.run_sync(
        Grader(
            grader_id="contains_tracking",
            grader_type=GraderKind.deterministic,
            config={"assertions": {"contains": ["tracking"]}},
        ),
        {
            "example_id": "case-det",
            "response_text": "Your tracking number is ready.",
        },
    )
    regex = runtime.run_sync(
        Grader(
            grader_id="order_id_present",
            grader_type=GraderKind.regex,
            config={"pattern": r"ORD-\d+"},
        ),
        {
            "example_id": "case-regex",
            "response_text": "I found order ORD-12345 in the queue.",
        },
    )
    similarity = runtime.run_sync(
        Grader(
            grader_id="reference_match",
            grader_type=GraderKind.similarity,
            config={"reference_text": "Order shipped yesterday", "threshold": 0.3},
        ),
        {
            "example_id": "case-sim",
            "response_text": "Your order shipped yesterday and is in transit.",
        },
    )
    llm_judge = runtime.run_sync(
        Grader(
            grader_id="answer_quality",
            grader_type=GraderKind.llm_judge,
            config={"pass_threshold": 0.5, "model_family": "anthropic"},
        ),
        {
            "example_id": "case-judge",
            "user_message": "How do I reset my password?",
            "response_text": "Use the reset link in your email to reset your password safely.",
            "reference_text": "Reset your password with the email reset link.",
            "agent_model_family": "openai",
        },
    )
    pairwise = runtime.run_sync(
        Grader(
            grader_id="better_than_baseline",
            grader_type=GraderKind.pairwise,
            config={"criteria": {"correctness": ["reset link", "password"]}},
        ),
        {
            "example_id": "case-pairwise",
            "input_text": "How do I reset my password?",
            "candidate_response": "Use the reset link in your email to reset your password safely.",
            "baseline_response": "I do not know.",
        },
    )
    composite = runtime.run_sync(
        Grader(
            grader_id="routing_and_keywords",
            grader_type=GraderKind.composite,
            children=[
                Grader(
                    grader_id="routing",
                    grader_type=GraderKind.classification,
                    config={"expected_field": "expected_label", "predicted_field": "predicted_label"},
                    required=True,
                ),
                Grader(
                    grader_id="keywords",
                    grader_type=GraderKind.deterministic,
                    config={"assertions": {"contains": ["tracking"]}},
                ),
            ],
        ),
        {
            "example_id": "case-composite",
            "expected_label": "orders",
            "predicted_label": "orders",
            "response_text": "Your tracking update is available now.",
        },
    )
    human = runtime.run_sync(
        Grader(
            grader_id="human_review",
            grader_type=GraderKind.human,
        ),
        {
            "example_id": "case-human",
            "human_score": 0.85,
            "human_passed": True,
            "human_reasoning": "The answer is accurate and appropriately scoped.",
        },
    )
    classification = runtime.run_sync(
        Grader(
            grader_id="route_match",
            grader_type=GraderKind.classification,
            config={"expected_field": "expected_label", "predicted_field": "predicted_label"},
        ),
        {
            "example_id": "case-classification",
            "expected_label": "orders",
            "predicted_label": "orders",
        },
    )

    assert deterministic.passed is True
    assert regex.passed is True
    assert similarity.passed is True
    assert llm_judge.score >= 0.5
    assert pairwise.passed is True
    assert composite.passed is True
    assert composite.metadata["child_results"]
    assert human.reasoning.startswith("The answer is accurate")
    assert classification.label == "orders"


def test_grader_runtime_supports_async_batch_execution() -> None:
    """Batch execution should return one canonical result per example."""

    runtime = GraderRuntime()
    grader = Grader(
        grader_id="route_match",
        grader_type=GraderKind.classification,
        config={"expected_field": "expected_label", "predicted_field": "predicted_label"},
    )

    results = asyncio.run(
        runtime.run_many(
            grader,
            [
                {"example_id": "case-1", "expected_label": "orders", "predicted_label": "orders"},
                {"example_id": "case-2", "expected_label": "support", "predicted_label": "orders"},
            ],
        )
    )

    assert [item.example_id for item in results] == ["case-1", "case-2"]
    assert results[0].passed is True
    assert results[1].passed is False

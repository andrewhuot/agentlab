"""Unit tests for the simplified graders hierarchy."""

from __future__ import annotations

import pytest

from graders import (
    BinaryRubricJudge,
    CalibrationTracker,
    DeterministicGrader,
    GraderStack,
    LLMJudgeConfig,
    SimilarityGrader,
)


def test_deterministic_grader_assertions() -> None:
    grader = DeterministicGrader()
    result = grader.grade(
        response_text="Your order has shipped and tracking is available.",
        assertions={"contains": ["shipped"], "not_contains": ["password"]},
    )
    assert result.passed is True
    assert result.score == 1.0


def test_similarity_grader_exact_match() -> None:
    grader = SimilarityGrader()
    result = grader.grade("Order shipped tomorrow", "Order shipped tomorrow")
    assert result.passed is True
    assert result.score == 1.0


def test_llm_judge_requires_different_model_family() -> None:
    judge = BinaryRubricJudge(config=LLMJudgeConfig(model_family="google"))
    with pytest.raises(ValueError):
        judge.grade(
            user_message="Where is my order?",
            response_text="It shipped.",
            agent_model_family="google",
        )


def test_llm_judge_majority_vote_runs() -> None:
    judge = BinaryRubricJudge(
        config=LLMJudgeConfig(model_family="anthropic", majority_vote=True)
    )
    result = judge.grade(
        user_message="Where is my order?",
        response_text="Your order shipped yesterday.",
        agent_model_family="google",
    )
    assert 0.0 <= result.score <= 1.0
    assert isinstance(result.passed, bool)
    assert "votes" in result.details


def test_grader_stack_short_circuits_on_failed_deterministic() -> None:
    stack = GraderStack()
    grade = stack.grade(
        user_message="Where is my order?",
        response_text="I cannot help.",
        case={"assertions": {"contains": ["tracking number"]}},
    )
    assert grade.stage == "deterministic"
    assert grade.passed is False


def test_calibration_tracker_agreement_and_drift(tmp_path) -> None:
    tracker = CalibrationTracker(db_path=str(tmp_path / "calibration.db"))
    tracker.record("c1", judge_score=1.0, human_label=1.0)
    tracker.record("c2", judge_score=0.0, human_label=1.0)
    assert tracker.agreement_rate() == 0.5
    drift = tracker.drift()
    assert isinstance(drift, float)

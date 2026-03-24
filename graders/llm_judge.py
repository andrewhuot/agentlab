"""Binary-rubric LLM judge layer with optional majority voting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .deterministic import GradeResult


@dataclass
class LLMJudgeConfig:
    """Configuration for the binary-rubric judge."""

    model_family: str = "anthropic"
    pass_threshold: float = 0.75
    majority_vote: bool = False


class BinaryRubricJudge:
    """Judge responses using fixed yes/no rubric questions.

    This is the DEFAULT routine judge. Uses binary rubric questions
    (yes/no) rather than 1-5 scales. CC's existing judges/llm_judge.py
    (evidence spans, full analysis) is the PROMOTION judge used only
    for final deployment decisions.
    """

    RUBRIC_QUESTIONS = (
        "answered_question",
        "factually_incorrect",
        "unnecessary_caveats",
        "human_would_handle_differently",
    )

    def __init__(self, config: LLMJudgeConfig | None = None) -> None:
        self.config = config or LLMJudgeConfig()

    def grade(
        self,
        *,
        user_message: str,
        response_text: str,
        reference_text: str = "",
        agent_model_family: str | None = None,
        evaluator: Callable[[str, str, str], dict[str, bool]] | None = None,
    ) -> GradeResult:
        """Run single-vote or 3x majority vote rubric judging."""
        self._validate_model_family(agent_model_family)

        if self.config.majority_vote:
            votes = [
                self._single_vote(user_message, response_text, reference_text, evaluator)
                for _ in range(3)
            ]
            passed_votes = sum(1 for vote in votes if vote.passed)
            score = sum(vote.score for vote in votes) / len(votes)
            return GradeResult(
                score=round(score, 4),
                passed=passed_votes >= 2,
                grader="llm_judge",
                details={"votes": [vote.details for vote in votes]},
            )

        return self._single_vote(user_message, response_text, reference_text, evaluator)

    def _single_vote(
        self,
        user_message: str,
        response_text: str,
        reference_text: str,
        evaluator: Callable[[str, str, str], dict[str, bool]] | None,
    ) -> GradeResult:
        if evaluator is not None:
            answers = evaluator(user_message, response_text, reference_text)
        else:
            answers = self._heuristic_answers(user_message, response_text, reference_text)

        good_answers = 0
        total = len(self.RUBRIC_QUESTIONS)
        normalized: dict[str, bool] = {}
        for question in self.RUBRIC_QUESTIONS:
            value = bool(answers.get(question, False))
            normalized[question] = value
            if question == "answered_question":
                good_answers += 1 if value else 0
            else:
                # For the remaining questions, "False" is desirable.
                good_answers += 1 if not value else 0

        score = good_answers / total if total else 0.0
        return GradeResult(
            score=round(score, 4),
            passed=score >= self.config.pass_threshold,
            grader="llm_judge",
            details={"rubric": normalized},
        )

    def _validate_model_family(self, agent_model_family: str | None) -> None:
        if agent_model_family and agent_model_family == self.config.model_family:
            raise ValueError(
                "Judge model family must differ from agent/proposer model family."
            )

    @staticmethod
    def _heuristic_answers(
        user_message: str,
        response_text: str,
        reference_text: str,
    ) -> dict[str, bool]:
        response_lower = (response_text or "").lower()
        user_lower = (user_message or "").lower()
        answered = len(response_text.strip()) > 0 and (
            any(token in response_lower for token in user_lower.split()[:3]) or len(response_text.split()) > 3
        )
        factually_incorrect = False
        unnecessary_caveats = response_lower.count("cannot") > 1 or response_lower.count("i might be wrong") > 0
        human_would_differ = len(response_text.strip()) < 4
        if reference_text:
            factually_incorrect = reference_text.lower() not in response_lower and answered

        return {
            "answered_question": answered,
            "factually_incorrect": factually_incorrect,
            "unnecessary_caveats": unnecessary_caveats,
            "human_would_handle_differently": human_would_differ,
        }

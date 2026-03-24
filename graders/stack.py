"""Ordered grading stack: deterministic -> similarity -> LLM judge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .deterministic import DeterministicGrader, GradeResult
from .llm_judge import BinaryRubricJudge
from .similarity import SimilarityGrader


@dataclass
class StackGrade:
    """Result payload from the ordered grader stack."""

    score: float
    passed: bool
    stage: str
    details: dict[str, Any]


class GraderStack:
    """Execute ordered grading, using the simplest layer that works."""

    def __init__(
        self,
        deterministic: DeterministicGrader | None = None,
        similarity: SimilarityGrader | None = None,
        llm_judge: BinaryRubricJudge | None = None,
    ) -> None:
        self.deterministic = deterministic or DeterministicGrader()
        self.similarity = similarity or SimilarityGrader()
        self.llm_judge = llm_judge or BinaryRubricJudge()

    def grade(
        self,
        *,
        user_message: str,
        response_text: str,
        case: dict[str, Any],
        tool_calls: list[dict[str, Any]] | None = None,
        status_code: int | None = None,
        agent_model_family: str | None = None,
    ) -> StackGrade:
        """Apply deterministic checks first, then similarity, then LLM judge."""
        assertions = case.get("assertions") or {}
        if assertions:
            det = self.deterministic.grade(
                response_text=response_text,
                assertions=assertions,
                tool_calls=tool_calls,
                status_code=status_code,
            )
            if not det.passed:
                return self._to_stack_grade(det, stage="deterministic")

        reference = str(case.get("reference_answer") or "")
        if reference:
            sim = self.similarity.grade(response_text=response_text, reference_text=reference)
            if sim.passed:
                return self._to_stack_grade(sim, stage="similarity")

        judge = self.llm_judge.grade(
            user_message=user_message,
            response_text=response_text,
            reference_text=reference,
            agent_model_family=agent_model_family,
        )
        return self._to_stack_grade(judge, stage="llm_judge")

    @staticmethod
    def _to_stack_grade(result: GradeResult, stage: str) -> StackGrade:
        return StackGrade(
            score=result.score,
            passed=result.passed,
            stage=stage,
            details=result.details,
        )

"""Semantic similarity grader (lightweight token overlap baseline)."""

from __future__ import annotations

import re

from .deterministic import GradeResult


class SimilarityGrader:
    """Compute semantic similarity against reference text."""

    def __init__(self, threshold: float = 0.65) -> None:
        self.threshold = threshold

    def grade(self, response_text: str, reference_text: str) -> GradeResult:
        if not reference_text:
            return GradeResult(score=0.0, passed=False, grader="similarity")
        response_tokens = self._tokenize(response_text)
        reference_tokens = self._tokenize(reference_text)
        if not response_tokens or not reference_tokens:
            return GradeResult(score=0.0, passed=False, grader="similarity")

        overlap = response_tokens & reference_tokens
        union = response_tokens | reference_tokens
        score = len(overlap) / len(union) if union else 0.0
        return GradeResult(
            score=round(score, 4),
            passed=score >= self.threshold,
            grader="similarity",
        )

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return {token for token in re.findall(r"[a-zA-Z0-9]+", (text or "").lower())}

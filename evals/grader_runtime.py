"""Unified grader runtime for canonical eval definitions.

This runtime is intentionally adapter-friendly. It can execute the new
canonical :class:`core.eval_model.Grader` objects directly while still
reusing the existing deterministic graders and judges already present in
the codebase.
"""

from __future__ import annotations

import asyncio
from typing import Any, Mapping

from core.eval_model import Grader, GraderKind, GraderResult
from graders import BinaryRubricJudge, DeterministicGrader, LLMJudgeConfig, SimilarityGrader
from judges.audit_judge import AuditJudge
from judges.deterministic import DeterministicJudge
from judges.pairwise import PairwiseJudge
from judges.rule_based import RuleBasedJudge


class GraderRuntime:
    """Single runtime that executes any supported grader type.

    WHY: Eval definitions should not care whether a score came from a
    deterministic assertion, a pairwise comparison, or a human review.
    This runtime gives the rest of the system one execution interface.
    """

    def __init__(
        self,
        *,
        deterministic_grader: DeterministicGrader | None = None,
        regex_judge: DeterministicJudge | None = None,
        pairwise_judge: PairwiseJudge | None = None,
        rule_based_judge: RuleBasedJudge | None = None,
        audit_judge: AuditJudge | None = None,
    ) -> None:
        self.deterministic_grader = deterministic_grader or DeterministicGrader()
        self.regex_judge = regex_judge or DeterministicJudge()
        self.pairwise_judge = pairwise_judge or PairwiseJudge()
        self.rule_based_judge = rule_based_judge or RuleBasedJudge()
        self.audit_judge = audit_judge or AuditJudge()

    def run_sync(self, grader: Grader, example: Mapping[str, Any]) -> GraderResult:
        """Synchronously execute one grader against one example."""

        return self._run(grader, dict(example))

    async def run(self, grader: Grader, example: Mapping[str, Any]) -> GraderResult:
        """Asynchronously execute one grader against one example."""

        return self._run(grader, dict(example))

    async def run_many(
        self,
        grader: Grader,
        examples: list[Mapping[str, Any]],
        *,
        batch_size: int | None = None,
    ) -> list[GraderResult]:
        """Execute a grader over many examples.

        The implementation uses ``asyncio.gather`` so callers can batch
        sync and async grader types through the same API.
        """

        del batch_size  # Reserved for future transport-aware implementations.
        return list(await asyncio.gather(*(self.run(grader, example) for example in examples)))

    def _run(self, grader: Grader, example: dict[str, Any]) -> GraderResult:
        """Dispatch execution to the canonical implementation for each type."""

        grader_type = grader.grader_type

        if grader_type == GraderKind.deterministic:
            return self._run_deterministic(grader, example)
        if grader_type == GraderKind.regex:
            return self._run_regex(grader, example)
        if grader_type == GraderKind.similarity:
            return self._run_similarity(grader, example)
        if grader_type == GraderKind.llm_judge:
            return self._run_llm_judge(grader, example)
        if grader_type == GraderKind.pairwise:
            return self._run_pairwise(grader, example)
        if grader_type == GraderKind.composite:
            return self._run_composite(grader, example)
        if grader_type == GraderKind.human:
            return self._run_human(grader, example)
        if grader_type == GraderKind.classification:
            return self._run_classification(grader, example)
        if grader_type == GraderKind.rule_based:
            return self._run_rule_based(grader, example)
        if grader_type == GraderKind.audit_judge:
            return self._run_audit(grader, example)

        raise ValueError(f"Unsupported grader type: {grader_type}")

    def _run_deterministic(self, grader: Grader, example: dict[str, Any]) -> GraderResult:
        """Run deterministic assertions against the example response."""

        config = grader.config or {}
        assertions = dict(config.get("assertions", {}) or {})
        if not assertions:
            assertions = {
                "contains": list(config.get("contains", []) or []),
                "not_contains": list(config.get("not_contains", []) or []),
            }
            if config.get("expected_tool"):
                assertions["expected_tool"] = config["expected_tool"]
            if config.get("status_code") is not None:
                assertions["status_code"] = config["status_code"]

        raw_result = self.deterministic_grader.grade(
            response_text=self._response_text(example),
            assertions=assertions,
            tool_calls=self._tool_calls(example),
            status_code=self._status_code(example),
        )
        reasoning = (
            "Deterministic assertions passed."
            if raw_result.passed
            else "Deterministic assertions failed."
        )
        return GraderResult(
            grader_id=grader.grader_id,
            grader_type=grader.grader_type,
            example_id=self._example_id(example),
            score=raw_result.score,
            passed=raw_result.passed,
            reasoning=reasoning,
            metadata=raw_result.details,
        )

    def _run_regex(self, grader: Grader, example: dict[str, Any]) -> GraderResult:
        """Run regex matching against the response text."""

        pattern = str(grader.config.get("pattern") or grader.config.get("regex") or "")
        verdict = self.regex_judge.check_regex(pattern, self._response_text(example))
        reasoning = (
            f"Regex matched pattern '{pattern}'."
            if verdict.passed
            else "; ".join(verdict.failure_reasons) or f"Regex did not match '{pattern}'."
        )
        return GraderResult(
            grader_id=grader.grader_id,
            grader_type=grader.grader_type,
            example_id=self._example_id(example),
            score=verdict.score,
            passed=verdict.passed,
            reasoning=reasoning,
            confidence=verdict.confidence,
            metadata=verdict.metadata,
        )

    def _run_similarity(self, grader: Grader, example: dict[str, Any]) -> GraderResult:
        """Run semantic similarity scoring against a reference answer."""

        threshold = float(grader.config.get("threshold", 0.65))
        reference_text = str(
            grader.config.get("reference_text")
            or example.get("reference_text")
            or example.get("reference_answer")
            or ""
        )
        raw_result = SimilarityGrader(threshold=threshold).grade(
            response_text=self._response_text(example),
            reference_text=reference_text,
        )
        reasoning = (
            f"Similarity score {raw_result.score:.4f} met threshold {threshold:.2f}."
            if raw_result.passed
            else f"Similarity score {raw_result.score:.4f} fell below threshold {threshold:.2f}."
        )
        return GraderResult(
            grader_id=grader.grader_id,
            grader_type=grader.grader_type,
            example_id=self._example_id(example),
            score=raw_result.score,
            passed=raw_result.passed,
            reasoning=reasoning,
            metadata={"threshold": threshold},
        )

    def _run_llm_judge(self, grader: Grader, example: dict[str, Any]) -> GraderResult:
        """Run the lightweight LLM-judge layer."""

        config = LLMJudgeConfig(
            model_family=str(grader.config.get("model_family", "anthropic")),
            pass_threshold=float(grader.config.get("pass_threshold", 0.75)),
            majority_vote=bool(grader.config.get("majority_vote", False)),
        )
        raw_result = BinaryRubricJudge(config=config).grade(
            user_message=str(
                example.get("user_message")
                or example.get("task")
                or example.get("input_text")
                or ""
            ),
            response_text=self._response_text(example),
            reference_text=str(
                grader.config.get("reference_text")
                or example.get("reference_text")
                or example.get("reference_answer")
                or ""
            ),
            agent_model_family=(
                str(example["agent_model_family"])
                if example.get("agent_model_family") is not None
                else None
            ),
        )
        reasoning = (
            f"LLM judge accepted the answer with score {raw_result.score:.4f}."
            if raw_result.passed
            else f"LLM judge rejected the answer with score {raw_result.score:.4f}."
        )
        return GraderResult(
            grader_id=grader.grader_id,
            grader_type=grader.grader_type,
            example_id=self._example_id(example),
            score=raw_result.score,
            passed=raw_result.passed,
            reasoning=reasoning,
            metadata=raw_result.details,
        )

    def _run_pairwise(self, grader: Grader, example: dict[str, Any]) -> GraderResult:
        """Compare a candidate answer against a baseline answer."""

        allow_ties = bool(grader.config.get("allow_ties", False))
        comparison = self.pairwise_judge.compare(
            input_text=str(example.get("input_text") or example.get("user_message") or ""),
            response_a=str(example.get("candidate_response") or self._response_text(example)),
            response_b=str(example.get("baseline_response") or example.get("comparison_response") or ""),
            criteria=dict(grader.config.get("criteria", {}) or {}),
        )
        passed = comparison.winner == "a" or (allow_ties and comparison.winner == "tie")
        score_map = {"a": 1.0, "tie": 0.5, "b": 0.0}
        return GraderResult(
            grader_id=grader.grader_id,
            grader_type=grader.grader_type,
            example_id=self._example_id(example),
            score=score_map.get(comparison.winner, 0.0),
            passed=passed,
            reasoning=comparison.reasoning,
            confidence=comparison.confidence,
            label=comparison.winner,
            metadata={"comparison": comparison.to_dict(), "allow_ties": allow_ties},
        )

    def _run_composite(self, grader: Grader, example: dict[str, Any]) -> GraderResult:
        """Aggregate child graders into one composite verdict."""

        children = grader.children or [
            Grader.from_dict(item)
            for item in grader.config.get("graders", []) or []
        ]
        child_results = [self._run(child, example) for child in children]
        total_weight = sum(max(child.weight, 0.0) for child in children) or float(len(child_results) or 1)
        weighted_score = 0.0
        for child, result in zip(children, child_results, strict=False):
            weight = max(child.weight, 0.0) or 1.0
            weighted_score += result.score * weight

        score = weighted_score / total_weight if child_results else 0.0
        required_failed = any(
            not result.passed
            for child, result in zip(children, child_results, strict=False)
            if child.required
        )
        pass_threshold = float(grader.config.get("pass_threshold", 0.5))
        passed = bool(child_results) and score >= pass_threshold and not required_failed
        reasoning = (
            f"Composite grader aggregated {len(child_results)} child results."
            if child_results
            else "Composite grader has no child graders configured."
        )
        return GraderResult(
            grader_id=grader.grader_id,
            grader_type=grader.grader_type,
            example_id=self._example_id(example),
            score=round(score, 4),
            passed=passed,
            reasoning=reasoning,
            metadata={
                "pass_threshold": pass_threshold,
                "required_failed": required_failed,
                "child_results": [result.to_dict() for result in child_results],
            },
        )

    def _run_human(self, grader: Grader, example: dict[str, Any]) -> GraderResult:
        """Project human annotations into the canonical result schema."""

        pending_default = bool(grader.config.get("pending_is_failure", True))
        score = example.get("human_score")
        if score is None:
            reasoning = str(grader.config.get("pending_reasoning", "Pending human review."))
            return GraderResult(
                grader_id=grader.grader_id,
                grader_type=grader.grader_type,
                example_id=self._example_id(example),
                score=0.0,
                passed=not pending_default,
                reasoning=reasoning,
                metadata={"status": "pending"},
            )

        numeric_score = float(score)
        passed = bool(example.get("human_passed", numeric_score >= float(grader.config.get("pass_threshold", 0.5))))
        reasoning = str(example.get("human_reasoning") or grader.config.get("reasoning") or "Human review completed.")
        return GraderResult(
            grader_id=grader.grader_id,
            grader_type=grader.grader_type,
            example_id=self._example_id(example),
            score=round(numeric_score, 4),
            passed=passed,
            reasoning=reasoning,
            metadata={"status": "completed"},
        )

    def _run_classification(self, grader: Grader, example: dict[str, Any]) -> GraderResult:
        """Compare predicted and expected labels."""

        expected_field = str(grader.config.get("expected_field", "expected_label"))
        predicted_field = str(grader.config.get("predicted_field", "predicted_label"))
        expected_label = grader.config.get("expected_label", example.get(expected_field))
        predicted_label = grader.config.get("predicted_label", example.get(predicted_field))
        passed = (
            expected_label is not None
            and predicted_label is not None
            and str(expected_label).strip().lower() == str(predicted_label).strip().lower()
        )
        reasoning = (
            f"Predicted label matched expected label '{expected_label}'."
            if passed
            else f"Predicted label '{predicted_label}' did not match expected label '{expected_label}'."
        )
        return GraderResult(
            grader_id=grader.grader_id,
            grader_type=grader.grader_type,
            example_id=self._example_id(example),
            score=1.0 if passed else 0.0,
            passed=passed,
            reasoning=reasoning,
            label=(str(predicted_label) if predicted_label is not None else None),
            metadata={
                "expected_label": expected_label,
                "predicted_label": predicted_label,
            },
        )

    def _run_rule_based(self, grader: Grader, example: dict[str, Any]) -> GraderResult:
        """Run the legacy rule-based judge through the canonical result shape."""

        rules = dict(grader.config.get("rules", {}) or {})
        verdict = self.rule_based_judge.check_format(self._response_text(example), rules)
        reasoning = (
            "Rule-based checks passed."
            if verdict.passed
            else "; ".join(verdict.failure_reasons) or "Rule-based checks failed."
        )
        return GraderResult(
            grader_id=grader.grader_id,
            grader_type=grader.grader_type,
            example_id=self._example_id(example),
            score=verdict.score,
            passed=verdict.passed,
            reasoning=reasoning,
            confidence=verdict.confidence,
            metadata=verdict.metadata,
        )

    def _run_audit(self, grader: Grader, example: dict[str, Any]) -> GraderResult:
        """Run the legacy audit judge using a primary verdict from the example."""

        primary = example.get("primary_verdict")
        if primary is None and example.get("primary_result") is not None:
            primary_result = example["primary_result"]
            if isinstance(primary_result, GraderResult):
                primary = {
                    "score": primary_result.score,
                    "passed": primary_result.passed,
                    "judge_id": primary_result.grader_id,
                    "confidence": primary_result.confidence,
                    "metadata": primary_result.metadata,
                    "evidence_spans": [],
                    "failure_reasons": [],
                }

        if not isinstance(primary, Mapping):
            return GraderResult(
                grader_id=grader.grader_id,
                grader_type=grader.grader_type,
                example_id=self._example_id(example),
                score=0.0,
                passed=False,
                reasoning="Audit judge requires a primary_verdict in the example context.",
                metadata={"status": "missing_primary_verdict"},
            )

        from core.types import JudgeVerdict

        verdict = self.audit_judge.audit(
            task=str(example.get("task") or example.get("user_message") or ""),
            response=self._response_text(example),
            primary_verdict=JudgeVerdict(
                score=float(primary.get("score", 0.0)),
                passed=bool(primary.get("passed", False)),
                judge_id=str(primary.get("judge_id", "primary")),
                evidence_spans=list(primary.get("evidence_spans", []) or []),
                failure_reasons=list(primary.get("failure_reasons", []) or []),
                confidence=float(primary.get("confidence", 1.0)),
                metadata=dict(primary.get("metadata", {}) or {}),
            ),
        )
        reasoning = (
            "Audit judge agreed with the primary verdict."
            if verdict.passed
            else "; ".join(verdict.failure_reasons) or "Audit judge flagged the primary verdict."
        )
        return GraderResult(
            grader_id=grader.grader_id,
            grader_type=grader.grader_type,
            example_id=self._example_id(example),
            score=verdict.score,
            passed=verdict.passed,
            reasoning=reasoning,
            confidence=verdict.confidence,
            metadata=verdict.metadata,
        )

    @staticmethod
    def _example_id(example: Mapping[str, Any]) -> str:
        """Return the stable example identifier used across grader results."""

        return str(example.get("example_id") or example.get("case_id") or "example")

    @staticmethod
    def _response_text(example: Mapping[str, Any]) -> str:
        """Extract response text from the example payload."""

        return str(example.get("response_text") or example.get("response") or "")

    @staticmethod
    def _tool_calls(example: Mapping[str, Any]) -> list[dict[str, Any]] | None:
        """Extract tool calls from the example payload."""

        tool_calls = example.get("tool_calls")
        return tool_calls if isinstance(tool_calls, list) else None

    @staticmethod
    def _status_code(example: Mapping[str, Any]) -> int | None:
        """Extract an optional HTTP status code from the example payload."""

        value = example.get("status_code")
        return int(value) if value is not None else None

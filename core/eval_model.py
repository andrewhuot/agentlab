"""Canonical eval object model shared across runner, API, and adapters.

The older codebase grew separate concepts for scorers, rewards, judges,
challenge suites, and human annotations. This module provides a single
language for those concepts so other layers can translate legacy payloads
without inventing new one-off schemas.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _now_iso() -> str:
    """Return a UTC timestamp for persisted canonical objects."""

    return datetime.now(timezone.utc).isoformat()


def _stable_hash(payload: Any) -> str:
    """Return a deterministic SHA256 hash for JSON-serializable content."""

    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _normalize_grader_kind(value: str | "GraderKind") -> "GraderKind":
    """Map legacy grader names onto the canonical enum.

    WHY: Existing modules use several closely related names such as
    ``human_review`` and ``rule_based``. The canonical model keeps one
    normalized enum while still accepting those legacy inputs.
    """

    if isinstance(value, GraderKind):
        return value

    normalized = str(value).strip().lower()
    alias_map = {
        "human_review": "human",
        "human_label": "human",
        "regex_match": "regex",
    }
    return GraderKind(alias_map.get(normalized, normalized))


class GraderKind(str, Enum):
    """Supported canonical grader types."""

    deterministic = "deterministic"
    regex = "regex"
    similarity = "similarity"
    llm_judge = "llm_judge"
    pairwise = "pairwise"
    composite = "composite"
    human = "human"
    classification = "classification"
    rule_based = "rule_based"
    audit_judge = "audit_judge"


@dataclass
class Dataset:
    """Versioned collection of evaluation examples."""

    dataset_id: str
    name: str
    version: str
    source_ref: str = ""
    cases: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def case_count(self) -> int:
        """Return the number of examples stored in the dataset."""

        return len(self.cases)

    @property
    def content_hash(self) -> str:
        """Return a deterministic hash over the dataset payload."""

        return _stable_hash(
            {
                "name": self.name,
                "version": self.version,
                "source_ref": self.source_ref,
                "cases": self.cases,
            }
        )[:16]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the dataset into a JSON-safe dict."""

        return {
            "dataset_id": self.dataset_id,
            "name": self.name,
            "version": self.version,
            "source_ref": self.source_ref,
            "cases": self.cases,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Dataset":
        """Deserialize a dataset from a plain dict."""

        return cls(
            dataset_id=str(data.get("dataset_id", f"dataset_{uuid.uuid4().hex[:12]}")),
            name=str(data.get("name", "dataset")),
            version=str(data.get("version", "v1")),
            source_ref=str(data.get("source_ref", "")),
            cases=list(data.get("cases", []) or []),
            metadata=dict(data.get("metadata", {}) or {}),
        )

    @classmethod
    def from_test_cases(
        cls,
        *,
        name: str,
        cases: list[Any],
        source_ref: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> "Dataset":
        """Convert legacy runner TestCase objects into a canonical Dataset."""

        normalized_cases = [cls._legacy_case_to_payload(case) for case in cases]
        dataset_hash = _stable_hash(
            {
                "name": name,
                "source_ref": source_ref,
                "cases": normalized_cases,
            }
        )
        return cls(
            dataset_id=f"dataset_{dataset_hash[:12]}",
            name=name,
            version=f"sha256:{dataset_hash[:12]}",
            source_ref=source_ref,
            cases=normalized_cases,
            metadata=dict(metadata or {}),
        )

    @staticmethod
    def _legacy_case_to_payload(case: Any) -> dict[str, Any]:
        """Project a legacy TestCase/EvalCase object into a canonical example."""

        payload = {
            "case_id": str(getattr(case, "id", getattr(case, "case_id", ""))),
            "task": str(getattr(case, "user_message", getattr(case, "task", ""))),
            "category": str(getattr(case, "category", "general")),
            "expected_specialist": getattr(case, "expected_specialist", None),
            "expected_behavior": getattr(case, "expected_behavior", None),
            "expected_keywords": list(getattr(case, "expected_keywords", []) or []),
            "expected_tool": getattr(case, "expected_tool", None),
            "reference_answer": getattr(case, "reference_answer", None),
            "safety_probe": bool(getattr(case, "safety_probe", False)),
            "split": getattr(case, "split", None),
        }
        return payload


@dataclass
class Grader:
    """Reusable grader definition that can wrap legacy scoring abstractions."""

    grader_id: str
    grader_type: GraderKind
    name: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    required: bool = False
    children: list["Grader"] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the grader definition into a JSON-safe dict."""

        return {
            "grader_id": self.grader_id,
            "grader_type": self.grader_type.value,
            "name": self.name,
            "config": self.config,
            "weight": self.weight,
            "required": self.required,
            "children": [child.to_dict() for child in self.children],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Grader":
        """Deserialize a grader from a plain dict."""

        return cls(
            grader_id=str(data.get("grader_id", "")),
            grader_type=_normalize_grader_kind(data.get("grader_type", "deterministic")),
            name=str(data.get("name", "")),
            config=dict(data.get("config", {}) or {}),
            weight=float(data.get("weight", 1.0)),
            required=bool(data.get("required", False)),
            children=[cls.from_dict(item) for item in data.get("children", []) or []],
            metadata=dict(data.get("metadata", {}) or {}),
        )

    @classmethod
    def from_legacy(cls, legacy: Any) -> "Grader":
        """Wrap an existing scorer/judge/reward object as a canonical grader.

        WHY: Migration to a single eval model has to preserve current entry
        points. This adapter accepts the shapes already used by the codebase
        instead of forcing every caller to migrate in one step.
        """

        if hasattr(legacy, "grader_type") and hasattr(legacy, "grader_id"):
            grader_type = getattr(legacy, "grader_type")
            kind_value = getattr(grader_type, "value", grader_type)
            return cls(
                grader_id=str(getattr(legacy, "grader_id")),
                grader_type=_normalize_grader_kind(kind_value),
                name=str(getattr(legacy, "grader_id")),
                config=dict(getattr(legacy, "config", {}) or {}),
                weight=float(getattr(legacy, "weight", 1.0)),
                required=bool(getattr(legacy, "required", False)),
                metadata={"source": "legacy_grader_spec"},
            )

        if hasattr(legacy, "grader_type") and hasattr(legacy, "name"):
            layer = getattr(legacy, "layer", "outcome")
            return cls(
                grader_id=str(getattr(legacy, "name")),
                grader_type=_normalize_grader_kind(getattr(legacy, "grader_type")),
                name=str(getattr(legacy, "name")),
                config=dict(getattr(legacy, "grader_config", {}) or {}),
                weight=float(getattr(legacy, "weight", 1.0)),
                required=bool(getattr(legacy, "required", False)),
                metadata={
                    "source": "legacy_scorer_dimension",
                    "source_layer": str(layer),
                    "description": str(getattr(legacy, "description", "")),
                },
            )

        if hasattr(legacy, "reward_id") and hasattr(legacy, "source"):
            source = getattr(legacy, "source")
            source_value = getattr(source, "value", source)
            source_to_kind = {
                "deterministic_checker": GraderKind.deterministic,
                "environment_checker": GraderKind.deterministic,
                "human_label": GraderKind.human,
                "llm_judge": GraderKind.llm_judge,
                "ai_preference": GraderKind.pairwise,
            }
            return cls(
                grader_id=str(getattr(legacy, "reward_id")),
                grader_type=source_to_kind.get(str(source_value), GraderKind.deterministic),
                name=str(getattr(legacy, "name", getattr(legacy, "reward_id", "reward"))),
                config={
                    "reward_kind": getattr(getattr(legacy, "kind", None), "value", getattr(legacy, "kind", "")),
                    "reward_scope": getattr(getattr(legacy, "scope", None), "value", getattr(legacy, "scope", "")),
                    "freshness_window_hours": float(getattr(legacy, "freshness_window_hours", 0.0)),
                },
                weight=float(getattr(legacy, "weight", 1.0)),
                required=bool(getattr(legacy, "hard_gate", False)),
                metadata={"source": "legacy_reward_definition"},
            )

        raise TypeError(f"Unsupported legacy grader shape: {type(legacy)!r}")


@dataclass
class GraderResult:
    """Canonical output for one grader on one example."""

    grader_id: str
    grader_type: GraderKind
    example_id: str
    score: float
    passed: bool
    reasoning: str = ""
    confidence: float = 1.0
    label: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    result_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def to_dict(self) -> dict[str, Any]:
        """Serialize the grader result into a JSON-safe dict."""

        return {
            "result_id": self.result_id,
            "grader_id": self.grader_id,
            "grader_type": self.grader_type.value,
            "example_id": self.example_id,
            "score": self.score,
            "passed": self.passed,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "label": self.label,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraderResult":
        """Deserialize a grader result from a plain dict."""

        return cls(
            grader_id=str(data.get("grader_id", "")),
            grader_type=_normalize_grader_kind(data.get("grader_type", "deterministic")),
            example_id=str(data.get("example_id", "")),
            score=float(data.get("score", 0.0)),
            passed=bool(data.get("passed", False)),
            reasoning=str(data.get("reasoning", "")),
            confidence=float(data.get("confidence", 1.0)),
            label=(str(data["label"]) if data.get("label") is not None else None),
            metadata=dict(data.get("metadata", {}) or {}),
            result_id=str(data.get("result_id", uuid.uuid4().hex[:12])),
        )


@dataclass
class Annotation:
    """Human override or note attached to a grader result or run."""

    target_id: str
    target_type: str
    author: str
    score_override: float | None = None
    label: str | None = None
    notes: str = ""
    created_at: str = field(default_factory=_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)
    annotation_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def to_dict(self) -> dict[str, Any]:
        """Serialize the annotation into a JSON-safe dict."""

        return {
            "annotation_id": self.annotation_id,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "author": self.author,
            "score_override": self.score_override,
            "label": self.label,
            "notes": self.notes,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Annotation":
        """Deserialize an annotation from a plain dict."""

        return cls(
            annotation_id=str(data.get("annotation_id", uuid.uuid4().hex[:12])),
            target_id=str(data.get("target_id", "")),
            target_type=str(data.get("target_type", "grader_result")),
            author=str(data.get("author", "")),
            score_override=(
                float(data["score_override"])
                if data.get("score_override") is not None
                else None
            ),
            label=(str(data["label"]) if data.get("label") is not None else None),
            notes=str(data.get("notes", "")),
            created_at=str(data.get("created_at", _now_iso())),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass
class Evaluation:
    """Reusable eval definition with dataset and grader references."""

    evaluation_id: str
    name: str
    dataset_ref: str
    dataset_version: str
    metrics: list[str] = field(default_factory=list)
    graders: list[Grader] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the evaluation definition into a JSON-safe dict."""

        return {
            "evaluation_id": self.evaluation_id,
            "name": self.name,
            "dataset_ref": self.dataset_ref,
            "dataset_version": self.dataset_version,
            "metrics": self.metrics,
            "graders": [grader.to_dict() for grader in self.graders],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Evaluation":
        """Deserialize an evaluation definition from a plain dict."""

        return cls(
            evaluation_id=str(data.get("evaluation_id", f"eval_{uuid.uuid4().hex[:12]}")),
            name=str(data.get("name", "evaluation")),
            dataset_ref=str(data.get("dataset_ref", "")),
            dataset_version=str(data.get("dataset_version", "")),
            metrics=list(data.get("metrics", []) or []),
            graders=[Grader.from_dict(item) for item in data.get("graders", []) or []],
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass
class RunResult:
    """Aggregated results for one evaluation run."""

    evaluation_id: str
    per_example_results: list[dict[str, Any]] = field(default_factory=list)
    summary_stats: dict[str, Any] = field(default_factory=dict)
    annotations: list[Annotation] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def to_dict(self) -> dict[str, Any]:
        """Serialize the run result into a JSON-safe dict."""

        serialized_examples: list[dict[str, Any]] = []
        for item in self.per_example_results:
            serialized_item = dict(item)
            serialized_item["grader_results"] = [
                result.to_dict() if isinstance(result, GraderResult) else GraderResult.from_dict(result).to_dict()
                for result in item.get("grader_results", []) or []
            ]
            serialized_examples.append(serialized_item)

        return {
            "run_id": self.run_id,
            "evaluation_id": self.evaluation_id,
            "per_example_results": serialized_examples,
            "summary_stats": self.summary_stats,
            "annotations": [annotation.to_dict() for annotation in self.annotations],
            "warnings": self.warnings,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunResult":
        """Deserialize a run result from a plain dict."""

        normalized_examples: list[dict[str, Any]] = []
        for item in data.get("per_example_results", []) or []:
            normalized = dict(item)
            normalized["grader_results"] = [
                GraderResult.from_dict(result)
                for result in item.get("grader_results", []) or []
            ]
            normalized_examples.append(normalized)

        return cls(
            run_id=str(data.get("run_id", uuid.uuid4().hex[:12])),
            evaluation_id=str(data.get("evaluation_id", "")),
            per_example_results=normalized_examples,
            summary_stats=dict(data.get("summary_stats", {}) or {}),
            annotations=[
                Annotation.from_dict(annotation)
                for annotation in data.get("annotations", []) or []
            ],
            warnings=list(data.get("warnings", []) or []),
            metadata=dict(data.get("metadata", {}) or {}),
        )

    @classmethod
    def from_example_results(
        cls,
        *,
        evaluation_id: str,
        per_example_results: list[dict[str, Any]],
        annotations: list[Annotation] | None = None,
        warnings: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> "RunResult":
        """Build a RunResult and derive summary statistics from examples."""

        normalized_examples: list[dict[str, Any]] = []
        total_score = 0.0
        passed_examples = 0
        grader_totals: dict[str, int] = {}

        for item in per_example_results:
            grader_results = [
                result if isinstance(result, GraderResult) else GraderResult.from_dict(result)
                for result in item.get("grader_results", []) or []
            ]
            if item.get("score") is not None:
                example_score = float(item["score"])
            elif grader_results:
                example_score = sum(result.score for result in grader_results) / len(grader_results)
            else:
                example_score = 0.0

            if item.get("passed") is not None:
                example_passed = bool(item["passed"])
            elif grader_results:
                example_passed = all(result.passed for result in grader_results)
            else:
                example_passed = example_score >= 0.5

            total_score += example_score
            passed_examples += 1 if example_passed else 0

            for result in grader_results:
                grader_totals[result.grader_id] = grader_totals.get(result.grader_id, 0) + 1

            normalized = dict(item)
            normalized["score"] = round(example_score, 4)
            normalized["passed"] = example_passed
            normalized["grader_results"] = grader_results
            normalized_examples.append(normalized)

        total_examples = len(normalized_examples)
        average_score = total_score / total_examples if total_examples else 0.0
        pass_rate = passed_examples / total_examples if total_examples else 0.0

        summary_stats = {
            "total_examples": total_examples,
            "passed_examples": passed_examples,
            "failed_examples": max(total_examples - passed_examples, 0),
            "average_score": round(average_score, 4),
            "pass_rate": round(pass_rate, 4),
            "grader_counts": grader_totals,
        }

        return cls(
            run_id=run_id or uuid.uuid4().hex[:12],
            evaluation_id=evaluation_id,
            per_example_results=normalized_examples,
            summary_stats=summary_stats,
            annotations=list(annotations or []),
            warnings=list(warnings or []),
            metadata=dict(metadata or {}),
        )


@dataclass
class EvaluationRun:
    """One execution of an Evaluation with a frozen config snapshot."""

    run_id: str
    evaluation_id: str
    dataset_ref: str
    dataset_version: str
    config_snapshot: dict[str, Any]
    result: RunResult
    mode: str = "mock"
    started_at: str = field(default_factory=_now_iso)
    completed_at: str = field(default_factory=_now_iso)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the evaluation run into a JSON-safe dict."""

        return {
            "run_id": self.run_id,
            "evaluation_id": self.evaluation_id,
            "dataset_ref": self.dataset_ref,
            "dataset_version": self.dataset_version,
            "config_snapshot": self.config_snapshot,
            "result": self.result.to_dict(),
            "mode": self.mode,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvaluationRun":
        """Deserialize an evaluation run from a plain dict."""

        raw_result = data.get("result", {})
        result = raw_result if isinstance(raw_result, RunResult) else RunResult.from_dict(raw_result)
        return cls(
            run_id=str(data.get("run_id", uuid.uuid4().hex[:12])),
            evaluation_id=str(data.get("evaluation_id", "")),
            dataset_ref=str(data.get("dataset_ref", "")),
            dataset_version=str(data.get("dataset_version", "")),
            config_snapshot=dict(data.get("config_snapshot", {}) or {}),
            result=result,
            mode=str(data.get("mode", "mock")),
            started_at=str(data.get("started_at", _now_iso())),
            completed_at=str(data.get("completed_at", _now_iso())),
            warnings=list(data.get("warnings", []) or []),
            metadata=dict(data.get("metadata", {}) or {}),
        )


__all__ = [
    "Annotation",
    "Dataset",
    "Evaluation",
    "EvaluationRun",
    "Grader",
    "GraderKind",
    "GraderResult",
    "RunResult",
]

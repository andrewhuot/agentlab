"""Pairwise evaluation engine and JSON-backed comparison store."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from evals.judges.pairwise_judge import PairwiseJudgeVerdict, PairwiseLLMJudge
from evals.pairwise_stats import PairwiseAnalysis, analyze_pairwise_scores
from evals.runner import EvalRunner, TestCase
from evals.scorer import CompositeScorer, EvalResult


@dataclass
class PairwiseVariantResult:
    """One side of a pairwise case comparison."""

    response: str
    specialist_used: str
    passed: bool
    quality_score: float
    safety_passed: bool
    latency_ms: float
    token_count: int
    composite_score: float
    details: str
    raw_output: dict[str, Any] = field(default_factory=dict)
    custom_scores: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize one pairwise side for storage and API responses."""
        return {
            "response": self.response,
            "specialist_used": self.specialist_used,
            "passed": self.passed,
            "quality_score": self.quality_score,
            "safety_passed": self.safety_passed,
            "latency_ms": self.latency_ms,
            "token_count": self.token_count,
            "composite_score": self.composite_score,
            "details": self.details,
            "raw_output": self.raw_output,
            "custom_scores": self.custom_scores,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PairwiseVariantResult:
        """Rehydrate one side of a persisted pairwise comparison."""
        return cls(
            response=str(payload.get("response", "")),
            specialist_used=str(payload.get("specialist_used", "")),
            passed=bool(payload.get("passed", False)),
            quality_score=float(payload.get("quality_score", 0.0)),
            safety_passed=bool(payload.get("safety_passed", False)),
            latency_ms=float(payload.get("latency_ms", 0.0)),
            token_count=int(payload.get("token_count", 0)),
            composite_score=float(payload.get("composite_score", 0.0)),
            details=str(payload.get("details", "")),
            raw_output=dict(payload.get("raw_output", {}) or {}),
            custom_scores={
                str(key): float(value)
                for key, value in (payload.get("custom_scores", {}) or {}).items()
            },
        )


@dataclass
class HumanPreferenceTask:
    """A deferred preference judgment for human review."""

    task_id: str
    case_id: str
    label_a: str
    label_b: str
    prompt: str
    status: str = "pending"

    def to_dict(self) -> dict[str, str]:
        """Serialize a human preference review task."""
        return {
            "task_id": self.task_id,
            "case_id": self.case_id,
            "label_a": self.label_a,
            "label_b": self.label_b,
            "prompt": self.prompt,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, str]) -> HumanPreferenceTask:
        """Rehydrate a persisted human preference task."""
        return cls(
            task_id=str(payload.get("task_id", "")),
            case_id=str(payload.get("case_id", "")),
            label_a=str(payload.get("label_a", "A")),
            label_b=str(payload.get("label_b", "B")),
            prompt=str(payload.get("prompt", "")),
            status=str(payload.get("status", "pending")),
        )


@dataclass
class PairwiseCaseResult:
    """One pairwise outcome at the case level."""

    case_id: str
    category: str
    input_message: str
    left: PairwiseVariantResult
    right: PairwiseVariantResult
    winner: str
    winner_reason: str
    score_delta: float
    human_preference_task: HumanPreferenceTask | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize one pairwise case result."""
        return {
            "case_id": self.case_id,
            "category": self.category,
            "input_message": self.input_message,
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
            "winner": self.winner,
            "winner_reason": self.winner_reason,
            "score_delta": self.score_delta,
            "human_preference_task": (
                self.human_preference_task.to_dict()
                if self.human_preference_task is not None
                else None
            ),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PairwiseCaseResult:
        """Rehydrate one persisted pairwise case result."""
        human_task_payload = payload.get("human_preference_task")
        return cls(
            case_id=str(payload.get("case_id", "")),
            category=str(payload.get("category", "")),
            input_message=str(payload.get("input_message", "")),
            left=PairwiseVariantResult.from_dict(dict(payload.get("left", {}) or {})),
            right=PairwiseVariantResult.from_dict(dict(payload.get("right", {}) or {})),
            winner=str(payload.get("winner", "tie")),
            winner_reason=str(payload.get("winner_reason", "")),
            score_delta=float(payload.get("score_delta", 0.0)),
            human_preference_task=(
                HumanPreferenceTask.from_dict(dict(human_task_payload))
                if isinstance(human_task_payload, dict)
                else None
            ),
        )


@dataclass
class PairwiseSummary:
    """Aggregate counts for a pairwise comparison."""

    total_cases: int
    left_wins: int
    right_wins: int
    ties: int
    pending_human: int = 0

    def to_dict(self) -> dict[str, int]:
        """Serialize pairwise summary counts."""
        return {
            "total_cases": self.total_cases,
            "left_wins": self.left_wins,
            "right_wins": self.right_wins,
            "ties": self.ties,
            "pending_human": self.pending_human,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PairwiseSummary:
        """Rehydrate persisted summary counts."""
        return cls(
            total_cases=int(payload.get("total_cases", 0)),
            left_wins=int(payload.get("left_wins", 0)),
            right_wins=int(payload.get("right_wins", 0)),
            ties=int(payload.get("ties", 0)),
            pending_human=int(payload.get("pending_human", 0)),
        )


@dataclass
class PairwiseComparisonResult:
    """Top-level persisted result for a pairwise evaluation run."""

    comparison_id: str
    created_at: str
    dataset_name: str
    label_a: str
    label_b: str
    judge_strategy: str
    summary: PairwiseSummary
    analysis: PairwiseAnalysis
    case_results: list[PairwiseCaseResult]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the comparison result for persistence or API output."""
        return {
            "comparison_id": self.comparison_id,
            "created_at": self.created_at,
            "dataset_name": self.dataset_name,
            "label_a": self.label_a,
            "label_b": self.label_b,
            "judge_strategy": self.judge_strategy,
            "summary": self.summary.to_dict(),
            "analysis": self.analysis.to_dict(),
            "case_results": [case_result.to_dict() for case_result in self.case_results],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PairwiseComparisonResult:
        """Rehydrate a persisted pairwise comparison."""
        return cls(
            comparison_id=str(payload.get("comparison_id", "")),
            created_at=str(payload.get("created_at", "")),
            dataset_name=str(payload.get("dataset_name", "default")),
            label_a=str(payload.get("label_a", "A")),
            label_b=str(payload.get("label_b", "B")),
            judge_strategy=str(payload.get("judge_strategy", "metric_delta")),
            summary=PairwiseSummary.from_dict(dict(payload.get("summary", {}) or {})),
            analysis=PairwiseAnalysis.from_dict(dict(payload.get("analysis", {}) or {})),
            case_results=[
                PairwiseCaseResult.from_dict(dict(item))
                for item in list(payload.get("case_results", []) or [])
                if isinstance(item, dict)
            ],
        )


class PairwiseComparisonStore:
    """Persist pairwise comparison payloads as JSON files."""

    def __init__(self, base_dir: str = ".agentlab/pairwise") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, result: PairwiseComparisonResult) -> None:
        """Write one pairwise comparison result to disk."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        path = self.base_dir / f"{result.comparison_id}.json"
        path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")

    def get(self, comparison_id: str) -> PairwiseComparisonResult | None:
        """Load one pairwise comparison result by ID."""
        path = self.base_dir / f"{comparison_id}.json"
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return PairwiseComparisonResult.from_dict(payload)

    def list(self, limit: int = 20) -> list[PairwiseComparisonResult]:
        """Return recent pairwise comparison results newest-first."""
        results: list[PairwiseComparisonResult] = []
        files = sorted(self.base_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
        for path in files[:limit]:
            payload = json.loads(path.read_text(encoding="utf-8"))
            results.append(PairwiseComparisonResult.from_dict(payload))
        return results

    def latest(self) -> PairwiseComparisonResult | None:
        """Return the newest pairwise comparison if one exists."""
        items = self.list(limit=1)
        return items[0] if items else None


class PairwiseEvalEngine:
    """Run side-by-side evaluations using the existing eval runner contract."""

    def __init__(
        self,
        *,
        eval_runner: EvalRunner,
        store: PairwiseComparisonStore | None = None,
        judge: PairwiseLLMJudge | None = None,
        tie_margin: float = 0.01,
    ) -> None:
        self.eval_runner = eval_runner
        self.store = store or PairwiseComparisonStore()
        self.judge = judge or PairwiseLLMJudge()
        self.tie_margin = max(0.0, float(tie_margin))

    def compare(
        self,
        *,
        config_a: dict | None = None,
        config_b: dict | None = None,
        label_a: str,
        label_b: str,
        dataset_path: str | None = None,
        dataset_name: str = "default",
        split: str = "all",
        judge_strategy: str = "metric_delta",
        agent_fn_a: Callable[[str, dict | None], dict] | None = None,
        agent_fn_b: Callable[[str, dict | None], dict] | None = None,
    ) -> PairwiseComparisonResult:
        """Compare two variants across a dataset or the default eval case set."""
        if dataset_path:
            cases = self.eval_runner.load_dataset_cases(dataset_path, split=split)
            dataset_name = Path(dataset_path).name
        else:
            cases = self.eval_runner.load_cases()
        return self.compare_cases(
            cases,
            config_a=config_a,
            config_b=config_b,
            label_a=label_a,
            label_b=label_b,
            dataset_name=dataset_name,
            judge_strategy=judge_strategy,
            agent_fn_a=agent_fn_a,
            agent_fn_b=agent_fn_b,
        )

    def compare_cases(
        self,
        cases: list[TestCase],
        *,
        config_a: dict | None = None,
        config_b: dict | None = None,
        label_a: str,
        label_b: str,
        dataset_name: str = "default",
        judge_strategy: str = "metric_delta",
        agent_fn_a: Callable[[str, dict | None], dict] | None = None,
        agent_fn_b: Callable[[str, dict | None], dict] | None = None,
    ) -> PairwiseComparisonResult:
        """Compare two variants on an explicit list of cases."""
        normalized_strategy = judge_strategy.strip().lower()
        if normalized_strategy not in {"metric_delta", "llm_judge", "human_preference"}:
            raise ValueError(f"Unsupported judge strategy: {judge_strategy}")

        comparison_id = f"cmp_{uuid.uuid4().hex[:12]}"
        created_at = datetime.now(timezone.utc).isoformat()
        case_results: list[PairwiseCaseResult] = []
        left_scores: list[float] = []
        right_scores: list[float] = []
        analysis_outcomes: list[str] = []

        for case in cases:
            left_result = self._evaluate_variant(case, config_a, agent_fn=agent_fn_a)
            right_result = self._evaluate_variant(case, config_b, agent_fn=agent_fn_b)
            left_scores.append(left_result.composite_score)
            right_scores.append(right_result.composite_score)

            if normalized_strategy == "human_preference":
                human_task = self._build_human_preference_task(case, label_a=label_a, label_b=label_b, left=left_result, right=right_result)
                winner = "pending_human"
                winner_reason = "Deferred to human preference review."
                analysis_outcomes.append("tie")
            elif normalized_strategy == "llm_judge":
                verdict = self.judge.judge_case(
                    case=case,
                    label_a=label_a,
                    label_b=label_b,
                    output_a=left_result.raw_output,
                    output_b=right_result.raw_output,
                    eval_a=self._variant_eval_result(left_result, case),
                    eval_b=self._variant_eval_result(right_result, case),
                )
                winner = verdict.winner
                winner_reason = verdict.reasoning
                human_task = None
                analysis_outcomes.append(winner if winner in {label_a, label_b} else "tie")
            else:
                winner, winner_reason = self._metric_delta_winner(
                    label_a=label_a,
                    label_b=label_b,
                    left_score=left_result.composite_score,
                    right_score=right_result.composite_score,
                )
                human_task = None
                analysis_outcomes.append(winner if winner in {label_a, label_b} else "tie")

            case_results.append(
                PairwiseCaseResult(
                    case_id=case.id,
                    category=case.category,
                    input_message=case.user_message,
                    left=left_result,
                    right=right_result,
                    winner=winner,
                    winner_reason=winner_reason,
                    score_delta=round(right_result.composite_score - left_result.composite_score, 4),
                    human_preference_task=human_task,
                )
            )

        summary = self._build_summary(case_results, label_a=label_a, label_b=label_b)
        analysis = analyze_pairwise_scores(
            label_a=label_a,
            label_b=label_b,
            left_scores=left_scores,
            right_scores=right_scores,
            outcomes=analysis_outcomes,
        )
        result = PairwiseComparisonResult(
            comparison_id=comparison_id,
            created_at=created_at,
            dataset_name=dataset_name,
            label_a=label_a,
            label_b=label_b,
            judge_strategy=normalized_strategy,
            summary=summary,
            analysis=analysis,
            case_results=case_results,
        )
        self.store.save(result)
        return result

    def _evaluate_variant(
        self,
        case: TestCase,
        config: dict | None,
        *,
        agent_fn: Callable[[str, dict | None], dict] | None,
    ) -> PairwiseVariantResult:
        """Run one side of a pairwise case while capturing the raw agent payload."""
        captured: dict[str, Any] = {}
        active_agent_fn = agent_fn or self.eval_runner.agent_fn
        original_agent_fn = self.eval_runner.agent_fn

        def _capturing_agent(message: str, agent_config: dict | None = None) -> dict:
            payload = active_agent_fn(message, agent_config)
            captured["payload"] = payload
            return payload

        self.eval_runner.agent_fn = _capturing_agent
        try:
            eval_result = self.eval_runner.evaluate_case(case, config=config)
        finally:
            self.eval_runner.agent_fn = original_agent_fn

        raw_output = dict(captured.get("payload", {}) or {})
        composite_score = self._per_case_composite(eval_result)
        return PairwiseVariantResult(
            response=str(raw_output.get("response", "")),
            specialist_used=str(raw_output.get("specialist_used", "")),
            passed=eval_result.passed,
            quality_score=eval_result.quality_score,
            safety_passed=eval_result.safety_passed,
            latency_ms=eval_result.latency_ms,
            token_count=eval_result.token_count,
            composite_score=composite_score,
            details=eval_result.details,
            raw_output=raw_output,
            custom_scores=dict(eval_result.custom_scores),
        )

    def _per_case_composite(self, result: EvalResult) -> float:
        """Mirror the scorer's weighted composite formula for one case."""
        latency_score = max(
            0.0,
            min(1.0, 1.0 - (result.latency_ms / CompositeScorer.MAX_LATENCY_MS)),
        )
        cost_score = max(
            0.0,
            min(1.0, 1.0 - (result.token_count / CompositeScorer.MAX_TOKENS)),
        )
        composite = (
            CompositeScorer.QUALITY_WEIGHT * result.quality_score
            + CompositeScorer.SAFETY_WEIGHT * (1.0 if result.safety_passed else 0.0)
            + CompositeScorer.LATENCY_WEIGHT * latency_score
            + CompositeScorer.COST_WEIGHT * cost_score
        )
        return round(composite, 4)

    def _metric_delta_winner(
        self,
        *,
        label_a: str,
        label_b: str,
        left_score: float,
        right_score: float,
    ) -> tuple[str, str]:
        """Pick a winner based on deterministic score delta."""
        delta = right_score - left_score
        if abs(delta) <= self.tie_margin:
            return ("tie", f"Scores were within the tie margin ({self.tie_margin:.2f}).")
        if delta > 0:
            return (label_b, f"{label_b} won on composite score delta ({delta:+.4f}).")
        return (label_a, f"{label_a} won on composite score delta ({delta:+.4f}).")

    def _build_human_preference_task(
        self,
        case: TestCase,
        *,
        label_a: str,
        label_b: str,
        left: PairwiseVariantResult,
        right: PairwiseVariantResult,
    ) -> HumanPreferenceTask:
        """Create a deferred annotation task for human preference review."""
        task_id = f"pref_{uuid.uuid4().hex[:12]}"
        prompt = (
            f"Case: {case.user_message}\n\n"
            f"{label_a}:\n{left.response}\n\n"
            f"{label_b}:\n{right.response}\n\n"
            "Choose the better answer or mark a tie. Explain the preference in one sentence."
        )
        return HumanPreferenceTask(
            task_id=task_id,
            case_id=case.id,
            label_a=label_a,
            label_b=label_b,
            prompt=prompt,
        )

    def _build_summary(
        self,
        case_results: list[PairwiseCaseResult],
        *,
        label_a: str,
        label_b: str,
    ) -> PairwiseSummary:
        """Aggregate winner counts across all case results."""
        left_wins = sum(1 for result in case_results if result.winner == label_a)
        right_wins = sum(1 for result in case_results if result.winner == label_b)
        ties = sum(1 for result in case_results if result.winner == "tie")
        pending_human = sum(1 for result in case_results if result.winner == "pending_human")
        return PairwiseSummary(
            total_cases=len(case_results),
            left_wins=left_wins,
            right_wins=right_wins,
            ties=ties,
            pending_human=pending_human,
        )

    @staticmethod
    def _variant_eval_result(result: PairwiseVariantResult, case: TestCase) -> EvalResult:
        """Rebuild an EvalResult-like object for judge compatibility."""
        return EvalResult(
            case_id=case.id,
            category=case.category,
            passed=result.passed,
            quality_score=result.quality_score,
            safety_passed=result.safety_passed,
            latency_ms=result.latency_ms,
            token_count=result.token_count,
            custom_scores=result.custom_scores,
            details=result.details,
        )

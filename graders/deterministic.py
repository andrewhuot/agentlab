"""Deterministic assertion grader (fastest, cheapest, most reliable)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GradeResult:
    """Generic grade result used across grader layers."""

    score: float
    passed: bool
    grader: str
    details: dict[str, Any] = field(default_factory=dict)


class DeterministicGrader:
    """Evaluate strict assertions against response/tool/status outputs."""

    def grade(
        self,
        *,
        response_text: str,
        assertions: dict[str, Any],
        tool_calls: list[dict[str, Any]] | None = None,
        status_code: int | None = None,
    ) -> GradeResult:
        checks: list[bool] = []
        details: dict[str, Any] = {}
        text = response_text or ""

        contains = assertions.get("contains") or []
        not_contains = assertions.get("not_contains") or []
        expected_tool = assertions.get("expected_tool")
        expected_status = assertions.get("status_code")

        for phrase in contains:
            ok = str(phrase).lower() in text.lower()
            checks.append(ok)
        for phrase in not_contains:
            ok = str(phrase).lower() not in text.lower()
            checks.append(ok)

        if expected_tool:
            calls = tool_calls or []
            called = {
                str(call.get("tool") or call.get("name") or "").strip().lower()
                for call in calls
                if isinstance(call, dict)
            }
            ok = str(expected_tool).strip().lower() in called
            checks.append(ok)
            details["called_tools"] = sorted(called)

        if expected_status is not None:
            ok = status_code == int(expected_status)
            checks.append(ok)
            details["status_code"] = status_code

        if not checks:
            return GradeResult(score=1.0, passed=True, grader="deterministic", details={})

        score = sum(1 for item in checks if item) / len(checks)
        return GradeResult(
            score=round(score, 4),
            passed=all(checks),
            grader="deterministic",
            details=details,
        )

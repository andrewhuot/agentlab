"""Gap analyzer — identifies missing capabilities from blame clusters and opportunities."""

from __future__ import annotations

import re
import uuid
from typing import Any

from agent_skills.types import SkillGap


# ---------------------------------------------------------------------------
# Severity weights per failure family
# ---------------------------------------------------------------------------

_SEVERITY_WEIGHTS: dict[str, float] = {
    "tool_error": 0.8,
    "routing_failure": 0.7,
    "quality_degradation": 0.5,
    "hallucination": 0.6,
    "safety_violation": 0.9,
    "latency_spike": 0.3,
    "cost_spike": 0.2,
    "transfer_loop": 0.5,
}

_DEFAULT_SEVERITY_WEIGHT = 0.5


class GapAnalyzer:
    """Analyzes blame clusters and opportunities to identify skill gaps."""

    # Heuristic keyword lists (checked case-insensitively)
    _NEW_SKILL_KEYWORDS = [
        "no tool",
        "not found",
        "unknown intent",
        "no handler",
        "missing",
        "unsupported",
        "unrecognized",
    ]
    _TUNING_KEYWORDS = [
        "unhelpful",
        "hallucination",
        "slow",
        "timeout",
        "expensive",
        "cost",
    ]

    def analyze(
        self,
        blame_clusters: list,
        opportunities: list,
        platform: str = "adk",
    ) -> list[SkillGap]:
        """Identify skill gaps from blame clusters and opportunities.

        Duck-types both ``BlameCluster`` (fields: cluster_id, grader_name,
        agent_path, failure_reason, count, total_traces, impact_score,
        example_trace_ids, first_seen, last_seen, trend) and
        ``OptimizationOpportunity`` (fields: opportunity_id, failure_family,
        affected_agent_path, severity, prevalence, priority_score,
        sample_trace_ids, recommended_operator_families).

        Returns a list of :class:`SkillGap` sorted by ``frequency *
        impact_score`` descending.
        """
        # Build a lookup from cluster_id -> opportunity for extra context.
        opp_by_cluster: dict[str, Any] = {}
        for opp in opportunities:
            cid = getattr(opp, "cluster_id", None)
            if cid:
                opp_by_cluster[cid] = opp

        # Group clusters by normalised root cause so duplicates are merged.
        # Key: (normalised_reason, failure_family)
        groups: dict[tuple[str, str], list[Any]] = {}
        for cluster in blame_clusters:
            failure_reason: str = getattr(cluster, "failure_reason", "") or ""
            # Derive failure_family from an associated opportunity, or infer it.
            failure_family = self._infer_failure_family(
                cluster, opp_by_cluster
            )
            norm_reason = self._normalise_reason(failure_reason)
            key = (norm_reason, failure_family)
            groups.setdefault(key, []).append(cluster)

        gaps: list[SkillGap] = []
        for (norm_reason, failure_family), clusters in groups.items():
            # Use the cluster with the highest count as the representative.
            rep = max(clusters, key=lambda c: getattr(c, "count", 0))

            failure_reason: str = getattr(rep, "failure_reason", "") or ""
            agent_path: str = getattr(rep, "agent_path", "") or ""
            trend: str = getattr(rep, "trend", "stable") or "stable"

            # Prevalence: use associated opportunity if available, else derive.
            prevalence = self._prevalence(rep, opp_by_cluster)

            if not self._is_new_skill_needed(
                failure_reason, failure_family, trend, prevalence
            ):
                continue

            classification = self._classify_gap(
                failure_reason, failure_family, agent_path, trend, prevalence, platform
            )
            if classification is None:
                continue

            gap_type, suggested_platform = classification
            frequency = sum(getattr(c, "count", 0) for c in clusters)
            evidence = []
            for c in clusters:
                evidence.extend(getattr(c, "example_trace_ids", []) or [])
            evidence = list(dict.fromkeys(evidence))[:10]  # deduplicate, cap at 10

            severity_weight = _SEVERITY_WEIGHTS.get(
                failure_family, _DEFAULT_SEVERITY_WEIGHT
            )
            impact_score = round(min(prevalence * severity_weight, 1.0), 4)

            gaps.append(
                SkillGap(
                    gap_id=uuid.uuid4().hex[:12],
                    gap_type=gap_type,
                    description=f"Detected '{failure_reason}' pattern in {agent_path or 'unknown agent'} ({failure_family})",
                    evidence=evidence,
                    failure_family=failure_family,
                    frequency=frequency,
                    impact_score=impact_score,
                    suggested_name=self._suggest_name(gap_type, failure_reason),
                    suggested_platform=suggested_platform,
                    context={
                        "trend": trend,
                        "prevalence": prevalence,
                        "agent_path": agent_path,
                        "cluster_count": len(clusters),
                    },
                )
            )

        # Sort by frequency * impact_score descending.
        gaps.sort(key=lambda g: g.frequency * g.impact_score, reverse=True)
        return gaps

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _classify_gap(
        self,
        failure_reason: str,
        failure_family: str,
        agent_path: str,
        trend: str,
        prevalence: float,
        platform: str,
    ) -> tuple[str, str] | None:
        """Return ``(gap_type, suggested_platform)`` or ``None`` for tuning issues.

        Maps failure patterns to gap types based on platform and failure family:

        * ADK platform:
          - tool_error + missing-keyword → ``missing_tool``
          - routing_failure + unknown agent → ``missing_sub_agent``
          - tool_error + existing tool + enhancement → ``tool_enhancement``

        * CX platform:
          - routing → ``missing_intent``
          - quality → ``missing_playbook_step``
          - flow/transfer → ``missing_flow``
        """
        reason_lower = failure_reason.lower()
        family_lower = failure_family.lower()

        if platform == "cx":
            if "routing" in family_lower or "intent" in reason_lower:
                return ("missing_intent", "cx")
            if "flow" in family_lower or "flow" in reason_lower or "transfer" in reason_lower:
                return ("missing_flow", "cx")
            if "quality" in family_lower or "playbook" in reason_lower:
                return ("missing_playbook_step", "cx")
            # Fall back to missing_intent for generic tool errors on CX
            if "tool" in family_lower:
                return ("missing_intent", "cx")
            return None

        # ADK platform (default)
        if "tool" in family_lower:
            has_missing_kw = any(
                kw in reason_lower
                for kw in ("no tool", "not found", "missing", "unsupported", "unrecognized", "no handler")
            )
            if has_missing_kw:
                return ("missing_tool", "adk")
            # Enhancement pattern: existing tool but needs improvement
            has_enhancement_kw = any(
                kw in reason_lower for kw in ("enhancement", "improve", "extend", "add parameter")
            )
            if has_enhancement_kw:
                return ("tool_enhancement", "adk")
            # High-prevalence tool error with growing trend → treat as missing tool
            if prevalence > 0.3 and trend == "growing":
                return ("missing_tool", "adk")
            return ("tool_enhancement", "adk")

        if "routing" in family_lower:
            unknown_agent = (
                not agent_path
                or agent_path in ("unknown", "")
                or "unknown" in reason_lower
            )
            if unknown_agent:
                return ("missing_sub_agent", "adk")
            return ("missing_sub_agent", "adk")

        return None

    def _suggest_name(self, gap_type: str, failure_reason: str) -> str:
        """Generate a suggested skill name from the gap type and failure reason.

        Extracts meaningful tokens from the failure reason, strips noise words,
        and combines them with the gap type suffix.
        """
        # Strip common noise phrases to get a meaningful noun phrase.
        noise_patterns = [
            r"\bno tool\b",
            r"\bnot found\b",
            r"\bunknown intent\b",
            r"\bno handler\b",
            r"\bmissing\b",
            r"\bunsupported\b",
            r"\bunrecognized\b",
            r"\berror\b",
            r"\bfailure\b",
            r"\bfor\b",
        ]
        cleaned = failure_reason.lower()
        for pattern in noise_patterns:
            cleaned = re.sub(pattern, " ", cleaned)

        # Keep only word characters, collapse whitespace, title-case each word.
        tokens = [t for t in re.split(r"\W+", cleaned) if len(t) > 2]
        if tokens:
            base = "_".join(tokens[:3])
        else:
            base = gap_type

        suffix_map = {
            "missing_tool": "tool",
            "missing_sub_agent": "agent",
            "tool_enhancement": "tool",
            "missing_intent": "intent",
            "missing_playbook_step": "playbook",
            "missing_flow": "flow",
        }
        suffix = suffix_map.get(gap_type, "skill")
        return f"{base}_{suffix}"

    def _is_new_skill_needed(
        self,
        failure_reason: str,
        failure_family: str,
        trend: str,
        prevalence: float,
    ) -> bool:
        """Return True if this failure pattern indicates a missing capability.

        Heuristic rules (checked in order):

        1. Any new-skill keyword in the failure reason → True.
        2. tool_error family + high prevalence (>0.3) + growing trend → True.
        3. routing_failure family + unknown/empty agent path → True (handled
           upstream via agent_path, but prevalence alone is enough here).
        4. Tuning-only keywords (quality/cost/latency) → False.
        5. Default → False (conservative: don't propose skills for ambiguous cases).
        """
        reason_lower = failure_reason.lower()
        family_lower = failure_family.lower()

        # Rule 1: explicit "missing" signal
        if any(kw in reason_lower for kw in self._NEW_SKILL_KEYWORDS):
            return True

        # Rule 2: prevalent + growing tool errors suggest a missing tool
        if (
            family_lower == "tool_error"
            and prevalence > 0.3
            and trend == "growing"
        ):
            return True

        # Rule 3: routing failures always suggest a missing sub-agent
        if family_lower == "routing_failure":
            return True

        # Rule 4: pure quality / cost / latency issues → tuning, not new skill
        if any(kw in reason_lower for kw in self._TUNING_KEYWORDS):
            return False

        return False

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise_reason(reason: str) -> str:
        """Collapse whitespace and lowercase for grouping purposes."""
        return re.sub(r"\s+", " ", reason.lower().strip())

    @staticmethod
    def _infer_failure_family(cluster: Any, opp_by_cluster: dict[str, Any]) -> str:
        """Derive the failure_family for a cluster.

        Prefers the linked ``OptimizationOpportunity.failure_family`` if
        present; otherwise guesses from the grader name.
        """
        cid = getattr(cluster, "cluster_id", None)
        if cid and cid in opp_by_cluster:
            return getattr(opp_by_cluster[cid], "failure_family", "") or ""

        grader_name: str = getattr(cluster, "grader_name", "") or ""
        grader_lower = grader_name.lower()
        if "tool" in grader_lower:
            return "tool_error"
        if "routing" in grader_lower or "route" in grader_lower:
            return "routing_failure"
        if "safety" in grader_lower:
            return "safety_violation"
        if "latency" in grader_lower or "timeout" in grader_lower:
            return "latency_spike"
        if "quality" in grader_lower or "helpful" in grader_lower:
            return "quality_degradation"
        if "hallucin" in grader_lower:
            return "hallucination"
        return "tool_error"

    @staticmethod
    def _prevalence(cluster: Any, opp_by_cluster: dict[str, Any]) -> float:
        """Return the prevalence (0-1) for a cluster.

        Uses the associated opportunity's prevalence if available, otherwise
        computes ``count / total_traces`` from the cluster itself.
        """
        cid = getattr(cluster, "cluster_id", None)
        if cid and cid in opp_by_cluster:
            opp_prevalence = getattr(opp_by_cluster[cid], "prevalence", None)
            if opp_prevalence is not None:
                return float(opp_prevalence)

        count = getattr(cluster, "count", 0) or 0
        total = getattr(cluster, "total_traces", 1) or 1
        return min(count / total, 1.0)

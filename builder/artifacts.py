"""Artifact card factories for Builder Workspace output."""

from __future__ import annotations

from typing import Any

from builder.types import ArtifactRef, ArtifactType, now_ts


class ArtifactCardFactory:
    """Factory helpers for all builder artifact card types."""

    def create_plan_card(
        self,
        task_id: str,
        session_id: str,
        project_id: str,
        goal: str,
        assumptions: list[str],
        targeted_artifacts: list[str],
        expected_impact: str,
        risk_level: str,
        required_approvals: list[str],
        *,
        skills_used: list[str] | None = None,
        source_versions: dict[str, str] | None = None,
        release_candidate_id: str | None = None,
    ) -> ArtifactRef:
        """Create a plan artifact card."""

        payload = {
            "goal": goal,
            "assumptions": assumptions,
            "targeted_artifacts": targeted_artifacts,
            "expected_impact": expected_impact,
            "risk_level": risk_level,
            "required_approvals": required_approvals,
        }
        return self._artifact(
            artifact_type=ArtifactType.PLAN,
            title="Plan",
            summary=goal,
            payload=payload,
            task_id=task_id,
            session_id=session_id,
            project_id=project_id,
            skills_used=skills_used,
            source_versions=source_versions,
            release_candidate_id=release_candidate_id,
        )

    def create_source_diff_card(
        self,
        task_id: str,
        session_id: str,
        project_id: str,
        files: list[dict[str, Any]],
        summary: str,
        *,
        skills_used: list[str] | None = None,
        source_versions: dict[str, str] | None = None,
        release_candidate_id: str | None = None,
    ) -> ArtifactRef:
        """Create a source diff artifact card."""

        return self._artifact(
            artifact_type=ArtifactType.SOURCE_DIFF,
            title="Source Diff",
            summary=summary,
            payload={"files": files, "summary": summary},
            task_id=task_id,
            session_id=session_id,
            project_id=project_id,
            skills_used=skills_used,
            source_versions=source_versions,
            release_candidate_id=release_candidate_id,
        )

    def create_adk_graph_diff_card(
        self,
        task_id: str,
        session_id: str,
        project_id: str,
        before_graph: dict[str, Any],
        after_graph: dict[str, Any],
        summary: str,
        *,
        skills_used: list[str] | None = None,
        source_versions: dict[str, str] | None = None,
        release_candidate_id: str | None = None,
    ) -> ArtifactRef:
        """Create an ADK graph diff artifact card."""

        return self._artifact(
            artifact_type=ArtifactType.ADK_GRAPH_DIFF,
            title="ADK Graph Diff",
            summary=summary,
            payload={"before_graph": before_graph, "after_graph": after_graph, "summary": summary},
            task_id=task_id,
            session_id=session_id,
            project_id=project_id,
            skills_used=skills_used,
            source_versions=source_versions,
            release_candidate_id=release_candidate_id,
        )

    def create_skill_card(
        self,
        task_id: str,
        session_id: str,
        project_id: str,
        name: str,
        manifest: dict[str, Any],
        effectiveness: float | None,
        *,
        skills_used: list[str] | None = None,
        source_versions: dict[str, str] | None = None,
        release_candidate_id: str | None = None,
    ) -> ArtifactRef:
        """Create a skill artifact card."""

        return self._artifact(
            artifact_type=ArtifactType.SKILL,
            title=f"Skill: {name}",
            summary=f"Skill {name}",
            payload={"name": name, "manifest": manifest, "effectiveness": effectiveness},
            task_id=task_id,
            session_id=session_id,
            project_id=project_id,
            skills_used=skills_used,
            source_versions=source_versions,
            release_candidate_id=release_candidate_id,
        )

    def create_guardrail_card(
        self,
        task_id: str,
        session_id: str,
        project_id: str,
        name: str,
        attached_scope: list[str],
        failure_examples: list[str],
        *,
        skills_used: list[str] | None = None,
        source_versions: dict[str, str] | None = None,
        release_candidate_id: str | None = None,
    ) -> ArtifactRef:
        """Create a guardrail artifact card."""

        return self._artifact(
            artifact_type=ArtifactType.GUARDRAIL,
            title=f"Guardrail: {name}",
            summary=f"Guardrail {name}",
            payload={
                "name": name,
                "attached_scope": attached_scope,
                "failure_examples": failure_examples,
            },
            task_id=task_id,
            session_id=session_id,
            project_id=project_id,
            skills_used=skills_used,
            source_versions=source_versions,
            release_candidate_id=release_candidate_id,
        )

    def create_eval_card(
        self,
        task_id: str,
        session_id: str,
        project_id: str,
        eval_bundle_id: str,
        hard_gate_passed: bool,
        summary: str,
        *,
        skills_used: list[str] | None = None,
        source_versions: dict[str, str] | None = None,
        release_candidate_id: str | None = None,
    ) -> ArtifactRef:
        """Create an eval artifact card."""

        return self._artifact(
            artifact_type=ArtifactType.EVAL,
            title="Eval Results",
            summary=summary,
            payload={
                "eval_bundle_id": eval_bundle_id,
                "hard_gate_passed": hard_gate_passed,
                "summary": summary,
            },
            task_id=task_id,
            session_id=session_id,
            project_id=project_id,
            skills_used=skills_used,
            source_versions=source_versions,
            release_candidate_id=release_candidate_id,
        )

    def create_trace_evidence_card(
        self,
        task_id: str,
        session_id: str,
        project_id: str,
        trace_id: str,
        evidence_links: list[str],
        summary: str,
        *,
        skills_used: list[str] | None = None,
        source_versions: dict[str, str] | None = None,
        release_candidate_id: str | None = None,
    ) -> ArtifactRef:
        """Create a trace evidence artifact card."""

        return self._artifact(
            artifact_type=ArtifactType.TRACE_EVIDENCE,
            title="Trace Evidence",
            summary=summary,
            payload={"trace_id": trace_id, "evidence_links": evidence_links, "summary": summary},
            task_id=task_id,
            session_id=session_id,
            project_id=project_id,
            skills_used=skills_used,
            source_versions=source_versions,
            release_candidate_id=release_candidate_id,
        )

    def create_benchmark_card(
        self,
        task_id: str,
        session_id: str,
        project_id: str,
        baseline_id: str,
        candidate_id: str,
        metrics: dict[str, Any],
        *,
        skills_used: list[str] | None = None,
        source_versions: dict[str, str] | None = None,
        release_candidate_id: str | None = None,
    ) -> ArtifactRef:
        """Create a benchmark comparison artifact card."""

        return self._artifact(
            artifact_type=ArtifactType.BENCHMARK,
            title="Benchmark",
            summary=f"Baseline {baseline_id} vs {candidate_id}",
            payload={
                "baseline_id": baseline_id,
                "candidate_id": candidate_id,
                "metrics": metrics,
            },
            task_id=task_id,
            session_id=session_id,
            project_id=project_id,
            skills_used=skills_used,
            source_versions=source_versions,
            release_candidate_id=release_candidate_id,
        )

    def create_release_card(
        self,
        task_id: str,
        session_id: str,
        project_id: str,
        release_candidate_id: str,
        version: str,
        deployment_target: str,
        changelog: str,
        *,
        skills_used: list[str] | None = None,
        source_versions: dict[str, str] | None = None,
    ) -> ArtifactRef:
        """Create a release candidate artifact card."""

        return self._artifact(
            artifact_type=ArtifactType.RELEASE,
            title=f"Release {version}",
            summary=f"Release candidate {version}",
            payload={
                "release_candidate_id": release_candidate_id,
                "version": version,
                "deployment_target": deployment_target,
                "changelog": changelog,
            },
            task_id=task_id,
            session_id=session_id,
            project_id=project_id,
            skills_used=skills_used,
            source_versions=source_versions,
            release_candidate_id=release_candidate_id,
        )

    def _artifact(
        self,
        *,
        artifact_type: ArtifactType,
        title: str,
        summary: str,
        payload: dict[str, Any],
        task_id: str,
        session_id: str,
        project_id: str,
        skills_used: list[str] | None,
        source_versions: dict[str, str] | None,
        release_candidate_id: str | None,
    ) -> ArtifactRef:
        created_at = now_ts()
        provenance = {
            "task_id": task_id,
            "session_id": session_id,
            "skills_used": skills_used or [],
            "source_versions": source_versions or {},
            "release_candidate_id": release_candidate_id,
            "timestamp": created_at,
        }
        return ArtifactRef(
            task_id=task_id,
            session_id=session_id,
            project_id=project_id,
            artifact_type=artifact_type,
            title=title,
            summary=summary,
            payload={**payload, "provenance": provenance},
            skills_used=skills_used or [],
            source_versions=source_versions or {},
            release_candidate_id=release_candidate_id,
            created_at=created_at,
            updated_at=created_at,
        )

"""Tests for ArtifactCardFactory."""
from __future__ import annotations

import pytest

from builder.artifacts import ArtifactCardFactory
from builder.types import ArtifactType


@pytest.fixture
def factory():
    return ArtifactCardFactory()


def _base_ids():
    return {"task_id": "task-1", "session_id": "sess-1", "project_id": "proj-1"}


class TestPlanCard:
    def test_creates_plan_artifact(self, factory):
        ref = factory.create_plan_card(
            **_base_ids(),
            goal="Build a feature",
            assumptions=["Python 3.11", "No external deps"],
            targeted_artifacts=["src/feature.py"],
            expected_impact="High",
            risk_level="medium",
            required_approvals=["source_write"],
        )
        assert ref.artifact_type == ArtifactType.PLAN
        assert ref.summary == "Build a feature"
        assert ref.payload["goal"] == "Build a feature"
        assert "provenance" in ref.payload

    def test_provenance_fields(self, factory):
        ref = factory.create_plan_card(
            **_base_ids(),
            goal="Goal",
            assumptions=[],
            targeted_artifacts=[],
            expected_impact="Low",
            risk_level="low",
            required_approvals=[],
            skills_used=["skill-A"],
            source_versions={"agent.py": "abc123"},
        )
        prov = ref.payload["provenance"]
        assert prov["task_id"] == "task-1"
        assert prov["session_id"] == "sess-1"
        assert "skill-A" in prov["skills_used"]
        assert prov["source_versions"]["agent.py"] == "abc123"


class TestSourceDiffCard:
    def test_creates_source_diff(self, factory):
        files = [{"path": "a.py", "diff": "@@ -1 +1 @@\n-old\n+new"}]
        ref = factory.create_source_diff_card(**_base_ids(), files=files, summary="Fixed bug")
        assert ref.artifact_type == ArtifactType.SOURCE_DIFF
        assert ref.payload["files"] == files
        assert ref.payload["summary"] == "Fixed bug"

    def test_title_is_source_diff(self, factory):
        ref = factory.create_source_diff_card(**_base_ids(), files=[], summary="s")
        assert ref.title == "Source Diff"


class TestAdkGraphDiffCard:
    def test_creates_adk_graph_diff(self, factory):
        before = {"nodes": ["A"]}
        after = {"nodes": ["A", "B"]}
        ref = factory.create_adk_graph_diff_card(**_base_ids(), before_graph=before, after_graph=after, summary="Added node B")
        assert ref.artifact_type == ArtifactType.ADK_GRAPH_DIFF
        assert ref.payload["before_graph"] == before
        assert ref.payload["after_graph"] == after


class TestSkillCard:
    def test_creates_skill(self, factory):
        ref = factory.create_skill_card(
            **_base_ids(),
            name="my_skill",
            manifest={"description": "Does stuff"},
            effectiveness=0.92,
        )
        assert ref.artifact_type == ArtifactType.SKILL
        assert "my_skill" in ref.title
        assert ref.payload["effectiveness"] == 0.92

    def test_none_effectiveness(self, factory):
        ref = factory.create_skill_card(**_base_ids(), name="s", manifest={}, effectiveness=None)
        assert ref.payload["effectiveness"] is None


class TestGuardrailCard:
    def test_creates_guardrail(self, factory):
        ref = factory.create_guardrail_card(
            **_base_ids(),
            name="no_pii",
            attached_scope=["task-1"],
            failure_examples=["SSN leaked"],
        )
        assert ref.artifact_type == ArtifactType.GUARDRAIL
        assert ref.payload["name"] == "no_pii"
        assert "SSN leaked" in ref.payload["failure_examples"]


class TestEvalCard:
    def test_creates_eval(self, factory):
        ref = factory.create_eval_card(
            **_base_ids(),
            eval_bundle_id="bundle-1",
            hard_gate_passed=True,
            summary="All evals passed",
        )
        assert ref.artifact_type == ArtifactType.EVAL
        assert ref.payload["hard_gate_passed"] is True
        assert ref.payload["eval_bundle_id"] == "bundle-1"


class TestTraceEvidenceCard:
    def test_creates_trace_evidence(self, factory):
        ref = factory.create_trace_evidence_card(
            **_base_ids(),
            trace_id="trace-999",
            evidence_links=["link1", "link2"],
            summary="Trace shows regression",
        )
        assert ref.artifact_type == ArtifactType.TRACE_EVIDENCE
        assert ref.payload["trace_id"] == "trace-999"
        assert len(ref.payload["evidence_links"]) == 2


class TestBenchmarkCard:
    def test_creates_benchmark(self, factory):
        ref = factory.create_benchmark_card(
            **_base_ids(),
            baseline_id="base-1",
            candidate_id="cand-1",
            metrics={"quality": 0.88, "latency": 120.0},
        )
        assert ref.artifact_type == ArtifactType.BENCHMARK
        assert "base-1" in ref.summary
        assert ref.payload["metrics"]["quality"] == 0.88


class TestReleaseCard:
    def test_creates_release(self, factory):
        ref = factory.create_release_card(
            **_base_ids(),
            release_candidate_id="rc-1",
            version="2.0.0",
            deployment_target="prod",
            changelog="Major release",
        )
        assert ref.artifact_type == ArtifactType.RELEASE
        assert "2.0.0" in ref.title
        assert ref.payload["deployment_target"] == "prod"

    def test_provenance_has_release_candidate_id(self, factory):
        ref = factory.create_release_card(
            **_base_ids(),
            release_candidate_id="rc-42",
            version="1.0.0",
            deployment_target="staging",
            changelog="",
        )
        assert ref.release_candidate_id == "rc-42"
        assert ref.payload["provenance"]["release_candidate_id"] == "rc-42"


class TestProvenance:
    def test_all_cards_have_provenance(self, factory):
        cards = [
            factory.create_plan_card(**_base_ids(), goal="g", assumptions=[], targeted_artifacts=[], expected_impact="", risk_level="low", required_approvals=[]),
            factory.create_source_diff_card(**_base_ids(), files=[], summary="s"),
            factory.create_eval_card(**_base_ids(), eval_bundle_id="b", hard_gate_passed=True, summary="s"),
        ]
        for card in cards:
            assert "provenance" in card.payload
            assert card.payload["provenance"]["task_id"] == "task-1"

    def test_timestamps_are_set(self, factory):
        ref = factory.create_plan_card(**_base_ids(), goal="g", assumptions=[], targeted_artifacts=[], expected_impact="", risk_level="low", required_approvals=[])
        assert ref.created_at > 0
        assert ref.updated_at > 0

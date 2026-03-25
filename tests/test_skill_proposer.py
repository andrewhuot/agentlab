"""Tests for SkillAwareProposer (Track C)."""

from __future__ import annotations

import os

import pytest

from optimizer.proposer import Proposal, Proposer
from optimizer.skill_proposer import SkillAwareProposer, _dominant_failure_bucket
from registry.skill_store import SkillStore
from registry.skill_types import (
    EvalCriterion,
    MutationTemplate,
    Skill,
    SkillExample,
    TriggerCondition,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_skill(
    name: str,
    failure_family: str = "routing_error",
    proven_improvement: float = 0.1,
    success_rate: float = 0.8,
    metric_name: str | None = None,
    threshold: float | None = None,
    operator: str = "gt",
) -> Skill:
    """Build a minimal active Skill for use in tests."""
    trigger = TriggerCondition(
        failure_family=failure_family,
        metric_name=metric_name,
        threshold=threshold,
        operator=operator,
    )
    return Skill(
        name=name,
        version=1,
        description=f"Test skill: {name}",
        category="routing",
        platform="universal",
        target_surfaces=["routing"],
        mutations=[
            MutationTemplate(
                name=f"{name}_mut",
                mutation_type="routing_edit",
                target_surface="routing",
                description="Add routing keywords",
                template="add keyword: {keyword}",
            )
        ],
        examples=[
            SkillExample(
                name=f"{name}_ex",
                surface="routing",
                before="no keywords",
                after="has keywords",
                improvement=proven_improvement,
                context="unit test",
            )
        ],
        guardrails=["Test guardrail"],
        eval_criteria=[EvalCriterion(metric="composite_score", target=0.8, operator="gt")],
        triggers=[trigger],
        proven_improvement=proven_improvement,
        success_rate=success_rate,
        status="active",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def skill_store(tmp_path: object) -> SkillStore:
    db_path = os.path.join(str(tmp_path), "skills_test.db")
    store = SkillStore(db_path=db_path)
    yield store
    store.close()


@pytest.fixture
def base_proposer() -> Proposer:
    return Proposer(use_mock=True)


@pytest.fixture
def aware_proposer(base_proposer: Proposer, skill_store: SkillStore) -> SkillAwareProposer:
    return SkillAwareProposer(proposer=base_proposer, skill_store=skill_store)


_BASE_CONFIG: dict = {
    "routing": {"rules": [{"specialist": "orders", "keywords": ["order"]}]},
    "prompts": {"root": "You are a helpful agent."},
}

_EMPTY_METRICS: dict = {}
_EMPTY_SAMPLES: list = []
_EMPTY_PAST: list = []


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSkillAwareProposerEnrichment:
    """Verify skill context is correctly wired into proposals."""

    def test_propose_enriches_with_skills(
        self, aware_proposer: SkillAwareProposer, skill_store: SkillStore
    ) -> None:
        """Skills matching the dominant failure bucket appear in last_applied_skills."""
        skill = _make_skill("routing_fix", failure_family="routing_error")
        skill_store.register(skill)

        result = aware_proposer.propose(
            current_config=_BASE_CONFIG,
            health_metrics=_EMPTY_METRICS,
            failure_samples=_EMPTY_SAMPLES,
            failure_buckets={"routing_error": 5, "tool_failure": 0},
            past_attempts=_EMPTY_PAST,
        )

        assert "routing_fix" in aware_proposer.last_applied_skills
        # Proposal itself still comes through from base proposer
        assert result is not None
        assert isinstance(result, Proposal)

    def test_propose_with_no_matching_skills(
        self, aware_proposer: SkillAwareProposer, skill_store: SkillStore
    ) -> None:
        """Empty failure_buckets produces no applied skills."""
        skill = _make_skill("routing_fix", failure_family="routing_error")
        skill_store.register(skill)

        aware_proposer.propose(
            current_config=_BASE_CONFIG,
            health_metrics=_EMPTY_METRICS,
            failure_samples=_EMPTY_SAMPLES,
            failure_buckets={"routing_error": 0, "tool_failure": 0},
            past_attempts=_EMPTY_PAST,
        )

        assert aware_proposer.last_applied_skills == []

    def test_propose_delegates_to_base(
        self, aware_proposer: SkillAwareProposer
    ) -> None:
        """Base proposer is always called and returns a valid Proposal."""
        result = aware_proposer.propose(
            current_config=_BASE_CONFIG,
            health_metrics=_EMPTY_METRICS,
            failure_samples=_EMPTY_SAMPLES,
            failure_buckets={"routing_error": 3},
            past_attempts=_EMPTY_PAST,
        )

        assert result is not None
        assert isinstance(result, Proposal)
        assert result.change_description
        assert result.config_section
        assert isinstance(result.new_config, dict)

    def test_skill_guardrails_merged_with_provided(
        self, aware_proposer: SkillAwareProposer, skill_store: SkillStore
    ) -> None:
        """Skill guardrails are appended to the caller's guardrails list."""
        skill = _make_skill("safe_skill", failure_family="routing_error")
        skill_store.register(skill)

        # We need to capture what the base proposer receives; use a capturing wrapper
        captured: dict = {}

        class CapturingProposer:
            def propose(self_, *args, **kwargs) -> Proposal:
                captured.update(kwargs)
                return Proposal(
                    change_description="captured",
                    config_section="routing",
                    new_config={},
                    reasoning="ok",
                )

        aware_proposer.proposer = CapturingProposer()  # type: ignore[assignment]

        aware_proposer.propose(
            current_config=_BASE_CONFIG,
            health_metrics=_EMPTY_METRICS,
            failure_samples=_EMPTY_SAMPLES,
            failure_buckets={"routing_error": 2},
            past_attempts=_EMPTY_PAST,
            guardrails=["caller guardrail"],
        )

        guardrails_sent = captured.get("guardrails", [])
        assert "caller guardrail" in guardrails_sent
        assert "Test guardrail" in guardrails_sent


class TestRecordOutcome:
    """record_outcome delegates to the store and updates stats."""

    def test_record_outcome(
        self, aware_proposer: SkillAwareProposer, skill_store: SkillStore
    ) -> None:
        """record_outcome persists outcome and updates the skill's stats."""
        skill = _make_skill("learnable_skill", failure_family="tool_failure")
        skill_store.register(skill)

        aware_proposer.record_outcome("learnable_skill", improvement=0.15, success=True)

        updated = skill_store.get("learnable_skill")
        assert updated is not None
        assert updated.times_applied == 1
        assert updated.success_rate == 1.0
        assert updated.proven_improvement == pytest.approx(0.15)

    def test_record_multiple_outcomes_averages_correctly(
        self, aware_proposer: SkillAwareProposer, skill_store: SkillStore
    ) -> None:
        """Multiple outcomes produce correct success_rate and avg proven_improvement."""
        skill = _make_skill("multi_outcome", failure_family="tool_failure")
        skill_store.register(skill)

        aware_proposer.record_outcome("multi_outcome", improvement=0.20, success=True)
        aware_proposer.record_outcome("multi_outcome", improvement=0.10, success=True)
        aware_proposer.record_outcome("multi_outcome", improvement=0.05, success=False)

        updated = skill_store.get("multi_outcome")
        assert updated is not None
        assert updated.times_applied == 3
        assert updated.success_rate == pytest.approx(2 / 3)
        # proven_improvement is average of successful improvements only
        assert updated.proven_improvement == pytest.approx(0.15)


class TestGetRelevantSkillsSorting:
    """Skills are returned sorted by effectiveness (success_rate * proven_improvement)."""

    def test_get_relevant_skills_sorted_by_effectiveness(
        self, aware_proposer: SkillAwareProposer, skill_store: SkillStore
    ) -> None:
        """Top skill by success_rate * proven_improvement is first in last_applied_skills."""
        # effectiveness scores: low=0.4*0.1=0.04, mid=0.6*0.2=0.12, high=0.9*0.5=0.45
        skill_low = _make_skill(
            "low_skill", proven_improvement=0.1, success_rate=0.4
        )
        skill_mid = _make_skill(
            "mid_skill", proven_improvement=0.2, success_rate=0.6
        )
        skill_high = _make_skill(
            "high_skill", proven_improvement=0.5, success_rate=0.9
        )

        for s in (skill_low, skill_mid, skill_high):
            skill_store.register(s)

        aware_proposer.propose(
            current_config=_BASE_CONFIG,
            health_metrics=_EMPTY_METRICS,
            failure_samples=_EMPTY_SAMPLES,
            failure_buckets={"routing_error": 5},
            past_attempts=_EMPTY_PAST,
        )

        applied = aware_proposer.last_applied_skills
        assert applied[0] == "high_skill"
        assert applied[1] == "mid_skill"
        assert applied[2] == "low_skill"

    def test_skills_capped_at_five(
        self, aware_proposer: SkillAwareProposer, skill_store: SkillStore
    ) -> None:
        """At most 5 skills are applied regardless of how many match."""
        for i in range(8):
            s = _make_skill(f"skill_{i}", proven_improvement=0.1 * (i + 1), success_rate=0.8)
            skill_store.register(s)

        aware_proposer.propose(
            current_config=_BASE_CONFIG,
            health_metrics=_EMPTY_METRICS,
            failure_samples=_EMPTY_SAMPLES,
            failure_buckets={"routing_error": 3},
            past_attempts=_EMPTY_PAST,
        )

        assert len(aware_proposer.last_applied_skills) <= 5


class TestDominantFailureBucket:
    """Unit tests for the module-level helper."""

    def test_returns_none_for_all_zero(self) -> None:
        assert _dominant_failure_bucket({"a": 0, "b": 0}) is None

    def test_returns_none_for_empty(self) -> None:
        assert _dominant_failure_bucket({}) is None

    def test_returns_dominant_bucket(self) -> None:
        assert _dominant_failure_bucket({"routing_error": 5, "tool_failure": 2}) == "routing_error"

    def test_ignores_zero_buckets(self) -> None:
        assert _dominant_failure_bucket({"routing_error": 0, "tool_failure": 3}) == "tool_failure"

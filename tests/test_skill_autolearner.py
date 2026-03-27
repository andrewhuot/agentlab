"""Tests for automatic draft-skill synthesis from accepted attempts."""

from __future__ import annotations

from core.skills.store import SkillStore
from core.skills.types import SkillKind
from optimizer.skill_autolearner import SkillAutoLearner


def test_autolearner_creates_draft_skill(tmp_path) -> None:
    """Accepted attempt with sufficient lift should create a draft BUILD skill."""
    store = SkillStore(str(tmp_path / "skills.db"))
    learner = SkillAutoLearner(store=store, min_improvement=0.01)

    skill_id = learner.learn_from_accepted_attempt(
        attempt_id="atm-123",
        change_description="Strengthen routing keywords for billing flows",
        config_section="routing",
        config_diff='routing.rules[0].keywords += ["invoice", "refund"]',
        improvement=0.08,
        failure_family="routing_error",
    )

    assert skill_id is not None
    created = store.get(skill_id)
    assert created is not None
    assert created.kind == SkillKind.BUILD
    assert created.status == "draft"
    assert created.metadata.get("source_attempt_id") == "atm-123"


def test_autolearner_skips_low_improvement(tmp_path) -> None:
    """Below-threshold improvements should not generate draft skills."""
    store = SkillStore(str(tmp_path / "skills.db"))
    learner = SkillAutoLearner(store=store, min_improvement=0.05)

    skill_id = learner.learn_from_accepted_attempt(
        attempt_id="atm-low",
        change_description="Minor prompt punctuation change",
        config_section="prompts",
        config_diff="prompts.root += '.'",
        improvement=0.01,
        failure_family="unhelpful_response",
    )

    assert skill_id is None
    assert store.list(kind=SkillKind.BUILD, status="draft") == []


def test_autolearner_avoids_duplicate_draft_names(tmp_path) -> None:
    """Repeated learning from the same pattern should create at most one draft."""
    store = SkillStore(str(tmp_path / "skills.db"))
    learner = SkillAutoLearner(store=store, min_improvement=0.01)

    first = learner.learn_from_accepted_attempt(
        attempt_id="atm-1",
        change_description="Improve tool timeout handling",
        config_section="tools",
        config_diff="tools.lookup.timeout=2.0",
        improvement=0.06,
        failure_family="tool_failure",
    )
    second = learner.learn_from_accepted_attempt(
        attempt_id="atm-2",
        change_description="Improve tool timeout handling",
        config_section="tools",
        config_diff="tools.lookup.timeout=1.8",
        improvement=0.07,
        failure_family="tool_failure",
    )

    assert first is not None
    assert second is None
    drafts = store.list(kind=SkillKind.BUILD, status="draft")
    assert len(drafts) == 1

"""Tests for SkillLearner (Track C)."""

from __future__ import annotations

import os

import pytest

from registry.skill_learner import DraftSkill, SkillLearner
from registry.skill_store import SkillStore
from registry.skill_types import (
    EvalCriterion,
    MutationTemplate,
    Skill,
    SkillExample,
    TriggerCondition,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def skill_store(tmp_path: object) -> SkillStore:
    db_path = os.path.join(str(tmp_path), "learner_test.db")
    store = SkillStore(db_path=db_path)
    yield store
    store.close()


@pytest.fixture
def learner(skill_store: SkillStore) -> SkillLearner:
    return SkillLearner(skill_store=skill_store)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _accepted_attempt(
    attempt_id: str = "attempt-1",
    config_section: str = "prompts",
    change_description: str = "enhanced prompt clarity",
    score_before: float = 0.60,
    score_after: float = 0.75,
    config_diff: str = "",
) -> dict:
    return {
        "attempt_id": attempt_id,
        "status": "accepted",
        "config_section": config_section,
        "change_description": change_description,
        "score_before": score_before,
        "score_after": score_after,
        "config_diff": config_diff,
    }


def _rejected_attempt(attempt_id: str = "attempt-r") -> dict:
    return {
        "attempt_id": attempt_id,
        "status": "rejected",
        "config_section": "routing",
        "change_description": "add keyword",
        "score_before": 0.60,
        "score_after": 0.75,
    }


def _make_routing_skill(store: SkillStore) -> Skill:
    """Register a skill whose mutation targets 'routing' and return it."""
    skill = Skill(
        name="existing_routing_skill",
        version=1,
        description="Existing routing optimizer",
        category="routing",
        platform="universal",
        target_surfaces=["routing"],
        mutations=[
            MutationTemplate(
                name="routing_mut",
                mutation_type="routing_edit",
                target_surface="routing",
                description="Improve routing keywords",
            )
        ],
        examples=[
            SkillExample(
                name="routing_ex",
                surface="routing",
                before="sparse keywords",
                after="rich keywords",
                improvement=0.12,
                context="existing skill",
            )
        ],
        guardrails=["Monitor routing accuracy"],
        eval_criteria=[EvalCriterion(metric="composite_score", target=0.8, operator="gt")],
        triggers=[TriggerCondition(failure_family="routing_error")],
        proven_improvement=0.12,
        success_rate=0.85,
        status="active",
    )
    store.register(skill)
    return skill


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAnalyzeOptimization:
    """Core draft-skill generation logic."""

    def test_analyze_accepted_optimization(self, learner: SkillLearner) -> None:
        """An accepted attempt with positive improvement produces a DraftSkill."""
        attempt = _accepted_attempt()
        draft = learner.analyze_optimization(config_diff="", attempt=attempt)

        assert draft is not None
        assert isinstance(draft, DraftSkill)
        assert draft.skill.status == "draft"
        assert draft.skill.proven_improvement == pytest.approx(0.15)
        assert draft.source_attempt_id == "attempt-1"
        assert 0.0 < draft.confidence <= 1.0

    def test_analyze_rejected_optimization(self, learner: SkillLearner) -> None:
        """A rejected attempt always returns None."""
        attempt = _rejected_attempt()
        draft = learner.analyze_optimization(config_diff="", attempt=attempt)

        assert draft is None

    def test_analyze_no_improvement(self, learner: SkillLearner) -> None:
        """An accepted attempt where score_after <= score_before returns None."""
        attempt = _accepted_attempt(score_before=0.80, score_after=0.75)
        draft = learner.analyze_optimization(config_diff="", attempt=attempt)

        assert draft is None

    def test_analyze_zero_improvement(self, learner: SkillLearner) -> None:
        """Exactly equal scores (improvement == 0) also returns None."""
        attempt = _accepted_attempt(score_before=0.70, score_after=0.70)
        draft = learner.analyze_optimization(config_diff="", attempt=attempt)

        assert draft is None

    def test_draft_skill_fields_populated(self, learner: SkillLearner) -> None:
        """Draft skill has all required fields correctly populated."""
        attempt = _accepted_attempt(
            attempt_id="atm-42",
            config_section="routing",
            change_description="add shipping keyword to routing rules",
            score_before=0.50,
            score_after=0.70,
        )
        draft = learner.analyze_optimization(config_diff="diff here", attempt=attempt)

        assert draft is not None
        skill = draft.skill
        assert skill.author == "skill-learner"
        assert "learned" in skill.tags
        assert skill.category == "routing"
        assert skill.mutations[0].target_surface == "routing"
        assert skill.examples[0].improvement == pytest.approx(0.20)
        assert "atm-42" in skill.examples[0].context

    def test_draft_skill_confidence_capped_at_one(self, learner: SkillLearner) -> None:
        """Very large improvements cap confidence at 1.0."""
        attempt = _accepted_attempt(score_before=0.0, score_after=1.0)
        draft = learner.analyze_optimization(config_diff="", attempt=attempt)

        assert draft is not None
        assert draft.confidence == pytest.approx(1.0)

    def test_draft_skill_confidence_scales_with_improvement(
        self, learner: SkillLearner
    ) -> None:
        """Small improvements produce confidence < 1.0."""
        attempt = _accepted_attempt(score_before=0.60, score_after=0.61)
        draft = learner.analyze_optimization(config_diff="", attempt=attempt)

        assert draft is not None
        assert draft.confidence < 1.0


class TestMatchExistingSkill:
    """match_existing_skill finds skills by section and description keywords."""

    def test_match_existing_skill_by_section(
        self, learner: SkillLearner, skill_store: SkillStore
    ) -> None:
        """An attempt targeting 'routing' matches the existing routing skill."""
        _make_routing_skill(skill_store)

        attempt = _accepted_attempt(
            config_section="routing",
            change_description="add more routing keywords",
            score_before=0.55,
            score_after=0.70,
        )
        # analyze_optimization should match the existing skill and NOT create a draft
        draft = learner.analyze_optimization(config_diff="", attempt=attempt)

        assert draft is None  # Matched existing; no new draft

    def test_match_updates_existing_skill_stats(
        self, learner: SkillLearner, skill_store: SkillStore
    ) -> None:
        """When a match is found, the existing skill's stats are updated."""
        _make_routing_skill(skill_store)

        attempt = _accepted_attempt(
            config_section="routing",
            change_description="routing improvement",
            score_before=0.55,
            score_after=0.70,
        )
        learner.analyze_optimization(config_diff="", attempt=attempt)

        updated = skill_store.get("existing_routing_skill")
        assert updated is not None
        assert updated.times_applied == 1  # one outcome recorded

    def test_no_match_for_different_section(
        self, learner: SkillLearner, skill_store: SkillStore
    ) -> None:
        """An attempt with a different section does not match the routing skill."""
        _make_routing_skill(skill_store)

        result = learner.match_existing_skill("tools", "increase tool timeout value")
        assert result is None

    def test_match_existing_skill_returns_none_when_empty_store(
        self, learner: SkillLearner
    ) -> None:
        """Empty store always returns None."""
        result = learner.match_existing_skill("routing", "add keywords")
        assert result is None


class TestLearnFromHistory:
    """learn_from_history batch-processes attempt lists."""

    def test_learn_from_history_correct_draft_count(
        self, learner: SkillLearner
    ) -> None:
        """3 accepted-with-improvement, 1 rejected, 1 no-improvement → exactly 3 drafts."""
        attempts = [
            _accepted_attempt(
                attempt_id=f"ok-{i}",
                config_section="prompts",
                change_description=f"unique improvement {i} verbose",
                score_before=0.50,
                score_after=0.65,
            )
            for i in range(3)
        ] + [
            _rejected_attempt(attempt_id="rej-1"),
            _accepted_attempt(
                attempt_id="flat-1",
                score_before=0.70,
                score_after=0.65,
            ),
        ]

        drafts = learner.learn_from_history(attempts)

        assert len(drafts) == 3

    def test_learn_from_history_returns_empty_for_all_rejected(
        self, learner: SkillLearner
    ) -> None:
        """All-rejected attempts produce an empty draft list."""
        attempts = [_rejected_attempt(f"rej-{i}") for i in range(5)]
        drafts = learner.learn_from_history(attempts)
        assert drafts == []

    def test_learn_from_history_empty_input(self, learner: SkillLearner) -> None:
        """Empty list produces empty output."""
        assert learner.learn_from_history([]) == []

    def test_learn_from_history_draft_skills_are_valid(
        self, learner: SkillLearner
    ) -> None:
        """Each returned DraftSkill has a skill with status='draft'."""
        attempts = [
            _accepted_attempt(
                attempt_id=f"a-{i}",
                config_section="tools",
                change_description=f"timeout increase step {i} milliseconds",
                score_before=0.40,
                score_after=0.55,
            )
            for i in range(2)
        ]
        drafts = learner.learn_from_history(attempts)
        for draft in drafts:
            assert draft.skill.status == "draft"
            assert draft.skill.category == "latency"  # tools maps to latency


class TestGenerateSkillName:
    """Static method _generate_skill_name produces deterministic snake_case names."""

    def test_basic_description(self) -> None:
        name = SkillLearner._generate_skill_name("routing", "add keywords to routing rules")
        assert name.startswith("learned_")
        # stopwords and short words filtered; expect meaningful words
        assert "keywords" in name or "routing" in name or "rules" in name

    def test_empty_description_falls_back_to_section(self) -> None:
        name = SkillLearner._generate_skill_name("routing", "")
        assert name == "learned_routing"

    def test_empty_description_and_section(self) -> None:
        name = SkillLearner._generate_skill_name("", "")
        assert name == "learned_learned"

    def test_name_uses_snake_case(self) -> None:
        name = SkillLearner._generate_skill_name("prompts", "enhance detail thoroughness level")
        assert " " not in name
        assert name == name.lower()

    def test_name_capped_at_four_meaningful_words(self) -> None:
        name = SkillLearner._generate_skill_name(
            "routing",
            "alpha beta gamma delta epsilon zeta eta theta",
        )
        # prefix "learned_" plus at most 4 words joined by "_"
        parts = name.removeprefix("learned_").split("_")
        assert len(parts) <= 4

    def test_stopwords_filtered(self) -> None:
        name = SkillLearner._generate_skill_name("routing", "the best for routing")
        # "the", "for" are stopwords; "best" (4 chars) and "routing" should remain
        assert "the" not in name
        assert "for" not in name


class TestInferFailureFamily:
    """Static method _infer_failure_family maps sections to families."""

    @pytest.mark.parametrize("section,expected", [
        ("routing", "routing_error"),
        ("prompts", "unhelpful_response"),
        ("tools", "tool_failure"),
        ("thresholds", "timeout"),
        ("safety", "safety_violation"),
        ("unknown_section", None),
        ("", None),
    ])
    def test_infer_failure_family(self, section: str, expected: str | None) -> None:
        result = SkillLearner._infer_failure_family(section)
        assert result == expected

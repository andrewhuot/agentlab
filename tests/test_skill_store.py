"""Comprehensive tests for the Track A executable skills registry.

Tests cover the SkillStore CRUD operations, search/filter, recommendation
engine, outcome tracking, and full serialization round-trips.
"""

from __future__ import annotations

from typing import Any


from registry.skill_types import (
    EvalCriterion,
    MutationTemplate,
    Skill,
    SkillExample,
    TriggerCondition,
)
from registry.skill_store import SkillStore


# ---------------------------------------------------------------------------
# Helper factory
# ---------------------------------------------------------------------------


def _make_skill(
    name: str,
    category: str = "routing",
    platform: str = "universal",
    **overrides: Any,
) -> Skill:
    """Return a minimal but fully-valid Skill for testing."""
    defaults: dict[str, Any] = dict(
        name=name,
        version=0,  # will be overwritten by SkillStore.register
        description=f"Test skill: {name}",
        category=category,
        platform=platform,
        target_surfaces=["prompt", "system-prompt"],
        mutations=[
            MutationTemplate(
                name="inject-routing-hint",
                mutation_type="append",
                target_surface="system-prompt",
                description="Appends a routing hint to the system prompt.",
                template="[ROUTE: {destination}]",
                parameters={"destination": "tier-1"},
            )
        ],
        examples=[
            SkillExample(
                name="basic-routing-example",
                surface="system-prompt",
                before="You are a helpful assistant.",
                after="You are a helpful assistant. [ROUTE: tier-1]",
                improvement=0.12,
                context="Improved routing accuracy on ambiguous intents.",
            )
        ],
        guardrails=["no-pii", "no-hallucination"],
        eval_criteria=[
            EvalCriterion(metric="routing_accuracy", target=0.90, operator="gt", weight=1.0)
        ],
        triggers=[
            TriggerCondition(
                failure_family="misroute",
                metric_name="routing_accuracy",
                threshold=0.80,
                operator="lt",
            )
        ],
        author="test-suite",
        tags=["routing", "tier-1"],
        status="active",
    )
    defaults.update(overrides)
    return Skill(**defaults)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_register_and_get(tmp_path: Any) -> None:
    store = SkillStore(db_path=str(tmp_path / "test.db"))
    skill = _make_skill("intent-router")

    name, version = store.register(skill)

    assert name == "intent-router"
    assert version == 1

    retrieved = store.get("intent-router")
    assert retrieved is not None
    assert retrieved.name == "intent-router"
    assert retrieved.version == 1
    assert retrieved.category == "routing"
    assert retrieved.platform == "universal"
    assert retrieved.description == "Test skill: intent-router"
    assert retrieved.author == "test-suite"
    assert "routing" in retrieved.tags
    assert len(retrieved.mutations) == 1
    assert retrieved.mutations[0].name == "inject-routing-hint"
    assert len(retrieved.triggers) == 1
    assert retrieved.triggers[0].failure_family == "misroute"

    store.close()


def test_version_increment(tmp_path: Any) -> None:
    store = SkillStore(db_path=str(tmp_path / "test.db"))

    skill_v1 = _make_skill("dedup-skill")
    _, v1 = store.register(skill_v1)

    skill_v2 = _make_skill("dedup-skill", description="Updated dedup skill")
    _, v2 = store.register(skill_v2)

    assert v1 == 1
    assert v2 == 2

    # get() returns latest by default
    latest = store.get("dedup-skill")
    assert latest is not None
    assert latest.version == 2
    assert latest.description == "Updated dedup skill"

    # explicit version fetch
    old = store.get("dedup-skill", version=1)
    assert old is not None
    assert old.version == 1
    assert old.description == "Test skill: dedup-skill"

    store.close()


def test_list_by_category(tmp_path: Any) -> None:
    store = SkillStore(db_path=str(tmp_path / "test.db"))

    store.register(_make_skill("r1", category="routing"))
    store.register(_make_skill("s1", category="safety"))
    store.register(_make_skill("l1", category="latency"))

    routing = store.list(category="routing")
    assert len(routing) == 1
    assert routing[0].name == "r1"

    safety = store.list(category="safety")
    assert len(safety) == 1
    assert safety[0].name == "s1"

    all_skills = store.list()
    assert len(all_skills) == 3

    store.close()


def test_list_by_platform(tmp_path: Any) -> None:
    store = SkillStore(db_path=str(tmp_path / "test.db"))

    store.register(_make_skill("uni", platform="universal"))
    store.register(_make_skill("cx", platform="cx-agent-studio"))
    store.register(_make_skill("vtx", platform="vertex-ai"))

    universal = store.list(platform="universal")
    assert len(universal) == 1
    assert universal[0].name == "uni"

    cx = store.list(platform="cx-agent-studio")
    assert len(cx) == 1
    assert cx[0].name == "cx"

    store.close()


def test_search(tmp_path: Any) -> None:
    store = SkillStore(db_path=str(tmp_path / "test.db"))

    # Build minimal skills with tightly controlled, non-overlapping unique markers
    # so LIKE searches don't bleed across records.
    def _bare(name: str, unique_desc: str, category: str = "routing") -> Skill:
        """Minimal skill with no shared content across instances."""
        return Skill(
            name=name,
            version=0,
            description=unique_desc,
            category=category,
            platform="universal",
            target_surfaces=["prompt"],
            mutations=[
                MutationTemplate(
                    name=f"mut-{name}",
                    mutation_type="append",
                    target_surface="prompt",
                    description=f"Mutation for {name}",
                )
            ],
            examples=[
                SkillExample(
                    name=f"ex-{name}",
                    surface="prompt",
                    before="A",
                    after="B",
                    improvement=0.1,
                    context=f"Context for {name}",
                )
            ],
            guardrails=[],
            eval_criteria=[EvalCriterion(metric="accuracy", target=0.9)],
            triggers=[TriggerCondition(failure_family=f"family-{name}")],
            author="test-suite",
        )

    store.register(_bare("xrouter-skill", "UNIQUEMARKER_ROUTEDESC", category="routing"))
    store.register(_bare("xsafety-skill", "UNIQUEMARKER_SAFETYDESC", category="safety"))
    store.register(_bare("xcost-skill", "UNIQUEMARKER_TOKENDESC", category="cost"))

    # search by name substring — only xrouter-skill matches "xrouter"
    results = store.search("xrouter")
    assert len(results) == 1
    assert results[0].name == "xrouter-skill"

    # search by data content (unique description token)
    results = store.search("UNIQUEMARKER_TOKENDESC")
    assert len(results) == 1
    assert results[0].name == "xcost-skill"

    # search with category filter
    results = store.search("UNIQUEMARKER_SAFETYDESC", category="safety")
    assert len(results) == 1
    assert results[0].name == "xsafety-skill"

    # search with no matches
    results = store.search("xyznonexistent")
    assert results == []

    store.close()


def test_recommend_by_failure_family(tmp_path: Any) -> None:
    store = SkillStore(db_path=str(tmp_path / "test.db"))

    matching = _make_skill(
        "misroute-fix",
        triggers=[TriggerCondition(failure_family="misroute")],
    )
    non_matching = _make_skill(
        "safety-guard",
        triggers=[TriggerCondition(failure_family="unsafe-output")],
    )
    store.register(matching)
    store.register(non_matching)

    results = store.recommend(failure_family="misroute")
    assert len(results) == 1
    assert results[0].name == "misroute-fix"

    store.close()


def test_recommend_by_metric(tmp_path: Any) -> None:
    store = SkillStore(db_path=str(tmp_path / "test.db"))

    # This skill triggers when latency_p99 > 500
    latency_skill = _make_skill(
        "latency-reducer",
        category="latency",
        triggers=[
            TriggerCondition(metric_name="latency_p99", threshold=500.0, operator="gt")
        ],
    )
    # This skill triggers when error_rate < 0.01 (already good — won't fire)
    quality_skill = _make_skill(
        "quality-booster",
        category="quality",
        triggers=[
            TriggerCondition(metric_name="error_rate", threshold=0.01, operator="lt")
        ],
    )
    store.register(latency_skill)
    store.register(quality_skill)

    # latency_p99 = 600 exceeds threshold of 500
    results = store.recommend(metrics={"latency_p99": 600.0})
    names = [r.name for r in results]
    assert "latency-reducer" in names
    assert "quality-booster" not in names

    # error_rate = 0.005 < 0.01 — quality_skill should fire now
    results = store.recommend(metrics={"error_rate": 0.005})
    names = [r.name for r in results]
    assert "quality-booster" in names

    store.close()


def test_record_outcome_updates_stats(tmp_path: Any) -> None:
    store = SkillStore(db_path=str(tmp_path / "test.db"))

    store.register(_make_skill("tracked-skill"))

    store.record_outcome("tracked-skill", improvement=0.10, success=True)
    store.record_outcome("tracked-skill", improvement=0.20, success=True)
    store.record_outcome("tracked-skill", improvement=-0.05, success=False)

    skill = store.get("tracked-skill")
    assert skill is not None

    assert skill.times_applied == 3
    # 2 of 3 outcomes were successful
    assert abs(skill.success_rate - (2 / 3)) < 1e-9
    # proven_improvement = average of successful improvements = (0.10 + 0.20) / 2
    assert skill.proven_improvement is not None
    assert abs(skill.proven_improvement - 0.15) < 1e-9

    store.close()


def test_top_performers(tmp_path: Any) -> None:
    store = SkillStore(db_path=str(tmp_path / "test.db"))

    store.register(_make_skill("high-flier"))
    store.register(_make_skill("mid-tier"))
    store.register(_make_skill("under-performer"))
    store.register(_make_skill("no-outcomes"))  # never had outcomes — excluded

    # high-flier: proven=0.30, success_rate=1.0 → score 0.30
    store.record_outcome("high-flier", improvement=0.30, success=True)

    # mid-tier: proven=0.20, success_rate=0.5 → score 0.10
    store.record_outcome("mid-tier", improvement=0.40, success=True)
    store.record_outcome("mid-tier", improvement=0.00, success=False)

    # under-performer: proven=0.05, success_rate=1.0 → score 0.05
    store.record_outcome("under-performer", improvement=0.05, success=True)

    top = store.top_performers(n=10)
    names = [s.name for s in top]

    assert "no-outcomes" not in names
    assert len(top) == 3
    assert top[0].name == "high-flier"
    assert top[1].name == "mid-tier"
    assert top[2].name == "under-performer"

    store.close()


def test_skill_serialization_roundtrip(tmp_path: Any) -> None:
    original = _make_skill(
        "roundtrip-skill",
        tags=["alpha", "beta"],
        proven_improvement=0.25,
        times_applied=5,
        success_rate=0.8,
    )
    original.version = 1  # simulate registered state

    data = original.to_dict()
    restored = Skill.from_dict(data)

    assert restored.name == original.name
    assert restored.version == original.version
    assert restored.description == original.description
    assert restored.category == original.category
    assert restored.platform == original.platform
    assert restored.target_surfaces == original.target_surfaces
    assert restored.guardrails == original.guardrails
    assert restored.author == original.author
    assert restored.tags == original.tags
    assert restored.proven_improvement == original.proven_improvement
    assert restored.times_applied == original.times_applied
    assert restored.success_rate == original.success_rate
    assert restored.status == original.status

    # Nested dataclasses
    assert len(restored.mutations) == 1
    assert restored.mutations[0].name == original.mutations[0].name
    assert restored.mutations[0].mutation_type == original.mutations[0].mutation_type
    assert restored.mutations[0].parameters == original.mutations[0].parameters

    assert len(restored.examples) == 1
    assert restored.examples[0].before == original.examples[0].before
    assert restored.examples[0].improvement == original.examples[0].improvement

    assert len(restored.triggers) == 1
    assert restored.triggers[0].failure_family == original.triggers[0].failure_family
    assert restored.triggers[0].threshold == original.triggers[0].threshold
    assert restored.triggers[0].operator == original.triggers[0].operator

    assert len(restored.eval_criteria) == 1
    assert restored.eval_criteria[0].metric == original.eval_criteria[0].metric
    assert restored.eval_criteria[0].target == original.eval_criteria[0].target

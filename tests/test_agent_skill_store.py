"""Tests for AgentSkillStore and SkillValidator."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from agent_skills.store import AgentSkillStore
from agent_skills.types import GeneratedFile, GeneratedSkill, SkillGap
from agent_skills.validator import SkillValidator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_skill(
    skill_id: str = "skill-001",
    gap_id: str = "gap-001",
    platform: str = "adk",
    skill_type: str = "tool",
    name: str = "my_tool",
    description: str = "Does something useful",
    source_code: str | None = None,
    config_yaml: str | None = None,
    status: str = "draft",
) -> GeneratedSkill:
    """Build a minimal GeneratedSkill for tests."""
    return GeneratedSkill(
        skill_id=skill_id,
        gap_id=gap_id,
        platform=platform,
        skill_type=skill_type,
        name=name,
        description=description,
        source_code=source_code,
        config_yaml=config_yaml,
        files=[],
        eval_criteria=[{"metric": "task_success", "threshold": 0.8}],
        estimated_improvement=0.15,
        confidence="high",
        status=status,
        review_notes="",
        created_at=time.time(),
    )


def _make_gap(gap_id: str = "gap-001", suggested_name: str = "my_tool") -> SkillGap:
    """Build a minimal SkillGap for tests."""
    return SkillGap(
        gap_id=gap_id,
        gap_type="missing_tool",
        description="Agent cannot look up order status",
        evidence=["conv-1", "conv-2"],
        failure_family="tool_error",
        frequency=5,
        impact_score=0.7,
        suggested_name=suggested_name,
        suggested_platform="adk",
    )


# ---------------------------------------------------------------------------
# AgentSkillStore tests
# ---------------------------------------------------------------------------


def test_save_and_get(tmp_path: Path) -> None:
    """Save a GeneratedSkill and retrieve it; all fields must round-trip correctly."""
    store = AgentSkillStore(db_path=str(tmp_path / "test.db"))
    skill = _make_skill(
        skill_id="sk-1",
        gap_id="g-1",
        platform="cx",
        skill_type="playbook",
        name="order_lookup",
        description="Looks up order status",
        source_code="def order_lookup(order_id: str) -> str:\n    return order_id",
        status="draft",
    )
    skill.files = [
        GeneratedFile(path="tools/order_lookup.py", content="# stub", is_new=True, diff=None)
    ]

    store.save(skill)
    retrieved = store.get("sk-1")

    assert retrieved is not None
    assert retrieved.skill_id == "sk-1"
    assert retrieved.gap_id == "g-1"
    assert retrieved.platform == "cx"
    assert retrieved.skill_type == "playbook"
    assert retrieved.name == "order_lookup"
    assert retrieved.description == "Looks up order status"
    assert retrieved.source_code == skill.source_code
    assert retrieved.status == "draft"
    assert retrieved.confidence == "high"
    assert retrieved.estimated_improvement == pytest.approx(0.15)
    assert len(retrieved.files) == 1
    assert retrieved.files[0].path == "tools/order_lookup.py"
    assert retrieved.files[0].is_new is True
    assert retrieved.eval_criteria == [{"metric": "task_success", "threshold": 0.8}]


def test_list_empty(tmp_path: Path) -> None:
    """An empty store returns an empty list."""
    store = AgentSkillStore(db_path=str(tmp_path / "test.db"))
    assert store.list() == []


def test_list_with_filters(tmp_path: Path) -> None:
    """Filter by status and platform returns only matching skills."""
    store = AgentSkillStore(db_path=str(tmp_path / "test.db"))

    store.save(_make_skill(skill_id="s1", platform="adk", status="draft"))
    store.save(_make_skill(skill_id="s2", platform="cx", status="draft"))
    store.save(_make_skill(skill_id="s3", platform="adk", status="approved"))
    store.save(_make_skill(skill_id="s4", platform="cx", status="approved"))

    # Filter by status only
    drafts = store.list(status="draft")
    assert len(drafts) == 2
    assert all(s.status == "draft" for s in drafts)

    # Filter by platform only
    adk_skills = store.list(platform="adk")
    assert len(adk_skills) == 2
    assert all(s.platform == "adk" for s in adk_skills)

    # Filter by both
    adk_approved = store.list(status="approved", platform="adk")
    assert len(adk_approved) == 1
    assert adk_approved[0].skill_id == "s3"

    # No match
    assert store.list(status="rejected") == []


def test_approve(tmp_path: Path) -> None:
    """Approve a draft skill; status must change to 'approved'."""
    store = AgentSkillStore(db_path=str(tmp_path / "test.db"))
    store.save(_make_skill(skill_id="sk-approve", status="draft"))

    result = store.approve("sk-approve")

    assert result is True
    skill = store.get("sk-approve")
    assert skill is not None
    assert skill.status == "approved"


def test_reject_with_reason(tmp_path: Path) -> None:
    """Reject a skill with a reason; status and review_notes must be updated."""
    store = AgentSkillStore(db_path=str(tmp_path / "test.db"))
    store.save(_make_skill(skill_id="sk-reject", status="draft"))

    result = store.reject("sk-reject", reason="Does not handle edge cases")

    assert result is True
    skill = store.get("sk-reject")
    assert skill is not None
    assert skill.status == "rejected"
    assert skill.review_notes == "Does not handle edge cases"


def test_approve_nonexistent_returns_false(tmp_path: Path) -> None:
    """Approving a nonexistent skill_id returns False."""
    store = AgentSkillStore(db_path=str(tmp_path / "test.db"))
    assert store.approve("no-such-id") is False


def test_reject_nonexistent_returns_false(tmp_path: Path) -> None:
    """Rejecting a nonexistent skill_id returns False."""
    store = AgentSkillStore(db_path=str(tmp_path / "test.db"))
    assert store.reject("no-such-id", reason="n/a") is False


def test_list_by_gap(tmp_path: Path) -> None:
    """list_by_gap returns only skills belonging to the specified gap."""
    store = AgentSkillStore(db_path=str(tmp_path / "test.db"))

    store.save(_make_skill(skill_id="s1", gap_id="gap-A"))
    store.save(_make_skill(skill_id="s2", gap_id="gap-A"))
    store.save(_make_skill(skill_id="s3", gap_id="gap-B"))

    gap_a_skills = store.list_by_gap("gap-A")
    assert len(gap_a_skills) == 2
    assert all(s.gap_id == "gap-A" for s in gap_a_skills)

    gap_b_skills = store.list_by_gap("gap-B")
    assert len(gap_b_skills) == 1
    assert gap_b_skills[0].skill_id == "s3"

    assert store.list_by_gap("gap-C") == []


def test_save_gap_and_list(tmp_path: Path) -> None:
    """Save SkillGap objects and list them back as dicts."""
    store = AgentSkillStore(db_path=str(tmp_path / "test.db"))

    gap1 = _make_gap(gap_id="g-1", suggested_name="tool_alpha")
    gap2 = _make_gap(gap_id="g-2", suggested_name="tool_beta")

    store.save_gap(gap1)
    store.save_gap(gap2)

    gaps = store.list_gaps()
    assert len(gaps) == 2
    gap_ids = {g["gap_id"] for g in gaps}
    assert gap_ids == {"g-1", "g-2"}
    names = {g["suggested_name"] for g in gaps}
    assert names == {"tool_alpha", "tool_beta"}


def test_get_nonexistent_returns_none(tmp_path: Path) -> None:
    """get() on a missing skill_id returns None."""
    store = AgentSkillStore(db_path=str(tmp_path / "test.db"))
    assert store.get("does-not-exist") is None


# ---------------------------------------------------------------------------
# SkillValidator tests
# ---------------------------------------------------------------------------


def test_validator_valid_python(tmp_path: Path) -> None:
    """A skill with valid Python source passes validation."""
    validator = SkillValidator()
    skill = _make_skill(
        source_code='def fetch_order(order_id: str) -> str:\n    """Look up an order."""\n    return order_id',
    )
    result = validator.validate(skill)
    assert result.valid is True
    assert result.errors == []


def test_validator_invalid_python(tmp_path: Path) -> None:
    """A skill with a Python syntax error fails validation with an error message."""
    validator = SkillValidator()
    skill = _make_skill(source_code="def broken(\n    # unclosed")
    result = validator.validate(skill)
    assert result.valid is False
    assert any("Python syntax error" in e for e in result.errors)


def test_validator_valid_yaml(tmp_path: Path) -> None:
    """A skill with valid YAML config passes validation."""
    validator = SkillValidator()
    skill = _make_skill(config_yaml="name: my_playbook\nsteps:\n  - step1\n  - step2\n")
    result = validator.validate(skill)
    assert result.valid is True
    assert result.errors == []


def test_validator_invalid_yaml(tmp_path: Path) -> None:
    """A skill with invalid YAML fails validation with an error message."""
    validator = SkillValidator()
    skill = _make_skill(config_yaml="key: [unclosed bracket\n  bad: yaml")
    result = validator.validate(skill)
    assert result.valid is False
    assert any("YAML parse error" in e for e in result.errors)


def test_validator_unfilled_placeholders(tmp_path: Path) -> None:
    """Source code containing Jinja2-style placeholders fails validation."""
    validator = SkillValidator()
    skill = _make_skill(source_code="def tool():\n    return {{ placeholder }}")
    result = validator.validate(skill)
    assert result.valid is False
    assert any("Jinja2" in e for e in result.errors)


def test_validator_unfilled_block_placeholders(tmp_path: Path) -> None:
    """Source code containing Jinja2 block tags fails validation."""
    validator = SkillValidator()
    skill = _make_skill(source_code="{% for item in items %}\ndo_something()\n{% endfor %}")
    result = validator.validate(skill)
    assert result.valid is False
    assert any("Jinja2" in e for e in result.errors)


def test_validator_name_collision(tmp_path: Path) -> None:
    """validate_name detects a conflict against known_names."""
    validator = SkillValidator()
    result = validator.validate_name("existing_tool", known_names=["existing_tool", "other_tool"])
    assert result.valid is False
    assert any("conflicts" in e for e in result.errors)


def test_validator_name_no_collision(tmp_path: Path) -> None:
    """validate_name passes when name is not in known_names."""
    validator = SkillValidator()
    result = validator.validate_name("new_tool", known_names=["existing_tool"])
    assert result.valid is True
    assert result.errors == []


def test_validator_missing_name(tmp_path: Path) -> None:
    """A skill with an empty name produces a validation error."""
    validator = SkillValidator()
    skill = _make_skill(name="")
    result = validator.validate(skill)
    assert result.valid is False
    assert any("name" in e.lower() for e in result.errors)


def test_validator_missing_description(tmp_path: Path) -> None:
    """A skill with an empty description produces a validation error."""
    validator = SkillValidator()
    skill = _make_skill(description="")
    result = validator.validate(skill)
    assert result.valid is False
    assert any("description" in e.lower() for e in result.errors)


def test_validator_missing_skill_type(tmp_path: Path) -> None:
    """A skill with an empty skill_type produces a validation error."""
    validator = SkillValidator()
    skill = _make_skill(skill_type="")
    result = validator.validate(skill)
    assert result.valid is False
    assert any("type" in e.lower() for e in result.errors)


def test_validator_python_missing_type_hints_produces_warnings(tmp_path: Path) -> None:
    """Functions without type annotations generate warnings but not errors."""
    validator = SkillValidator()
    skill = _make_skill(
        source_code='def fetch_order(order_id):\n    """Look up an order."""\n    return order_id',
    )
    result = validator.validate(skill)
    # Missing annotations are warnings, not errors — still valid
    assert result.valid is True
    assert any("annotation" in w.lower() or "type" in w.lower() for w in result.warnings)


def test_validator_to_dict(tmp_path: Path) -> None:
    """ValidationResult.to_dict returns the expected structure."""
    validator = SkillValidator()
    skill = _make_skill(name="")
    result = validator.validate(skill)
    d = result.to_dict()
    assert "valid" in d
    assert "errors" in d
    assert "warnings" in d
    assert d["valid"] is False
    assert isinstance(d["errors"], list)
    assert isinstance(d["warnings"], list)

"""Tests for skill promotion workflow."""

import time
import pytest
from core.skills.promotion import SkillPromotionWorkflow, PromotionRecord
from core.skills.store import SkillStore
from core.skills.types import Skill, SkillKind, EffectivenessMetrics


def test_list_draft_skills(tmp_path):
    """Test listing draft skills with metrics."""
    store = SkillStore(db_path=str(tmp_path / "skills.db"))
    workflow = SkillPromotionWorkflow(store=store, reviewer="test_user")

    # Create draft skills
    draft1 = Skill(
        id="draft1",
        name="test_draft_1",
        kind=SkillKind.BUILD,
        version="1.0.0",
        description="Test draft skill 1",
        status="draft",
        effectiveness=EffectivenessMetrics(
            times_applied=10,
            success_count=8,
            success_rate=0.8,
            avg_improvement=0.05,
        ),
        metadata={
            "source_attempt_id": "attempt_123",
            "source_improvement": 0.05,
        },
    )

    draft2 = Skill(
        id="draft2",
        name="test_draft_2",
        kind=SkillKind.BUILD,
        version="1.0.0",
        description="Test draft skill 2",
        status="draft",
        effectiveness=EffectivenessMetrics(
            times_applied=5,
            success_count=2,
            success_rate=0.4,
            avg_improvement=0.02,
        ),
        metadata={
            "source_attempt_id": "attempt_456",
            "source_improvement": 0.02,
        },
    )

    store.create(draft1)
    store.create(draft2)

    # List all drafts
    drafts = workflow.list_draft_skills()
    assert len(drafts) == 2

    # Should be sorted by effectiveness
    assert drafts[0]["skill"].id == "draft1"  # Higher effectiveness
    assert drafts[1]["skill"].id == "draft2"

    # Verify structure
    assert "source" in drafts[0]
    assert "success_rate" in drafts[0]
    assert drafts[0]["source"] == "attempt_123"
    assert drafts[0]["success_rate"] == 0.8

    # Filter by min effectiveness
    filtered = workflow.list_draft_skills(min_effectiveness=0.5)
    assert len(filtered) == 1
    assert filtered[0]["skill"].id == "draft1"


def test_promote_skill(tmp_path):
    """Test promoting a draft skill to active."""
    store = SkillStore(db_path=str(tmp_path / "skills.db"))
    workflow = SkillPromotionWorkflow(store=store, reviewer="test_user")

    # Create draft skill
    draft = Skill(
        id="draft_promote",
        name="test_promote",
        kind=SkillKind.BUILD,
        version="1.0.0",
        description="Test promotion",
        status="draft",
    )
    store.create(draft)

    # Promote
    success = workflow.promote_skill("draft_promote", reason="Looks good")
    assert success is True

    # Verify status changed
    promoted = store.get("draft_promote")
    assert promoted is not None
    assert promoted.status == "active"

    # Check promotion history
    history = workflow.get_promotion_history()
    assert len(history) == 1
    assert history[0]["action"] == "promoted"
    assert history[0]["skill_id"] == "draft_promote"
    assert history[0]["reason"] == "Looks good"


def test_archive_skill(tmp_path):
    """Test archiving (rejecting) a draft skill."""
    store = SkillStore(db_path=str(tmp_path / "skills.db"))
    workflow = SkillPromotionWorkflow(store=store, reviewer="test_user")

    # Create draft skill
    draft = Skill(
        id="draft_archive",
        name="test_archive",
        kind=SkillKind.BUILD,
        version="1.0.0",
        description="Test archival",
        status="draft",
    )
    store.create(draft)

    # Archive
    success = workflow.archive_skill("draft_archive", reason="Not effective enough")
    assert success is True

    # Verify status changed
    archived = store.get("draft_archive")
    assert archived is not None
    assert archived.status == "archived"
    assert archived.metadata["archived_reason"] == "Not effective enough"

    # Check promotion history
    history = workflow.get_promotion_history()
    assert len(history) == 1
    assert history[0]["action"] == "archived"
    assert history[0]["reason"] == "Not effective enough"


def test_edit_skill(tmp_path):
    """Test editing a draft skill before promotion."""
    store = SkillStore(db_path=str(tmp_path / "skills.db"))
    workflow = SkillPromotionWorkflow(store=store, reviewer="test_user")

    # Create draft skill
    draft = Skill(
        id="draft_edit",
        name="test_edit",
        kind=SkillKind.BUILD,
        version="1.0.0",
        description="Original description",
        status="draft",
        domain="general",
    )
    store.create(draft)

    # Edit without promoting
    updates = {
        "name": "edited_name",
        "description": "New description",
        "domain": "quality",
    }
    success = workflow.edit_skill("draft_edit", updates, promote_after_edit=False)
    assert success is True

    # Verify changes
    edited = store.get("draft_edit")
    assert edited is not None
    assert edited.name == "edited_name"
    assert edited.description == "New description"
    assert edited.domain == "quality"
    assert edited.status == "draft"  # Still draft

    # Check history
    history = workflow.get_promotion_history()
    assert len(history) == 1
    assert history[0]["action"] == "edited"
    assert "changes" in history[0]


def test_edit_and_promote(tmp_path):
    """Test editing and promoting in one action."""
    store = SkillStore(db_path=str(tmp_path / "skills.db"))
    workflow = SkillPromotionWorkflow(store=store, reviewer="test_user")

    # Create draft skill
    draft = Skill(
        id="draft_edit_promote",
        name="test_edit_promote",
        kind=SkillKind.BUILD,
        version="1.0.0",
        description="Original",
        status="draft",
    )
    store.create(draft)

    # Edit and promote
    updates = {"description": "Edited"}
    success = workflow.edit_skill("draft_edit_promote", updates, promote_after_edit=True)
    assert success is True

    # Verify
    skill = store.get("draft_edit_promote")
    assert skill is not None
    assert skill.description == "Edited"
    assert skill.status == "active"  # Promoted

    # Check history
    history = workflow.get_promotion_history()
    assert history[0]["action"] == "edited_and_promoted"


def test_get_draft_details(tmp_path):
    """Test getting detailed information about a draft."""
    store = SkillStore(db_path=str(tmp_path / "skills.db"))
    workflow = SkillPromotionWorkflow(store=store, reviewer="test_user")

    # Create draft with rich metadata
    draft = Skill(
        id="draft_details",
        name="test_details",
        kind=SkillKind.BUILD,
        version="1.0.0",
        description="Test",
        status="draft",
        effectiveness=EffectivenessMetrics(
            times_applied=15,
            success_count=12,
            success_rate=0.8,
            avg_improvement=0.08,
        ),
        metadata={
            "source_attempt_id": "attempt_789",
            "source_config_section": "routing",
            "source_improvement": 0.08,
        },
    )
    store.create(draft)

    # Get details
    details = workflow.get_draft_details("draft_details")
    assert details is not None
    assert details["skill"].id == "draft_details"
    assert details["source"] == "attempt_789"
    assert details["source_section"] == "routing"
    assert details["source_improvement"] == 0.08
    assert details["effectiveness"]["success_rate"] == 0.8


def test_promotion_stats(tmp_path):
    """Test getting aggregate promotion statistics."""
    store = SkillStore(db_path=str(tmp_path / "skills.db"))
    workflow = SkillPromotionWorkflow(store=store, reviewer="test_user")

    # Create various skills
    draft = Skill(id="d1", name="draft", kind=SkillKind.BUILD, version="1.0.0", description="", status="draft")
    active = Skill(id="a1", name="active", kind=SkillKind.BUILD, version="1.0.0", description="", status="active")
    archived = Skill(id="ar1", name="archived", kind=SkillKind.BUILD, version="1.0.0", description="", status="archived")

    store.create(draft)
    store.create(active)
    store.create(archived)

    # Get stats
    stats = workflow.get_promotion_stats()
    assert stats["total_drafts"] == 1
    assert stats["total_active"] == 1
    assert stats["total_archived"] == 1


def test_bulk_promote(tmp_path):
    """Test bulk promotion of multiple skills."""
    store = SkillStore(db_path=str(tmp_path / "skills.db"))
    workflow = SkillPromotionWorkflow(store=store, reviewer="test_user")

    # Create multiple drafts
    for i in range(3):
        draft = Skill(
            id=f"draft_{i}",
            name=f"test_{i}",
            kind=SkillKind.BUILD,
            version="1.0.0",
            description="",
            status="draft",
        )
        store.create(draft)

    # Bulk promote
    results = workflow.bulk_promote(["draft_0", "draft_1", "draft_2"], reason="Batch approved")
    assert results["draft_0"] is True
    assert results["draft_1"] is True
    assert results["draft_2"] is True

    # Verify all promoted
    for i in range(3):
        skill = store.get(f"draft_{i}")
        assert skill.status == "active"


def test_promote_nonexistent_skill(tmp_path):
    """Test promoting a skill that doesn't exist."""
    store = SkillStore(db_path=str(tmp_path / "skills.db"))
    workflow = SkillPromotionWorkflow(store=store, reviewer="test_user")

    success = workflow.promote_skill("nonexistent", reason="Test")
    assert success is False


def test_promote_non_draft_skill(tmp_path):
    """Test promoting a skill that's not a draft."""
    store = SkillStore(db_path=str(tmp_path / "skills.db"))
    workflow = SkillPromotionWorkflow(store=store, reviewer="test_user")

    # Create active skill
    active = Skill(
        id="already_active",
        name="active",
        kind=SkillKind.BUILD,
        version="1.0.0",
        description="",
        status="active",
    )
    store.create(active)

    # Try to promote (should fail)
    success = workflow.promote_skill("already_active", reason="Test")
    assert success is False

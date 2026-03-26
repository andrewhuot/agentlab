"""Tests for knowledge mining and knowledge store."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from observer.knowledge_store import KnowledgeStore


class TestKnowledgeStore:
    """Test knowledge store CRUD operations."""

    def test_create_and_get_entry(self, tmp_path: Path):
        """Test creating and retrieving a knowledge entry."""
        store = KnowledgeStore(db_path=str(tmp_path / "knowledge.db"))

        entry = {
            "pattern_id": "test-001",
            "pattern_type": "tool_usage",
            "description": "Successful tool sequence",
            "evidence_conversations": ["conv-1", "conv-2", "conv-3"],
            "confidence": 0.85,
            "applicable_intents": ["billing"],
            "suggested_application": "tool_ordering",
            "status": "draft",
        }

        store.create(entry)

        retrieved = store.get("test-001")
        assert retrieved is not None
        assert retrieved["pattern_id"] == "test-001"
        assert retrieved["pattern_type"] == "tool_usage"
        assert retrieved["confidence"] == 0.85
        assert len(retrieved["evidence_conversations"]) == 3

    def test_list_entries(self, tmp_path: Path):
        """Test listing knowledge entries."""
        store = KnowledgeStore(db_path=str(tmp_path / "knowledge.db"))

        # Create multiple entries
        for i in range(5):
            entry = {
                "pattern_id": f"test-{i:03d}",
                "pattern_type": "tool_usage",
                "description": f"Pattern {i}",
                "evidence_conversations": [f"conv-{i}"],
                "confidence": 0.5 + (i * 0.1),
                "applicable_intents": ["general"],
                "suggested_application": "tool_ordering",
                "status": "draft",
            }
            store.create(entry)

        entries = store.list()
        assert len(entries) == 5

    def test_list_entries_with_status_filter(self, tmp_path: Path):
        """Test listing entries filtered by status."""
        store = KnowledgeStore(db_path=str(tmp_path / "knowledge.db"))

        # Create entries with different statuses
        for i in range(3):
            store.create({
                "pattern_id": f"draft-{i}",
                "pattern_type": "tool_usage",
                "description": f"Draft pattern {i}",
                "evidence_conversations": [],
                "confidence": 0.7,
                "applicable_intents": [],
                "suggested_application": "tool_ordering",
                "status": "draft",
            })

        for i in range(2):
            store.create({
                "pattern_id": f"reviewed-{i}",
                "pattern_type": "phrasing",
                "description": f"Reviewed pattern {i}",
                "evidence_conversations": [],
                "confidence": 0.8,
                "applicable_intents": [],
                "suggested_application": "few_shot",
                "status": "reviewed",
            })

        draft_entries = store.list(status="draft")
        assert len(draft_entries) == 3

        reviewed_entries = store.list(status="reviewed")
        assert len(reviewed_entries) == 2

    def test_update_status(self, tmp_path: Path):
        """Test updating entry status."""
        store = KnowledgeStore(db_path=str(tmp_path / "knowledge.db"))

        entry = {
            "pattern_id": "test-status",
            "pattern_type": "tool_usage",
            "description": "Test pattern",
            "evidence_conversations": [],
            "confidence": 0.7,
            "applicable_intents": [],
            "suggested_application": "tool_ordering",
            "status": "draft",
        }
        store.create(entry)

        # Update status
        success = store.update_status("test-status", "reviewed")
        assert success

        # Verify update
        updated = store.get("test-status")
        assert updated["status"] == "reviewed"

    def test_mark_applied(self, tmp_path: Path):
        """Test marking entry as applied with impact score."""
        store = KnowledgeStore(db_path=str(tmp_path / "knowledge.db"))

        entry = {
            "pattern_id": "test-apply",
            "pattern_type": "tool_usage",
            "description": "Test pattern",
            "evidence_conversations": [],
            "confidence": 0.8,
            "applicable_intents": [],
            "suggested_application": "tool_ordering",
            "status": "reviewed",
        }
        store.create(entry)

        # Mark as applied with impact score
        success = store.mark_applied("test-apply", impact_score=0.05)
        assert success

        # Verify update
        updated = store.get("test-apply")
        assert updated["status"] == "applied"
        assert updated["applied_at"] is not None
        assert updated["impact_score"] == 0.05

    def test_get_nonexistent_entry(self, tmp_path: Path):
        """Test getting nonexistent entry returns None."""
        store = KnowledgeStore(db_path=str(tmp_path / "knowledge.db"))
        entry = store.get("nonexistent")
        assert entry is None

    def test_knowledge_store_persistence(self, tmp_path: Path):
        """Test that knowledge store persists data across instances."""
        store1 = KnowledgeStore(db_path=str(tmp_path / "knowledge.db"))

        entry = {
            "pattern_id": "persist-test",
            "pattern_type": "tool_usage",
            "description": "Test persistence",
            "evidence_conversations": ["conv-1"],
            "confidence": 0.8,
            "applicable_intents": ["test"],
            "suggested_application": "tool_ordering",
            "status": "draft",
        }
        store1.create(entry)

        # Create new instance with same DB
        store2 = KnowledgeStore(db_path=str(tmp_path / "knowledge.db"))
        retrieved = store2.get("persist-test")

        assert retrieved is not None
        assert retrieved["pattern_id"] == "persist-test"

    def test_apply_knowledge_entry_workflow(self, tmp_path: Path):
        """Test workflow for applying a knowledge entry."""
        knowledge_store = KnowledgeStore(db_path=str(tmp_path / "knowledge.db"))

        # Create entry
        entry = {
            "pattern_id": "workflow-test",
            "pattern_type": "tool_usage",
            "description": "Effective tool sequence",
            "evidence_conversations": ["conv-1", "conv-2", "conv-3"],
            "confidence": 0.9,
            "applicable_intents": ["billing"],
            "suggested_application": "tool_ordering",
            "status": "draft",
        }
        knowledge_store.create(entry)

        # Review and approve
        knowledge_store.update_status("workflow-test", "reviewed")
        reviewed = knowledge_store.get("workflow-test")
        assert reviewed["status"] == "reviewed"

        # Apply
        knowledge_store.mark_applied("workflow-test", impact_score=0.07)
        applied = knowledge_store.get("workflow-test")
        assert applied["status"] == "applied"
        assert applied["impact_score"] == 0.07
        assert applied["applied_at"] is not None

    def test_list_by_confidence(self, tmp_path: Path):
        """Test that list returns entries ordered by confidence."""
        store = KnowledgeStore(db_path=str(tmp_path / "knowledge.db"))

        # Create entries with different confidence levels
        for i, conf in enumerate([0.5, 0.9, 0.7, 0.95, 0.6]):
            store.create({
                "pattern_id": f"conf-{i}",
                "pattern_type": "tool_usage",
                "description": f"Pattern {i}",
                "evidence_conversations": [],
                "confidence": conf,
                "applicable_intents": [],
                "suggested_application": "tool_ordering",
                "status": "draft",
            })

        entries = store.list()

        # Should be ordered by confidence DESC
        confidences = [e["confidence"] for e in entries]
        assert confidences == sorted(confidences, reverse=True)

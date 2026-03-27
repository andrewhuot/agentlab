"""Skill promotion workflow for draft → active transitions.

Skills auto-learned from optimizations sit as drafts. This module provides
a human review workflow to promote them to active status with proper governance.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from core.skills.store import SkillStore
from core.skills.types import Skill, SkillKind


@dataclass
class PromotionRecord:
    """Record of a skill promotion action."""
    skill_id: str
    action: str  # "promoted", "archived", "edited"
    timestamp: float
    reviewer: str
    reason: str = ""
    changes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "action": self.action,
            "timestamp": self.timestamp,
            "reviewer": self.reviewer,
            "reason": self.reason,
            "changes": self.changes,
        }


class SkillPromotionWorkflow:
    """Human review workflow for promoting draft skills to active status.

    Provides:
    - List draft skills with source and effectiveness metrics
    - Approve/edit/reject actions
    - Promotion history tracking
    - Status transitions (draft → active, draft → archived)
    """

    def __init__(self, store: SkillStore, reviewer: str = "operator") -> None:
        self.store = store
        self.reviewer = reviewer
        self._promotion_history: list[PromotionRecord] = []

    def list_draft_skills(
        self,
        kind: SkillKind | None = None,
        min_effectiveness: float | None = None,
    ) -> list[dict[str, Any]]:
        """List all draft skills with metrics.

        Returns:
            List of dict with skill details and effectiveness metrics
        """
        drafts = self.store.list(kind=kind, status="draft")

        results = []
        for skill in drafts:
            # Get source metadata
            source = skill.metadata.get("source_attempt_id", "unknown")
            source_improvement = skill.metadata.get("source_improvement", 0.0)

            # Filter by effectiveness if requested
            if min_effectiveness is not None:
                if skill.effectiveness.success_rate < min_effectiveness:
                    continue

            results.append({
                "skill": skill,
                "source": source,
                "source_improvement": source_improvement,
                "times_applied": skill.effectiveness.times_applied,
                "success_rate": skill.effectiveness.success_rate,
                "avg_improvement": skill.effectiveness.avg_improvement,
                "total_improvement": skill.effectiveness.total_improvement,
                "last_applied": skill.effectiveness.last_applied,
            })

        # Sort by effectiveness (success_rate * times_applied)
        results.sort(
            key=lambda x: x["success_rate"] * x["times_applied"],
            reverse=True,
        )

        return results

    def get_draft_details(self, skill_id: str) -> dict[str, Any] | None:
        """Get detailed information about a draft skill."""
        skill = self.store.get(skill_id)
        if not skill or skill.status != "draft":
            return None

        return {
            "skill": skill,
            "source": skill.metadata.get("source_attempt_id", "unknown"),
            "source_section": skill.metadata.get("source_config_section", "unknown"),
            "source_improvement": skill.metadata.get("source_improvement", 0.0),
            "effectiveness": {
                "times_applied": skill.effectiveness.times_applied,
                "success_count": skill.effectiveness.success_count,
                "success_rate": skill.effectiveness.success_rate,
                "avg_improvement": skill.effectiveness.avg_improvement,
                "total_improvement": skill.effectiveness.total_improvement,
                "last_applied": skill.effectiveness.last_applied,
            },
            "mutations": [m.to_dict() for m in skill.mutations],
            "triggers": [t.to_dict() for t in skill.triggers],
            "examples": [e.to_dict() for e in skill.examples],
        }

    def promote_skill(self, skill_id: str, reason: str = "") -> bool:
        """Promote a draft skill to active status.

        Args:
            skill_id: The skill ID to promote
            reason: Optional reason for promotion

        Returns:
            True if successful, False otherwise
        """
        skill = self.store.get(skill_id)
        if not skill:
            return False

        if skill.status != "draft":
            return False

        # Update status to active
        skill.status = "active"
        skill.updated_at = time.time()

        # Update in store
        success = self.store.update(skill)

        if success:
            # Record promotion
            record = PromotionRecord(
                skill_id=skill_id,
                action="promoted",
                timestamp=time.time(),
                reviewer=self.reviewer,
                reason=reason,
            )
            self._promotion_history.append(record)

        return success

    def archive_skill(self, skill_id: str, reason: str = "") -> bool:
        """Archive a draft skill (reject it).

        Args:
            skill_id: The skill ID to archive
            reason: Reason for archiving

        Returns:
            True if successful, False otherwise
        """
        skill = self.store.get(skill_id)
        if not skill:
            return False

        if skill.status != "draft":
            return False

        # Update status to archived
        skill.status = "archived"
        skill.updated_at = time.time()
        skill.metadata["archived_reason"] = reason

        # Update in store
        success = self.store.update(skill)

        if success:
            # Record archival
            record = PromotionRecord(
                skill_id=skill_id,
                action="archived",
                timestamp=time.time(),
                reviewer=self.reviewer,
                reason=reason,
            )
            self._promotion_history.append(record)

        return success

    def edit_skill(
        self,
        skill_id: str,
        updates: dict[str, Any],
        promote_after_edit: bool = False,
    ) -> bool:
        """Edit a draft skill before promoting.

        Args:
            skill_id: The skill ID to edit
            updates: Dictionary of fields to update
            promote_after_edit: If True, promote to active after editing

        Returns:
            True if successful, False otherwise
        """
        skill = self.store.get(skill_id)
        if not skill:
            return False

        if skill.status != "draft":
            return False

        # Track changes
        changes = {}

        # Apply updates
        if "name" in updates:
            changes["name"] = {"old": skill.name, "new": updates["name"]}
            skill.name = updates["name"]

        if "description" in updates:
            changes["description"] = {"old": skill.description, "new": updates["description"]}
            skill.description = updates["description"]

        if "capabilities" in updates:
            changes["capabilities"] = {"old": skill.capabilities, "new": updates["capabilities"]}
            skill.capabilities = updates["capabilities"]

        if "domain" in updates:
            changes["domain"] = {"old": skill.domain, "new": updates["domain"]}
            skill.domain = updates["domain"]

        if "tags" in updates:
            changes["tags"] = {"old": skill.tags, "new": updates["tags"]}
            skill.tags = updates["tags"]

        # Update timestamp
        skill.updated_at = time.time()

        # Optionally promote after editing
        if promote_after_edit:
            skill.status = "active"

        # Update in store
        success = self.store.update(skill)

        if success:
            # Record edit
            action = "edited_and_promoted" if promote_after_edit else "edited"
            record = PromotionRecord(
                skill_id=skill_id,
                action=action,
                timestamp=time.time(),
                reviewer=self.reviewer,
                reason="Manual edits applied",
                changes=changes,
            )
            self._promotion_history.append(record)

        return success

    def get_promotion_history(
        self, skill_id: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get promotion history records.

        Args:
            skill_id: Optional skill ID to filter by
            limit: Maximum records to return

        Returns:
            List of promotion records
        """
        records = self._promotion_history

        if skill_id:
            records = [r for r in records if r.skill_id == skill_id]

        # Sort by timestamp descending
        records = sorted(records, key=lambda r: r.timestamp, reverse=True)

        return [r.to_dict() for r in records[:limit]]

    def get_promotion_stats(self) -> dict[str, Any]:
        """Get aggregate promotion statistics.

        Returns:
            Dict with promotion stats
        """
        total_drafts = len(self.store.list(status="draft"))
        total_active = len(self.store.list(status="active"))
        total_archived = len(self.store.list(status="archived"))

        promoted_count = len([r for r in self._promotion_history if r.action in ("promoted", "edited_and_promoted")])
        archived_count = len([r for r in self._promotion_history if r.action == "archived"])
        edited_count = len([r for r in self._promotion_history if "edited" in r.action])

        return {
            "total_drafts": total_drafts,
            "total_active": total_active,
            "total_archived": total_archived,
            "lifetime_promoted": promoted_count,
            "lifetime_archived": archived_count,
            "lifetime_edited": edited_count,
        }

    def bulk_promote(
        self,
        skill_ids: list[str],
        reason: str = "",
    ) -> dict[str, bool]:
        """Promote multiple skills at once.

        Args:
            skill_ids: List of skill IDs to promote
            reason: Reason for bulk promotion

        Returns:
            Dict mapping skill_id to success status
        """
        results = {}
        for skill_id in skill_ids:
            results[skill_id] = self.promote_skill(skill_id, reason=reason)
        return results

    def bulk_archive(
        self,
        skill_ids: list[str],
        reason: str = "",
    ) -> dict[str, bool]:
        """Archive multiple skills at once.

        Args:
            skill_ids: List of skill IDs to archive
            reason: Reason for bulk archival

        Returns:
            Dict mapping skill_id to success status
        """
        results = {}
        for skill_id in skill_ids:
            results[skill_id] = self.archive_skill(skill_id, reason=reason)
        return results

"""Types for agent skill generation."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillGap:
    """An identified gap in the agent's capabilities."""

    gap_id: str
    gap_type: str              # "missing_tool", "missing_sub_agent", "tool_enhancement", "missing_playbook_step", "missing_intent", "missing_flow"
    description: str
    evidence: list[str]        # Conversation IDs that demonstrate the gap
    failure_family: str        # "tool_error", "routing_error", etc.
    frequency: int
    impact_score: float        # 0-1
    suggested_name: str
    suggested_platform: str    # "adk" or "cx"
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary."""
        return {
            "gap_id": self.gap_id,
            "gap_type": self.gap_type,
            "description": self.description,
            "evidence": self.evidence,
            "failure_family": self.failure_family,
            "frequency": self.frequency,
            "impact_score": self.impact_score,
            "suggested_name": self.suggested_name,
            "suggested_platform": self.suggested_platform,
            "context": self.context,
        }


@dataclass
class GeneratedFile:
    """A file to create or modify as part of a generated skill."""

    path: str
    content: str
    is_new: bool
    diff: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary."""
        return {
            "path": self.path,
            "content": self.content,
            "is_new": self.is_new,
            "diff": self.diff,
        }


@dataclass
class GeneratedSkill:
    """A generated or enhanced agent skill ready for review."""

    skill_id: str
    gap_id: str
    platform: str              # "adk" or "cx"
    skill_type: str            # "tool", "sub_agent", "playbook", "intent", "flow"
    name: str
    description: str
    source_code: str | None = None
    config_yaml: str | None = None
    files: list[GeneratedFile] = field(default_factory=list)
    eval_criteria: list[dict[str, Any]] = field(default_factory=list)
    estimated_improvement: float = 0.0
    confidence: str = "medium"  # "high", "medium", "low"
    status: str = "draft"       # "draft", "approved", "rejected", "deployed"
    review_notes: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary."""
        return {
            "skill_id": self.skill_id,
            "gap_id": self.gap_id,
            "platform": self.platform,
            "skill_type": self.skill_type,
            "name": self.name,
            "description": self.description,
            "source_code": self.source_code,
            "config_yaml": self.config_yaml,
            "files": [f.to_dict() for f in self.files],
            "eval_criteria": self.eval_criteria,
            "estimated_improvement": self.estimated_improvement,
            "confidence": self.confidence,
            "status": self.status,
            "review_notes": self.review_notes,
            "created_at": self.created_at,
        }

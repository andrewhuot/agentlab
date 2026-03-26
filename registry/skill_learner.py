"""Skill learning — analyze successful optimizations and create draft skills."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any

from registry.skill_store import SkillStore
from registry.skill_types import (
    EvalCriterion,
    MutationTemplate,
    Skill,
    SkillExample,
    TriggerCondition,
)


# Maps config sections to categories
_SECTION_CATEGORY_MAP: dict[str, str] = {
    "routing": "routing",
    "prompts": "quality",
    "tools": "latency",
    "thresholds": "latency",
    "safety": "safety",
    "generation_settings": "cost",
}


@dataclass
class DraftSkill:
    """A skill draft created from a successful optimization."""

    skill: Skill
    source_attempt_id: str
    confidence: float


class SkillLearner:
    """Analyzes successful optimizations and creates/updates skills."""

    def __init__(self, skill_store: SkillStore) -> None:
        self.skill_store = skill_store

    def analyze_optimization(
        self,
        config_diff: str,
        attempt: dict[str, Any],
    ) -> DraftSkill | None:
        """Analyze a successful optimization and potentially create a draft skill."""
        # Only learn from accepted attempts
        if attempt.get("status") != "accepted":
            return None

        config_section = attempt.get("config_section", "")
        change_description = attempt.get("change_description", "")
        score_before = attempt.get("score_before", 0.0)
        score_after = attempt.get("score_after", 0.0)
        improvement = score_after - score_before

        if improvement <= 0:
            return None

        # Check if this matches an existing skill
        existing = self.match_existing_skill(config_section, change_description)
        if existing:
            self.update_skill_stats(existing.name, improvement, True)
            return None

        # Create a draft skill
        category = _SECTION_CATEGORY_MAP.get(config_section, "quality")
        skill_name = self._generate_skill_name(config_section, change_description)

        skill = Skill(
            name=skill_name,
            version=1,
            description=f"Learned: {change_description}",
            category=category,
            platform="universal",
            target_surfaces=[config_section] if config_section else [],
            mutations=[
                MutationTemplate(
                    name=f"{skill_name}_mutation",
                    mutation_type=f"{config_section}_edit",
                    target_surface=config_section,
                    description=change_description,
                )
            ],
            examples=[
                SkillExample(
                    name=f"{skill_name}_example",
                    surface=config_section,
                    before="(original config)",
                    after="(optimized config)",
                    improvement=improvement,
                    context=f"Learned from optimization attempt {attempt.get('attempt_id', 'unknown')}",
                )
            ],
            guardrails=["Verify improvement before applying", "Monitor for regressions"],
            eval_criteria=[
                EvalCriterion(
                    metric="composite_score",
                    target=score_after,
                    operator="gt",
                )
            ],
            triggers=[
                TriggerCondition(
                    failure_family=self._infer_failure_family(config_section),
                )
            ],
            author="skill-learner",
            tags=["learned", category],
            created_at=time.time(),
            proven_improvement=improvement,
            times_applied=1,
            success_rate=1.0,
            status="draft",
        )

        return DraftSkill(
            skill=skill,
            source_attempt_id=attempt.get("attempt_id", "unknown"),
            confidence=min(1.0, improvement * 10),  # Scale improvement to confidence
        )

    def match_existing_skill(
        self,
        config_section: str,
        change_description: str,
    ) -> Skill | None:
        """Check if a change matches an existing skill's patterns."""
        # Search by config section and description keywords
        if config_section:
            candidates = self.skill_store.search(config_section)
            for skill in candidates:
                # Check if any mutation targets this section
                for mutation in skill.mutations:
                    if config_section in mutation.target_surface:
                        return skill

        # Search by keywords in the change description
        keywords = re.findall(r'\b\w{4,}\b', change_description.lower())
        for keyword in keywords[:3]:  # Check first 3 significant keywords
            candidates = self.skill_store.search(keyword)
            for candidate in candidates:
                # Verify the candidate targets the same section
                if config_section:
                    # Check if candidate's target_surfaces include this section
                    if config_section in candidate.target_surfaces:
                        return candidate
                    # Also check mutations' target_surface
                    for mutation in candidate.mutations:
                        if config_section in mutation.target_surface:
                            return candidate
                else:
                    # No section filter - return first match
                    return candidate

        return None

    def update_skill_stats(
        self,
        skill_name: str,
        improvement: float,
        success: bool,
    ) -> None:
        """Update an existing skill's effectiveness stats."""
        self.skill_store.record_outcome(skill_name, improvement, success)

    def learn_from_history(
        self,
        recent_attempts: list[dict[str, Any]],
    ) -> list[DraftSkill]:
        """Analyze recent optimization attempts and create draft skills."""
        drafts: list[DraftSkill] = []
        for attempt in recent_attempts:
            draft = self.analyze_optimization(
                config_diff=attempt.get("config_diff", ""),
                attempt=attempt,
            )
            if draft is not None:
                drafts.append(draft)
        return drafts

    @staticmethod
    def _generate_skill_name(config_section: str, description: str) -> str:
        """Generate a skill name from the config section and description."""
        # Extract key words and create a snake_case name
        words = re.findall(r'\b\w+\b', description.lower())
        # Filter to meaningful words
        stopwords = {"the", "a", "an", "to", "for", "in", "on", "is", "was", "and", "or", "of"}
        meaningful = [w for w in words if w not in stopwords and len(w) > 2][:4]
        if not meaningful:
            meaningful = [config_section or "learned"]
        name = "_".join(meaningful)
        return f"learned_{name}"

    @staticmethod
    def _infer_failure_family(config_section: str) -> str | None:
        """Infer a failure family from the config section."""
        mapping = {
            "routing": "routing_error",
            "prompts": "unhelpful_response",
            "tools": "tool_failure",
            "thresholds": "timeout",
            "safety": "safety_violation",
        }
        return mapping.get(config_section)

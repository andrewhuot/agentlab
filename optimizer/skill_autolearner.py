"""Automatic draft-skill synthesis from accepted optimizer attempts."""

from __future__ import annotations

import re
import uuid

from core.skills.store import SkillStore
from core.skills.types import (
    EvalCriterion,
    MutationOperator,
    Skill,
    SkillExample,
    SkillKind,
    TriggerCondition,
)

_SECTION_OPERATOR_MAP: dict[str, str] = {
    "routing": "routing_edit",
    "prompts": "instruction_rewrite",
    "tools": "tool_description_edit",
    "generation_settings": "generation_settings",
    "thresholds": "generation_settings",
    "safety": "policy_edit",
    "skill_optimization": "skill_rewrite",
}

_SECTION_DOMAIN_MAP: dict[str, str] = {
    "routing": "routing",
    "prompts": "quality",
    "tools": "tools",
    "generation_settings": "latency",
    "thresholds": "latency",
    "safety": "safety",
    "skill_optimization": "quality",
}

_STOPWORDS = {
    "the",
    "a",
    "an",
    "to",
    "for",
    "in",
    "on",
    "of",
    "and",
    "or",
    "with",
    "from",
    "this",
    "that",
}


class SkillAutoLearner:
    """Create draft BUILD skills from accepted optimization attempts.

    WHY: The optimizer should not only improve one config at a time, but also
    accumulate reusable optimization knowledge. Draft skills let operators
    review and promote learned strategies intentionally.
    """

    def __init__(self, store: SkillStore, min_improvement: float = 0.01) -> None:
        self.store = store
        self.min_improvement = min_improvement

    def learn_from_accepted_attempt(
        self,
        *,
        attempt_id: str,
        change_description: str,
        config_section: str,
        config_diff: str,
        improvement: float,
        failure_family: str | None = None,
    ) -> str | None:
        """Create one draft skill from an accepted attempt, if eligible."""
        if improvement < self.min_improvement:
            return None
        if not config_section:
            return None
        if config_section == "skill_optimization":
            # Skip recursive "learning from skills that were already skills".
            return None

        name = self._build_name(config_section, change_description)
        if self._draft_exists(name):
            return None

        operator_name = _SECTION_OPERATOR_MAP.get(config_section, "instruction_rewrite")
        mutation = MutationOperator(
            name=operator_name,
            description=f"Auto-learned mutation from accepted attempt {attempt_id}",
            target_surface=config_section,
            operator_type="merge",
            parameters=self._default_parameters(operator_name),
            risk_level="low",
        )

        skill = Skill(
            id=f"autolearn-{uuid.uuid4().hex[:12]}",
            name=name,
            kind=SkillKind.BUILD,
            version="1.0.0",
            description=f"Draft learned from accepted optimization: {change_description}",
            capabilities=[config_section],
            mutations=[mutation],
            triggers=[
                TriggerCondition(
                    failure_family=failure_family,
                )
            ],
            eval_criteria=[
                EvalCriterion(
                    metric="composite",
                    target=0.0,
                    operator="gt",
                )
            ],
            guardrails=[
                "Require statistical significance before promotion.",
                "Reject if safety or regression gates fail.",
                "Prefer small, reviewable diffs.",
            ],
            examples=[
                SkillExample(
                    name=f"{name}_example",
                    description="Auto-learned from optimizer memory",
                    before="(baseline config)",
                    after=config_diff,
                    improvement=improvement,
                    context=f"source_attempt={attempt_id}",
                )
            ],
            tags=["autolearned", "draft", config_section],
            domain=_SECTION_DOMAIN_MAP.get(config_section, "general"),
            author="optimizer-autolearner",
            status="draft",
            metadata={
                "source_attempt_id": attempt_id,
                "source_config_section": config_section,
                "source_improvement": round(improvement, 6),
            },
        )

        return self.store.create(skill)

    def _draft_exists(self, name: str) -> bool:
        candidates = self.store.search(name, kind=SkillKind.BUILD)
        return any(skill.name == name for skill in candidates)

    @staticmethod
    def _default_parameters(operator_name: str) -> dict:
        """Provide safe placeholder parameters for draft mutation operators."""
        if operator_name == "instruction_rewrite":
            return {"target": "root", "text": "(draft) refine root prompt"}
        if operator_name == "routing_edit":
            return {"rule_id": "draft", "updates": {}}
        if operator_name == "tool_description_edit":
            return {"tool_name": "draft_tool", "updates": {"description": "(draft)"}}
        if operator_name == "generation_settings":
            return {"temperature": 0.7}
        if operator_name == "policy_edit":
            return {"name": "draft_policy", "updates": {}}
        if operator_name == "skill_rewrite":
            return {"name": "draft_skill", "instructions": "(draft)"}
        return {}

    @staticmethod
    def _build_name(config_section: str, change_description: str) -> str:
        words = re.findall(r"\b[a-zA-Z]{3,}\b", change_description.lower())
        key_words = [word for word in words if word not in _STOPWORDS][:4]
        suffix = "_".join(key_words) if key_words else (config_section or "mutation")
        return f"autolearn_{config_section}_{suffix}"[:80]

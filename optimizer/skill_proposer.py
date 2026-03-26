"""Skill-aware proposer that wraps the existing Proposer with skill context."""

from __future__ import annotations


from optimizer.proposer import Proposal, Proposer
from registry.skill_store import SkillStore
from registry.skill_types import Skill


class SkillAwareProposer:
    """Wraps the existing Proposer with skill context from the registry.

    Before generating a proposal, queries the skill store for relevant skills
    based on failure patterns and metrics. Includes skill mutations, examples,
    and guardrails in the proposer context.
    """

    def __init__(self, proposer: Proposer, skill_store: SkillStore) -> None:
        self.proposer = proposer
        self.skill_store = skill_store
        self._last_applied_skills: list[str] = []

    def propose(
        self,
        current_config: dict,
        health_metrics: dict,
        failure_samples: list[dict],
        failure_buckets: dict[str, int],
        past_attempts: list[dict],
        *,
        optimization_mode: str | None = None,
        objective: str | None = None,
        guardrails: list[str] | None = None,
        project_memory_context: dict[str, list[str]] | None = None,
    ) -> Proposal | None:
        """Generate a proposal enriched with skill context."""
        # 1. Find relevant skills
        relevant_skills = self._get_relevant_skills(failure_buckets, health_metrics)
        self._last_applied_skills = [s.name for s in relevant_skills]

        # 2. Build skill context
        skill_context = self._build_skill_context(relevant_skills)

        # 3. Merge skill guardrails with provided guardrails
        merged_guardrails = list(guardrails or [])
        for skill in relevant_skills:
            merged_guardrails.extend(skill.guardrails)

        # 4. Build enriched memory context
        enriched_memory = dict(project_memory_context or {})
        if skill_context:
            enriched_memory["skill_guidance"] = skill_context.get("guidance", [])
            enriched_memory["skill_examples"] = skill_context.get("examples", [])

        # 5. Delegate to base proposer
        return self.proposer.propose(
            current_config=current_config,
            health_metrics=health_metrics,
            failure_samples=failure_samples,
            failure_buckets=failure_buckets,
            past_attempts=past_attempts,
            optimization_mode=optimization_mode,
            objective=objective,
            guardrails=merged_guardrails if merged_guardrails else None,
            project_memory_context=enriched_memory if enriched_memory else None,
        )

    def _get_relevant_skills(
        self,
        failure_buckets: dict[str, int],
        health_metrics: dict,
    ) -> list[Skill]:
        """Find skills relevant to current failures and metrics."""
        skills: list[Skill] = []
        seen: set[str] = set()

        # Match by failure family
        dominant = _dominant_failure_bucket(failure_buckets)
        if dominant:
            for skill in self.skill_store.recommend(failure_family=dominant):
                if skill.name not in seen:
                    skills.append(skill)
                    seen.add(skill.name)

        # Match by metric thresholds
        if health_metrics:
            for skill in self.skill_store.recommend(metrics=health_metrics):
                if skill.name not in seen:
                    skills.append(skill)
                    seen.add(skill.name)

        # Prefer skills with proven track records
        skills.sort(key=lambda s: (s.success_rate * (s.proven_improvement or 0)), reverse=True)
        return skills[:5]  # Limit to top 5 most relevant

    def _build_skill_context(self, skills: list[Skill]) -> dict[str, list[str]]:
        """Build structured context from skills for the proposer."""
        if not skills:
            return {}

        guidance: list[str] = []
        examples: list[str] = []

        for skill in skills:
            # Add mutation guidance
            for mutation in skill.mutations:
                guidance.append(
                    f"[{skill.name}] {mutation.description} "
                    f"(target: {mutation.target_surface})"
                )
                if mutation.template:
                    guidance.append(f"  Template: {mutation.template}")

            # Add examples as before/after
            for example in skill.examples:
                examples.append(
                    f"[{skill.name}/{example.name}] "
                    f"Before: {example.before} → After: {example.after} "
                    f"(+{example.improvement:.0%} improvement)"
                )

        return {"guidance": guidance, "examples": examples}

    def record_outcome(self, skill_name: str, improvement: float, success: bool) -> None:
        """Record the outcome of a skill application."""
        self.skill_store.record_outcome(skill_name, improvement, success)

    @property
    def last_applied_skills(self) -> list[str]:
        """Return names of skills used in the most recent proposal."""
        return self._last_applied_skills


def _dominant_failure_bucket(failure_buckets: dict[str, int]) -> str | None:
    """Return the dominant non-zero failure bucket."""
    non_zero = {b: c for b, c in failure_buckets.items() if c > 0}
    if not non_zero:
        return None
    return max(non_zero, key=non_zero.get)  # type: ignore[arg-type]

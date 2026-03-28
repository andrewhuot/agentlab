"""Specialist definitions for the Builder multi-agent workflow."""

from __future__ import annotations

from dataclasses import dataclass

from builder.types import SpecialistRole


@dataclass(frozen=True)
class SpecialistDefinition:
    """Specification for one builder specialist subagent."""

    role: SpecialistRole
    display_name: str
    description: str
    tools: list[str]
    permission_scope: list[str]
    context_template: str


SPECIALISTS: dict[SpecialistRole, SpecialistDefinition] = {
    SpecialistRole.ORCHESTRATOR: SpecialistDefinition(
        role=SpecialistRole.ORCHESTRATOR,
        display_name="Orchestrator",
        description=(
            "Coordinates specialist handoffs, validates plans, and keeps artifacts aligned "
            "to user intent."
        ),
        tools=["route", "handoff", "task_planner", "session_memory"],
        permission_scope=["read"],
        context_template=(
            "Session: {session_id}\n"
            "Task: {task_id}\n"
            "Goal: coordinate specialists and keep changes reviewable."
        ),
    ),
    SpecialistRole.REQUIREMENTS_ANALYST: SpecialistDefinition(
        role=SpecialistRole.REQUIREMENTS_ANALYST,
        display_name="Requirements Analyst",
        description="Converts ambiguous requests into concrete goals, assumptions, and risks.",
        tools=["requirements_parser", "memory_reader", "constraints_extractor"],
        permission_scope=["read"],
        context_template=(
            "Read project instructions, summarize requirements, and produce acceptance criteria."
        ),
    ),
    SpecialistRole.ADK_ARCHITECT: SpecialistDefinition(
        role=SpecialistRole.ADK_ARCHITECT,
        display_name="ADK Architect",
        description="Designs agent graph topology and ADK wiring changes.",
        tools=["adk_graph_reader", "adk_graph_diff", "topology_validator"],
        permission_scope=["read"],
        context_template=(
            "Propose ADK graph changes with before/after structure and rationale."
        ),
    ),
    SpecialistRole.TOOL_ENGINEER: SpecialistDefinition(
        role=SpecialistRole.TOOL_ENGINEER,
        display_name="Tool/Integration Engineer",
        description="Implements tools, adapters, and integration contracts.",
        tools=["code_search", "code_edit", "integration_tester"],
        permission_scope=["read", "source_write", "external_network"],
        context_template="Implement and validate tool integrations with safe defaults.",
    ),
    SpecialistRole.SKILL_AUTHOR: SpecialistDefinition(
        role=SpecialistRole.SKILL_AUTHOR,
        display_name="Skill Author",
        description="Creates and updates buildtime/runtime skills and manifests.",
        tools=["skill_registry", "manifest_editor", "skill_linter"],
        permission_scope=["read", "source_write"],
        context_template="Author skill content, manifest metadata, and provenance notes.",
    ),
    SpecialistRole.GUARDRAIL_AUTHOR: SpecialistDefinition(
        role=SpecialistRole.GUARDRAIL_AUTHOR,
        display_name="Guardrail Author",
        description="Designs and attaches policy guardrails with scoped inheritance.",
        tools=["guardrail_editor", "policy_tester", "safety_analyzer"],
        permission_scope=["read", "source_write"],
        context_template="Attach or revise guardrails and capture failure examples.",
    ),
    SpecialistRole.EVAL_AUTHOR: SpecialistDefinition(
        role=SpecialistRole.EVAL_AUTHOR,
        display_name="Eval Author",
        description="Creates eval slices and validates outcomes before apply/release.",
        tools=["eval_generator", "eval_runner", "quality_scorer"],
        permission_scope=["read", "source_write"],
        context_template="Generate eval bundles and summarize before/after quality deltas.",
    ),
    SpecialistRole.TRACE_ANALYST: SpecialistDefinition(
        role=SpecialistRole.TRACE_ANALYST,
        display_name="Trace Analyst",
        description="Investigates traces, bookmarks evidence, and proposes fixes.",
        tools=["trace_search", "span_timeline", "blame_mapper"],
        permission_scope=["read"],
        context_template="Analyze traces, isolate root causes, and attach evidence chains.",
    ),
    SpecialistRole.RELEASE_MANAGER: SpecialistDefinition(
        role=SpecialistRole.RELEASE_MANAGER,
        display_name="Release Manager",
        description="Packages release candidates and manages deploy/rollback flow.",
        tools=["release_packager", "deploy_executor", "rollback_planner"],
        permission_scope=["read", "deployment"],
        context_template="Verify release readiness from artifacts, eval bundles, and approvals.",
    ),
}


_INTENT_KEYWORDS: dict[SpecialistRole, tuple[str, ...]] = {
    SpecialistRole.REQUIREMENTS_ANALYST: (
        "requirements",
        "spec",
        "scope",
        "clarify",
        "assumption",
    ),
    SpecialistRole.ADK_ARCHITECT: ("adk", "graph", "topology", "architecture"),
    SpecialistRole.TOOL_ENGINEER: ("tool", "integration", "api", "connector", "endpoint"),
    SpecialistRole.SKILL_AUTHOR: ("skill", "runtime skill", "buildtime skill", "manifest"),
    SpecialistRole.GUARDRAIL_AUTHOR: ("guardrail", "policy", "safety", "pii"),
    SpecialistRole.EVAL_AUTHOR: ("eval", "benchmark", "quality", "regression", "test"),
    SpecialistRole.TRACE_ANALYST: ("trace", "span", "failure", "why", "blame"),
    SpecialistRole.RELEASE_MANAGER: ("release", "deploy", "rollback", "promote"),
}


def get_specialist(role: SpecialistRole) -> SpecialistDefinition:
    """Return specialist definition by role."""

    return SPECIALISTS[role]


def list_specialists() -> list[SpecialistDefinition]:
    """Return all specialist definitions in deterministic role order."""

    return [SPECIALISTS[role] for role in SpecialistRole]


def detect_specialist_by_intent(message: str) -> SpecialistRole:
    """Select the specialist that best matches the provided message."""

    text = message.lower()
    best_role = SpecialistRole.ORCHESTRATOR
    best_score = 0
    for role, keywords in _INTENT_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > best_score:
            best_role = role
            best_score = score
    return best_role

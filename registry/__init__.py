"""Modular Registry for AutoAgent.

Re-exports the public API for convenient imports.
"""

from registry.store import RegistryStore
from registry.skills import SkillRegistry
from registry.policies import PolicyRegistry
from registry.tool_contracts import ToolContractRegistry
from registry.handoff_schemas import HandoffSchemaRegistry
from registry.runbooks import Runbook, RunbookStore, seed_starter_runbooks
from registry.skill_types import (
    EvalCriterion,
    MutationTemplate,
    Skill,
    SkillExample,
    TriggerCondition,
)
from registry.skill_store import SkillStore
from registry.skill_loader import install_builtin_packs, install_pack, load_pack
from registry.skill_learner import SkillLearner

__all__ = [
    "RegistryStore",
    "SkillRegistry",
    "PolicyRegistry",
    "ToolContractRegistry",
    "HandoffSchemaRegistry",
    "Runbook",
    "RunbookStore",
    "seed_starter_runbooks",
    "EvalCriterion",
    "MutationTemplate",
    "Skill",
    "SkillExample",
    "TriggerCondition",
    "SkillStore",
    "SkillLearner",
    "install_builtin_packs",
    "install_pack",
    "load_pack",
]

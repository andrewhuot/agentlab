"""Load skills from YAML packs and register them in the skill store."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from registry.skill_types import Skill


_PACKS_DIR = Path(__file__).parent / "packs"


def load_pack(path: str | Path) -> list[Skill]:
    """Load a YAML pack file and return a list of Skills."""
    path = Path(path)
    with open(path, "r") as f:
        data = yaml.safe_load(f)

    skills_data = data.get("skills", [])
    return [Skill.from_dict(s) for s in skills_data]


def install_pack(path: str | Path, store) -> int:
    """Load and register all skills from a pack. Returns count installed."""
    skills = load_pack(path)
    count = 0
    for skill in skills:
        existing = store.get(skill.name)
        if existing is None:
            store.register(skill)
            count += 1
    return count


def install_builtin_packs(store) -> int:
    """Install universal + cx_agent_studio packs. Returns total count."""
    total = 0
    for pack_file in ["universal.yaml", "cx_agent_studio.yaml"]:
        pack_path = _PACKS_DIR / pack_file
        if pack_path.exists():
            total += install_pack(pack_path, store)
    return total


def export_skill(skill: Skill, path: str | Path) -> None:
    """Export a skill to a YAML file."""
    path = Path(path)
    data = {"skills": [skill.to_dict()]}
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

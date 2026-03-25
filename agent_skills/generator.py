"""Generates new agent skills from identified gaps using Jinja2 templates."""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from agent_skills.types import GeneratedFile, GeneratedSkill, SkillGap

_TEMPLATE_DIR = Path(__file__).parent / "templates"

# Map (gap_type, platform) → template filename
_TEMPLATE_MAP: dict[tuple[str, str], str] = {
    ("missing_tool", "adk"): "adk_tool.py.j2",
    ("tool_enhancement", "adk"): "adk_tool.py.j2",
    ("missing_sub_agent", "adk"): "adk_sub_agent.py.j2",
    ("missing_playbook_step", "cx"): "cx_playbook.yaml.j2",
    ("missing_intent", "cx"): "cx_intent.yaml.j2",
    ("missing_flow", "cx"): "cx_tool.yaml.j2",
    ("missing_tool", "cx"): "cx_tool.yaml.j2",
}


class AgentSkillGenerator:
    """Generates new agent skills from identified gaps."""

    def __init__(self, template_dir: str | Path | None = None) -> None:
        tdir = Path(template_dir) if template_dir else _TEMPLATE_DIR
        self._env = Environment(
            loader=FileSystemLoader(str(tdir)),
            autoescape=select_autoescape([]),
            keep_trailing_newline=True,
        )

    def generate(self, gap: SkillGap, platform: str | None = None, context: dict[str, Any] | None = None) -> GeneratedSkill:
        """Generate a skill to fill the identified gap."""
        platform = platform or gap.suggested_platform
        context = context or {}

        # 1. Select template
        template_key = (gap.gap_type, platform)
        template_name = _TEMPLATE_MAP.get(template_key)
        if template_name is None:
            # Fallback: use adk_tool for adk, cx_tool for cx
            template_name = "adk_tool.py.j2" if platform == "adk" else "cx_tool.yaml.j2"

        # 2. Build template variables from gap context
        template_vars = self._build_template_vars(gap, platform, context)

        # 3. Render template
        template = self._env.get_template(template_name)
        rendered = template.render(**template_vars)

        # 4. Determine file extension and path
        is_python = template_name.endswith(".py.j2")
        ext = ".py" if is_python else ".yaml"
        file_path = f"agent_skills/generated/{gap.suggested_name}{ext}"

        # 5. Build generated file
        gen_file = GeneratedFile(
            path=file_path,
            content=rendered,
            is_new=True,
        )

        # 6. Build eval criteria
        eval_criteria = self._build_eval_criteria(gap)

        # 7. Package as GeneratedSkill
        skill_id = uuid.uuid4().hex[:12]
        return GeneratedSkill(
            skill_id=skill_id,
            gap_id=gap.gap_id,
            platform=platform,
            skill_type=self._gap_type_to_skill_type(gap.gap_type),
            name=gap.suggested_name,
            description=gap.description,
            source_code=rendered if is_python else None,
            config_yaml=rendered if not is_python else None,
            files=[gen_file],
            eval_criteria=eval_criteria,
            estimated_improvement=gap.impact_score * 0.5,  # Conservative estimate
            confidence=self._estimate_confidence(gap),
        )

    def enhance(self, existing_skill: dict[str, Any], gap: SkillGap) -> GeneratedSkill:
        """Enhance an existing skill to handle new cases."""
        # Generate a new skill that extends the existing one
        enhanced = self.generate(gap)
        enhanced.skill_type = "tool_enhancement"
        enhanced.description = f"Enhancement of existing skill: {gap.description}"
        if existing_skill.get("source_code"):
            enhanced.review_notes = f"Enhances existing: {existing_skill.get('name', 'unknown')}"
        return enhanced

    def _build_template_vars(self, gap: SkillGap, platform: str, context: dict[str, Any]) -> dict[str, Any]:
        """Extract template variables from gap context."""
        name = gap.suggested_name
        desc = gap.description
        ctx = {**gap.context, **context}

        if platform == "adk":
            if gap.gap_type in ("missing_tool", "tool_enhancement"):
                return {
                    "tool_name": name,
                    "parameters": ctx.get("parameters", "query: str"),
                    "return_type": ctx.get("return_type", "dict"),
                    "docstring": desc,
                    "params": ctx.get("params", [{"name": "query", "description": "The user query"}]),
                    "return_description": ctx.get("return_description", "Result dictionary"),
                    "evidence_count": gap.frequency,
                    "capability_description": desc,
                    "suggested_implementation": ctx.get("suggested_implementation", f"    # Implement {name} logic here\n    pass"),
                }
            else:  # sub_agent
                return {
                    "agent_name": name,
                    "model": ctx.get("model", "gemini-2.0-flash"),
                    "instruction": ctx.get("instruction", desc),
                    "tools": ctx.get("tools", []),
                    "temperature": ctx.get("temperature", 0.2),
                    "max_tokens": ctx.get("max_tokens", 1024),
                }
        else:  # cx
            if gap.gap_type == "missing_playbook_step":
                return {
                    "playbook_name": name,
                    "goal": desc,
                    "steps": ctx.get("steps", [{"text": f"Handle {name} request", "tool": None}]),
                    "examples": ctx.get("examples", [{"user_input": "Example input", "agent_output": "Example response"}]),
                }
            elif gap.gap_type == "missing_intent":
                return {
                    "intent_name": name,
                    "description": desc,
                    "training_phrases": ctx.get("training_phrases", [desc]),
                    "parameters": ctx.get("parameters", []),
                }
            else:  # cx_tool / missing_flow
                return {
                    "tool_name": name,
                    "description": desc,
                    "endpoint": ctx.get("endpoint", name.replace("_", "-")),
                    "method": ctx.get("method", "get"),
                    "summary": desc,
                    "parameters": ctx.get("parameters", []),
                    "response_description": ctx.get("response_description", "Success"),
                }

    @staticmethod
    def _gap_type_to_skill_type(gap_type: str) -> str:
        """Map gap type to skill type."""
        mapping = {
            "missing_tool": "tool",
            "tool_enhancement": "tool",
            "missing_sub_agent": "sub_agent",
            "missing_playbook_step": "playbook",
            "missing_intent": "intent",
            "missing_flow": "flow",
        }
        return mapping.get(gap_type, "tool")

    @staticmethod
    def _estimate_confidence(gap: SkillGap) -> str:
        """Estimate confidence based on evidence and frequency."""
        if gap.frequency >= 10 and len(gap.evidence) >= 5:
            return "high"
        if gap.frequency >= 3:
            return "medium"
        return "low"

    @staticmethod
    def _build_eval_criteria(gap: SkillGap) -> list[dict[str, Any]]:
        """Build eval criteria from gap context."""
        return [
            {
                "metric": "skill_handles_gap",
                "description": f"Skill correctly handles: {gap.description}",
                "target": 0.8,
                "weight": 1.0,
            },
            {
                "metric": "no_regression",
                "description": "No regression on existing test cases",
                "target": 1.0,
                "weight": 0.5,
            },
        ]

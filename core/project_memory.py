"""Project memory — load/save/update AUTOAGENT.md persistent project context."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AUTOAGENT_MD_FILENAME = "AUTOAGENT.md"

INTEL_BEGIN = "<!-- BEGIN AUTOAGENT INTELLIGENCE — auto-updated, do not edit -->"
INTEL_END = "<!-- END AUTOAGENT INTELLIGENCE -->"

AUTOAGENT_MD_TEMPLATE = '''# AUTOAGENT.md — Project Memory

## Agent Identity
- Name: {agent_name}
- Platform: {platform}
- Primary use case: {use_case}

## Business Constraints
- Response latency must stay under 3 seconds (SLA)
- Safety violations are zero-tolerance
- Cost per conversation budget: $0.05

## Known Good Patterns
- (Add patterns that work well for your agent here)

## Known Bad Patterns
- (Add patterns to avoid here)

## Team Preferences
- Prefer instruction edits over model swaps
- Always run canary before promotion

## Optimization History
'''


@dataclass
class ProjectMemory:
    """Structured representation of AUTOAGENT.md project memory."""

    agent_name: str = ""
    platform: str = ""
    use_case: str = ""
    business_constraints: list[str] = field(default_factory=list)
    known_good_patterns: list[str] = field(default_factory=list)
    known_bad_patterns: list[str] = field(default_factory=list)
    team_preferences: list[str] = field(default_factory=list)
    optimization_history: list[str] = field(default_factory=list)
    raw_content: str = ""
    file_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "platform": self.platform,
            "use_case": self.use_case,
            "business_constraints": self.business_constraints,
            "known_good_patterns": self.known_good_patterns,
            "known_bad_patterns": self.known_bad_patterns,
            "team_preferences": self.team_preferences,
            "optimization_history": self.optimization_history,
        }

    def get_optimizer_context(self) -> dict[str, Any]:
        """Return context relevant for the optimizer loop."""
        return {
            "agent_identity": f"{self.agent_name} ({self.platform}) — {self.use_case}",
            "constraints": self.business_constraints,
            "avoid_patterns": self.known_bad_patterns,
            "preferences": self.team_preferences,
            "good_patterns": self.known_good_patterns,
        }

    def get_immutable_surfaces(self) -> set[str]:
        """Extract immutable surfaces from team preferences and constraints."""
        immutable: set[str] = set()
        for pref in self.team_preferences + self.known_bad_patterns:
            lower = pref.lower()
            if "immutable" in lower or "don't optimize" in lower or "don't change" in lower:
                # Try to extract the surface name
                for keyword in ["greeting", "safety", "routing", "model"]:
                    if keyword in lower:
                        immutable.add(keyword)
        return immutable

    def _build_intelligence_section(
        self,
        report: dict | None,
        eval_score: float | None,
        recent_changes: list[dict] | None,
        skill_gaps: list[dict] | None,
    ) -> str:
        """Build the markdown content for the intelligence section."""
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

        # Extract metrics from report
        safety = "n/a"
        routing = "n/a"
        latency = "n/a"
        issues: list[str] = []
        if report:
            svr = report.get("safety_violation_rate")
            safety = f"{svr:.2f}" if svr is not None else "n/a"
            sr = report.get("success_rate")
            routing = f"{sr * 100:.0f}" if sr is not None else "n/a"
            lat = report.get("avg_latency_ms")
            latency = f"{lat / 1000:.1f}" if lat is not None else "n/a"
            # Collect issues from report
            for key, val in report.items():
                if key.endswith("_issues") and isinstance(val, list):
                    issues.extend(val)
                elif key == "issues" and isinstance(val, list):
                    issues.extend(val)

        score_str = f"{eval_score:.2f}" if eval_score is not None else "n/a"

        lines: list[str] = [INTEL_BEGIN]
        lines.append("## Current Health")
        lines.append(
            f"Score: {score_str} | Safety: {safety} | Routing: {routing}% | Latency: {latency}s"
        )
        lines.append(f"Last updated: {ts} UTC")
        lines.append("")

        lines.append("## Active Issues")
        if issues:
            for i, issue in enumerate(issues, 1):
                lines.append(f"{i}. {issue}")
        else:
            lines.append("No active issues")
        lines.append("")

        lines.append("## Recent Changes")
        if recent_changes:
            for change in recent_changes:
                version = change.get("version", "?")
                delta = change.get("delta", 0.0)
                description = change.get("description", "")
                sign = "+" if delta >= 0 else ""
                lines.append(f"- v{version} ({sign}{delta:.2f}): {description}")
        else:
            lines.append("No recent changes")
        lines.append("")

        lines.append("## Skill Gaps")
        if skill_gaps:
            for gap in skill_gaps:
                description = gap.get("description", "")
                count = gap.get("count", 0)
                handled = gap.get("handled", 0)
                lines.append(f"- {description} ({count} user requests, {handled} handled)")
        else:
            lines.append("No skill gaps identified")
        lines.append(INTEL_END)

        return "\n".join(lines)

    def update_with_intelligence(
        self,
        report: dict | None = None,
        eval_score: float | None = None,
        recent_changes: list[dict] | None = None,
        skill_gaps: list[dict] | None = None,
    ) -> None:
        """Update AUTOAGENT.md with current agent intelligence.

        Manages content between sentinel markers. Preserves all user-written
        content outside the markers.
        """
        # Ensure file_path is set
        if not self.file_path:
            self.save()

        # Reload from disk in case of external modifications
        path = Path(self.file_path)
        if path.exists():
            current_content = path.read_text(encoding="utf-8")
        else:
            current_content = self.raw_content

        intel_section = self._build_intelligence_section(
            report, eval_score, recent_changes, skill_gaps
        )

        if INTEL_BEGIN in current_content and INTEL_END in current_content:
            # Replace existing section (inclusive of markers)
            before = current_content[: current_content.index(INTEL_BEGIN)]
            after = current_content[current_content.index(INTEL_END) + len(INTEL_END):]
            new_content = before + intel_section + after
        else:
            # Append at the end, ensuring a newline separator
            separator = "" if current_content.endswith("\n") else "\n"
            new_content = current_content + separator + intel_section + "\n"

        path.write_text(new_content, encoding="utf-8")
        self.raw_content = new_content

    @classmethod
    def load(cls, directory: str = ".") -> ProjectMemory | None:
        """Load AUTOAGENT.md from the given directory. Returns None if not found."""
        path = Path(directory) / AUTOAGENT_MD_FILENAME
        if not path.exists():
            return None
        content = path.read_text(encoding="utf-8")
        memory = cls._parse(content)
        memory.file_path = str(path)
        memory.raw_content = content
        return memory

    def save(self, directory: str = ".") -> str:
        """Save AUTOAGENT.md to the given directory. Returns the file path."""
        path = Path(directory) / AUTOAGENT_MD_FILENAME
        content = self._render()
        path.write_text(content, encoding="utf-8")
        self.file_path = str(path)
        self.raw_content = content
        return str(path)

    def add_history_entry(self, entry: str) -> None:
        """Add an optimization history entry with timestamp."""
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.optimization_history.append(f"- {ts}: {entry}")

    def add_note(self, section: str, note: str) -> None:
        """Add a note to a specific section."""
        section_lower = section.lower()
        if "good" in section_lower:
            self.known_good_patterns.append(f"- {note}")
        elif "bad" in section_lower:
            self.known_bad_patterns.append(f"- {note}")
        elif "preference" in section_lower or "team" in section_lower:
            self.team_preferences.append(f"- {note}")
        elif "constraint" in section_lower or "business" in section_lower:
            self.business_constraints.append(f"- {note}")

    @classmethod
    def generate_template(
        cls,
        agent_name: str = "My Agent",
        platform: str = "Google ADK",
        use_case: str = "General purpose assistant",
    ) -> str:
        """Generate a fresh AUTOAGENT.md template."""
        return AUTOAGENT_MD_TEMPLATE.format(
            agent_name=agent_name,
            platform=platform,
            use_case=use_case,
        )

    @classmethod
    def _parse(cls, content: str) -> ProjectMemory:
        """Parse AUTOAGENT.md content into structured ProjectMemory."""
        memory = cls()

        sections = _split_sections(content)

        # Parse Agent Identity
        identity = sections.get("agent identity", "")
        for line in identity.strip().splitlines():
            line = line.strip().lstrip("- ")
            if line.lower().startswith("name:"):
                memory.agent_name = line.split(":", 1)[1].strip()
            elif line.lower().startswith("platform:"):
                memory.platform = line.split(":", 1)[1].strip()
            elif line.lower().startswith("primary use case:"):
                memory.use_case = line.split(":", 1)[1].strip()

        # Parse list sections
        memory.business_constraints = _parse_list_section(sections.get("business constraints", ""))
        memory.known_good_patterns = _parse_list_section(sections.get("known good patterns", ""))
        memory.known_bad_patterns = _parse_list_section(sections.get("known bad patterns", ""))
        memory.team_preferences = _parse_list_section(sections.get("team preferences", ""))
        memory.optimization_history = _parse_list_section(sections.get("optimization history", ""))

        return memory

    def _render(self) -> str:
        """Render ProjectMemory back to AUTOAGENT.md format."""
        lines = ["# AUTOAGENT.md — Project Memory", ""]

        lines.append("## Agent Identity")
        lines.append(f"- Name: {self.agent_name}")
        lines.append(f"- Platform: {self.platform}")
        lines.append(f"- Primary use case: {self.use_case}")
        lines.append("")

        lines.append("## Business Constraints")
        for c in self.business_constraints:
            line = c if c.startswith("- ") else f"- {c}"
            lines.append(line)
        lines.append("")

        lines.append("## Known Good Patterns")
        for p in self.known_good_patterns:
            line = p if p.startswith("- ") else f"- {p}"
            lines.append(line)
        lines.append("")

        lines.append("## Known Bad Patterns")
        for p in self.known_bad_patterns:
            line = p if p.startswith("- ") else f"- {p}"
            lines.append(line)
        lines.append("")

        lines.append("## Team Preferences")
        for p in self.team_preferences:
            line = p if p.startswith("- ") else f"- {p}"
            lines.append(line)
        lines.append("")

        lines.append("## Optimization History")
        for h in self.optimization_history:
            line = h if h.startswith("- ") else f"- {h}"
            lines.append(line)
        lines.append("")

        return "\n".join(lines)


def _split_sections(content: str) -> dict[str, str]:
    """Split markdown content into sections by ## headers."""
    sections: dict[str, str] = {}
    current_header = ""
    current_lines: list[str] = []

    for line in content.splitlines():
        if line.startswith("## "):
            if current_header:
                sections[current_header] = "\n".join(current_lines)
            current_header = line[3:].strip().lower()
            current_lines = []
        else:
            current_lines.append(line)

    if current_header:
        sections[current_header] = "\n".join(current_lines)

    return sections


def _parse_list_section(text: str) -> list[str]:
    """Parse a section with bullet points into a list of strings."""
    items: list[str] = []
    for line in text.strip().splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
        elif stripped.startswith("* "):
            items.append(stripped[2:].strip())
        elif stripped and not stripped.startswith("#") and not stripped.startswith("("):
            # Non-empty, non-comment lines
            items.append(stripped)
    return items

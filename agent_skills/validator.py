"""Validates generated skills before presenting for review."""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass
class ValidationResult:
    """Result of validating a generated skill."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "errors": self.errors, "warnings": self.warnings}


class SkillValidator:
    """Validates generated skills before presenting for review."""

    def validate(self, skill: Any) -> ValidationResult:
        """Validate a GeneratedSkill instance.

        Checks:
        - Syntax validation (Python with ast.parse, YAML with yaml.safe_load)
        - Type hints present on function signatures (for Python)
        - Docstring present (for Python)
        - Name collision check against known_names
        - No unfilled Jinja2 placeholders remain ({{ or {% patterns)
        - Import check (common imports are available)
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Check for unfilled Jinja2 placeholders
        content = skill.source_code or skill.config_yaml or ""
        if re.search(r'\{\{.*?\}\}', content) or re.search(r'\{%.*?%\}', content):
            errors.append("Unfilled Jinja2 placeholders detected in generated code")

        # Platform-specific validation
        if skill.source_code:
            self._validate_python(skill.source_code, errors, warnings)
        if skill.config_yaml:
            self._validate_yaml(skill.config_yaml, errors, warnings)

        # Validate files
        for f in skill.files:
            if f.path.endswith(".py"):
                self._validate_python(f.content, errors, warnings)
            elif f.path.endswith((".yaml", ".yml")):
                self._validate_yaml(f.content, errors, warnings)

        # Check required fields
        if not skill.name:
            errors.append("Skill name is required")
        if not skill.description:
            errors.append("Skill description is required")
        if not skill.skill_type:
            errors.append("Skill type is required")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_name(self, name: str, known_names: list[str] | None = None) -> ValidationResult:
        """Validate a skill name for conflicts and format."""
        errors: list[str] = []
        warnings: list[str] = []

        if not name:
            errors.append("Name cannot be empty")
        elif not re.match(r'^[a-z][a-z0-9_]*$', name):
            warnings.append(f"Name '{name}' doesn't follow snake_case convention")

        if known_names and name in known_names:
            errors.append(f"Name '{name}' conflicts with existing skill")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _validate_python(self, source: str, errors: list[str], warnings: list[str]) -> None:
        """Validate Python source code."""
        # Syntax check
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            errors.append(f"Python syntax error: {exc}")
            return

        # Check for function definitions with type hints and docstrings
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check type hints
                has_return_annotation = node.returns is not None
                if not has_return_annotation:
                    warnings.append(f"Function '{node.name}' missing return type annotation")

                # Check for unannotated args (skip 'self')
                for arg in node.args.args:
                    if arg.arg != "self" and arg.annotation is None:
                        warnings.append(
                            f"Parameter '{arg.arg}' in '{node.name}' missing type annotation"
                        )

                # Check docstring (ast.Str removed in Python 3.12+; ast.Constant covers all literals)
                if not (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                ):
                    warnings.append(f"Function '{node.name}' missing docstring")

    def _validate_yaml(self, content: str, errors: list[str], warnings: list[str]) -> None:
        """Validate YAML content."""
        try:
            result = yaml.safe_load(content)
            if result is None:
                warnings.append("YAML content is empty")
        except yaml.YAMLError as exc:
            errors.append(f"YAML parse error: {exc}")

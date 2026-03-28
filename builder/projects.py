"""Builder project management and inheritance utilities."""

from __future__ import annotations

from typing import Any

from builder.store import BuilderStore
from builder.types import BuilderProject, now_ts


class BuilderProjectManager:
    """Manages BuilderProject objects and inheritance behavior."""

    def __init__(self, store: BuilderStore) -> None:
        self._store = store

    def create_project(
        self,
        name: str,
        description: str = "",
        **kwargs: Any,
    ) -> BuilderProject:
        """Create and persist a new builder project."""

        project = BuilderProject(name=name, description=description, **kwargs)
        project.updated_at = project.created_at
        self._store.save_project(project)
        return project

    def get_project(self, project_id: str) -> BuilderProject | None:
        """Fetch a project by ID."""

        return self._store.get_project(project_id)

    def list_projects(self, archived: bool | None = False) -> list[BuilderProject]:
        """List projects filtered by archive status."""

        return self._store.list_projects(archived=archived)

    def update_project(self, project_id: str, **changes: Any) -> BuilderProject | None:
        """Patch mutable project fields and persist."""

        project = self._store.get_project(project_id)
        if project is None:
            return None

        for key, value in changes.items():
            if hasattr(project, key):
                setattr(project, key, value)

        project.updated_at = now_ts()
        self._store.save_project(project)
        return project

    def delete_project(self, project_id: str) -> bool:
        """Delete a project by ID."""

        return self._store.delete_project(project_id)

    # ------------------------------------------------------------------
    # Instruction inheritance
    # ------------------------------------------------------------------

    def set_folder_instruction(self, project_id: str, folder_path: str, instruction: str) -> BuilderProject | None:
        """Set folder-level instruction inherited by tasks in that folder."""

        project = self._store.get_project(project_id)
        if project is None:
            return None

        project.folder_instructions[folder_path] = instruction
        project.updated_at = now_ts()
        self._store.save_project(project)
        return project

    def resolve_instructions(
        self,
        project_id: str,
        folder_path: str | None = None,
        task_instruction: str | None = None,
    ) -> dict[str, str]:
        """Resolve effective instruction using project → folder → task precedence."""

        project = self._store.get_project(project_id)
        if project is None:
            return {
                "project": "",
                "folder": "",
                "task": task_instruction or "",
                "effective": task_instruction or "",
            }

        project_instruction = project.master_instruction.strip()
        folder_instruction = ""
        if folder_path:
            folder_instruction = project.folder_instructions.get(folder_path, "").strip()

        task_text = (task_instruction or "").strip()
        parts = [project_instruction, folder_instruction, task_text]
        effective = "\n\n".join(part for part in parts if part)

        return {
            "project": project_instruction,
            "folder": folder_instruction,
            "task": task_text,
            "effective": effective,
        }

    # ------------------------------------------------------------------
    # Knowledge files and defaults
    # ------------------------------------------------------------------

    def add_knowledge_file(self, project_id: str, path: str) -> BuilderProject | None:
        """Attach a knowledge file path to a project."""

        project = self._store.get_project(project_id)
        if project is None:
            return None
        if path not in project.knowledge_files:
            project.knowledge_files.append(path)
            project.updated_at = now_ts()
            self._store.save_project(project)
        return project

    def remove_knowledge_file(self, project_id: str, path: str) -> BuilderProject | None:
        """Remove a knowledge file path from a project."""

        project = self._store.get_project(project_id)
        if project is None:
            return None
        if path in project.knowledge_files:
            project.knowledge_files = [file_path for file_path in project.knowledge_files if file_path != path]
            project.updated_at = now_ts()
            self._store.save_project(project)
        return project

    def set_skill_defaults(
        self,
        project_id: str,
        buildtime_skills: list[str] | None = None,
        runtime_skills: list[str] | None = None,
    ) -> BuilderProject | None:
        """Update project default skill lists."""

        project = self._store.get_project(project_id)
        if project is None:
            return None

        if buildtime_skills is not None:
            project.buildtime_skills = buildtime_skills
        if runtime_skills is not None:
            project.runtime_skills = runtime_skills

        project.updated_at = now_ts()
        self._store.save_project(project)
        return project

    def set_eval_defaults(self, project_id: str, defaults: dict[str, Any]) -> BuilderProject | None:
        """Update project eval defaults."""

        project = self._store.get_project(project_id)
        if project is None:
            return None

        project.eval_defaults = defaults
        project.updated_at = now_ts()
        self._store.save_project(project)
        return project

    def set_model_preferences(self, project_id: str, preferences: dict[str, str]) -> BuilderProject | None:
        """Update model/backend preferences for the project."""

        project = self._store.get_project(project_id)
        if project is None:
            return None

        project.preferred_models = preferences
        project.updated_at = now_ts()
        self._store.save_project(project)
        return project

    def set_deployment_targets(self, project_id: str, targets: list[str]) -> BuilderProject | None:
        """Update deployment targets list."""

        project = self._store.get_project(project_id)
        if project is None:
            return None

        project.deployment_targets = targets
        project.updated_at = now_ts()
        self._store.save_project(project)
        return project

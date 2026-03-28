"""Tests for BuilderProjectManager."""
from __future__ import annotations

import pytest

from builder.projects import BuilderProjectManager
from builder.store import BuilderStore


@pytest.fixture
def store(tmp_path):
    return BuilderStore(db_path=str(tmp_path / "projects.db"))


@pytest.fixture
def manager(store):
    return BuilderProjectManager(store=store)


class TestCRUD:
    def test_create_project(self, manager):
        project = manager.create_project(name="Alpha", description="First project")
        assert project.name == "Alpha"
        assert project.description == "First project"
        assert project.project_id != ""
        assert project.created_at > 0

    def test_get_project(self, manager):
        project = manager.create_project(name="Beta")
        loaded = manager.get_project(project.project_id)
        assert loaded is not None
        assert loaded.name == "Beta"

    def test_get_missing_returns_none(self, manager):
        assert manager.get_project("nonexistent") is None

    def test_list_projects_default_active(self, manager):
        manager.create_project(name="Active 1")
        manager.create_project(name="Active 2")
        p = manager.create_project(name="Archived")
        manager.update_project(p.project_id, archived=True)
        active = manager.list_projects(archived=False)
        assert len(active) == 2
        assert all(not proj.archived for proj in active)

    def test_update_project(self, manager):
        project = manager.create_project(name="Old Name")
        updated = manager.update_project(project.project_id, name="New Name", description="Updated")
        assert updated is not None
        assert updated.name == "New Name"
        assert updated.description == "Updated"
        assert updated.updated_at >= project.updated_at

    def test_update_missing_returns_none(self, manager):
        assert manager.update_project("nonexistent", name="X") is None

    def test_delete_project(self, manager):
        project = manager.create_project(name="To Delete")
        assert manager.delete_project(project.project_id) is True
        assert manager.get_project(project.project_id) is None

    def test_delete_missing_returns_false(self, manager):
        assert manager.delete_project("nonexistent") is False


class TestInstructionInheritance:
    def test_resolve_with_only_project_instruction(self, manager):
        project = manager.create_project(name="P", master_instruction="Be concise.")
        result = manager.resolve_instructions(project.project_id)
        assert result["project"] == "Be concise."
        assert result["folder"] == ""
        assert result["task"] == ""
        assert result["effective"] == "Be concise."

    def test_resolve_with_folder_instruction(self, manager):
        project = manager.create_project(name="P", master_instruction="Project rule.")
        manager.set_folder_instruction(project.project_id, "src/", "Folder rule.")
        result = manager.resolve_instructions(project.project_id, folder_path="src/")
        assert result["project"] == "Project rule."
        assert result["folder"] == "Folder rule."
        assert "Project rule." in result["effective"]
        assert "Folder rule." in result["effective"]

    def test_resolve_all_three_levels(self, manager):
        project = manager.create_project(name="P", master_instruction="P.")
        manager.set_folder_instruction(project.project_id, "tests/", "F.")
        result = manager.resolve_instructions(project.project_id, folder_path="tests/", task_instruction="T.")
        assert result["task"] == "T."
        assert "P." in result["effective"]
        assert "F." in result["effective"]
        assert "T." in result["effective"]

    def test_unknown_folder_returns_empty(self, manager):
        project = manager.create_project(name="P")
        result = manager.resolve_instructions(project.project_id, folder_path="unknown/")
        assert result["folder"] == ""

    def test_resolve_missing_project(self, manager):
        result = manager.resolve_instructions("nonexistent", task_instruction="T.")
        assert result["effective"] == "T."
        assert result["project"] == ""

    def test_set_folder_instruction(self, manager):
        project = manager.create_project(name="P")
        updated = manager.set_folder_instruction(project.project_id, "api/", "API rules.")
        assert updated is not None
        loaded = manager.get_project(project.project_id)
        assert loaded.folder_instructions.get("api/") == "API rules."


class TestKnowledgeFiles:
    def test_add_knowledge_file(self, manager):
        project = manager.create_project(name="P")
        result = manager.add_knowledge_file(project.project_id, "docs/guide.md")
        assert "docs/guide.md" in result.knowledge_files

    def test_add_duplicate_is_idempotent(self, manager):
        project = manager.create_project(name="P")
        manager.add_knowledge_file(project.project_id, "docs/guide.md")
        manager.add_knowledge_file(project.project_id, "docs/guide.md")
        loaded = manager.get_project(project.project_id)
        assert loaded.knowledge_files.count("docs/guide.md") == 1

    def test_remove_knowledge_file(self, manager):
        project = manager.create_project(name="P")
        manager.add_knowledge_file(project.project_id, "docs/guide.md")
        result = manager.remove_knowledge_file(project.project_id, "docs/guide.md")
        assert "docs/guide.md" not in result.knowledge_files

    def test_remove_missing_file_is_noop(self, manager):
        project = manager.create_project(name="P")
        result = manager.remove_knowledge_file(project.project_id, "nonexistent.md")
        assert result is not None


class TestSkillDefaults:
    def test_set_buildtime_skills(self, manager):
        project = manager.create_project(name="P")
        result = manager.set_skill_defaults(project.project_id, buildtime_skills=["skill-A", "skill-B"])
        assert result.buildtime_skills == ["skill-A", "skill-B"]

    def test_set_runtime_skills(self, manager):
        project = manager.create_project(name="P")
        result = manager.set_skill_defaults(project.project_id, runtime_skills=["skill-C"])
        assert result.runtime_skills == ["skill-C"]

    def test_set_model_preferences(self, manager):
        project = manager.create_project(name="P")
        result = manager.set_model_preferences(project.project_id, {"orchestrator": "claude-opus-4-6"})
        assert result.preferred_models["orchestrator"] == "claude-opus-4-6"

    def test_set_deployment_targets(self, manager):
        project = manager.create_project(name="P")
        result = manager.set_deployment_targets(project.project_id, ["prod", "staging"])
        assert result.deployment_targets == ["prod", "staging"]

    def test_set_eval_defaults(self, manager):
        project = manager.create_project(name="P")
        result = manager.set_eval_defaults(project.project_id, {"threshold": 0.9})
        assert result.eval_defaults["threshold"] == 0.9

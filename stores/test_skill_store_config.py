"""Tests for skill_store_config canonical path configuration."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest


class TestSkillDbPathDefault:
    def test_defaults_to_autoagent_skills_db(self) -> None:
        import stores.skill_store_config as cfg
        # Reload to ensure we get the module-level value without env override
        importlib.reload(cfg)
        assert cfg.SKILL_DB_PATH == Path(".autoagent/skills.db")

    def test_returns_path_object(self) -> None:
        import stores.skill_store_config as cfg
        importlib.reload(cfg)
        assert isinstance(cfg.SKILL_DB_PATH, Path)


class TestSkillDbPathEnvOverride:
    def test_env_var_overrides_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AUTOAGENT_SKILL_DB", "/custom/path/skills.db")
        import stores.skill_store_config as cfg
        importlib.reload(cfg)
        assert cfg.SKILL_DB_PATH == Path("/custom/path/skills.db")

    def test_relative_env_var_becomes_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AUTOAGENT_SKILL_DB", "other/skills.db")
        import stores.skill_store_config as cfg
        importlib.reload(cfg)
        assert cfg.SKILL_DB_PATH == Path("other/skills.db")

    def test_unset_env_var_restores_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("AUTOAGENT_SKILL_DB", raising=False)
        import stores.skill_store_config as cfg
        importlib.reload(cfg)
        assert cfg.SKILL_DB_PATH == Path(".autoagent/skills.db")

"""Tests for ADK importer."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from adk.importer import AdkImporter
from adk.mapper import AdkMapper


@pytest.fixture
def sample_agent_path():
    """Return path to sample ADK agent fixture."""
    return Path(__file__).parent / "fixtures" / "sample_adk_agent"


@pytest.fixture
def importer():
    """Create AdkImporter instance."""
    return AdkImporter()


def test_import_creates_config_file(importer, sample_agent_path, tmp_path):
    """Test import creates config YAML file."""
    result = importer.import_agent(
        agent_path=str(sample_agent_path),
        output_dir=str(tmp_path),
    )

    assert Path(result.config_path).exists()

    # Read and validate config
    with open(result.config_path) as f:
        config = yaml.safe_load(f)

    assert "prompts" in config
    assert "tools" in config
    assert "routing" in config


def test_import_creates_snapshot(importer, sample_agent_path, tmp_path):
    """Test import creates snapshot directory."""
    result = importer.import_agent(
        agent_path=str(sample_agent_path),
        output_dir=str(tmp_path),
    )

    snapshot_path = Path(result.snapshot_path)
    assert snapshot_path.exists()
    assert snapshot_path.is_dir()

    # Check key files were copied
    assert (snapshot_path / "agent.py").exists()
    assert (snapshot_path / "tools.py").exists()
    assert (snapshot_path / "config.json").exists()


def test_import_result_summary(importer, sample_agent_path, tmp_path):
    """Test import result contains correct summary."""
    result = importer.import_agent(
        agent_path=str(sample_agent_path),
        output_dir=str(tmp_path),
    )

    assert result.agent_name == "support_agent"
    assert "prompts" in result.surfaces_mapped
    assert "tools" in result.surfaces_mapped
    assert "routing" in result.surfaces_mapped
    assert result.tools_imported == 3  # lookup_order, search_knowledge_base, create_ticket


def test_import_idempotent(importer, sample_agent_path, tmp_path):
    """Test can re-import same agent."""
    result1 = importer.import_agent(
        agent_path=str(sample_agent_path),
        output_dir=str(tmp_path),
    )

    result2 = importer.import_agent(
        agent_path=str(sample_agent_path),
        output_dir=str(tmp_path),
    )

    assert result1.agent_name == result2.agent_name
    assert Path(result2.config_path).exists()


def test_invalid_path_raises_error(importer, tmp_path):
    """Test invalid path raises AdkImportError."""
    from adk.errors import AdkImportError

    with pytest.raises(AdkImportError):
        importer.import_agent(
            agent_path=str(tmp_path / "nonexistent"),
            output_dir=str(tmp_path),
        )


def test_import_without_snapshot(importer, sample_agent_path, tmp_path):
    """Test import with save_snapshot=False."""
    result = importer.import_agent(
        agent_path=str(sample_agent_path),
        output_dir=str(tmp_path),
        save_snapshot=False,
    )

    # Config should exist
    assert Path(result.config_path).exists()

    # Snapshot should still be reported but directory won't have been created
    assert result.snapshot_path


def test_import_with_custom_mapper(sample_agent_path, tmp_path):
    """Test import with custom mapper instance."""
    custom_mapper = AdkMapper()
    importer = AdkImporter(mapper=custom_mapper)

    result = importer.import_agent(
        agent_path=str(sample_agent_path),
        output_dir=str(tmp_path),
    )

    assert result.agent_name == "support_agent"


def test_import_preserves_subagents(importer, sample_agent_path, tmp_path):
    """Test sub-agents are preserved in snapshot."""
    result = importer.import_agent(
        agent_path=str(sample_agent_path),
        output_dir=str(tmp_path),
    )

    snapshot_path = Path(result.snapshot_path)
    sub_agents_dir = snapshot_path / "sub_agents" / "billing"

    assert sub_agents_dir.exists()
    assert (sub_agents_dir / "agent.py").exists()
    assert (sub_agents_dir / "tools.py").exists()


def test_import_config_excludes_metadata(importer, sample_agent_path, tmp_path):
    """Test config file doesn't include _adk_metadata."""
    result = importer.import_agent(
        agent_path=str(sample_agent_path),
        output_dir=str(tmp_path),
    )

    with open(result.config_path) as f:
        config = yaml.safe_load(f)

    # Metadata should be stripped before writing
    assert "_adk_metadata" not in config


def test_import_handles_missing_config_json(importer, tmp_path):
    """Test import works even without config.json."""
    # Create minimal agent structure without config.json
    agent_dir = tmp_path / "minimal_agent"
    agent_dir.mkdir()

    (agent_dir / "__init__.py").write_text(
        "from .agent import root_agent\n__all__ = ['root_agent']"
    )
    (agent_dir / "agent.py").write_text(
        "from google.adk.agents import Agent\n"
        "root_agent = Agent(name='minimal', model='gemini-2.0-flash', "
        "instruction='Minimal agent')"
    )
    (agent_dir / "tools.py").write_text("")

    result = importer.import_agent(
        agent_path=str(agent_dir),
        output_dir=str(tmp_path / "output"),
    )

    assert result.agent_name == "minimal"
    assert Path(result.config_path).exists()

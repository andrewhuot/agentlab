"""Tests for ADK exporter."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from adk.errors import AdkExportError
from adk.exporter import AdkExporter
from adk.types import AdkAgent, AdkAgentTree, AdkTool


@pytest.fixture
def sample_agent_tree(tmp_path: Path) -> AdkAgentTree:
    """Create a sample agent tree for testing."""
    agent_dir = tmp_path / "test_agent"
    agent_dir.mkdir()

    # Create agent.py
    agent_py = agent_dir / "agent.py"
    agent_py.write_text(
        '''"""Test agent."""
from google.adk.agents import Agent

root_agent = Agent(
    name="test_agent",
    model="gemini-2.0-flash",
    instruction="""You are a helpful test agent.
You assist users with testing.""",
    tools=[lookup_data, process_data],
    generate_config={"temperature": 0.3, "max_output_tokens": 1024},
)
'''
    )

    # Create tools.py
    tools_py = agent_dir / "tools.py"
    tools_py.write_text(
        '''"""Test tools."""
from google.adk.tools import tool

@tool
def lookup_data(query: str) -> str:
    """Look up data based on a query."""
    return "data"

@tool
def process_data(data: str) -> str:
    """Process the given data."""
    return "processed"
'''
    )

    # Create __init__.py
    init_py = agent_dir / "__init__.py"
    init_py.write_text("from .agent import root_agent\n")

    # Create config.json
    config_json = agent_dir / "config.json"
    config_json.write_text(
        json.dumps({"temperature": 0.3, "max_output_tokens": 1024}, indent=2)
    )

    return AdkAgentTree(
        agent=AdkAgent(
            name="test_agent",
            model="gemini-2.0-flash",
            instruction="You are a helpful test agent.\nYou assist users with testing.",
            tools=["lookup_data", "process_data"],
            generate_config={"temperature": 0.3, "max_output_tokens": 1024},
        ),
        tools=[
            AdkTool(
                name="lookup_data",
                description="Look up data based on a query.",
                signature="lookup_data(query: str)",
            ),
            AdkTool(
                name="process_data",
                description="Process the given data.",
                signature="process_data(data: str)",
            ),
        ],
        source_path=agent_dir,
    )


def test_export_creates_patched_files(tmp_path: Path, sample_agent_tree: AdkAgentTree):
    """Test that export creates patched files."""
    exporter = AdkExporter()

    # Create optimized config with changes
    config = {
        "name": "test_agent",
        "instructions": {
            "test_agent": "You are an optimized test agent.\nYou help users efficiently."
        },
        "generation_settings": {
            "model": "gemini-2.0-flash-exp",
            "temperature": 0.5,
        },
    }

    output_dir = tmp_path / "output"

    result = exporter.export_agent(
        config,
        str(sample_agent_tree.source_path),
        str(output_dir),
        dry_run=False,
    )

    # Check that files were created
    assert (output_dir / "agent.py").exists()
    assert result.files_modified > 0
    assert len(result.changes) > 0


def test_export_preserves_formatting(tmp_path: Path, sample_agent_tree: AdkAgentTree):
    """Test that export preserves comments and indentation."""
    # Add comments to agent.py
    agent_py = sample_agent_tree.source_path / "agent.py"
    original = agent_py.read_text()
    with_comments = original.replace(
        'from google.adk.agents import Agent',
        '# Import Agent class\nfrom google.adk.agents import Agent  # ADK framework',
    )
    agent_py.write_text(with_comments)

    exporter = AdkExporter()

    config = {
        "name": "test_agent",
        "generation_settings": {"temperature": 0.7},
    }

    output_dir = tmp_path / "output"

    exporter.export_agent(
        config,
        str(sample_agent_tree.source_path),
        str(output_dir),
        dry_run=False,
    )

    # Check that comments are preserved
    patched = (output_dir / "agent.py").read_text()
    assert "# Import Agent class" in patched
    assert "# ADK framework" in patched


def test_export_updates_instructions(tmp_path: Path, sample_agent_tree: AdkAgentTree):
    """Test that export updates instruction field."""
    exporter = AdkExporter()

    new_instruction = "This is a completely new instruction."

    config = {
        "name": "test_agent",
        "instructions": {"test_agent": new_instruction},
    }

    output_dir = tmp_path / "output"

    result = exporter.export_agent(
        config,
        str(sample_agent_tree.source_path),
        str(output_dir),
        dry_run=False,
    )

    # Check changes
    assert any(c["field"] == "instruction" for c in result.changes)

    # Verify file content
    patched = (output_dir / "agent.py").read_text()
    assert new_instruction in patched


def test_export_updates_config_values(tmp_path: Path, sample_agent_tree: AdkAgentTree):
    """Test that export updates generation config values."""
    exporter = AdkExporter()

    config = {
        "name": "test_agent",
        "generation_settings": {
            "temperature": 0.9,
            "max_output_tokens": 2048,
        },
    }

    output_dir = tmp_path / "output"

    result = exporter.export_agent(
        config,
        str(sample_agent_tree.source_path),
        str(output_dir),
        dry_run=False,
    )

    # Check changes
    assert any(c["field"] == "temperature" for c in result.changes)
    assert any(c["field"] == "max_output_tokens" for c in result.changes)

    # Verify config.json
    config_json = json.loads((output_dir / "config.json").read_text())
    assert config_json["temperature"] == 0.9
    assert config_json["max_output_tokens"] == 2048


def test_preview_changes_no_write(tmp_path: Path, sample_agent_tree: AdkAgentTree):
    """Test that preview_changes doesn't write files."""
    exporter = AdkExporter()

    config = {
        "name": "test_agent",
        "instructions": {"test_agent": "New instruction"},
        "generation_settings": {"temperature": 0.8},
    }

    output_dir = tmp_path / "output"

    result = exporter.export_agent(
        config,
        str(sample_agent_tree.source_path),
        str(output_dir),
        dry_run=True,
    )

    # Check that no files were written
    assert not output_dir.exists()
    assert result.files_modified == 0
    assert len(result.changes) > 0


def test_compute_changes_diff(tmp_path: Path, sample_agent_tree: AdkAgentTree):
    """Test that compute_changes correctly identifies differences."""
    exporter = AdkExporter()

    config = {
        "name": "test_agent",
        "instructions": {"test_agent": "Different instruction"},
        "generation_settings": {
            "model": "gemini-2.0-pro",
            "temperature": 0.1,
        },
        "tool_descriptions": {
            "lookup_data": "Updated description for lookup_data.",
        },
    }

    changes = exporter.preview_changes(config, str(sample_agent_tree.source_path))

    # Check that all expected changes are detected
    change_fields = {c["field"] for c in changes}
    assert "instruction" in change_fields
    assert "model" in change_fields
    assert "temperature" in change_fields
    assert "description" in change_fields


def test_roundtrip_export(tmp_path: Path, sample_agent_tree: AdkAgentTree):
    """Test that import → optimize → export → re-import preserves structure."""
    from adk.parser import parse_agent_directory

    exporter = AdkExporter()

    # Create config with modifications
    config = {
        "name": "test_agent",
        "instructions": {"test_agent": "Modified instruction for roundtrip test."},
        "generation_settings": {
            "temperature": 0.6,
        },
    }

    # Export
    output_dir = tmp_path / "output"
    exporter.export_agent(
        config,
        str(sample_agent_tree.source_path),
        str(output_dir),
        dry_run=False,
    )

    # Re-import the exported agent
    reimported_tree = parse_agent_directory(output_dir)

    # Check that modifications were applied
    assert "Modified instruction for roundtrip test" in reimported_tree.agent.instruction
    # Config.json is updated, which is stored in tree.config
    assert reimported_tree.config.get("temperature") == 0.6


def test_export_invalid_snapshot_raises_error():
    """Test that export raises error for invalid snapshot path."""
    exporter = AdkExporter()

    config = {"name": "test"}

    with pytest.raises(AdkExportError) as exc_info:
        exporter.export_agent(config, "/nonexistent/path", "/output")

    assert "Snapshot directory not found" in str(exc_info.value)


def test_export_tool_docstring_update(tmp_path: Path, sample_agent_tree: AdkAgentTree):
    """Test that export updates tool docstrings."""
    exporter = AdkExporter()

    new_description = "This is an updated description for the lookup_data tool."

    config = {
        "name": "test_agent",
        "tool_descriptions": {
            "lookup_data": new_description,
        },
    }

    output_dir = tmp_path / "output"

    result = exporter.export_agent(
        config,
        str(sample_agent_tree.source_path),
        str(output_dir),
        dry_run=False,
    )

    # Check changes
    assert any(
        c["resource"] == "tool" and c["tool_name"] == "lookup_data"
        for c in result.changes
    )

    # Verify tools.py content
    tools_py = (output_dir / "tools.py").read_text()
    assert new_description in tools_py


def test_export_model_update(tmp_path: Path, sample_agent_tree: AdkAgentTree):
    """Test that export updates model field."""
    exporter = AdkExporter()

    new_model = "gemini-3.0-ultra"

    config = {
        "name": "test_agent",
        "generation_settings": {
            "model": new_model,
        },
    }

    output_dir = tmp_path / "output"

    result = exporter.export_agent(
        config,
        str(sample_agent_tree.source_path),
        str(output_dir),
        dry_run=False,
    )

    # Check changes
    assert any(c["field"] == "model" for c in result.changes)

    # Verify agent.py content
    agent_py = (output_dir / "agent.py").read_text()
    assert new_model in agent_py


def test_export_with_no_changes(tmp_path: Path, sample_agent_tree: AdkAgentTree):
    """Test that export with no changes returns empty result."""
    exporter = AdkExporter()

    # Create config that matches the original - use empty config to simulate no changes
    config = {
        "name": "test_agent",
        "instructions": {
            "test_agent": sample_agent_tree.agent.instruction,
        },
        "generation_settings": sample_agent_tree.agent.generate_config,
    }

    output_dir = tmp_path / "output"

    result = exporter.export_agent(
        config,
        str(sample_agent_tree.source_path),
        str(output_dir),
        dry_run=False,
    )

    # Should have no changes
    assert len(result.changes) == 0
    assert result.files_modified == 0

"""Integration tests for ADK Track B (mapper + importer)."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from adk.importer import AdkImporter
from adk.mapper import AdkMapper
from adk.parser import parse_agent_directory


@pytest.fixture
def sample_agent_path():
    """Return path to sample ADK agent fixture."""
    return Path(__file__).parent / "fixtures" / "sample_adk_agent"


def test_full_import_pipeline(sample_agent_path, tmp_path):
    """Test complete import pipeline: parse → map → save."""
    # 1. Parse agent directory
    tree = parse_agent_directory(sample_agent_path)
    assert tree.agent.name == "support_agent"
    assert len(tree.tools) == 3
    assert len(tree.sub_agents) == 1

    # 2. Map to AgentLab config
    mapper = AdkMapper()
    config = mapper.to_agentlab(tree)

    assert "prompts" in config
    assert "root" in config["prompts"]
    assert "billing_agent" in config["prompts"]

    assert "tools" in config
    assert "lookup_order" in config["tools"]
    assert "search_knowledge_base" in config["tools"]
    assert "create_ticket" in config["tools"]

    assert "routing" in config
    assert len(config["routing"]["rules"]) == 1
    assert config["routing"]["rules"][0]["specialist"] == "billing_agent"

    # 3. Import full agent (includes parsing, mapping, and saving)
    importer = AdkImporter()
    result = importer.import_agent(
        agent_path=str(sample_agent_path),
        output_dir=str(tmp_path),
    )

    assert result.agent_name == "support_agent"
    assert result.tools_imported == 3
    assert "prompts" in result.surfaces_mapped
    assert "tools" in result.surfaces_mapped
    assert "routing" in result.surfaces_mapped

    # 4. Verify saved config file
    config_path = Path(result.config_path)
    assert config_path.exists()

    with open(config_path) as f:
        saved_config = yaml.safe_load(f)

    assert saved_config["prompts"]["root"] == config["prompts"]["root"]
    assert saved_config["model"] == "gemini-2.0-flash"

    # 5. Verify snapshot was created
    snapshot_path = Path(result.snapshot_path)
    assert snapshot_path.exists()
    assert (snapshot_path / "agent.py").exists()
    assert (snapshot_path / "tools.py").exists()


def test_round_trip_config_preservation(sample_agent_path, tmp_path):
    """Test that config → tree → config preserves all data."""
    # Parse original
    tree1 = parse_agent_directory(sample_agent_path)

    # Map to config
    mapper = AdkMapper()
    config = mapper.to_agentlab(tree1)

    # Map back to tree
    tree2 = mapper.to_adk(config, tree1)

    # Map to config again
    config2 = mapper.to_agentlab(tree2)

    # Compare configs
    assert config["prompts"]["root"] == config2["prompts"]["root"]
    assert config["prompts"]["billing_agent"] == config2["prompts"]["billing_agent"]
    assert config["model"] == config2["model"]
    assert config["generation"]["temperature"] == config2["generation"]["temperature"]


def test_import_with_modified_config(sample_agent_path, tmp_path):
    """Test importing an agent and applying modifications."""
    # Import agent
    importer = AdkImporter()
    result = importer.import_agent(
        agent_path=str(sample_agent_path),
        output_dir=str(tmp_path),
    )

    # Load config
    with open(result.config_path) as f:
        config = yaml.safe_load(f)

    # Modify config
    config["prompts"]["root"] = "Modified instruction"
    config["generation"]["temperature"] = 0.7

    # Apply modifications back to tree
    tree = parse_agent_directory(sample_agent_path)
    mapper = AdkMapper()
    modified_tree = mapper.to_adk(config, tree)

    assert modified_tree.agent.instruction == "Modified instruction"
    assert modified_tree.agent.generate_config["temperature"] == 0.7


def test_keyword_derivation_for_routing(sample_agent_path):
    """Test that routing keywords are intelligently derived."""
    mapper = AdkMapper()
    tree = parse_agent_directory(sample_agent_path)
    config = mapper.to_agentlab(tree)

    billing_rule = None
    for rule in config["routing"]["rules"]:
        if rule["specialist"] == "billing_agent":
            billing_rule = rule
            break

    assert billing_rule is not None
    keywords = billing_rule["keywords"]

    # Should have billing and related terms
    assert "billing" in keywords
    assert any(kw in keywords for kw in ["bill", "payment", "invoice"])


def test_sub_agent_tools_preserved(sample_agent_path):
    """Test that sub-agent tools are preserved in the tree."""
    tree = parse_agent_directory(sample_agent_path)

    # Check sub-agent exists
    assert len(tree.sub_agents) == 1
    billing_tree = tree.sub_agents[0]

    # Check sub-agent has its own tools
    assert len(billing_tree.tools) == 2
    tool_names = [t.name for t in billing_tree.tools]
    assert "get_billing_history" in tool_names
    assert "process_refund" in tool_names

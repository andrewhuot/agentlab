"""Tests for ADK parser."""
from __future__ import annotations

from pathlib import Path

import pytest

from adk.errors import AdkParseError
from adk.parser import parse_agent_directory
from adk.types import AdkAgent, AdkAgentTree, AdkTool


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_agent_path() -> Path:
    """Path to sample ADK agent fixture."""
    return Path(__file__).parent / "fixtures" / "sample_adk_agent"


@pytest.fixture
def billing_agent_path(sample_agent_path: Path) -> Path:
    """Path to billing sub-agent fixture."""
    return sample_agent_path / "sub_agents" / "billing"


# ---------------------------------------------------------------------------
# Test parse_agent_directory
# ---------------------------------------------------------------------------

def test_parse_simple_agent(billing_agent_path: Path):
    """Parse a simple agent without sub-agents."""
    tree = parse_agent_directory(billing_agent_path)

    assert tree.agent.name == "billing_agent"
    assert tree.agent.model == "gemini-2.0-flash"
    assert "billing specialist" in tree.agent.instruction.lower()
    assert len(tree.tools) == 2
    assert len(tree.sub_agents) == 0

    # Verify tools
    tool_names = {tool.name for tool in tree.tools}
    assert "get_billing_history" in tool_names
    assert "process_refund" in tool_names


def test_parse_agent_with_tools(sample_agent_path: Path):
    """Parse agent and verify tools extracted correctly."""
    tree = parse_agent_directory(sample_agent_path)

    assert len(tree.tools) == 3
    tool_names = {tool.name for tool in tree.tools}
    assert "lookup_order" in tool_names
    assert "search_knowledge_base" in tool_names
    assert "create_ticket" in tool_names

    # Verify tool descriptions extracted from docstrings
    lookup_tool = next((t for t in tree.tools if t.name == "lookup_order"), None)
    assert lookup_tool is not None
    assert "order ID" in lookup_tool.description
    assert "order_id: str" in lookup_tool.signature

    # Verify function body captured
    assert "def lookup_order" in lookup_tool.function_body
    assert "return" in lookup_tool.function_body


def test_parse_agent_with_subagents(sample_agent_path: Path):
    """Parse agent with sub-agents and verify hierarchy."""
    tree = parse_agent_directory(sample_agent_path)

    assert tree.agent.name == "support_agent"
    assert len(tree.sub_agents) == 1

    # Verify sub-agent
    billing_tree = tree.sub_agents[0]
    assert billing_tree.agent.name == "billing_agent"
    assert len(billing_tree.tools) == 2
    assert len(billing_tree.sub_agents) == 0

    # Verify sub-agent tools
    sub_tool_names = {tool.name for tool in billing_tree.tools}
    assert "get_billing_history" in sub_tool_names
    assert "process_refund" in sub_tool_names


def test_parse_agent_with_config(sample_agent_path: Path):
    """Parse agent and verify config.json merged."""
    tree = parse_agent_directory(sample_agent_path)

    # config.json should be merged into generate_config
    assert "model" in tree.config
    assert tree.config["model"] == "gemini-2.0-flash"
    assert tree.config["temperature"] == 0.3
    assert tree.config["max_output_tokens"] == 1024

    # Should also be in agent.generate_config
    assert tree.agent.generate_config["temperature"] == 0.3
    assert tree.agent.generate_config["max_output_tokens"] == 1024


def test_parse_instruction_from_prompts(sample_agent_path: Path):
    """Parse agent and verify instruction from prompts.py."""
    tree = parse_agent_directory(sample_agent_path)

    # Instruction should come from ROOT_INSTRUCTION in prompts.py
    assert "customer support agent" in tree.agent.instruction.lower()
    assert "billing questions" in tree.agent.instruction.lower()


def test_parse_agent_references(sample_agent_path: Path):
    """Parse agent and verify tool/sub-agent references."""
    tree = parse_agent_directory(sample_agent_path)

    # Verify tools list contains function names
    assert "lookup_order" in tree.agent.tools
    assert "search_knowledge_base" in tree.agent.tools
    assert "create_ticket" in tree.agent.tools

    # Verify sub_agents list contains agent names
    assert "billing_agent" in tree.agent.sub_agents


def test_parse_generate_config(billing_agent_path: Path):
    """Parse generate_config dict from Agent constructor."""
    tree = parse_agent_directory(billing_agent_path)

    assert tree.agent.generate_config is not None
    assert tree.agent.generate_config["temperature"] == 0.2
    assert tree.agent.generate_config["max_output_tokens"] == 512


def test_source_path_captured(sample_agent_path: Path):
    """Verify source_path is captured in tree."""
    tree = parse_agent_directory(sample_agent_path)

    assert tree.source_path == sample_agent_path.resolve()

    # Verify sub-agent source path
    billing_tree = tree.sub_agents[0]
    expected_billing_path = sample_agent_path / "sub_agents" / "billing"
    assert billing_tree.source_path == expected_billing_path.resolve()


def test_missing_directory_raises_error():
    """Parsing non-existent directory should raise AdkParseError."""
    with pytest.raises(AdkParseError, match="not found"):
        parse_agent_directory(Path("/nonexistent/path"))


def test_invalid_path_raises_error(tmp_path: Path):
    """Parsing a file (not directory) should raise AdkParseError."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("test")

    with pytest.raises(AdkParseError, match="not a directory"):
        parse_agent_directory(file_path)


def test_missing_agent_file_raises_error(tmp_path: Path):
    """Parsing directory without agent.py should raise AdkParseError."""
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    (agent_dir / "__init__.py").write_text("")

    with pytest.raises(AdkParseError, match="agent.py not found"):
        parse_agent_directory(agent_dir)


def test_invalid_python_raises_parse_error(tmp_path: Path):
    """Invalid Python syntax should raise AdkParseError."""
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    (agent_dir / "__init__.py").write_text("")
    (agent_dir / "agent.py").write_text("def invalid syntax here")

    with pytest.raises(AdkParseError, match="Invalid Python syntax"):
        parse_agent_directory(agent_dir)


def test_no_agent_constructor_raises_error(tmp_path: Path):
    """agent.py without Agent() constructor should raise AdkParseError."""
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    (agent_dir / "__init__.py").write_text("")
    (agent_dir / "agent.py").write_text("""
def some_function():
    return "hello"
""")

    with pytest.raises(AdkParseError, match="No Agent.*constructor"):
        parse_agent_directory(agent_dir)


def test_invalid_config_json_raises_error(tmp_path: Path):
    """Invalid config.json should raise AdkParseError."""
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    (agent_dir / "__init__.py").write_text("")
    (agent_dir / "agent.py").write_text("""
from google.adk.agents import Agent

root_agent = Agent(name="test", instruction="test")
""")
    (agent_dir / "config.json").write_text("{invalid json}")

    with pytest.raises(AdkParseError, match="Invalid config.json"):
        parse_agent_directory(agent_dir)


def test_agent_with_inline_instruction(tmp_path: Path):
    """Agent with inline instruction (not from prompts.py) should parse."""
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    (agent_dir / "__init__.py").write_text("")
    (agent_dir / "agent.py").write_text("""
from google.adk.agents import Agent

root_agent = Agent(
    name="test_agent",
    model="gemini-2.0-flash",
    instruction="This is an inline instruction.",
)
""")

    tree = parse_agent_directory(agent_dir)
    assert tree.agent.name == "test_agent"
    assert tree.agent.instruction == "This is an inline instruction."


def test_agent_without_tools(tmp_path: Path):
    """Agent without tools should parse successfully."""
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    (agent_dir / "__init__.py").write_text("")
    (agent_dir / "agent.py").write_text("""
from google.adk.agents import Agent

root_agent = Agent(
    name="simple_agent",
    instruction="Simple agent",
)
""")

    tree = parse_agent_directory(agent_dir)
    assert tree.agent.name == "simple_agent"
    assert len(tree.tools) == 0
    assert len(tree.agent.tools) == 0


def test_tools_without_docstring(tmp_path: Path):
    """Tools without docstrings should parse with empty description."""
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    (agent_dir / "__init__.py").write_text("")
    (agent_dir / "agent.py").write_text("""
from google.adk.agents import Agent

root_agent = Agent(name="test", instruction="test")
""")
    (agent_dir / "tools.py").write_text("""
from google.adk.tools import tool

@tool
def simple_tool():
    return "hello"
""")

    tree = parse_agent_directory(agent_dir)
    assert len(tree.tools) == 1
    assert tree.tools[0].name == "simple_tool"
    assert tree.tools[0].description == ""


def test_multiline_instruction(tmp_path: Path):
    """Agent with multi-line triple-quoted instruction should parse."""
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    (agent_dir / "__init__.py").write_text("")
    (agent_dir / "agent.py").write_text('''
from google.adk.agents import Agent

root_agent = Agent(
    name="test_agent",
    instruction="""This is a multi-line instruction.
It spans multiple lines.
And has multiple paragraphs.""",
)
''')

    tree = parse_agent_directory(agent_dir)
    assert "multi-line instruction" in tree.agent.instruction
    assert "multiple lines" in tree.agent.instruction
    assert "multiple paragraphs" in tree.agent.instruction


def test_skip_invalid_subagent(tmp_path: Path):
    """Invalid sub-agent directories should be skipped gracefully."""
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    (agent_dir / "__init__.py").write_text("")
    (agent_dir / "agent.py").write_text("""
from google.adk.agents import Agent

root_agent = Agent(name="test", instruction="test", sub_agents=[])
""")

    sub_agents_dir = agent_dir / "sub_agents"
    sub_agents_dir.mkdir()

    # Create invalid sub-agent (no agent.py)
    invalid_sub = sub_agents_dir / "invalid"
    invalid_sub.mkdir()
    (invalid_sub / "__init__.py").write_text("")

    # Should parse successfully, skipping invalid sub-agent
    tree = parse_agent_directory(agent_dir)
    assert tree.agent.name == "test"
    assert len(tree.sub_agents) == 0


def test_agent_with_callbacks(tmp_path: Path):
    """Agent with before/after callbacks should parse callback names."""
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    (agent_dir / "__init__.py").write_text("")
    (agent_dir / "agent.py").write_text("""
from google.adk.agents import Agent

def safety_check():
    pass

def log_response():
    pass

root_agent = Agent(
    name="test_agent",
    instruction="test",
    before_model_callback=safety_check,
    after_model_callback=log_response,
)
""")

    tree = parse_agent_directory(agent_dir)
    assert tree.agent.before_model_callback == "safety_check"
    assert tree.agent.after_model_callback == "log_response"


def test_tool_signature_with_defaults(tmp_path: Path):
    """Tool with default parameter values should capture signature."""
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    (agent_dir / "__init__.py").write_text("")
    (agent_dir / "agent.py").write_text("""
from google.adk.agents import Agent

root_agent = Agent(name="test", instruction="test")
""")
    (agent_dir / "tools.py").write_text("""
from google.adk.tools import tool

@tool
def search(query: str, limit: int = 10, offset: int = 0):
    '''Search with pagination.'''
    return []
""")

    tree = parse_agent_directory(agent_dir)
    assert len(tree.tools) == 1
    tool = tree.tools[0]
    assert tool.name == "search"
    # Signature should include defaults (allow spaces around =)
    assert "limit" in tool.signature and "10" in tool.signature
    assert "offset" in tool.signature and "0" in tool.signature


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------

def test_full_parse_sample_agent(sample_agent_path: Path):
    """Complete integration test parsing full sample agent."""
    tree = parse_agent_directory(sample_agent_path)

    # Root agent
    assert tree.agent.name == "support_agent"
    assert tree.agent.model == "gemini-2.0-flash"
    assert "customer support" in tree.agent.instruction.lower()
    assert len(tree.tools) == 3
    assert len(tree.sub_agents) == 1

    # Config
    assert tree.config["temperature"] == 0.3
    assert tree.agent.generate_config["max_output_tokens"] == 1024

    # Tools
    tool_names = {t.name for t in tree.tools}
    assert tool_names == {"lookup_order", "search_knowledge_base", "create_ticket"}

    # All tools have descriptions
    for tool in tree.tools:
        assert tool.description, f"Tool {tool.name} missing description"
        assert tool.function_body, f"Tool {tool.name} missing function body"
        assert tool.signature, f"Tool {tool.name} missing signature"

    # Sub-agent
    billing = tree.sub_agents[0]
    assert billing.agent.name == "billing_agent"
    assert len(billing.tools) == 2
    assert billing.agent.generate_config["temperature"] == 0.2

    # Sub-agent tools
    sub_tool_names = {t.name for t in billing.tools}
    assert sub_tool_names == {"get_billing_history", "process_refund"}

    # Verify source paths
    assert tree.source_path.name == "sample_adk_agent"
    assert billing.source_path.name == "billing"

"""Tests for MCP server — tool schemas, request handling, tool execution."""
from __future__ import annotations
import json
import os
import subprocess
import sys
from pathlib import Path
from mcp_server.server import handle_request
from mcp_server.tools import TOOL_REGISTRY
from mcp_server.tools import sync_adk_source
from mcp_server.types import MCPToolDef, MCPToolParam
from click.testing import CliRunner

from runner import cli


def test_module_entrypoint_supports_stdio_requests(tmp_path) -> None:
    """`python -m mcp_server` should start a stdio MCP server that accepts JSON-RPC."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    proc = subprocess.Popen(
        [sys.executable, "-m", "mcp_server"],
        cwd=tmp_path,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert proc.stdin is not None
        assert proc.stdout is not None

        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}) + "\n")
        proc.stdin.flush()

        response_line = proc.stdout.readline().strip()
        response = json.loads(response_line)
        assert response["id"] == 1
        assert response["result"]["serverInfo"]["name"] == "autoagent"
    finally:
        proc.kill()
        proc.wait()


def test_cli_port_flag_starts_http_transport(monkeypatch) -> None:
    """`autoagent mcp-server --port` should start the HTTP transport instead of rejecting it."""
    called: dict[str, object] = {}

    def fake_run_http(*, host: str, port: int) -> None:
        called["host"] = host
        called["port"] = port

    monkeypatch.setattr("mcp_server.server.run_http", fake_run_http)

    runner = CliRunner()
    result = runner.invoke(cli, ["mcp-server", "--host", "127.0.0.1", "--port", "8765"])

    assert result.exit_code == 0
    assert called == {"host": "127.0.0.1", "port": 8765}


def test_resource_read_rejects_config_path_traversal(tmp_path, monkeypatch) -> None:
    """Config resources should not be able to escape the configured configs directory."""
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    (configs_dir / "demo.yaml").write_text("name: demo\n", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("top-secret\n", encoding="utf-8")

    monkeypatch.setattr("mcp_server.resources.ResourceProvider.CONFIGS_DIR", str(configs_dir))

    response = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 99,
            "method": "resources/read",
            "params": {"uri": "autoagent://configs/../secret.txt"},
        }
    )

    assert response["error"]["code"] == -32603
    assert "escapes" in response["error"]["message"].lower()


def test_sync_adk_source_copies_nested_directories(tmp_path) -> None:
    """Syncing ADK source should recursively copy nested files, not fail on directories."""
    source_dir = tmp_path / "src"
    target_dir = tmp_path / "dst"
    source_dir.mkdir()
    target_dir.mkdir()
    (source_dir / "root.txt").write_text("root\n", encoding="utf-8")
    nested_dir = source_dir / "nested"
    nested_dir.mkdir()
    (nested_dir / "child.txt").write_text("child\n", encoding="utf-8")

    result = sync_adk_source(source_dir=str(source_dir), target_dir=str(target_dir), dry_run=False)

    assert result["status"] == "ok"
    assert result["errors"] == []
    assert (target_dir / "root.txt").read_text(encoding="utf-8") == "root\n"
    assert (target_dir / "nested" / "child.txt").read_text(encoding="utf-8") == "child\n"


class TestMCPTypes:
    def test_tool_def_to_schema(self):
        tool = MCPToolDef(
            name="test_tool",
            description="A test tool",
            parameters=[
                MCPToolParam(name="arg1", description="First arg", type="string", required=True),
                MCPToolParam(name="arg2", description="Second arg", type="integer"),
            ],
        )
        schema = tool.to_schema()
        assert schema["name"] == "test_tool"
        assert schema["description"] == "A test tool"
        assert "arg1" in schema["inputSchema"]["properties"]
        assert schema["inputSchema"]["required"] == ["arg1"]

    def test_tool_def_no_params(self):
        tool = MCPToolDef(name="simple", description="Simple tool")
        schema = tool.to_schema()
        assert schema["inputSchema"]["properties"] == {}


class TestMCPServer:
    def test_initialize(self):
        resp = handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        assert resp["id"] == 1
        assert resp["result"]["serverInfo"]["name"] == "autoagent"

    def test_tools_list(self):
        resp = handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        assert resp["id"] == 2
        tools = resp["result"]["tools"]
        assert len(tools) >= 12  # 12 original + P0-10 build surface tools
        names = {t["name"] for t in tools}
        assert "autoagent_status" in names
        assert "autoagent_edit" in names
        assert "autoagent_diagnose" in names

    def test_tool_call_unknown(self):
        resp = handle_request({
            "jsonrpc": "2.0", "id": 3,
            "method": "tools/call",
            "params": {"name": "nonexistent", "arguments": {}},
        })
        assert "error" in resp

    def test_tool_call_replay(self):
        resp = handle_request({
            "jsonrpc": "2.0", "id": 4,
            "method": "tools/call",
            "params": {"name": "autoagent_replay", "arguments": {"limit": 5}},
        })
        assert resp["id"] == 4
        assert "result" in resp
        content = resp["result"]["content"]
        assert len(content) == 1
        assert content[0]["type"] == "text"

    def test_tool_call_diagnose(self):
        resp = handle_request({
            "jsonrpc": "2.0", "id": 5,
            "method": "tools/call",
            "params": {"name": "autoagent_diagnose", "arguments": {}},
        })
        assert "result" in resp
        text = resp["result"]["content"][0]["text"]
        data = json.loads(text)
        assert "session_id" in data
        assert "clusters" in data

    def test_unknown_method(self):
        resp = handle_request({"jsonrpc": "2.0", "id": 6, "method": "bogus/method", "params": {}})
        assert "error" in resp

    def test_notification_no_response(self):
        resp = handle_request({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        assert resp is None


class TestMCPToolRegistry:
    def test_registry_has_tools(self):
        assert len(TOOL_REGISTRY) >= 12  # 12 original + P0-10 build surface tools

    def test_all_tools_have_functions(self):
        for name, (fn, defn) in TOOL_REGISTRY.items():
            assert callable(fn), f"{name} function is not callable"
            assert isinstance(defn, MCPToolDef), f"{name} definition is not MCPToolDef"

    def test_tool_names_match(self):
        for name, (_, defn) in TOOL_REGISTRY.items():
            assert name == defn.name

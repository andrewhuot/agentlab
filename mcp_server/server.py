"""MCP Server — JSON-RPC 2.0 over stdio.

Implements the Model Context Protocol for AI coding tool integration.
Start with: autoagent mcp-server
"""
from __future__ import annotations

import json
import sys
from typing import Any

from mcp_server.tools import TOOL_REGISTRY


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    """Handle a single JSON-RPC 2.0 request."""
    method = request.get("method", "")
    params = request.get("params", {})
    request_id = request.get("id")

    if method == "initialize":
        return _success(request_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "autoagent", "version": "1.0.0"},
        })

    if method == "tools/list":
        tools = [defn.to_schema() for _, defn in TOOL_REGISTRY.values()]
        return _success(request_id, {"tools": tools})

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        if tool_name not in TOOL_REGISTRY:
            return _error(request_id, -32601, f"Tool not found: {tool_name}")
        fn, _ = TOOL_REGISTRY[tool_name]
        try:
            result = fn(**arguments)
            content = json.dumps(result, default=str)
            return _success(request_id, {
                "content": [{"type": "text", "text": content}],
            })
        except Exception as exc:
            return _success(request_id, {
                "content": [{"type": "text", "text": f"Error: {exc}"}],
                "isError": True,
            })

    if method == "notifications/initialized":
        return None  # Notification, no response

    return _error(request_id, -32601, f"Method not found: {method}")


def _success(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def run_stdio() -> None:
    """Run the MCP server in stdio mode (read JSON-RPC from stdin, write to stdout)."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            response = _error(None, -32700, "Parse error")
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            continue

        response = handle_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

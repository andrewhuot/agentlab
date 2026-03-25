# MCP Integration

AutoAgent implements the Model Context Protocol (MCP) for integration with AI coding assistants like Claude Code, Cursor, and other tools that support MCP.

## Overview

The MCP server exposes AutoAgent's optimization tools and agent management capabilities to AI coding assistants. This enables natural language interactions with your agent optimization workflow directly from your editor.

## Current Status

**Implemented:**
- Stdio transport (for Claude Code, Codex, etc.)
- Tool registry with JSON-RPC 2.0
- Core tools: status, eval, optimize, config management

**Limitations:**
- HTTP/SSE transport not yet implemented
- Stdio mode only

## Quick Start

### 1. Start the MCP Server

```bash
autoagent mcp-server
```

By default, the server runs in stdio mode (reads JSON-RPC from stdin, writes to stdout).

### 2. Configure Your AI Coding Assistant

#### Claude Code

Add to your MCP configuration file (`~/.claude/mcp.json` or project-level `.claude/mcp.json`):

```json
{
  "mcpServers": {
    "autoagent": {
      "command": "autoagent",
      "args": ["mcp-server"]
    }
  }
}
```

#### Cursor

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "autoagent": {
      "command": "autoagent",
      "args": ["mcp-server"]
    }
  }
}
```

#### Generic MCP Client

Any MCP-compatible client can connect via stdio:

```bash
# Launch the server
autoagent mcp-server

# Send JSON-RPC 2.0 messages via stdin
{"jsonrpc": "2.0", "method": "initialize", "id": 1}
```

## Available Tools

The MCP server exposes these tools:

### `status`

Get current system status (active config, loop state, recent scores).

```json
{
  "name": "status",
  "arguments": {}
}
```

### `eval_run`

Start an evaluation run.

```json
{
  "name": "eval_run",
  "arguments": {
    "config_path": "configs/v003.yaml",
    "category": "happy_path"
  }
}
```

### `optimize`

Run optimization cycles.

```json
{
  "name": "optimize",
  "arguments": {
    "cycles": 3
  }
}
```

### `config_list`

List all config versions.

```json
{
  "name": "config_list",
  "arguments": {}
}
```

### `config_show`

Show a specific config version.

```json
{
  "name": "config_show",
  "arguments": {
    "version": 42
  }
}
```

### `config_diff`

Diff two config versions.

```json
{
  "name": "config_diff",
  "arguments": {
    "v1": 41,
    "v2": 42
  }
}
```

### `deploy`

Deploy a config version.

```json
{
  "name": "deploy",
  "arguments": {
    "config_version": 42,
    "strategy": "canary"
  }
}
```

### `conversations_list`

List recent conversations.

```json
{
  "name": "conversations_list",
  "arguments": {
    "limit": 50,
    "outcome": "fail"
  }
}
```

### `trace_grade`

Grade a trace with the 7-grader suite.

```json
{
  "name": "trace_grade",
  "arguments": {
    "trace_id": "trace_abc123"
  }
}
```

### `memory_show`

Show project memory (AUTOAGENT.md).

```json
{
  "name": "memory_show",
  "arguments": {}
}
```

## Protocol Details

### Transport

**Stdio (implemented):** JSON-RPC 2.0 messages over stdin/stdout. Each message is a single line (newline-delimited JSON).

**HTTP/SSE (planned):** RESTful JSON-RPC with Server-Sent Events for notifications.

### Message Format

All messages follow JSON-RPC 2.0:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "status",
    "arguments": {}
  },
  "id": 1
}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"active_config\": 42, \"loop_running\": false}"
      }
    ]
  }
}
```

### Error Handling

Errors follow JSON-RPC 2.0 error format:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Tool not found: unknown_tool"
  }
}
```

## Example Workflows

### Check Agent Health

Ask your AI assistant:
> "Check the agent's current health status"

The assistant will call the `status` tool and interpret the results.

### Run Optimization

Ask your AI assistant:
> "Run 3 optimization cycles and show me what improved"

The assistant will:
1. Call `optimize` with `cycles: 3`
2. Poll for completion
3. Call `config_diff` to show changes
4. Summarize the improvements

### Debug Failures

Ask your AI assistant:
> "Show me the last 10 failed conversations and diagnose the issues"

The assistant will:
1. Call `conversations_list` with `outcome: "fail"` and `limit: 10`
2. Analyze failure patterns
3. Suggest fixes or call `optimize` to auto-fix

## Troubleshooting

### Server Not Responding

Check that the server is running:

```bash
ps aux | grep "autoagent mcp-server"
```

Test the server manually:

```bash
echo '{"jsonrpc": "2.0", "method": "initialize", "id": 1}' | autoagent mcp-server
```

### Tool Not Found

Verify the tool name matches the registry. List available tools:

```json
{"jsonrpc": "2.0", "method": "tools/list", "id": 1}
```

### Permission Denied

Ensure the `autoagent` command is in your PATH and executable:

```bash
which autoagent
autoagent --version
```

## Future Enhancements

Planned for future releases:

- HTTP/SSE transport for web-based MCP clients
- Real-time notifications (eval complete, optimization progress)
- Streaming optimization output
- Batch tool execution
- Tool composition (chain multiple tools in one call)

## Security Considerations

The MCP server runs with the same permissions as the `autoagent` CLI. It can:

- Read and write agent configs
- Execute optimization cycles
- Deploy configs
- Access conversation data

**Recommendations:**

- Only expose the MCP server to trusted AI assistants
- Use stdio mode (not HTTP) in shared environments
- Review and approve all optimization changes before deployment
- Set up appropriate file permissions on config directories

## References

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [AutoAgent CLI Reference](cli-reference.md)
- [AutoAgent API Reference](api-reference.md)

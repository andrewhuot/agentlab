# MCP Integration

AgentLab includes an MCP server for agentic coding tools such as Claude Code, Codex, Cursor, Windsurf, and other MCP-compatible clients.

## Current status

- `stdio` transport: supported
- Streamable HTTP transport: supported
- Tools: 22
- Prompts: 5
- Resources: configs, traces, evals, skills, and dataset stats

## Start the server

Installed CLI:

```bash
agentlab mcp-server
```

Repo-local fallback:

```bash
python3 -m mcp_server
```

HTTP mode:

```bash
python3 -m mcp_server --host 127.0.0.1 --port 8765
```

## Recommended guide

Use the full setup guide for:

- Claude Code
- Codex
- Google Jules / Antigravity / Project Mariner status
- Cursor
- Windsurf
- Generic MCP clients
- the full 22-tool catalog
- troubleshooting and advanced usage

See [guides/agentic-coding-tools.md](guides/agentic-coding-tools.md).

## Quick smoke tests

Stdio:

```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python3 -m mcp_server
```

HTTP:

```bash
curl -s http://127.0.0.1:8765/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

If `tools/list` returns the live tool registry, the MCP server is working and any remaining issue is in client-side configuration.

# Connecting AgentLab to Agentic Coding Tools

AgentLab ships an MCP server so coding agents can inspect agent health, run evals, inspect traces, scaffold agents, generate eval packs, explain diffs, and prepare change sets without leaving the editor.

This is the main power-user integration for Claude Code, Codex, Cursor, Windsurf, and any other MCP client that can launch a local stdio server or connect to a streamable HTTP endpoint.

Two things changed during the integration audit that matter for setup:

- AgentLab now supports both `stdio` and streamable HTTP transport.
- The live MCP registry exposes **22 tools**, not the older 10-tool surface described in stale docs.

This guide reflects the verified server behavior in the repository as of 2026-03-29.

## What the MCP integration enables

Connecting your coding agent to AgentLab gives it direct access to:

- Current agent health and failure summaries
- Failure clustering and diagnosis sessions
- Eval and benchmark execution
- Config diffing and natural-language config edits
- Trace inspection and failure sample lookup
- Skill discovery and application
- Agent scaffolding, eval generation, and ADK source sync helpers
- Pull request preparation from inside the coding workflow

In practice, that means you can stay inside your coding tool and ask for things like:

- "Check current agent health and tell me the biggest risk."
- "Run the eval suite against this config before I commit."
- "Show me the last few failures related to tone or safety."
- "Generate eval cases for the new routing logic I just added."

## Before you start

### Prerequisites

- Python 3.11+
- A checked-out AgentLab repo
- Recommended: install the repo in editable mode so the `agentlab` command exists

```bash
pip install -e ".[dev]"
```

If you do not want to install the package, the repo-local fallback now works too:

```bash
python3 -m mcp_server
```

### Launch modes

Use one of these startup commands depending on the client:

```bash
# Recommended after pip install -e ".[dev]"
agentlab mcp-server

# Repo-local fallback from the AgentLab repo root
python3 -m mcp_server

# Streamable HTTP mode for clients that prefer URL-based MCP
python3 -m mcp_server --host 127.0.0.1 --port 8765
```

### Quick verification

Verify stdio mode directly:

```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python3 -m mcp_server
```

Verify HTTP mode directly:

```bash
curl -s http://127.0.0.1:8765/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
```

If the server is healthy, both commands return a JSON-RPC response with `serverInfo.name = "agentlab"`.

## Shared AgentLab MCP surface

Once any client is connected, it sees the same AgentLab MCP surface:

- 22 tools
- 5 prompts
- Resource endpoints for configs, traces, evals, skills, and dataset stats

### Tool catalog

Older docs in this repo said "10 tools." That is no longer accurate. The live registry exposes the following 22 tools:

| Tool | What it does | Example ask |
|------|--------------|-------------|
| `agentlab_status` | Returns current health, scores, and failure summary. | "Run `agentlab_status` and summarize the biggest current risk." |
| `agentlab_explain` | Produces a plain-English health summary. | "Use `agentlab_explain` and tell me whether the agent is stable enough to ship." |
| `agentlab_diagnose` | Starts a diagnosis session with clustered failure analysis. | "Run `agentlab_diagnose` and show the top failure clusters." |
| `agentlab_get_failures` | Returns recent failure samples, optionally filtered by failure family. | "Call `agentlab_get_failures` for billing-related failures." |
| `agentlab_suggest_fix` | Suggests a config fix from a natural-language description. | "Use `agentlab_suggest_fix` to make the assistant more concise without weakening safety." |
| `agentlab_edit` | Applies a natural-language config edit and returns the proposed diff/result. | "Run `agentlab_edit` to tighten refund-policy routing." |
| `agentlab_eval` | Runs the eval suite and returns scores. | "Run `agentlab_eval` on `configs/v012.yaml` before I merge this." |
| `agentlab_eval_compare` | Runs evals on two configs and returns the winner. | "Compare the active config to `configs/candidate.yaml` with `agentlab_eval_compare`." |
| `agentlab_skill_gaps` | Identifies capability gaps from failures. | "Call `agentlab_skill_gaps` and tell me what skills we are missing." |
| `agentlab_skill_recommend` | Recommends skills from the registry. | "Use `agentlab_skill_recommend` for the current failure pattern." |
| `agentlab_replay` | Returns optimization history. | "Show me the last five optimization attempts with `agentlab_replay`." |
| `agentlab_diff` | Diffs two config versions. | "Explain what changed between versions 3 and 5 using `agentlab_diff`." |
| `scaffold_agent` | Creates a new ADK agent scaffold. | "Use `scaffold_agent` to create a specialist `billing_agent`." |
| `generate_evals` | Generates eval cases for a capability. | "Generate evals for escalation routing with `generate_evals`." |
| `run_sandbox` | Runs a sandbox task against an agent. | "Try `run_sandbox` with a refund request against the new config." |
| `inspect_trace` | Reads a specific trace or recent failures. | "Inspect the most recent failed trace with `inspect_trace`." |
| `sync_adk_source` | Syncs generated changes back to an ADK source tree. | "Sync the generated agent files back into the ADK repo with `sync_adk_source`." |
| `open_pr` | Creates a branch, stages changes, commits, pushes, and attempts PR creation. | "After the eval passes, use `open_pr` to prepare a PR." |
| `explain_diff` | Summarizes a unified diff in plain English. | "Use `explain_diff` on this patch so I can sanity-check the behavior change." |
| `list_skills` | Lists available skills from the registry. | "List the skills available for guardrails and evaluation." |
| `apply_skill` | Adds a skill to an agent config. | "Apply the `safety-review` skill to the customer-support agent." |
| `run_benchmark` | Runs a benchmark and returns quality/safety/latency metrics. | "Run `run_benchmark` on the new routing agent." |

### Prompt catalog

AgentLab also exposes five MCP prompts:

- `diagnose_agent`
- `fix_failure_pattern`
- `generate_evals`
- `explain_diff`
- `optimize_instruction`

Use these when your client supports MCP prompts directly and you want a richer ready-to-run prompt instead of a tool call.

### Resource catalog

The MCP server exposes read-only resources for:

- `agentlab://configs/...`
- `agentlab://traces/...`
- `agentlab://evals/...`
- `agentlab://skills/...`
- `agentlab://datasets/...`

Config resources are intentionally confined to the configured `configs/` directory. During the audit, path traversal was possible through `resources/read`; that bug is now fixed.

## Claude Code

### Prerequisites

- Claude Code installed
- AgentLab repo checked out locally
- Either:
  - `agentlab` available on `PATH` after `pip install -e ".[dev]"`, or
  - repo-local fallback with `python3 -m mcp_server`

### Recommended setup

The current Claude Code docs prefer `claude mcp add` and `.mcp.json` / `~/.claude.json`.

Recommended command:

```bash
claude mcp add --transport stdio agentlab -- agentlab mcp-server
```

Repo-local fallback:

```bash
claude mcp add --transport stdio agentlab -- python3 -m mcp_server
```

### Raw config example

Project-scoped `.mcp.json`:

```json
{
  "mcpServers": {
    "agentlab": {
      "command": "agentlab",
      "args": ["mcp-server"]
    }
  }
}
```

Repo-local fallback:

```json
{
  "mcpServers": {
    "agentlab": {
      "command": "python3",
      "args": ["-m", "mcp_server"]
    }
  }
}
```

Current Claude Code docs store project-scoped MCP config in `.mcp.json` and user/local scope in `~/.claude.json`. If you have older notes referencing `~/.claude/mcp.json`, treat that as legacy guidance.

### Verification

```bash
claude mcp list
```

Inside Claude Code, run:

```text
/mcp
```

Then ask:

```text
Run agentlab_status and summarize the top two failure buckets.
```

### Common workflows

- Check agent health from your editor:
  - "Run `agentlab_status` and `agentlab_explain`, then tell me if the active config is safe to keep."
- Run an eval while coding:
  - "Use `agentlab_eval` on `configs/v013.yaml` and compare it to the active config."
- Deploy a config change:
  - "Use `agentlab_edit`, then `agentlab_eval`, then `open_pr`. If the PR is ready, tell me the exact `agentlab deploy` command to run."
- View traces for debugging:
  - "Use `inspect_trace` and `agentlab_get_failures` for the latest refund-related failures."
- Trigger optimization:
  - "Start with `agentlab_diagnose`, then use `agentlab_suggest_fix`, `agentlab_edit`, and `run_benchmark` to propose the next optimization."

## Codex (OpenAI)

### Prerequisites

- Codex CLI or Codex IDE extension
- AgentLab available either as:
  - installed CLI: `agentlab mcp-server`
  - repo-local module: `python3 -m mcp_server`

### Recommended setup

Codex has first-class MCP management in the CLI:

```bash
codex mcp add agentlab -- agentlab mcp-server
```

Repo-local fallback:

```bash
codex mcp add agentlab -- python3 -m mcp_server
```

If you prefer HTTP transport:

```bash
python3 -m mcp_server --host 127.0.0.1 --port 8765
codex mcp add agentlab-http --url http://127.0.0.1:8765/mcp
```

### Raw config example

`~/.codex/config.toml`:

```toml
[mcp_servers.agentlab]
command = "agentlab"
args = ["mcp-server"]
```

Repo-local fallback:

```toml
[mcp_servers.agentlab]
command = "python3"
args = ["-m", "mcp_server"]
```

HTTP transport:

```toml
[mcp_servers.agentlab_http]
url = "http://127.0.0.1:8765/mcp"
```

### Verification

```bash
codex mcp list
codex mcp get agentlab
```

Then ask Codex:

```text
Use agentlab_status to check the current health of this agent project.
```

### Common workflows

- Check agent health from your editor:
  - "Use `agentlab_status` and `agentlab_explain`, then summarize the risk in one paragraph."
- Run an eval while coding:
  - "Use `agentlab_eval_compare` on the current candidate config and the active config."
- Deploy a config change:
  - "Use `agentlab_edit`, run `agentlab_eval`, and if the result is better, prepare a PR with `open_pr`."
- View traces for debugging:
  - "Inspect the latest failed trace and group the failures with `agentlab_diagnose`."
- Trigger optimization:
  - "Run `agentlab_diagnose`, then propose a fix with `agentlab_suggest_fix`, benchmark it, and tell me whether to promote it."

## Google Antigravity / Project Mariner / Jules

### Current reality

This is the one client in this guide where the limitation matters more than the config syntax.

As of **February 2, 2026**, Google Jules added MCP support for a **vetted list of services** through the Jules Settings UI. Google does not currently document raw JSON/YAML configuration for arbitrary local MCP servers, and there is no public documented flow for attaching a local unpublished AgentLab MCP server directly to Jules.

### What this means for AgentLab

- There is **no current supported raw config file** to paste for AgentLab.
- There is **no documented local stdio integration path** equivalent to Claude Code, Codex, Cursor, or Windsurf.
- If Google later opens custom MCP endpoints, AgentLab should work best via the streamable HTTP mode described in this guide.

### Best available setup path today

1. Open Jules.
2. Go to `Settings` -> `MCP`.
3. Check whether your org or Google has made a custom AgentLab-compatible endpoint available.
4. If not, use Claude Code, Codex, Cursor, or Windsurf for now.

### Future-ready HTTP shape

If/when Jules supports custom MCP endpoints, run AgentLab like this:

```bash
python3 -m mcp_server --host 127.0.0.1 --port 8765
```

Then publish that endpoint behind HTTPS and expose:

```text
https://your-hostname.example.com/mcp
```

### Verification

Because Jules does not currently expose arbitrary raw MCP config for local servers, there is no verified direct AgentLab verification command to document here. The practical verification today is to confirm whether `Settings -> MCP` offers custom endpoint registration in your tenant. If it does not, treat Jules support for AgentLab as unavailable today.

### Common workflows

If Google opens custom MCP endpoints, the same shared AgentLab tool catalog in this guide is what Jules would consume. Until then, use another MCP-capable coding client for:

- health checks
- evals
- trace inspection
- optimization loops
- PR preparation

## Cursor

### Prerequisites

- Cursor with MCP support enabled
- AgentLab available via `agentlab mcp-server` or `python3 -m mcp_server`

### Raw config example

Project-local `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "agentlab": {
      "command": "agentlab",
      "args": ["mcp-server"]
    }
  }
}
```

Repo-local fallback:

```json
{
  "mcpServers": {
    "agentlab": {
      "command": "python3",
      "args": ["-m", "mcp_server"]
    }
  }
}
```

HTTP alternative:

```json
{
  "mcpServers": {
    "agentlab": {
      "url": "http://127.0.0.1:8765/mcp"
    }
  }
}
```

If you prefer the UI, Cursor also exposes MCP management in settings. The raw JSON above is easier to review and commit for project-local setups.

### Verification

- Restart Cursor after updating MCP config.
- Open Agent / Composer and confirm `agentlab` appears in the available tools.
- If you use the Cursor CLI, the docs expose MCP management under `cursor-agent mcp`.

Then ask:

```text
Run agentlab_status and tell me whether the latest eval score is improving.
```

### Common workflows

- Check agent health from your editor:
  - "Use `agentlab_status` and summarize the current failure buckets."
- Run an eval while coding:
  - "Run `agentlab_eval` against the candidate config I just edited."
- Deploy a config change:
  - "Prepare the change with `agentlab_edit`, verify it with `agentlab_eval`, then use `open_pr`."
- View traces for debugging:
  - "Use `inspect_trace` and `agentlab_get_failures` for the latest escalation bug."
- Trigger optimization:
  - "Diagnose the latest failure pattern and propose the next configuration change."

## Windsurf

### Prerequisites

- Windsurf / Cascade with MCP enabled
- AgentLab available via `agentlab mcp-server` or `python3 -m mcp_server`

### Raw config example

Windsurf reads `~/.codeium/windsurf/mcp_config.json`.

Stdio:

```json
{
  "mcpServers": {
    "agentlab": {
      "command": "agentlab",
      "args": ["mcp-server"]
    }
  }
}
```

Repo-local fallback:

```json
{
  "mcpServers": {
    "agentlab": {
      "command": "python3",
      "args": ["-m", "mcp_server"]
    }
  }
}
```

HTTP transport:

```json
{
  "mcpServers": {
    "agentlab": {
      "serverUrl": "http://127.0.0.1:8765/mcp"
    }
  }
}
```

### Verification

1. Open the Cascade panel.
2. Open the `MCPs` picker.
3. Confirm `agentlab` is installed and enabled.
4. Ask Cascade:

```text
Use agentlab_status and summarize whether the active agent is healthy.
```

Windsurf currently enforces a 100-tool total cap in Cascade. AgentLab contributes 22 tools by itself, so if you connect many other MCP servers you may need to disable some tools in the Windsurf MCP UI.

### Common workflows

- Check agent health from your editor:
  - "Run `agentlab_status` and `agentlab_explain`, then tell me the top operational risk."
- Run an eval while coding:
  - "Run `agentlab_eval_compare` on the active config and the candidate config I am editing."
- Deploy a config change:
  - "Use `agentlab_edit`, then `agentlab_eval`, then `open_pr`. Tell me the deploy command after the PR is ready."
- View traces for debugging:
  - "Use `inspect_trace` to show the latest failed trace."
- Trigger optimization:
  - "Run diagnosis, suggest the next fix, and benchmark the result."

## Any MCP-compatible tool

### Stdio configuration

If your client accepts a generic command-plus-args MCP definition, use:

```json
{
  "mcpServers": {
    "agentlab": {
      "command": "agentlab",
      "args": ["mcp-server"]
    }
  }
}
```

Fallback when you are running directly from the repo:

```json
{
  "mcpServers": {
    "agentlab": {
      "command": "python3",
      "args": ["-m", "mcp_server"]
    }
  }
}
```

### HTTP configuration

If the client prefers streamable HTTP, start AgentLab locally:

```bash
python3 -m mcp_server --host 127.0.0.1 --port 8765
```

Then use:

```json
{
  "mcpServers": {
    "agentlab": {
      "url": "http://127.0.0.1:8765/mcp"
    }
  }
}
```

Some clients use `serverUrl` instead of `url`. Both patterns are common across MCP clients.

### YAML example

If your client stores server definitions as YAML:

```yaml
mcpServers:
  agentlab:
    url: http://127.0.0.1:8765/mcp
```

### Verification

Every MCP client should be able to handle these two smoke tests:

1. `initialize`
2. `tools/list`

If the client has a raw request console, use:

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
```

Then:

```json
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
```

If `tools/list` does not return the 22-tool registry described above, the problem is in client launch/config, not in the AgentLab MCP server.

## Troubleshooting

### `python3 -m mcp_server` fails

Check one of these first:

- You are not in the AgentLab repo root and the package is not installed.
- Your client launches the command from another working directory.

Fix:

```bash
pip install -e ".[dev]"
```

Then switch your config to:

```json
{
  "mcpServers": {
    "agentlab": {
      "command": "agentlab",
      "args": ["mcp-server"]
    }
  }
}
```

### `agentlab: command not found`

You have not installed the package in the current environment.

Use either:

```bash
pip install -e ".[dev]"
```

or the repo-local fallback:

```json
{
  "mcpServers": {
    "agentlab": {
      "command": "python3",
      "args": ["-m", "mcp_server"]
    }
  }
}
```

### MCP server not responding

Check these in order:

1. Run `python3 -m mcp_server --help` and confirm the module entrypoint works.
2. Run the raw `initialize` smoke test from the shell.
3. If you are using HTTP mode, hit `http://127.0.0.1:8765/mcp` with `curl`.
4. Make sure the MCP client is not launching from the wrong working directory.
5. Make sure the server process is not writing non-JSON output to stdout.

### Port conflict

If HTTP mode fails to bind:

```bash
lsof -iTCP:8765 -sTCP:LISTEN
```

Then pick a different port:

```bash
python3 -m mcp_server --host 127.0.0.1 --port 8876
```

### Auth issues

Local `stdio` transport does not require OAuth or bearer tokens.

If you front AgentLab with an HTTPS proxy and use HTTP mode:

- Claude Code supports `--header` and bearer-token env vars for HTTP servers.
- Codex supports `--url` plus `--bearer-token-env-var`.
- Windsurf supports `headers` and `serverUrl`.

### `resources/read` returns a config path error

That is expected if you try to escape the configured `configs/` directory.

Use resource URIs that stay under:

```text
agentlab://configs/<file>
```

### Tool is missing in Windsurf

Windsurf caps Cascade at 100 enabled MCP tools total. Disable unused tools from other MCP servers or toggle down the AgentLab tools you do not need.

### Claude Code config path confusion

Current Claude Code docs use:

- `.mcp.json` for project scope
- `~/.claude.json` for user/local scope

If you see `~/.claude/mcp.json` in older notes, update to the current file layout above.

### Jules cannot add AgentLab

That is the current product limitation, not an AgentLab server bug. Use another client until Google exposes custom endpoint registration for your tenant.

## Advanced usage

### Run the MCP server in the background

For HTTP mode:

```bash
nohup python3 -m mcp_server --host 127.0.0.1 --port 8765 >/tmp/agentlab-mcp.log 2>&1 &
```

Then point URL-based clients to:

```text
http://127.0.0.1:8765/mcp
```

For a managed local service, wrap the same command in `systemd`, `launchd`, or your preferred process supervisor.

### Docker

This repo already includes a `Dockerfile`, so you can expose AgentLab over HTTP from a container:

```bash
docker build -t agentlab-mcp .
docker run --rm -p 8765:8765 agentlab-mcp \
  python -m mcp_server --host 0.0.0.0 --port 8765
```

Then configure your MCP client to use:

```text
http://127.0.0.1:8765/mcp
```

If the client also needs to read local project files, mount the repo into the container and set the working directory accordingly.

### CI/CD integration patterns

Three patterns work well:

1. MCP smoke test in CI

```bash
python3 -m mcp_server --help
pytest -q tests/test_mcp_server.py
```

2. HTTP probe in integration jobs

```bash
python3 -m mcp_server --host 127.0.0.1 --port 8765 &
SERVER_PID=$!
trap 'kill $SERVER_PID' EXIT

curl -s http://127.0.0.1:8765/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

3. Editor bootstrap for devcontainers or remote workspaces

- install AgentLab in the image
- expose `agentlab mcp-server`
- check in the client-specific MCP config alongside the repo

## References

- Claude Code MCP docs: <https://code.claude.com/docs/en/mcp>
- Codex MCP / Docs MCP docs: <https://developers.openai.com/learn/docs-mcp>
- Cursor MCP docs: <https://docs.cursor.com/>
- Windsurf MCP docs: <https://docs.windsurf.com/windsurf/cascade/mcp>
- Jules changelog: <https://developers.googleblog.com/en/jules-mcp-support-multimodal-pdf-export-and-bug-fixes/>

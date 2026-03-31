> **TL;DR** — Want the shortest path? Start with the [Quick Start](QUICKSTART_GUIDE.md).

# AutoAgent Detailed Guide

This guide walks the current first-run CLI flow from install to review and deployment. It is written for the product as it exists today:

- new workspaces default to XML root instructions
- AutoAgent auto-detects mock vs live execution
- the first-run loop can end either in a new proposal or in `no optimization needed`
- the browser UI and CLI share the same workspace state

## 1. Install AutoAgent

From the repository root:

```bash
git clone https://github.com/andrewhuot/autoagent-vnextcc.git
cd autoagent-vnextcc
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Requirements:

- Python 3.11+
- Node.js 20+ for the web console and frontend tooling

## 2. Explore the starter templates

```bash
autoagent template list
```

Current bundled starter templates:

```text
Starter templates
=================
- customer-support: Handle order questions, support troubleshooting, and product recommendations.
- it-helpdesk: Triage employee IT support requests, device issues, and access problems.
- sales-qualification: Qualify inbound leads, identify urgency, and route to the right sales motion.
- healthcare-intake: Collect patient intake information safely before clinical follow-up.
```

## 3. Create a workspace

For a reproducible walkthrough, start with demo data:

```bash
autoagent new my-project --template customer-support --demo
cd my-project
autoagent status
```

What `--demo` adds:

- starter eval cases and scorer specs
- seeded review and autofix data
- enough local state to make review and deploy flows visible immediately

### Mock vs live mode

AutoAgent auto-detects the execution mode from your environment.

- no provider keys -> mock mode
- configured provider keys -> live mode is available

The recommended first run is **mock mode** because it is deterministic and does not require credentials.

When you are ready to configure live providers:

```bash
autoagent provider configure
autoagent provider test
autoagent mode set live
autoagent mode show
```

Helpful notes:

- `mode set auto` restores API-key detection after an explicit override
- `provider configure` writes workspace provider settings
- `provider test` checks that the expected environment variables are present

## 4. Inspect the default XML instruction

New workspaces now start with an XML root instruction in `prompts.root`.

Show the current instruction:

```bash
autoagent instruction show
```

Validate that it is well-formed:

```bash
autoagent instruction validate
```

Open it in your editor:

```bash
autoagent instruction edit
```

Generate a fresh XML draft from a brief:

```bash
autoagent instruction generate --brief "customer support agent for order tracking and refunds" --apply
```

Migrate an older plain-text prompt:

```bash
autoagent instruction migrate
autoagent instruction validate
```

For the full XML workflow, see [XML Instructions](xml-instructions.md).

## 5. Build your first config

Generate a config and build artifact from a natural-language prompt:

```bash
autoagent build "Build a customer support agent for order tracking, refunds, and cancellations"
```

The build step stages:

- a new versioned config
- generated eval cases
- a saved build artifact

Inspect the latest build artifact:

```bash
autoagent build show latest
```

### Transcript and builder flows

The CLI also supports transcript-driven generation through the `intelligence` surface:

```bash
autoagent intelligence import /path/to/transcripts.zip
autoagent intelligence report list
autoagent intelligence generate-agent <report-id> --output configs/v003_transcript.yaml
```

## 6. Run evals

Evaluate the active config:

```bash
autoagent eval run
```

Show the latest run again:

```bash
autoagent eval show latest
```

List recent runs:

```bash
autoagent eval list
```

### Useful eval options

Run one category only:

```bash
autoagent eval run --category safety
```

Write the result to a file:

```bash
autoagent eval run --output results.json
```

Run against a specific config:

```bash
autoagent eval run --config configs/v003.yaml
```

Run with XML instruction overrides:

```yaml
constraints:
  - Always confirm the cancellation reason before taking action.
```

```bash
autoagent eval run --instruction-overrides instruction_override.yaml
```

Inspect structured results:

```bash
autoagent eval results --run-id <run-id>
autoagent eval results --run-id <run-id> --failures
autoagent eval results export <run-id> --format markdown
```

### What to expect

In mock mode, AutoAgent will tell you that the run is simulated. That is expected until you connect a real runtime and live providers.

Do not rely on a specific starter score like `4/5` or `5/5` in docs or scripts. The exact demo output can change as templates and seeded data evolve.

## 7. Optimize the agent

Run one optimization cycle:

```bash
autoagent optimize --cycles 1
```

Run several cycles:

```bash
autoagent optimize --cycles 5
```

Run continuously:

```bash
autoagent optimize --continuous
```

Switch optimizer mode:

```bash
autoagent optimize --mode advanced
autoagent optimize --mode research
```

### Two normal first-run outcomes

Outcome 1: AutoAgent finds a failure cluster, proposes a change, and evaluates it.

Outcome 2: AutoAgent prints:

```text
Cycle 1/1 — Latest eval passed; no optimization needed.
```

That second outcome is normal when the current workspace is already healthy enough for the current cycle.

### Compare candidate-like versions

```bash
autoagent compare candidates
```

This only shows versions already marked with statuses such as `candidate`, `canary`, `imported`, or `evaluated`.

## 8. Review and deploy

### Review change cards

```bash
autoagent review list
autoagent review show pending
autoagent review apply pending
```

`review apply` supports selectors such as `pending` and `latest`.

### Deploy locally

Canary the latest deployable version:

```bash
autoagent deploy canary --yes
autoagent deploy status
```

Quick path that applies pending review cards first:

```bash
autoagent deploy --auto-review --yes
```

Preview the deployment plan without mutating state:

```bash
autoagent deploy --auto-review --yes --dry-run
```

### Release objects

Create a signed release object from an experiment:

```bash
autoagent release create --experiment-id exp-abc123
```

### External deployment target example

The deploy command also exposes a CX target:

```bash
autoagent deploy --target cx-studio --project PROJECT --agent-id AGENT --snapshot .autoagent/cx/snapshot.json
```

## 9. Use the interactive shell

Launch the shell:

```bash
autoagent shell
```

Resume the most recent saved session:

```bash
autoagent continue
autoagent session list
```

Common shell slash commands:

- `/status`
- `/config`
- `/memory`
- `/doctor`
- `/review`
- `/mcp`
- `/compact`
- `/resume`
- `/exit`

## 10. Models, providers, and permissions

Show the effective model setup:

```bash
autoagent model show
autoagent model list
autoagent model set proposer openai:gpt-4o
```

Manage provider settings:

```bash
autoagent provider configure
autoagent provider list
autoagent provider test
```

Inspect or change permission mode:

```bash
autoagent permissions show
autoagent permissions set acceptEdits
```

Available permission modes:

| Mode | Behavior |
|------|----------|
| `plan` | Read-only exploration |
| `default` | Prompts for risky actions |
| `acceptEdits` | Auto-allows config, memory, and model writes; still prompts for review, deploy, and MCP changes |
| `dontAsk` | Auto-allows everything |
| `bypass` | Same practical effect as `dontAsk`; usually for automation |

## 11. MCP integration

Inspect current MCP status:

```bash
autoagent mcp status
```

Manage workspace MCP servers:

```bash
autoagent mcp add my-tool --command "npx" --arg "-y" --arg "@my/tool-server"
autoagent mcp list
autoagent mcp inspect my-tool
autoagent mcp remove my-tool
```

Start the AutoAgent MCP server:

```bash
autoagent mcp-server
```

See [MCP Integration](mcp-integration.md) and [Connecting AutoAgent to Agentic Coding Tools](guides/agentic-coding-tools.md) for the full setup.

## 12. Connect existing runtimes

Import an existing runtime into AutoAgent:

```bash
autoagent connect openai-agents --path ./agent-project
autoagent connect anthropic --path ./claude-project
autoagent connect http --url https://agent.example.com
autoagent connect transcript --file ./conversations.jsonl --name imported-agent
```

The web UI equivalent lives at `/connect`.

## 13. CX Studio integration

Authenticate and browse CX agents:

```bash
autoagent cx auth
autoagent cx list --project PROJECT --location us-central1
```

Import, diff, export, and sync:

```bash
autoagent cx import AGENT_ID --project PROJECT --location us-central1
autoagent cx diff AGENT_ID --project PROJECT --location us-central1
autoagent cx export AGENT_ID --project PROJECT --location us-central1 --dry-run
autoagent cx sync AGENT_ID --project PROJECT --location us-central1
```

See [CX Studio Integration](cx-studio-integration.md) for the full round-trip workflow.

## 14. Recommended daily flow

Once the workspace exists, the normal loop is:

```bash
autoagent status
autoagent build "Describe the next refinement"
autoagent eval run
autoagent optimize --cycles 3
autoagent review show pending
autoagent review apply pending
autoagent deploy canary --yes
autoagent deploy status
```

Shortcut:

```bash
autoagent deploy --auto-review --yes
```

## 15. Next steps

- [CLI Reference](cli-reference.md)
- [UI Quick Start](UI_QUICKSTART_GUIDE.md)
- [App Guide](app-guide.md)
- [Platform Overview](platform-overview.md)
- [Concepts](concepts.md)
- [XML Instructions](xml-instructions.md)
- [MCP Integration](mcp-integration.md)

## Troubleshooting

### `No workspace found`

You are outside a workspace directory. Either `cd` into one or create one:

```bash
autoagent new my-project --template customer-support
```

### Provider credentials missing

Mock mode is still valid:

```bash
autoagent mode set mock
```

Or finish live setup:

```bash
autoagent provider configure
autoagent provider test
autoagent mode set live
```

### No pending review card

Generate or inspect more improvement output:

```bash
autoagent optimize --cycles 1
autoagent autofix suggest
```

### `autoagent compare candidates` prints `No candidate configs found.`

That command is optional. It only lists versions already marked as `candidate`, `canary`, `imported`, or `evaluated`.

### Need the broader command surface?

```bash
autoagent advanced
```

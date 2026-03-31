# AutoAgent

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB)
![Test Suite](https://img.shields.io/badge/test%20suite-pytest%20%2B%20vite-22C55E)
![License](https://img.shields.io/badge/license-Apache%202.0-111827)

AutoAgent automatically makes your AI agents better. Give it an agent, define what "good" looks like, and AutoAgent will build, evaluate, compare, optimize, review, and deploy changes in a loop you can inspect end to end.

```text
BUILD -> EVAL -> OPTIMIZE -> REVIEW -> DEPLOY
```

> **[Quick Start](docs/QUICKSTART_GUIDE.md)** — Get a workspace running in minutes
>
> **[Detailed Guide](docs/DETAILED_GUIDE.md)** — Full CLI walkthrough, including XML instructions and deployment
>
> **[UI Quick Start](docs/UI_QUICKSTART_GUIDE.md)** — Browser walkthrough for the current web console
>
> **[Platform Overview](docs/platform-overview.md)** — Product and architecture map

---

## Install

```bash
git clone https://github.com/andrewhuot/autoagent-vnextcc.git
cd autoagent-vnextcc
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Prerequisites

| Tool | Version | Why you need it |
|------|---------|-----------------|
| Python | 3.11+ | CLI, API, eval, and optimization runtime |
| Node.js | 20+ | Web console dev mode (`./start.sh`, `npm run dev`, `npm run build`) |
| `gcloud` | optional | CX / Google Cloud integration flows |

### API keys

AutoAgent auto-detects your environment:

- if provider credentials are present, it can use live LLM providers
- if they are missing, it falls back to deterministic mock responses

To enable live provider workflows, set at least one key:

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AI...
```

Run `autoagent doctor` to verify the current mode and provider readiness.

---

## Quick Start

```bash
autoagent new my-agent --template customer-support --demo
cd my-agent
autoagent instruction show
autoagent build "customer support agent for order tracking, refunds, and cancellations"
autoagent eval run
autoagent optimize --cycles 1
autoagent deploy --auto-review --yes
```

Notes:

- `--demo` seeds a friendlier first workspace with review and autofix data.
- New workspaces start with an XML root instruction by default.
- If the starter eval already passes cleanly, `autoagent optimize --cycles 1` may say `Latest eval passed; no optimization needed.` That is expected.
- `autoagent deploy --auto-review --yes` still works on a demo workspace because the seeded review data and staged versions make the deploy path reproducible.

---

## CLI

Default help groups the CLI into **Primary** and **Secondary** commands. Run `autoagent advanced` to see the broader hidden command set.

### Primary commands

| Command | Purpose |
|---------|---------|
| `new` | Create a new workspace from a starter template |
| `build` | Generate or inspect build artifacts |
| `eval` | Run evals, inspect results, compare runs, and generate eval suites |
| `optimize` | Run optimization cycles (`--continuous` for loop mode) |
| `deploy` | Canary, release, rollback, or auto-review-and-deploy |
| `status` | Show workspace health, versions, and recommended next steps |
| `doctor` | Check configuration, providers, data stores, and readiness |
| `shell` | Launch the interactive AutoAgent shell |

### Secondary commands

| Command | Purpose |
|---------|---------|
| `config` | List, diff, import, edit, resolve, rollback, and activate configs |
| `connect` | Import OpenAI Agents, Anthropic, HTTP, or transcript-backed runtimes |
| `instruction` | Show, validate, edit, generate, or migrate XML instructions |
| `memory` | Manage `AUTOAGENT.md` project memory |
| `mode` | Show or set mock/live/auto execution mode |
| `model` | Inspect or override proposer/evaluator model preferences |
| `provider` | Configure, list, and test provider profiles |
| `review` | Review, apply, reject, or export change cards |
| `template` | List and apply bundled starter templates |

All commands support `--help`. See [docs/cli-reference.md](docs/cli-reference.md) for the full reference, including the advanced surface.

---

## How It Works

AutoAgent centers everything around a closed improvement loop:

1. **Build** — create or refine agent configs and starter evals
2. **Eval** — run the current config against the active suite
3. **Compare** — inspect run-to-run deltas and case-level changes
4. **Optimize** — generate and test targeted changes
5. **Review** — accept or reject change cards in `review` or `Improvements`
6. **Deploy** — canary, release, rollback, or push through an integration target

The CLI, API, and UI all work off the same local workspace state, so you can move between surfaces without losing context.

---

## Key Features

- **Build workspace** — Prompt, transcript, builder chat, and saved artifacts in one place
- **XML instructions** — New workspaces default to XML root prompts with CLI and UI editing flows
- **Eval runs** — Run suites, inspect historical runs, and drill into case-level results
- **Results Explorer** — Filter failures, annotate examples, export runs, and compare outcomes
- **Compare** — Run or inspect pairwise config comparisons with significance summaries
- **Improvements** — One review workflow for opportunities, experiments, approvals, and history
- **Connect** — Import existing OpenAI Agents, Anthropic, HTTP, and transcript-backed runtimes
- **CX Studio** — Auth, import, diff, export, and sync Google CX agents from one surface
- **NL scorer** — Create eval scorers from natural language
- **Context workbench** — Inspect context usage and compaction tradeoffs
- **Registry and skills** — Manage reusable skills, policies, tools, and handoffs
- **MCP server** — 22 tools plus prompts/resources for Claude Code, Codex, Cursor, Windsurf, and other MCP clients

---

## Integrations

- **Google CX Studio / Dialogflow CX** — import, diff, export, sync, deploy
- **Google ADK** — import ADK agents, inspect diffs, export patches, deploy
- **MCP** — expose the live AutoAgent surface to coding agents
- **Transcript intelligence** — ingest archives and turn them into build artifacts and eval inputs

---

## Web Console

For the combined app:

```bash
autoagent server
```

Then open `http://localhost:8000`.

For hot-reload local development:

```bash
./start.sh
```

Then open:

- UI: `http://localhost:5173/dashboard`
- API docs: `http://localhost:8000/docs`

The current simple-mode nav is:

- `Dashboard`
- `Setup`
- `Build`
- `Connect`
- `Eval Runs`
- `Results Explorer`
- `Compare`
- `Optimize`
- `Improvements`
- `Deploy`

See [docs/UI_QUICKSTART_GUIDE.md](docs/UI_QUICKSTART_GUIDE.md) for the current browser walkthrough.

---

## Deploy

```bash
# Docker
docker compose up --build -d

# Cloud Run helper
./deploy/deploy.sh "$PROJECT_ID" "$REGION"

# Fly.io
fly launch --name autoagent --region ord && fly deploy
```

See [docs/deployment.md](docs/deployment.md) for local, container, and Cloud Run details.

---

## Documentation

**Guides:**

- [Quick Start](docs/QUICKSTART_GUIDE.md)
- [Detailed Guide](docs/DETAILED_GUIDE.md)
- [UI Quick Start](docs/UI_QUICKSTART_GUIDE.md)
- [Agentic Coding Tools](docs/guides/agentic-coding-tools.md)

**Reference:**

- [CLI Reference](docs/cli-reference.md)
- [API Reference](docs/api-reference.md)
- [Concepts](docs/concepts.md)
- [FAQ](docs/faq.md)
- [Architecture](docs/architecture.md)
- [Diagrams](docs/architecture-diagram.md)

**Product docs:**

- [Platform Overview](docs/platform-overview.md)
- [Web App Guide](docs/app-guide.md)
- [XML Instructions](docs/xml-instructions.md)
- [CX Studio Integration](docs/cx-studio-integration.md)
- [MCP Integration](docs/mcp-integration.md)
- [Deployment](docs/deployment.md)

**Feature deep dives:**

- [AutoFix](docs/features/autofix.md)
- [Judge Ops](docs/features/judge-ops.md)
- [Context Workbench](docs/features/context-workbench.md)
- [Prompt Optimization](docs/features/prompt-optimization.md)
- [Registry](docs/features/registry.md)
- [Trace Grading](docs/features/trace-grading.md)
- [NL Scorer](docs/features/nl-scorer.md)

---

## License

Apache 2.0

# AutoAgent

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB)
![Tests](https://img.shields.io/badge/tests-1131%2B%20passing-22C55E)
![License](https://img.shields.io/badge/license-Apache%202.0-111827)

AutoAgent is a continuous optimization platform for AI agents. It traces agent behavior, diagnoses failures, generates improvements, evaluates them with statistical rigor, and deploys winners — in an automated loop.

Point it at a broken agent. Get a better one back.

```
TRACE → DIAGNOSE → SEARCH → EVAL → GATE → DEPLOY → LEARN → REPEAT
```

> **[Quick Start](docs/QUICKSTART_GUIDE.md)** — Get a working agent in 2 minutes
>
> **[Detailed Guide](docs/DETAILED_GUIDE.md)** — Full walkthrough of every workflow
>
> **[UI Quick Start](docs/UI_QUICKSTART_GUIDE.md)** — Web console walkthrough
>
> **[Platform Overview](docs/platform-overview.md)** — Every subsystem explained

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

| Tool | Version | How to get it |
|------|---------|--------------|
| Python | 3.11+ | [python.org/downloads](https://python.org/downloads) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) (for web console) |

### API keys (auto-detect)

AutoAgent auto-detects your environment. If API keys are present, it uses live LLM providers. If not, it falls back to deterministic mock responses — no configuration needed.

To enable live optimization, set at least one key:

```bash
export OPENAI_API_KEY=sk-...          # GPT models
export ANTHROPIC_API_KEY=sk-ant-...   # Claude models
export GOOGLE_API_KEY=AI...           # Gemini models
```

Run `autoagent doctor` to verify your setup.

---

## Quick start

```bash
autoagent new my-agent --template customer-support
cd my-agent
autoagent build "customer support agent for order tracking, refunds, and cancellations"
autoagent eval run
autoagent optimize --cycles 3
autoagent deploy canary --yes
```

That's the full golden path: create → build → evaluate → optimize → deploy.

---

## CLI

AutoAgent shows 15 commands by default (8 primary + 7 secondary). Run `autoagent advanced` for the full list.

### Primary commands

| Command | Purpose |
|---------|---------|
| `new` | Create a new workspace from a starter template |
| `build` | Build agent artifacts or inspect build output |
| `eval` | Evaluate agent configs against test suites |
| `optimize` | Run optimization cycles (`--continuous` for loop mode) |
| `deploy` | Deploy with canary, release, or rollback (`--auto-review` for ship mode) |
| `status` | Show system health, config versions, and recent activity |
| `doctor` | Check system health and configuration |
| `shell` | Launch the interactive AutoAgent shell |

### Secondary commands

| Command | Purpose |
|---------|---------|
| `config` | Manage config versions (list, show, diff, edit, pin) |
| `memory` | Manage AUTOAGENT.md persistent project context |
| `mode` | Show or set CLI execution mode |
| `model` | Inspect and override model preferences |
| `provider` | Configure and validate provider settings |
| `review` | Review proposed change cards from the optimizer |
| `template` | List and apply starter workspace templates |

All commands support `--help`. Major commands support `--json` for structured output. See [docs/cli-reference.md](docs/cli-reference.md) for the full reference.

---

## How it works

Each optimization cycle follows eight steps:

| Step | What happens |
|------|-------------|
| **Trace** | Collect structured telemetry from agent invocations |
| **Diagnose** | Cluster failures, score opportunities, identify root causes |
| **Search** | Generate typed mutations ranked by expected lift, risk, and novelty |
| **Eval** | Replay mutations against test suites with side-effect isolation |
| **Gate** | Hard safety constraints first, then optimize objectives |
| **Deploy** | Promote winners via canary rollout with experiment card tracking |
| **Learn** | Record what worked and what didn't for future searches |
| **Repeat** | Loop autonomously until plateau or human intervention |

Every cycle produces a reviewable **experiment card** with a hypothesis, config diff, statistical significance, and rollback instructions. Hard safety gates are never traded off against performance.

---

## Key features

- **Evaluation engine** — 7 eval modes with bootstrap CI, sequential testing, anti-Goodhart guards
- **Trace analysis** — Span-level grading with 7 graders, blame maps, opportunity queue
- **Judge stack** — Tiered scoring: deterministic → similarity → LLM → audit judge
- **AutoFix copilot** — AI-driven fix proposals with review-before-apply
- **NL scorer** — Describe "good" in English, get a typed eval scorer
- **Context workbench** — Context window diagnostics and compaction simulation
- **Registry** — Versioned skills, policies, tool contracts, handoff schemas
- **Intelligence studio** — Upload transcripts, get analytics, generate agents
- **Human controls** — Pause, resume, pin surfaces, reject experiments, budget caps
- **Multi-model** — Google Gemini, OpenAI GPT-4o, Anthropic Claude, OpenAI-compatible

---

## Integrations

- **Google CX Agent Studio** — Import, optimize, export, deploy CX agents
- **Google ADK** — Import ADK agents via AST parsing, export patches, deploy to Cloud Run
- **MCP server** — 22 tools for Claude Code, Codex, Cursor, Windsurf ([setup guide](docs/guides/agentic-coding-tools.md))
- **CI/CD** — Gate deploys on eval scores, post experiment cards as PR comments

---

## Web console

Start with `autoagent server` and open `http://localhost:5173`. The sidebar toggles between Simple and Pro views.

**Observe** — Dashboard, traces, blame map, conversations, event log
**Optimize** — Trigger cycles, AutoFix proposals, opportunity queue, experiments
**Evaluate** — Eval runs, per-case results, judge ops, scorer studio
**Build** — Agent Studio, Intelligence Studio, assistant, simulation
**Manage** — Configs, registry, deploy, loop monitor, skills, runbooks, settings

---

## Deploy

```bash
# Docker
docker compose up --build -d

# Google Cloud Run
./deploy/deploy.sh $PROJECT_ID $REGION

# Fly.io
fly launch --name autoagent --region ord && fly deploy
```

See [docs/deployment.md](docs/deployment.md) for detailed setup.

---

## Documentation

**Guides:**
- [Quick Start](docs/QUICKSTART_GUIDE.md) | [Detailed Guide](docs/DETAILED_GUIDE.md) | [UI Quick Start](docs/UI_QUICKSTART_GUIDE.md)
- [Agentic Coding Tools](docs/guides/agentic-coding-tools.md)

**Reference:**
- [CLI Reference](docs/cli-reference.md) | [API Reference](docs/api-reference.md)
- [Concepts](docs/concepts.md) | [FAQ](docs/faq.md)
- [Architecture](docs/architecture.md) | [Diagrams](docs/architecture-diagram.md)

**Feature deep dives:**
[AutoFix](docs/features/autofix.md) | [Judge Ops](docs/features/judge-ops.md) | [Context Workbench](docs/features/context-workbench.md) | [Prompt Optimization](docs/features/prompt-optimization.md) | [Registry](docs/features/registry.md) | [Trace Grading](docs/features/trace-grading.md) | [NL Scorer](docs/features/nl-scorer.md)

**More:**
[Platform Overview](docs/platform-overview.md) | [Deployment](docs/deployment.md) | [Web App Guide](docs/app-guide.md) | [CX Integration](docs/cx-agent-studio.md) | [MCP Integration](docs/mcp-integration.md)

---

## License

Apache 2.0

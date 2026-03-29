# AutoAgent -- Beginner User Guide

**Version:** 1.1 | **Last Updated:** 2026-03-28

---

## Welcome

### What is AutoAgent?

AutoAgent is a continuous optimization platform for AI agents. If you have a chatbot, support agent, or any AI-powered assistant that talks to users, AutoAgent watches how it performs, figures out what's going wrong, generates targeted fixes, proves they work with statistical testing, and deploys the winners -- all in an automated loop that can run for hours, days, or weeks without you lifting a finger.

Think of it like CI/CD for your agent's brain. Instead of manually tweaking prompts and hoping for the best, AutoAgent traces every conversation, clusters failures by root cause, proposes specific mutations to your agent's configuration, evaluates them against a rigorous test suite, and only promotes changes that pass safety gates and show statistically significant improvement. You stay in control the whole time -- you can pause the loop, lock specific settings from being changed, or reject any experiment with a single command.

### Who is this guide for?

This guide is for developers and technical PMs who:

- Have an AI agent (or want to build one) and want to make it better systematically
- Have never used AutoAgent before
- Want to understand every feature, from installation to advanced optimization strategies

You should be comfortable with a terminal, basic Python, and have a general understanding of what LLMs are. No prior optimization or ML experience is needed.

> **Note:** "Beginner" in this guide means beginner to AutoAgent, not beginner to engineering. The platform has significant operational depth -- this guide opens all of it.

### What you'll learn

By the end of this guide, you'll know how to:

1. Install and run AutoAgent
2. Understand the core concepts behind agent optimization
3. Run your first optimization cycle via CLI and web UI
4. Navigate every page in the web console
5. Use the Builder Workspace to iterate on agents interactively
6. Leverage advanced features like AutoFix, Judge Ops, and prompt optimization
7. Integrate with Google CX Agent Studio and ADK
8. Use the policy optimization and reward systems
9. Troubleshoot common issues

### Your first mental model

Keep this in mind through the rest of the guide:

```
Observe real behavior -> Diagnose failures -> Propose changes -> Validate under gates -> Promote safely -> Repeat
```

AutoAgent is not just a dashboard and not just a CLI. It is a closed-loop system with controls.

> **Warning:** Optimization without hard gates leads to local wins and global regressions. AutoAgent is designed to avoid this, but only if you keep safety gates and human controls active.

---

## Chapter 1: Getting Started

### 1.1 Prerequisites

Before installing AutoAgent, make sure you have these tools on your machine:

| Tool | Minimum Version | Recommended | How to check |
|------|----------------|-------------|--------------|
| Python | 3.11 | 3.12 | `python3 --version` |
| Node.js | 18 | 20+ | `node --version` |
| npm | (comes with Node) | latest | `npm --version` |
| Git | any recent version | latest | `git --version` |

> **Note:** macOS ships with an older Python. If `python3 --version` shows anything below 3.11, install a newer version with Homebrew (`brew install python@3.12`) or from python.org.

> **Note:** If you don't have Node.js, install it from nodejs.org or use nvm: `nvm install 20 && nvm use 20`.

**Optional -- for live model-backed runs:**

| Variable | Provider |
|----------|----------|
| `OPENAI_API_KEY` | OpenAI (GPT-4o, o1, o3) |
| `ANTHROPIC_API_KEY` | Anthropic (Claude Sonnet, Haiku) |
| `GOOGLE_API_KEY` | Google (Gemini 2.5 Pro, Flash) |

You do **not** need API keys to get started. AutoAgent runs in mock mode by default, using deterministic responses instead of real LLM calls. This is perfect for exploring the platform.

### 1.2 Installation

Clone the repository and run the setup script:

```bash
git clone <repo-url> autoagent-vnextcc
cd autoagent-vnextcc
./setup.sh
```

If you get a "Permission denied" error:

```bash
chmod +x setup.sh start.sh stop.sh
./setup.sh
```

The setup script does six things automatically:

1. **Checks Python and Node versions** -- fails with a clear error if versions are too old
2. **Creates a Python virtual environment** -- `.venv` in the project root
3. **Installs Python dependencies** -- via `pip install -e '.[dev]'`
4. **Installs frontend dependencies** -- via `npm install` in the `web/` directory
5. **Copies `.env.example` to `.env`** -- your environment config file
6. **Seeds demo data** -- synthetic conversations, traces, and optimization history

When it finishes, you'll see:

```
  +  Setup complete in 47s

  What's next:
    ./start.sh          Start AutoAgent (backend + frontend)
```

> **Tip:** The entire setup typically takes under 2 minutes. If `pip install` is slow, it's downloading dependencies -- this only happens on first run.

### 1.3 Starting AutoAgent

Run the start script:

```bash
./start.sh
```

This script:

1. Activates the Python virtual environment
2. Loads environment variables from `.env`
3. Frees stale ports (8000, 5173) if needed
4. Starts the **FastAPI backend** on port 8000 (via `uvicorn api.server:app`)
5. Starts the **Vite frontend dev server** on port 5173 (via `npm run dev`)
6. Waits for both to be healthy (with a spinner animation)
7. Opens your browser to `http://localhost:5173` automatically
8. Handles Ctrl+C cleanup and PID file teardown

When everything is ready, you'll see:

```
  AutoAgent is running!

  Open in browser:
    Frontend   ->  http://localhost:5173
    API        ->  http://localhost:8000
    API docs   ->  http://localhost:8000/docs

  Logs:  .autoagent/backend.log  .  .autoagent/frontend.log
  Stop:  Ctrl+C  or  ./stop.sh
```

The process stays alive in the foreground. Press **Ctrl+C** to shut everything down cleanly, or use `./stop.sh` from another terminal.

> **Tip:** If you see "Port 8000 in use", run `./stop.sh` first to kill any previous AutoAgent processes.

### 1.4 Verifying your CLI

After setup, verify the CLI works. The entry point is `python3 runner.py`:

```bash
python3 runner.py --help
```

You'll see a list of all 30+ command groups:

```
Usage: runner.py [OPTIONS] COMMAND [ARGS]...

  AutoAgent VNextCC — agent optimization platform.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  adk         Google Agent Development Kit (ADK) integration
  autofix     AutoFix Copilot — reviewable improvement proposals
  autonomous  Run autonomous optimization with scoped permissions
  benchmark   Run standard benchmarks
  build       Build an agent artifact from natural language
  changes     Aliases for reviewable optimizer change cards
  config      Manage agent config versions
  context     Context Engineering Workbench
  curriculum  Self-play curriculum generator for adversarial eval prompts
  cx          Google Cloud CX Agent Studio — import, export, deploy
  dataset     Manage datasets for evaluation and training
  demo        Demo commands for presentations and quick trials
  deploy      Deploy a config version
  diagnose    Run failure diagnosis and optionally fix issues interactively
  doctor      Check system health and configuration
  edit        Apply natural language edits to agent config
  eval        Evaluate agent configs against test suites
  explain     Generate a plain-English summary of agent state
  full-auto   Run optimization + loop in dangerous full-auto mode
  init        Scaffold a new AutoAgent project
  judges      Judge Ops — monitoring, calibration, and human feedback
  logs        Browse conversation logs
  loop        Run the continuous autoresearch loop
  mcp-server  Start MCP server for AI coding tool integration
  memory      Project memory — manage AUTOAGENT.md
  optimize    Run optimization cycles to improve agent config
  outcomes    Manage business outcome data
  pause       Pause the optimization loop (human escape hatch)
  pin         Mark a config surface as immutable
  pref        Preference collection and export
  quickstart  Run the ENTIRE golden path: init -> seed -> eval -> optimize -> deploy
  registry    Modular registry — skills, policies, tool contracts
  reject      Reject a promoted experiment and rollback any active canary
  release     Manage signed release objects
  replay      Show optimization history like git log --oneline
  resume      Resume the optimization loop after a pause
  review      Review proposed change cards from the optimizer
  reward      Manage reward definitions
  rl          Policy optimization commands
  runbook     Runbooks — curated bundles of skills, policies, and tools
  scorer      NL Scorer — create eval scorers from natural language
  server      Start the API server + web console
  skill       Unified skill management — build-time and run-time skills
  status      Show system health, config versions, and recent activity
  trace       Trace analysis — grading, blame maps, and graphs
  unpin       Remove immutable marking from a config surface
```

Run a few quick confidence checks:

```bash
python3 runner.py status
python3 runner.py config list
python3 runner.py eval list
python3 runner.py runbook list
```

The `status` command shows a quick health summary:

```
AutoAgent Status
━━━━━━━━━━━━━━━━━
  Pulse check complete. Your agent is alive and learning.
  Config:     v001
  Conversations: 6840
  Eval score: 0.9487
  Mood:       Flying
  Safety:     0.360 ✗
  Success:    ███░░░░░░░  28%
  Errors:     ███████░░░  72%
  Cycles run: 100
```

`runbook list` shows the pre-built fix recipes:

```
Runbooks (7):
  enhance-few-shot-examples
  fix-retrieval-grounding
  improve-routing-accuracy
  optimize-cost-efficiency
  reduce-tool-latency
  stabilize-multilingual-support
  tighten-safety-policy
```

> **Tip:** For onboarding, run `quickstart` first to bootstrap end-to-end behavior, then inspect generated config and eval artifacts before touching advanced subsystems.

### 1.5 Your first look at the dashboard

When your browser opens, you'll land on the **Builder Workspace** -- the primary authoring surface. But let's start with the Dashboard to get oriented.

Click **Dashboard** in the left sidebar (or navigate to `/dashboard`). You'll see:

- **Health Pulse** -- A large circular indicator showing your agent's overall health score. In demo mode, this starts around 0.62 (needs improvement). Color-coded: green (0.80-1.00), amber (0.60-0.79), red (0.00-0.59).
- **Hard Gates** -- Two binary indicators:
  - **Safety Gate**: Pass or Fail. Zero tolerance for safety violations.
  - **Regression Gate**: Pass or Fail. Based on whether the latest optimization attempt regressed performance.
- **Four primary metrics**:
  - **Task Success**: Percentage of conversations that resolved successfully
  - **Error Rate**: Percentage of conversations that hit errors
  - **Latency p95**: 95th percentile response time in milliseconds
  - **Cost/Conversation**: Average spend per conversation
- **Optimization Journey Timeline** -- A horizontal timeline showing the last 10 optimization attempts with scores and accept/reject status
- **Score Trajectory Chart** -- A line chart showing how the composite score has changed over time
- **Recommended next actions** -- Exact CLI commands to try next

> **Tip:** Toggle between **Simple** and **Advanced** views using the button in the top right. Advanced mode reveals additional panels: Diagnostic Signals, Cost Controls, and Human Escape Hatches.

### 1.6 Understanding the navigation

The left sidebar organizes the entire app into logical groups:

**Build**
- **Builder Workspace** (`/builder`) -- The primary IDE-like authoring surface
- **Agent Studio** (`/agent-studio`) -- Natural language config editing
- **Intelligence Studio** (`/intelligence-studio`) -- Transcript archive analytics
- **Assistant** (`/assistant`) -- Chat-based agent builder with file upload
- **Sandbox** (`/sandbox`) -- Synthetic scenario testing
- **What-If** (`/what-if`) -- Counterfactual scenario analysis
- **Knowledge** (`/knowledge`) -- Knowledge base from successful conversations

**Observe**
- **Dashboard** (`/dashboard`) -- Health scorecard and journey timeline
- **Traces** (`/traces`) -- Span-level trace viewer
- **Blame Map** (`/blame`) -- Failure clustering by root cause
- **Conversations** (`/conversations`) -- Browse real agent conversations
- **Event Log** (`/events`) -- Real-time system event timeline

**Optimize**
- **Optimize** (`/optimize`) -- Trigger optimization cycles
- **Live Optimize** (`/live-optimize`) -- Real-time SSE streaming
- **AutoFix** (`/autofix`) -- AI-generated fix proposals
- **Opportunities** (`/opportunities`) -- Ranked optimization queue
- **Experiments** (`/experiments`) -- Experiment cards with diffs and stats

**Evaluate**
- **Eval Runs** (`/evals`) -- Run evaluations and compare results
- **Judge Ops** (`/judge-ops`) -- Judge versioning and calibration
- **Scorer Studio** (`/scorer-studio`) -- Create scorers from natural language

**Manage**
- **Configs** (`/configs`) -- Browse and diff config versions
- **Deploy** (`/deploy`) -- Canary deployment and rollback
- **Loop Monitor** (`/loop`) -- Continuous optimization loop control
- **Skills** (`/skills`) -- Skills Marketplace
- **Agent Skills** (`/agent-skills`) -- Capability gap analysis
- **Registry** (`/registry`) -- Skills, policies, tools, handoffs
- **Runbooks** (`/runbooks`) -- Curated fix bundles
- **Project Memory** (`/memory`) -- Persistent project context (AUTOAGENT.md)
- **Notifications** (`/notifications`) -- Alert configuration
- **Settings** (`/settings`) -- Runtime configuration

**Policy Optimization**
- **Reward Studio** (`/reward-studio`) -- Define and audit reward functions
- **Preference Inbox** (`/preference-inbox`) -- Human preference pairs for RLHF
- **Policy Candidates** (`/policy-candidates`) -- RL training jobs and OPE evaluation
- **Reward Audit** (`/reward-audit`) -- Challenge suites and sycophancy detection

**Integrations**
- **CX Import/Deploy** (`/cx/import`, `/cx/deploy`) -- Google CX Agent Studio
- **ADK Import/Deploy** (`/adk/import`, `/adk/deploy`) -- Google Agent Development Kit

**Keyboard shortcuts** work globally (except when typing in form fields):
- `Cmd+K` (or `Ctrl+K`) -- Open the command palette for quick navigation
- `n` -- New evaluation
- `o` -- New optimization
- `d` -- New deployment

---

## Chapter 2: Core Concepts

### 2.1 What is an "agent"?

In AutoAgent, an "agent" is any AI system that:

1. Receives messages from users (or other systems)
2. Uses an LLM to generate responses
3. May call tools, route to specialist sub-agents, or maintain state

An agent's behavior is defined by its **configuration** -- a YAML file that includes:

- **Instructions** -- The system prompt that tells the agent how to behave
- **Routing rules** -- Logic that decides which specialist handles a conversation
- **Tool descriptions** -- Schemas for tools the agent can call
- **Few-shot examples** -- Example conversations that guide the agent's responses
- **Generation settings** -- Temperature, max tokens, and other LLM parameters
- **Safety policies** -- Rules the agent must never violate
- **Model selection** -- Which LLM powers the agent

AutoAgent treats this configuration as the thing it optimizes. Instead of manually tweaking prompts, you let AutoAgent propose, test, and deploy configuration changes automatically.

### 2.2 What is "optimization"?

Optimization in AutoAgent means **systematically improving your agent's configuration** through a data-driven feedback loop. Here's what happens in each cycle:

1. **Trace** -- AutoAgent collects structured telemetry from agent conversations: every message, tool call, agent transfer, and outcome
2. **Diagnose** -- Failures are classified and clustered by root cause. A blame map identifies what's going wrong and how often.
3. **Search** -- The optimizer generates a candidate mutation -- a specific, targeted change to the agent's configuration
4. **Eval** -- The candidate is evaluated against a test suite with statistical significance testing
5. **Gate** -- Safety gates are checked first (non-negotiable), then improvement gates
6. **Deploy** -- If the candidate passes all gates, it's promoted via canary deployment
7. **Learn** -- The outcome is recorded so future searches are smarter
8. **Repeat** -- The loop continues until you stop it, the budget runs out, or improvements plateau

This is fundamentally different from manual prompt tuning. Instead of "try this prompt and see if it feels better," AutoAgent says "this specific change improved task success by 8% with p < 0.05, and it didn't trip any safety gates."

### 2.3 The optimization loop explained simply

Imagine you run a customer support chatbot. Users complain that billing questions get routed to the wrong agent, causing frustration and escalation. Here's what AutoAgent does:

```
Step 1: TRACE
  AutoAgent sees 100 recent conversations.
  23 of them failed because billing queries went to the shipping agent.

Step 2: DIAGNOSE
  Failure cluster: "billing_misroute" -- 23 occurrences, high impact.
  Root cause: routing rules missing keywords "invoice", "refund", "charge".

Step 3: SEARCH
  Proposed mutation: Add missing keywords to routing.rules[billing_agent].
  Mutation type: routing_rule (medium risk).

Step 4: EVAL
  Run the mutation against 50 test cases.
  Results: 42/50 pass (up from 35/50 baseline).
  Statistical significance: p = 0.02.

Step 5: GATE
  Safety gate: PASS (no safety regressions)
  Improvement gate: PASS (+14% on task success)
  Regression gate: PASS (no other metrics degraded)

Step 6: DEPLOY
  New config v13 deployed as canary (10% of traffic).
  Monitor for 1 hour, then promote to 100%.

Step 7: LEARN
  Record: routing_rule mutations work well for misroute failures.
  Update bandit weights to favor routing fixes for similar issues.

Step 8: REPEAT
  Next cycle targets the second-highest failure cluster.
```

### 2.4 Metrics: quality, safety, latency, cost

AutoAgent evaluates agents across multiple dimensions, organized into a 4-layer hierarchy:

#### Layer 1: Hard Gates (must pass -- no exceptions)

| Metric | What it measures | Gate condition |
|--------|-----------------|----------------|
| Safety score | Percentage of responses free from safety violations | Must be 100% |
| Format compliance | Response format correctness | Must exceed 95% |

If a proposed change causes even one safety violation in the test suite, it is **immediately rejected**. Hard gates are never traded off against other metrics. A mutation that improves task success by 12% but trips a safety gate is rejected. No exceptions.

#### Layer 2: North-Star Outcomes (must improve)

| Metric | What it measures |
|--------|-----------------|
| Task completion rate | Did the agent successfully resolve the user's request? |
| User satisfaction | Would a human rate this response as helpful? |

These are the metrics you're optimizing *for*. A mutation must show improvement here to be promoted.

#### Layer 3: Operating SLOs (must not regress)

| Metric | What it measures | Typical threshold |
|--------|-----------------|-------------------|
| Latency p95 | 95th percentile response time | < 5000ms |
| Cost per conversation | Average spend per conversation | < $0.50 |

A mutation that improves task success but doubles your latency will be rejected. SLOs are guardrails.

#### Layer 4: Diagnostics (observed only)

| Metric | What it measures |
|--------|-----------------|
| Tool selection accuracy | Did the agent call the right tools? |
| Routing precision | Did the agent route to the right specialist? |

Diagnostics help you understand *why* things are going well or poorly, but they don't block deployments.

### 2.5 Experiments and experiment cards

Every optimization attempt in AutoAgent produces an **experiment card** -- a structured record of what was tried, what changed, and whether it worked. Think of it like a lab notebook entry.

An experiment card contains:

| Field | What it records |
|-------|----------------|
| `experiment_id` | Unique identifier (e.g., `exp_a1b2c3`) |
| `hypothesis` | What the optimizer thinks will improve |
| `touched_surfaces` | Which parts of the config were changed |
| `baseline_scores` | Scores before the change |
| `candidate_scores` | Scores after the change |
| `significance` | Statistical p-value from bootstrap test |
| `config_sha` | Hash of the proposed config for reproducibility |
| `risk_class` | low, medium, high, or critical |
| `diff_summary` | Human-readable description of what changed |
| `status` | pending -> running -> accepted / rejected / expired |
| `rollback_instructions` | How to undo if needed |

Experiment cards form a complete audit trail. You can go back to any point in your optimization history and understand exactly what was tried and why it was accepted or rejected.

### 2.6 Skills -- what they are and why they matter

Skills in AutoAgent are a unified abstraction that serves two purposes:

**Build-time skills** are optimization strategies the optimizer uses. They're reusable recipes for specific types of fixes:

- "How to fix routing misroutes" -- add missing keywords, adjust thresholds
- "How to reduce latency" -- tune timeouts, simplify prompts, swap to faster models
- "How to patch safety gaps" -- add guardrails, tighten policies

Each build-time skill tracks its own effectiveness. If a skill stops working (its success rate drops), it's automatically retired.

**Run-time skills** are agent capabilities -- API integrations, handoff protocols, specialized tools. They compose together with dependency resolution and conflict detection.

Skills can be discovered, installed, composed, and shared. The recommendation engine suggests skills based on your agent's current failure patterns.

### 2.7 The typed mutation system

When AutoAgent proposes a change to your agent, it's not just "rewrite the whole prompt." Changes are **typed mutations** that target specific configuration surfaces:

| Mutation type | What it changes | Risk level | Auto-deploy? |
|---------------|----------------|------------|--------------|
| Instruction rewrite | Agent instructions/prompts | Low | Yes |
| Few-shot edit | Example conversations | Low | Yes |
| Temperature nudge | Generation settings | Low | Yes |
| Tool hint | Tool descriptions | Medium | Conditional |
| Routing rule | Agent routing logic | Medium | Conditional |
| Policy patch | Safety/business policies | Medium | Conditional |
| Model swap | Underlying LLM | High | No (human review) |
| Topology change | Agent graph structure | High | No (human review) |
| Callback patch | Callback handlers | High | No (human review) |

Low-risk mutations can be auto-deployed without human review. High-risk mutations always require you to approve before deployment. Critical mutations (custom) require all gates plus explicit approval and are never auto-deployed.

---

## Chapter 3: Your First Optimization (CLI)

This chapter walks you through the complete optimization workflow using the command line. Make sure you've run `./setup.sh` and have the virtual environment active:

```bash
cd autoagent-vnextcc
source .venv/bin/activate
```

### 3.1 Creating a project with `autoagent init`

Start by scaffolding a new project:

```bash
autoagent init --template customer-support
```

This creates three directories:

```
configs/v001_base.yaml    # Base agent configuration
evals/cases/              # Eval test cases (YAML files)
agent/config/             # Agent config schema
```

The `customer-support` template includes a multi-specialist agent with support, orders, and recommendations routing. For a bare scaffold with no pre-built agent, use:

```bash
autoagent init --template minimal
```

For a specific target directory:

```bash
autoagent init --template customer-support --dir my-project
```

The full golden path -- init through deploy in one command:

```bash
autoagent quickstart --agent-name "My Agent" --verbose --open
```

### 3.2 Checking system status with `autoagent status`

Before optimizing, check the current state:

```bash
autoagent status
```

You'll see output like:

```
+------------------------------------------+
Agent Status
+------------------------------------------+

Overall Score:     0.62 +++++++++.....  NEEDS WORK
Safety Score:      0.95 +++++++++++++.  !
Routing Accuracy:  0.71 ++++++++++....  !
Avg Latency:       4.2s +++++++++++++.  !
Resolution Rate:   0.58 ++++++++......

Active Config:     v1 (deployed 1h ago)
Loop Status:       Idle
Budget Used:       $0.00 / $10.00 daily

Failure Breakdown:
  routing_error:   ++++++.... 23%
  tool_timeout:    +++....... 8%
  safety_issue:    +......... 3%

-> Next: Run diagnostics to understand failures
  autoagent diagnose
```

For machine-readable output:

```bash
autoagent status --json | jq '.score'
```

You can also specify custom database paths:

```bash
autoagent status --db /path/to/conversations.db --configs-dir /path/to/configs
```

### 3.3 Collecting trace data with `autoagent trace`

AutoAgent records structured telemetry from every agent invocation. To analyze a specific trace:

```bash
autoagent trace grade <trace_id>
```

This runs the 7-grader suite against the trace:

| Grader | What it evaluates |
|--------|-------------------|
| Routing | Was the correct specialist agent selected? |
| Tool selection | Was the right tool chosen for the task? |
| Tool arguments | Were tool arguments correct and complete? |
| Retrieval quality | Did retrieval return relevant context? |
| Handoff quality | Was context preserved across agent handoffs? |
| Memory use | Was memory read/written appropriately? |
| Final outcome | Did the span achieve its intended result? |

To see failure clusters over a time window:

```bash
autoagent trace blame --window 24h --top 10
autoagent trace blame --window 7d --top 20
```

This builds a **blame map** -- groups of related failures organized by root cause, each with an impact score based on frequency and severity.

To visualize a trace as a span dependency graph:

```bash
autoagent trace graph <trace_id>
```

### 3.4 Finding problems with `autoagent diagnose`

The diagnose command clusters failures and proposes fixes:

```bash
autoagent diagnose
```

For an interactive experience with fix proposals:

```bash
autoagent diagnose --interactive
```

Interactive mode walks you through each failure cluster:

```
> Issue #1: Billing Misroutes (23 failures)
> Root cause: Missing keywords "invoice", "refund", "charge"
> Fix: Add keywords to routing.rules[billing_agent]
>
> Commands: fix | examples | next | skip
>
> You: fix
>
> Applied fix. Score: 0.62 -> 0.74 (+0.12)
```

You can also output diagnosis as JSON for integration with other tools:

```bash
autoagent diagnose --json
```

### 3.5 Running an optimization cycle with `autoagent optimize`

Run one optimization cycle:

```bash
autoagent optimize --cycles 1
```

The full option set:

```bash
python3 runner.py optimize --help

Usage: runner.py optimize [OPTIONS]
Options:
  --cycles INTEGER
  --mode [standard|advanced|research]
  --db TEXT
  --configs-dir TEXT
  --memory-db TEXT
  --full-auto
  -j, --json
```

Use `--mode research` to engage pro-mode algorithms (MIPROv2, BootstrapFewShot, GEPA, SIMBA). Use `--mode advanced` for multi-hypothesis adaptive search. `standard` is the default and best for getting started.

To run multiple cycles:

```bash
autoagent optimize --cycles 5
```

Each cycle produces an experiment card. You'll see output like:

```
Cycle 1/5:
  Hypothesis: Add missing billing keywords to routing rules
  Mutation: routing_rule (medium risk)
  Baseline: 0.62 | Candidate: 0.74 | Delta: +0.12
  Significance: p = 0.02
  Status: ACCEPTED -> config v2

Cycle 2/5:
  Hypothesis: Reduce tool timeout from 10s to 4s
  Mutation: generation_settings (low risk)
  Baseline: 0.74 | Candidate: 0.78 | Delta: +0.04
  Significance: p = 0.04
  Status: ACCEPTED -> config v3

Cycle 3/5:
  Hypothesis: Rewrite support agent instructions for clarity
  Mutation: instruction_rewrite (low risk)
  Baseline: 0.78 | Candidate: 0.77 | Delta: -0.01
  Significance: p = 0.62 (not significant)
  Status: REJECTED (no improvement)
```

### 3.6 Continuous optimization with `autoagent loop`

For hands-off optimization, use the loop command:

```bash
autoagent loop --max-cycles 20 --stop-on-plateau
```

The full option set:

```bash
python3 runner.py loop --help

Usage: runner.py loop [OPTIONS]
Options:
  --max-cycles INTEGER
  --stop-on-plateau
  --delay FLOAT
  --schedule [continuous|interval|cron]
  --interval-minutes FLOAT
  --cron TEXT
  --checkpoint-file TEXT
  --resume / --no-resume
  --full-auto
```

The loop runs the full optimization cycle repeatedly until:
- It reaches the maximum number of cycles
- Improvements plateau (no significant gains in N consecutive cycles)
- The daily budget is exhausted
- You press Ctrl+C or run `autoagent pause`

Additional scheduling options:

```bash
# Run on a fixed interval (every 5 minutes)
autoagent loop --schedule interval --interval-minutes 5

# Run on a cron schedule (every 10 minutes)
autoagent loop --schedule cron --cron "*/10 * * * *"

# Resume from where you left off after a restart
autoagent loop --resume --checkpoint-file .autoagent/loop_checkpoint.json
```

The loop is designed for multi-day unattended operation:
- **Checkpointing** -- State is saved after every cycle; restarts resume seamlessly
- **Dead letter queue** -- Failed cycles are captured for inspection, never dropped
- **Watchdog** -- Stuck cycles are killed after a configurable timeout
- **Graceful shutdown** -- Ctrl+C (or SIGTERM) finishes the current cycle before stopping
- **Resource monitoring** -- Warnings when memory or CPU exceed configured thresholds
- **Structured logging** -- JSON log rotation with configurable size limits

### 3.7 Reading the results

After optimization, review what changed:

```bash
# List all config versions
autoagent config list

# Show the current active config
autoagent config show

# Show a specific version
autoagent config show v3

# Diff two versions
autoagent config diff v1 v3

# View optimization history
autoagent replay --limit 10
```

The replay command shows a git-log style history of optimization attempts:

```
v3 [accepted] Reduce tool timeout 10s->4s  (0.74 -> 0.78)  2h ago
v2 [accepted] Add billing routing keywords  (0.62 -> 0.74)  3h ago
v1 [initial]  Base configuration            (0.62)          1d ago
```

### 3.8 Deploying a version

Once you're happy with a config version, deploy it:

```bash
# Canary deploy (recommended) -- routes a percentage of traffic to the new config
autoagent deploy --config-version v3 --strategy canary

# Immediate deploy -- switches all traffic instantly
autoagent deploy --config-version v3 --strategy immediate
```

The deploy command also supports deploying directly to CX or ADK targets:

```bash
autoagent deploy --config-version 3 --strategy canary --target cx-studio \
  --project my-project --location us-central1 --agent-id abc123
```

Canary deployments let you monitor the new config against real traffic before committing. If something goes wrong, the system can roll back automatically.

### 3.9 Human control commands

You're always in control of the optimization loop:

```bash
# Pause the loop (takes effect after current cycle)
autoagent pause

# Resume a paused loop
autoagent resume

# Lock a config surface so the optimizer can't touch it
autoagent pin safety_instructions
autoagent pin routing

# Unlock a previously pinned surface
autoagent unpin routing

# Reject and rollback a specific experiment
autoagent reject exp_a1b2c3
```

**Pinnable surfaces:** `instruction`, `few_shot`, `tool_description`, `model`, `generation_settings`, `callback`, `context_caching`, `memory_policy`, `routing`.

You can also set permanently immutable surfaces in `autoagent.yaml`:

```yaml
human_control:
  immutable_surfaces: ["safety_instructions"]
```

Pinned surfaces and the pause state persist across restarts via `.autoagent/human_control.json`.

### 3.10 Operator daily checklist

Once you're running AutoAgent regularly, the typical daily CLI workflow is:

```bash
# 1. Check system state
autoagent status
autoagent config list
autoagent logs

# 2. Evaluate current baseline
autoagent eval run --output results.json
autoagent eval results --file results.json

# 3. Run bounded optimization cycles
autoagent optimize --cycles 3

# 4. Review cards and apply only gated wins
autoagent review list
autoagent review show <card_id>
autoagent review apply <card_id>

# 5. Deploy via canary
autoagent deploy --config-version <v> --strategy canary

# 6. Monitor outcomes
autoagent status
autoagent replay --limit 10
```

> **Tip:** Save your most common sequences as shell aliases or Makefile recipes.

### 3.11 Every CLI command at a glance

Here's the complete CLI command reference:

#### Core commands

| Command | What it does |
|---------|-------------|
| `autoagent init` | Scaffold a new project |
| `autoagent server` | Start the API server and web console |
| `autoagent status` | Show system health and metrics |
| `autoagent doctor` | Run setup diagnostics |
| `autoagent logs` | View optimization loop logs |
| `autoagent quickstart` | Run the full golden path |
| `autoagent build <prompt>` | Build an agent from natural language |
| `autoagent full-auto` | **Dangerous:** Full autonomous mode |
| `autoagent autonomous` | Scoped autonomous optimization |
| `autoagent mcp-server` | Start MCP server for AI coding tools |
| `autoagent benchmark run <name>` | Run a benchmark suite |

#### Eval commands

| Command | What it does |
|---------|-------------|
| `autoagent eval run` | Run the eval suite |
| `autoagent eval results` | Display results from a previous run |
| `autoagent eval list` | List all historical eval runs |

#### Optimize & loop commands

| Command | What it does |
|---------|-------------|
| `autoagent optimize` | Run optimization cycles |
| `autoagent loop` | Run continuous optimization |
| `autoagent pause` | Pause the loop |
| `autoagent resume` | Resume the loop |
| `autoagent pin <surface>` | Lock a surface from mutation |
| `autoagent unpin <surface>` | Unlock a surface |
| `autoagent reject <id>` | Reject and rollback an experiment |

#### Config commands

| Command | What it does |
|---------|-------------|
| `autoagent config list` | List all config versions |
| `autoagent config show [VERSION]` | Display a config version |
| `autoagent config diff <v1> <v2>` | Diff two versions |
| `autoagent config migrate <file>` | Migrate old config format |

#### Deploy commands

| Command | What it does |
|---------|-------------|
| `autoagent deploy` | Promote a config version |
| `autoagent replay` | Show optimization history |
| `autoagent release` | Manage signed release objects |

#### Trace commands

| Command | What it does |
|---------|-------------|
| `autoagent trace grade <id>` | Grade all spans in a trace |
| `autoagent trace blame` | Build failure cluster map |
| `autoagent trace graph <id>` | Render trace as span graph |

#### AutoFix commands

| Command | What it does |
|---------|-------------|
| `autoagent autofix suggest` | Generate fix proposals from failures |
| `autoagent autofix apply <id>` | Apply a fix proposal |
| `autoagent autofix history` | View fix proposal history |

#### Judge commands

| Command | What it does |
|---------|-------------|
| `autoagent judges list` | List registered judges |
| `autoagent judges calibrate` | Run calibration analysis |
| `autoagent judges drift` | Check for scoring drift |

#### Context commands

| Command | What it does |
|---------|-------------|
| `autoagent context analyze` | Analyze context window usage |
| `autoagent context simulate` | Simulate compaction strategies |
| `autoagent context report` | Generate context health report |

#### Registry commands

| Command | What it does |
|---------|-------------|
| `autoagent registry list` | List registry items by type |
| `autoagent registry show` | Show a specific item |
| `autoagent registry add` | Add a new item |
| `autoagent registry diff` | Diff two versions of an item |
| `autoagent registry import` | Bulk import from YAML/JSON |

#### Scorer commands

| Command | What it does |
|---------|-------------|
| `autoagent scorer create` | Create a scorer from natural language |
| `autoagent scorer list` | List all scorers |
| `autoagent scorer show <name>` | Display a scorer's spec |
| `autoagent scorer refine <name>` | Add criteria to a scorer |
| `autoagent scorer test <name>` | Test a scorer against a trace |

#### Skill commands

| Command | What it does |
|---------|-------------|
| `autoagent skill list` | List available skills |
| `autoagent skill show <name>` | Show skill details |
| `autoagent skill recommend` | Get recommendations for failures |
| `autoagent skill apply <name>` | Apply a skill |
| `autoagent skill install <path>` | Install from file |
| `autoagent skill export <name>` | Export a skill |
| `autoagent skill stats` | Usage statistics |
| `autoagent skill learn` | Learn from recent patterns |

#### Review & runbook commands

| Command | What it does |
|---------|-------------|
| `autoagent review list` | List pending change cards |
| `autoagent review show <id>` | Show change card details |
| `autoagent review apply <id>` | Apply a change card |
| `autoagent review reject <id>` | Reject a change card |
| `autoagent review export <id>` | Export a change card |
| `autoagent changes approve <id>` | Alias for review apply |
| `autoagent changes reject <id>` | Alias for review reject |
| `autoagent runbook list` | List available runbooks |
| `autoagent runbook show <name>` | Show runbook details |
| `autoagent runbook apply <name>` | Apply a runbook |
| `autoagent runbook create <name>` | Create a new runbook |

#### Memory commands

| Command | What it does |
|---------|-------------|
| `autoagent memory show` | Display project memory (AUTOAGENT.md) |
| `autoagent memory add <note>` | Add a note to project memory |

#### Natural language commands

| Command | What it does |
|---------|-------------|
| `autoagent edit` | Natural language config edits |
| `autoagent explain` | Plain-English agent health summary |
| `autoagent diagnose` | Interactive failure diagnosis |

#### Dataset & outcomes commands

| Command | What it does |
|---------|-------------|
| `autoagent dataset` | Create, version, split, and export eval datasets |
| `autoagent outcomes` | Manage and calibrate business outcome data |
| `autoagent curriculum` | Self-play curriculum generator for adversarial prompts |

#### Policy optimization commands

| Command | What it does |
|---------|-------------|
| `autoagent reward` | Define and manage reward functions |
| `autoagent rl` | Policy optimization (train, evaluate, promote, rollback) |
| `autoagent pref` | Preference collection and export for RLHF |

#### CX Integration commands

| Command | What it does |
|---------|-------------|
| `autoagent cx list` | List CX agents in a project |
| `autoagent cx import` | Import a CX agent |
| `autoagent cx export` | Export optimized config to CX |
| `autoagent cx deploy` | Deploy to CX environment |
| `autoagent cx status` | Show CX deployment status |
| `autoagent cx widget` | Generate chat widget HTML |

#### ADK Integration commands

| Command | What it does |
|---------|-------------|
| `autoagent adk import <path>` | Import an ADK agent |
| `autoagent adk export <path>` | Export to ADK format |
| `autoagent adk deploy <path>` | Deploy ADK agent |
| `autoagent adk status <path>` | Show ADK agent status |
| `autoagent adk diff <path>` | Diff against a snapshot |

#### Demo commands

| Command | What it does |
|---------|-------------|
| `autoagent demo quickstart` | Quick demo setup |
| `autoagent demo vp` | VP-level 5-minute demo |

> **Tip:** Every command supports `--help` for inline documentation. Major commands support `--json` for structured output that you can pipe to `jq` or other tools.

---

## Chapter 4: Your First Optimization (Web UI)

The web console provides the same capabilities as the CLI, plus rich visualizations and interactive workflows. Start the server if it's not running:

```bash
./start.sh
```

Then open `http://localhost:5173` in your browser.

### 4.1 Dashboard overview

Navigate to **Dashboard** in the sidebar. Here's what each section does:

#### Health Pulse

The large circular indicator shows your agent's overall health score from 0 to 1. The pulse speed varies by health state (green: 3s pulse, amber: 1.5s pulse, red: 0.8s pulse -- a living, animated indicator).

| Color | Score range | Meaning |
|-------|------------|---------|
| Green | 0.80 - 1.00 | Healthy |
| Amber | 0.60 - 0.79 | Needs attention |
| Red | 0.00 - 0.59 | Critical |

#### Hard Gates

Two binary pass/fail indicators:

- **Safety Gate** -- Fails if `safety_violation_rate > 0`. Any safety violation fails this gate.
- **Regression Gate** -- Fails if the latest optimization attempt caused a regression.

#### Primary Metrics

Four cards showing the key numbers:

| Card | What to look for |
|------|-----------------|
| Task Success | Higher is better. Target: > 80% |
| Error Rate | Lower is better. Target: < 5% |
| Latency p95 | Lower is better. Target: < 3000ms |
| Cost/Conversation | Lower is better. Depends on budget |

Each card shows a trend arrow (up, down, or neutral) based on recent changes.

#### Optimization Journey Timeline

A horizontal timeline (animated SVG line drawing) showing the last 10 optimization attempts. Each node shows:
- Version number
- Score
- Accept/reject status
- Brief description of the change

Click any node to jump to the config diff view.

#### Score Trajectory Chart

A line chart tracking the composite score over time. Use this to spot trends: steady improvement, plateaus, or regressions.

#### Advanced Mode sections

Toggle to **Advanced** mode to see:

- **Diagnostic Signals** -- Error rate, safety compliance, and latency score bars. Plus common failure families with "Fix" buttons.
- **Cost Controls** -- Total spend, daily budget tracking, cost per improvement unit, and stall detection.
- **Human Escape Hatches** -- Pause/resume the optimizer, pin surfaces, reject experiments -- all from the UI.
- **Event Timeline** -- The last 12 system events.
- **Recommended next actions** -- Exact CLI commands to run.

**Data sources:**
- `GET /api/health`
- `GET /api/health/scorecard`
- `GET /api/optimize/history`

### 4.2 Builder Workspace walkthrough

The **Builder Workspace** (`/builder`) is the primary surface for building and iterating on agents. It's an IDE-like interface with multiple panels.

#### Top bar

The top bar contains:

| Element | What it does |
|---------|-------------|
| Project selector | Switch between projects |
| Environment switcher | Toggle between `dev`, `staging`, and `prod` environments |
| Model selector | Choose between models (gpt-5.4, gpt-5.4-mini, claude-sonnet-4-6) |
| Execution mode | `ask`, `draft`, `apply`, or `delegate` (see below) |
| Pause toggle | Pause/resume the workspace |
| Permission badge | Shows count of pending approvals |

#### Execution modes

The Builder Workspace has four execution modes:

| Mode | What it does | When to use |
|------|-------------|-------------|
| `ask` | Conversational exploration and analysis. No side effects. | Understanding state, planning, Q&A |
| `draft` | Propose and stage changes without direct irreversible action. | Reviewing mutations before applying |
| `apply` | Execute direct changes through the task pipeline. | Ready to make real changes |
| `delegate` | Autonomous specialist execution with sandbox expectations. | Trusted automated workflows |

> **Warning:** Default to `draft` for most teams until your approval and guardrail posture is mature. `apply` and `delegate` make real changes.

#### Left rail

A collapsible panel showing:

- **Projects** -- Your workspace projects. Click to select.
- **Sessions** -- Conversation sessions within the selected project.
- **Tasks** -- Individual work items with status indicators:
  - `pending`, `running` (blue spinner), `paused` (yellow), `completed` (green check), `failed` (red X), `cancelled` (gray)
- **Favorites** -- Starred items for quick access
- **Notifications** -- Alerts and updates

> **Tip:** On screens narrower than 1100px, the left and right panels collapse automatically. Click the panel headers to expand them.

#### Conversation pane (center)

The main interaction area. It displays:

- **User messages** -- What you've typed
- **Assistant responses** -- AutoAgent's replies
- **System events** -- Status updates, task completions, etc.
- **Task details** -- When viewing a specific task, shows:
  - Artifacts (code diffs, graphs, evals, traces)
  - Proposals (pending changes)
  - Approvals (pending permissions)

Click any artifact to open it in the Inspector panel.

#### Composer (bottom)

The text input where you type requests. Features:

- Free-text input for natural language requests
- Mode selector for different interaction styles
- Enter sends; Shift+Enter inserts a newline
- Type `/` to open the slash command menu

**Available slash commands:**

| Command | What it does |
|---------|-------------|
| `/plan` | Create a plan for a complex task |
| `/improve` | Suggest improvements to the current agent |
| `/trace` | Analyze a specific trace |
| `/eval` | Run an evaluation |
| `/skill` | Browse or apply skills |
| `/guardrail` | Add or inspect guardrails |
| `/compare` | Compare two config versions |
| `/branch` | Fork the current task |
| `/deploy` | Deploy a config version |
| `/rollback` | Rollback to a previous version |
| `/memory` | View or update project memory |
| `/permissions` | Manage approval permissions |

**Example free-text requests:**
- "Make the agent more empathetic in billing conversations"
- "Add safety guardrails for PII disclosure"
- "Reduce response latency by tuning tool timeouts"
- "Run an eval against the safety test cases"

#### Inspector panel (right)

A tabbed panel that shows details about the selected artifact:

| Tab | What it shows |
|-----|---------------|
| **Overview** | Summary of the selected artifact, task, or session |
| **Diff** | Code/config diff for proposed changes |
| **ADK Graph** | Agent graph visualization (for ADK agents) |
| **Evals** | Evaluation results and scores |
| **Traces** | Trace span details |
| **Skills** | Skills applied or recommended |
| **Guardrails** | Safety rules and guardrail status |
| **Files** | Project knowledge files |
| **Config** | Raw configuration YAML / AGENTS.md / CLAUDE.md context |

#### Task drawer (slide-in)

Click the tasks icon to open a slide-in drawer showing:
- **Running tasks** -- Currently active work items
- **Completed tasks** -- Finished items with outcomes
- **Pending approvals** -- Changes waiting for your review

Each task has action buttons: Pause, Resume, Cancel, Fork.

### 4.3 Optimize page

Navigate to **Optimize** (`/optimize`). This page lets you trigger optimization cycles and review the results.

**Controls:**
- **Observation window** -- How far back to look for conversation data
- **Force toggle** -- Override normal gating (use carefully)
- **Start Optimization** button

**What you see after starting:**
- Active task progress with polling updates
- Score trajectory chart showing historical attempts
- Timeline of attempts with status badges (accepted, rejected, reasons)
- Diff/details panel for the selected attempt

**Typical workflow:**
1. Set the observation window (e.g., "last 24 hours")
2. Click **Start Optimization**
3. Watch the progress bar
4. Review the experiment card when it completes
5. Check the diff to see exactly what changed
6. If accepted, the new config is ready for deployment

**Data sources:**
- `GET /api/optimize/history`
- `POST /api/optimize/run`
- `GET /api/tasks/{task_id}`
- WebSocket `optimize_complete`

### 4.4 Live Optimize page

Navigate to **Live Optimize** (`/live-optimize`). This is the same as Optimize but with real-time Server-Sent Events (SSE) streaming. You'll see each phase of the optimization cycle as it happens:

- Diagnosing failures...
- Generating candidate...
- Running evaluation...
- Checking gates...
- Deploying...

This is useful for presentations or when you want to see the optimization process in detail.

**Data source:** `GET /api/optimize/stream` (SSE)

### 4.5 Eval Runs page

Navigate to **Eval Runs** (`/evals`). This page lets you create and track evaluation runs.

**Creating a new eval:**
1. Click **Start New Evaluation**
2. Optionally select a specific config version (defaults to active)
3. Optionally filter by category (e.g., `safety`, `happy_path`)
4. Click **Run**

**What you see:**
- Runs table with columns: status, progress, score, case counts
- Click any run to view details
- Comparison mode: select two completed runs to compare side-by-side

**Eval Detail page** (`/evals/:id`):
- Run header with status, timestamp, pass count, safety failure callout
- Composite score block
- Score bars for quality/safety/latency/cost
- Per-case table with filters (category, pass/fail) and sorting
- Expandable rows for deep case inspection

**Data sources:**
- `GET /api/eval/runs`
- `GET /api/config/list`
- `POST /api/eval/run`
- `GET /api/eval/runs/{run_id}`
- `GET /api/eval/runs/{run_id}/cases`
- WebSocket `eval_complete`

### 4.6 Experiments page

Navigate to **Experiments** (`/experiments`). This page shows all experiment cards from optimization attempts.

Each card displays:
- Experiment ID and hypothesis
- Touched config surfaces
- Baseline vs. candidate scores
- Statistical significance
- Status (accepted, rejected with reason, pending)
- Risk classification
- Config diff

Use this page to audit your optimization history and understand what's been tried.

**Data sources:**
- `GET /api/experiments/{experiment_id}`
- `GET /api/experiments/stats`
- `GET /api/experiments/archive`
- `GET /api/experiments/pareto`
- `GET /api/experiments/judge-calibration`

### 4.7 Traces page

Navigate to **Traces** (`/traces`). This page shows structured trace events from agent invocations.

- Filter by trace ID, session, or time range
- View span trees with nested tool calls and agent transfers
- See timing, token counts, and outcomes for each span
- Link to trace grading results

**Data sources:**
- `GET /api/traces/recent`
- `GET /api/traces/search`
- `GET /api/traces/{trace_id}`
- `GET /api/traces/{trace_id}/grades`
- `GET /api/traces/{trace_id}/graph`
- `GET /api/traces/sessions/{session_id}`

### 4.8 Conversations page

Navigate to **Conversations** (`/conversations`). Browse real agent conversations.

**What you see:**
- Overview stats: total conversations, success rate, avg latency, avg tokens
- Filters: outcome (success/fail/error), limit, search text
- Conversation table with expandable detail panels
- Each conversation shows:
  - User and agent message turns
  - Tool call summaries
  - Safety flags
  - Error messages

**Data sources:**
- `GET /api/conversations` (list with filters)
- `GET /api/conversations/stats`
- `GET /api/conversations/{conversation_id}`

### 4.9 Skills pages

**Skills** (`/skills`) -- Browse optimization strategies (build-time skills). Each skill shows:
- Name and category
- Platform compatibility
- Effectiveness tracking (success rate, times applied)
- Description and examples

**Agent Skills** (`/agent-skills`) -- Agent capability gap analysis. AutoAgent identifies what your agent can't do and suggests skills to fill the gaps.

**Registry** (`/registry`) -- The modular registry for all configuration types:
- Skills
- Policies
- Tool contracts
- Handoff schemas

Each item is versioned. You can view history, compare versions, import, and export.

**Data sources:**
- `GET /api/skills/marketplace`
- `GET /api/skills/recommend`
- `GET /api/skills/stats`
- `GET /api/registry/{item_type}`
- `GET /api/registry/{item_type}/{name}`

### 4.10 Configs page

Navigate to **Configs** (`/configs`). This is your config version browser.

**What you see:**
- Version list with: status (active/canary/archived), hash, composite score, timestamp
- Click a version to view its full YAML
- Compare mode: select two versions for side-by-side diff

**Data sources:**
- `GET /api/config/list`
- `GET /api/config/show/{version}`
- `GET /api/config/diff?a={a}&b={b}`
- `GET /api/config/active`

### 4.11 Deploy page

Navigate to **Deploy** (`/deploy`). Manage deployments.

**What you see:**
- Active version card -- the config currently serving traffic
- Canary version card -- if a canary is running, shows version and verdict
- Deploy form:
  - Version selector
  - Strategy: `canary` or `immediate`
- Deployment history table
- Rollback button for active canaries

**Typical workflow:**
1. Select a version that passed optimization
2. Choose `canary` strategy
3. Click **Deploy**
4. Monitor the canary verdict
5. If healthy, promote to full deployment
6. If problems, click **Rollback**

**Data sources:**
- `GET /api/deploy/status`
- `POST /api/deploy`
- `POST /api/deploy/rollback`
- `GET /api/config/list`

### 4.12 Loop Monitor page

Navigate to **Loop Monitor** (`/loop`). Control the continuous optimization loop.

**What you see:**
- Loop control form:
  - Number of cycles
  - Delay between cycles (seconds)
  - Observation window
- Running/idle status with progress counters
- Success-rate trajectory chart
- Per-cycle cards showing optimization/deploy outcomes

**Typical workflow:**
1. Set max cycles (e.g., 20) and delay
2. Click **Start Loop**
3. Watch cycle-by-cycle results
4. Click **Stop Loop** if you see degradation
5. Review per-cycle acceptance/rejection patterns

**Data sources:**
- `GET /api/loop/status`
- `POST /api/loop/start`
- `POST /api/loop/stop`
- WebSocket `loop_cycle`

### 4.13 Settings page

Navigate to **Settings** (`/settings`). This page is informational:

- Key project file paths (config, evals, storage locations)
- Keyboard shortcut reference
- Links to API docs (`/docs` and `/redoc`)

This page does not mutate system state.

### 4.14 Demo mode

Navigate to `/builder/demo` (or click the demo link in the Dashboard). The demo page offers a guided 5-act walkthrough:

| Act | Title | What it teaches |
|-----|-------|----------------|
| 1 | Build | Creating an agent from a description |
| 2 | Configure | Setting up routing, tools, and policies |
| 3 | Evaluate | Running evals and reading results |
| 4 | Optimize | Running the optimization loop |
| 5 | Ship | Deploying to production |

**How to use the demo:**
1. Click **Load Demo Data** to seed the demo scenario
2. Click **Play** on Act 1
3. The demo opens the Builder Workspace with pre-loaded data
4. Follow along as each act highlights different features
5. Track your progress with the act progress bar

> **Tip:** The VP demo (`autoagent demo vp --web`) is a CLI-driven 5-minute demo that walks through fixing a broken e-commerce support bot. It improves health from 0.62 to 0.87 in three cycles.

### 4.15 Blame Map page

Navigate to **Blame Map** (`/blame`). This page visualizes failure clusters from your agent's traces.

**What you see:**
- Failure clusters grouped by `(grader, agent_path, reason)`
- Each cluster shows:
  - Cluster name and root cause description
  - Occurrence count and frequency
  - Impact score (frequency x severity x business impact)
  - Trend indicator (getting better, worse, or stable)
  - Example trace links
- Clusters are ranked by impact score, so the most important problems appear first

**Data sources:**
- `GET /api/traces/blame`

### 4.16 AutoFix page

Navigate to **AutoFix** (`/autofix`). AI-generated fix proposals.

**What you see:**
- List of fix proposals, each with:
  - Root cause description with evidence
  - Suggested mutation type (e.g., routing_rule, instruction_rewrite)
  - Target config surface
  - Expected lift (estimated improvement)
  - Risk level (low/medium/high)
  - Confidence score
- Action buttons: **Apply** or **Reject** for each proposal
- History of past proposals with outcomes

**Typical workflow:**
1. Review proposals ranked by expected lift
2. Click a proposal to see the full analysis and proposed diff
3. Click **Apply** to create a new config version with the fix
4. The applied fix goes through the standard eval/gate pipeline

### 4.17 Opportunities page

Navigate to **Opportunities** (`/opportunities`). A ranked optimization queue.

**What you see:**
- Opportunities derived from the blame map
- Each opportunity includes:
  - Failure family name
  - Priority rank and impact score
  - Recommended mutation operators
  - Expected lift estimate
  - Link to example traces for investigation
- The optimizer pulls from this queue automatically during optimization cycles

**Data sources:**
- `GET /api/opportunities/count`
- `GET /api/opportunities/{opportunity_id}`

### 4.18 Judge Ops page

Navigate to **Judge Ops** (`/judge-ops`). Judge management and quality assurance.

**What you see:**
- **Judge list** -- All registered judges with their types (deterministic, similarity, binary_rubric, audit)
- **Version history** -- Track judge changes and their impact on scores
- **Calibration panel** -- Compare judge scores to human labels
  - Agreement rate
  - False positive/negative rates
  - Confusion matrix
- **Drift monitor** -- Track judge scoring patterns over time
  - Agreement rate trend chart
  - Drift alerts when patterns shift beyond threshold

**Data sources:**
- `GET /api/judges/calibration`
- `GET /api/judges/drift`
- `POST /api/judges/feedback`

### 4.19 Context Workbench page

Navigate to **Context Workbench** (`/context`). Diagnose context window issues.

**What you see:**
- **Growth pattern chart** -- How context window usage changes over conversation turns
  - Linear growth: steady increase per turn
  - Exponential growth: accelerating increase (problem!)
  - Sawtooth: periodic compaction
  - Stable: well-managed context
- **Utilization meter** -- Current context window utilization percentage
- **Failure correlation** -- Which failures correlate with context state
- **Compaction simulator** -- Preview the impact of different compaction strategies:
  - Aggressive: maximum compression, some information loss
  - Balanced: moderate compression, minimal loss
  - Conservative: minimal compression, preserves all context

**Data sources:**
- `GET /api/context/analysis/{trace_id}`
- `POST /api/context/simulate`
- `GET /api/context/report`

### 4.20 Event Log page

Navigate to **Event Log** (`/events`). Real-time system event stream.

**What you see:**
- Chronological list of all system events
- Each event shows:
  - Event type (optimization_complete, eval_complete, deploy, safety_violation, etc.)
  - Timestamp
  - Cycle ID (if applicable)
  - Event details and metadata
- Auto-refreshes with new events via Server-Sent Events

**Data source:** `GET /api/events` (SSE)

### 4.21 Scorer Studio page

Navigate to **Scorer Studio** (`/scorer-studio`). Create custom evaluation scorers.

**What you see:**
- **Create panel** -- Type a natural language description of what good looks like
- **Scorer list** -- All created scorers with their dimensions and weights
- **Detail panel** -- Full scorer spec showing named dimensions, rubric criteria, and weight distribution
- **Test panel** -- Test a scorer against a real trace and see dimension-by-dimension results
- **Refine panel** -- Add additional criteria to an existing scorer

**Data sources:**
- `POST /api/scorers/create`
- `GET /api/scorers/{name}`
- `POST /api/scorers/{name}/refine`
- `POST /api/scorers/{name}/test`

### 4.22 Change Review page

Navigate to **Change Review** (`/changes`). Review pending configuration changes.

**What you see:**
- List of pending change cards from various sources:
  - AutoFix proposals
  - Agent Studio edits
  - Intelligence Studio insights
  - Optimizer proposals
- Each card shows:
  - Source (where the change came from)
  - Config diff (what will change)
  - Root cause analysis (why)
  - Expected impact
  - Risk assessment
- Action buttons: Approve, Reject (with reason), Export

**Data sources:**
- `GET /api/reviews/pending`
- `POST /api/reviews/request`
- `POST /api/reviews/{request_id}/submit`

### 4.23 Policy Optimization pages

The **Policy Optimization** section exposes RLHF-style tooling for teams running reward model training.

**Reward Studio** (`/reward-studio`):
- Define and audit reward functions that drive RLHF training and policy optimization
- Test and validate reward functions against sample interactions
- Data source: `GET /api/rewards/{name}`, `POST /api/rewards/{name}/test`, `POST /api/rewards/{name}/audit`

**Preference Inbox** (`/preference-inbox`):
- Collect and manage human preference pairs used for RLHF fine-tuning
- Review pairs side-by-side and choose preferred responses
- Data source: `GET /api/preferences/pairs`, `POST /api/preferences/pairs`, `POST /api/preferences/export`

**Policy Candidates** (`/policy-candidates`):
- Manage RL training jobs, evaluate policy artifacts with OPE (off-policy evaluation), and promote or roll back candidates
- Data source: `GET /api/rl/jobs`, `POST /api/rl/train`, `POST /api/rl/evaluate`, `POST /api/rl/ope`, `POST /api/rl/promote`, `POST /api/rl/rollback`

**Reward Audit** (`/reward-audit`):
- Run challenge suites, inspect audit findings, evaluate OPE reports, and detect sycophancy in reward models
- Data source: `POST /api/rewards/challenge/run`, `GET /api/rewards/hard-gates/list`

### 4.24 Additional pages reference

Here's a quick reference for every remaining page:

| Page | Route | What it does |
|------|-------|-------------|
| **Blame Map** | `/blame` | Failure clustering and root cause attribution with impact scores |
| **Opportunities** | `/opportunities` | Ranked optimization queue showing what to fix next |
| **AutoFix** | `/autofix` | AI-generated fix proposals with review-before-apply workflow |
| **Judge Ops** | `/judge-ops` | Judge versioning, calibration, and drift monitoring |
| **Context Workbench** | `/context` | Context window analysis and compaction strategies |
| **Change Review** | `/changes` | Review and approve proposed config changes |
| **Runbooks** | `/runbooks` | Curated bundles of skills, policies, and tools |
| **Project Memory** | `/memory` | Persistent project context (AUTOAGENT.md) |
| **Scorer Studio** | `/scorer-studio` | Create eval scorers from natural language |
| **Event Log** | `/events` | Real-time system event timeline |
| **Agent Studio** | `/agent-studio` | Chat interface for natural language agent editing |
| **Intelligence Studio** | `/intelligence-studio` | Transcript archive analytics and Q&A |
| **Assistant** | `/assistant` | Chat-based agent builder with file upload |
| **Sandbox** | `/sandbox` | Synthetic scenario testing |
| **What-If** | `/what-if` | Counterfactual scenario analysis |
| **Knowledge** | `/knowledge` | Knowledge base from successful conversations |
| **Notifications** | `/notifications` | Webhook, Slack, and email notification settings |
| **Reward Studio** | `/reward-studio` | Define and audit reward functions for RLHF |
| **Preference Inbox** | `/preference-inbox` | Human preference pairs for RLHF fine-tuning |
| **Policy Candidates** | `/policy-candidates` | RL training jobs and policy artifact evaluation |
| **Reward Audit** | `/reward-audit` | Challenge suites and sycophancy detection |
| **CX Import** | `/cx/import` | Import Google CX Agent Studio agents |
| **CX Deploy** | `/cx/deploy` | Deploy to CX with widget generation |
| **ADK Import** | `/adk/import` | Import Google ADK agents from Python source |
| **ADK Deploy** | `/adk/deploy` | Deploy ADK agents to Cloud Run or Vertex AI |
| **Reviews** | `/reviews` | Broader review queue |
| **Demo** | `/demo` | Standalone demo page |

### 4.25 Safe exploration order for beginners

When you first explore the UI, work from safe to risky:

1. **Read-only pages first:** Dashboard, Configs, Conversations, Traces
2. **Action pages with side effects next:** Optimize, AutoFix, Deploy, Changes
3. **Governance pages before production changes:** Judge Ops, Notifications, Runbooks, Settings
4. **Builder and Intelligence surfaces last:** Once you understand gating and approvals

> **Warning:** Some pages expose operations that can mutate configs, run eval workloads, or trigger deploy behavior. Confirm environment and target before executing.

---

## Chapter 5: The Builder Workspace Deep Dive

The Builder Workspace is the most powerful surface in AutoAgent. This chapter explores every feature in detail.

### 5.1 Modes: Ask vs. Draft vs. Apply vs. Delegate

The top bar includes an **execution mode** selector with four values:

**Ask mode:**
- Conversational exploration and analysis
- No side effects on your configuration
- Best for: understanding state, planning changes, Q&A about failures

**Draft mode:**
- Changes are proposed and staged but not applied
- Safe for exploration and experimentation
- Artifacts are generated for review
- Best for: reviewing mutations before committing

**Apply mode:**
- Changes are applied to the agent configuration
- Evaluations run against real test suites
- Deployments go live
- Best for: when you're confident in your changes

**Delegate mode:**
- Autonomous specialist execution with sandbox expectations
- Stronger approval and guardrail requirements
- Best for: trusted automated workflows

> **Warning:** Always start in `ask` or `draft` mode when exploring new changes. Switch to `apply` only when you've reviewed the proposed changes and are ready to apply them.

### 5.2 Environments: Dev vs. Staging vs. Production

The environment switcher has three values:

**Dev environment:**
- Uses mock providers (no API keys needed)
- Faster iteration cycles
- No cost implications
- Safe for experiments

**Staging environment:**
- Uses real LLM providers
- Test data and non-production traffic
- Intermediate validation before production

**Production environment:**
- Uses real LLM providers with live traffic
- Real deployment implications
- Requires API keys and careful approval posture

### 5.3 Working with artifacts

When you interact with the Builder Workspace, it generates **artifacts** -- structured outputs that you can inspect, approve, or reject.

Types of artifacts:

| Type | What it contains | Where to view |
|------|-----------------|---------------|
| **Code diff** | Proposed config changes in diff format | Inspector > Diff tab |
| **ADK graph** | Agent graph visualization | Inspector > ADK Graph tab |
| **Eval results** | Evaluation scores and per-case breakdown | Inspector > Evals tab |
| **Traces** | Span-level trace data | Inspector > Traces tab |
| **Skills** | Skill recommendations or applications | Inspector > Skills tab |
| **Guardrails** | Safety rule status and violations | Inspector > Guardrails tab |
| **Files** | Project knowledge files | Inspector > Files tab |
| **Releases** | Deployment records | Inspector > Overview tab |

Click any artifact in the conversation pane to automatically open it in the Inspector with the appropriate tab selected.

### 5.4 Task management

Tasks represent individual work items in the Builder Workspace. Each task has a lifecycle:

**Statuses:** `pending`, `running`, `paused`, `completed`, `failed`, `cancelled`

**Task actions:**
- **Pause** -- Suspend a running task
- **Resume** -- Continue a paused task
- **Cancel** -- Stop a task permanently
- **Fork** -- Create a copy of a task to try a different approach
- **Approve request** -- Grant a pending permission
- **Reject request** -- Deny a pending permission

### 5.5 The Inspector tabs explained

The Inspector is the right panel of the Builder Workspace. It has nine tabs:

#### Overview tab

Summary information about the selected item:
- Task description and status
- Key metrics and scores
- Timestamps and duration
- Links to related items

#### Diff tab

Shows configuration changes in diff format:
- Green lines = additions
- Red lines = deletions
- Context lines for surrounding code
- Line-by-line comparison

#### Evals tab

Evaluation results for the current task:
- Composite score with breakdown
- Per-case pass/fail table
- Score comparison (baseline vs. candidate)
- Statistical significance indicators

#### Traces tab

Span-level trace data:
- Hierarchical span tree
- Timing information per span
- Tool call details
- Error messages and stack traces
- Grading results per span

#### Skills tab

Skills relevant to the current context:
- Applied skills with effectiveness data
- Recommended skills based on failure patterns
- Skill version history

#### Guardrails tab

Safety and policy status:
- Active guardrails and their rules
- Violation history
- Policy compliance status
- Suggested guardrail additions

#### Files tab

Project knowledge files:
- Knowledge base files
- SOPs and documentation uploads
- Click to view file contents

#### Config tab

Raw configuration YAML:
- Full config dump (AGENTS.md / CLAUDE.md context)
- Instruction memory panel
- Syntax highlighted and searchable

#### ADK Graph tab

Agent graph visualization for ADK agents:
- Node-edge diagram of agent topology
- Click nodes to inspect individual agents
- Highlights routing paths and tool connections

### 5.6 Proposals and approvals

The Builder Workspace uses a **proposal/approval** workflow for changes:

1. You describe a change in natural language
2. AutoAgent generates a **proposal** -- a structured description of what will change
3. You review the proposal in the conversation pane
4. You **approve**, **reject**, or **revise** the proposal
5. If approved, the change is applied

For higher-risk changes, the system generates **approval requests** -- permission checks that require explicit confirmation before proceeding.

**Approval scope values:**

| Scope | What it means |
|-------|--------------|
| `once` | Single-use approval for this specific action |
| `task` | Approval applies for the duration of this task |
| `project` | Approval applies across the project (use cautiously) |

**Privileged action values that require approval:**

| Action | Description |
|--------|------------|
| `source_write` | Modifying source files |
| `external_network` | Making external network calls |
| `secret_access` | Accessing environment secrets |
| `deployment` | Deploying to production |
| `benchmark_spend` | Running expensive benchmark workloads |

> **Warning:** "Task created" is not equivalent to "change safely deployed." Always verify approvals, eval bundles, and deploy status explicitly.

### 5.7 Approval permission categories

| Category | Example actions | Requires approval? |
|----------|----------------|-------------------|
| Config changes | Modify agent instructions | In apply mode, yes |
| Deployments | Deploy to production | Always yes |
| Safety modifications | Change safety policies | Always yes |
| Eval runs | Run evaluations | In draft mode, no |
| Read operations | View configs, traces | Never |

The permission count badge in the top bar shows how many pending approvals need your attention.

### 5.8 Real-time events

The Builder Workspace maintains a WebSocket connection to `ws://<host>/ws` for live updates:
- Task progress updates
- Evaluation results streaming
- Optimization phase changes
- System notifications

Message types: `eval_complete`, `optimize_complete`, `loop_cycle`.

Events appear in real-time in the conversation pane without needing to refresh.

### 5.9 Working with the model selector

The top bar includes a model selector that lets you choose which LLM powers the Builder Workspace interactions:

| Model | Characteristics | Best for |
|-------|----------------|----------|
| `gpt-5.4` | Highest quality, slower, more expensive | Complex agent design, critical config changes |
| `gpt-5.4-mini` | Good quality, faster, cheaper | Iterative refinement, quick experiments |
| `claude-sonnet-4-6` | Strong reasoning, balanced | Architecture decisions, safety analysis |

The model you select here affects the Builder Workspace's own AI interactions -- not your agent's model. Your agent's model is configured separately in `autoagent.yaml`.

### 5.10 Builder Workspace backend APIs

The Builder frontend maps to `/api/builder` endpoints covering:

- Project CRUD
- Session lifecycle
- Task lifecycle and progress updates
- Proposal review
- Artifact retrieval and commenting
- Approval response
- Permission grant management
- Event listing and SSE stream
- Metrics snapshots
- Specialist invocation

### 5.11 Compact layout

On screens narrower than 1100px, the Builder Workspace automatically enters compact mode:
- Left rail collapses to icons only
- Inspector panel slides over the conversation pane instead of sitting beside it
- Click panel headers to expand/collapse

### 5.12 Recommended beginner workflow in Builder

1. Select project and confirm `dev` environment
2. Choose `draft` mode
3. Ask for a plan with explicit constraints (use `ask` mode)
4. Inspect proposed artifacts in timeline and inspector tabs
5. Approve only narrow-scope requests
6. Run eval and inspect result deltas
7. Promote to broader environment only after stable validation

**Common failure patterns to avoid:**
- Sending apply-mode instructions unintentionally
- Forgetting environment context before approval
- Ignoring failed task notifications in drawer
- Approving project-wide permission grants too early
- Interpreting a plan artifact as an executed change

### 5.13 End-to-end walkthrough example

**Step 1: Select your project**

Click on a project in the left rail.

**Step 2: Type a request**

```
Analyze the top failure patterns and suggest improvements for billing conversations
```

Press Enter to submit.

**Step 3: Review the response**

The conversation pane will show AutoAgent's analysis, suggestions with evidence, and generated artifacts (diffs, eval previews).

**Step 4: Inspect an artifact**

Click on a generated diff artifact. The Inspector panel opens to the **Diff** tab, showing exactly what config changes are proposed.

**Step 5: Review the proposal**

If the changes look good, click **Approve** on the proposal card. If you want modifications, click **Revise** and describe what you'd change.

**Step 6: Check evaluation results**

Switch to the **Evals** tab in the Inspector to see how the proposed changes performed against the test suite.

**Step 7: Deploy**

If everything looks good, the task will generate a deployment action. Approve it to deploy the changes.

---

## Chapter 6: Advanced Features

### 6.1 Agent Studio

**Page:** `/agent-studio`
**Purpose:** Describe agent changes in plain language without writing YAML.

Agent Studio provides a chat interface where you type what you want to change, and AutoAgent translates it into configuration mutations.

**What you see:**
- Intercom-style conversational UI
- Sample prompts for quick-start
- **Live draft mutations** -- Real-time change preview on each user input
- **Change set cards** -- Visual breakdown with surface, impact score, and description
- **Metric impact visualization** -- Before/after score estimates

**Example workflow:**
1. Type: "Make the agent more empathetic in billing conversations"
2. Review change card: "prompts.root - Add empathy instructions to billing agent prompt"
3. Refine: "Also mention patience and acknowledgment"
4. Apply -> Config v13 created with new instructions
5. View the diff in the Configs page

**Sample prompts:**
- "Make BillingAgent verify invoices before answering"
- "Route shipping delays straight to RefundAgent"
- "Tighten orchestrator handoffs so specialists inherit context"
- "Add safety guardrails to prevent unauthorized PII disclosure"

**CLI equivalent:**

```bash
autoagent edit "Make the agent more empathetic in billing conversations"
autoagent edit "Add safety guardrails for PII" --dry-run    # Preview only
autoagent edit "Reduce latency by tuning timeouts" --json   # Machine output
autoagent edit --interactive  # Interactive mode with confirmation
```

**Data source:** `POST /api/edit` (when user confirms changes)

### 6.2 Intelligence Studio

**Page:** `/intelligence-studio`
**Purpose:** Build agents from conversation data rather than from scratch.

If you have a collection of past support conversations, Intelligence Studio can analyze them and generate an agent automatically.

**Step-by-step:**

1. **Upload** -- Drag and drop a ZIP archive containing transcripts (JSON, CSV, or TXT files)
2. **Wait for processing** -- Watch the real-time progress bar (parsing, analyzing, extracting)
3. **Review summary cards:**
   - Total transcripts processed
   - Language distribution (en, es, fr, etc.)
   - Intent distribution (order tracking, refunds, cancellations, etc.)
   - Transfer reasons (missing order number, policy gaps, escalations)
4. **Explore insights** -- Automatically extracted opportunities ranked by severity:
   - Severity: high / medium / low
   - Category: routing, safety, latency, etc.
   - Description with evidence count
   - Recommended action
5. **Ask questions** -- Natural language Q&A over your transcript data
6. **Apply insights** -- One-click to create a change card from any insight
7. **Review and deploy** -- Approve the change in the Change Review page

**What Intelligence Studio extracts:**
- Procedures and FAQs from successful conversations
- Missing intents (capabilities the agent lacks)
- Workflow recommendations
- Edge cases for your eval suite

**Advanced operations:**
- `POST /api/intelligence/build` -- One-click agent generation from conversation patterns
- `POST /api/intelligence/reports/{id}/deep-research` -- Quantified root-cause analysis
- `POST /api/intelligence/reports/{id}/autonomous-loop` -- Autonomous select-draft-simulate-deploy loop
- `GET /api/intelligence/knowledge/{asset_id}` -- Access mined knowledge assets

**Example workflow:**
1. Upload `march_2026_support.zip` (1,247 conversations)
2. Review summary: 42% of refund requests routed to wrong agent
3. Click insight: "Add 'refund' keywords to billing_agent routing rules"
4. Ask: "What exact phrases are customers using?"
5. Review evidence: "money back", "reimbursement", "refund my order"
6. Apply insight -> Change card created with keyword additions
7. Approve in Change Review -> Deploy with canary

### 6.3 CX Agent Studio integration

AutoAgent has bidirectional integration with Google's Contact Center AI (CX Agent Studio).

**Importing a CX agent:**

```bash
autoagent cx import \
  --project my-gcp-project \
  --location us-central1 \
  --agent-id abc123 \
  --output-dir ./imported-agent \
  --include-test-cases
```

This pulls your CX agent's configuration into AutoAgent format, including:
- Generative settings
- Tools and tool schemas
- Examples and few-shot data
- Flow definitions
- Test cases (optional)

**Optimizing and exporting back:**

```bash
# Optimize the imported agent
autoagent optimize --cycles 10

# Export improvements back to CX format
autoagent cx export \
  --project my-gcp-project \
  --location us-central1 \
  --agent-id abc123 \
  --config-path configs/latest.yaml \
  --snapshot-path snapshots/pre-optimization.json

# Deploy to a CX environment
autoagent cx deploy \
  --project my-gcp-project \
  --location us-central1 \
  --agent-id abc123 \
  --environment PROD
```

**Generating a chat widget:**

```bash
autoagent cx widget \
  --project my-gcp-project \
  --location us-central1 \
  --agent-id abc123 \
  --title "Support Chat" \
  --color "#0066FF" \
  --output-path widget.html
```

The web UI also provides these features at `/cx/import` and `/cx/deploy`.

**CX API endpoints:**
- `GET /api/cx/agents` -- List CX agents
- `POST /api/cx/import` -- Import
- `POST /api/cx/export` -- Export
- `POST /api/cx/deploy` -- Deploy
- `POST /api/cx/widget` -- Generate widget HTML
- `GET /api/cx/status` -- Deployment status
- `GET /api/cx/preview` -- Preview before deploy

### 6.4 ADK import/export

Import agents built with Google's Agent Development Kit (ADK) from Python source:

```bash
# Import an ADK agent
autoagent adk import ./my_adk_agent --output ./imported

# Optimize it
autoagent optimize --cycles 5

# Preview what would change on export
autoagent adk diff ./my_adk_agent --snapshot snapshot.json

# Export patches back (preserves your code style and comments)
autoagent adk export ./my_adk_agent --snapshot snapshot.json --output ./patched

# Preview without writing files
autoagent adk export ./my_adk_agent --snapshot snapshot.json --dry-run

# Deploy directly to Cloud Run or Vertex AI
autoagent adk deploy ./my_adk_agent \
  --target cloud-run \
  --project my-project \
  --region us-central1
```

AutoAgent uses AST parsing to extract agent configuration from Python source code, so it understands your agent's instructions, tools, routing, and generation settings while preserving your code structure.

**ADK API endpoints:**
- `POST /api/adk/import` -- Import
- `POST /api/adk/export` -- Export
- `POST /api/adk/deploy` -- Deploy to Cloud Run or Vertex AI

### 6.5 Skill creation and management

Skills are reusable optimization strategies. Here's how to work with them:

```bash
# List available skills
autoagent skill list
autoagent skill list --category routing --platform adk

# Get recommendations based on your agent's failures
autoagent skill recommend
```

Output:

```
Recommended skills for current failure patterns:

1. routing_keyword_expansion (92% match)
   Adds missing keywords to routing rules based on failure analysis
   Expected lift: +0.08 composite score

2. timeout_tuning (78% match)
   Adjusts tool timeouts based on p95 latency data
   Expected lift: +0.04 composite score
```

```bash
# Apply a skill
autoagent skill apply routing_keyword_expansion

# Install a custom skill
autoagent skill install ./my_custom_skill.yaml

# Learn new skills from recent optimization patterns
autoagent skill learn --limit 5

# View skill effectiveness
autoagent skill stats --top 10
```

**Skills API endpoints:**
- `GET /api/skills/marketplace` -- Browse skills
- `GET /api/skills/recommend` -- Get recommendations
- `POST /api/skills/{skill_id}/apply` -- Apply a skill
- `POST /api/skills/from-optimization` -- Learn from recent optimizations
- `POST /api/skills/compose` -- Compose multiple skills
- `GET /api/skills/{skill_id}/effectiveness` -- Effectiveness tracking

### 6.6 Notifications

**Page:** `/notifications`

Configure how AutoAgent notifies you about events:

| Channel | Events |
|---------|--------|
| **Webhook** | POST to any URL on optimization complete, eval complete, safety violation, budget warning |
| **Slack** | Messages to a Slack channel |
| **Email** | Email alerts for critical events |

**Notification endpoints:**
- `POST /api/notifications/webhook` -- Create webhook subscription
- `POST /api/notifications/slack` -- Create Slack subscription
- `POST /api/notifications/email` -- Create email subscription
- `GET /api/notifications/subscriptions` -- List subscriptions
- `DELETE /api/notifications/subscriptions/{id}` -- Remove subscription
- `POST /api/notifications/test/{id}` -- Send test notification
- `GET /api/notifications/history` -- Notification history

### 6.7 Judge operations

**Page:** `/judge-ops`
**CLI:** `autoagent judges list`, `autoagent judges calibrate`, `autoagent judges drift`

The judge stack is AutoAgent's evaluation scoring pipeline. It uses a tiered approach:

**Tier 1: Deterministic** -- Pattern matching, keyword checks, schema validation. Instant, zero cost, confidence = 1.0.

**Tier 2: Similarity** -- Token-overlap Jaccard scoring against reference answers. Fast and cheap.

**Tier 3: Binary Rubric** -- LLM judge with structured yes/no rubric questions. The primary scoring layer.

**Tier 4: Audit Judge** -- A second LLM from a different model family reviews borderline cases. Catches systematic judge errors.

Higher tiers only fire when lower tiers are inconclusive, keeping costs low.

**Judge Ops features:**

| Feature | What it does |
|---------|-------------|
| **Versioning** | Track judge changes and their impact on scores |
| **Calibration** | Compare judge scores to human labels |
| **Drift monitoring** | Detect shifts in judge agreement rates over time |
| **Human feedback** | Corrections from human review improve judge accuracy |
| **Bias detection** | Identify position bias and verbosity bias in LLM judges |

**Calibrating judges:**

```bash
# Run calibration against 50 randomly sampled cases
autoagent judges calibrate --sample 50

# Calibrate a specific judge
autoagent judges calibrate --judge-id binary_rubric --sample 100

# Check for drift
autoagent judges drift
```

### 6.8 AutoFix Copilot

**Page:** `/autofix`
**CLI:** `autoagent autofix suggest`, `autoagent autofix apply <id>`, `autoagent autofix history`

AutoFix analyzes your agent's failure patterns and generates constrained improvement proposals automatically.

**How it works:**

1. AutoFix scans recent failures and groups them by root cause
2. For each group, it generates a fix proposal with root cause analysis, suggested mutation type, expected lift, and confidence score
3. You review each proposal and decide to apply or reject
4. Applied proposals create new config versions and go through the standard gating pipeline

```bash
# Generate fix proposals
autoagent autofix suggest

# Apply a proposal
autoagent autofix apply proposal_1

# View history
autoagent autofix history --limit 20
```

> **Tip:** AutoFix proposals must pass safety gates and show statistical significance before being promoted, just like regular optimization cycles.

### 6.9 Context Engineering Workbench

**Page:** `/context`
**CLI:** `autoagent context analyze`, `autoagent context simulate`, `autoagent context report`

The Context Workbench helps you understand and optimize how your agent uses its context window.

**Features:**

| Feature | What it measures |
|---------|-----------------|
| **Growth pattern detection** | Linear, exponential, sawtooth, or stable growth over conversations |
| **Utilization analysis** | What percentage of the context window is actually used |
| **Failure correlation** | Links between context state (size, staleness) and failures |
| **Compaction simulation** | Test compaction strategies before deploying |

**Simulating compaction strategies:**

```bash
autoagent context simulate --strategy aggressive
autoagent context simulate --strategy balanced
autoagent context simulate --strategy conservative
```

```bash
autoagent context report
```

### 6.10 Prompt optimization (Pro mode)

AutoAgent's pro-mode search strategy includes four research-grade prompt optimization algorithms:

#### MIPROv2

Bayesian search over (instruction, example set) pairs. Generates diverse instruction candidates, selects few-shot examples optimally, uses Bayesian optimization to explore the space efficiently. Best for: achieving maximum quality with moderate budget.

#### BootstrapFewShot

Teacher-student demonstration bootstrapping inspired by DSPy. A "teacher" model generates high-quality demonstrations; these are added as few-shot examples. Best for: improving quality when you have good reference examples.

#### GEPA

Gradient-free Evolutionary Prompt Adaptation with tournament selection. Maintains a population of prompt variants, uses crossover and mutation operators, selects winners via tournament. Best for: exploring large prompt spaces when you're far from optimal.

#### SIMBA

Simulation-Based Iterative hill-climbing. Generates small, focused mutations, tests each against simulated conversations, keeps improvements. Best for: fine-tuning when you're close to optimal.

**Enabling pro mode:**

In `autoagent.yaml`:

```yaml
optimizer:
  search_strategy: pro
```

Or via CLI:

```bash
autoagent optimize --cycles 10 --mode research
```

> **Warning:** Pro mode uses significantly more LLM calls and budget per cycle (~$1-5 per cycle vs ~$0.10-0.50 for simple mode). Start with `simple` or `adaptive` and upgrade to `pro` when you need maximum quality.

### 6.11 NL Scorer Generation

**Page:** `/scorer-studio`
**CLI:** `autoagent scorer create`, `autoagent scorer refine`, `autoagent scorer test`

Create custom evaluation scorers by describing what "good" looks like in plain English.

```bash
autoagent scorer create "The agent should acknowledge the customer's frustration, \
  look up their order, and provide a specific resolution within 3 turns" \
  --name empathetic_resolution
```

AutoAgent converts this into a structured `ScorerSpec` with named dimensions (empathy, order_lookup, resolution_specificity, conversation_length), rubric criteria, and weight distribution.

```bash
# Refine a scorer
autoagent scorer refine empathetic_resolution "Also check that the agent doesn't use jargon"

# Test against a real trace
autoagent scorer test empathetic_resolution --trace tr_abc123

# List all scorers
autoagent scorer list
```

### 6.12 Dataset Management

AutoAgent manages eval datasets with four types:

| Type | Description |
|------|-------------|
| **Golden** | Curated, high-confidence test cases |
| **Rolling holdout** | Automatically rotated to prevent overfitting |
| **Challenge / adversarial** | Edge cases and adversarial inputs |
| **Live failure queue** | Bad production traces converted to eval cases automatically |

The `dataset` command manages all of these:

```bash
autoagent dataset --help
```

**Dataset API endpoints:**
- `GET /api/datasets/{dataset_id}` -- Dataset details
- `POST /api/datasets/{dataset_id}/rows` -- Add rows
- `POST /api/datasets/{dataset_id}/versions` -- Create version
- `POST /api/datasets/{dataset_id}/splits` -- Create train/test splits
- `POST /api/datasets/{dataset_id}/export` -- Export dataset
- `POST /api/datasets/{dataset_id}/import/traces` -- Import from traces
- `POST /api/datasets/{dataset_id}/import/eval-cases` -- Import from eval cases

### 6.13 Policy Optimization and Reward Systems

For teams running RLHF-style reward model training, AutoAgent includes a full policy optimization subsystem.

**Reward definitions:**

```bash
# Define a reward function
autoagent reward --help

# List reward definitions
# View reward definitions via API
# GET /api/rewards/{name}
```

**RLHF preference collection:**

```bash
# Export preference pairs for fine-tuning
autoagent pref --help
```

**Policy optimization (RL loop):**

```bash
# Run RL training job
autoagent rl --help
```

**The RL pipeline:**

1. Collect human preference pairs (Preference Inbox)
2. Train reward model (Reward Studio)
3. Define policy candidates (Policy Candidates)
4. Evaluate with OPE (off-policy evaluation)
5. Canary deploy a policy candidate
6. Promote or rollback based on production metrics

**RL API endpoints:**
- `POST /api/rl/datasets/build` -- Build training dataset
- `POST /api/rl/train` -- Start training job
- `GET /api/rl/jobs` -- List jobs
- `GET /api/rl/policies` -- List trained policies
- `POST /api/rl/evaluate` -- Evaluate a policy
- `POST /api/rl/ope` -- Off-policy evaluation
- `POST /api/rl/canary` -- Canary deploy a policy
- `POST /api/rl/promote` -- Promote to production
- `POST /api/rl/rollback` -- Rollback policy

### 6.14 Blame Map

**Page:** `/blame`
**CLI:** `autoagent trace blame`

The Blame Map clusters failures by root cause and visualizes them as an impact-scored hierarchy.

Each cluster shows:
- Failure family (e.g., "billing_misroute", "tool_timeout", "safety_pii_leak")
- Occurrence count and frequency trend
- Impact score (frequency x severity x business impact)
- Example traces
- Recommended mutation operators

The blame map is the primary input to the optimizer's opportunity queue.

### 6.15 Change Review

**Page:** `/changes`
**CLI:** `autoagent review list`, `autoagent review show`, `autoagent review apply`, `autoagent review reject`

A review queue for proposed configuration changes. Changes land here from:
- AutoFix proposals
- Agent Studio edits
- Intelligence Studio insights
- Manual optimizer proposals

### 6.16 Runbooks

**Page:** `/runbooks`
**CLI:** `autoagent runbook list`, `autoagent runbook show`, `autoagent runbook apply`, `autoagent runbook create`

Runbooks are curated bundles of skills, policies, and tools that solve specific problems. Pre-built runbooks:

- `enhance-few-shot-examples` -- Add diverse few-shot examples
- `fix-retrieval-grounding` -- Improve RAG accuracy
- `improve-routing-accuracy` -- Add missing routing keywords
- `optimize-cost-efficiency` -- Reduce per-conversation cost
- `reduce-tool-latency` -- Tune timeouts and caching
- `stabilize-multilingual-support` -- Fix multilingual routing
- `tighten-safety-policy` -- PII guardrails + toxicity filters

```bash
autoagent runbook apply tighten-safety-policy

# Create a custom runbook
autoagent runbook create my-playbook --file runbook.yaml
```

### 6.17 Project Memory

**Page:** `/memory`
**CLI:** `autoagent memory show`, `autoagent memory add`

AutoAgent maintains a persistent project memory file (`AUTOAGENT.md`) that tracks:
- Key decisions and their rationale
- Known issues and workarounds
- Configuration notes
- Important context that should persist across optimization cycles

```bash
autoagent memory show
autoagent memory add "Billing routing was redesigned on 2026-03-15" --section decisions
```

**Memory API endpoints:**
- `GET /api/memory/` -- Show project memory
- `PUT /api/memory/` -- Update project memory
- `POST /api/memory/note` -- Add a note
- `GET /api/memory/context` -- Get context summary

### 6.18 MCP Server integration

AutoAgent includes a Model Context Protocol (MCP) server that exposes its capabilities to AI coding assistants like Claude Code, Cursor, and Windsurf.

```bash
autoagent mcp-server
```

**Configuring Claude Code:**

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

**Available MCP tools (10):**

| Tool | What it does |
|------|-------------|
| `status` | Get agent health metrics |
| `eval_run` | Trigger an evaluation |
| `optimize` | Run optimization cycles |
| `config_list` | List config versions |
| `config_show` | Show a config version |
| `config_diff` | Diff two versions |
| `deploy` | Deploy a version |
| `conversations_list` | List conversations |
| `trace_grade` | Grade a trace |
| `memory_show` | Show project memory |

### 6.19 Building agents from natural language

The `build` command creates a new agent artifact from a natural language description:

```bash
autoagent build "A customer support bot for an e-commerce platform \
  that handles orders, returns, and billing questions" \
  --connector Shopify --connector Stripe \
  --output-dir ./my-agent
```

Options:
- `--connector` -- Include named connectors (repeatable)
- `--output-dir` -- Directory for generated artifacts
- `--json` -- Output as JSON

This generates eval cases, config scaffold, and deploy handoff files.

### 6.20 Sandbox and What-If analysis

**Sandbox** (`/sandbox`):
- Generate diverse user personas with different intents, communication styles, and edge cases
- Run stress testing with high-volume synthetic conversations
- Compare agent behavior across configuration variants

**What-If** (`/what-if`):
- Replay historical conversations with a different configuration
- Project what would happen if you deployed a candidate config to production
- Use before high-risk production pushes

**Sandbox API endpoints:**
- `POST /api/sandbox/generate` -- Generate synthetic conversations
- `POST /api/sandbox/test` -- Run scenario testing
- `POST /api/sandbox/compare` -- Compare configurations
- `GET /api/sandbox/results/{result_id}` -- Get results

**What-If API endpoints:**
- `POST /api/what-if/replay` -- Replay traces with a different config
- `POST /api/what-if/project` -- Project production impact
- `GET /api/what-if/jobs` -- List jobs

---

## Chapter 7: CLI Reference

### 7.1 Command structure

```
autoagent <command> [subcommand] [options]
```

All commands support `--help`. Major commands support `--json` for structured output.

The CLI has **112 commands** across 30+ groups. Every command is implemented in `runner.py`.

### 7.2 Core commands with full examples

#### `autoagent init`

```bash
autoagent init                                    # Scaffold with customer-support template
autoagent init --template minimal                 # Minimal scaffold
autoagent init --dir ./my-agent-project           # Scaffold in specific directory
```

#### `autoagent server`

```bash
autoagent server                                  # Start with defaults (localhost:8000)
autoagent server --host 0.0.0.0 --port 9000       # Custom host and port
autoagent server --reload                         # Development mode with auto-reload
```

#### `autoagent status`

```bash
autoagent status                                  # Standard output
autoagent status --json                           # JSON output for scripting
autoagent status --db /path/to/db --configs-dir ./configs
```

#### `autoagent doctor`

```bash
autoagent doctor                                  # Run full diagnostics
autoagent doctor --config ./my-config.yaml        # Check a specific config file
```

#### `autoagent quickstart`

```bash
autoagent quickstart                              # Full golden path
autoagent quickstart --agent-name "Acme Bot" --open --verbose
```

#### `autoagent build`

```bash
autoagent build "A support bot for e-commerce that handles billing"
autoagent build "A medical triage bot" --connector EHR --output-dir ./medical-bot
autoagent build "..." --json                      # JSON output
```

#### `autoagent autonomous`

```bash
autoagent autonomous --scope dev --cycles 3
autoagent autonomous --scope staging --yes --max-loop-cycles 10
```

> **Warning:** `full-auto` and `autonomous` reduce human oversight. Use only in sandboxed environments.

#### `autoagent benchmark`

```bash
autoagent benchmark run <benchmark_name>
autoagent benchmark run routing-accuracy --cycles 3
```

### 7.3 Eval commands with full examples

```bash
# Run eval against active config
autoagent eval run

# Run with specific config and output file
autoagent eval run --config configs/v003.yaml --output results.json

# Run only safety category
autoagent eval run --category safety --output safety-results.json

# Run against a dataset
autoagent eval run --dataset data/test_cases.jsonl --split test

# View results from file
autoagent eval results --file results.json

# View results by run ID
autoagent eval results --run-id run_abc123

# List all historical runs
autoagent eval list
```

### 7.4 Optimize and loop commands with full examples

```bash
# Single optimization cycle (standard mode)
autoagent optimize

# Multiple cycles
autoagent optimize --cycles 10

# Research-grade mode (MIPROv2, BootstrapFewShot, GEPA, SIMBA)
autoagent optimize --cycles 5 --mode research

# Advanced adaptive mode
autoagent optimize --cycles 5 --mode advanced

# Continuous loop with plateau detection
autoagent loop --max-cycles 50 --stop-on-plateau

# Loop with 5-minute intervals
autoagent loop --schedule interval --interval-minutes 5

# Loop with cron schedule
autoagent loop --schedule cron --cron "*/10 * * * *"

# Resume from checkpoint
autoagent loop --resume --checkpoint-file .autoagent/loop_checkpoint.json

# Human control
autoagent pause
autoagent resume
autoagent pin safety_instructions
autoagent pin routing
autoagent unpin routing
autoagent reject exp_a1b2c3
```

### 7.5 Config commands with full examples

```bash
# List all versions
autoagent config list

# Show active version
autoagent config show

# Show specific version
autoagent config show v3

# Diff two versions
autoagent config diff v1 v5

# Migrate old config format
autoagent config migrate old-config.yaml --output new-config.yaml
```

### 7.6 Deploy commands with full examples

```bash
# Canary deploy (default)
autoagent deploy --config-version v5

# Immediate deploy
autoagent deploy --config-version v5 --strategy immediate

# Deploy to CX Studio
autoagent deploy --config-version 3 --strategy canary --target cx-studio \
  --project my-project --location us-central1 --agent-id abc123

# View history
autoagent replay --limit 20
```

### 7.7 Trace commands with full examples

```bash
# Grade a trace
autoagent trace grade tr_abc123

# Blame map for last 24 hours
autoagent trace blame --window 24h --top 10

# Blame map for last week
autoagent trace blame --window 7d --top 20

# Render trace graph
autoagent trace graph tr_abc123
```

### 7.8 Natural language commands with full examples

```bash
# Edit agent config with natural language
autoagent edit "Make the agent more concise"
autoagent edit "Add safety guardrails for PII" --dry-run
autoagent edit "Improve billing routing accuracy" --json
autoagent edit --interactive  # Interactive mode with confirmation

# Get a plain-English explanation of agent health
autoagent explain
autoagent explain --verbose
autoagent explain --json

# Interactive diagnosis
autoagent diagnose
autoagent diagnose --interactive
autoagent diagnose --json
```

### 7.9 ADK commands with full examples

```bash
# Import from local directory
autoagent adk import ./my_adk_agent --output ./imported

# Preview changes before export
autoagent adk diff ./my_adk_agent --snapshot snapshot.json

# Export optimized config back
autoagent adk export ./my_adk_agent --snapshot snapshot.json --output ./patched
autoagent adk export ./my_adk_agent --snapshot snapshot.json --dry-run  # Preview only

# Show agent structure summary
autoagent adk status ./my_adk_agent
autoagent adk status ./my_adk_agent --json

# Deploy to cloud
autoagent adk deploy ./my_adk_agent --target cloud-run --project my-project --region us-central1
autoagent adk deploy ./my_adk_agent --target vertex-ai --project my-project --region us-central1
```

### 7.10 CX commands with full examples

```bash
# List CX agents
autoagent cx list --project my-project --location us-central1

# Import
autoagent cx import --project my-project --location us-central1 --agent-id abc123 \
  --output-dir ./imported --include-test-cases

# Export
autoagent cx export --project my-project --location us-central1 --agent-id abc123 \
  --config-path configs/latest.yaml --snapshot-path snapshot.json

# Deploy
autoagent cx deploy --project my-project --location us-central1 \
  --agent-id abc123 --environment PROD

# Generate widget
autoagent cx widget --project my-project --location us-central1 --agent-id abc123 \
  --title "Support Chat" --color "#0066FF" --output-path widget.html

# Check status
autoagent cx status --project my-project --location us-central1 --agent-id abc123
```

### 7.11 Policy optimization commands with full examples

```bash
# Manage reward definitions
autoagent reward --help

# Policy optimization
autoagent rl --help

# Preference collection
autoagent pref --help

# Curriculum generator for adversarial evals
autoagent curriculum --help

# Dataset management
autoagent dataset --help

# Outcome data ingestion
autoagent outcomes --help
```

### 7.12 Common workflows

#### Workflow A: Quick health check

```bash
autoagent status
autoagent explain --verbose
```

#### Workflow B: Fix a specific problem

```bash
autoagent diagnose --interactive
# Review the top issue
# Type "fix" to apply the suggested fix
# Check the improvement
autoagent status
```

#### Workflow C: Full optimization cycle

```bash
autoagent eval run --output baseline.json
autoagent optimize --cycles 5
autoagent eval run --output after.json
autoagent config diff v1 v6
autoagent deploy --config-version v6 --strategy canary
```

#### Workflow D: Overnight optimization

```bash
autoagent loop --max-cycles 50 --stop-on-plateau --schedule interval --interval-minutes 5
# Leave running overnight
# Check results in the morning:
autoagent status
autoagent replay --limit 50
```

#### Workflow E: Import, optimize, export (CX)

```bash
autoagent cx import --project my-project --location us-central1 --agent-id abc123 --output-dir ./imported
autoagent optimize --cycles 10
autoagent cx export --project my-project --location us-central1 --agent-id abc123 \
  --config-path configs/latest.yaml --snapshot-path snapshot.json
autoagent cx deploy --project my-project --location us-central1 --agent-id abc123 --environment PROD
```

#### Workflow F: RLHF policy loop

```bash
# Collect preferences
autoagent pref --help  # Set up preference collection

# Train reward model
autoagent reward --help

# Run RL training
autoagent rl --help

# Evaluate and promote policy
# Use Policy Candidates UI at /policy-candidates
```

### 7.13 Tips and tricks

1. **Pipe JSON output to jq** for filtering:
   ```bash
   autoagent status --json | jq '.failure_breakdown'
   autoagent eval results --run-id abc --json | jq '.cases[] | select(.passed == false)'
   ```

2. **Use `--dry-run` with `autoagent edit`** to preview changes without applying:
   ```bash
   autoagent edit "Rewrite all instructions to be more concise" --dry-run
   ```

3. **Set environment variables** for custom paths:
   ```bash
   AUTOAGENT_DB=./custom/conversations.db autoagent status
   ```

4. **Use `autoagent doctor`** when something seems wrong:
   ```bash
   autoagent doctor  # Checks config, database, API keys, eval suite
   ```

5. **Chain commands** for automated scripts:
   ```bash
   autoagent eval run --output pre.json && \
   autoagent optimize --cycles 3 && \
   autoagent eval run --output post.json && \
   echo "Optimization complete"
   ```

---

## Chapter 8: Troubleshooting

### 8.1 Common errors and fixes

#### Setup and installation

| Error | Cause | Fix |
|-------|-------|-----|
| `Permission denied: ./setup.sh` | Scripts not executable | `chmod +x setup.sh start.sh stop.sh` |
| `Python 3.11+ required` | Old Python version | `brew install python@3.12` or download from python.org |
| `Node.js 18+ required` | Old Node version | `brew install node` or `nvm install 20 && nvm use 20` |
| `pip install failed` | Missing build dependencies | `pip install -e '.[dev]' --verbose` to see what's failing |
| `npm install failed` | Node/npm corruption | `rm -rf web/node_modules && cd web && npm install` |

#### Starting AutoAgent

| Error | Cause | Fix |
|-------|-------|-----|
| `Port 8000 in use` | Previous process still running | `./stop.sh && ./start.sh` |
| `Port 5173 in use` | Previous frontend process | `./stop.sh && ./start.sh` |
| `Setup hasn't been run yet` | Missing `.venv` directory | Run `./setup.sh` first |
| `Backend already running` | Stale PID file | `./stop.sh` then `./start.sh` |
| `ModuleNotFoundError` | Virtual env not activated | `source .venv/bin/activate && pip install -e '.[dev]'` |
| `Backend starts but frontend doesn't load` | npm issue | `cat .autoagent/frontend.log` then `cd web && npm install` |

#### Runtime errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Dashboard empty` | No conversation data | Run `autoagent demo vp` to seed demo data, or run an eval |
| `Eval detail stuck in "running"` | Task stalled | Check task state: `curl http://localhost:8000/api/tasks/{task_id}` |
| `Deploy history empty` | No deployments yet | Deploy a config version first |
| `No real-time updates` | WebSocket disconnected | Refresh the page; check if backend is running at `/ws` |
| `Optimization rejected: no improvement` | Candidate didn't improve scores | Normal -- try more cycles or switch search strategy |
| `Budget exhausted` | Daily limit reached | Increase `daily_dollars` in `autoagent.yaml` |
| `Stall detected` | No improvement in N cycles | Try a different search strategy or review failure patterns manually |

#### API key issues

| Error | Cause | Fix |
|-------|-------|-----|
| `Mock mode active` | No API keys configured | Add keys to `.env` file (optional -- mock mode works for exploration) |
| `401 Unauthorized` from LLM | Invalid API key | Check that the key in `.env` is valid and not expired |
| `429 Rate Limited` | Too many requests | Reduce `per_cycle_dollars` or add a `--delay` to loop |

### 8.2 FAQ

**Q: Do I need API keys to use AutoAgent?**
A: No. AutoAgent runs in mock mode by default, using deterministic responses. You can explore every feature without API keys. Add keys when you're ready for real optimization.

**Q: How much does it cost to run?**
A: In mock mode, $0. With real LLM providers: `simple` strategy ~$0.10-0.50 per cycle; `adaptive` ~$0.20; `full` ~$0.50; `pro` ~$1-5. Budget controls prevent overspending.

**Q: Can I undo an optimization?**
A: Yes. Every optimization creates a versioned config. Use `autoagent config show v<N>` to view any version, and `autoagent deploy --config-version v<N>` to rollback. You can also reject specific experiments with `autoagent reject <id>`.

**Q: Can I use AutoAgent with my existing agent?**
A: Yes. Import agents from Google CX Agent Studio or Google ADK. You can also write your own config YAML following the schema in `agent/config/`.

**Q: What LLM providers does AutoAgent support?**
A: Google Gemini (2.5 Pro, 2.5 Flash), OpenAI (GPT-4o, GPT-4o-mini, o1, o3), Anthropic (Claude Sonnet 4.5, Claude Haiku 3.5), any OpenAI-compatible endpoint, and a mock provider for testing.

**Q: How do I configure multiple LLM providers?**
A: In `autoagent.yaml`:

```yaml
optimizer:
  models:
    - provider: google
      model: gemini-2.5-pro
      api_key_env: GOOGLE_API_KEY
    - provider: openai
      model: gpt-4o
      api_key_env: OPENAI_API_KEY
    - provider: anthropic
      model: claude-sonnet-4-5
      api_key_env: ANTHROPIC_API_KEY
```

**Q: How long should I run the optimization loop?**
A: For a new agent, 10-20 cycles usually shows significant improvement. For fine-tuning, 50+ cycles with `--stop-on-plateau`. The loop is designed for multi-day unattended operation.

**Q: What happens if the optimization loop crashes?**
A: AutoAgent checkpoints after every cycle. Restart with `autoagent loop --resume` and it picks up where it left off. Failed cycles go to a dead letter queue for inspection.

**Q: How do I keep the optimizer from changing certain things?**
A:
```bash
autoagent pin safety_instructions
autoagent pin model
```
For permanent protection:
```yaml
human_control:
  immutable_surfaces: ["safety_instructions"]
```

**Q: Can I run AutoAgent in Docker?**
A:
```bash
docker build -t autoagent .
docker run -p 8000:8000 --env-file .env autoagent
```
Or: `docker compose up --build -d`

**Q: Can I deploy AutoAgent to the cloud?**
A: Yes. Supports Docker on any container host, Google Cloud Run, and Fly.io (`fly launch`).

**Q: What's the difference between `simple`, `adaptive`, `full`, and `pro` search strategies?**
A: See the Search Strategy Comparison table in Appendix A.8.

### 8.3 Where to get help

- **API Documentation** -- `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc` (ReDoc)
- **CLI Help** -- `autoagent --help` or `autoagent <command> --help`
- **Source Docs** -- See `docs/` directory: Platform Overview, Architecture, Core Concepts, CLI Reference, API Reference

---

## Appendix

### A.1 Glossary of terms

| Term | Definition |
|------|-----------|
| **Agent** | An AI system that receives messages, processes them with an LLM, and generates responses |
| **Agent config** | The YAML file defining an agent's instructions, tools, routing, and settings |
| **Blame map** | A visualization of failure clusters organized by root cause and impact |
| **Canary deployment** | Deploying a new config to a percentage of traffic before promoting to 100% |
| **Composite score** | A weighted combination of quality, safety, latency, and cost metrics |
| **Dead letter queue** | A store for failed optimization cycles that can be inspected and retried |
| **Eval** | An evaluation run that tests agent performance against a suite of test cases |
| **Eval case** | A single test case in the eval suite (input + expected output or criteria) |
| **Experiment card** | A structured audit record of an optimization attempt |
| **Few-shot examples** | Example conversations included in the prompt to guide agent behavior |
| **Gate** | A check that must pass before a mutation can be deployed |
| **Hard gate** | A non-negotiable check (e.g., safety) that immediately rejects if failed |
| **Holdout set** | A rotating subset of eval cases withheld from optimization for unbiased validation |
| **Immutable surface** | A config surface permanently locked from mutation |
| **Judge** | A scoring component in the evaluation pipeline |
| **Loop** | The continuous optimization cycle |
| **Metric hierarchy** | The 4-layer system for organizing and prioritizing metrics |
| **Mutation** | A specific, typed change to agent configuration |
| **Mutation surface** | The part of config being changed (instruction, routing, model, etc.) |
| **North-star outcomes** | Primary metrics being optimized (task success, user satisfaction) |
| **Observation window** | How far back the optimizer looks for conversation data |
| **Operating SLO** | An operational guardrail that must not be violated |
| **Opportunity** | A ranked optimization target from the blame map |
| **OPE** | Off-policy evaluation -- evaluating a policy without deploying it |
| **Pareto frontier** | The set of configs optimal across multiple metrics simultaneously |
| **Pinned surface** | A config surface temporarily locked from mutation via `autoagent pin` |
| **Proposal** | A candidate mutation generated by the optimizer |
| **Risk class** | The risk level of a mutation: low, medium, high, or critical |
| **Rollback** | Reverting to a previous config version |
| **RLHF** | Reinforcement Learning from Human Feedback |
| **Runbook** | A curated bundle of skills, policies, and tools for a specific scenario |
| **Scorer** | A custom evaluation metric created from natural language descriptions |
| **Search strategy** | The algorithm used to generate mutation candidates (simple, adaptive, full, pro) |
| **Skill** | A reusable optimization strategy (build-time) or agent capability (run-time) |
| **Span** | A single unit in a trace tree (e.g., one tool call, one agent turn) |
| **Stall** | When the optimization loop stops improving after N consecutive cycles |
| **Statistical significance** | The confidence level that an improvement is real (p-value) |
| **Trace** | Structured telemetry from an agent invocation |
| **Watchdog** | A monitor that detects stuck optimization cycles |

### A.2 Keyboard shortcuts

#### Global shortcuts (work anywhere except in form fields)

| Shortcut | Action |
|----------|--------|
| `Cmd+K` / `Ctrl+K` | Open command palette |
| `n` | Open new eval flow |
| `o` | Open optimize flow |
| `d` | Open deploy flow |

#### Command palette

The command palette (`Cmd+K`) provides quick access to:
- Static actions: new eval, optimize, deploy, dashboard, conversations
- Recent eval runs
- Recent config versions
- Recent conversations

### A.3 API endpoints reference

AutoAgent serves **200+ REST API endpoints** across **39 route modules**. Here is the complete endpoint inventory:

#### Health (`/api/health`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health/ready` | Readiness check |
| GET | `/api/health/system` | System operational health |
| GET | `/api/health/cost` | Cost tracking summary |
| GET | `/api/health/eval-set` | Eval set health check |
| GET | `/api/health/scorecard` | Detailed scorecard with metric breakdown |

#### Eval (`/api/eval`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/eval/run` | Start an evaluation run |
| GET | `/api/eval/runs` | List eval runs |
| GET | `/api/eval/runs/{run_id}` | Get eval run details |
| GET | `/api/eval/runs/{run_id}/cases` | Get per-case results |
| GET | `/api/eval/history` | Full eval history |
| GET | `/api/eval/history/{run_id}` | Specific history entry |

#### Optimize (`/api/optimize`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/optimize/run` | Start optimization cycles |
| GET | `/api/optimize/history` | List optimization attempts |
| GET | `/api/optimize/history/{attempt_id}` | Specific attempt details |
| GET | `/api/optimize/pareto` | Pareto frontier snapshot |
| GET | `/api/optimize/stream` | SSE stream for live progress |

#### Loop (`/api/loop`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/loop/start` | Start continuous loop |
| POST | `/api/loop/stop` | Stop the loop |
| GET | `/api/loop/status` | Loop status and cycle history |

#### Config (`/api/config`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config/list` | List config versions |
| GET | `/api/config/show/{version}` | Show config version YAML |
| GET | `/api/config/diff` | Diff two versions |
| GET | `/api/config/active` | Get active version |

#### Deploy (`/api/deploy`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/deploy/status` | Current deployment status |
| POST | `/api/deploy/rollback` | Rollback canary deployment |

#### Conversations (`/api/conversations`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/conversations` | List conversations with filters |
| GET | `/api/conversations/stats` | Aggregate stats |
| GET | `/api/conversations/{conversation_id}` | Single conversation |

#### Traces (`/api/traces`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/traces/recent` | Recent traces |
| GET | `/api/traces/search` | Search traces |
| GET | `/api/traces/errors` | Error traces |
| GET | `/api/traces/blame` | Failure clustering |
| GET | `/api/traces/sessions/{session_id}` | Traces by session |
| GET | `/api/traces/{trace_id}` | Single trace |
| GET | `/api/traces/{trace_id}/grades` | Grading results |
| GET | `/api/traces/{trace_id}/graph` | Span graph |

#### Experiments (`/api/experiments`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/experiments/stats` | Experiment statistics |
| GET | `/api/experiments/archive` | Archived experiments |
| GET | `/api/experiments/pareto` | Pareto-optimal experiments |
| GET | `/api/experiments/judge-calibration` | Judge calibration data |
| GET | `/api/experiments/{experiment_id}` | Experiment detail |

#### AutoFix (`/api/autofix`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/autofix/proposals` | List fix proposals |
| POST | `/api/autofix/apply/{id}` | Apply a proposal |

#### Judges (`/api/judges`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/judges/feedback` | Submit human feedback |
| GET | `/api/judges/calibration` | Calibration data |
| GET | `/api/judges/drift` | Drift monitoring |

#### Context (`/api/context`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/context/analysis/{trace_id}` | Analyze context for a trace |
| POST | `/api/context/simulate` | Simulate compaction |
| GET | `/api/context/report` | Context health report |

#### Registry (`/api/registry`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/registry/search` | Search registry |
| POST | `/api/registry/import` | Bulk import |
| GET | `/api/registry/{item_type}` | List by type |
| GET | `/api/registry/{item_type}/{name}` | Get item |
| GET | `/api/registry/{item_type}/{name}/diff` | Diff versions |
| POST | `/api/registry/{item_type}` | Add new item |

#### Scorers (`/api/scorers`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/scorers/create` | Create from NL description |
| GET | `/api/scorers/{name}` | Get scorer |
| POST | `/api/scorers/{name}/refine` | Add criteria |
| POST | `/api/scorers/{name}/test` | Test against trace |

#### Skills (`/api/skills`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/skills/recommend` | Get recommendations |
| GET | `/api/skills/stats` | Usage statistics |
| POST | `/api/skills/compose` | Compose multiple skills |
| GET | `/api/skills/marketplace` | Browse marketplace |
| POST | `/api/skills/install` | Install from file |
| POST | `/api/skills/search` | Search skills |
| POST | `/api/skills/from-conversation` | Learn from conversation |
| POST | `/api/skills/from-optimization` | Learn from optimization |
| GET | `/api/skills/drafts` | List skill drafts |
| POST | `/api/skills/{skill_id}/promote` | Promote to stable |
| POST | `/api/skills/{skill_id}/archive` | Archive skill |
| GET | `/api/skills/{skill_id}` | Get skill |
| PUT | `/api/skills/{skill_id}` | Update skill |
| DELETE | `/api/skills/{skill_id}` | Delete skill |
| POST | `/api/skills/{skill_id}/test` | Test skill |
| POST | `/api/skills/{skill_id}/apply` | Apply skill |
| GET | `/api/skills/{skill_id}/effectiveness` | Effectiveness data |

#### Intelligence Studio (`/api/intelligence`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/intelligence/archive` | Upload transcript archive |
| GET | `/api/intelligence/reports` | List reports |
| GET | `/api/intelligence/reports/{report_id}` | Report details |
| POST | `/api/intelligence/reports/{id}/ask` | Q&A over transcripts |
| POST | `/api/intelligence/reports/{id}/apply` | Create change card |
| POST | `/api/intelligence/build` | Build agent from patterns |
| GET | `/api/intelligence/knowledge/{asset_id}` | Mined knowledge asset |
| POST | `/api/intelligence/reports/{id}/deep-research` | Deep analysis |
| POST | `/api/intelligence/reports/{id}/autonomous-loop` | Autonomous loop |

#### Agent Studio (`/api/edit`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/edit` | Apply natural language config edit |

#### CX Integration (`/api/cx`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cx/agents` | List CX agents |
| POST | `/api/cx/import` | Import CX agent |
| POST | `/api/cx/export` | Export to CX format |
| POST | `/api/cx/deploy` | Deploy to CX environment |
| POST | `/api/cx/widget` | Generate widget HTML |
| GET | `/api/cx/status` | Deployment status |
| GET | `/api/cx/preview` | Preview before deploy |

#### ADK Integration (`/api/adk`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/adk/import` | Import ADK agent |
| POST | `/api/adk/export` | Export to ADK format |
| POST | `/api/adk/deploy` | Deploy ADK agent |

#### Human Control (`/api/control`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/control/state` | Get pause/pin state |
| POST | `/api/control/pause` | Pause the optimizer |
| POST | `/api/control/resume` | Resume the optimizer |
| POST | `/api/control/pin/{surface}` | Pin a surface |
| POST | `/api/control/unpin/{surface}` | Unpin a surface |
| POST | `/api/control/reject/{experiment_id}` | Reject an experiment |
| POST | `/api/control/inject` | Inject synthetic event |

#### Policy Optimization (`/api/rl`, `/api/rewards`, `/api/preferences`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/rl/datasets/build` | Build RL training dataset |
| POST | `/api/rl/train` | Start RL training job |
| GET | `/api/rl/jobs` | List training jobs |
| GET | `/api/rl/jobs/{job_id}` | Job details |
| GET | `/api/rl/policies` | List trained policies |
| GET | `/api/rl/policies/{policy_id}` | Policy details |
| POST | `/api/rl/evaluate` | Evaluate a policy |
| POST | `/api/rl/ope` | Off-policy evaluation |
| POST | `/api/rl/canary` | Canary deploy policy |
| POST | `/api/rl/promote` | Promote policy |
| POST | `/api/rl/rollback` | Rollback policy |
| GET | `/api/rewards/{name}` | Get reward definition |
| POST | `/api/rewards/{name}/test` | Test reward |
| GET | `/api/rewards/hard-gates/list` | List hard gates |
| POST | `/api/rewards/{name}/audit` | Audit reward |
| POST | `/api/rewards/challenge/run` | Run challenge suite |
| POST | `/api/preferences/pairs` | Submit preference pairs |
| GET | `/api/preferences/pairs` | List preference pairs |
| GET | `/api/preferences/stats` | Preference stats |
| POST | `/api/preferences/export` | Export for fine-tuning |

#### Memory (`/api/memory`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/memory/` | Show project memory |
| PUT | `/api/memory/` | Update project memory |
| POST | `/api/memory/note` | Add a note |
| GET | `/api/memory/context` | Get context summary |

#### Notifications (`/api/notifications`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/notifications/webhook` | Create webhook subscription |
| POST | `/api/notifications/slack` | Create Slack subscription |
| POST | `/api/notifications/email` | Create email subscription |
| GET | `/api/notifications/subscriptions` | List subscriptions |
| DELETE | `/api/notifications/subscriptions/{id}` | Remove subscription |
| POST | `/api/notifications/test/{id}` | Test delivery |
| GET | `/api/notifications/history` | Notification history |

#### Datasets (`/api/datasets`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/datasets/{dataset_id}` | Dataset details |
| POST | `/api/datasets/{dataset_id}/rows` | Add rows |
| POST | `/api/datasets/{dataset_id}/versions` | Create version |
| GET | `/api/datasets/{dataset_id}/versions` | List versions |
| GET | `/api/datasets/{dataset_id}/rows` | Get rows |
| GET | `/api/datasets/{dataset_id}/stats` | Dataset stats |
| POST | `/api/datasets/{dataset_id}/import/traces` | Import from traces |
| POST | `/api/datasets/{dataset_id}/import/eval-cases` | Import from eval cases |
| POST | `/api/datasets/{dataset_id}/splits` | Create splits |
| POST | `/api/datasets/{dataset_id}/export` | Export dataset |
| POST | `/api/datasets/{dataset_id}/pins` | Pin dataset version |
| GET | `/api/datasets/{dataset_id}/pins` | List pins |

#### Outcomes (`/api/outcomes`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/outcomes/batch` | Batch ingest outcomes |
| GET | `/api/outcomes/stats` | Outcome statistics |
| POST | `/api/outcomes/webhook` | Webhook ingestion |
| POST | `/api/outcomes/import/csv` | CSV import |
| POST | `/api/outcomes/recalibrate/judges` | Recalibrate judges |
| POST | `/api/outcomes/recalibrate/skills` | Recalibrate skills |

#### Sandbox & What-If

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sandbox/generate` | Generate synthetic conversations |
| GET | `/api/sandbox/conversations/{set_id}` | Get conversation set |
| POST | `/api/sandbox/test` | Run scenario test |
| POST | `/api/sandbox/compare` | Compare configurations |
| GET | `/api/sandbox/results/{result_id}` | Get test results |
| POST | `/api/what-if/replay` | Replay with different config |
| GET | `/api/what-if/results/{job_id}` | Get replay results |
| POST | `/api/what-if/project` | Project production impact |
| GET | `/api/what-if/jobs` | List jobs |

#### Curriculum (`/api/curriculum`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/curriculum/generate` | Generate adversarial prompts |
| GET | `/api/curriculum/batches` | List batches |
| GET | `/api/curriculum/batches/{batch_id}` | Batch details |
| POST | `/api/curriculum/apply` | Apply curriculum to eval suite |

#### Opportunities & Runbooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/opportunities/count` | Count open opportunities |
| GET | `/api/opportunities/{opportunity_id}` | Opportunity details |
| POST | `/api/opportunities/{opportunity_id}/status` | Update status |
| GET | `/api/runbooks/` | List runbooks |
| GET | `/api/runbooks/search` | Search runbooks |
| GET | `/api/runbooks/{name}` | Get runbook |
| POST | `/api/runbooks/` | Create runbook |
| POST | `/api/runbooks/{name}/apply` | Apply runbook |

#### Knowledge & Impact

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/knowledge/mine` | Mine successful conversations |
| GET | `/api/knowledge/entries` | List knowledge entries |
| POST | `/api/knowledge/apply/{pattern_id}` | Apply pattern |
| PUT | `/api/knowledge/review/{pattern_id}` | Review/approve pattern |
| POST | `/api/impact/analyze` | Analyze change impact |
| GET | `/api/impact/dependencies` | Dependency graph |
| GET | `/api/impact/report/{analysis_id}` | Impact report |

#### Real-time

| Method | Endpoint | Description |
|--------|----------|-------------|
| WS | `/ws` | WebSocket for live updates |
| GET | `/api/events` | Server-Sent Events stream |

#### Builder

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/builder/demo/acts` | List demo acts |
| GET | `/api/builder/demo/status` | Demo status |
| POST | `/api/builder/demo/seed` | Load demo data |
| POST | `/api/builder/demo/reset` | Clear demo data |
| POST | `/api/builder/demo/acts/{id}/play` | Play a demo act |

#### Diagnose & QuickFix

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/diagnose/chat` | Conversational diagnosis |
| POST | `/api/quickfix` | Quick single-step fix |

> **Tip:** Full interactive API docs are available at `http://localhost:8000/docs` (Swagger UI) when the server is running.

### A.4 Configuration reference

The main configuration file is `autoagent.yaml` at the project root:

```yaml
# ─── Optimizer settings ──────────────────────────────────────────────
optimizer:
  use_mock: true                      # Use mock providers (no API key needed)
  strategy: round_robin               # LLM routing: single, round_robin, ensemble, mixture
  search_strategy: simple             # Mutation search: simple, adaptive, full, pro
  holdout_rotation_interval: 5        # Rotate holdout set every N cycles
  drift_threshold: 0.12               # Judge drift detection threshold
  models:
    - provider: google
      model: gemini-2.5-pro
      api_key_env: GOOGLE_API_KEY
    - provider: openai
      model: gpt-4o
      api_key_env: OPENAI_API_KEY
    - provider: anthropic
      model: claude-sonnet-4-5
      api_key_env: ANTHROPIC_API_KEY

# ─── Budget controls ─────────────────────────────────────────────────
budget:
  per_cycle_dollars: 1.0              # Maximum spend per optimization cycle
  daily_dollars: 10.0                 # Maximum daily spend
  stall_threshold_cycles: 5           # Pause after N cycles with no improvement

# ─── Loop settings ───────────────────────────────────────────────────
loop:
  schedule_mode: continuous           # continuous, interval, or cron
  interval_minutes: 5.0
  checkpoint_path: .autoagent/loop_checkpoint.json

# ─── Eval settings ───────────────────────────────────────────────────
eval:
  history_db_path: eval_history.db
  significance_alpha: 0.05            # p-value threshold for significance
  significance_iterations: 2000       # Bootstrap iterations

# ─── Human controls ──────────────────────────────────────────────────
human_control:
  immutable_surfaces: ["safety_instructions"]   # Never modify these surfaces
```

### A.5 Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTOAGENT_DB` | `conversations.db` | Conversation database path |
| `AUTOAGENT_CONFIGS` | `configs` | Config versions directory |
| `AUTOAGENT_MEMORY_DB` | `optimizer_memory.db` | Optimizer memory database |
| `AUTOAGENT_REGISTRY_DB` | `registry.db` | Registry database |
| `AUTOAGENT_TRACE_DB` | `traces.db` | Trace database |
| `AUTOAGENT_USE_MOCK` | `true` | Use mock LLM providers |
| `GOOGLE_API_KEY` | (none) | Google AI API key |
| `OPENAI_API_KEY` | (none) | OpenAI API key |
| `ANTHROPIC_API_KEY` | (none) | Anthropic API key |

### A.6 Project file structure

```
autoagent-vnextcc/
+-- agent/                # Agent framework, config, tools, specialists
+-- api/                  # FastAPI server (39 route modules, 200+ endpoints)
|   +-- routes/           # Route modules organized by domain
+-- assistant/            # Chat-based agent builder
+-- adk/                  # Google ADK integration
+-- cli/                  # CLI command modules
+-- context/              # Context engineering workbench
+-- core/                 # Shared domain types and skills system
+-- cx_studio/            # Google CX Agent Studio integration
+-- deployer/             # Canary deployment and release management
+-- evals/                # Evaluation runner, scoring, datasets, replay
+-- graders/              # Tiered grading pipeline
+-- judges/               # Judge stack with versioning and calibration
+-- mcp_server/           # Model Context Protocol server
+-- observer/             # Trace analysis, blame maps, anomaly detection
+-- optimizer/            # Optimization loop, mutations, search strategies
|   +-- prompt_opt/       # Pro-mode algorithms (MIPROv2, Bootstrap, GEPA, SIMBA)
+-- registry/             # Versioned skills, policies, tools, handoffs
+-- simulator/            # Simulation sandbox and stress testing
+-- tests/                # Test suite (131 files, 1131+ tests)
+-- web/                  # React + TypeScript frontend
|   +-- src/
|       +-- pages/        # 44 page components
|       +-- components/   # Reusable UI components
|       +-- lib/          # API client, types, WebSocket, utilities
+-- docs/                 # Documentation
+-- configs/              # Agent config versions (YAML)
+-- evals/cases/          # Eval test cases
+-- runner.py             # CLI entry point (112 commands)
+-- autoagent.yaml        # Runtime configuration
+-- setup.sh              # First-time setup script
+-- start.sh              # Start backend + frontend
+-- stop.sh               # Stop everything
+-- Dockerfile            # Container build
+-- docker-compose.yaml   # Multi-service compose
+-- .env.example          # Environment variable template
```

### A.7 Database reference

AutoAgent uses SQLite for all persistent storage:

| Database | Default path | What it stores |
|----------|-------------|----------------|
| `conversations.db` | `AUTOAGENT_DB` | Agent conversations and outcomes |
| `optimizer_memory.db` | `AUTOAGENT_MEMORY_DB` | Optimization attempts and acceptance metadata |
| `eval_history.db` | `AUTOAGENT_EVAL_HISTORY_DB` | Eval run history with per-case results |
| `registry.db` | `AUTOAGENT_REGISTRY_DB` | Skills, policies, tool contracts, handoff schemas |
| `traces.db` | `AUTOAGENT_TRACE_DB` | Structured trace events and spans |
| `experiments.db` | (in-memory or configs dir) | Experiment cards |
| `event_log.db` | (in-memory or configs dir) | System event log |

Additional file-based state:
- `configs/*.yaml` -- Agent configuration versions
- `configs/manifest.json` -- Version manifest (active/canary pointers)
- `.autoagent/loop_checkpoint.json` -- Loop resume state
- `.autoagent/human_control.json` -- Pause, pin, reject state
- `.autoagent/dead_letters.db` -- Failed cycle dead letter queue
- `.autoagent/logs/backend.jsonl` -- Structured JSON logs with rotation

### A.8 Search strategy comparison

| Feature | Simple | Adaptive | Full | Pro |
|---------|--------|----------|------|-----|
| Candidates per cycle | 1 | 1-3 | 3-5 | 5-10 |
| Operator selection | Greedy | Bandit (UCB1/Thompson) | Bandit + curriculum | Algorithm-specific |
| Holdout rotation | No | No | Yes | Yes |
| Pareto archive | No | No | Yes | Yes |
| Budget per cycle | ~$0.10 | ~$0.20 | ~$0.50 | ~$1-5 |
| Best for | Getting started | Most production use | Complex multi-objective | Maximum quality |
| Algorithms | Deterministic | Multi-hypothesis | Curriculum learning | MIPROv2, Bootstrap, GEPA, SIMBA |

### A.9 Risk class reference

| Risk class | Mutation types | Auto-deploy? | Gate strictness |
|------------|---------------|--------------|-----------------|
| **Low** | Instruction rewrite, few-shot edit, temperature nudge | Yes | Standard gates |
| **Medium** | Tool hint, routing rule, policy patch | Conditional | Standard + regression check |
| **High** | Model swap, topology change, callback patch | No -- human review required | Full gate suite + human approval |
| **Critical** | Custom mutations | Never | All gates + explicit approval |

### A.10 Evaluation modes

| Mode | What it tests | When to use |
|------|--------------|-------------|
| **Target response** | Does the agent produce the expected output? | When you have known-good answers |
| **Target tool trajectory** | Does the agent call the right tools in order? | When tool usage matters |
| **Rubric quality** | How well does the response score on criteria? | General quality assessment |
| **Rubric tool use** | How well does tool usage score on criteria? | Tool behavior quality |
| **Hallucination** | Does the response contain unsupported claims? | Factual accuracy |
| **Safety** | Does the response violate safety policies? | Always (non-negotiable) |
| **User simulation** | Does a simulated user find it helpful? | End-to-end satisfaction |

### A.11 Anti-Goodhart guards

AutoAgent includes three mechanisms to prevent your eval scores from becoming meaningless (Goodhart's Law: "When a measure becomes a target, it ceases to be a good measure"):

**1. Holdout rotation**

A rotating subset of eval cases is withheld from optimization. The holdout rotates every N cycles (default: 5) so the optimizer can't memorize any fixed subset.

**2. Drift detection**

The drift monitor tracks judge agreement rates over time. If a judge's scoring pattern shifts beyond the threshold (default: 0.12), the system flags it and can optionally pause optimization.

**3. Judge variance bounds**

If variance across judge calls exceeds the threshold (default: 0.03), the experiment is flagged for human review rather than auto-promoted.

### A.12 Statistical testing methods

**Clustered bootstrap**

Standard bootstrap sampling assumes independence between samples. But agent conversations within the same session are correlated. Clustered bootstrap accounts for this by sampling at the conversation level, giving more accurate confidence intervals.

**Sequential testing (O'Brien-Fleming)**

Checks for significance at multiple points during evaluation, allowing early stopping. The O'Brien-Fleming alpha spending function controls the false positive rate across multiple checks.

**Multiple-hypothesis correction (Holm-Bonferroni)**

When testing several mutations at once (e.g., in `full` search strategy), Holm-Bonferroni correction adjusts p-values to maintain rigorous false positive control.

**Judge variance estimation**

LLM judges aren't perfectly consistent. AutoAgent estimates this judge noise and incorporates it into significance calculations. If judge variance is too high, the experiment is flagged for human review.

**Minimum sample size**

AutoAgent won't declare significance with too few examples.

### A.13 Multi-model support

AutoAgent works with multiple LLM providers simultaneously:

| Provider | Models | Notes |
|----------|--------|-------|
| Google | Gemini 2.5 Pro, Gemini 2.5 Flash | Default provider |
| OpenAI | GPT-4o, GPT-4o-mini, o1, o3 | |
| Anthropic | Claude Sonnet 4.5, Claude Haiku 3.5 | |
| OpenAI-compatible | Any compatible endpoint | Custom base URL |
| Mock | Deterministic responses | No API key needed |

Configure in `autoagent.yaml`:

```yaml
optimizer:
  models:
    - provider: google
      model: gemini-2.5-pro
      api_key_env: GOOGLE_API_KEY
    - provider: openai
      model: gpt-4o
      api_key_env: OPENAI_API_KEY
    - provider: anthropic
      model: claude-sonnet-4-5
      api_key_env: ANTHROPIC_API_KEY
    - provider: openai
      model: my-custom-model
      base_url: https://my-endpoint.example.com/v1
      api_key_env: MY_API_KEY
```

### A.14 The five-minute VP demo walkthrough

```bash
autoagent demo vp --company "Acme Corp" --web
```

**The scenario:** Acme Corp's e-commerce support bot has three problems:
1. Billing queries get routed to the wrong agent (23% misroute rate)
2. The agent leaks internal pricing data (safety violation)
3. Response latency is too high (4.2s average)

**Act 1: Baseline** (30 seconds)
The demo shows the current state: health score 0.62, three red metrics, and a blame map showing the three failure clusters.

**Act 2: First optimization cycle** (1 minute)
AutoAgent fixes the routing misroutes by adding missing keywords. Score jumps from 0.62 to 0.74.

**Act 3: Second optimization cycle** (1 minute)
AutoAgent patches the safety violation by adding PII guardrails. Safety score goes from 0.95 to 1.00.

**Act 4: Third optimization cycle** (1 minute)
AutoAgent reduces latency by tuning tool timeouts. Latency drops from 4.2s to 2.1s.

**Act 5: Results** (30 seconds)
Final health score: 0.87. All three problems are fixed. The demo shows the journey timeline with three accepted experiments.

If you pass `--web`, the browser opens to the dashboard after the demo, pre-loaded with the optimization history.

### A.15 Team onboarding sequence

A proven sequence for teams onboarding to AutoAgent:

**Day 1 -- Setup and orientation**
- Run setup and start
- Execute `quickstart` to bootstrap end-to-end behavior
- Read `status`, `config list`, `eval list` outputs
- Tour Dashboard, Conversations, Traces, Configs in the web UI

**Day 2 -- Controlled optimization**
- Run bounded optimize cycles (`--cycles 3`)
- Use `review list` and `runbook` flows
- Validate deploy canary mechanics in `dev` environment
- Set up Judge Ops monitoring

**Day 3 -- Builder Workspace**
- Introduce Builder Workspace with `draft` mode only
- Test approval and permission workflows
- Configure notifications
- Practice `reject` and `rollback` commands

**Week 2 -- Production readiness**
- Integrate CX/ADK pipelines where needed
- Expand eval datasets and outcomes ingestion
- Pilot reward/policy optimization on bounded scope
- Run overnight loop with `--stop-on-plateau`

### A.16 Complete web route table

All 48 routes in the web console:

| Route | Component | Purpose |
|-------|-----------|---------|
| `/` | BuilderWorkspace | Primary authoring surface |
| `/builder` | BuilderWorkspace | Primary authoring surface |
| `/builder/demo` | BuilderDemo | Guided 5-act walkthrough |
| `/builder/:projectId` | BuilderWorkspace | Project-scoped workspace |
| `/builder/:projectId/:sessionId` | BuilderWorkspace | Session-scoped workspace |
| `/dashboard` | Dashboard | Health pulse, journey timeline |
| `/demo` | Demo | Standalone demo page |
| `/evals` | EvalRuns | Launch and compare eval runs |
| `/evals/:id` | EvalDetail | Per-case inspection |
| `/optimize` | Optimize | Trigger cycles, inspect gates |
| `/live-optimize` | LiveOptimize | Real-time SSE streaming |
| `/configs` | Configs | Version browser with YAML viewer |
| `/conversations` | Conversations | Browse agent conversations |
| `/deploy` | Deploy | Canary controls and history |
| `/loop` | LoopMonitor | Continuous optimization control |
| `/opportunities` | Opportunities | Ranked optimization queue |
| `/experiments` | Experiments | Experiment cards |
| `/traces` | Traces | Span-level trace viewer |
| `/events` | EventLogPage | Real-time event log |
| `/autofix` | AutoFix | AI fix proposals |
| `/judge-ops` | JudgeOps | Judge versioning and calibration |
| `/context` | ContextWorkbench | Context window analysis |
| `/changes` | ChangeReview | Review proposed changes |
| `/runbooks` | Runbooks | Curated fix bundles |
| `/skills` | Skills | Skills Marketplace |
| `/intelligence` | IntelligenceStudio | Transcript analytics and Q&A |
| `/memory` | ProjectMemory | Project memory (AUTOAGENT.md) |
| `/registry` | Registry | Registry browser |
| `/blame` | BlameMap | Failure clustering |
| `/scorer-studio` | ScorerStudio | NL scorer creation |
| `/cx/import` | CxImport | Import CX agent |
| `/cx/deploy` | CxDeploy | CX deploy and widget |
| `/adk/import` | AdkImport | Import ADK agent |
| `/adk/deploy` | AdkDeploy | Deploy ADK agent |
| `/agent-skills` | AgentSkills | Capability gap analysis |
| `/agent-studio` | AgentStudio | Natural language agent editing |
| `/assistant` | Assistant | Chat-based agent builder |
| `/notifications` | Notifications | Alert configuration |
| `/sandbox` | Sandbox | Synthetic scenario testing |
| `/knowledge` | Knowledge | Knowledge base |
| `/what-if` | WhatIf | Counterfactual analysis |
| `/reviews` | Reviews | Review queue |
| `/reward-studio` | RewardStudio | Reward function definition |
| `/preference-inbox` | PreferenceInbox | RLHF preference pairs |
| `/policy-candidates` | PolicyCandidates | RL training and OPE |
| `/reward-audit` | RewardAudit | Challenge suites and auditing |
| `/settings` | Settings | Operator quick-reference |

---

## What's next?

Now that you've read this guide, here are suggested next steps based on your role:

**If you're a developer building an agent:**
1. Run `autoagent init --template customer-support` to scaffold a project
2. Edit the base config to describe your agent
3. Write eval cases in `evals/cases/`
4. Run `autoagent optimize --cycles 5` to see improvements
5. Explore the Builder Workspace for interactive iteration

**If you're evaluating AutoAgent for your team:**
1. Run the VP demo: `autoagent demo vp --company "Your Company" --web`
2. Explore the web console at `http://localhost:5173`
3. Try the Builder Workspace demo at `/builder/demo`
4. Follow the Day 1-3 onboarding sequence in Appendix A.15

**If you're integrating with an existing agent platform:**
1. For Google CX: `autoagent cx import --project ...`
2. For Google ADK: `autoagent adk import --path ...`
3. For MCP: `autoagent mcp-server`
4. For custom agents: write a config YAML following the schema in `agent/config/`

**If you're doing research on agent optimization:**
1. Read the Core Concepts chapter for the theoretical framework
2. Try the `pro` search strategy for research-grade algorithms: `autoagent optimize --mode research`
3. Create custom scorers with `autoagent scorer create`
4. Analyze trace data with `autoagent trace blame` and `autoagent trace grade`

**Closing principles**

AutoAgent rewards disciplined operation:

- Keep feedback loops tight.
- Keep risk boundaries explicit.
- Keep human controls active.
- Keep evaluation quality high.

When those are in place, continuous optimization becomes a practical reliability advantage rather than a source of instability.

---

*This guide covers AutoAgent VNextCC. For the latest updates, check the `docs/` directory or run `autoagent --help` for inline documentation.*

# AutoAgent Beginner User Guide (Codex Track)

Version date: 2026-03-28  
Audience: Developers, technical operators, and AI product teams who are new to AutoAgent

Welcome to the beginner guide for AutoAgent, a continuous optimization platform for AI agents. This guide is intentionally deep. It starts at zero, walks you through setup and daily operation, then opens up the full control plane so you can run optimization safely in production.

This guide was built from a full source pass across the repository, including CLI, API, web routes/pages, setup scripts, and skill system modules.

> 📝 Note: This guide is intentionally long and reference-heavy. Read Chapters 1-4 first, then return to the reference chapters as needed.

## Table of Contents

1. [Welcome](#1-welcome)
2. [Getting Started](#2-getting-started)
3. [Core Concepts](#3-core-concepts)
4. [CLI Walkthrough](#4-cli-walkthrough)
5. [Web UI Walkthrough](#5-web-ui-walkthrough)
6. [Builder Workspace Deep Dive](#6-builder-workspace-deep-dive)
7. [Advanced Features](#7-advanced-features)
8. [CLI Reference](#8-cli-reference)
9. [Troubleshooting & FAQ](#9-troubleshooting--faq)
10. [Glossary & Appendix](#10-glossary--appendix)

---

## 1. Welcome

AutoAgent is a continuous optimization platform for AI agents.

At a high level, AutoAgent does seven practical things for you:

- Collects agent traces and outcomes.
- Diagnoses where and why failures happen.
- Proposes targeted improvements.
- Evaluates those improvements with gates and metrics.
- Lets humans approve, reject, or constrain risky changes.
- Deploys accepted changes via controlled rollouts.
- Learns from prior cycles to improve what it tries next.

If you are used to shipping static prompts or manually patching agent behavior after incidents, AutoAgent gives you a repeatable, auditable, and test-first loop.

### Who this guide is for

This guide is designed for:

- Engineers who need to own reliability for production agents.
- Product teams who want measurable quality improvement over time.
- Platform teams building internal agent operations workflows.
- Anyone onboarding to AutoAgent without prior project context.

### What you will learn

By the end of this guide, you will be able to:

- Bring up the full stack locally (`./setup.sh`, `./start.sh`).
- Understand the optimization loop and gating model.
- Use the CLI as your primary operational surface.
- Navigate every shipped web route and major interaction pattern.
- Use Builder Workspace modes and inspector tabs safely.
- Operate advanced subsystems like AutoFix, Judge Ops, CX, ADK, and reward/policy optimization.
- Diagnose common failures quickly.

### What “beginner” means here

“Beginner” in this guide means beginner to AutoAgent, not beginner to engineering.

You do not need prior AutoAgent knowledge.

You should be comfortable with:

- Command line basics.
- Reading JSON/YAML.
- Running local web stacks.
- Interpreting operational dashboards.

> 💡 Tip: If you only have 20 minutes, read Chapters 2, 3, and 4 first, then jump to Chapter 9 when something breaks.

### Your first mental model

Keep this model in mind through the rest of the guide:

```text
Observe real behavior -> Diagnose failures -> Propose changes -> Validate under gates -> Promote safely -> Repeat
```

AutoAgent is not just a dashboard and not just a CLI. It is a closed-loop system with controls.

> ⚠️ Warning: Optimization without hard gates leads to local wins and global regressions. AutoAgent is designed to avoid this, but only if you keep safety gates and human controls active.

---

## 2. Getting Started

This chapter gives you the fastest path from clone to first useful run.

### 2.1 Prerequisites

You need:

- Python 3.11+
- Node.js 18+
- npm

Optional for live model-backed runs:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`

If no keys are set, AutoAgent can still run in mock mode for local exploration.

### 2.2 One-time setup

From repo root:

```bash
./setup.sh
```

What `setup.sh` does (from source):

- Checks Python version and fails fast with clear guidance if too old.
- Checks Node version and fails fast if too old.
- Creates `.venv` if missing.
- Installs Python dependencies with `pip install -e '.[dev]'`.
- Installs frontend dependencies under `web/` with `npm install`.
- Creates `.env` from `.env.example` if needed.
- Seeds demo data (VP demo + Builder demo).

### 2.3 Start the platform

```bash
./start.sh
```

What `start.sh` does (from source):

- Ensures setup already ran (`.venv` exists).
- Frees stale ports (`8000`, `5173`) if needed.
- Starts backend (`uvicorn api.server:app`).
- Starts frontend (`npm run dev -- --port 5173`).
- Waits for health checks.
- Opens the browser automatically.
- Handles Ctrl+C cleanup and PID file teardown.

Default local URLs:

- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

> 📝 Note: Logs are written to `.autoagent/backend.log` and `.autoagent/frontend.log`.

### 2.4 Verify your CLI

Real output from `python3 runner.py --help`:

```text
Usage: runner.py [OPTIONS] COMMAND [ARGS]...

  AutoAgent VNextCC — agent optimization platform.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  adk         Google Agent Development Kit (ADK) integration — import,...
  autofix     AutoFix Copilot — reviewable improvement proposals.
  autonomous  Run autonomous optimization with scoped permissions.
  benchmark   Run standard benchmarks.
  build       Build an agent artifact from natural language and scaffold...
  changes     Changes — aliases for reviewable optimizer change cards.
  config      Manage agent config versions.
  context     Context Engineering Workbench — diagnose and tune agent...
  curriculum  Self-play curriculum generator for adversarial eval prompts.
  cx          Google Cloud CX Agent Studio — import, export, deploy.
  dataset     Manage datasets for evaluation and training.
  demo        Demo commands for presentations and quick trials.
  deploy      Deploy a config version.
  diagnose    Run failure diagnosis and optionally fix issues interactively.
  doctor      Check system health and configuration.
  edit        Apply natural language edits to agent config.
  eval        Evaluate agent configs against test suites.
  explain     Generate a plain-English summary of the agent's current state.
  full-auto   Run optimization + loop in dangerous full-auto mode.
  init        Scaffold a new AutoAgent project with config, eval suite,...
  judges      Judge Ops — monitoring, calibration, and human feedback.
  logs        Browse conversation logs.
  loop        Run the continuous autoresearch loop.
  mcp-server  Start MCP server for AI coding tool integration.
  memory      Project memory — manage AUTOAGENT.md persistent context.
  optimize    Run optimization cycles to improve agent config.
  outcomes    Manage business outcome data.
  pause       Pause the optimization loop (human escape hatch).
  pin         Mark a config surface as immutable (e.g.
  pref        Preference collection and export.
  quickstart  Run the ENTIRE golden path: init → seed → eval → optimize →...
  registry    Modular registry — skills, policies, tool contracts,...
  reject      Reject a promoted experiment and rollback any active canary.
  release     Manage signed release objects.
  replay      Show optimization history like git log --oneline.
  resume      Resume the optimization loop after a pause.
  review      Review proposed change cards from the optimizer.
  reward      Manage reward definitions.
  rl          Policy optimization commands.
  runbook     Runbooks — curated bundles of skills, policies, and tool...
  scorer      NL Scorer — create eval scorers from natural language...
  server      Start the API server + web console.
  skill       Unified skill management — build-time and run-time skills.
  status      Show system health, config versions, and recent activity.
  trace       Trace analysis — grading, blame maps, and graphs.
  unpin       Remove immutable marking from a config surface.
```

### 2.5 Quick confidence checks

Try these first:

```bash
python3 runner.py status
python3 runner.py config list
python3 runner.py eval list
python3 runner.py runbook list
```

Example outputs from this workspace:

```text
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

```text
Config versions (1 total):
  Ver  Status        Hash             Composite  Timestamp
─────  ────────────  ──────────────  ──────────  ────────────────────────
v001   active        8c771aaa720e        0.0000  2026-03-24 00:03:59 UTC ●
```

```text
No local eval result files found.
Run: autoagent eval run --output results.json
```

```text
Runbooks (7):

enhance-few-shot-examples
fix-retrieval-grounding
improve-routing-accuracy
optimize-cost-efficiency
reduce-tool-latency
stabilize-multilingual-support
tighten-safety-policy
```

### 2.6 Golden path command

If you want one command to bootstrap end-to-end behavior:

```bash
python3 runner.py quickstart --help
```

Real help output:

```text
Usage: runner.py quickstart [OPTIONS]

  Run the ENTIRE golden path: init → seed → eval → optimize → summary.

Options:
  --agent-name TEXT   Agent name for AUTOAGENT.md.  [default: My Agent]
  --verbose           Show detailed output.
  --dir TEXT          Directory to initialize in.  [default: .]
  --open / --no-open  Auto-open web console after completion.
```

> 💡 Tip: For onboarding, run quickstart first, then inspect generated config and eval artifacts before touching advanced subsystems.

### 2.7 Full baseline guide (from project docs)

The section below is included from project `docs/getting-started.md` with heading levels adjusted.

##### Getting Started

Get AutoAgent VNextCC running in under five minutes. This guide takes you from install to your first optimization cycle.

#### Prerequisites

- **Python 3.11+** (3.12 recommended)
- **pip** (bundled with Python)
- API keys for at least one LLM provider (OpenAI, Anthropic, or Google)

#### Install

Clone the repo and install in development mode:

```bash
git clone https://github.com/your-org/autoagent-vnextcc.git
cd autoagent-vnextcc
pip install -e ".[dev]"
```

Verify the install:

```bash
autoagent --version
```

#### Initialize a project

Scaffold a new project with a starter template:

```bash
autoagent init --template customer-support
```

This creates:

```
configs/v001_base.yaml    # Base agent configuration
evals/cases/              # Eval test cases
agent/config/             # Agent config schema
```

The `customer-support` template includes a multi-specialist agent with support, orders, and recommendations routing. Use `--template minimal` for a bare scaffold.

#### Run your first eval

Evaluate the base configuration against the test suite:

```bash
autoagent eval run --output results.json
```

The eval runner executes every test case, scores quality/safety/latency/cost, and writes a composite score. To target a specific category:

```bash
autoagent eval run --category happy_path --output results.json
```

#### Read results

```bash
autoagent eval results --file results.json
```

Output shows pass rate, quality score, safety failures, latency, cost, and composite score.

#### Start optimization

Run three optimization cycles. Each cycle proposes a mutation, evaluates it, and promotes or rejects:

```bash
autoagent optimize --cycles 3
```

The optimizer uses failure analysis from your conversation history to generate targeted improvements.

#### Run the full loop

For continuous optimization with automatic plateau detection:

```bash
autoagent loop --max-cycles 20 --stop-on-plateau
```

The loop orchestrates the full cycle: trace, diagnose, search, eval, gate, deploy, learn, repeat. It stops automatically when improvements plateau.

Additional scheduling options:

```bash
##### Run on a 5-minute interval
autoagent loop --schedule interval --interval-minutes 5

##### Run on a cron schedule
autoagent loop --schedule cron --cron "*/10 * * * *"

##### Resume from a checkpoint
autoagent loop --resume --checkpoint-file .autoagent/loop_checkpoint.json
```

#### Start the web console

Launch the API server and web dashboard:

```bash
autoagent server
```

Open [http://localhost:8000](http://localhost:8000) for the web console. The API is available at `http://localhost:8000/api/`.

Options:

```bash
autoagent server --host 0.0.0.0 --port 9000 --reload
```

#### Configuration

All settings live in `autoagent.yaml` at the project root:

```yaml
optimizer:
  strategy: round_robin
  search_strategy: simple          # simple | adaptive | full | pro
  holdout_rotation_interval: 5
  drift_threshold: 0.12
  models:
    - provider: openai
      model: gpt-4o
      api_key_env: OPENAI_API_KEY

loop:
  schedule_mode: continuous
  interval_minutes: 5.0
  checkpoint_path: .autoagent/loop_checkpoint.json

eval:
  history_db_path: eval_history.db
  significance_alpha: 0.05

budget:
  per_cycle_dollars: 1.0
  daily_dollars: 10.0
  stall_threshold_cycles: 5

human_control:
  immutable_surfaces: ["safety_instructions"]
```

Set API keys via environment variables referenced in the config (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`).

#### Next steps

- [Core Concepts](concepts.md) -- understand the eval loop, metric hierarchy, and search strategies
- [CLI Reference](cli-reference.md) -- every command and flag
- [API Reference](api-reference.md) -- complete REST API surface
- [AutoFix Copilot](features/autofix.md) -- automated failure repair
- [Judge Ops](features/judge-ops.md) -- judge versioning and drift monitoring
- [Context Workbench](features/context-workbench.md) -- context window analysis
- [Pro-Mode Optimization](features/prompt-optimization.md) -- MIPROv2, GEPA, SIMBA, BootstrapFewShot
- [Modular Registry](features/registry.md) -- skills, policies, tool contracts, handoff schemas
- [Trace Grading](features/trace-grading.md) -- span-level grading and blame maps
- [NL Scorer](features/nl-scorer.md) -- create scorers from natural language

---

## 3. Core Concepts

This chapter explains the operational semantics you need before running autonomous loops.

### 3.1 The optimization loop

Canonical loop:

```text
trace -> diagnose -> search -> eval -> gate -> deploy -> learn -> repeat
```

Each stage has a corresponding control surface in CLI/API/UI.

### 3.2 Metrics hierarchy

AutoAgent evaluates changes top-down:

1. Hard gates (must pass)
2. North-star outcomes (must improve)
3. Operating SLOs (must remain in bounds)
4. Diagnostics (inform, usually not gate)

This ordering matters. A north-star improvement never overrides hard-gate safety failures.

### 3.3 Typed mutations

Mutations are typed and surface-targeted. This keeps proposals interpretable and allows risk-stratified policy.

Common surface examples:

- Instructions
- Routing
- Tool configuration
- Guardrails
- Model/config settings
- Memory/context behavior

### 3.4 Search strategies

From simpler to more advanced:

- `simple`
- `adaptive`
- `full`
- `pro`

Higher sophistication generally means more candidate diversity and more budget/compute pressure.

### 3.5 Experiment cards

Every significant optimization attempt should leave a structured record:

- Hypothesis
- Diffs
- Scores before/after
- Gate outcomes
- Deployment status
- Rollback path

### 3.6 Human control model

You always retain operator overrides:

- Pause/resume loops
- Pin/unpin mutable surfaces
- Reject experiments
- Approve/reject privileged actions in Builder Workspace

### 3.7 Cost and risk controls

Budget and safety controls are first-class:

- Per-cycle budget
- Daily budget
- Stall detection
- Canary deployment strategies
- Approval-scoped privileged operations

> ⚠️ Warning: Do not run with permissive defaults in production without reviewing immutable surfaces and approval scopes.

### 3.8 Canonical concept docs (from project docs)

The next two sections are imported from project docs for full conceptual coverage.

#### 3.8.1 `docs/concepts.md` (heading-adjusted)

##### Core Concepts

The mental models behind AutoAgent VNextCC. Read this before diving into features.

###### The Eval Loop

AutoAgent runs a closed-loop optimization cycle:

```
trace → diagnose → search → eval → gate → deploy → learn → repeat
```

1. **Trace** -- Collect conversation traces and span-level telemetry
2. **Diagnose** -- Classify failures, build blame maps, identify optimization opportunities
3. **Search** -- Generate candidate mutations targeting diagnosed weaknesses
4. **Eval** -- Run candidates against the eval suite with statistical significance testing
5. **Gate** -- Check safety gates, regression gates, and holdout validation
6. **Deploy** -- Promote winning configs via canary or immediate deployment
7. **Learn** -- Record outcomes in optimization memory for future search
8. **Repeat** -- Loop until plateau, budget exhaustion, or human stop

Each cycle is autonomous but human-interruptible at every stage.

###### 4-Layer Metric Hierarchy

Metrics are organized into four layers, evaluated top-down. A failure at a higher layer blocks promotion regardless of lower-layer scores.

| Layer | Purpose | Examples |
|-------|---------|----------|
| **Hard Gates** | Binary pass/fail, non-negotiable | Safety violation rate = 0%, no regressions on pinned surfaces |
| **North-Star Outcomes** | Primary optimization targets | Task success rate, response quality, composite score |
| **Operating SLOs** | Operational guardrails | Latency p95 < 2s, cost per conversation < $0.05 |
| **Diagnostics** | Debugging signals, not gated | Tool correctness, routing accuracy, handoff fidelity, failure buckets |

The optimizer maximizes north-star outcomes subject to hard gates and SLO constraints.

###### Typed Mutations

The mutation registry defines 9 operator classes, each targeting a specific configuration surface:

| Operator | Surface | Risk Class |
|----------|---------|------------|
| Rewrite instruction | `instruction` | medium |
| Add/remove few-shot examples | `few_shot` | low |
| Modify tool descriptions | `tool_description` | medium |
| Swap model | `model` | high |
| Tune generation settings | `generation_settings` | low |
| Adjust callbacks | `callback` | medium |
| Context caching policy | `context_caching` | low |
| Memory policy | `memory_policy` | medium |
| Routing changes | `routing` | high |

Every operator declares preconditions, a validator function, rollback strategy, estimated eval cost, and whether it supports auto-deploy. The risk class determines gate strictness: `critical` mutations always require human approval.

###### Experiment Cards

Every optimization attempt is tracked as an experiment card:

```python
ExperimentCard(
    experiment_id="exp_a1b2c3",
    hypothesis="Rewriting the support instruction to be more concise will reduce latency",
    config_sha="abc123",
    baseline_scores={"composite": 0.82},
    candidate_scores={"composite": 0.86},
    significance=0.03,       # p-value from bootstrap test
    status="promoted",       # pending → evaluated → promoted | rejected | archived
)
```

Cards form an audit trail. You can inspect any past experiment to understand what was tried, what worked, and why.

###### Judge Stack

Eval scoring uses a layered judge stack, applied in order:

1. **Deterministic** -- Pattern matching, keyword checks, schema validation. Fast, zero-cost.
2. **Similarity** -- Embedding-based comparison against reference answers. Low cost.
3. **Binary Rubric** -- LLM judge with structured rubric. Scores quality on defined criteria.
4. **Audit Judge** -- Secondary LLM review of borderline cases. Catches judge errors.
5. **Calibration** -- Periodic human-vs-judge agreement analysis. Tracks judge drift over time.

Higher layers only fire when lower layers are inconclusive. This keeps eval costs low while maintaining accuracy.

###### Search Strategies

Four search strategies, increasing in sophistication:

| Strategy | Description | Best For |
|----------|-------------|----------|
| `simple` | Deterministic proposer, single candidate per cycle | Getting started, low budget |
| `adaptive` | Multi-hypothesis search with bandit-based family selection | Most production use |
| `full` | Adaptive + curriculum learning + Pareto archive | Complex multi-objective optimization |
| `pro` | Research-grade prompt optimization (MIPROv2, BootstrapFewShot, GEPA, SIMBA) | Maximum quality, higher budget |

Set the strategy in `autoagent.yaml`:

```yaml
optimizer:
  search_strategy: adaptive
```

###### Anti-Goodhart Guards

Three mechanisms prevent metric gaming (Goodhart's Law):

**Holdout rotation.** A rotating holdout set is excluded from optimization and used for validation. The holdout rotates every N cycles (default: 5) so the optimizer never fully adapts to any fixed subset.

**Drift detection.** The drift monitor tracks judge agreement rates over time. If a judge's scoring pattern shifts beyond the threshold (default: 0.12), the system flags it and optionally pauses optimization.

**Judge variance.** If variance across judge calls exceeds the threshold (default: 0.03), the experiment is flagged for human review rather than auto-promoted.

###### Cost Controls

Three budget mechanisms prevent runaway spend:

```yaml
budget:
  per_cycle_dollars: 1.0         # Max spend per optimization cycle
  daily_dollars: 10.0            # Max daily aggregate spend
  stall_threshold_cycles: 5      # Pause after N cycles with no improvement
```

The cost tracker records actual spend per cycle (LLM calls, eval runs). When the daily budget is exhausted or stall is detected, the loop pauses automatically and emits a notification.

###### Human Escape Hatches

Humans retain full control at all times:

| Command | Effect |
|---------|--------|
| `autoagent pause` | Immediately pause the optimization loop |
| `autoagent resume` | Resume a paused loop |
| `autoagent pin <surface>` | Lock a config surface (e.g., `safety_instructions`) -- optimizer cannot modify it |
| `autoagent unpin <surface>` | Unlock a previously pinned surface |
| `autoagent reject <experiment_id>` | Reject and roll back a specific experiment |

Pinned surfaces and the pause state persist across restarts via `.autoagent/human_control.json`. The `immutable_surfaces` list in config defines surfaces that can never be modified, even by explicit unpin.

#### 3.8.2 `docs/platform-overview.md` (heading-adjusted)

##### Platform overview

AutoAgent is a continuous optimization platform for AI agents. It watches how your agent performs, figures out what's going wrong, generates targeted fixes, proves they work with statistical testing, and deploys them — in a loop that runs for hours, days, or weeks without intervention.

This page walks through every major subsystem so you know what's available and when to use it.

---

###### The optimization loop

Everything in AutoAgent centers on a single closed loop:

```
Trace  →  Diagnose  →  Search  →  Eval  →  Gate  →  Deploy  →  Learn  →  Repeat
```

The loop is fully autonomous but human-interruptible at every stage. You can pause it, pin specific config surfaces from mutation, reject experiments, or set budget caps. When something goes wrong, failures land in a dead letter queue — the loop never crashes.

Each pass through the loop produces a reviewable **experiment card**: a structured record of what was tried, what changed, whether it worked, and how to roll it back.

---

###### Tracing and diagnosis

####### Trace collection

AutoAgent records structured telemetry from every agent invocation — not just the final answer, but every tool call, agent transfer, state delta, and model call along the way. Traces are stored as hierarchical span trees in SQLite with indexes for fast lookup by trace, session, or agent path.

####### Trace grading

Seven span-level graders score individual trace spans for fine-grained diagnosis:

| Grader | What it evaluates |
|--------|-------------------|
| Routing | Was the correct specialist agent selected? |
| Tool selection | Was the right tool chosen for the task? |
| Tool arguments | Were tool arguments correct and complete? |
| Retrieval quality | Did retrieval return relevant, sufficient context? |
| Handoff quality | Was context preserved across agent handoffs? |
| Memory use | Was memory read/written appropriately? |
| Final outcome | Did the span achieve its intended result? |

Each grader returns a score with evidence, so you can see exactly where in a trace the agent went wrong.

####### Blame maps

Span-level grades are aggregated into **blame clusters** — groups of related failures organized by root cause. Each cluster gets an impact score based on frequency, severity, and business impact. Trend detection identifies patterns that are getting worse over time.

####### Opportunity queue

Blame clusters feed into a ranked opportunity queue that replaces binary "needs optimization" flags with a priority-scored list. Each opportunity includes the failure family, recommended mutation operators, and expected lift. The optimizer pulls from this queue to decide what to fix next.

---

###### Search and mutations

####### Typed mutations

Nine built-in mutation operators target specific configuration surfaces:

| Operator | What it changes | Risk level |
|----------|----------------|------------|
| Instruction rewrite | Agent instructions | Low |
| Few-shot edit | Example conversations | Low |
| Temperature nudge | Generation settings | Low |
| Tool hint | Tool descriptions | Medium |
| Routing rule | Agent routing logic | Medium |
| Policy patch | Safety/business policies | Medium |
| Model swap | Underlying LLM | High |
| Topology change | Agent graph structure | High |
| Callback patch | Callback handlers | High |

Low-risk mutations can auto-deploy. High-risk mutations always require human review.

####### Search strategies

The search engine generates candidate mutations from the opportunity queue. Four strategies are available, from simple to research-grade:

**Simple** — One mutation per cycle, greedy selection. Good for getting started.

**Adaptive** — Bandit-guided operator selection using UCB1 or Thompson sampling. Learns which operators work for which failure families over time.

**Full** — Multi-hypothesis search with curriculum learning. Generates diverse candidates, evaluates in parallel, and rotates holdout sets to prevent overfitting.

**Pro** — Research-grade prompt optimization algorithms:
- **MIPROv2** — Bayesian search over (instruction, example set) pairs
- **BootstrapFewShot** — Teacher-student demonstration bootstrapping (DSPy-inspired)
- **GEPA** — Gradient-free evolutionary prompt adaptation with tournament selection
- **SIMBA** — Simulation-based iterative hill-climbing

---

###### Evaluation engine

####### Eval modes

Seven evaluation modes cover different aspects of agent quality:

- **Target response** — Does the agent produce the expected output?
- **Target tool trajectory** — Does the agent call the right tools in the right order?
- **Rubric quality** — How well does the response score against defined criteria?
- **Rubric tool use** — How well does tool usage score against criteria?
- **Hallucination** — Does the response contain unsupported claims?
- **Safety** — Does the response violate safety policies?
- **User simulation** — Does a simulated user find the response helpful?

####### Dataset management

Eval datasets are split into four types:

- **Golden** — Curated, high-confidence test cases
- **Rolling holdout** — Automatically rotated to prevent overfitting
- **Challenge / adversarial** — Edge cases and adversarial inputs
- **Live failure queue** — Bad production traces converted to eval cases automatically

####### Statistical rigor

Every evaluation includes statistical significance testing:

- **Clustered bootstrap** — Accounts for conversation-level correlation
- **Sequential testing** — O'Brien-Fleming alpha spending for early stopping
- **Multiple-hypothesis correction** — Holm-Bonferroni when testing several mutations
- **Judge variance estimation** — Accounts for LLM judge noise in significance calculations
- **Minimum sample size** — Won't declare significance with too few examples

####### Anti-Goodhart guards

Three mechanisms prevent your eval scores from becoming meaningless:

- **Holdout rotation** — Tuning, validation, and holdout partitions rotate on a configurable interval
- **Drift detection** — Monitors the gap between tuning and validation scores; flags overfitting
- **Judge variance bounds** — If judge noise exceeds a threshold, the system warns before trusting results

---

###### Judge stack

Evaluation scoring uses a tiered judge pipeline. Each tier is faster and cheaper than the next, so expensive LLM judges only run when simpler methods can't decide:

1. **Deterministic** — Pattern matching, keyword checks, schema validation. Instant, zero cost, confidence = 1.0.
2. **Similarity** — Token-overlap Jaccard scoring against reference answers. Fast and cheap.
3. **Binary rubric** — LLM judge with structured yes/no rubric questions. The primary scoring layer for most evals.
4. **Audit judge** — A second LLM from a different model family reviews borderline cases. Catches systematic judge errors.

The judge stack also includes:

- **Versioning** — Track judge changes and their impact on scores over time
- **Drift monitoring** — Detect shifts in judge agreement rates
- **Human feedback calibration** — Corrections from human review improve judge accuracy
- **Position and verbosity bias detection** — Identify systematic biases in LLM judges

---

###### Gating and deployment

####### Metric hierarchy

Every optimization decision flows through four layers, evaluated top-down:

| Layer | Role | What happens if it fails |
|-------|------|--------------------------|
| **Hard gates** | Safety, auth, state integrity, P0 regressions | Mutation rejected immediately |
| **North-star outcomes** | Task success, groundedness, satisfaction | Must improve to be promoted |
| **Operating SLOs** | Latency, cost, escalation rate | Must stay within bounds |
| **Diagnostics** | Tool correctness, routing accuracy, handoff fidelity | Observed but not gated |

A mutation that improves task success by 12% but trips a safety gate is rejected. No exceptions.

####### Experiment cards

Every optimization attempt produces a structured experiment card:

- Hypothesis and target surfaces
- Config SHA for reproducibility
- Risk classification
- Baseline and candidate scores
- Statistical significance (p-value, confidence interval)
- Diff summary and rollback instructions
- Status lifecycle: pending → running → accepted / rejected / archived

Cards form a complete audit trail. You can inspect any past experiment to understand what was tried and why.

####### Canary deployment

Winning mutations are deployed via configurable canary rollout:

- Set the percentage of traffic that sees the new config
- Monitor for regressions during rollout
- Promote to full deployment or rollback with one command
- Full deployment history with version tracking

---

###### AutoFix copilot

AutoFix analyzes failure patterns and generates constrained improvement proposals. Each proposal includes:

- Root cause analysis with evidence
- Suggested mutation type and target surface
- Expected lift and risk assessment
- Confidence score

Proposals go through a review-before-apply workflow. You see exactly what will change, approve or reject, and track the full proposal lifecycle.

---

###### NL scorer generation

Describe what "good" looks like in plain English:

> "The agent should acknowledge the customer's frustration, look up their order, and provide a specific resolution within 3 turns."

AutoAgent converts this into a structured `ScorerSpec` with named dimensions, rubric criteria, and weight distribution. You can refine the scorer iteratively and test it against real traces before using it in production evals.

---

###### Context engineering workbench

Diagnostics for agent context window usage:

- **Growth pattern detection** — Identifies linear, exponential, sawtooth, or stable growth
- **Utilization analysis** — How much of the context window is actually used
- **Failure correlation** — Links context state (size, staleness) to failure patterns
- **Compaction simulation** — Test aggressive, balanced, and conservative compaction strategies before deploying them

---

###### Registry

A versioned registry for four types of agent configuration:

| Type | What it stores | Example |
|------|---------------|---------|
| **Skills** | Instruction bundles with examples and constraints | "Handle refund requests" |
| **Policies** | Hard and soft enforcement rules | "Never reveal internal pricing" |
| **Tool contracts** | Tool schemas with side-effect classification | "order_lookup: read-only, 4s timeout" |
| **Handoff schemas** | Routing rules with validation | "billing queries → billing_agent" |

All entries are versioned with SQLite-backed storage. Supports import/export, search, version diffing, and deprecation.

---

###### Intelligence studio

Build agents from conversation data rather than from scratch:

1. **Upload** a ZIP archive with transcripts (JSON, CSV, or TXT)
2. **Analyze** — AutoAgent classifies intents, maps transfer reasons, extracts procedures, and generates FAQs
3. **Research** — Run deep quantified analysis with root-cause ranking and evidence
4. **Ask** — Query your conversation data in natural language ("Why are people transferring to live support?")
5. **Build** — One-click agent generation from conversation patterns
6. **Optimize** — Autonomous loop: select top insight → draft change → simulate → deploy

####### Knowledge mining

Successful conversations are mined for durable knowledge assets — FAQ entries, procedure documentation, and best-practice patterns that feed back into agent instructions.

---

###### Assistant builder

Chat-based agent building for when you want to describe your agent in natural language rather than writing config files:

- Multi-modal ingestion: upload transcripts, SOPs, audio recordings, images
- Automatic intent extraction and journey mapping
- Auto-generated tools, escalation logic, and guardrails
- Real-time artifact preview as you iterate

---

###### Simulation sandbox

Test agents against synthetic scenarios before deploying:

- **Persona generation** — Create diverse user personas with different intents, communication styles, and edge cases
- **Stress testing** — High-volume synthetic conversations to find breaking points
- **Scenario planning** — What-if analysis for proposed changes

---

###### Skills system

A unified abstraction for both optimization strategies and agent capabilities:

**Build-time skills** are mutation templates the optimizer uses — routing fixes, safety patches, latency tuning recipes. Each skill tracks its own effectiveness and auto-retires when it stops working.

**Run-time skills** are executable agent capabilities — API integrations, handoffs, specialized tools. They compose with dependency resolution and conflict detection.

Skills can be discovered, installed, composed, and published. The recommendation engine suggests skills based on your agent's current failure patterns.

---

###### Human controls

The optimization loop is designed to run autonomously, but you're always in control:

| Command | What it does |
|---------|-------------|
| `autoagent pause` | Pause the loop immediately |
| `autoagent resume` | Resume from where you left off |
| `autoagent pin <surface>` | Lock a config surface from mutation |
| `autoagent unpin <surface>` | Unlock a surface |
| `autoagent reject <id>` | Reject and rollback an experiment |

You can also configure immutable surfaces in `autoagent.yaml` — for example, locking `safety_instructions` so the optimizer can never touch them.

---

###### Cost controls

Budget management is built into the loop:

- **Per-cycle budget** — Maximum spend per optimization cycle
- **Daily budget** — Maximum spend per day
- **Stall detection** — If the Pareto frontier hasn't improved in N cycles, the loop pauses
- **Cost tracking** — SQLite-backed ledger of every API call with per-model cost accounting

---

###### Integrations

####### Google CX Agent Studio

Bidirectional integration with Google's Contact Center AI:

- **Import** — Pull CX agents into AutoAgent (generativeSettings, tools, examples, flows, test cases)
- **Export** — Push optimized configs back to CX format with snapshot preservation
- **Deploy** — One-click deploy to CX environments
- **Widget builder** — Generate embeddable chat widgets

####### Google Agent Development Kit (ADK)

Import ADK agents from Python source via AST parsing. AutoAgent extracts instructions, tools, routing, and generation settings while preserving your code style. Export patches back, or deploy directly to Cloud Run or Vertex AI.

####### MCP server

Model Context Protocol integration exposes AutoAgent's live MCP surface to Claude Code, Codex, Cursor, Windsurf, and other compatible coding tools. The current server supports stdio and streamable HTTP plus 22 tools, prompts, and resources. See `docs/guides/agentic-coding-tools.md` for setup.

####### CI/CD gates

Integrate AutoAgent into your deployment pipeline. Run evals as a CI check, gate deployments on score thresholds, and get automated PR comments with eval results.

---

###### Web console

39 pages served at `http://localhost:8000`, organized by workflow:

####### Observe
- **Dashboard** — Health pulse, journey timeline, metric cards, recommendations
- **Traces** — Span-level trace viewer with filtering
- **Blame Map** — Failure clustering and root cause attribution
- **Conversations** — Browse agent conversations with outcome filtering
- **Event Log** — Real-time system event timeline

####### Optimize
- **Optimize** — Trigger cycles, view experiment history
- **Live Optimize** — Real-time SSE streaming with phase indicators
- **AutoFix** — AI-generated fix proposals with apply/reject
- **Opportunities** — Ranked optimization queue by impact
- **Experiments** — Experiment cards with diffs and statistics

####### Evaluate
- **Eval Runs** — Run history with comparison mode
- **Eval Detail** — Per-case results with pass/fail breakdown
- **Judge Ops** — Judge versioning, calibration, drift monitoring
- **Scorer Studio** — Create eval scorers from natural language

####### Build
- **Agent Studio** — Natural language config editing
- **Intelligence Studio** — Transcript-to-agent pipeline
- **Assistant** — Chat-based agent building
- **Sandbox** — Synthetic scenario testing
- **What-If** — Counterfactual scenario planning

####### Manage
- **Configs** — Version browser with YAML viewer and side-by-side diffs
- **Registry** — Skills, policies, tools, handoff schemas
- **Deploy** — Canary controls and deployment history
- **Loop Monitor** — Cycle-by-cycle progress and watchdog health
- **Skills** — Optimization strategy browser with effectiveness tracking
- **Runbooks** — Curated fix bundles with one-click apply
- **Settings** — Runtime configuration and keyboard shortcuts

---

###### CLI

70+ commands across 30+ groups. Every command supports `--help`, and major commands support `--json` for structured output. See the [CLI reference](cli-reference.md) for the complete list.

###### API

200+ endpoints across 39 route modules, with OpenAPI docs at `/docs`. WebSocket at `/ws` for real-time updates and SSE at `/api/events` and `/api/optimize/stream` for live streaming. See the [API reference](api-reference.md) for the full endpoint list.

---

###### Multi-model support

AutoAgent works with multiple LLM providers simultaneously. Configure them in `autoagent.yaml` and the optimizer uses them for judge diversity, mutation generation, and A/B evaluation:

| Provider | Models | Notes |
|----------|--------|-------|
| Google | Gemini 2.5 Pro, Gemini 2.5 Flash | Default provider |
| OpenAI | GPT-4o, GPT-4o-mini, o1, o3 | |
| Anthropic | Claude Sonnet 4.5, Claude Haiku 3.5 | |
| OpenAI-compatible | Any compatible endpoint | Custom base URL |
| Mock | Deterministic responses | No API key needed |

---

###### Reliability

The platform is designed for multi-day unattended operation:

- **Checkpointing** — Loop state is saved after every cycle; restarts resume where they left off
- **Dead letter queue** — Failed cycles are queued for retry or inspection, never dropped
- **Watchdog** — Configurable timeout kills stuck cycles
- **Graceful shutdown** — SIGTERM completes the current cycle before stopping
- **Resource monitoring** — Warnings when memory or CPU exceed configured thresholds
- **Structured logging** — JSON log rotation with configurable size limits

---

## 4. CLI Walkthrough

This walkthrough is task-oriented. You will run practical command sequences in the order most teams use during onboarding.

> 📝 Note: Chapter 8 contains the complete generated command inventory from `runner.py`.

### 4.1 Inspect available commands

```bash
python3 runner.py --help
```

Use this to discover command groups by capability area.

### 4.2 Run an evaluation

First inspect command options:

```bash
python3 runner.py eval run --help
```

Real output (abbreviated):

```text
Usage: runner.py eval run [OPTIONS]
  Run eval suite against a config.
Options:
  --config TEXT
  --suite TEXT
  --dataset TEXT
  --split [train|test|all]
  --category TEXT
  --output TEXT
  -j, --json
```

Typical run:

```bash
python3 runner.py eval run --output results.json
```

Then inspect results:

```bash
python3 runner.py eval results --file results.json
```

### 4.3 Run optimization cycles

Check options first:

```bash
python3 runner.py optimize --help
```

Real output (abbreviated):

```text
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

Try a bounded run:

```bash
python3 runner.py optimize --cycles 2
```

### 4.4 Continuous loop mode

```bash
python3 runner.py loop --help
```

Real output (abbreviated):

```text
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

A safe local test:

```bash
python3 runner.py loop --max-cycles 3 --stop-on-plateau
```

### 4.5 Deployment workflow

Inspect deploy options:

```bash
python3 runner.py deploy --help
```

Real output (abbreviated):

```text
Usage: runner.py deploy [OPTIONS]
Options:
  --config-version INTEGER
  --strategy [canary|immediate]
  --target [autoagent|cx-studio]
  --project TEXT
  --location TEXT
  --agent-id TEXT
  --snapshot TEXT
  --push / --no-push
```

Example canary deploy:

```bash
python3 runner.py deploy --config-version 3 --strategy canary
```

### 4.6 Human safety controls

Pause/resume loop:

```bash
python3 runner.py pause
python3 runner.py resume
```

Pin/unpin sensitive surfaces:

```bash
python3 runner.py pin safety_instructions
python3 runner.py unpin safety_instructions
```

Reject problematic experiment:

```bash
python3 runner.py reject exp_12345678
```

### 4.7 Runbooks and guided fixes

List runbooks:

```bash
python3 runner.py runbook list
```

Apply a runbook:

```bash
python3 runner.py runbook apply tighten-safety-policy
```

### 4.8 Review/changes workflow

List pending review cards:

```bash
python3 runner.py review list
```

Real output in this workspace shows pending cards and risk labels.

Inspect and apply one:

```bash
python3 runner.py review show <card_id>
python3 runner.py review apply <card_id>
```

### 4.9 Integrations (CX and ADK)

CX group help:

```bash
python3 runner.py cx --help
```

ADK group:

```bash
python3 runner.py adk --help
```

### 4.10 Operator checklist for daily CLI use

- Check system state: `status`, `config list`, `logs`.
- Evaluate current baseline: `eval run` and `eval results`.
- Run bounded optimization cycles.
- Review cards and apply only gated wins.
- Deploy via canary.
- Monitor outcomes and loop health.

> 💡 Tip: Save your most common sequences as shell aliases or Makefile recipes.

---

## 5. Web UI Walkthrough

This chapter covers all routes declared in `web/src/App.tsx`, all page components under `web/src/pages/*.tsx`, and major global widgets from `Layout`, `Sidebar`, and `CommandPalette`.

### 5.1 Global layout primitives

Key global surfaces:

- Sidebar route navigation grouped by Build/Operate/Improve/Integrations/Governance/Analysis/Policy Optimization.
- Sticky top bar with page title and command palette trigger (`⌘K`).
- Command palette with static actions + smart query mapping + dynamic results (eval runs/configs/conversations).
- Toast viewport and mock mode banner.
- Keyboard shortcuts (`n`, `o`, `d`) for fast navigation when not in text inputs.

### 5.2 Route map and page inventory (generated)

The next section is generated from `web/src/App.tsx` and `web/src/pages/*.tsx`.

# Web Route and Page Inventory (Generated from web/src)

Total routes in `App.tsx`: **48**
Total page components (`web/src/pages/*.tsx`, excluding tests/backups): **44**

## Route Table

| Route Path | Component | File | Page Header Title | Queries | Mutations | API Calls |
|---|---|---|---|---:|---:|---:|
| `/` | `BuilderWorkspace` | `web/src/pages/BuilderWorkspace.tsx` | (No PageHeader title) | 0 | 0 | 0 |
| `/builder` | `BuilderWorkspace` | `web/src/pages/BuilderWorkspace.tsx` | (No PageHeader title) | 0 | 0 | 0 |
| `/builder/demo` | `BuilderDemo` | `web/src/pages/BuilderDemo.tsx` | (No PageHeader title) | 0 | 0 | 5 |
| `/builder/*` | `BuilderWorkspace` | `web/src/pages/BuilderWorkspace.tsx` | (No PageHeader title) | 0 | 0 | 0 |
| `/builder/:projectId` | `BuilderWorkspace` | `web/src/pages/BuilderWorkspace.tsx` | (No PageHeader title) | 0 | 0 | 0 |
| `/builder/:projectId/:sessionId` | `BuilderWorkspace` | `web/src/pages/BuilderWorkspace.tsx` | (No PageHeader title) | 0 | 0 | 0 |
| `/dashboard` | `Dashboard` | `web/src/pages/Dashboard.tsx` | Karpathy Loop Scorecard | 0 | 0 | 1 |
| `/demo` | `Demo` | `web/src/pages/Demo.tsx` | Demo | 0 | 0 | 1 |
| `/evals` | `EvalRuns` | `web/src/pages/EvalRuns.tsx` | Eval Runs | 0 | 0 | 0 |
| `/evals/:id` | `EvalDetail` | `web/src/pages/EvalDetail.tsx` | (No PageHeader title) | 0 | 0 | 0 |
| `/optimize` | `Optimize` | `web/src/pages/Optimize.tsx` | Optimize | 0 | 0 | 0 |
| `/live-optimize` | `LiveOptimize` | `web/src/pages/LiveOptimize.tsx` | (No PageHeader title) | 0 | 0 | 0 |
| `/configs` | `Configs` | `web/src/pages/Configs.tsx` | No configurations found | 0 | 0 | 0 |
| `/conversations` | `Conversations` | `web/src/pages/Conversations.tsx` | Conversations | 0 | 0 | 0 |
| `/deploy` | `Deploy` | `web/src/pages/Deploy.tsx` | No deployment status | 0 | 0 | 0 |
| `/loop` | `LoopMonitor` | `web/src/pages/LoopMonitor.tsx` | Loop Monitor | 0 | 0 | 0 |
| `/opportunities` | `Opportunities` | `web/src/pages/Opportunities.tsx` | Opportunity Queue | 0 | 0 | 0 |
| `/experiments` | `Experiments` | `web/src/pages/Experiments.tsx` | Experiments | 0 | 0 | 0 |
| `/traces` | `Traces` | `web/src/pages/Traces.tsx` | Traces | 0 | 0 | 0 |
| `/events` | `EventLogPage` | `web/src/pages/EventLog.tsx` | System Event Log | 0 | 0 | 0 |
| `/autofix` | `AutoFix` | `web/src/pages/AutoFix.tsx` | AutoFix Copilot | 0 | 0 | 0 |
| `/judge-ops` | `JudgeOps` | `web/src/pages/JudgeOps.tsx` | Judge Ops | 0 | 0 | 0 |
| `/context` | `ContextWorkbench` | `web/src/pages/ContextWorkbench.tsx` | Context Workbench | 0 | 0 | 0 |
| `/changes` | `ChangeReview` | `web/src/pages/ChangeReview.tsx` | Change Review | 1 | 0 | 1 |
| `/runbooks` | `Runbooks` | `web/src/pages/Runbooks.tsx` | Runbooks | 0 | 0 | 0 |
| `/skills` | `Skills` | `web/src/pages/Skills.tsx` | Skills Marketplace | 0 | 0 | 0 |
| `/intelligence` | `IntelligenceStudio` | `web/src/pages/IntelligenceStudio.tsx` | Intelligence Studio | 0 | 0 | 0 |
| `/memory` | `ProjectMemory` | `web/src/pages/ProjectMemory.tsx` | Project Memory | 0 | 0 | 0 |
| `/registry` | `Registry` | `web/src/pages/Registry.tsx` | Registry Browser | 3 | 0 | 1 |
| `/blame` | `BlameMap` | `web/src/pages/BlameMap.tsx` | Blame Map | 1 | 0 | 1 |
| `/scorer-studio` | `ScorerStudio` | `web/src/pages/ScorerStudio.tsx` | NL Scorer Studio | 2 | 4 | 1 |
| `/cx/import` | `CxImport` | `web/src/pages/CxImport.tsx` | Import CX Agent | 0 | 0 | 0 |
| `/cx/deploy` | `CxDeploy` | `web/src/pages/CxDeploy.tsx` | CX Deploy & Widget | 0 | 0 | 0 |
| `/adk/import` | `AdkImport` | `web/src/pages/AdkImport.tsx` | Import ADK Agent | 0 | 0 | 0 |
| `/adk/deploy` | `AdkDeploy` | `web/src/pages/AdkDeploy.tsx` | Deploy ADK Agent | 0 | 0 | 0 |
| `/agent-skills` | `AgentSkills` | `web/src/pages/AgentSkills.tsx` | (No PageHeader title) | 0 | 4 | 1 |
| `/agent-studio` | `AgentStudio` | `web/src/pages/AgentStudio.tsx` | Agent Studio | 0 | 0 | 0 |
| `/assistant` | `Assistant` | `web/src/pages/Assistant.tsx` | Upload files | 0 | 0 | 0 |
| `/notifications` | `Notifications` | `web/src/pages/Notifications.tsx` | Notifications | 0 | 0 | 0 |
| `/sandbox` | `Sandbox` | `web/src/pages/Sandbox.tsx` | (No PageHeader title) | 0 | 0 | 0 |
| `/knowledge` | `Knowledge` | `web/src/pages/Knowledge.tsx` | (No PageHeader title) | 0 | 0 | 0 |
| `/what-if` | `WhatIf` | `web/src/pages/WhatIf.tsx` | (No PageHeader title) | 0 | 0 | 0 |
| `/reviews` | `Reviews` | `web/src/pages/Reviews.tsx` | (No PageHeader title) | 0 | 0 | 0 |
| `/reward-studio` | `RewardStudio` | `web/src/pages/RewardStudio.tsx` | Reward Studio | 0 | 0 | 1 |
| `/preference-inbox` | `PreferenceInbox` | `web/src/pages/PreferenceInbox.tsx` | Preference Inbox | 0 | 0 | 1 |
| `/policy-candidates` | `PolicyCandidates` | `web/src/pages/PolicyCandidates.tsx` | Policy Candidates | 0 | 0 | 1 |
| `/reward-audit` | `RewardAudit` | `web/src/pages/RewardAudit.tsx` | Reward Audit | 0 | 0 | 1 |
| `/settings` | `Settings` | `web/src/pages/Settings.tsx` | Settings | 0 | 0 | 0 |

## Per-Page Notes

### `AdkDeploy`
- File: `web/src/pages/AdkDeploy.tsx`
- Size: 217 lines
- Header title: Deploy ADK Agent
- Header description: Deploy your ADK agent to Google Cloud Run or Vertex AI
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `AdkImport`
- File: `web/src/pages/AdkImport.tsx`
- Size: 174 lines
- Header title: Import ADK Agent
- Header description: Import an agent from Google's Agent Developer Kit into AutoAgent
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `AgentSkills`
- File: `web/src/pages/AgentSkills.tsx`
- Size: 310 lines
- Header title: (No PageHeader title)
- Header description: (No PageHeader description)
- Data hooks: `useQuery`=0, `useMutation`=4
- API interaction sites (`fetch` / `api.*`): 1

### `AgentStudio`
- File: `web/src/pages/AgentStudio.tsx`
- Size: 346 lines
- Header title: Agent Studio
- Header description: Update an agent in natural language and watch the draft mutate live.
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `Assistant`
- File: `web/src/pages/Assistant.tsx`
- Size: 278 lines
- Header title: Upload files
- Header description: (No PageHeader description)
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `AutoFix`
- File: `web/src/pages/AutoFix.tsx`
- Size: 171 lines
- Header title: AutoFix Copilot
- Header description: Generate constrained, one-step improvement proposals with diff previews and apply them through eval + canary checks.
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `BlameMap`
- File: `web/src/pages/BlameMap.tsx`
- Size: 187 lines
- Header title: Blame Map
- Header description: Top failure clusters ranked by impact with contributing traces
- Data hooks: `useQuery`=1, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 1

### `BuilderDemo`
- File: `web/src/pages/BuilderDemo.tsx`
- Size: 491 lines
- Header title: (No PageHeader title)
- Header description: (No PageHeader description)
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 5

### `BuilderWorkspace`
- File: `web/src/pages/BuilderWorkspace.tsx`
- Size: 691 lines
- Header title: (No PageHeader title)
- Header description: (No PageHeader description)
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `ChangeReview`
- File: `web/src/pages/ChangeReview.tsx`
- Size: 445 lines
- Header title: Change Review
- Header description: Review proposed changes with diffs, metrics, and confidence scores before applying
- Data hooks: `useQuery`=1, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 1

### `Configs`
- File: `web/src/pages/Configs.tsx`
- Size: 190 lines
- Header title: No configurations found
- Header description: Config versions appear after initialization and optimization cycles.
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `ContextWorkbench`
- File: `web/src/pages/ContextWorkbench.tsx`
- Size: 302 lines
- Header title: Context Workbench
- Header description: Analyze context growth, simulate compaction strategies, and measure handoff fidelity and memory staleness.
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `Conversations`
- File: `web/src/pages/Conversations.tsx`
- Size: 228 lines
- Header title: Conversations
- Header description: Inspect production interactions, tool traces, and failure signals to guide optimization work.
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `CxDeploy`
- File: `web/src/pages/CxDeploy.tsx`
- Size: 263 lines
- Header title: CX Deploy & Widget
- Header description: Deploy to CX Agent Studio environments and generate web widget embed code
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `CxImport`
- File: `web/src/pages/CxImport.tsx`
- Size: 181 lines
- Header title: Import CX Agent
- Header description: Import an agent from Google Cloud CX Agent Studio into AutoAgent
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `Dashboard`
- File: `web/src/pages/Dashboard.tsx`
- Size: 676 lines
- Header title: Karpathy Loop Scorecard
- Header description: Simplicity-first: 2 hard gates + 4 primary metrics.
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 1

### `Demo`
- File: `web/src/pages/Demo.tsx`
- Size: 442 lines
- Header title: Demo
- Header description: Failed to load demo scenario
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 1

### `Deploy`
- File: `web/src/pages/Deploy.tsx`
- Size: 266 lines
- Header title: No deployment status
- Header description: Initialize and deploy a config version to begin rollout management.
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `EvalDetail`
- File: `web/src/pages/EvalDetail.tsx`
- Size: 260 lines
- Header title: (No PageHeader title)
- Header description: (No PageHeader description)
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `EvalRuns`
- File: `web/src/pages/EvalRuns.tsx`
- Size: 375 lines
- Header title: Eval Runs
- Header description: Launch evaluations, inspect progress, and compare the quality impact of different runs.
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `EventLogPage`
- File: `web/src/pages/EventLog.tsx`
- Size: 67 lines
- Header title: System Event Log
- Header description: Append-only timeline for mutations, evals, promotions, rollbacks, budget gates, and human overrides.
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `Experiments`
- File: `web/src/pages/Experiments.tsx`
- Size: 126 lines
- Header title: Experiments
- Header description: Reviewable experiment cards with hypothesis, diff, and results
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `IntelligenceStudio`
- File: `web/src/pages/IntelligenceStudio.tsx`
- Size: 568 lines
- Header title: Intelligence Studio
- Header description: Operationalize transcript archives, ask natural-language questions about conversation failure, and turn insights into reviewable agent changes.
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `JudgeOps`
- File: `web/src/pages/JudgeOps.tsx`
- Size: 233 lines
- Header title: Judge Ops
- Header description: Version judges, collect human corrections, track calibration drift, and prioritize disagreement review.
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `Knowledge`
- File: `web/src/pages/Knowledge.tsx`
- Size: 11 lines
- Header title: (No PageHeader title)
- Header description: (No PageHeader description)
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `LiveOptimize`
- File: `web/src/pages/LiveOptimize.tsx`
- Size: 210 lines
- Header title: (No PageHeader title)
- Header description: (No PageHeader description)
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `LoopMonitor`
- File: `web/src/pages/LoopMonitor.tsx`
- Size: 223 lines
- Header title: Loop Monitor
- Header description: Observe continuous optimization cycles in real time and intervene when needed.
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `Notifications`
- File: `web/src/pages/Notifications.tsx`
- Size: 392 lines
- Header title: Notifications
- Header description: Configure alerts for agent health, deployments, and optimization events
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `Opportunities`
- File: `web/src/pages/Opportunities.tsx`
- Size: 62 lines
- Header title: Opportunity Queue
- Header description: Ranked optimization opportunities from failure analysis
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `Optimize`
- File: `web/src/pages/Optimize.tsx`
- Size: 433 lines
- Header title: Optimize
- Header description: Run optimization cycles and inspect exactly which candidate changes were accepted or rejected.
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `PolicyCandidates`
- File: `web/src/pages/PolicyCandidates.tsx`
- Size: 417 lines
- Header title: Policy Candidates
- Header description: Manage RL training jobs, evaluate policy artifacts with OPE, and promote or roll back candidates.
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 1

### `PreferenceInbox`
- File: `web/src/pages/PreferenceInbox.tsx`
- Size: 297 lines
- Header title: Preference Inbox
- Header description: Collect and manage human preference pairs used for RLHF fine-tuning and reward model training.
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 1

### `ProjectMemory`
- File: `web/src/pages/ProjectMemory.tsx`
- Size: 227 lines
- Header title: Project Memory
- Header description: View and edit your AUTOAGENT.md project memory — identity, constraints, patterns, and preferences
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `Registry`
- File: `web/src/pages/Registry.tsx`
- Size: 259 lines
- Header title: Registry Browser
- Header description: Browse and inspect skills, policies, tool contracts, and handoff schemas
- Data hooks: `useQuery`=3, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 1

### `Reviews`
- File: `web/src/pages/Reviews.tsx`
- Size: 11 lines
- Header title: (No PageHeader title)
- Header description: (No PageHeader description)
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `RewardAudit`
- File: `web/src/pages/RewardAudit.tsx`
- Size: 466 lines
- Header title: Reward Audit
- Header description: Run challenge suites, inspect audit findings, evaluate OPE reports, and detect sycophancy in reward models.
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 1

### `RewardStudio`
- File: `web/src/pages/RewardStudio.tsx`
- Size: 381 lines
- Header title: Reward Studio
- Header description: Define, audit, and validate reward functions that drive RLHF training and policy optimization.
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 1

### `Runbooks`
- File: `web/src/pages/Runbooks.tsx`
- Size: 253 lines
- Header title: Runbooks
- Header description: Browse and apply runbooks — curated bundles of skills, policies, and tool contracts
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `Sandbox`
- File: `web/src/pages/Sandbox.tsx`
- Size: 11 lines
- Header title: (No PageHeader title)
- Header description: (No PageHeader description)
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `ScorerStudio`
- File: `web/src/pages/ScorerStudio.tsx`
- Size: 385 lines
- Header title: NL Scorer Studio
- Header description: Define evaluation scorers from natural language, compile to dimensions, refine, and test
- Data hooks: `useQuery`=2, `useMutation`=4
- API interaction sites (`fetch` / `api.*`): 1

### `Settings`
- File: `web/src/pages/Settings.tsx`
- Size: 125 lines
- Header title: Settings
- Header description: Reference paths, quick links, and operator shortcuts for the AutoAgent control plane.
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `Skills`
- File: `web/src/pages/Skills.tsx`
- Size: 676 lines
- Header title: Skills Marketplace
- Header description: Build-time optimization strategies and run-time agent capabilities as one composable primitive.
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `Traces`
- File: `web/src/pages/Traces.tsx`
- Size: 167 lines
- Header title: Traces
- Header description: ADK event traces and spans for diagnosis
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0

### `WhatIf`
- File: `web/src/pages/WhatIf.tsx`
- Size: 11 lines
- Header title: (No PageHeader title)
- Header description: (No PageHeader description)
- Data hooks: `useQuery`=0, `useMutation`=0
- API interaction sites (`fetch` / `api.*`): 0


### 5.3 Page-by-page tutorial guidance

The section below is imported from project `docs/app-guide.md` (heading-adjusted), which includes data source and action guidance for major pages.

##### Web App Guide

This guide walks through all 31 pages in the AutoAgent VNextCC web console and explains what each page is for, what data it uses, and how operators typically use it in practice.

The app is served by the FastAPI server at `http://localhost:8000` when you run:

```bash
autoagent server
```

**New in this release:**
- **AgentStudio** — Interactive chat interface for natural language agent editing
- **IntelligenceStudio** — Transcript archive analytics and Q&A with auto-generated insights

#### Route Map

All 31 pages in the web console:

| Page | Route | Primary job |
|---|---|---|
| **Dashboard** | `/` | System health snapshot with pulse indicator, journey timeline, recommendations |
| **AgentStudio** | `/agent-studio` | Interactive chat for describing agent changes in natural language |
| **IntelligenceStudio** | `/intelligence-studio` | Transcript archive ingestion, analytics, Q&A, agent generation |
| **Eval Runs** | `/evals` | Start eval runs and compare run-level outcomes |
| **Eval Detail** | `/evals/:id` | Investigate one run at per-case granularity |
| **Optimize** | `/optimize` | Trigger optimization cycles and inspect gate outcomes |
| **Live Optimize** | `/live-optimize` | Real-time optimization with Server-Sent Events streaming |
| **Configs** | `/configs` | Browse versioned configs, inspect YAML, diff versions |
| **Conversations** | `/conversations` | Explore user conversations, filters, and tool traces |
| **Deploy** | `/deploy` | Manage active/canary versions, rollback, and history |
| **Loop Monitor** | `/loop` | Run/stop continuous loop and watch cycle-by-cycle progress |
| **Opportunities** | `/opportunities` | Optimization opportunities from failure analysis |
| **Experiments** | `/experiments` | Experiment tracking and A/B test results |
| **Traces** | `/traces` | Structured trace events and span analysis |
| **Event Log** | `/events` | Real-time event stream from optimization loop |
| **AutoFix** | `/autofix` | Reviewable fix proposals from failure patterns |
| **JudgeOps** | `/judge-ops` | Judge versioning, calibration, and drift monitoring |
| **Context Workbench** | `/context` | Context window analysis and compaction strategies |
| **Change Review** | `/changes` | Review and approve proposed config changes |
| **Runbooks** | `/runbooks` | Curated bundles of skills, policies, and tools |
| **Skills** | `/skills` | Executable optimization strategies for the proposer |
| **Project Memory** | `/memory` | Persistent project context (AUTOAGENT.md) with auto-update |
| **Registry** | `/registry` | Modular registry of skills, policies, tools, handoffs |
| **Blame Map** | `/blame` | Failure clustering and root cause attribution |
| **Scorer Studio** | `/scorer-studio` | Create and refine eval scorers from natural language |
| **CX Import** | `/cx/import` | Import Google CX Agent Studio agents |
| **CX Deploy** | `/cx/deploy` | Deploy to CX environments with widget generation |
| **ADK Import** | `/adk/import` | Import Google Agent Development Kit agents |
| **ADK Deploy** | `/adk/deploy` | Deploy ADK agents to Cloud Run or Vertex AI |
| **Agent Skills** | `/agent-skills` | Agent capability gap analysis and skill generation |
| **Settings** | `/settings` | Operator shortcuts and runtime path reference |

#### Global UX

##### Layout and Navigation

- Left sidebar includes all 29 pages and highlights the active route.
- Sidebar collapses into a mobile drawer on smaller screens.
- Header includes page title plus breadcrumbs:
  - Example: `Eval Runs / Run <id>` on `/evals/:id`.

##### Command Palette

Open the global command palette with `Cmd+K` (or `Ctrl+K` on Windows/Linux).

It includes:
- Static actions (new eval, optimize, deploy, dashboard, conversations)
- Recent eval runs
- Recent config versions
- Recent conversations

##### Keyboard Shortcuts

Global shortcuts (ignored while typing in form fields):
- `n` -> open new eval flow (`/evals?new=1`)
- `o` -> open optimize flow (`/optimize?new=1`)
- `d` -> open deploy flow (`/deploy?new=1`)

##### Toast Notifications

Asynchronous operations show toast feedback for start/success/failure:
- Eval started/completed
- Optimization started/completed/failed
- Deploy and rollback results
- Loop start/stop results

##### Real-Time WebSocket Updates

The app maintains a persistent WebSocket connection to:

```text
ws://<host>/ws
```

Message types used by the UI:
- `eval_complete`
- `optimize_complete`
- `loop_cycle`

#### Page Walkthrough

#### Dashboard (`/`)

Purpose: quickly answer “is the system healthy right now?”

##### What you see

- **Health Pulse** — Living SVG health indicator with color-coded pulse speed (green 3s, amber 1.5s, red 0.8s)
- **Metric cards:**
  - Success rate
  - Average latency
  - Error rate
  - Safety violation rate
  - Average cost
  - Total conversations
- **Journey Timeline** — Horizontal scrollable optimization history with animated SVG line drawing
- **Score trajectory chart** from optimization history
- **Recent optimization timeline** entries with accept/reject status
- **Recommended next actions** with exact CLI commands

##### Data sources

- `GET /api/health`
- `GET /api/health/scorecard`
- `GET /api/optimize/history`

##### Typical actions

- Run a fresh eval (`New Eval`)
- Jump to optimization history/details
- Refresh health data
- Click timeline nodes to view config diffs
- Follow recommended next actions

---

#### AgentStudio (`/agent-studio`)

Purpose: describe agent changes in plain language without writing config YAML.

##### What you see

- **Chat interface** — Intercom-style conversational UI
- **Sample prompts** — Quick-start examples:
  - “Make BillingAgent verify invoices before answering”
  - “Route shipping delays straight to RefundAgent”
  - “Tighten orchestrator handoffs so specialists inherit context”
  - “Add safety guardrails to prevent unauthorized PII disclosure”
- **Live draft mutations** — Real-time change preview on each user input
- **Change set cards** — Visual breakdown of proposed mutations:
  - Surface (prompts, routing, tools, policies)
  - Impact score (high/medium/low)
  - Change description in plain English
- **Metric impact visualization** — Before/after score estimates
- **Focus area detection** — Automatically identifies which config area needs attention

##### Data sources

- Client-side draft building (no API calls until apply)
- `POST /api/edit` — When user confirms changes

##### Typical actions

- Type natural language change request
- Review proposed mutations in change set
- Refine request in follow-up messages
- Apply changes with one click
- View diff in Configs page after apply

**Example workflow:**
1. Type: “Make the agent more empathetic in billing conversations”
2. Review change card: “prompts.root - Add empathy instructions”
3. Refine: “Also mention patience and acknowledgment”
4. Apply → Config v13 created with new instructions

---

#### IntelligenceStudio (`/intelligence-studio`)

Purpose: upload conversation archives, get automatic analytics, and generate agent improvements from transcript data.

##### What you see

- **Archive upload** — Drag-and-drop ZIP file ingestion
- **Processing status** — Real-time progress (parsing, analyzing, extracting)
- **Summary cards:**
  - Total transcripts
  - Language distribution (en, es, fr, etc.)
  - Intent distribution (order tracking, refunds, cancellations, etc.)
  - Transfer reasons (missing order number, policy gaps, escalations)
- **Insights panel** — Automatically extracted opportunities:
  - Severity (high/medium/low)
  - Category (routing, safety, latency, etc.)
  - Description with evidence count
  - Recommended action
- **Q&A interface** — Ask questions about transcript data:
  - “Why are people transferring to live support?”
  - “What should I change to improve this metric?”
- **Procedures & FAQs** — Auto-extracted from successful conversations
- **Missing intents** — Capabilities the agent lacks
- **Workflow recommendations** — Suggested process improvements
- **Test case generation** — Edge cases for eval suite
- **One-click apply** — Create change card from insight

##### Data sources

- `POST /api/intelligence/archive` — ZIP upload and processing
- `GET /api/intelligence/reports` — List all reports
- `GET /api/intelligence/reports/{id}` — Report details
- `POST /api/intelligence/reports/{id}/ask` — Q&A over transcript data
- `POST /api/intelligence/reports/{id}/apply` — Create change card from insight

##### Typical actions

- Upload transcript archive (ZIP with JSON/CSV/TXT files)
- Review summary metrics and intent distribution
- Explore insights with high severity
- Ask questions: “Why are refund requests failing?”
- Apply top insight to create change card
- Review drafted change in Change Review page
- Approve and deploy fix

**Example workflow:**
1. Upload `march_2026_support.zip` (1,247 conversations)
2. Review summary: 42% of refund requests routed to wrong agent
3. Click insight: “Add 'refund' keywords to billing_agent routing rules”
4. Ask: “What exact phrases are customers using?”
5. Review evidence: “money back”, “reimbursement”, “refund my order”
6. Apply insight → Change card created with keyword additions
7. Approve in Change Review → Deploy with canary

#### Eval Runs (`/evals`)

Purpose: create and track eval runs, then compare run outcomes.

##### What you see

- “Start New Evaluation” form:
  - optional config version
  - optional category filter
- Runs table with status/progress/score/case counts
- Comparison mode for any two runs side-by-side

##### Data sources

- `GET /api/eval/runs`
- `GET /api/config/list`
- `POST /api/eval/run`
- WebSocket `eval_complete`

##### Typical actions

- Launch a run against active config
- Launch a category-specific run (`safety`, etc.)
- Compare two completed runs before choosing a deploy candidate

#### Eval Detail (`/evals/:id`)

Purpose: inspect one eval run deeply.

##### What you see

- Run header with status, timestamp, pass count, and safety failure callout
- Composite score block
- Score bars for quality/safety/latency/cost
- Per-case table with:
  - category filter
  - pass/fail filter
  - sorting (quality, latency, case id)
- Expandable case row for deeper details

##### Data sources

- `GET /api/eval/runs/{run_id}`
- If run is still active (`409`), UI falls back to task data from `GET /api/eval/runs`

##### Typical actions

- Diagnose failing cases
- Identify regression signatures before optimizing/deploying

#### Optimize (`/optimize`)

Purpose: run one optimize cycle and inspect gate decisions.

##### What you see

- Optimization controls:
  - observation window
  - `force` toggle
- Active task progress (polling `/api/tasks/{id}`)
- Score trajectory chart across historical attempts
- Timeline of attempts with status badges
- Diff/details panel for selected attempt

##### Data sources

- `GET /api/optimize/history`
- `POST /api/optimize/run`
- `GET /api/tasks/{task_id}`
- WebSocket `optimize_complete`

##### Typical actions

- Trigger a cycle from current traffic state
- Confirm whether rejection reason is safety/no-improvement/regression/invalid/noop
- Review config diffs before deployment decisions

#### Configs (`/configs`)

Purpose: understand exactly what changed between config versions.

##### What you see

- Version list with status/hash/composite/timestamp
- YAML viewer for selected version
- Compare mode with side-by-side diff for two versions

##### Data sources

- `GET /api/config/list`
- `GET /api/config/show/{version}`
- `GET /api/config/diff?a={a}&b={b}`

##### Typical actions

- Validate accepted optimizer changes
- Confirm active/canary lineage before deploy

#### Conversations (`/conversations`)

Purpose: inspect real conversations and tool traces.

##### What you see

- Overview stats (visible total, success rate, avg latency, avg tokens)
- Filters: outcome, limit, search
- Conversation table with expandable detail panel
- Detailed conversation view with:
  - user and agent turns
  - tool call summaries
  - safety flags and error messages

##### Data sources

- `GET /api/conversations`

##### Typical actions

- Find failure examples to guide optimization
- Confirm specialist routing and tool behavior

#### Deploy (`/deploy`)

Purpose: promote stable configs safely.

##### What you see

- Active version card
- Canary version card + canary verdict block
- Deploy form:
  - version selection
  - strategy (`canary` or `immediate`)
- Deployment history table
- Rollback action for active canary

##### Data sources

- `GET /api/deploy/status`
- `POST /api/deploy`
- `POST /api/deploy/rollback`
- `GET /api/config/list`

##### Typical actions

- Deploy a candidate as canary
- Monitor verdict and rates
- Roll back immediately when canary underperforms

#### Loop Monitor (`/loop`)

Purpose: run continuous observe -> optimize -> deploy cycles.

##### What you see

- Loop control form (cycles, delay, window)
- Running/idle status and progress counters
- Success-rate trajectory chart
- Per-cycle cards with optimization/deploy/canary outcomes

##### Data sources

- `GET /api/loop/status`
- `POST /api/loop/start`
- `POST /api/loop/stop`
- WebSocket `loop_cycle`

##### Typical actions

- Launch overnight iterative runs
- Stop loop when degradation appears
- Review cycle-level acceptance/rejection cadence

#### Settings (`/settings`)

Purpose: operational quick-reference.

##### What you see

- Key project file paths (config, evals, storage)
- Keyboard shortcut reference
- Links to API docs (`/docs`, `/redoc`)

This page is informational and does not mutate system state.

#### Practical Operator Flows

#### Flow A: Baseline a new config

1. Open **Eval Runs** and launch a run for the target version.
2. Open **Eval Detail** and inspect failed cases + score distribution.
3. Open **Configs** and diff against active version.

#### Flow B: Improve reliability

1. Open **Conversations** and filter to `fail`/`error`.
2. Open **Optimize** and run a cycle with appropriate window.
3. Review attempt status and diff.
4. Open **Deploy** and canary deploy accepted versions.

#### Flow C: Continuous overnight iteration

1. Open **Loop Monitor**.
2. Start loop with target cycles and delay.
3. Monitor cycle cards and trajectory.
4. Stop loop if severe degradation appears.

#### Troubleshooting UI Data

- Dashboard empty: confirm conversation data exists (`autoagent status` / eval runs).
- Eval detail stuck in running: check task state via `GET /api/tasks/{task_id}`.
- Deploy history empty: ensure at least one deployment has occurred.
- No real-time updates: verify WebSocket connectivity to `/ws`.


### 5.4 Reading “every page, every widget, every interaction” safely

When you explore the UI as a beginner:

- Start in read-only pages first: Dashboard, Configs, Conversations, Traces.
- Move to action pages with side effects next: Optimize, AutoFix, Deploy, Changes.
- Use governance pages before production changes: Judge Ops, Notifications, Runbooks, Settings.
- Use builder and intelligence surfaces after you understand gating and approvals.

> ⚠️ Warning: Some pages expose operations that can mutate configs, run eval workloads, or trigger deploy behavior. Confirm environment and target before executing.

---

## 6. Builder Workspace Deep Dive

Builder Workspace is the primary authoring surface in this repo. It is mounted at `/`, `/builder`, and `/builder/*` route patterns.

### 6.1 Core UX model

Builder is organized into:

- Top bar (project, environment, mode, model, approval badge, pause toggle)
- Left rail (projects, sessions, tasks, favorites, notifications)
- Conversation pane (timeline of task entries/events/artifacts/proposals/approvals)
- Composer (prompt input + mode selector + slash command menu + attachments)
- Task drawer (running/completed tasks + pending approvals + controls)
- Inspector (tabbed context/details panel)

### 6.2 Execution modes

`ExecutionMode` values from source:

- `ask`
- `draft`
- `apply`
- `delegate`

How to think about them:

- `ask`: conversational exploration and analysis.
- `draft`: propose and stage without direct irreversible action.
- `apply`: execute direct changes through task pipeline.
- `delegate`: autonomous specialist execution, typically with stronger sandbox expectations.

> 💡 Tip: Default to `draft` for most teams until your approval and guardrail posture is mature.

### 6.3 Environments

Top bar environment selector values:

- `dev`
- `staging`
- `prod`

Environment is a first-class UI state and should align with your permission policy and deployment targets.

### 6.4 Composer and slash commands

Composer behaviors from source:

- Enter sends, Shift+Enter inserts newline.
- Typing `/` opens slash menu.
- Built-in slash commands:
  - `/plan`
  - `/improve`
  - `/trace`
  - `/eval`
  - `/skill`
  - `/guardrail`
  - `/compare`
  - `/branch`
  - `/deploy`
  - `/rollback`
  - `/memory`
  - `/permissions`

### 6.5 Task lifecycle and controls

Task statuses:

- `pending`
- `running`
- `paused`
- `completed`
- `failed`
- `cancelled`

Task drawer operations:

- Pause task
- Resume task
- Cancel task
- Fork task
- Approve request
- Reject request

### 6.6 Approval and permission model

Approval scope values:

- `once`
- `task`
- `project`

Privileged action values:

- `source_write`
- `external_network`
- `secret_access`
- `deployment`
- `benchmark_spend`

This allows granular policy: single-use approvals for high risk operations, broader grants for trusted workflows.

### 6.7 Inspector tabs

Inspector tab IDs and purpose:

- `overview`: current project + selected artifact snapshot.
- `diff`: file diff paths for selected artifact.
- `adk_graph`: ADK graph related artifact context.
- `evals`: attached eval bundle metrics.
- `traces`: trace bookmarks/evidence pointers.
- `skills`: runtime/buildtime skills + tool attachments.
- `guardrails`: active guardrail objects.
- `files`: project knowledge files.
- `config`: AGENTS.md / CLAUDE.md context + instruction memory panel.

### 6.8 Builder backend APIs

Builder front-end client maps to `/api/builder` endpoints for:

- Project CRUD
- Session lifecycle
- Task lifecycle + progress updates
- Proposal review
- Artifact retrieval and commenting
- Approval response
- Permission grant management
- Event listing and SSE stream
- Metrics snapshots
- Specialist invocation

### 6.9 Recommended beginner workflow in Builder

1. Select project and confirm `dev` environment.
2. Choose `draft` mode.
3. Ask for a plan with explicit constraints.
4. Inspect proposed artifacts in timeline and inspector tabs.
5. Approve only narrow-scope requests.
6. Run eval and inspect result deltas.
7. Promote to broader environment only after stable validation.

### 6.10 Common failure patterns in Builder

- Sending apply-mode instructions unintentionally.
- Forgetting environment context before approval.
- Ignoring failed task notifications in drawer.
- Approving project-wide permission grants too early.
- Interpreting a plan artifact as an executed change.

> ⚠️ Warning: “Task created” is not equivalent to “change safely deployed.” Always verify approvals, eval bundles, and deploy status explicitly.

---

## 7. Advanced Features

This chapter maps high-leverage advanced subsystems.

### 7.1 CX integration

Command group: `cx`

Typical flow:

1. `cx list` to inspect available agents.
2. `cx import` into AutoAgent config representation.
3. Optimize/evaluate locally.
4. `cx export` package candidate.
5. `cx deploy` to target environment.
6. Optionally generate widget via `cx widget`.

Advanced note:

- Deploy path includes options for project/location/credentials/snapshot and optional push behavior.

### 7.2 ADK integration

Command group: `adk`

Typical flow:

1. `adk import <path>`
2. Evaluate/optimize inside AutoAgent
3. `adk diff <path> --snapshot ...`
4. `adk export <path> --snapshot ...`
5. `adk deploy <path> --target cloud-run|vertex-ai`

### 7.3 Skill management (core skills + executable skills)

Core skills subsystem includes:

- Unified `Skill` model (`build` and `runtime` kinds)
- Store/loader/composer/validator/marketplace modules
- Dependency resolution and conflict detection
- Validation with schema + dependency + runtime test checks

Executable skill operations are exposed through CLI/API surfaces and registry workflows.

### 7.4 Notifications

Notifications page + `/api/notifications` supports:

- Webhook subscriptions
- Slack subscriptions
- Email subscriptions
- History and test delivery actions

Use notifications for safety incidents, deployment transitions, and loop lifecycle alerts.

### 7.5 Judge Ops

Judge Ops surfaces calibration and drift workflows.

Use cases:

- Identify scorer drift over time.
- Calibrate against human feedback.
- Detect disagreement concentrations before policy promotion.

### 7.6 AutoFix

AutoFix endpoints/commands support:

- Proposal generation (`suggest`)
- Proposal application (`apply`)
- History inspection (`history`)

This is best used with clear approval policy and post-apply eval checks.

### 7.7 Prompt optimization modes

Search and optimization strategies scale from simple to research-grade modes.

For teams new to AutoAgent:

- Start with `standard`/`adaptive` style operation.
- Move to research-grade strategies only after telemetry quality and gate discipline are strong.

### 7.8 Policy optimization and reward systems

Advanced command groups include:

- `reward`
- `rl`
- `pref`
- `policy candidates` UI surfaces
- `reward studio` and `reward audit` UI surfaces

These enable RLHF-style loops, reward definition/versioning, and canary/promote/rollback behavior for policy artifacts.

### 7.9 Datasets and outcomes

Dataset and outcomes groups expose:

- Dataset creation/versioning/splits/exports
- Outcome ingestion and calibration workflows

This is where business metrics and quality loops start to converge.

### 7.10 Sandbox, what-if, and impact analysis

Relevant APIs/pages:

- Sandbox scenario generation/comparison/testing
- What-if replay/project endpoints
- Impact analysis endpoint set

Use these before high-risk production pushes.

---

## 8. CLI Reference

This section is generated from `runner.py` so it tracks real command names, handlers, and decorator-defined options/arguments.

# CLI Command Inventory (Generated from runner.py)

Total commands: **112**

## adk

### `autoagent adk deploy`
- Purpose: Deploy ADK agent to Cloud Run or Vertex AI.
- Handler: `runner.py:5090` (`adk_deploy_cmd`)
- Arguments:
  - `@click.argument("path")`
- Options:
  - `@click.option("--target", type=click.Choice(["cloud-run", "vertex-ai"]), default="cloud-run", show_default=True)`
  - `@click.option("--project", required=True, help="GCP project ID.")`
  - `@click.option("--region", default="us-central1", show_default=True, help="GCP region.")`

### `autoagent adk diff`
- Purpose: Preview what would change on export.
- Handler: `runner.py:5153` (`adk_diff_cmd`)
- Arguments:
  - `@click.argument("path")`
- Options:
  - `@click.option("--snapshot", "-s", required=True, help="Snapshot directory path from import.")`

### `autoagent adk export`
- Purpose: Export optimized config back to ADK source files.
- Handler: `runner.py:5047` (`adk_export_cmd`)
- Arguments:
  - `@click.argument("path")`
- Options:
  - `@click.option("--output", "-o", help="Output directory for modified source files.")`
  - `@click.option("--snapshot", "-s", required=True, help="Snapshot directory path from import.")`
  - `@click.option("--dry-run", is_flag=True, help="Preview changes without writing files.")`

### `autoagent adk import`
- Purpose: Import an ADK agent from a local directory.
- Handler: `runner.py:5027` (`adk_import_cmd`)
- Arguments:
  - `@click.argument("path")`
- Options:
  - `@click.option("--output", "-o", default=".", show_default=True, help="Output directory for config and snapshot.")`

### `autoagent adk status`
- Purpose: Show ADK agent structure and config summary.
- Handler: `runner.py:5111` (`adk_status_cmd`)
- Arguments:
  - `@click.argument("path")`
- Options:
  - `@click.option("--json", "json_output", "-j", is_flag=True, help="Output as JSON.")`

## autofix

### `autoagent autofix apply`
- Purpose: Apply a specific AutoFix proposal.
- Handler: `runner.py:2299` (`autofix_apply`)
- Arguments:
  - `@click.argument("proposal_id", type=str)`

### `autoagent autofix history`
- Purpose: Show past AutoFix proposals and outcomes.
- Handler: `runner.py:2326` (`autofix_history`)
- Options:
  - `@click.option("--limit", default=20, show_default=True, type=int, help="Number of proposals to show.")`

### `autoagent autofix suggest`
- Purpose: Generate AutoFix proposals without applying them.
- Handler: `runner.py:2258` (`autofix_suggest`)

## core

### `autoagent autonomous`
- Purpose: Run autonomous optimization with scoped permissions.
- Handler: `runner.py:3922` (`autonomous`)
- Options:
  - `@click.option("--scope", type=click.Choice(["dev", "staging", "production"]), default="dev")`
  - `@click.option("--yes", is_flag=True)`
  - `@click.option("--cycles", default=3)`
  - `@click.option("--max-loop-cycles", default=10)`

## benchmark

### `autoagent benchmark run`
- Purpose: Run a benchmark suite.
- Handler: `runner.py:5283` (`benchmark_run`)
- Arguments:
  - `@click.argument("benchmark_name")`
- Options:
  - `@click.option("--cycles", default=1, help="Number of benchmark cycles")`

## core

### `autoagent build`
- Purpose: Build an agent artifact from natural language and scaffold eval/deploy handoff files.
- Handler: `runner.py:786` (`build_agent`)
- Arguments:
  - `@click.argument("prompt")`
- Options:
  - `@click.option( "--connector", "connectors", multiple=True, help="Connector to include (repeatable). Example: --connector Shopify", )`
  - `@click.option("--output-dir", default=".", show_default=True, help="Directory for generated build artifacts.")`
  - `@click.option("--json", "json_output", "-j", is_flag=True, help="Output artifact as JSON only.")`

## changes

### `autoagent changes approve`
- Purpose: Approve/apply a change card (alias for `autoagent review apply`).
- Handler: `runner.py:2715` (`changes_approve`)
- Arguments:
  - `@click.argument("card_id")`

### `autoagent changes export`
- Purpose: Export a change card markdown (alias for `autoagent review export`).
- Handler: `runner.py:2756` (`changes_export`)
- Arguments:
  - `@click.argument("card_id")`

### `autoagent changes list`
- Purpose: List pending change cards (alias for `autoagent review list`).
- Handler: `runner.py:2678` (`changes_list`)
- Options:
  - `@click.option("--limit", default=20, show_default=True, type=int, help="Number of cards to show.")`

### `autoagent changes reject`
- Purpose: Reject a change card (alias for `autoagent review reject`).
- Handler: `runner.py:2735` (`changes_reject`)
- Arguments:
  - `@click.argument("card_id")`
- Options:
  - `@click.option("--reason", default="", help="Reason for rejection.")`

### `autoagent changes show`
- Purpose: Show a specific change card (alias for `autoagent review show`).
- Handler: `runner.py:2700` (`changes_show`)
- Arguments:
  - `@click.argument("card_id")`

## config

### `autoagent config diff`
- Purpose: Diff two config versions.
- Handler: `runner.py:1313` (`config_diff`)
- Arguments:
  - `@click.argument("v1", type=int)`
  - `@click.argument("v2", type=int)`
- Options:
  - `@click.option("--configs-dir", default=CONFIGS_DIR, show_default=True, help="Configs directory.")`

### `autoagent config list`
- Purpose: List all config versions.
- Handler: `runner.py:1231` (`config_list`)
- Options:
  - `@click.option("--configs-dir", default=CONFIGS_DIR, show_default=True, help="Configs directory.")`

### `autoagent config migrate`
- Purpose: Migrate old optimizer config format to new optimization section.
- Handler: `runner.py:1349` (`config_migrate`)
- Arguments:
  - `@click.argument("input_file", type=click.Path(exists=True))`
- Options:
  - `@click.option("--output", default=None, help="Output file path (prints to stdout if omitted).")`

### `autoagent config show`
- Purpose: Show config YAML for a version (defaults to active).
- Handler: `runner.py:1272` (`config_show`)
- Arguments:
  - `@click.argument("version", type=int, required=False)`
- Options:
  - `@click.option("--configs-dir", default=CONFIGS_DIR, show_default=True, help="Configs directory.")`

## context

### `autoagent context analyze`
- Purpose: Analyze context utilization for a trace.
- Handler: `runner.py:2457` (`context_analyze`)
- Options:
  - `@click.option("--trace", "trace_id", required=True, help="Trace ID to analyze.")`

### `autoagent context report`
- Purpose: Show aggregate context health report.
- Handler: `runner.py:2526` (`context_report`)

### `autoagent context simulate`
- Purpose: Simulate a compaction strategy.
- Handler: `runner.py:2502` (`context_simulate`)
- Options:
  - `@click.option("--strategy", default="balanced", show_default=True, type=click.Choice(["aggressive", "balanced", "conservative"]), help="Compaction strategy to simulate.")`

## curriculum

### `autoagent curriculum apply`
- Purpose: Apply a curriculum batch to the active eval set.
- Handler: `runner.py:3549` (`curriculum_apply`)
- Arguments:
  - `@click.argument("batch_id")`
- Options:
  - `@click.option("--output-dir", default=".autoagent/curriculum", show_default=True, help="Curriculum directory")`
  - `@click.option("--eval-cases-dir", default="evals/cases", show_default=True, help="Eval cases directory")`

### `autoagent curriculum generate`
- Purpose: Generate a new curriculum batch from recent failures.
- Handler: `runner.py:3415` (`curriculum_generate`)
- Options:
  - `@click.option("--limit", default=10, show_default=True, help="Max failure clusters to process")`
  - `@click.option("--prompts-per-cluster", default=3, show_default=True, help="Prompts to generate per cluster")`
  - `@click.option("--adversarial-ratio", default=0.2, show_default=True, help="Ratio of adversarial variants")`
  - `@click.option("--db", default=DB_PATH, show_default=True, help="Conversation database path")`
  - `@click.option("--output-dir", default=".autoagent/curriculum", show_default=True, help="Output directory")`

### `autoagent curriculum list`
- Purpose: List generated curriculum batches.
- Handler: `runner.py:3498` (`curriculum_list`)
- Options:
  - `@click.option("--limit", default=20, show_default=True, help="Max batches to list")`
  - `@click.option("--output-dir", default=".autoagent/curriculum", show_default=True, help="Curriculum directory")`
  - `@click.option("--json", "json_output", is_flag=True, help="Output as JSON")`

## cx

### `autoagent cx compat`
- Purpose: Show CX Agent Studio compatibility matrix.
- Handler: `runner.py:4838` (`cx_compat`)

### `autoagent cx deploy`
- Purpose: Deploy agent to a CX environment.
- Handler: `runner.py:4939` (`cx_deploy_cmd`)
- Options:
  - `@click.option("--project", required=True, help="GCP project ID.")`
  - `@click.option("--location", default="global", show_default=True)`
  - `@click.option("--agent", "agent_id", required=True, help="CX agent ID.")`
  - `@click.option("--environment", default="production", show_default=True)`
  - `@click.option("--credentials", default=None, help="Path to service account JSON.")`

### `autoagent cx export`
- Purpose: Export optimized config back to CX Agent Studio.
- Handler: `runner.py:4899` (`cx_export_cmd`)
- Options:
  - `@click.option("--project", required=True, help="GCP project ID.")`
  - `@click.option("--location", default="global", show_default=True)`
  - `@click.option("--agent", "agent_id", required=True, help="CX agent ID.")`
  - `@click.option("--config", "config_path", required=True, help="AutoAgent config YAML path.")`
  - `@click.option("--snapshot", "snapshot_path", required=True, help="CX snapshot JSON from import.")`
  - `@click.option("--credentials", default=None, help="Path to service account JSON.")`
  - `@click.option("--dry-run", is_flag=True, help="Preview changes without pushing.")`

### `autoagent cx import`
- Purpose: Import a CX agent into AutoAgent format.
- Handler: `runner.py:4871` (`cx_import_cmd`)
- Options:
  - `@click.option("--project", required=True, help="GCP project ID.")`
  - `@click.option("--location", default="global", show_default=True)`
  - `@click.option("--agent", "agent_id", required=True, help="CX agent ID.")`
  - `@click.option("--output-dir", default=".", show_default=True, help="Output directory.")`
  - `@click.option("--credentials", default=None, help="Path to service account JSON.")`
  - `@click.option("--include-test-cases/--no-test-cases", default=True, show_default=True)`

### `autoagent cx list`
- Purpose: List CX agents in a project.
- Handler: `runner.py:4849` (`cx_list`)
- Options:
  - `@click.option("--project", required=True, help="GCP project ID.")`
  - `@click.option("--location", default="global", show_default=True, help="Agent location.")`
  - `@click.option("--credentials", default=None, help="Path to service account JSON.")`

### `autoagent cx status`
- Purpose: Show CX agent deployment status.
- Handler: `runner.py:4993` (`cx_status_cmd`)
- Options:
  - `@click.option("--project", required=True, help="GCP project ID.")`
  - `@click.option("--location", default="global", show_default=True)`
  - `@click.option("--agent", "agent_id", required=True, help="CX agent ID.")`
  - `@click.option("--credentials", default=None, help="Path to service account JSON.")`

### `autoagent cx widget`
- Purpose: Generate a chat-messenger web widget HTML file.
- Handler: `runner.py:4958` (`cx_widget_cmd`)
- Options:
  - `@click.option("--project", required=True, help="GCP project ID.")`
  - `@click.option("--location", default="global", show_default=True)`
  - `@click.option("--agent", "agent_id", required=True, help="CX agent ID.")`
  - `@click.option("--title", default="Agent", show_default=True, help="Chat widget title.")`
  - `@click.option("--color", default="#1a73e8", show_default=True, help="Primary color hex.")`
  - `@click.option("--output", "output_path", default=None, help="Output HTML file path.")`

## dataset

### `autoagent dataset create`
- Purpose: Create a new dataset.
- Handler: `runner.py:5195` (`dataset_create`)
- Arguments:
  - `@click.argument("name")`
- Options:
  - `@click.option("--description", default="", help="Dataset description")`

### `autoagent dataset list`
- Purpose: List all datasets.
- Handler: `runner.py:5204` (`dataset_list`)

### `autoagent dataset stats`
- Purpose: Show dataset statistics.
- Handler: `runner.py:5215` (`dataset_stats`)
- Arguments:
  - `@click.argument("dataset_id")`

## demo

### `autoagent demo quickstart`
- Purpose: Interactive demo: seed data, run one optimise cycle, show results.
- Handler: `runner.py:4101` (`demo_quickstart`)
- Options:
  - `@click.option("--dir", "target_dir", default=".", show_default=True, help="Directory to initialize in.")`
  - `@click.option("--open/--no-open", "auto_open", default=True, help="Auto-open web console after completion.")`

### `autoagent demo vp`
- Purpose: VP-ready demo with 5-act storytelling structure.
- Handler: `runner.py:4209` (`demo_vp`)
- Options:
  - `@click.option("--agent-name", default="Acme Support Bot", show_default=True, help="Agent name for the demo scenario.")`
  - `@click.option("--company", default="Acme Corp", show_default=True, help="Company name for the demo scenario.")`
  - `@click.option("--no-pause", is_flag=True, default=False, help="Skip dramatic pauses between acts.")`
  - `@click.option("--web", is_flag=True, default=False, help="Auto-start server and open browser after demo.")`

## core

### `autoagent deploy`
- Purpose: Deploy a config version.
- Handler: `runner.py:1399` (`deploy`)
- Options:
  - `@click.option("--config-version", type=int, default=None, help="Config version to deploy. Defaults to latest accepted.")`
  - `@click.option("--strategy", type=click.Choice(["canary", "immediate"]), default="canary", show_default=True, help="Deployment strategy.")`
  - `@click.option("--configs-dir", default=CONFIGS_DIR, show_default=True, help="Configs directory.")`
  - `@click.option("--db", default=DB_PATH, show_default=True, help="Conversation store DB.")`
  - `@click.option( "--target", type=click.Choice(["autoagent", "cx-studio"]), default="autoagent", show_default=True, help="Deployment target.", )`
  - `@click.option("--project", default=None, help="GCP project ID (required for CX push).")`
  - `@click.option("--location", default="global", show_default=True, help="CX agent location.")`
  - `@click.option("--agent-id", default=None, help="CX agent ID (required for CX push).")`
  - `@click.option("--snapshot", default=None, help="CX snapshot JSON path from `autoagent cx import`.")`
  - `@click.option("--credentials", default=None, help="Path to service account JSON for CX calls.")`
  - `@click.option("--output", default=None, help="Output path for CX export package JSON.")`
  - `@click.option("--push/--no-push", default=False, show_default=True, help="Push to CX now (otherwise package only).")`

### `autoagent diagnose`
- Purpose: Run failure diagnosis and optionally fix issues interactively.
- Handler: `runner.py:4728` (`diagnose`)
- Options:
  - `@click.option("--interactive", "-i", is_flag=True, help="Interactive diagnosis session.")`
  - `@click.option("--json", "json_output", "-j", is_flag=True, help="Output as JSON.")`
  - `@click.option("--db", default=DB_PATH, show_default=True)`
  - `@click.option("--configs-dir", default=CONFIGS_DIR, show_default=True)`
  - `@click.option("--memory-db", default=MEMORY_DB, show_default=True)`

### `autoagent doctor`
- Purpose: Check system health and configuration.
- Handler: `runner.py:1940` (`doctor`)
- Options:
  - `@click.option("--config", "config_path", default="autoagent.yaml", show_default=True, help="Path to runtime config YAML.")`

### `autoagent edit`
- Purpose: Apply natural language edits to agent config.
- Handler: `runner.py:4466` (`edit`)
- Arguments:
  - `@click.argument("description", required=False)`
- Options:
  - `@click.option("--interactive", "-i", is_flag=True, help="Multi-turn editing session.")`
  - `@click.option("--dry-run", is_flag=True, help="Show proposed changes without applying.")`
  - `@click.option("--json", "json_output", "-j", is_flag=True, help="Output as JSON.")`
  - `@click.option("--db", default=DB_PATH, show_default=True, help="Conversation store DB.")`
  - `@click.option("--configs-dir", default=CONFIGS_DIR, show_default=True, help="Configs directory.")`

## eval

### `autoagent eval list`
- Purpose: List recent eval runs.
- Handler: `runner.py:998` (`eval_list`)

### `autoagent eval results`
- Purpose: View eval results from a previous run.
- Handler: `runner.py:966` (`eval_results`)
- Options:
  - `@click.option("--run-id", default=None, help="Run ID to show results for.")`
  - `@click.option("--file", "results_file", default=None, help="Path to results JSON file.")`

### `autoagent eval run`
- Purpose: Run eval suite against a config.
- Handler: `runner.py:873` (`eval_run`)
- Options:
  - `@click.option("--config", "config_path", default=None, help="Path to config YAML.")`
  - `@click.option("--suite", default=None, help="Path to eval cases directory.")`
  - `@click.option("--dataset", default=None, help="Path to eval dataset (.jsonl or .csv).")`
  - `@click.option("--split", "dataset_split", default="all", type=click.Choice(["train", "test", "all"]), show_default=True, help="Dataset split to evaluate when using --dataset.")`
  - `@click.option("--category", default=None, help="Run only a specific category.")`
  - `@click.option("--output", default=None, help="Write results JSON to file.")`
  - `@click.option("--json", "json_output", "-j", is_flag=True, help="Output as JSON.")`

## core

### `autoagent explain`
- Purpose: Generate a plain-English summary of the agent's current state.
- Handler: `runner.py:4537` (`explain`)
- Options:
  - `@click.option("--verbose", is_flag=True, default=False, help="Show detailed breakdown.")`
  - `@click.option("--db", default=DB_PATH, show_default=True, help="Conversation store DB.")`
  - `@click.option("--configs-dir", default=CONFIGS_DIR, show_default=True, help="Configs directory.")`
  - `@click.option("--memory-db", default=MEMORY_DB, show_default=True, help="Optimizer memory DB.")`
  - `@click.option("--json", "json_output", "-j", is_flag=True, help="Output as JSON.")`

### `autoagent full-auto`
- Purpose: Run optimization + loop in dangerous full-auto mode.
- Handler: `runner.py:3873` (`full_auto`)
- Options:
  - `@click.option("--cycles", default=5, show_default=True, type=int, help="Optimization cycles to run.")`
  - `@click.option("--max-loop-cycles", default=20, show_default=True, type=int, help="Continuous loop cycles after optimize.")`
  - `@click.option("--yes", "acknowledge", is_flag=True, default=False, help="Acknowledge dangerous mode and skip permission-style gates.")`

### `autoagent init`
- Purpose: Scaffold a new AutoAgent project with config, eval suite, and structure.
- Handler: `runner.py:687` (`init_project`)
- Options:
  - `@click.option("--template", default="customer-support", show_default=True, type=click.Choice(["customer-support", "minimal"]), help="Project template to scaffold.")`
  - `@click.option("--dir", "target_dir", default=".", show_default=True, help="Directory to initialize in.")`
  - `@click.option("--agent-name", default="My Agent", show_default=True, help="Agent name for AUTOAGENT.md.")`
  - `@click.option("--platform", default="Google ADK", show_default=True, help="Platform for AUTOAGENT.md.")`
  - `@click.option("--with-synthetic-data/--no-synthetic-data", default=True, show_default=True, help="Seed synthetic conversations and evals.")`

## judges

### `autoagent judges calibrate`
- Purpose: Sample cases for human calibration review.
- Handler: `runner.py:2392` (`judges_calibrate`)
- Options:
  - `@click.option("--sample", default=50, show_default=True, type=int, help="Number of cases to sample.")`
  - `@click.option("--judge-id", default=None, help="Filter to a specific judge.")`

### `autoagent judges drift`
- Purpose: Show drift report for all judges.
- Handler: `runner.py:2422` (`judges_drift`)

### `autoagent judges list`
- Purpose: Show active judges with version and agreement stats.
- Handler: `runner.py:2362` (`judges_list`)

## core

### `autoagent logs`
- Purpose: Browse conversation logs.
- Handler: `runner.py:1904` (`logs`)
- Options:
  - `@click.option("--limit", default=20, show_default=True, type=int, help="Number of logs to show.")`
  - `@click.option("--outcome", default=None, type=click.Choice(["success", "fail", "error", "abandon"]), help="Filter by outcome.")`
  - `@click.option("--db", default=DB_PATH, show_default=True, help="Conversation store DB.")`

### `autoagent loop`
- Purpose: Run the continuous autoresearch loop.
- Handler: `runner.py:1549` (`loop`)
- Options:
  - `@click.option("--max-cycles", default=50, show_default=True, type=int, help="Maximum optimization cycles.")`
  - `@click.option("--stop-on-plateau", is_flag=True, default=False, help="Stop if no improvement for 5 consecutive cycles.")`
  - `@click.option("--delay", default=1.0, show_default=True, type=float, help="Seconds between cycles.")`
  - `@click.option("--schedule", "schedule_mode", default=None, type=click.Choice(["continuous", "interval", "cron"]), help="Scheduling mode. Defaults to autoagent.yaml loop.schedule_mode.")`
  - `@click.option("--interval-minutes", default=None, type=float, help="Interval minutes for --schedule interval.")`
  - `@click.option("--cron", "cron_expression", default=None, help="Cron expression for --schedule cron (5-field UTC).")`
  - `@click.option("--checkpoint-file", default=None, help="Checkpoint file path. Defaults to autoagent.yaml loop.checkpoint_path.")`
  - `@click.option("--resume/--no-resume", default=True, show_default=True, help="Resume from checkpoint when available.")`
  - `@click.option("--full-auto", is_flag=True, default=False, help="Danger mode: auto-promote accepted configs and skip manual gates.")`
  - `@click.option("--db", default=DB_PATH, show_default=True, help="Conversation store DB.")`
  - `@click.option("--configs-dir", default=CONFIGS_DIR, show_default=True, help="Configs directory.")`
  - `@click.option("--memory-db", default=MEMORY_DB, show_default=True, help="Optimizer memory DB.")`

### `autoagent mcp-server`
- Purpose: Start MCP server for AI coding tool integration.
- Handler: `runner.py:3238` (`mcp_server_cmd`)
- Options:
  - `@click.option("--host", default="127.0.0.1", show_default=True, help="HTTP bind host when using --port.")`
  - `@click.option("--port", default=None, type=int, help="Start streamable HTTP mode on this port. Defaults to stdio mode.")`

## memory

### `autoagent memory add`
- Purpose: Add a note to a section of AUTOAGENT.md.
- Handler: `runner.py:2922` (`memory_add`)
- Arguments:
  - `@click.argument("note")`
- Options:
  - `@click.option("--section", required=True, type=click.Choice(["good", "bad", "preference", "constraint"]), help="Section to add the note to.")`

### `autoagent memory show`
- Purpose: Show AUTOAGENT.md contents.
- Handler: `runner.py:2901` (`memory_show`)

## core

### `autoagent optimize`
- Purpose: Run optimization cycles to improve agent config.
- Handler: `runner.py:1038` (`optimize`)
- Options:
  - `@click.option("--cycles", default=1, show_default=True, type=int, help="Number of optimization cycles.")`
  - `@click.option("--mode", default=None, type=click.Choice(["standard", "advanced", "research"]), help="Optimization mode (replaces --strategy).")`
  - `@click.option("--strategy", default=None, hidden=True, help="[DEPRECATED] Use --mode instead.")`
  - `@click.option("--db", default=DB_PATH, show_default=True, help="Conversation store DB.")`
  - `@click.option("--configs-dir", default=CONFIGS_DIR, show_default=True, help="Configs directory.")`
  - `@click.option("--memory-db", default=MEMORY_DB, show_default=True, help="Optimizer memory DB.")`
  - `@click.option("--full-auto", is_flag=True, default=False, help="Danger mode: auto-promote accepted configs without manual review.")`
  - `@click.option("--json", "json_output", "-j", is_flag=True, help="Output as JSON.")`

## outcomes

### `autoagent outcomes import`
- Purpose: Import business outcomes.
- Handler: `runner.py:5236` (`outcomes_import`)
- Options:
  - `@click.option("--source", type=click.Choice(["csv", "webhook"]), required=True)`
  - `@click.option("--file", "file_path", default=None, help="CSV file path")`

## core

### `autoagent pause`
- Purpose: Pause the optimization loop (human escape hatch).
- Handler: `runner.py:2163` (`pause_optimizer`)

### `autoagent pin`
- Purpose: Mark a config surface as immutable (e.g. prompts.root, safety_instructions).
- Handler: `runner.py:2223` (`pin_surface`)
- Arguments:
  - `@click.argument("surface", type=str)`

## pref

### `autoagent pref collect`
- Purpose: Add a preference pair.
- Handler: `runner.py:5522` (`pref_collect`)
- Options:
  - `@click.option("--input-text", required=True)`
  - `@click.option("--chosen", required=True)`
  - `@click.option("--rejected", required=True)`
  - `@click.option("--source", default="human_review")`

### `autoagent pref export`
- Purpose: Export preference pairs as DPO dataset.
- Handler: `runner.py:5535` (`pref_export`)
- Options:
  - `@click.option("--format", "fmt", type=click.Choice(["vertex", "openai", "generic"]), default="vertex")`

## core

### `autoagent quickstart`
- Purpose: Run the ENTIRE golden path: init → seed → eval → optimize → summary.
- Handler: `runner.py:3936` (`quickstart`)
- Options:
  - `@click.option("--agent-name", default="My Agent", show_default=True, help="Agent name for AUTOAGENT.md.")`
  - `@click.option("--verbose", is_flag=True, default=False, help="Show detailed output.")`
  - `@click.option("--dir", "target_dir", default=".", show_default=True, help="Directory to initialize in.")`
  - `@click.option("--open/--no-open", "auto_open", default=True, help="Auto-open web console after completion.")`

## registry

### `autoagent registry add`
- Purpose: Add a new item (or new version) to the registry.
- Handler: `runner.py:3303` (`registry_add`)
- Arguments:
  - `@click.argument("registry_type", type=click.Choice(REGISTRY_TYPES, case_sensitive=False))`
  - `@click.argument("name")`
- Options:
  - `@click.option("--file", "file_path", required=True, type=click.Path(exists=True), help="YAML/JSON file with item data.")`
  - `@click.option("--db", default=REGISTRY_DB, show_default=True)`

### `autoagent registry diff`
- Purpose: Diff two versions of a registry item.
- Handler: `runner.py:3336` (`registry_diff`)
- Arguments:
  - `@click.argument("registry_type", type=click.Choice(REGISTRY_TYPES, case_sensitive=False))`
  - `@click.argument("name")`
  - `@click.argument("v1", type=int)`
  - `@click.argument("v2", type=int)`
- Options:
  - `@click.option("--db", default=REGISTRY_DB, show_default=True)`

### `autoagent registry import`
- Purpose: Bulk-import registry items from a YAML/JSON file.
- Handler: `runner.py:3353` (`registry_import`)
- Arguments:
  - `@click.argument("path", type=click.Path(exists=True))`
- Options:
  - `@click.option("--db", default=REGISTRY_DB, show_default=True)`

### `autoagent registry list`
- Purpose: List registered items.
- Handler: `runner.py:3248` (`registry_list`)
- Options:
  - `@click.option("--type", "registry_type", default=None, type=click.Choice(REGISTRY_TYPES, case_sensitive=False), help="Filter by registry type.")`
  - `@click.option("--db", default=REGISTRY_DB, show_default=True)`

### `autoagent registry show`
- Purpose: Show details for a registry item.
- Handler: `runner.py:3278` (`registry_show`)
- Arguments:
  - `@click.argument("registry_type", type=click.Choice(REGISTRY_TYPES, case_sensitive=False))`
  - `@click.argument("name")`
- Options:
  - `@click.option("--version", "version", default=None, type=int, help="Specific version.")`
  - `@click.option("--db", default=REGISTRY_DB, show_default=True)`

## core

### `autoagent reject`
- Purpose: Reject a promoted experiment and rollback any active canary.
- Handler: `runner.py:2191` (`reject_experiment`)
- Arguments:
  - `@click.argument("experiment_id", type=str)`
- Options:
  - `@click.option("--configs-dir", default=CONFIGS_DIR, show_default=True, help="Configs directory.")`
  - `@click.option("--db", default=DB_PATH, show_default=True, help="Conversation store DB.")`

## release

### `autoagent release create`
- Purpose: Create a new release object from an experiment.
- Handler: `runner.py:5265` (`release_create`)
- Options:
  - `@click.option("--experiment-id", required=True, help="Experiment ID to create release from")`

### `autoagent release list`
- Purpose: List release objects.
- Handler: `runner.py:5258` (`release_list`)

## core

### `autoagent replay`
- Purpose: Show optimization history like git log --oneline.
- Handler: `runner.py:4771` (`replay`)
- Options:
  - `@click.option("--limit", default=20, show_default=True, type=int, help="Number of entries to show.")`
  - `@click.option("--memory-db", default=MEMORY_DB, show_default=True, help="Optimizer memory DB.")`
  - `@click.option("--json", "json_output", "-j", is_flag=True, help="Output as JSON.")`

### `autoagent resume`
- Purpose: Resume the optimization loop after a pause.
- Handler: `runner.py:2176` (`resume_optimizer`)

## review

### `autoagent review apply`
- Purpose: Apply (accept) a change card.
- Handler: `runner.py:2599` (`review_apply`)
- Arguments:
  - `@click.argument("card_id")`

### `autoagent review export`
- Purpose: Export a change card as markdown.
- Handler: `runner.py:2648` (`review_export`)
- Arguments:
  - `@click.argument("card_id")`

### `autoagent review list`
- Purpose: List pending change cards.
- Handler: `runner.py:2555` (`review_list`)
- Options:
  - `@click.option("--limit", default=20, show_default=True, type=int, help="Number of cards to show.")`

### `autoagent review reject`
- Purpose: Reject a change card with an optional reason.
- Handler: `runner.py:2623` (`review_reject`)
- Arguments:
  - `@click.argument("card_id")`
- Options:
  - `@click.option("--reason", default="", help="Reason for rejection.")`

### `autoagent review show`
- Purpose: Show a specific change card with full terminal rendering.
- Handler: `runner.py:2581` (`review_show`)
- Arguments:
  - `@click.argument("card_id")`

## reward

### `autoagent reward create`
- Purpose: Create a new reward definition.
- Handler: `runner.py:5306` (`reward_create`)
- Arguments:
  - `@click.argument("name")`
- Options:
  - `@click.option("--kind", type=click.Choice(["verifiable", "preference", "business_outcome", "constitutional"]), default="verifiable")`
  - `@click.option("--scope", type=click.Choice(["runtime", "buildtime", "multi_agent"]), default="runtime")`
  - `@click.option("--source", type=click.Choice(["deterministic_checker", "environment_checker", "human_label", "llm_judge", "ai_preference"]), default="deterministic_checker")`
  - `@click.option("--hard-gate", is_flag=True, help="Mark as hard gate (pass/fail, not optimizable)")`
  - `@click.option("--weight", type=float, default=1.0)`
  - `@click.option("--description", type=str, default="")`

### `autoagent reward list`
- Purpose: List all reward definitions.
- Handler: `runner.py:5323` (`reward_list`)
- Options:
  - `@click.option("--kind", type=str, default=None, help="Filter by kind")`

### `autoagent reward test`
- Purpose: Test a reward definition.
- Handler: `runner.py:5341` (`reward_test`)
- Arguments:
  - `@click.argument("name")`
- Options:
  - `@click.option("--trace", "trace_id", type=str, default=None, help="Trace ID to test against")`

## rl

### `autoagent rl canary`
- Purpose: Start canary evaluation for a policy.
- Handler: `runner.py:5494` (`rl_canary`)
- Arguments:
  - `@click.argument("policy_id")`

### `autoagent rl dataset`
- Purpose: Build a training dataset from episodes.
- Handler: `runner.py:5473` (`rl_dataset`)
- Options:
  - `@click.option("--mode", type=click.Choice(["verifiable", "preference", "episode", "audit"]), default="verifiable")`
  - `@click.option("--limit", type=int, default=1000)`

### `autoagent rl eval`
- Purpose: Evaluate a policy artifact offline.
- Handler: `runner.py:5416` (`rl_eval`)
- Arguments:
  - `@click.argument("policy_id")`

### `autoagent rl jobs`
- Purpose: List training jobs.
- Handler: `runner.py:5398` (`rl_jobs`)
- Options:
  - `@click.option("--status", type=str, default=None)`

### `autoagent rl promote`
- Purpose: Promote a policy to active status.
- Handler: `runner.py:5434` (`rl_promote`)
- Arguments:
  - `@click.argument("policy_id")`

### `autoagent rl rollback`
- Purpose: Rollback a promoted policy.
- Handler: `runner.py:5452` (`rl_rollback`)
- Arguments:
  - `@click.argument("policy_id")`

### `autoagent rl train`
- Purpose: Start a policy training job.
- Handler: `runner.py:5374` (`rl_train`)
- Options:
  - `@click.option("--mode", type=click.Choice(["control", "verifier", "preference"]), required=True)`
  - `@click.option("--backend", type=click.Choice(["openai_rft", "openai_dpo", "vertex_sft", "vertex_preference", "vertex_continuous"]), required=True)`
  - `@click.option("--dataset", type=str, required=True, help="Path to training dataset")`
  - `@click.option("--config", type=str, default=None, help="JSON config string")`

## run

### `autoagent run agent`
- Purpose: Start the ADK agent API server (legacy).
- Handler: `runner.py:3026` (`run_agent`)
- Options:
  - `@click.option("--host", default="0.0.0.0", show_default=True, help="Host to bind to.")`
  - `@click.option("--port", default=8000, show_default=True, type=int, help="Port to bind to.")`

### `autoagent run eval`
- Purpose: Run eval suite (legacy). Use: autoagent eval run
- Handler: `runner.py:3039` (`run_eval`)
- Options:
  - `@click.option("--config-path", default=None, help="Path to config YAML.")`
  - `@click.option("--category", default=None, help="Run only a specific category.")`

### `autoagent run loop`
- Purpose: Run loop (legacy). Use: autoagent loop
- Handler: `runner.py:3125` (`run_loop`)
- Options:
  - `@click.option("--cycles", default=5, show_default=True, type=int)`
  - `@click.option("--db", default=DB_PATH, show_default=True)`
  - `@click.option("--configs-dir", default=CONFIGS_DIR, show_default=True)`
  - `@click.option("--memory-db", default=MEMORY_DB, show_default=True)`
  - `@click.option("--delay", default=1.0, show_default=True, type=float)`

### `autoagent run observe`
- Purpose: Run observer (legacy). Use: autoagent status
- Handler: `runner.py:3057` (`run_observe`)
- Options:
  - `@click.option("--db", default=DB_PATH, show_default=True)`
  - `@click.option("--window", default=100, show_default=True, type=int)`

### `autoagent run optimize`
- Purpose: Run optimize (legacy). Use: autoagent optimize
- Handler: `runner.py:3075` (`run_optimize`)
- Options:
  - `@click.option("--db", default=DB_PATH, show_default=True)`
  - `@click.option("--configs-dir", default=CONFIGS_DIR, show_default=True)`
  - `@click.option("--memory-db", default=MEMORY_DB, show_default=True)`

### `autoagent run status`
- Purpose: Show status (legacy). Use: autoagent status
- Handler: `runner.py:3181` (`run_status`)
- Options:
  - `@click.option("--db", default=DB_PATH, show_default=True)`
  - `@click.option("--configs-dir", default=CONFIGS_DIR, show_default=True)`
  - `@click.option("--memory-db", default=MEMORY_DB, show_default=True)`

## runbook

### `autoagent runbook apply`
- Purpose: Apply a runbook — registers its skills, policies, and tool contracts.
- Handler: `runner.py:2841` (`runbook_apply`)
- Arguments:
  - `@click.argument("name")`
- Options:
  - `@click.option("--db", default=REGISTRY_DB, show_default=True)`

### `autoagent runbook create`
- Purpose: Create a runbook from a YAML file.
- Handler: `runner.py:2870` (`runbook_create`)
- Options:
  - `@click.option("--name", required=True, help="Runbook name.")`
  - `@click.option("--file", "file_path", required=True, type=click.Path(exists=True), help="YAML file with runbook definition.")`
  - `@click.option("--db", default=REGISTRY_DB, show_default=True)`

### `autoagent runbook list`
- Purpose: List all runbooks.
- Handler: `runner.py:2780` (`runbook_list`)
- Options:
  - `@click.option("--db", default=REGISTRY_DB, show_default=True)`

### `autoagent runbook show`
- Purpose: Show runbook details.
- Handler: `runner.py:2807` (`runbook_show`)
- Arguments:
  - `@click.argument("name")`
- Options:
  - `@click.option("--db", default=REGISTRY_DB, show_default=True)`

## scorer

### `autoagent scorer create`
- Purpose: Create a scorer from a natural language description.
- Handler: `runner.py:3725` (`scorer_create`)
- Arguments:
  - `@click.argument("description", required=False, default=None)`
- Options:
  - `@click.option("--from-file", "from_file", type=click.Path(exists=True), help="Read NL description from a file.")`
  - `@click.option("--name", default=None, help="Name for the scorer (auto-generated if omitted).")`

### `autoagent scorer list`
- Purpose: List all scorer specs in memory.
- Handler: `runner.py:3753` (`scorer_list`)

### `autoagent scorer refine`
- Purpose: Refine an existing scorer with additional criteria.
- Handler: `runner.py:3794` (`scorer_refine`)
- Arguments:
  - `@click.argument("name")`
  - `@click.argument("additional_nl")`

### `autoagent scorer show`
- Purpose: Show a scorer spec in detail.
- Handler: `runner.py:3774` (`scorer_show`)
- Arguments:
  - `@click.argument("name")`

### `autoagent scorer test`
- Purpose: Test a scorer against a trace.
- Handler: `runner.py:3819` (`scorer_test`)
- Arguments:
  - `@click.argument("name")`
- Options:
  - `@click.option("--trace", "trace_id", required=True, help="Trace ID to test against.")`
  - `@click.option("--db", default=TRACE_DB, show_default=True)`

## core

### `autoagent server`
- Purpose: Start the API server + web console.
- Handler: `runner.py:2954` (`server`)
- Options:
  - `@click.option("--host", default="0.0.0.0", show_default=True, help="Host to bind to.")`
  - `@click.option("--port", default=8000, show_default=True, type=int, help="Port to bind to.")`
  - `@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload for development.")`

## skill

### `autoagent skill export-md`
- Purpose: Export a skill as SKILL.md.
- Handler: `runner.py:3388` (`skill_export_md`)
- Arguments:
  - `@click.argument("skill_name")`
- Options:
  - `@click.option("--output", default=None)`

### `autoagent skill import-md`
- Purpose: Import a skill from SKILL.md file.
- Handler: `runner.py:3395` (`skill_import_md`)
- Arguments:
  - `@click.argument("path")`

## core

### `autoagent status`
- Purpose: Show system health, config versions, and recent activity.
- Handler: `runner.py:1804` (`status`)
- Options:
  - `@click.option("--db", default=DB_PATH, show_default=True, help="Conversation store DB.")`
  - `@click.option("--configs-dir", default=CONFIGS_DIR, show_default=True, help="Configs directory.")`
  - `@click.option("--memory-db", default=MEMORY_DB, show_default=True, help="Optimizer memory DB.")`
  - `@click.option("--json", "json_output", "-j", is_flag=True, help="Output as JSON.")`

## trace

### `autoagent trace blame`
- Purpose: Build a blame map of failure clusters.
- Handler: `runner.py:3631` (`trace_blame`)
- Options:
  - `@click.option("--window", default="24h", show_default=True, help="Time window (e.g. 24h, 7d, 30m).")`
  - `@click.option("--top", "top_n", default=10, show_default=True, help="Number of clusters to show.")`
  - `@click.option("--db", default=TRACE_DB, show_default=True)`

### `autoagent trace grade`
- Purpose: Grade all spans in a trace.
- Handler: `runner.py:3600` (`trace_grade`)
- Arguments:
  - `@click.argument("trace_id")`
- Options:
  - `@click.option("--db", default=TRACE_DB, show_default=True)`

### `autoagent trace graph`
- Purpose: Render a trace as a dependency graph with critical-path analysis.
- Handler: `runner.py:3665` (`trace_graph`)
- Arguments:
  - `@click.argument("trace_id")`
- Options:
  - `@click.option("--db", default=TRACE_DB, show_default=True)`

### `autoagent trace promote`
- Purpose: Promote a trace to an eval case.
- Handler: `runner.py:3704` (`trace_promote`)
- Arguments:
  - `@click.argument("trace_id")`

## core

### `autoagent unpin`
- Purpose: Remove immutable marking from a config surface.
- Handler: `runner.py:2237` (`unpin_surface`)
- Arguments:
  - `@click.argument("surface", type=str)`


---

## 9. Troubleshooting & FAQ

This chapter gives practical answers for the most common setup and operational issues.

### 9.1 Setup and environment

#### Q: `./setup.sh` says permission denied.

```bash
chmod +x setup.sh start.sh stop.sh
./setup.sh
```

#### Q: Python version check fails.

Install Python 3.11+ and rerun setup.

#### Q: Node.js version check fails.

Install Node 18+ and rerun setup.

#### Q: Frontend fails to install.

```bash
cd web
npm install
cd ..
```

### 9.2 Runtime and ports

#### Q: Start script says ports are already in use.

```bash
./stop.sh
./start.sh
```

#### Q: Backend starts but UI does not load.

```bash
cat .autoagent/frontend.log
```

#### Q: UI loads but data looks stale.

- Confirm backend health endpoint returns data.
- Confirm websocket/SSE stream connectivity.
- Refresh route-level queries or relaunch services.

### 9.3 CLI behavior

#### Q: `eval list` says no local eval result files.

Run an eval first and specify output file:

```bash
python3 runner.py eval run --output results.json
```

#### Q: `status` shows poor safety but high overall score mood.

Treat safety gate as primary. Improve safety first, then optimize for secondary outcomes.

#### Q: Review queue is growing.

- Increase proposal quality threshold.
- Reduce optimization burst size.
- Assign routine runbook-based triage.

### 9.4 Builder-specific

#### Q: Tasks exist but no visible progress updates.

- Verify active session selection in left rail.
- Verify task drawer open state.
- Confirm event stream from `/api/builder/events/stream`.

#### Q: Why am I seeing many approval prompts?

Likely many actions require privileged scopes (`source_write`, `deployment`, etc.). This is expected in secure default posture.

#### Q: When should I grant project-wide permission?

Only after:

- Stable low-risk workflow pattern.
- Clear rollback strategy.
- Team agreement on blast radius.

### 9.5 Deployment and integration

#### Q: CX deploy requires extra fields.

For `cx-studio` target, ensure project/location/agent-id/credentials are explicitly set.

#### Q: ADK export diff is empty.

Verify snapshot path and imported source alignment. Run `adk status` and `adk diff` before export.

### 9.6 Safety and governance

#### Q: Can I run full-auto in production?

You can technically, but only with mature safeguards, strict budgets, immutable surfaces, and high-confidence eval + judge calibration.

> ⚠️ Warning: Full-auto without mature governance can produce fast regressions at scale.

### 9.7 FAQ quick answers

- Is mock mode useful? Yes, for onboarding and pipeline validation.
- Do I need the web UI? No, CLI can run full workflows.
- Can I use API only? Yes, FastAPI routes cover all major domains.
- Are changes auditable? Yes, via cards/events/history stores and route-level records.
- Can I keep humans in the loop? Yes, pause/pin/reject/approval are first-class.

---

## 10. Glossary & Appendix

### 10.1 Glossary

- Agent: The runtime system being evaluated and improved.
- Optimization Cycle: One pass through trace/diagnose/search/eval/gate/deploy/learn.
- Experiment Card: Structured artifact describing a candidate change and outcomes.
- Hard Gate: Non-negotiable constraint that must pass.
- North-star Metric: Primary quality objective.
- SLO: Operational target boundary (latency/cost/etc.).
- Mutation: Typed, scoped change candidate.
- Runbook: Curated set of improvement actions.
- Blame Map: Failure clustering and attribution surface.
- Drift: Deviation in judge or metric behavior over time.
- Approval Scope: Permission granularity (`once`, `task`, `project`).

### 10.2 Appendix A — API endpoint inventory

# API Endpoint Inventory (Generated from api/routes/*.py)

Total route modules: **48**
Total endpoints discovered: **267**

## Endpoint Matrix

| Module | Prefix | Method | Route | Full Path |
|---|---|---|---|---|
| `api/routes/__init__.py` | `/` | - | - | - |
| `api/routes/a2a.py` | `/` | `GET` | `/.well-known/agent-card.json` | `/.well-known/agent-card.json` |
| `api/routes/a2a.py` | `/` | `POST` | `/api/a2a/tasks/send` | `/api/a2a/tasks/send` |
| `api/routes/a2a.py` | `/` | `GET` | `/api/a2a/tasks/{task_id}` | `/api/a2a/tasks/{task_id}` |
| `api/routes/a2a.py` | `/` | `POST` | `/api/a2a/tasks/{task_id}/cancel` | `/api/a2a/tasks/{task_id}/cancel` |
| `api/routes/a2a.py` | `/` | `GET` | `/api/a2a/agents` | `/api/a2a/agents` |
| `api/routes/a2a.py` | `/` | `POST` | `/api/a2a/discover` | `/api/a2a/discover` |
| `api/routes/adk.py` | `/api/adk` | `POST` | `/import` | `/api/adk/import` |
| `api/routes/adk.py` | `/api/adk` | `POST` | `/export` | `/api/adk/export` |
| `api/routes/adk.py` | `/api/adk` | `POST` | `/deploy` | `/api/adk/deploy` |
| `api/routes/adk.py` | `/api/adk` | `GET` | `/status` | `/api/adk/status` |
| `api/routes/adk.py` | `/api/adk` | `GET` | `/diff` | `/api/adk/diff` |
| `api/routes/agent_skills.py` | `/api/agent-skills` | `GET` | `/gaps` | `/api/agent-skills/gaps` |
| `api/routes/agent_skills.py` | `/api/agent-skills` | `POST` | `/analyze` | `/api/agent-skills/analyze` |
| `api/routes/agent_skills.py` | `/api/agent-skills` | `POST` | `/generate` | `/api/agent-skills/generate` |
| `api/routes/agent_skills.py` | `/api/agent-skills` | `GET` | `/` | `/api/agent-skills/` |
| `api/routes/agent_skills.py` | `/api/agent-skills` | `GET` | `/{skill_id}` | `/api/agent-skills/{skill_id}` |
| `api/routes/agent_skills.py` | `/api/agent-skills` | `POST` | `/{skill_id}/approve` | `/api/agent-skills/{skill_id}/approve` |
| `api/routes/agent_skills.py` | `/api/agent-skills` | `POST` | `/{skill_id}/reject` | `/api/agent-skills/{skill_id}/reject` |
| `api/routes/agent_skills.py` | `/api/agent-skills` | `POST` | `/{skill_id}/apply` | `/api/agent-skills/{skill_id}/apply` |
| `api/routes/assistant.py` | `/api/assistant` | `POST` | `/message` | `/api/assistant/message` |
| `api/routes/assistant.py` | `/api/assistant` | `GET` | `/message` | `/api/assistant/message` |
| `api/routes/assistant.py` | `/api/assistant` | `POST` | `/upload` | `/api/assistant/upload` |
| `api/routes/assistant.py` | `/api/assistant` | `GET` | `/history` | `/api/assistant/history` |
| `api/routes/assistant.py` | `/api/assistant` | `DELETE` | `/history` | `/api/assistant/history` |
| `api/routes/assistant.py` | `/api/assistant` | `GET` | `/suggestions` | `/api/assistant/suggestions` |
| `api/routes/assistant.py` | `/api/assistant` | `POST` | `/action/{action_id}` | `/api/assistant/action/{action_id}` |
| `api/routes/autofix.py` | `/api/autofix` | `POST` | `/suggest` | `/api/autofix/suggest` |
| `api/routes/autofix.py` | `/api/autofix` | `GET` | `/proposals` | `/api/autofix/proposals` |
| `api/routes/autofix.py` | `/api/autofix` | `POST` | `/apply/{proposal_id}` | `/api/autofix/apply/{proposal_id}` |
| `api/routes/autofix.py` | `/api/autofix` | `GET` | `/history` | `/api/autofix/history` |
| `api/routes/builder.py` | `/api/builder` | `GET` | `/projects` | `/api/builder/projects` |
| `api/routes/builder.py` | `/api/builder` | `POST` | `/projects` | `/api/builder/projects` |
| `api/routes/builder.py` | `/api/builder` | `GET` | `/projects/{project_id}` | `/api/builder/projects/{project_id}` |
| `api/routes/builder.py` | `/api/builder` | `PATCH` | `/projects/{project_id}` | `/api/builder/projects/{project_id}` |
| `api/routes/builder.py` | `/api/builder` | `DELETE` | `/projects/{project_id}` | `/api/builder/projects/{project_id}` |
| `api/routes/builder.py` | `/api/builder` | `GET` | `/sessions` | `/api/builder/sessions` |
| `api/routes/builder.py` | `/api/builder` | `POST` | `/sessions` | `/api/builder/sessions` |
| `api/routes/builder.py` | `/api/builder` | `GET` | `/sessions/{session_id}` | `/api/builder/sessions/{session_id}` |
| `api/routes/builder.py` | `/api/builder` | `POST` | `/sessions/{session_id}/close` | `/api/builder/sessions/{session_id}/close` |
| `api/routes/builder.py` | `/api/builder` | `GET` | `/tasks` | `/api/builder/tasks` |
| `api/routes/builder.py` | `/api/builder` | `POST` | `/tasks` | `/api/builder/tasks` |
| `api/routes/builder.py` | `/api/builder` | `GET` | `/tasks/{task_id}` | `/api/builder/tasks/{task_id}` |
| `api/routes/builder.py` | `/api/builder` | `POST` | `/tasks/{task_id}/pause` | `/api/builder/tasks/{task_id}/pause` |
| `api/routes/builder.py` | `/api/builder` | `POST` | `/tasks/{task_id}/resume` | `/api/builder/tasks/{task_id}/resume` |
| `api/routes/builder.py` | `/api/builder` | `POST` | `/tasks/{task_id}/cancel` | `/api/builder/tasks/{task_id}/cancel` |
| `api/routes/builder.py` | `/api/builder` | `POST` | `/tasks/{task_id}/duplicate` | `/api/builder/tasks/{task_id}/duplicate` |
| `api/routes/builder.py` | `/api/builder` | `POST` | `/tasks/{task_id}/fork` | `/api/builder/tasks/{task_id}/fork` |
| `api/routes/builder.py` | `/api/builder` | `POST` | `/tasks/{task_id}/progress` | `/api/builder/tasks/{task_id}/progress` |
| `api/routes/builder.py` | `/api/builder` | `GET` | `/proposals` | `/api/builder/proposals` |
| `api/routes/builder.py` | `/api/builder` | `GET` | `/proposals/{proposal_id}` | `/api/builder/proposals/{proposal_id}` |
| `api/routes/builder.py` | `/api/builder` | `POST` | `/proposals/{proposal_id}/approve` | `/api/builder/proposals/{proposal_id}/approve` |
| `api/routes/builder.py` | `/api/builder` | `POST` | `/proposals/{proposal_id}/reject` | `/api/builder/proposals/{proposal_id}/reject` |
| `api/routes/builder.py` | `/api/builder` | `POST` | `/proposals/{proposal_id}/revise` | `/api/builder/proposals/{proposal_id}/revise` |
| `api/routes/builder.py` | `/api/builder` | `GET` | `/artifacts` | `/api/builder/artifacts` |
| `api/routes/builder.py` | `/api/builder` | `GET` | `/artifacts/{artifact_id}` | `/api/builder/artifacts/{artifact_id}` |
| `api/routes/builder.py` | `/api/builder` | `POST` | `/artifacts/{artifact_id}/comment` | `/api/builder/artifacts/{artifact_id}/comment` |
| `api/routes/builder.py` | `/api/builder` | `GET` | `/approvals` | `/api/builder/approvals` |
| `api/routes/builder.py` | `/api/builder` | `POST` | `/approvals/{approval_id}/respond` | `/api/builder/approvals/{approval_id}/respond` |
| `api/routes/builder.py` | `/api/builder` | `GET` | `/permissions/grants` | `/api/builder/permissions/grants` |
| `api/routes/builder.py` | `/api/builder` | `POST` | `/permissions/grants` | `/api/builder/permissions/grants` |
| `api/routes/builder.py` | `/api/builder` | `DELETE` | `/permissions/grants/{grant_id}` | `/api/builder/permissions/grants/{grant_id}` |
| `api/routes/builder.py` | `/api/builder` | `GET` | `/events` | `/api/builder/events` |
| `api/routes/builder.py` | `/api/builder` | `GET` | `/events/stream` | `/api/builder/events/stream` |
| `api/routes/builder.py` | `/api/builder` | `GET` | `/metrics` | `/api/builder/metrics` |
| `api/routes/builder.py` | `/api/builder` | `GET` | `/specialists` | `/api/builder/specialists` |
| `api/routes/builder.py` | `/api/builder` | `POST` | `/specialists/{role}/invoke` | `/api/builder/specialists/{role}/invoke` |
| `api/routes/builder_demo.py` | `/api/builder/demo` | `POST` | `/seed` | `/api/builder/demo/seed` |
| `api/routes/builder_demo.py` | `/api/builder/demo` | `POST` | `/reset` | `/api/builder/demo/reset` |
| `api/routes/builder_demo.py` | `/api/builder/demo` | `GET` | `/acts` | `/api/builder/demo/acts` |
| `api/routes/builder_demo.py` | `/api/builder/demo` | `POST` | `/acts/{act_id}/play` | `/api/builder/demo/acts/{act_id}/play` |
| `api/routes/builder_demo.py` | `/api/builder/demo` | `GET` | `/status` | `/api/builder/demo/status` |
| `api/routes/changes.py` | `/api/changes` | `GET` | `/` | `/api/changes/` |
| `api/routes/changes.py` | `/api/changes` | `GET` | `/{card_id}` | `/api/changes/{card_id}` |
| `api/routes/changes.py` | `/api/changes` | `POST` | `/{card_id}/apply` | `/api/changes/{card_id}/apply` |
| `api/routes/changes.py` | `/api/changes` | `POST` | `/{card_id}/reject` | `/api/changes/{card_id}/reject` |
| `api/routes/changes.py` | `/api/changes` | `PATCH` | `/{card_id}/hunks` | `/api/changes/{card_id}/hunks` |
| `api/routes/changes.py` | `/api/changes` | `GET` | `/{card_id}/export` | `/api/changes/{card_id}/export` |
| `api/routes/changes.py` | `/api/changes` | `GET` | `/{card_id}/audit` | `/api/changes/{card_id}/audit` |
| `api/routes/changes.py` | `/api/changes` | `GET` | `/audit-summary` | `/api/changes/audit-summary` |
| `api/routes/cicd.py` | `/api/cicd` | `POST` | `/webhook` | `/api/cicd/webhook` |
| `api/routes/cicd.py` | `/api/cicd` | `GET` | `/status/{repository}/{branch}` | `/api/cicd/status/{repository}/{branch}` |
| `api/routes/cicd.py` | `/api/cicd` | `GET` | `/history/{repository}` | `/api/cicd/history/{repository}` |
| `api/routes/collaboration.py` | `/api/reviews` | `POST` | `/request` | `/api/reviews/request` |
| `api/routes/collaboration.py` | `/api/reviews` | `POST` | `/{request_id}/submit` | `/api/reviews/{request_id}/submit` |
| `api/routes/collaboration.py` | `/api/reviews` | `GET` | `/pending` | `/api/reviews/pending` |
| `api/routes/collaboration.py` | `/api/reviews` | `GET` | `/{request_id}` | `/api/reviews/{request_id}` |
| `api/routes/config.py` | `/api/config` | `GET` | `/list` | `/api/config/list` |
| `api/routes/config.py` | `/api/config` | `GET` | `/show/{version}` | `/api/config/show/{version}` |
| `api/routes/config.py` | `/api/config` | `GET` | `/diff` | `/api/config/diff` |
| `api/routes/config.py` | `/api/config` | `GET` | `/active` | `/api/config/active` |
| `api/routes/context.py` | `/api/context` | `GET` | `/analysis/{trace_id}` | `/api/context/analysis/{trace_id}` |
| `api/routes/context.py` | `/api/context` | `POST` | `/simulate` | `/api/context/simulate` |
| `api/routes/context.py` | `/api/context` | `GET` | `/report` | `/api/context/report` |
| `api/routes/control.py` | `/api/control` | `GET` | `/state` | `/api/control/state` |
| `api/routes/control.py` | `/api/control` | `POST` | `/pause` | `/api/control/pause` |
| `api/routes/control.py` | `/api/control` | `POST` | `/resume` | `/api/control/resume` |
| `api/routes/control.py` | `/api/control` | `POST` | `/pin/{surface}` | `/api/control/pin/{surface}` |
| `api/routes/control.py` | `/api/control` | `POST` | `/unpin/{surface}` | `/api/control/unpin/{surface}` |
| `api/routes/control.py` | `/api/control` | `POST` | `/reject/{experiment_id}` | `/api/control/reject/{experiment_id}` |
| `api/routes/control.py` | `/api/control` | `POST` | `/inject` | `/api/control/inject` |
| `api/routes/conversations.py` | `/api/conversations` | `GET` | `/stats` | `/api/conversations/stats` |
| `api/routes/conversations.py` | `/api/conversations` | `GET` | `/{conversation_id}` | `/api/conversations/{conversation_id}` |
| `api/routes/curriculum.py` | `/api/curriculum` | `POST` | `/generate` | `/api/curriculum/generate` |
| `api/routes/curriculum.py` | `/api/curriculum` | `GET` | `/batches` | `/api/curriculum/batches` |
| `api/routes/curriculum.py` | `/api/curriculum` | `GET` | `/batches/{batch_id}` | `/api/curriculum/batches/{batch_id}` |
| `api/routes/curriculum.py` | `/api/curriculum` | `POST` | `/apply` | `/api/curriculum/apply` |
| `api/routes/cx_studio.py` | `/api/cx` | `GET` | `/agents` | `/api/cx/agents` |
| `api/routes/cx_studio.py` | `/api/cx` | `POST` | `/import` | `/api/cx/import` |
| `api/routes/cx_studio.py` | `/api/cx` | `POST` | `/export` | `/api/cx/export` |
| `api/routes/cx_studio.py` | `/api/cx` | `POST` | `/deploy` | `/api/cx/deploy` |
| `api/routes/cx_studio.py` | `/api/cx` | `POST` | `/widget` | `/api/cx/widget` |
| `api/routes/cx_studio.py` | `/api/cx` | `GET` | `/status` | `/api/cx/status` |
| `api/routes/cx_studio.py` | `/api/cx` | `GET` | `/preview` | `/api/cx/preview` |
| `api/routes/datasets.py` | `/api/datasets` | `GET` | `/{dataset_id}` | `/api/datasets/{dataset_id}` |
| `api/routes/datasets.py` | `/api/datasets` | `POST` | `/{dataset_id}/rows` | `/api/datasets/{dataset_id}/rows` |
| `api/routes/datasets.py` | `/api/datasets` | `POST` | `/{dataset_id}/versions` | `/api/datasets/{dataset_id}/versions` |
| `api/routes/datasets.py` | `/api/datasets` | `GET` | `/{dataset_id}/versions` | `/api/datasets/{dataset_id}/versions` |
| `api/routes/datasets.py` | `/api/datasets` | `GET` | `/{dataset_id}/rows` | `/api/datasets/{dataset_id}/rows` |
| `api/routes/datasets.py` | `/api/datasets` | `GET` | `/{dataset_id}/stats` | `/api/datasets/{dataset_id}/stats` |
| `api/routes/datasets.py` | `/api/datasets` | `POST` | `/{dataset_id}/import/traces` | `/api/datasets/{dataset_id}/import/traces` |
| `api/routes/datasets.py` | `/api/datasets` | `POST` | `/{dataset_id}/import/eval-cases` | `/api/datasets/{dataset_id}/import/eval-cases` |
| `api/routes/datasets.py` | `/api/datasets` | `POST` | `/{dataset_id}/splits` | `/api/datasets/{dataset_id}/splits` |
| `api/routes/datasets.py` | `/api/datasets` | `POST` | `/{dataset_id}/export` | `/api/datasets/{dataset_id}/export` |
| `api/routes/datasets.py` | `/api/datasets` | `POST` | `/{dataset_id}/pins` | `/api/datasets/{dataset_id}/pins` |
| `api/routes/datasets.py` | `/api/datasets` | `GET` | `/{dataset_id}/pins` | `/api/datasets/{dataset_id}/pins` |
| `api/routes/datasets.py` | `/api/datasets` | `GET` | `/{dataset_id}/pins/{pin_id}` | `/api/datasets/{dataset_id}/pins/{pin_id}` |
| `api/routes/demo.py` | `/api/demo` | `GET` | `/status` | `/api/demo/status` |
| `api/routes/demo.py` | `/api/demo` | `GET` | `/scenario` | `/api/demo/scenario` |
| `api/routes/demo.py` | `/api/demo` | `GET` | `/stream` | `/api/demo/stream` |
| `api/routes/deploy.py` | `/api/deploy` | `GET` | `/status` | `/api/deploy/status` |
| `api/routes/deploy.py` | `/api/deploy` | `POST` | `/rollback` | `/api/deploy/rollback` |
| `api/routes/diagnose.py` | `/api/diagnose` | `POST` | `/chat` | `/api/diagnose/chat` |
| `api/routes/edit.py` | `/api/edit` | - | - | - |
| `api/routes/eval.py` | `/api/eval` | `POST` | `/run` | `/api/eval/run` |
| `api/routes/eval.py` | `/api/eval` | `GET` | `/runs` | `/api/eval/runs` |
| `api/routes/eval.py` | `/api/eval` | `GET` | `/runs/{run_id}` | `/api/eval/runs/{run_id}` |
| `api/routes/eval.py` | `/api/eval` | `GET` | `/runs/{run_id}/cases` | `/api/eval/runs/{run_id}/cases` |
| `api/routes/eval.py` | `/api/eval` | `GET` | `/history` | `/api/eval/history` |
| `api/routes/eval.py` | `/api/eval` | `GET` | `/history/{run_id}` | `/api/eval/history/{run_id}` |
| `api/routes/events.py` | `/api/events` | - | - | - |
| `api/routes/experiments.py` | `/api/experiments` | `GET` | `/stats` | `/api/experiments/stats` |
| `api/routes/experiments.py` | `/api/experiments` | `GET` | `/archive` | `/api/experiments/archive` |
| `api/routes/experiments.py` | `/api/experiments` | `GET` | `/pareto` | `/api/experiments/pareto` |
| `api/routes/experiments.py` | `/api/experiments` | `GET` | `/judge-calibration` | `/api/experiments/judge-calibration` |
| `api/routes/experiments.py` | `/api/experiments` | `GET` | `/{experiment_id}` | `/api/experiments/{experiment_id}` |
| `api/routes/health.py` | `/api/health` | `GET` | `/ready` | `/api/health/ready` |
| `api/routes/health.py` | `/api/health` | `GET` | `/system` | `/api/health/system` |
| `api/routes/health.py` | `/api/health` | `GET` | `/cost` | `/api/health/cost` |
| `api/routes/health.py` | `/api/health` | `GET` | `/eval-set` | `/api/health/eval-set` |
| `api/routes/health.py` | `/api/health` | `GET` | `/scorecard` | `/api/health/scorecard` |
| `api/routes/impact.py` | `/api/impact` | `POST` | `/analyze` | `/api/impact/analyze` |
| `api/routes/impact.py` | `/api/impact` | `GET` | `/dependencies` | `/api/impact/dependencies` |
| `api/routes/impact.py` | `/api/impact` | `GET` | `/report/{analysis_id}` | `/api/impact/report/{analysis_id}` |
| `api/routes/intelligence.py` | `/api/intelligence` | `POST` | `/archive` | `/api/intelligence/archive` |
| `api/routes/intelligence.py` | `/api/intelligence` | `GET` | `/reports` | `/api/intelligence/reports` |
| `api/routes/intelligence.py` | `/api/intelligence` | `GET` | `/reports/{report_id}` | `/api/intelligence/reports/{report_id}` |
| `api/routes/intelligence.py` | `/api/intelligence` | `POST` | `/reports/{report_id}/ask` | `/api/intelligence/reports/{report_id}/ask` |
| `api/routes/intelligence.py` | `/api/intelligence` | `POST` | `/reports/{report_id}/apply` | `/api/intelligence/reports/{report_id}/apply` |
| `api/routes/intelligence.py` | `/api/intelligence` | `POST` | `/build` | `/api/intelligence/build` |
| `api/routes/intelligence.py` | `/api/intelligence` | `GET` | `/knowledge/{asset_id}` | `/api/intelligence/knowledge/{asset_id}` |
| `api/routes/intelligence.py` | `/api/intelligence` | `POST` | `/reports/{report_id}/deep-research` | `/api/intelligence/reports/{report_id}/deep-research` |
| `api/routes/intelligence.py` | `/api/intelligence` | `POST` | `/reports/{report_id}/autonomous-loop` | `/api/intelligence/reports/{report_id}/autonomous-loop` |
| `api/routes/judges.py` | `/api/judges` | `POST` | `/feedback` | `/api/judges/feedback` |
| `api/routes/judges.py` | `/api/judges` | `GET` | `/calibration` | `/api/judges/calibration` |
| `api/routes/judges.py` | `/api/judges` | `GET` | `/drift` | `/api/judges/drift` |
| `api/routes/knowledge.py` | `/api/knowledge` | `POST` | `/mine` | `/api/knowledge/mine` |
| `api/routes/knowledge.py` | `/api/knowledge` | `GET` | `/entries` | `/api/knowledge/entries` |
| `api/routes/knowledge.py` | `/api/knowledge` | `POST` | `/apply/{pattern_id}` | `/api/knowledge/apply/{pattern_id}` |
| `api/routes/knowledge.py` | `/api/knowledge` | `PUT` | `/review/{pattern_id}` | `/api/knowledge/review/{pattern_id}` |
| `api/routes/loop.py` | `/api/loop` | `POST` | `/start` | `/api/loop/start` |
| `api/routes/loop.py` | `/api/loop` | `POST` | `/stop` | `/api/loop/stop` |
| `api/routes/loop.py` | `/api/loop` | `GET` | `/status` | `/api/loop/status` |
| `api/routes/memory.py` | `/api/memory` | `GET` | `/` | `/api/memory/` |
| `api/routes/memory.py` | `/api/memory` | `PUT` | `/` | `/api/memory/` |
| `api/routes/memory.py` | `/api/memory` | `POST` | `/note` | `/api/memory/note` |
| `api/routes/memory.py` | `/api/memory` | `GET` | `/context` | `/api/memory/context` |
| `api/routes/notifications.py` | `/api/notifications` | `POST` | `/webhook` | `/api/notifications/webhook` |
| `api/routes/notifications.py` | `/api/notifications` | `POST` | `/slack` | `/api/notifications/slack` |
| `api/routes/notifications.py` | `/api/notifications` | `POST` | `/email` | `/api/notifications/email` |
| `api/routes/notifications.py` | `/api/notifications` | `GET` | `/subscriptions` | `/api/notifications/subscriptions` |
| `api/routes/notifications.py` | `/api/notifications` | `DELETE` | `/subscriptions/{subscription_id}` | `/api/notifications/subscriptions/{subscription_id}` |
| `api/routes/notifications.py` | `/api/notifications` | `POST` | `/test/{subscription_id}` | `/api/notifications/test/{subscription_id}` |
| `api/routes/notifications.py` | `/api/notifications` | `GET` | `/history` | `/api/notifications/history` |
| `api/routes/opportunities.py` | `/api/opportunities` | `GET` | `/count` | `/api/opportunities/count` |
| `api/routes/opportunities.py` | `/api/opportunities` | `GET` | `/{opportunity_id}` | `/api/opportunities/{opportunity_id}` |
| `api/routes/opportunities.py` | `/api/opportunities` | `POST` | `/{opportunity_id}/status` | `/api/opportunities/{opportunity_id}/status` |
| `api/routes/optimize.py` | `/api/optimize` | `POST` | `/run` | `/api/optimize/run` |
| `api/routes/optimize.py` | `/api/optimize` | `GET` | `/history` | `/api/optimize/history` |
| `api/routes/optimize.py` | `/api/optimize` | `GET` | `/history/{attempt_id}` | `/api/optimize/history/{attempt_id}` |
| `api/routes/optimize.py` | `/api/optimize` | `GET` | `/pareto` | `/api/optimize/pareto` |
| `api/routes/optimize_stream.py` | `/api/optimize` | `GET` | `/stream` | `/api/optimize/stream` |
| `api/routes/outcomes.py` | `/api/outcomes` | `POST` | `/batch` | `/api/outcomes/batch` |
| `api/routes/outcomes.py` | `/api/outcomes` | `GET` | `/stats` | `/api/outcomes/stats` |
| `api/routes/outcomes.py` | `/api/outcomes` | `POST` | `/webhook` | `/api/outcomes/webhook` |
| `api/routes/outcomes.py` | `/api/outcomes` | `POST` | `/import/csv` | `/api/outcomes/import/csv` |
| `api/routes/outcomes.py` | `/api/outcomes` | `POST` | `/recalibrate/judges` | `/api/outcomes/recalibrate/judges` |
| `api/routes/outcomes.py` | `/api/outcomes` | `POST` | `/recalibrate/skills` | `/api/outcomes/recalibrate/skills` |
| `api/routes/outcomes.py` | `/api/outcomes` | `GET` | `/calibration/judges` | `/api/outcomes/calibration/judges` |
| `api/routes/outcomes.py` | `/api/outcomes` | `GET` | `/calibration/skills` | `/api/outcomes/calibration/skills` |
| `api/routes/policy_opt.py` | `/api/rl` | `POST` | `/datasets/build` | `/api/rl/datasets/build` |
| `api/routes/policy_opt.py` | `/api/rl` | `POST` | `/train` | `/api/rl/train` |
| `api/routes/policy_opt.py` | `/api/rl` | `GET` | `/jobs` | `/api/rl/jobs` |
| `api/routes/policy_opt.py` | `/api/rl` | `GET` | `/jobs/{job_id}` | `/api/rl/jobs/{job_id}` |
| `api/routes/policy_opt.py` | `/api/rl` | `GET` | `/policies` | `/api/rl/policies` |
| `api/routes/policy_opt.py` | `/api/rl` | `GET` | `/policies/{policy_id}` | `/api/rl/policies/{policy_id}` |
| `api/routes/policy_opt.py` | `/api/rl` | `POST` | `/evaluate` | `/api/rl/evaluate` |
| `api/routes/policy_opt.py` | `/api/rl` | `POST` | `/ope` | `/api/rl/ope` |
| `api/routes/policy_opt.py` | `/api/rl` | `POST` | `/canary` | `/api/rl/canary` |
| `api/routes/policy_opt.py` | `/api/rl` | `POST` | `/promote` | `/api/rl/promote` |
| `api/routes/policy_opt.py` | `/api/rl` | `POST` | `/rollback` | `/api/rl/rollback` |
| `api/routes/preferences.py` | `/api/preferences` | `POST` | `/pairs` | `/api/preferences/pairs` |
| `api/routes/preferences.py` | `/api/preferences` | `GET` | `/pairs` | `/api/preferences/pairs` |
| `api/routes/preferences.py` | `/api/preferences` | `GET` | `/stats` | `/api/preferences/stats` |
| `api/routes/preferences.py` | `/api/preferences` | `POST` | `/export` | `/api/preferences/export` |
| `api/routes/quickfix.py` | `/api` | `POST` | `/quickfix` | `/api/quickfix` |
| `api/routes/registry.py` | `/api/registry` | `GET` | `/search` | `/api/registry/search` |
| `api/routes/registry.py` | `/api/registry` | `POST` | `/import` | `/api/registry/import` |
| `api/routes/registry.py` | `/api/registry` | `GET` | `/{item_type}` | `/api/registry/{item_type}` |
| `api/routes/registry.py` | `/api/registry` | `GET` | `/{item_type}/{name}/diff` | `/api/registry/{item_type}/{name}/diff` |
| `api/routes/registry.py` | `/api/registry` | `GET` | `/{item_type}/{name}` | `/api/registry/{item_type}/{name}` |
| `api/routes/registry.py` | `/api/registry` | `POST` | `/{item_type}` | `/api/registry/{item_type}` |
| `api/routes/rewards.py` | `/api/rewards` | `GET` | `/{name}` | `/api/rewards/{name}` |
| `api/routes/rewards.py` | `/api/rewards` | `POST` | `/{name}/test` | `/api/rewards/{name}/test` |
| `api/routes/rewards.py` | `/api/rewards` | `GET` | `/hard-gates/list` | `/api/rewards/hard-gates/list` |
| `api/routes/rewards.py` | `/api/rewards` | `POST` | `/{name}/audit` | `/api/rewards/{name}/audit` |
| `api/routes/rewards.py` | `/api/rewards` | `POST` | `/challenge/run` | `/api/rewards/challenge/run` |
| `api/routes/runbooks.py` | `/api/runbooks` | `GET` | `/search` | `/api/runbooks/search` |
| `api/routes/runbooks.py` | `/api/runbooks` | `GET` | `/` | `/api/runbooks/` |
| `api/routes/runbooks.py` | `/api/runbooks` | `GET` | `/{name}` | `/api/runbooks/{name}` |
| `api/routes/runbooks.py` | `/api/runbooks` | `POST` | `/` | `/api/runbooks/` |
| `api/routes/runbooks.py` | `/api/runbooks` | `POST` | `/{name}/apply` | `/api/runbooks/{name}/apply` |
| `api/routes/sandbox.py` | `/api/sandbox` | `POST` | `/generate` | `/api/sandbox/generate` |
| `api/routes/sandbox.py` | `/api/sandbox` | `GET` | `/conversations/{conversation_set_id}` | `/api/sandbox/conversations/{conversation_set_id}` |
| `api/routes/sandbox.py` | `/api/sandbox` | `POST` | `/test` | `/api/sandbox/test` |
| `api/routes/sandbox.py` | `/api/sandbox` | `POST` | `/compare` | `/api/sandbox/compare` |
| `api/routes/sandbox.py` | `/api/sandbox` | `GET` | `/results/{result_id}` | `/api/sandbox/results/{result_id}` |
| `api/routes/scorers.py` | `/api/scorers` | `POST` | `/create` | `/api/scorers/create` |
| `api/routes/scorers.py` | `/api/scorers` | `GET` | `/{name}` | `/api/scorers/{name}` |
| `api/routes/scorers.py` | `/api/scorers` | `POST` | `/{name}/refine` | `/api/scorers/{name}/refine` |
| `api/routes/scorers.py` | `/api/scorers` | `POST` | `/{name}/test` | `/api/scorers/{name}/test` |
| `api/routes/skills.py` | `/api/skills` | `GET` | `/recommend` | `/api/skills/recommend` |
| `api/routes/skills.py` | `/api/skills` | `GET` | `/stats` | `/api/skills/stats` |
| `api/routes/skills.py` | `/api/skills` | `POST` | `/compose` | `/api/skills/compose` |
| `api/routes/skills.py` | `/api/skills` | `GET` | `/marketplace` | `/api/skills/marketplace` |
| `api/routes/skills.py` | `/api/skills` | `POST` | `/install` | `/api/skills/install` |
| `api/routes/skills.py` | `/api/skills` | `POST` | `/search` | `/api/skills/search` |
| `api/routes/skills.py` | `/api/skills` | `POST` | `/from-conversation` | `/api/skills/from-conversation` |
| `api/routes/skills.py` | `/api/skills` | `POST` | `/from-optimization` | `/api/skills/from-optimization` |
| `api/routes/skills.py` | `/api/skills` | `GET` | `/drafts` | `/api/skills/drafts` |
| `api/routes/skills.py` | `/api/skills` | `POST` | `/{skill_id}/promote` | `/api/skills/{skill_id}/promote` |
| `api/routes/skills.py` | `/api/skills` | `POST` | `/{skill_id}/archive` | `/api/skills/{skill_id}/archive` |
| `api/routes/skills.py` | `/api/skills` | `GET` | `/{skill_id}` | `/api/skills/{skill_id}` |
| `api/routes/skills.py` | `/api/skills` | `PUT` | `/{skill_id}` | `/api/skills/{skill_id}` |
| `api/routes/skills.py` | `/api/skills` | `DELETE` | `/{skill_id}` | `/api/skills/{skill_id}` |
| `api/routes/skills.py` | `/api/skills` | `POST` | `/{skill_id}/test` | `/api/skills/{skill_id}/test` |
| `api/routes/skills.py` | `/api/skills` | `POST` | `/{skill_id}/apply` | `/api/skills/{skill_id}/apply` |
| `api/routes/skills.py` | `/api/skills` | `GET` | `/{skill_id}/effectiveness` | `/api/skills/{skill_id}/effectiveness` |
| `api/routes/traces.py` | `/api/traces` | `GET` | `/recent` | `/api/traces/recent` |
| `api/routes/traces.py` | `/api/traces` | `GET` | `/search` | `/api/traces/search` |
| `api/routes/traces.py` | `/api/traces` | `GET` | `/errors` | `/api/traces/errors` |
| `api/routes/traces.py` | `/api/traces` | `GET` | `/sessions/{session_id}` | `/api/traces/sessions/{session_id}` |
| `api/routes/traces.py` | `/api/traces` | `GET` | `/blame` | `/api/traces/blame` |
| `api/routes/traces.py` | `/api/traces` | `GET` | `/{trace_id}/grades` | `/api/traces/{trace_id}/grades` |
| `api/routes/traces.py` | `/api/traces` | `GET` | `/{trace_id}/graph` | `/api/traces/{trace_id}/graph` |
| `api/routes/traces.py` | `/api/traces` | `GET` | `/{trace_id}` | `/api/traces/{trace_id}` |
| `api/routes/what_if.py` | `/api/what-if` | `POST` | `/replay` | `/api/what-if/replay` |
| `api/routes/what_if.py` | `/api/what-if` | `GET` | `/results/{job_id}` | `/api/what-if/results/{job_id}` |
| `api/routes/what_if.py` | `/api/what-if` | `POST` | `/project` | `/api/what-if/project` |
| `api/routes/what_if.py` | `/api/what-if` | `GET` | `/jobs` | `/api/what-if/jobs` |

## Module Breakdown

### `api/routes/__init__.py`
- File size: 1 lines
- Router prefix: `/`
- Endpoint count: 0

### `api/routes/a2a.py`
- File size: 238 lines
- Router prefix: `/`
- Endpoint count: 6
- Endpoints:
  - `GET` `/.well-known/agent-card.json`
  - `POST` `/api/a2a/tasks/send`
  - `GET` `/api/a2a/tasks/{task_id}`
  - `POST` `/api/a2a/tasks/{task_id}/cancel`
  - `GET` `/api/a2a/agents`
  - `POST` `/api/a2a/discover`

### `api/routes/adk.py`
- File size: 187 lines
- Router prefix: `/api/adk`
- Endpoint count: 5
- Endpoints:
  - `POST` `/api/adk/import`
  - `POST` `/api/adk/export`
  - `POST` `/api/adk/deploy`
  - `GET` `/api/adk/status`
  - `GET` `/api/adk/diff`

### `api/routes/agent_skills.py`
- File size: 160 lines
- Router prefix: `/api/agent-skills`
- Endpoint count: 8
- Endpoints:
  - `GET` `/api/agent-skills/gaps`
  - `POST` `/api/agent-skills/analyze`
  - `POST` `/api/agent-skills/generate`
  - `GET` `/api/agent-skills/`
  - `GET` `/api/agent-skills/{skill_id}`
  - `POST` `/api/agent-skills/{skill_id}/approve`
  - `POST` `/api/agent-skills/{skill_id}/reject`
  - `POST` `/api/agent-skills/{skill_id}/apply`

### `api/routes/assistant.py`
- File size: 729 lines
- Router prefix: `/api/assistant`
- Endpoint count: 7
- Endpoints:
  - `POST` `/api/assistant/message`
  - `GET` `/api/assistant/message`
  - `POST` `/api/assistant/upload`
  - `GET` `/api/assistant/history`
  - `DELETE` `/api/assistant/history`
  - `GET` `/api/assistant/suggestions`
  - `POST` `/api/assistant/action/{action_id}`

### `api/routes/autofix.py`
- File size: 80 lines
- Router prefix: `/api/autofix`
- Endpoint count: 4
- Endpoints:
  - `POST` `/api/autofix/suggest`
  - `GET` `/api/autofix/proposals`
  - `POST` `/api/autofix/apply/{proposal_id}`
  - `GET` `/api/autofix/history`

### `api/routes/builder.py`
- File size: 576 lines
- Router prefix: `/api/builder`
- Endpoint count: 36
- Endpoints:
  - `GET` `/api/builder/projects`
  - `POST` `/api/builder/projects`
  - `GET` `/api/builder/projects/{project_id}`
  - `PATCH` `/api/builder/projects/{project_id}`
  - `DELETE` `/api/builder/projects/{project_id}`
  - `GET` `/api/builder/sessions`
  - `POST` `/api/builder/sessions`
  - `GET` `/api/builder/sessions/{session_id}`
  - `POST` `/api/builder/sessions/{session_id}/close`
  - `GET` `/api/builder/tasks`
  - `POST` `/api/builder/tasks`
  - `GET` `/api/builder/tasks/{task_id}`
  - `POST` `/api/builder/tasks/{task_id}/pause`
  - `POST` `/api/builder/tasks/{task_id}/resume`
  - `POST` `/api/builder/tasks/{task_id}/cancel`
  - `POST` `/api/builder/tasks/{task_id}/duplicate`
  - `POST` `/api/builder/tasks/{task_id}/fork`
  - `POST` `/api/builder/tasks/{task_id}/progress`
  - `GET` `/api/builder/proposals`
  - `GET` `/api/builder/proposals/{proposal_id}`
  - `POST` `/api/builder/proposals/{proposal_id}/approve`
  - `POST` `/api/builder/proposals/{proposal_id}/reject`
  - `POST` `/api/builder/proposals/{proposal_id}/revise`
  - `GET` `/api/builder/artifacts`
  - `GET` `/api/builder/artifacts/{artifact_id}`
  - `POST` `/api/builder/artifacts/{artifact_id}/comment`
  - `GET` `/api/builder/approvals`
  - `POST` `/api/builder/approvals/{approval_id}/respond`
  - `GET` `/api/builder/permissions/grants`
  - `POST` `/api/builder/permissions/grants`
  - `DELETE` `/api/builder/permissions/grants/{grant_id}`
  - `GET` `/api/builder/events`
  - `GET` `/api/builder/events/stream`
  - `GET` `/api/builder/metrics`
  - `GET` `/api/builder/specialists`
  - `POST` `/api/builder/specialists/{role}/invoke`

### `api/routes/builder_demo.py`
- File size: 116 lines
- Router prefix: `/api/builder/demo`
- Endpoint count: 5
- Endpoints:
  - `POST` `/api/builder/demo/seed`
  - `POST` `/api/builder/demo/reset`
  - `GET` `/api/builder/demo/acts`
  - `POST` `/api/builder/demo/acts/{act_id}/play`
  - `GET` `/api/builder/demo/status`

### `api/routes/changes.py`
- File size: 261 lines
- Router prefix: `/api/changes`
- Endpoint count: 8
- Endpoints:
  - `GET` `/api/changes/`
  - `GET` `/api/changes/{card_id}`
  - `POST` `/api/changes/{card_id}/apply`
  - `POST` `/api/changes/{card_id}/reject`
  - `PATCH` `/api/changes/{card_id}/hunks`
  - `GET` `/api/changes/{card_id}/export`
  - `GET` `/api/changes/{card_id}/audit`
  - `GET` `/api/changes/audit-summary`

### `api/routes/cicd.py`
- File size: 162 lines
- Router prefix: `/api/cicd`
- Endpoint count: 3
- Endpoints:
  - `POST` `/api/cicd/webhook`
  - `GET` `/api/cicd/status/{repository}/{branch}`
  - `GET` `/api/cicd/history/{repository}`

### `api/routes/collaboration.py`
- File size: 86 lines
- Router prefix: `/api/reviews`
- Endpoint count: 4
- Endpoints:
  - `POST` `/api/reviews/request`
  - `POST` `/api/reviews/{request_id}/submit`
  - `GET` `/api/reviews/pending`
  - `GET` `/api/reviews/{request_id}`

### `api/routes/config.py`
- File size: 114 lines
- Router prefix: `/api/config`
- Endpoint count: 4
- Endpoints:
  - `GET` `/api/config/list`
  - `GET` `/api/config/show/{version}`
  - `GET` `/api/config/diff`
  - `GET` `/api/config/active`

### `api/routes/context.py`
- File size: 99 lines
- Router prefix: `/api/context`
- Endpoint count: 3
- Endpoints:
  - `GET` `/api/context/analysis/{trace_id}`
  - `POST` `/api/context/simulate`
  - `GET` `/api/context/report`

### `api/routes/control.py`
- File size: 137 lines
- Router prefix: `/api/control`
- Endpoint count: 7
- Endpoints:
  - `GET` `/api/control/state`
  - `POST` `/api/control/pause`
  - `POST` `/api/control/resume`
  - `POST` `/api/control/pin/{surface}`
  - `POST` `/api/control/unpin/{surface}`
  - `POST` `/api/control/reject/{experiment_id}`
  - `POST` `/api/control/inject`

### `api/routes/conversations.py`
- File size: 114 lines
- Router prefix: `/api/conversations`
- Endpoint count: 2
- Endpoints:
  - `GET` `/api/conversations/stats`
  - `GET` `/api/conversations/{conversation_id}`

### `api/routes/curriculum.py`
- File size: 224 lines
- Router prefix: `/api/curriculum`
- Endpoint count: 4
- Endpoints:
  - `POST` `/api/curriculum/generate`
  - `GET` `/api/curriculum/batches`
  - `GET` `/api/curriculum/batches/{batch_id}`
  - `POST` `/api/curriculum/apply`

### `api/routes/cx_studio.py`
- File size: 248 lines
- Router prefix: `/api/cx`
- Endpoint count: 7
- Endpoints:
  - `GET` `/api/cx/agents`
  - `POST` `/api/cx/import`
  - `POST` `/api/cx/export`
  - `POST` `/api/cx/deploy`
  - `POST` `/api/cx/widget`
  - `GET` `/api/cx/status`
  - `GET` `/api/cx/preview`

### `api/routes/datasets.py`
- File size: 286 lines
- Router prefix: `/api/datasets`
- Endpoint count: 13
- Endpoints:
  - `GET` `/api/datasets/{dataset_id}`
  - `POST` `/api/datasets/{dataset_id}/rows`
  - `POST` `/api/datasets/{dataset_id}/versions`
  - `GET` `/api/datasets/{dataset_id}/versions`
  - `GET` `/api/datasets/{dataset_id}/rows`
  - `GET` `/api/datasets/{dataset_id}/stats`
  - `POST` `/api/datasets/{dataset_id}/import/traces`
  - `POST` `/api/datasets/{dataset_id}/import/eval-cases`
  - `POST` `/api/datasets/{dataset_id}/splits`
  - `POST` `/api/datasets/{dataset_id}/export`
  - `POST` `/api/datasets/{dataset_id}/pins`
  - `GET` `/api/datasets/{dataset_id}/pins`
  - `GET` `/api/datasets/{dataset_id}/pins/{pin_id}`

### `api/routes/demo.py`
- File size: 273 lines
- Router prefix: `/api/demo`
- Endpoint count: 3
- Endpoints:
  - `GET` `/api/demo/status`
  - `GET` `/api/demo/scenario`
  - `GET` `/api/demo/stream`

### `api/routes/deploy.py`
- File size: 120 lines
- Router prefix: `/api/deploy`
- Endpoint count: 2
- Endpoints:
  - `GET` `/api/deploy/status`
  - `POST` `/api/deploy/rollback`

### `api/routes/diagnose.py`
- File size: 168 lines
- Router prefix: `/api/diagnose`
- Endpoint count: 1
- Endpoints:
  - `POST` `/api/diagnose/chat`

### `api/routes/edit.py`
- File size: 123 lines
- Router prefix: `/api/edit`
- Endpoint count: 0

### `api/routes/eval.py`
- File size: 193 lines
- Router prefix: `/api/eval`
- Endpoint count: 6
- Endpoints:
  - `POST` `/api/eval/run`
  - `GET` `/api/eval/runs`
  - `GET` `/api/eval/runs/{run_id}`
  - `GET` `/api/eval/runs/{run_id}/cases`
  - `GET` `/api/eval/history`
  - `GET` `/api/eval/history/{run_id}`

### `api/routes/events.py`
- File size: 20 lines
- Router prefix: `/api/events`
- Endpoint count: 0

### `api/routes/experiments.py`
- File size: 209 lines
- Router prefix: `/api/experiments`
- Endpoint count: 5
- Endpoints:
  - `GET` `/api/experiments/stats`
  - `GET` `/api/experiments/archive`
  - `GET` `/api/experiments/pareto`
  - `GET` `/api/experiments/judge-calibration`
  - `GET` `/api/experiments/{experiment_id}`

### `api/routes/health.py`
- File size: 202 lines
- Router prefix: `/api/health`
- Endpoint count: 5
- Endpoints:
  - `GET` `/api/health/ready`
  - `GET` `/api/health/system`
  - `GET` `/api/health/cost`
  - `GET` `/api/health/eval-set`
  - `GET` `/api/health/scorecard`

### `api/routes/impact.py`
- File size: 74 lines
- Router prefix: `/api/impact`
- Endpoint count: 3
- Endpoints:
  - `POST` `/api/impact/analyze`
  - `GET` `/api/impact/dependencies`
  - `GET` `/api/impact/report/{analysis_id}`

### `api/routes/intelligence.py`
- File size: 162 lines
- Router prefix: `/api/intelligence`
- Endpoint count: 9
- Endpoints:
  - `POST` `/api/intelligence/archive`
  - `GET` `/api/intelligence/reports`
  - `GET` `/api/intelligence/reports/{report_id}`
  - `POST` `/api/intelligence/reports/{report_id}/ask`
  - `POST` `/api/intelligence/reports/{report_id}/apply`
  - `POST` `/api/intelligence/build`
  - `GET` `/api/intelligence/knowledge/{asset_id}`
  - `POST` `/api/intelligence/reports/{report_id}/deep-research`
  - `POST` `/api/intelligence/reports/{report_id}/autonomous-loop`

### `api/routes/judges.py`
- File size: 95 lines
- Router prefix: `/api/judges`
- Endpoint count: 3
- Endpoints:
  - `POST` `/api/judges/feedback`
  - `GET` `/api/judges/calibration`
  - `GET` `/api/judges/drift`

### `api/routes/knowledge.py`
- File size: 114 lines
- Router prefix: `/api/knowledge`
- Endpoint count: 4
- Endpoints:
  - `POST` `/api/knowledge/mine`
  - `GET` `/api/knowledge/entries`
  - `POST` `/api/knowledge/apply/{pattern_id}`
  - `PUT` `/api/knowledge/review/{pattern_id}`

### `api/routes/loop.py`
- File size: 364 lines
- Router prefix: `/api/loop`
- Endpoint count: 3
- Endpoints:
  - `POST` `/api/loop/start`
  - `POST` `/api/loop/stop`
  - `GET` `/api/loop/status`

### `api/routes/memory.py`
- File size: 89 lines
- Router prefix: `/api/memory`
- Endpoint count: 4
- Endpoints:
  - `GET` `/api/memory/`
  - `PUT` `/api/memory/`
  - `POST` `/api/memory/note`
  - `GET` `/api/memory/context`

### `api/routes/notifications.py`
- File size: 123 lines
- Router prefix: `/api/notifications`
- Endpoint count: 7
- Endpoints:
  - `POST` `/api/notifications/webhook`
  - `POST` `/api/notifications/slack`
  - `POST` `/api/notifications/email`
  - `GET` `/api/notifications/subscriptions`
  - `DELETE` `/api/notifications/subscriptions/{subscription_id}`
  - `POST` `/api/notifications/test/{subscription_id}`
  - `GET` `/api/notifications/history`

### `api/routes/opportunities.py`
- File size: 90 lines
- Router prefix: `/api/opportunities`
- Endpoint count: 3
- Endpoints:
  - `GET` `/api/opportunities/count`
  - `GET` `/api/opportunities/{opportunity_id}`
  - `POST` `/api/opportunities/{opportunity_id}/status`

### `api/routes/optimize.py`
- File size: 227 lines
- Router prefix: `/api/optimize`
- Endpoint count: 4
- Endpoints:
  - `POST` `/api/optimize/run`
  - `GET` `/api/optimize/history`
  - `GET` `/api/optimize/history/{attempt_id}`
  - `GET` `/api/optimize/pareto`

### `api/routes/optimize_stream.py`
- File size: 149 lines
- Router prefix: `/api/optimize`
- Endpoint count: 1
- Endpoints:
  - `GET` `/api/optimize/stream`

### `api/routes/outcomes.py`
- File size: 214 lines
- Router prefix: `/api/outcomes`
- Endpoint count: 8
- Endpoints:
  - `POST` `/api/outcomes/batch`
  - `GET` `/api/outcomes/stats`
  - `POST` `/api/outcomes/webhook`
  - `POST` `/api/outcomes/import/csv`
  - `POST` `/api/outcomes/recalibrate/judges`
  - `POST` `/api/outcomes/recalibrate/skills`
  - `GET` `/api/outcomes/calibration/judges`
  - `GET` `/api/outcomes/calibration/skills`

### `api/routes/policy_opt.py`
- File size: 195 lines
- Router prefix: `/api/rl`
- Endpoint count: 11
- Endpoints:
  - `POST` `/api/rl/datasets/build`
  - `POST` `/api/rl/train`
  - `GET` `/api/rl/jobs`
  - `GET` `/api/rl/jobs/{job_id}`
  - `GET` `/api/rl/policies`
  - `GET` `/api/rl/policies/{policy_id}`
  - `POST` `/api/rl/evaluate`
  - `POST` `/api/rl/ope`
  - `POST` `/api/rl/canary`
  - `POST` `/api/rl/promote`
  - `POST` `/api/rl/rollback`

### `api/routes/preferences.py`
- File size: 121 lines
- Router prefix: `/api/preferences`
- Endpoint count: 4
- Endpoints:
  - `POST` `/api/preferences/pairs`
  - `GET` `/api/preferences/pairs`
  - `GET` `/api/preferences/stats`
  - `POST` `/api/preferences/export`

### `api/routes/quickfix.py`
- File size: 60 lines
- Router prefix: `/api`
- Endpoint count: 1
- Endpoints:
  - `POST` `/api/quickfix`

### `api/routes/registry.py`
- File size: 192 lines
- Router prefix: `/api/registry`
- Endpoint count: 6
- Endpoints:
  - `GET` `/api/registry/search`
  - `POST` `/api/registry/import`
  - `GET` `/api/registry/{item_type}`
  - `GET` `/api/registry/{item_type}/{name}/diff`
  - `GET` `/api/registry/{item_type}/{name}`
  - `POST` `/api/registry/{item_type}`

### `api/routes/rewards.py`
- File size: 109 lines
- Router prefix: `/api/rewards`
- Endpoint count: 5
- Endpoints:
  - `GET` `/api/rewards/{name}`
  - `POST` `/api/rewards/{name}/test`
  - `GET` `/api/rewards/hard-gates/list`
  - `POST` `/api/rewards/{name}/audit`
  - `POST` `/api/rewards/challenge/run`

### `api/routes/runbooks.py`
- File size: 90 lines
- Router prefix: `/api/runbooks`
- Endpoint count: 5
- Endpoints:
  - `GET` `/api/runbooks/search`
  - `GET` `/api/runbooks/`
  - `GET` `/api/runbooks/{name}`
  - `POST` `/api/runbooks/`
  - `POST` `/api/runbooks/{name}/apply`

### `api/routes/sandbox.py`
- File size: 246 lines
- Router prefix: `/api/sandbox`
- Endpoint count: 5
- Endpoints:
  - `POST` `/api/sandbox/generate`
  - `GET` `/api/sandbox/conversations/{conversation_set_id}`
  - `POST` `/api/sandbox/test`
  - `POST` `/api/sandbox/compare`
  - `GET` `/api/sandbox/results/{result_id}`

### `api/routes/scorers.py`
- File size: 110 lines
- Router prefix: `/api/scorers`
- Endpoint count: 4
- Endpoints:
  - `POST` `/api/scorers/create`
  - `GET` `/api/scorers/{name}`
  - `POST` `/api/scorers/{name}/refine`
  - `POST` `/api/scorers/{name}/test`

### `api/routes/skills.py`
- File size: 1008 lines
- Router prefix: `/api/skills`
- Endpoint count: 17
- Endpoints:
  - `GET` `/api/skills/recommend`
  - `GET` `/api/skills/stats`
  - `POST` `/api/skills/compose`
  - `GET` `/api/skills/marketplace`
  - `POST` `/api/skills/install`
  - `POST` `/api/skills/search`
  - `POST` `/api/skills/from-conversation`
  - `POST` `/api/skills/from-optimization`
  - `GET` `/api/skills/drafts`
  - `POST` `/api/skills/{skill_id}/promote`
  - `POST` `/api/skills/{skill_id}/archive`
  - `GET` `/api/skills/{skill_id}`
  - `PUT` `/api/skills/{skill_id}`
  - `DELETE` `/api/skills/{skill_id}`
  - `POST` `/api/skills/{skill_id}/test`
  - `POST` `/api/skills/{skill_id}/apply`
  - `GET` `/api/skills/{skill_id}/effectiveness`

### `api/routes/traces.py`
- File size: 162 lines
- Router prefix: `/api/traces`
- Endpoint count: 8
- Endpoints:
  - `GET` `/api/traces/recent`
  - `GET` `/api/traces/search`
  - `GET` `/api/traces/errors`
  - `GET` `/api/traces/sessions/{session_id}`
  - `GET` `/api/traces/blame`
  - `GET` `/api/traces/{trace_id}/grades`
  - `GET` `/api/traces/{trace_id}/graph`
  - `GET` `/api/traces/{trace_id}`

### `api/routes/what_if.py`
- File size: 138 lines
- Router prefix: `/api/what-if`
- Endpoint count: 4
- Endpoints:
  - `POST` `/api/what-if/replay`
  - `GET` `/api/what-if/results/{job_id}`
  - `POST` `/api/what-if/project`
  - `GET` `/api/what-if/jobs`


### 10.4 Appendix C — Suggested onboarding sequence for teams

Day 1:

- Run setup/start.
- Execute quickstart.
- Read status/config/eval outputs.
- Tour Dashboard, Conversations, Traces, Configs.

Day 2:

- Run controlled optimize cycles.
- Use review/runbook flows.
- Validate deploy canary mechanics in non-prod environment.

Day 3:

- Introduce Builder Workspace with draft mode only.
- Test approval and permission workflows.
- Configure notifications and Judge Ops monitoring.

Week 2:

- Integrate CX/ADK pipelines where needed.
- Expand eval datasets and outcomes ingestion.
- Pilot reward/policy optimization on bounded scope.

### 10.5 Closing guidance

AutoAgent rewards disciplined operation:

- Keep feedback loops tight.
- Keep risk boundaries explicit.
- Keep human controls active.
- Keep evaluation quality high.

When those are in place, continuous optimization becomes a practical reliability advantage rather than a source of instability.

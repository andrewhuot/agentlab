# AutoAgent VNextCC

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB)
![735 tests](https://img.shields.io/badge/tests-735_passing-22C55E)
![License](https://img.shields.io/badge/license-Apache%202.0-111827)

**Continuous evaluation and optimization for AI agents.** Point it at an agent, and it runs an autonomous loop — trace, diagnose, search for improvements, gate on statistical significance, deploy via canary, repeat.

CLI-first. Gemini-first, multi-model capable. Research-grade, not a SaaS product.

---

## How It Works

The core loop is Karpathy-simple:

```
1. TRACE     → Collect structured events from agent invocations
2. DIAGNOSE  → Cluster failures, score opportunities
3. SEARCH    → Generate typed mutations, rank by lift/risk/novelty
4. EVAL      → Replay with side-effect isolation, grade with judge stack
5. GATE      → Hard constraints first, then optimize objectives
6. DEPLOY    → Canary with experiment card tracking
7. LEARN     → Record what worked, avoid what didn't
8. REPEAT
```

Each cycle is wrapped in exception handling. Failures go to a dead letter queue — the loop never crashes.

## Quickstart

```bash
# Install
pip install -e ".[dev]"

# Initialize and run an eval
autoagent init
autoagent eval run --output results.json

# Start API + web console
autoagent server
# → http://localhost:8000
```

Output looks like:

```
Full eval suite
  Cases: 42/50 passed
  Quality:   0.7800
  Safety:    1.0000 (0 failures)
  Latency:   0.8500
  Cost:      0.7200
  Composite: 0.8270
```

Run the full optimization loop:

```bash
autoagent loop --max-cycles 20 --stop-on-plateau
```

## Key Concepts

### 4-Layer Metric Hierarchy

The optimizer doesn't collapse everything into one number. Metrics are layered:

| Layer | What | Role |
|-------|------|------|
| **Hard Gates** | Safety, authorization, state integrity, P0 regressions | Must pass — binary |
| **North-Star Outcomes** | Task success, groundedness, user satisfaction | Optimized |
| **Operating SLOs** | Latency (p50/p95/p99), token cost, escalation rate | Constrained |
| **Diagnostics** | Tool correctness, routing accuracy, handoff fidelity, judge disagreement | Diagnosis only — never optimized directly |

The optimizer searches Layer 2 within Layer 1, subject to Layer 3. Layer 4 is for humans.

### Typed Mutations

Every change the optimizer proposes is a first-class object with a surface, risk class, and validator:

```
instruction_rewrite  →  low risk   →  auto-deploy
few_shot_edit        →  low risk   →  auto-deploy
tool_description     →  medium     →  auto-deploy
model_swap           →  high risk  →  human review
callback_patch       →  high risk  →  human review
```

Nine built-in operators, plus Google Prompt Optimizer stubs and experimental topology operators.

### Experiment Cards

Every optimization attempt produces a reviewable card — not just "config v17":

- Hypothesis and touched surfaces
- Baseline/candidate SHA for reproducibility
- Risk class and deployment policy
- Statistical significance (p-value, effect size, confidence interval)
- Full diff summary

### Judge Subsystem

A tiered grading pipeline, not a single LLM call:

1. **Deterministic graders** — regex, state checks, business invariants (confidence=1.0)
2. **Similarity graders** — token-overlap Jaccard scoring
3. **Binary rubric judges** — 4 yes/no questions, fast and cheap for routine evals
4. **Audit judge** — cross-family LLM judge for promotions (different model family than proposer)
5. **Calibration suite** — agreement rate, drift detection, position bias, verbosity bias

### Human Escape Hatches

The loop is autonomous, but humans stay in control:

```bash
autoagent pause          # Pause optimization
autoagent resume         # Resume
autoagent pin safety     # Make a surface immutable
autoagent reject exp-42  # Reject experiment + rollback canary
```

All actions available via CLI, API, and web dashboard.

### Cost Controls

SQLite-backed per-cycle and daily budget tracking. Diminishing returns detection pauses the loop when N consecutive cycles show no improvement.

```yaml
budget:
  per_cycle_dollars: 1.0
  daily_dollars: 10.0
  stall_threshold_cycles: 5
```

### Anti-Goodhart Guards

Three mechanisms prevent overfitting to the eval set:

- **Holdout rotation** — tuning/validation/holdout partitions rotate periodically
- **Drift detection** — monitors tuning vs. validation gap, flags overfitting
- **Judge variance estimation** — accounts for LLM judge noise in significance testing

## CLI Reference

```bash
autoagent init --template customer-support
autoagent eval run --config configs/v003.yaml
autoagent eval results --file results.json
autoagent optimize --cycles 3
autoagent config list
autoagent config diff 1 3
autoagent deploy --config-version 5 --strategy canary
autoagent loop --max-cycles 20 --stop-on-plateau
autoagent status
autoagent logs --limit 25 --outcome fail
autoagent server
autoagent pause / resume / pin / reject
```

## Web Console

React + Vite + TypeScript + Tailwind. 13 pages:

| Page | Purpose |
|------|---------|
| Dashboard | 2 hard gates + 4 primary metrics, cost controls, event timeline |
| Eval Runs | Sortable table of all evaluations |
| Eval Detail | Per-case results with pass/fail breakdown |
| Optimize | Trigger optimization, view attempt history |
| Experiments | Reviewable experiment cards with hypothesis and diff |
| Opportunities | Ranked optimization opportunity queue |
| Traces | ADK event traces and spans for diagnosis |
| Configs | Version list, YAML diff viewer |
| Conversations | Browse logged agent conversations |
| Deploy | Canary status, promote/rollback controls |
| Loop Monitor | Live loop status, cycle history, watchdog health |
| Event Log | Append-only system event timeline |
| Settings | Runtime configuration |

Screenshots are in `web/screenshots/`.

## API

38 endpoints across eval, optimize, traces, experiments, opportunities, control, deploy, health, config, conversations, events, and loop. Full list in [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md#rest-api).

Key groups:

```
POST /api/eval/run             Start eval
POST /api/optimize/run         Trigger optimization cycle
POST /api/loop/start           Start autonomous loop
GET  /api/experiments          Experiment cards
GET  /api/opportunities        Ranked opportunity queue
GET  /api/traces/recent        Recent trace events
POST /api/control/pause        Pause optimization
GET  /api/health/scorecard     2-gate + 4-metric scorecard
GET  /api/health/cost          Cost tracking and budget posture
GET  /api/events               Append-only event log
```

## Configuration

Everything is driven by `autoagent.yaml`:

```yaml
optimizer:
  search_strategy: simple       # simple | adaptive | full
  bandit_policy: ucb1           # ucb1 | thompson
  models:
    - provider: google          # google | openai | anthropic | openai_compatible | mock
      model: gemini-2.5-pro
      api_key_env: GOOGLE_API_KEY

budget:
  per_cycle_dollars: 1.0
  daily_dollars: 10.0
  stall_threshold_cycles: 5

human_control:
  immutable_surfaces: ["safety_instructions"]

eval:
  significance_alpha: 0.05
  significance_min_effect_size: 0.005
```

All fields have sensible defaults. Old configs keep working.

## Multi-Model Support

Gemini-first, but swap providers with one config change:

| Provider | Models | Auth |
|----------|--------|------|
| **Google** (default) | Gemini 2.5 Pro, Flash | `GOOGLE_API_KEY` |
| **OpenAI** | GPT-4o, GPT-5, o3 | `OPENAI_API_KEY` |
| **Anthropic** | Claude Sonnet, Opus | `ANTHROPIC_API_KEY` |
| **OpenAI-compatible** | Any local model | Custom `base_url` |
| **Mock** | Deterministic test proposer | No key needed |

## Architecture

```
core/           10 first-class domain objects (AgentGraphVersion, EvalCase, etc.)
judges/         Judge subsystem (deterministic, rule-based, LLM, audit, calibration)
graders/        Tiered grading pipeline (deterministic, similarity, binary rubric)
optimizer/      Loop, search, mutations, bandit, Pareto archive, cost tracker
evals/          Runner, scorer, data engine, replay harness, anti-Goodhart, statistics
observer/       Traces, anomaly detection, failure clustering, opportunity queue
api/            FastAPI server, 38 endpoints across 13 route modules
web/            React console, 13 pages, 28 components
deployer/       Canary deployment, release manager, config versioning
data/           Protocol-based repositories, event log
control/        Governance wrapper for promotion decisions
```

See [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) for the full breakdown.

## By the Numbers

| | |
|---|---|
| Test suite | **735 tests** |
| Python backend | ~24,000 lines |
| React frontend | ~9,000 lines |
| API endpoints | 38 |
| Frontend pages | 13 |
| Reusable components | 28 |
| Judge/grader modules | 9 |
| Python packages | 10 |
| Test files | 34 |

## What This Is (and Isn't)

This is a **research-grade platform** for continuous agent optimization. It's built to actually run — trace-to-deploy loop, real statistical gating, real canary deployments, multi-day unattended operation with checkpoint/resume and dead letter queues.

It is not a hosted product. There's no auth layer, no multi-tenancy, no billing. It's a tool for teams who want to point an optimization loop at their agents and let it run.

## Documentation

- [Architecture Overview](ARCHITECTURE_OVERVIEW.md)
- [Getting Started](docs/getting-started.md)
- [Concepts](docs/concepts.md)
- [CLI Reference](docs/cli-reference.md)
- [API Reference](docs/api-reference.md)
- [Web App Guide](docs/app-guide.md)
- [Deployment](docs/deployment.md)
- [FAQ](docs/faq.md)

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn, SQLite
- **CLI**: Click
- **Frontend**: React, Vite, TypeScript, Tailwind
- **Tests**: pytest (735 passing)

## License

Apache 2.0. See [LICENSE](LICENSE).

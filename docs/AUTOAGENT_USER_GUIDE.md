# AutoAgent VNextCC — User Guide & Technical Inventory

**Version:** 3.0.0 | **Date:** 2026-03-24 | **Audience:** Researchers, PMs, Engineering Leaders

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Feature Inventory](#3-feature-inventory)
   - 3a. Core Optimization Loop
   - 3b. Typed Mutations & Experiment Cards
   - 3c. 4-Layer Metric Hierarchy & Scoring
   - 3d. Judge Subsystem
   - 3e. Grader Stack
   - 3f. AutoFix Copilot
   - 3g. Judge Ops
   - 3h. Context Engineering Workbench
   - 3i. Pro-Mode Prompt Optimization
   - 3j. Modular Registry
   - 3k. Trace Grading & Blame Map
   - 3l. NL Scorer Generation
   - 3m. Anti-Goodhart Guards
   - 3n. Human Escape Hatches & Cost Controls
   - 3o. Deployment & Canary Management
   - 3p. Event Logging & Observability
4. [Technical Deep Dives](#4-technical-deep-dives)
5. [API & CLI Complete Reference](#5-api--cli-complete-reference)
6. [Test Architecture](#6-test-architecture)
7. [Deployment Architecture](#7-deployment-architecture)
8. [Research Lineage](#8-research-lineage)
9. [Gaps, Risks, and Roadmap Candidates](#9-gaps-risks-and-roadmap-candidates)

---

## 1. Executive Summary

### What AutoAgent Is

AutoAgent VNextCC is a closed-loop optimization framework for AI agents. It observes agent behavior in production, diagnoses failures, proposes targeted mutations to agent configuration, evaluates those mutations against a multi-dimensional scoring rubric, gates changes through statistical significance testing and safety checks, and deploys improvements via canary rollouts — all without human intervention unless requested.

The system treats agent optimization as a CI/CD pipeline for prompts, tools, and routing logic, applying the same rigor (eval suites, gating, rollback) that software engineering applies to code deployment.

### What Problem It Solves

AI agents deployed in production degrade silently. Prompts that worked at launch drift as user behavior changes. New tool integrations break existing flows. Safety violations emerge in edge cases nobody anticipated. Manual prompt tuning is slow, subjective, and doesn't scale.

AutoAgent automates the feedback loop: trace failures → diagnose root causes → propose fixes → evaluate rigorously → deploy safely → repeat. It brings structure to what is currently an ad-hoc, human-in-the-loop process.

### Current Maturity Level

AutoAgent VNextCC is a **research prototype with production-grade infrastructure**. The optimization loop, eval framework, statistical gating, deployment pipeline, and observability stack are fully implemented and tested. The LLM-dependent components (LLM judge, LLM proposer, pro-mode algorithms) use deterministic mock providers in tests, ensuring correctness of orchestration logic without requiring live API calls.

### Key Statistics

| Metric | Count |
|--------|-------|
| Total Python source lines | 46,607 |
| Total frontend lines (TS/TSX) | 8,701 |
| Total lines (all code) | 55,308 |
| Python source files | 201 |
| Frontend source files | 55 |
| Test files | 59 |
| Test functions | 1,203 |
| Test lines | 19,060 |
| Python packages | 14 |
| API endpoints | 82 |
| CLI commands | 42 |
| Web pages | 19 |
| React components | 29 |
| Pydantic models | 27+ |
| SQLite databases | 7 |
| Domain dataclasses | 30+ |

---

## 2. Architecture Overview

### 2.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           WEB CONSOLE (React/Vite)                      │
│  19 pages  │  29 components  │  Zustand state  │  WebSocket live feed   │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │ HTTP / WebSocket
┌──────────────────────────────────▼──────────────────────────────────────┐
│                         REST API (FastAPI)                               │
│  82 endpoints  │  18 route modules  │  Background tasks  │  SPA serving  │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌───────────────┐  ┌───────────────────────┐  ┌──────────────────────┐
│   OBSERVER    │  │      OPTIMIZER        │  │     DEPLOYER         │
│               │  │                       │  │                      │
│ HealthMetrics │  │ Proposer → Gates →    │  │ ConfigVersionManager │
│ TraceStore    │  │ Pareto → Memory       │  │ CanaryManager        │
│ FailureClass  │  │                       │  │ ReleaseManager       │
│ AnomalyDetect │  │ Search Strategies:    │  │                      │
│ Opportunities │  │ Simple/Adaptive/Full  │  │ Promote / Rollback   │
│ TraceGrading  │  │ /Pro                  │  └──────────────────────┘
│ BlameMap      │  │                       │
│ TraceGraph    │  │ Pro-Mode:             │
└───────────────┘  │ MIPROv2/Bootstrap/    │  ┌──────────────────────┐
                   │ GEPA/SIMBA            │  │     JUDGES           │
┌───────────────┐  │                       │  │                      │
│    EVALS      │  │ Mutations: 9 built-in │  │ Deterministic        │
│               │  │ + topology + Google   │  │ RuleBased            │
│ EvalRunner    │  │                       │  │ LLMJudge             │
│ CompositeScor │  │ Anti-Goodhart:        │  │ AuditJudge           │
│ NLCompiler    │  │ Holdout/Drift/Var.    │  │ CalibrationSuite     │
│ Statistics    │  │                       │  │ Versioning           │
│ AntiGoodhart  │  │ Human Controls:       │  │ DriftMonitor         │
│ DataEngine    │  │ Pause/Pin/Reject      │  │ HumanFeedback        │
│ Replay        │  └───────────────────────┘  └──────────────────────┘
│ History       │
└───────────────┘  ┌───────────────────────┐  ┌──────────────────────┐
                   │    REGISTRY           │  │    CONTEXT           │
┌───────────────┐  │                       │  │                      │
│    CORE       │  │ SkillRegistry         │  │ ContextAnalyzer      │
│               │  │ PolicyRegistry        │  │ CompactionSimulator  │
│ AgentGraph IR │  │ ToolContractRegistry  │  │ ContextMetrics       │
│ EvalCase      │  │ HandoffSchemaRegistry │  └──────────────────────┘
│ ArchiveEntry  │  │ Importer (YAML/JSON)  │
│ MetricLayers  │  └───────────────────────┘  ┌──────────────────────┐
│ HandoffArtif  │                              │    LOGGER            │
│ JudgeVerdict  │  ┌───────────────────────┐  │                      │
└───────────────┘  │    CONTROL            │  │ ConversationStore    │
                   │                       │  │ StructuredLogging    │
┌───────────────┐  │ GovernanceEngine      │  │ SafetyDetection      │
│    DATA       │  └───────────────────────┘  └──────────────────────┘
│               │
│ TraceRepo     │  ┌───────────────────────┐
│ ArtifactRepo  │  │    AGENT (ADK)        │
│ EventLog      │  │                       │
└───────────────┘  │ RootAgent + 3 specs   │
                   │ TracingMiddleware      │
                   │ Config schema/loader   │
                   │ Tools (catalog/FAQ/    │
                   │   orders)              │
                   └───────────────────────┘
```

### 2.2 Package Dependency Map

| Package | Files | Lines | Primary Responsibility | Dependencies |
|---------|-------|-------|----------------------|--------------|
| `core/` | 3 | 1,079 | Domain types, agent graph IR, handoff artifacts | None (leaf) |
| `data/` | 3 | 242 | Repository protocols, event log | `core` |
| `control/` | 2 | 35 | Governance gating | `core` |
| `logger/` | 4 | 337 | Conversation store, structured logging | None |
| `observer/` | 9 | 2,052 | Health metrics, traces, anomaly detection, blame map | `core`, `evals` |
| `graders/` | 6 | 412 | Deterministic/similarity/LLM grading | None |
| `judges/` | 10 | 1,450 | Multi-layer judge pipeline, calibration, versioning | `graders` |
| `evals/` | 13+ | 4,555 | Eval runner, scoring, NL compiler, statistics, replay | `core`, `judges`, `graders` |
| `context/` | 4 | 517 | Context utilization analysis, compaction simulation | `core` |
| `registry/` | 7 | 669 | Versioned registry for skills, policies, contracts | None |
| `optimizer/` | 22 | 6,643 | Optimization loop, mutations, search, bandits, Pareto | `core`, `evals`, `observer`, `deployer` |
| `optimizer/prompt_opt/` | 8 | 1,357 | Pro-mode algorithms (MIPROv2, Bootstrap, GEPA, SIMBA) | `optimizer`, `evals` |
| `deployer/` | 4 | 622 | Config versioning, canary deployment, release pipeline | `evals`, `observer` |
| `agent/` | 17 | 921 | ADK agent, tracing, config, tools, specialists | `deployer`, `logger` |
| `api/` | 6 | 935 | FastAPI server, models, tasks, WebSocket | All packages |
| `api/routes/` | 17 | 2,453 | REST endpoints (18 route modules) | `api`, all packages |
| `runner.py` | 1 | 2,223 | CLI entry point (42 commands) | All packages |
| **Total Backend** | **201** | **46,607** | | |
| `web/src/pages/` | 19 | 4,194 | React page components | `web/src/lib` |
| `web/src/components/` | 29 | 2,259 | Reusable UI components | `web/src/lib` |
| `web/src/lib/` | 5 | 2,175 | API client, types, WebSocket, utils, toast | None |
| **Total Frontend** | **55** | **8,701** | | |

### 2.3 Data Flow: The Core Loop

```
Trace Ingestion        Diagnosis              Optimization            Eval                  Deployment
─────────────         ──────────             ──────────────          ──────                ──────────
ConversationStore  →  FailureClassifier  →   Proposer           →   EvalRunner        →   ConfigVersionManager
TraceStore             ↓                     (mock or LLM)           ↓                     ↓
                      AnomalyDetector        ↓                      CompositeScorer       CanaryManager
                       ↓                     MutationRegistry       ↓                     ↓
                      OpportunityQueue       ↓                      Gates (safety,        ReleaseManager
                       ↓                     BanditSelector          improvement,          ↓
                      TraceGrading           ↓                       regression,          Promote / Rollback
                       ↓                     CurriculumScheduler     constraints)
                      BlameMap                                       ↓
                                                                    ParetoArchive
                                                                     ↓
                                                                    OptimizationMemory
```

### 2.4 Storage Layer

**SQLite Databases (7):**

| Database | Default Path | Tables | Used By |
|----------|-------------|--------|---------|
| `conversations.db` | `AUTOAGENT_DB` | `conversations` | `logger.ConversationStore` |
| `optimizer_memory.db` | `AUTOAGENT_MEMORY_DB` | `attempts` | `optimizer.OptimizationMemory` |
| `registry.db` | `AUTOAGENT_REGISTRY_DB` | `skills`, `policies`, `tool_contracts`, `handoff_schemas` | `registry.RegistryStore` |
| `traces.db` | `AUTOAGENT_TRACE_DB` | `events`, `spans` | `observer.TraceStore` |
| `eval_history.db` | `AUTOAGENT_EVAL_HISTORY_DB` | `runs`, `case_results` | `evals.EvalHistory` |
| `experiments.db` | (in-memory or CONFIGS_DIR) | `experiments` | `optimizer.ExperimentStore` |
| `event_log.db` | (in-memory or CONFIGS_DIR) | `events` | `data.EventLog` |

Additional SQLite tables created by:
- `judges.GraderVersionStore` — `grader_versions`
- `judges.HumanFeedbackStore` — `human_feedback`
- `graders.CalibrationTracker` — `calibration_records`
- `observer.OpportunityQueue` — `opportunities`
- `optimizer.DeadLetterQueue` — `dead_letters`
- `optimizer.CostTracker` — `cycle_costs`

**File-Based State:**
- `configs/` — YAML agent configurations (versioned with `manifest.json`)
- `configs/manifest.json` — Version manifest (active/canary pointers)
- `loop_checkpoint.json` — Loop resume state
- `human_control.json` — Pause/pin/reject state

### 2.5 API Architecture

FastAPI application (`api/server.py`, 325 lines) with:
- **Lifespan management**: Initializes all stores, managers, and eval runner at startup
- **State injection**: All dependencies attached to `app.state` for route access
- **18 route modules** in `api/routes/` providing 82 endpoints
- **Background tasks**: `TaskManager` with thread-safe task tracking
- **WebSocket**: `ConnectionManager` for real-time progress updates
- **SPA serving**: Static file serving with HTML5 history fallback
- **Middleware**: Structured JSON logging via `JsonFormatter`

### 2.6 Frontend Architecture

React + TypeScript + Vite application:
- **Router**: React Router with 19 page routes
- **State**: Zustand for toast notifications; React hooks for local state
- **API Client**: `web/src/lib/api.ts` (~800 lines) wrapping all 82 endpoints
- **Types**: `web/src/lib/types.ts` (~400 lines) with 50+ TypeScript interfaces
- **WebSocket**: `web/src/lib/websocket.ts` for real-time loop monitoring
- **Components**: 29 reusable components (data tables, score visualizations, YAML viewers, diff viewers, charts)
- **Layout**: Sidebar navigation with collapsible menu + command palette (Ctrl+K)

### 2.7 CLI Architecture

Click-based CLI (`runner.py`, 2,223 lines):
- **10 command groups**: `eval`, `config`, `autofix`, `judges`, `context`, `registry`, `trace`, `scorer`, `run` (hidden)
- **32 leaf commands** + 10 group entry points = 42 total
- **Shared infrastructure**: Config loading, score formatting, failure sampling, runtime component building
- **Environment variables**: 5 configurable paths (`AUTOAGENT_DB`, `AUTOAGENT_CONFIGS`, `AUTOAGENT_MEMORY_DB`, `AUTOAGENT_REGISTRY_DB`, `AUTOAGENT_TRACE_DB`)

---

## 3. Feature Inventory

### 3a. Core Optimization Loop

**What it does:** Continuously observes agent conversations, diagnoses failures, proposes configuration mutations, evaluates them, and deploys improvements.

**How it works:**
1. **Observe**: Pull recent conversations from `ConversationStore`, classify failures via `FailureClassifier` into buckets (routing_error, unhelpful_response, timeout, tool_failure, safety_violation)
2. **Diagnose**: Rank failures by severity and frequency; build context for proposer
3. **Propose**: `Proposer` (mock-deterministic or LLM-based) generates a `Proposal` targeting a specific `config_section` with a config patch
4. **Evaluate**: `EvalRunner` scores the proposed config against baseline using the eval suite
5. **Gate**: `Gates.evaluate()` runs 4 checks — safety (hard), improvement (soft), regression (soft), constraints (hard)
6. **Record**: Results stored in `ExperimentStore` as an `ExperimentCard` and `OptimizationMemory`
7. **Deploy**: If accepted, config saved via `ConfigVersionManager`, optionally canary-deployed via `CanaryManager`
8. **Learn**: Bandit selector updates arm statistics; curriculum scheduler adjusts difficulty tier

**Key classes:**
- `optimizer.loop.Optimizer` — `optimizer/loop.py` — Main loop orchestrator
- `optimizer.proposer.Proposer` — `optimizer/proposer.py` (286 lines) — Generates proposals
- `optimizer.gates.Gates` — `optimizer/gates.py` (102 lines) — 4-stage gating
- `optimizer.search.SearchStrategy` — `optimizer/search.py` — Strategy selection (SIMPLE/ADAPTIVE/FULL/PRO)
- `optimizer.bandit.BanditSelector` — `optimizer/bandit.py` (171 lines) — UCB1/Thompson bandit
- `optimizer.curriculum.CurriculumScheduler` — `optimizer/curriculum.py` (190 lines) — Difficulty progression

**CLI commands:**
```bash
autoagent optimize --cycles 5            # Run N optimization cycles
autoagent loop --max-cycles 50           # Continuous optimization loop
autoagent loop --schedule cron --cron "0 */6 * * *"  # Cron-scheduled
autoagent loop --stop-on-plateau         # Stop when improvement stalls
autoagent loop --resume                  # Resume from checkpoint
```

**API endpoints:**
- `POST /api/optimize/run` — Start single optimization (202 Accepted)
- `GET /api/optimize/history` — List optimization attempts
- `GET /api/optimize/history/{attempt_id}` — Get specific attempt
- `GET /api/optimize/pareto` — Get Pareto frontier snapshot
- `POST /api/loop/start` — Start continuous loop (202 Accepted)
- `POST /api/loop/stop` — Stop running loop
- `GET /api/loop/status` — Loop status with cycle history

**Web pages:**
- `Optimize.tsx` (281 lines) — Single optimization cycle trigger with diagnostics
- `LoopMonitor.tsx` (222 lines) — Continuous loop status, cycle history, heartbeat

**Test coverage:**
- `test_optimizer.py` — 7 tests (loop orchestration)
- `test_search.py` — 24 tests (strategy selection, operator family mapping)
- `test_adaptive_search.py` — 21 tests (adaptive strategy behavior)
- `test_bandit.py` — 18 tests (UCB1, Thompson sampling)
- `test_curriculum.py` — 27 tests (difficulty tiers, advancement)
- `test_pro_strategy.py` — 22 tests (pro-mode routing)

**Limitations:**
- LLM proposer requires live API key; mock proposer uses heuristic rules
- No multi-objective optimization in SIMPLE strategy (single composite score)
- Curriculum scheduler requires manual tier advancement threshold tuning

---

### 3b. Typed Mutations & Experiment Cards

**What it does:** Every configuration change is a typed mutation with risk classification, rollback strategy, and full audit trail via experiment cards.

**How it works:**

**Mutation System:**
- 14 mutation surfaces defined in `MutationSurface` enum: instruction, few_shot, tool_description, model, generation_settings, callback, context_caching, memory_policy, routing, workflow, skill, policy, tool_contract, handoff_schema
- 4 risk classes: `low` < `medium` < `high` < `critical` (with comparison operators)
- Each `MutationOperator` has: name, surface, risk_class, preconditions, validator, rollback_strategy, estimated_eval_cost, supports_autodeploy, apply function
- 9 built-in operators + 3 Google stubs (zero-shot, few-shot, data-driven) + 3 topology stubs

**Experiment Cards:**
- `ExperimentCard` dataclass (34 fields) captures complete audit trail: hypothesis, touched surfaces/agents, diff, baseline/candidate SHA, scores, significance, cost, status
- Stored in SQLite via `ExperimentStore`
- Valid statuses: pending → running → accepted/rejected/expired

**Key classes:**
- `optimizer.mutations.MutationOperator` — `optimizer/mutations.py` — Operator definition
- `optimizer.mutations.MutationRegistry` — `optimizer/mutations.py` — Global operator registry
- `optimizer.mutations.RiskClass` — `optimizer/mutations.py` — Risk enum with ordering
- `optimizer.experiments.ExperimentCard` — `optimizer/experiments.py` (240 lines) — Full audit record
- `optimizer.experiments.ExperimentStore` — `optimizer/experiments.py` — SQLite persistence

**CLI commands:**
```bash
autoagent status        # Shows recent experiments and their outcomes
```

**API endpoints:**
- `GET /api/experiments` — List recent experiments
- `GET /api/experiments/stats` — Experiment statistics
- `GET /api/experiments/archive` — Elite Pareto archive
- `GET /api/experiments/{experiment_id}` — Specific experiment detail
- `GET /api/experiments/judge-calibration` — Judge calibration for experiments

**Web pages:**
- `Experiments.tsx` (120 lines) — Experiment cards with status, Pareto archive view

**Test coverage:**
- `test_experiments.py` — 5 tests
- `test_mutations.py` — 11 tests
- `test_core_types.py` — 56 tests (includes CandidateVariant, ArchiveEntry)

**Limitations:**
- Google mutation operators are stubs (`ready=False`) — require Vertex AI integration
- Topology operators are stubs (`supports_autodeploy=False`) — require agent graph runtime

---

### 3c. 4-Layer Metric Hierarchy & Scoring

**What it does:** Structures all evaluation metrics into 4 layers with different gating behavior, enabling nuanced optimization decisions.

**How it works:**

**Layer definitions:**
1. **HARD_GATE** — Binary pass/fail. Any failure = immediate rejection. (safety_score, format_compliance)
2. **OUTCOME** — North-star business metrics. Must improve. (task_completion_rate, user_satisfaction)
3. **SLO** — Operating SLOs. Must not regress beyond threshold. (latency_p95_ms, cost_per_conversation)
4. **DIAGNOSTIC** — Informational only. No gating. (tool_selection_accuracy, routing_precision)

**Metric registry** (`core/types.py:729-752`):
```python
METRIC_REGISTRY = [
    LayeredMetric("safety_score", MetricLayer.HARD_GATE, "maximize", 1.0, 1.0),
    LayeredMetric("format_compliance", MetricLayer.HARD_GATE, "maximize", 0.95, 0.8),
    LayeredMetric("task_completion_rate", MetricLayer.OUTCOME, "maximize", 0.80, 1.0),
    LayeredMetric("user_satisfaction", MetricLayer.OUTCOME, "maximize", 0.70, 0.8),
    LayeredMetric("latency_p95_ms", MetricLayer.SLO, "minimize", 5000, 0.6),
    LayeredMetric("cost_per_conversation", MetricLayer.SLO, "minimize", 0.50, 0.5),
    LayeredMetric("tool_selection_accuracy", MetricLayer.DIAGNOSTIC, "maximize", None, 0.3),
    LayeredMetric("routing_precision", MetricLayer.DIAGNOSTIC, "maximize", None, 0.3),
]
```

**Scoring pipeline** (`evals/scorer.py`):
- `DimensionScores` — 9-dimensional score vector: quality, safety, groundedness, tool_use, latency, cost, coherence, completeness, routing
- `CompositeScorer` — Weighted aggregation with configurable weights
- `EvalResult` — Per-case evaluation with dimension breakdown

**Key classes:**
- `core.types.MetricLayer` — `core/types.py:698-703` — Layer enum
- `core.types.LayeredMetric` — `core/types.py:706-722` — Metric definition
- `core.types.METRIC_REGISTRY` — `core/types.py:729-752` — Canonical metric list
- `evals.scorer.DimensionScores` — `evals/scorer.py` — 9D score vector
- `evals.scorer.CompositeScorer` — `evals/scorer.py` — Weighted aggregation

**Test coverage:**
- `test_layered_scorer.py` — 14 tests
- `test_scoring_v2.py` — 5 tests
- `test_enhanced_scorer.py` — 13 tests
- `test_core_types.py` — 56 tests (metric layer behavior)

---

### 3d. Judge Subsystem

**What it does:** Multi-layer evaluation pipeline that grades agent outputs through deterministic checks, rule-based validation, LLM assessment, and audit logging.

**How it works:**

5-layer judge pipeline (ordered by cost/reliability):
1. **DeterministicJudge** (`judges/deterministic.py`, 122 lines) — Regex matching, state verification, invariant checking. Zero cost, instant, deterministic.
2. **RuleBasedJudge** (`judges/rule_based.py`, 109 lines) — Format validation (JSON, markdown, length constraints), required field checking.
3. **LLMJudge** (`judges/llm_judge.py`, 209 lines) — Token overlap scoring, heuristic quality assessment, evidence extraction. Falls back to heuristics when no LLM available.
4. **AuditJudge** (`judges/audit_judge.py`, 81 lines) — Cross-validates earlier judges, flags disagreements.
5. **GraderStack** (`judges/grader_stack.py`, 210 lines) — Orchestrates grader execution, aggregates results.

**Key classes:**
- `judges.DeterministicJudge` — 3 check types: regex, state, invariant
- `judges.RuleBasedJudge` — Format validation with configurable rules
- `judges.LLMJudge` — Overlap + heuristic scoring with evidence extraction
- `judges.AuditJudge` — Cross-validation of prior judge results
- `judges.GraderStack` — Ordered execution with aggregation

**API endpoints:**
- `GET /api/judges` — List active judges and versions
- `POST /api/judges/feedback` — Submit human feedback
- `GET /api/judges/calibration` — Calibration metrics
- `GET /api/judges/drift` — Drift detection results

**Test coverage:**
- `test_judges.py` — 37 tests (all judge types, edge cases)
- `test_judge_variance.py` — 14 tests (variance estimation)

---

### 3e. Grader Stack

**What it does:** Simplified grading pipeline for individual eval cases, separate from the judge subsystem.

**How it works:**

Three grader types:
1. **DeterministicGrader** (`graders/deterministic.py`, 72 lines) — Keyword matching, regex validation, length checks. Returns `GradeResult` with pass/fail and evidence.
2. **SimilarityGrader** (`graders/similarity.py`, 36 lines) — Token overlap similarity score (0.0-1.0) against reference answers.
3. **BinaryRubricJudge** (`graders/llm_judge.py`, 128 lines) — 4-question rubric evaluation with majority voting. Questions: helpfulness, accuracy, completeness, safety.

`GraderStack` (`graders/stack.py`, 80 lines) — Chains graders with weighted combination into `StackGrade`.

`CalibrationTracker` (`graders/calibration.py`, 83 lines) — Tracks grader agreement rate and drift over time.

**Key classes:**
- `graders.GradeResult` — `graders/deterministic.py:10-17` — Dataclass with score, passed, evidence, metadata
- `graders.StackGrade` — `graders/stack.py:14-21` — Composite grade with per-grader breakdown
- `graders.BinaryRubricJudge` — `graders/llm_judge.py:20-128` — 4-question rubric with heuristic fallback

**Test coverage:**
- `test_graders.py` — 6 tests

---

### 3f. AutoFix Copilot

**What it does:** Analyzes failure patterns and generates targeted fix proposals that respect human control constraints.

**How it works:**

6-stage pipeline:
1. **Failure analysis**: Cluster conversations by error pattern (10 categories: timeout, rate_limit, context_length, hallucination, refusal, format_error, tool_error, safety, off_topic, incomplete)
2. **Pattern matching**: `FailurePatternProposer` identifies dominant failure clusters
3. **Proposal generation**: Creates `AutoFixProposal` with mutation name, surface, params, expected lift, risk class, diff preview
4. **Human review**: Proposals enter "proposed" status; require human approval
5. **Application**: On approval, patch applied to config, evaluated via `EvalRunner`
6. **Tracking**: `AutoFixHistoryEntry` records baseline/candidate scores, significance, canary verdict

**Key classes:**
- `optimizer.autofix.AutoFixProposal` — `optimizer/autofix.py:17-73` — 14-field proposal dataclass
- `optimizer.autofix.AutoFixHistoryEntry` — `optimizer/autofix.py:76-90` — Deployment history record
- `optimizer.autofix_proposers.FailurePatternProposer` — `optimizer/autofix_proposers.py` — Pattern-based proposal generation
- `optimizer.autofix.AutoFixStore` — SQLite-backed proposal and history storage

**CLI commands:**
```bash
autoagent autofix suggest              # Generate proposals from failure patterns
autoagent autofix apply <proposal_id>  # Apply a proposal
autoagent autofix history              # View application history
```

**API endpoints:**
- `POST /api/autofix/suggest` — Generate proposals
- `GET /api/autofix/proposals` — List proposals
- `POST /api/autofix/apply/{proposal_id}` — Apply proposal
- `GET /api/autofix/history` — Application history

**Web page:** `AutoFix.tsx` (170 lines) — Proposal interface with suggestion, review, and application

**Test coverage:**
- `test_autofix.py` — 39 tests (proposal generation, application, history, edge cases)

---

### 3g. Judge Ops

**What it does:** Versioned judge/grader management with drift monitoring, human feedback integration, and calibration analysis.

**How it works:**

**Versioning** (`judges/versioning.py`, 190 lines):
- `GraderVersionStore` tracks immutable versions of every grader configuration
- Each version: grader_name, version number, config hash, created_at, deprecated flag
- Supports: `save_version()`, `get_version()`, `list_versions()`, `get_latest()`, `diff_versions()`

**Drift Monitoring** (`judges/drift_monitor.py`, 193 lines):
- `DriftMonitor` checks: agreement drift, position bias, verbosity bias
- Produces `DriftAlert` dataclass with severity, details, metric values
- Configurable thresholds for alert triggering

**Human Feedback** (`judges/human_feedback.py`, 176 lines):
- `HumanFeedbackStore` records human corrections to judge outputs
- Tracks agreement rates between human and automated judges
- Identifies systematic disagreements via `disagreements()` method
- Samples cases for review via `sample_for_review()`

**Calibration** (`judges/calibration.py`, 147 lines):
- `JudgeCalibrationSuite` computes: agreement_rate, position_bias, verbosity_bias, disagreement_rate, drift over time
- Records human judgments paired with automated outputs

**CLI commands:**
```bash
autoagent judges list                  # List active judges and versions
autoagent judges calibrate             # Run calibration analysis
autoagent judges drift                 # Check for drift alerts
```

**API endpoints:**
- `GET /api/judges` — List judges
- `POST /api/judges/feedback` — Submit human feedback
- `GET /api/judges/calibration` — Calibration metrics
- `GET /api/judges/drift` — Drift detection results

**Web page:** `JudgeOps.tsx` (232 lines) — Versioning, agreement rates, drift monitoring, calibration

**Test coverage:**
- `test_judge_ops.py` — 38 tests (versioning, drift, feedback, calibration)

---

### 3h. Context Engineering Workbench

**What it does:** Analyzes how agents use their context window and simulates compaction strategies to reduce failures.

**How it works:**

**ContextAnalyzer** (`context/analyzer.py`, 273 lines):
- Analyzes traces for: token utilization over turns, growth patterns (linear, exponential, sawtooth, stable), failure correlations with context usage, handoff fidelity
- Produces `ContextAnalysis` with per-turn utilization, growth pattern, failure-context correlation coefficient

**CompactionSimulator** (`context/simulator.py`, 168 lines):
- Simulates 3 strategies: aggressive (50% target, 60% trigger), balanced (70% target, 80% trigger), conservative (85% target, 95% trigger)
- Estimates token savings, compaction loss, failure delta
- `compare_strategies()` runs all strategies for comparison

**ContextMetrics** (`context/metrics.py`, 74 lines):
- Static methods: `utilization_ratio()`, `compaction_loss_score()`, `handoff_fidelity()`, `memory_staleness()`, `aggregate_report()`

**CLI commands:**
```bash
autoagent context analyze <trace_id>   # Analyze a trace's context usage
autoagent context simulate             # Simulate compaction strategies
autoagent context report               # Generate context health report
```

**API endpoints:**
- `GET /api/context/analysis/{trace_id}` — Trace context analysis
- `POST /api/context/simulate` — Run compaction simulation
- `GET /api/context/report` — Context health report

**Web page:** `ContextWorkbench.tsx` (301 lines) — Trace analysis, compaction simulation, strategy comparison

**Test coverage:**
- `test_context.py` — 50 tests (analyzer, simulator, metrics, edge cases)

---

### 3i. Pro-Mode Prompt Optimization

**What it does:** Four research-grade prompt optimization algorithms for when standard heuristic-based optimization plateaus.

**How it works:**

**Algorithm Selection** (`optimizer/prompt_opt/strategy.py`, 82 lines):
- `ProSearchStrategy._select_algorithm()`:
  - Explicit: honors user's algorithm choice
  - Auto + budget < $1.0: `BOOTSTRAP_FEWSHOT` (cheapest)
  - Auto + budget >= $1.0: `MIPROV2` (best general-purpose)

**1. MIPROv2** (`optimizer/prompt_opt/mipro.py`, 294 lines):
- Multi-prompt Instruction Proposal and Optimization v2
- Uses Bayesian surrogate model with kNN-based UCB acquisition
- Generates N instruction candidates via LLM meta-prompting
- Bootstraps M few-shot example sets from training cases
- Searches (instruction_idx, example_set_idx) space
- Early stops after 3 rounds without improvement
- Best for: general optimization with sufficient budget

**2. BootstrapFewShot** (`optimizer/prompt_opt/bootstrap_fewshot.py`, 241 lines):
- DSPy-inspired greedy few-shot selection
- Teacher model generates high-quality demonstrations
- Scores individual examples, ranks by quality
- Tries increasing subset sizes (k=1 to max_k)
- Best for: low budget, when examples are valuable

**3. GEPA** (`optimizer/prompt_opt/gepa.py`, 302 lines):
- Gradient-free Evolutionary Prompt Adaptation
- Maintains population of instruction candidates
- Tournament selection → LLM crossover → LLM mutation → fitness evaluation → weakest replacement
- Best for: exploring diverse prompt space

**4. SIMBA** (`optimizer/prompt_opt/simba.py`, 214 lines):
- Simulation-Based prompt optimization (hill-climbing)
- Generates N variants per round, keeps top-k as seeds
- Iterative refinement across R rounds
- Best for: quick local improvement when near optimum

**Surrogate Model** (`optimizer/prompt_opt/surrogate.py`, 107 lines):
- `BayesianSurrogate`: kNN-based surrogate for MIPROv2
- UCB acquisition: estimated_score + exploration_weight / sqrt(1 + n_similar)
- Similarity: 1.0 (exact match), 0.5 (partial), 0.0 (no match)

**Configuration:**
```yaml
optimizer:
  search_strategy: pro
  pro_config:
    algorithm: auto      # auto, miprov2, bootstrap_fewshot, gepa, simba
    instruction_candidates: 5
    example_candidates: 3
    max_eval_rounds: 10
    budget_dollars: 10.0
```

**CLI commands:**
```bash
autoagent optimize --search-strategy pro --pro-algorithm miprov2
autoagent optimize --search-strategy pro --pro-budget 5.0
```

**Test coverage:**
- `test_mipro.py` — 32 tests (surrogate, UCB, instruction generation, bootstrap)
- `test_bootstrap_fewshot.py` — 15 tests (teacher generation, subset selection)
- `test_gepa.py` — 10 tests (population, crossover, mutation, selection)
- `test_simba.py` — 10 tests (perturbation, hill-climbing, budget checks)
- `test_pro_strategy.py` — 22 tests (algorithm selection, routing, budget handling)

---

### 3j. Modular Registry

**What it does:** Versioned registry for agent components — skills, policies, tool contracts, and handoff schemas — with immutable history, diff, search, and bulk import.

**How it works:**

**RegistryStore** (`registry/store.py`, 185 lines):
- SQLite-backed storage with 4 tables
- Immutable versioning: every update creates a new version
- Operations: insert, get (with version), list, deprecate, search (text), diff (between versions)

**Four registry types:**
1. **SkillRegistry** (`registry/skills.py`, 88 lines) — Agent capabilities with instructions, scripts, validators. Export support.
2. **PolicyRegistry** (`registry/policies.py`, 75 lines) — Safety rules, guardrail thresholds, authorization policies.
3. **ToolContractRegistry** (`registry/tool_contracts.py`, 83 lines) — Tool schemas with side-effect classes, replay modes. Tracks which agents use which tools.
4. **HandoffSchemaRegistry** (`registry/handoff_schemas.py`, 104 lines) — Handoff schemas with validation against `HandoffArtifact` structure.

**Importer** (`registry/importer.py`, 122 lines):
- `import_from_file()` supports YAML and JSON
- Bulk import with type-specific field mapping
- Returns per-item success/failure results

**CLI commands:**
```bash
autoagent registry list skills          # List all skills
autoagent registry show skills my_skill # Show specific skill (latest version)
autoagent registry add skills --name my_skill --data '{"instructions":"..."}'
autoagent registry diff skills my_skill --v1 1 --v2 2  # Diff versions
autoagent registry import skills.yaml   # Bulk import
```

**API endpoints:**
- `GET /api/registry/{type}` — List items of type
- `POST /api/registry/{type}` — Create new item
- `GET /api/registry/{type}/{name}` — Get item (optionally with version)
- `GET /api/registry/{type}/{name}/diff` — Diff two versions
- `GET /api/registry/search` — Text search across all types
- `POST /api/registry/import` — Bulk import from YAML/JSON

**Web page:** `Registry.tsx` (258 lines) — CRUD interface for all 4 registry types

**Test coverage:**
- `test_registry.py` — 60 tests (all CRUD, versioning, search, import, deprecation)
- `test_tool_contracts.py` — 16 tests (agent usage tracking, validation)

---

### 3k. Trace Grading & Blame Map

**What it does:** Grades individual spans within agent traces (routing decisions, tool selections, handoffs) and clusters failures into a blame map identifying high-impact surfaces.

**How it works:**

**Trace Grading** (`observer/trace_grading.py`, ~500 lines):
- 7 span-level graders:
  - `RoutingGrader` — Was the routing decision correct?
  - `ToolSelectionGrader` — Was the right tool selected?
  - `ToolArgumentGrader` — Were tool arguments correct?
  - `RetrievalQualityGrader` — Was retrieved context relevant?
  - `HandoffQualityGrader` — Was the handoff complete?
  - `MemoryUseGrader` — Was memory used effectively?
  - `FinalOutcomeGrader` — Did the overall outcome succeed?
- Each produces `SpanGrade` with score, passed, evidence, grader_id

**Trace Graph** (`observer/trace_graph.py`, 192 lines):
- `TraceGraph`: DAG of `TraceGraphNode` and `TraceGraphEdge`
- `from_spans()`: Build graph from span data
- `get_critical_path()`: Identify longest execution path
- `get_root_nodes()`, `get_children()`: Graph traversal

**Blame Map** (`observer/blame_map.py`, 188 lines):
- `BlameMap.compute()`: Clusters failed grades by (grader_id, surface)
- `BlameCluster`: count, total_score, avg_score, trend (increasing/decreasing/stable), examples
- `identify_high_impact_surfaces()`: Ranks surfaces by failure frequency × severity

**CLI commands:**
```bash
autoagent trace grade <trace_id>       # Grade all spans in a trace
autoagent trace blame                  # Compute blame map across recent traces
autoagent trace graph <trace_id>       # Visualize trace graph
```

**API endpoints:**
- `GET /api/traces/{trace_id}/grades` — Span-level grades
- `GET /api/traces/{trace_id}/graph` — Trace graph
- `GET /api/traces/blame` — Blame map summary
- `GET /api/traces/recent` — Recent traces
- `GET /api/traces/search` — Search traces
- `GET /api/traces/errors` — Error traces
- `GET /api/traces/sessions/{session_id}` — Session traces
- `GET /api/traces/{trace_id}` — Full trace detail

**Web pages:**
- `Traces.tsx` (166 lines) — Trace search, timeline visualization
- `BlameMap.tsx` (186 lines) — Failure cluster analysis

**Test coverage:**
- `test_trace_grading.py` — 61 tests (all 7 graders, blame map, clustering)
- `test_traces.py` — 6 tests (trace store operations)
- `test_tracing.py` — 22 tests (tracing middleware)

---

### 3l. NL Scorer Generation

**What it does:** Compiles natural language descriptions of evaluation criteria into structured scorer specifications with weighted dimensions.

**How it works:**

**NLCompiler** (`evals/nl_compiler.py`):
- Parses NL descriptions using 14+ regex patterns
- Detects dimension keywords: accuracy, completeness, helpfulness, safety, relevance, coherence, conciseness, format, latency, cost, creativity, engagement, professionalism, empathy
- Assigns weights based on emphasis cues ("most important", "critical", ordinal position)
- Produces `ScorerSpec` with name, description, and list of `ScorerDimension`

**ScorerSpec** (`evals/scorer_spec.py`):
- `ScorerDimension`: name, weight, description, rubric_items
- `ScorerSpec`: name, description, dimensions, version, created_at
- Methods: `to_dict()`, `from_dict()`, `to_yaml()`, `refine()` (merge new dimensions)

**NLScorer** (`evals/nl_scorer.py`):
- Entry point: `create()`, `refine()`, `test_scorer()`
- Stores specs in JSON on disk
- `test_scorer()` evaluates spec against sample inputs

**CLI commands:**
```bash
autoagent scorer create "Accuracy is most important, followed by completeness and safety"
autoagent scorer list
autoagent scorer show my_scorer
autoagent scorer refine my_scorer "Also consider latency"
autoagent scorer test my_scorer --input '{"response": "..."}'
```

**API endpoints:**
- `POST /api/scorers/create` — Create scorer from NL
- `GET /api/scorers` — List scorers
- `GET /api/scorers/{name}` — Get scorer spec
- `POST /api/scorers/{name}/refine` — Refine with additional NL
- `POST /api/scorers/{name}/test` — Test scorer against input

**Web page:** `ScorerStudio.tsx` (384 lines) — NL-to-scorer compiler with generation, refinement, testing

**Test coverage:**
- `test_nl_scorer.py` — 59 tests (compilation, weighting, refinement, edge cases)
- `test_eval_compiler.py` — 21 tests (NL compilation pipeline)

---

### 3m. Anti-Goodhart Guards

**What it does:** Prevents the optimizer from gaming metrics by maintaining holdout sets, detecting drift, and estimating judge variance.

**How it works:**

**1. Holdout Manager** (`optimizer/holdout.py:42-166`, 125 lines):
- Splits eval cases into tuning (60%), validation (20%), holdout (20%) using deterministic hash bucketing
- Optimizer only sees tuning scores; holdout scores are hidden
- Rotation: every N experiments (default 10), holdout cases rotate to prevent memorization
- Drift detection: compares early vs recent experiments on holdout; flags if gap > threshold (0.03)

**2. Judge Variance Estimator** (`optimizer/holdout.py:185-247`, 63 lines):
- Records multiple judge scores for same input
- Estimates mean, variance, confidence interval per metric
- `is_score_meaningful()`: true if improvement > 2 × confidence interval width

**3. Anti-Goodhart Integration** (`evals/anti_goodhart.py`):
- Coordinates holdout, drift, and variance into unified anti-Goodhart pipeline
- Applied at eval time to flag suspicious improvements

**CLI commands:**
```bash
autoagent doctor  # Includes anti-Goodhart health check
```

**Test coverage:**
- `test_holdout.py` — 20 tests (split creation, rotation, drift detection)
- `test_anti_goodhart_integration.py` — 31 tests (full pipeline integration)
- `test_judge_variance.py` — 14 tests (variance estimation, significance)

---

### 3n. Human Escape Hatches & Cost Controls

**What it does:** Allows humans to pause optimization, freeze specific config surfaces, reject experiments, and enforce budget limits.

**How it works:**

**Human Control** (`optimizer/human_control.py`, 101 lines):
- `HumanControlState`: paused (bool), immutable_surfaces (set), rejected_experiments (set), last_injected_mutation, updated_at
- JSON-backed persistence
- Operations: pause/resume, pin/unpin surfaces, reject experiments, inject mutations

**Cost Controls** (`optimizer/cost_tracker.py`, 191 lines):
- `CostTracker`: per-cycle and daily budget enforcement
- `can_start_cycle()`: checks both budgets before proceeding
- `should_pause_for_stall()`: detects N consecutive cycles without improvement
- Records: cycle_id, spent_dollars, improvement_delta, timestamp

**CLI commands:**
```bash
autoagent pause                        # Pause optimization
autoagent resume                       # Resume optimization
autoagent pin routing                  # Freeze routing surface
autoagent unpin routing                # Unfreeze routing surface
autoagent reject <experiment_id>       # Reject a specific experiment
```

**API endpoints:**
- `GET /api/control/state` — Current human control state
- `POST /api/control/pause` — Pause
- `POST /api/control/resume` — Resume
- `POST /api/control/pin/{surface}` — Pin surface
- `POST /api/control/unpin/{surface}` — Unpin surface
- `POST /api/control/reject/{experiment_id}` — Reject experiment
- `POST /api/control/inject` — Inject manual mutation

**Test coverage:**
- `test_human_control.py` — 25 tests (all operations, state persistence)
- `test_cost_tracker.py` — 27 tests (budgets, stall detection)
- `test_cli_control.py` — 24 tests (CLI commands for human control)

---

### 3o. Deployment & Canary Management

**What it does:** Manages versioned configuration deployment with canary rollout, promotion gating, and rollback.

**How it works:**

**Config Versioning** (`deployer/versioning.py`, 152 lines):
- `ConfigVersionManager`: Saves configs as YAML files with monotonic version numbers
- Manifest tracking: active version, canary version, history
- Operations: save_version, promote, rollback, get_active_config, get_canary_config

**Canary Deployment** (`deployer/canary.py`, 169 lines):
- `CanaryManager`: Routes traffic fraction to canary config
- `should_use_canary()`: Probabilistic routing based on canary percentage (default 10%)
- `check_canary()`: Evaluates canary against baseline using eval runner
- `execute_verdict()`: Promotes or rolls back based on results

**Release Pipeline** (`deployer/release_manager.py`, 300 lines):
- `ReleaseManager.run_full_pipeline()`: Full promotion pipeline
  1. Start promotion (create record)
  2. Check gates (safety, improvement, regression, constraints)
  3. Check holdout (anti-Goodhart)
  4. Check slices (per-category breakdown)
  5. Start canary (deploy at low traffic)
  6. Complete promotion (promote to active)
- 8 promotion stages: pending → gates_check → holdout_check → slice_check → canary_running → promoted / rolled_back / aborted

**CLI commands:**
```bash
autoagent deploy --config-version 5 --strategy canary
autoagent deploy --strategy immediate
```

**API endpoints:**
- `POST /api/deploy` — Deploy config version
- `GET /api/deploy/status` — Current deployment status
- `POST /api/deploy/rollback` — Rollback canary

**Web page:** `Deploy.tsx` (265 lines) — Deployment interface with strategy selection, status, rollback

**Test coverage:**
- `test_deployer.py` — 4 tests (versioning, canary basics)
- `test_release_manager.py` — 11 tests (full pipeline, gate checking, rollback)

---

### 3p. Event Logging & Observability

**What it does:** Append-only event log, health metrics computation, anomaly detection, and failure classification.

**How it works:**

**Event Log** (`data/event_log.py`, 141 lines):
- 27 valid event types including: optimization_started, experiment_accepted, experiment_rejected, safety_gate_failed, canary_deployed, config_promoted, human_pause, human_resume, surface_pinned, budget_exceeded, etc.
- SQLite-backed, append-only
- Query by type, time range, limit

**Health Metrics** (`observer/metrics.py`, 57 lines):
- `HealthMetrics`: success_rate, safety_rate, avg_latency_ms, p95_latency_ms, total_conversations
- `compute_metrics()`: Aggregates from conversation records

**Anomaly Detection** (`observer/anomaly.py`, 86 lines):
- `AnomalyDetector`: Z-score based anomaly detection against historical baselines
- `Baseline`: mean and standard deviation per metric
- Configurable threshold (default: 2 standard deviations)

**Failure Classification** (`observer/classifier.py`, 78 lines):
- `FailureClassifier`: Maps failures into 5 buckets with routing hints
- Buckets: routing_error, unhelpful_response, timeout, tool_failure, safety_violation
- Routing hints map buckets to optimization targets

**Opportunity Queue** (`observer/opportunities.py`, ~370 lines):
- `OpportunityQueue`: Priority queue of optimization opportunities
- Ranked by severity × frequency
- Statuses: open → in_progress → resolved / dismissed

**CLI commands:**
```bash
autoagent status    # Shows health metrics, anomaly detection
autoagent logs      # Shows recent optimization events
autoagent doctor    # Comprehensive system diagnostics
```

**API endpoints:**
- `GET /api/health` — Health metrics
- `GET /api/health/ready` — Readiness check
- `GET /api/health/system` — System health
- `GET /api/health/cost` — Cost tracking
- `GET /api/health/eval-set` — Eval set health
- `GET /api/health/scorecard` — Full scorecard
- `GET /api/events` — Event log
- `GET /api/opportunities` — Opportunity queue
- `GET /api/opportunities/count` — Open opportunity count
- `GET /api/opportunities/{id}` — Specific opportunity
- `POST /api/opportunities/{id}/status` — Update opportunity status

**Web pages:**
- `Dashboard.tsx` (403 lines) — Main dashboard with health metrics, failure buckets, Pareto frontier
- `EventLog.tsx` (66 lines) — Event log viewer
- `Opportunities.tsx` (73 lines) — Opportunity queue

**Test coverage:**
- `test_observer.py` — 4 tests
- `test_event_log.py` — 24 tests
- `test_opportunities.py` — 6 tests

---

## 4. Technical Deep Dives

### 4.1 Search Strategy Comparison

| Strategy | Algorithm | When to Use | Cost | Exploration | Implementation |
|----------|-----------|------------|------|-------------|---------------|
| **SIMPLE** | Single proposal → eval → gate | First-time setup, low budget | Low | None | `optimizer/loop.py` |
| **ADAPTIVE** | Bandit-selected operator → eval → gate → update arms | Steady-state optimization | Medium | UCB1/Thompson | `optimizer/bandit.py` |
| **FULL** | Multi-hypothesis + Pareto + curriculum + anti-Goodhart | Production optimization at scale | High | Pareto exploration | `optimizer/search.py`, `optimizer/pareto.py` |
| **PRO** | MIPROv2/Bootstrap/GEPA/SIMBA | Prompt plateau, research-grade optimization | Highest | Algorithm-dependent | `optimizer/prompt_opt/` |

**SIMPLE strategy:** The proposer generates one proposal. Eval runner scores it. Gates check it. If accepted, deploy.

**ADAPTIVE strategy:** The `BanditSelector` (`optimizer/bandit.py:44-170`) maintains arms for each (operator, failure_family) pair. Selection:
- **UCB1**: `mean_reward + exploration_weight × sqrt(log(total_pulls) / arm_pulls)` — exploitation-exploration tradeoff
- **Thompson**: Samples from `Beta(successes + 1, failures + 1)` — Bayesian exploration

After each cycle, `record_outcome()` updates arm statistics. The scheduler advances difficulty tiers (easy → medium → hard) when improvement stalls.

**FULL strategy:** Combines adaptive bandit selection with:
- `ParetoArchive` for multi-objective tracking
- `CurriculumScheduler` for difficulty-based case filtering
- `HoldoutManager` for anti-Goodhart protection
- `GovernanceEngine` for deployment gating
- `StructuredCritique` for judge aggregation

**PRO strategy:** Delegates to `ProSearchStrategy` which routes to one of 4 algorithms (see Section 4.2-4.4).

### 4.2 Bayesian Surrogate Model in MIPROv2

MIPROv2 (`optimizer/prompt_opt/mipro.py`) uses a surrogate model to efficiently search the joint (instruction, example_set) space.

**Surrogate architecture** (`optimizer/prompt_opt/surrogate.py`):

```
Observations: [(candidate_1, score_1), (candidate_2, score_2), ...]

suggest(untried_candidates):
  for each candidate:
    estimated = weighted_kNN(candidate, observations, k=5)
    n_similar = count of similar observations
    ucb = estimated + exploration_weight / sqrt(1 + n_similar)
  return argmax(ucb)
```

**kNN estimation:**
- Distance metric: 1.0 if both (instruction_idx, example_set_idx) match; 0.5 if one matches; 0.0 if neither
- Top-k neighbors weighted by similarity
- Estimated score = Σ(similarity_i × score_i) / Σ(similarity_i)

**UCB acquisition:**
- `UCB(c) = estimated_score(c) + exploration_weight / sqrt(1 + n_similar(c))`
- Exploration bonus decreases as more similar candidates are observed
- Default exploration_weight = 1.0

**Early stopping:**
- Patience = 3 rounds
- If no improvement for 3 consecutive rounds, stop
- Prevents wasteful evaluations once a good candidate is found

### 4.3 GEPA Evolutionary Algorithm

GEPA (`optimizer/prompt_opt/gepa.py`) is a gradient-free evolutionary algorithm for prompt optimization.

**Population dynamics:**
```
Initialize: P members from seed + LLM-generated variants (temperature=0.9)
For G generations:
  1. Tournament Selection: pick 2 random members → return fitter
     parent_a = tournament_select(population, fitness)
     parent_b = tournament_select(population, fitness)

  2. Crossover: LLM merges two parents (temperature=0.8)
     "Merge the best elements of these two prompts:
      Prompt A: {parent_a}
      Prompt B: {parent_b}"

  3. Mutation: LLM perturbs offspring (temperature=0.9)
     "Slightly modify this prompt to improve it:
      {offspring}"

  4. Evaluation: EvalRunner scores offspring

  5. Replacement: If offspring score > worst population score,
     replace weakest member
```

**Parameters:**
- Population size: 6 (default)
- Generations: 5 (default)
- Tournament size: 2 (fixed)
- Crossover rate: 1.0 (every generation produces an offspring)
- Mutation rate: 1.0 (every offspring is mutated)

### 4.4 Statistical Significance Gating

**Paired Bootstrap Test** (`evals/statistics.py`):

```
Given: baseline_scores[i] and candidate_scores[i] for i in 1..N

For b in 1..B bootstrap iterations:
  resample indices with replacement
  compute delta = mean(candidate[resampled]) - mean(baseline[resampled])

p_value = fraction of deltas <= 0

Significant if:
  - p_value < alpha (default 0.05)
  - abs(mean_delta) >= min_effect_size (default 0.01)
```

**Sequential Testing** (in FULL strategy):
- Accumulates evidence across cycles
- Stops early when significance is clear
- Uses Holm-Bonferroni correction for multiple comparisons across dimensions

**Gates Integration** (`optimizer/gates.py:8-101`):
1. `check_safety()` — Any safety metric failure → reject (hard gate)
2. `check_improvement()` — Composite score must improve (soft gate)
3. `check_regression()` — No individual metric drops > threshold (soft gate)
4. `check_constraints()` — All constraints from config must pass (hard gate)

### 4.5 Pareto Archive and Constrained Optimization

Three Pareto archive implementations (`optimizer/pareto.py`, 522 lines):

**1. ParetoArchive (basic):**
- Maintains non-dominated set
- `dominates(a, b)`: a is better on all objectives
- `recommend()`: Maximin knee-point selection (maximize minimum normalized objective)
- Size-limited with eviction of dominated candidates

**2. ConstrainedParetoArchive:**
- Direction-aware (MAXIMIZE/MINIMIZE per objective)
- Normalizes objectives to [0, 1] range
- `recommend_knee_point()`: Minimizes distance to ideal point in normalized space
- Feasibility filtering: only candidates passing all constraints enter the frontier

**3. EliteParetoArchive:**
- Role-based archive extending ConstrainedParetoArchive
- 6 roles: quality_leader, cost_leader, latency_leader, safety_leader, incumbent, cluster_specialist
- `assign_roles()`: Each role assigned to the candidate maximizing the corresponding objective
- `get_branch_candidates()`: Returns candidates suitable for branching new experiments

### 4.6 Trace Graph Model and Span-Level Grading

**Trace Graph** (`observer/trace_graph.py`):
```
TraceGraphNode:
  - node_id, agent_name, operation, start_time, end_time
  - duration_ms (computed property)

TraceGraphEdge:
  - source_id, target_id, edge_type (calls, delegates, returns)

TraceGraph:
  - from_spans(spans) → builds DAG
  - get_critical_path() → longest weighted path (by duration)
  - get_root_nodes() → entry points
```

**Span-Level Grading Pipeline:**
```
For each span in trace:
  1. Classify span type (routing, tool_call, handoff, etc.)
  2. Select appropriate grader(s)
  3. Grade span → SpanGrade(score, passed, evidence, grader_id)
  4. Aggregate: trace_score = weighted_mean(span_grades)

Blame Map:
  5. Group failed grades by (grader_id, surface)
  6. Compute cluster statistics (count, avg_score, trend)
  7. Rank by impact = count × (1 - avg_score)
```

### 4.7 NL-to-Rubric Compilation Pipeline

**NLCompiler** (`evals/nl_compiler.py`):

```
Input: "Accuracy is the most important metric. Completeness and safety are also critical."

Step 1: Dimension Detection (14 regex patterns)
  - "accuracy" → accuracy dimension
  - "completeness" → completeness dimension
  - "safety" → safety dimension

Step 2: Weight Assignment
  - "most important" modifier on accuracy → weight 1.0
  - "critical" modifier on completeness, safety → weight 0.8
  - Normalize weights to sum to 1.0

Step 3: Rubric Generation
  - Each dimension gets default rubric items:
    accuracy: [exact_match, factual_consistency, source_attribution]
    completeness: [all_parts_addressed, sufficient_detail, no_gaps]
    safety: [no_harmful_content, appropriate_boundaries, ethical_compliance]

Output: ScorerSpec(
  name="custom_scorer",
  dimensions=[
    ScorerDimension("accuracy", 0.385, "...", [...]),
    ScorerDimension("completeness", 0.308, "...", [...]),
    ScorerDimension("safety", 0.308, "...", [...])
  ]
)
```

**Refinement:** `ScorerSpec.refine()` merges new dimensions into existing spec, updating weights and rubric items for overlapping dimensions.

---

## 5. API & CLI Complete Reference

### 5.1 CLI Commands

#### Core Commands

| Command | Flags | Default | Description |
|---------|-------|---------|-------------|
| `init` | `--template`, `--dir` | customer-support, . | Bootstrap new project |
| `server` | `--host`, `--port` | 0.0.0.0, 8000 | Start API server |
| `status` | `--db`, `--configs-dir`, `--memory-db` | env vars | System status overview |
| `doctor` | `--config` | autoagent.yaml | Diagnostic health check |
| `logs` | `--limit`, `--outcome`, `--db` | 20, all | Recent optimization logs |

#### Eval Group

| Command | Flags | Default | Description |
|---------|-------|---------|-------------|
| `eval run` | `--config`, `--suite`, `--dataset`, `--split`, `--category`, `--output` | autoagent.yaml, all | Run evaluation suite |
| `eval results` | `--run-id`, `--file` | latest | Display eval results |
| `eval list` | | | List recent eval runs |

#### Optimization

| Command | Flags | Default | Description |
|---------|-------|---------|-------------|
| `optimize` | `--cycles`, `--db`, `--configs-dir`, `--memory-db` | 1 | Run N optimization cycles |
| `loop` | `--max-cycles`, `--stop-on-plateau`, `--delay`, `--schedule`, `--interval-minutes`, `--cron`, `--checkpoint-file`, `--resume` | 50, false, 1.0, continuous | Continuous optimization |

#### Config Group

| Command | Flags | Default | Description |
|---------|-------|---------|-------------|
| `config list` | | | List saved versions |
| `config show` | `[version]` | active | Show config YAML |
| `config diff` | `<v1> <v2>` | | Diff two versions |

#### Deploy

| Command | Flags | Default | Description |
|---------|-------|---------|-------------|
| `deploy` | `--config-version`, `--strategy`, `--configs-dir`, `--db` | latest, canary | Deploy configuration |

#### Human Control

| Command | Flags | Description |
|---------|-------|-------------|
| `pause` | | Pause optimization |
| `resume` | | Resume optimization |
| `pin` | `<surface>` | Freeze config surface |
| `unpin` | `<surface>` | Unfreeze surface |
| `reject` | `<experiment_id>`, `--configs-dir`, `--db` | Reject experiment |

#### AutoFix Group

| Command | Flags | Description |
|---------|-------|-------------|
| `autofix suggest` | | Generate fix proposals |
| `autofix apply` | `<proposal_id>` | Apply a proposal |
| `autofix history` | | View history |

#### Judges Group

| Command | Flags | Description |
|---------|-------|-------------|
| `judges list` | | List active judges |
| `judges calibrate` | | Run calibration |
| `judges drift` | | Check drift |

#### Context Group

| Command | Flags | Description |
|---------|-------|-------------|
| `context analyze` | `<trace_id>` | Analyze trace context |
| `context simulate` | | Simulate compaction |
| `context report` | | Context health report |

#### Registry Group

| Command | Flags | Description |
|---------|-------|-------------|
| `registry list` | `<type>` | List items |
| `registry show` | `<type> <name>` | Show item |
| `registry add` | `<type> --name --data` | Create item |
| `registry diff` | `<type> <name> --v1 --v2` | Diff versions |
| `registry import` | `<file>` | Bulk import |

#### Trace Group

| Command | Flags | Description |
|---------|-------|-------------|
| `trace grade` | `<trace_id>` | Grade trace spans |
| `trace blame` | | Compute blame map |
| `trace graph` | `<trace_id>` | Visualize trace graph |

#### Scorer Group

| Command | Flags | Description |
|---------|-------|-------------|
| `scorer create` | `<description>` | Create from NL |
| `scorer list` | | List scorers |
| `scorer show` | `<name>` | Show scorer spec |
| `scorer refine` | `<name> <description>` | Refine scorer |
| `scorer test` | `<name> --input` | Test scorer |

### 5.2 API Endpoints (82 total)

#### Health (6 endpoints)

| Method | Path | Response |
|--------|------|----------|
| GET | `/api/health/ready` | `{"status": "ok"}` |
| GET | `/api/health` | `HealthResponse` (metrics, report) |
| GET | `/api/health/system` | `SystemHealthResponse` (uptime, memory, CPU) |
| GET | `/api/health/cost` | Cost tracking data |
| GET | `/api/health/eval-set` | Eval set health |
| GET | `/api/health/scorecard` | Full scorecard with dimensions |

#### Eval (6 endpoints)

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/api/eval/run` | `EvalRunRequest` | 202 + task_id |
| GET | `/api/eval/runs` | | `[EvalRunResponse]` |
| GET | `/api/eval/runs/{run_id}` | | `EvalRunResponse` |
| GET | `/api/eval/runs/{run_id}/cases` | | `[EvalCaseResult]` |
| GET | `/api/eval/history` | | `[EvalResultsResponse]` |
| GET | `/api/eval/history/{run_id}` | | `EvalResultsResponse` |

#### Optimize (4 endpoints)

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/api/optimize/run` | `OptimizeRequest` | 202 + task_id |
| GET | `/api/optimize/history` | | `[OptimizationAttempt]` |
| GET | `/api/optimize/history/{attempt_id}` | | `OptimizationAttempt` |
| GET | `/api/optimize/pareto` | | Pareto frontier snapshot |

#### Loop (3 endpoints)

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/api/loop/start` | `LoopStartRequest` | 202 + task_id |
| POST | `/api/loop/stop` | | `{"status": "stopped"}` |
| GET | `/api/loop/status` | | `LoopStatusResponse` |

#### Control (7 endpoints)

| Method | Path | Response |
|--------|------|----------|
| GET | `/api/control/state` | Human control state |
| POST | `/api/control/pause` | Paused confirmation |
| POST | `/api/control/resume` | Resumed confirmation |
| POST | `/api/control/pin/{surface}` | Pinned confirmation |
| POST | `/api/control/unpin/{surface}` | Unpinned confirmation |
| POST | `/api/control/reject/{experiment_id}` | Rejected confirmation |
| POST | `/api/control/inject` | Injected mutation details |

#### Deploy (3 endpoints)

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/api/deploy` | `DeployRequest` | `DeployResponse` |
| GET | `/api/deploy/status` | | `DeployStatusResponse` |
| POST | `/api/deploy/rollback` | | Rollback confirmation |

#### Config (4 endpoints)

| Method | Path | Response |
|--------|------|----------|
| GET | `/api/config/list` | `ConfigListResponse` |
| GET | `/api/config/show/{version}` | `ConfigShowResponse` |
| GET | `/api/config/diff` | `ConfigDiffResponse` |
| GET | `/api/config/active` | Active config YAML |

#### Conversations (3 endpoints)

| Method | Path | Response |
|--------|------|----------|
| GET | `/api/conversations/stats` | `ConversationStatsResponse` |
| GET | `/api/conversations` | `ConversationListResponse` |
| GET | `/api/conversations/{id}` | `ConversationRecord` |

#### Traces (8 endpoints)

| Method | Path | Response |
|--------|------|----------|
| GET | `/api/traces/recent` | Recent traces list |
| GET | `/api/traces/search` | Filtered traces |
| GET | `/api/traces/errors` | Error traces |
| GET | `/api/traces/sessions/{session_id}` | Session traces |
| GET | `/api/traces/blame` | Blame map |
| GET | `/api/traces/{trace_id}/grades` | Span grades |
| GET | `/api/traces/{trace_id}/graph` | Trace graph |
| GET | `/api/traces/{trace_id}` | Full trace |

#### Experiments (5 endpoints)

| Method | Path | Response |
|--------|------|----------|
| GET | `/api/experiments/stats` | Stats summary |
| GET | `/api/experiments` | Recent experiments |
| GET | `/api/experiments/archive` | Elite Pareto archive |
| GET | `/api/experiments/judge-calibration` | Calibration data |
| GET | `/api/experiments/{experiment_id}` | Experiment detail |

#### Opportunities (4 endpoints)

| Method | Path | Response |
|--------|------|----------|
| GET | `/api/opportunities/count` | Open count |
| GET | `/api/opportunities` | Opportunity list |
| GET | `/api/opportunities/{id}` | Opportunity detail |
| POST | `/api/opportunities/{id}/status` | Updated status |

#### AutoFix (4 endpoints)

| Method | Path | Response |
|--------|------|----------|
| POST | `/api/autofix/suggest` | Proposals generated |
| GET | `/api/autofix/proposals` | Proposal list |
| POST | `/api/autofix/apply/{id}` | Application result |
| GET | `/api/autofix/history` | History entries |

#### Judges (4 endpoints)

| Method | Path | Response |
|--------|------|----------|
| GET | `/api/judges` | Judge list |
| POST | `/api/judges/feedback` | Recorded confirmation |
| GET | `/api/judges/calibration` | Calibration data |
| GET | `/api/judges/drift` | Drift alerts |

#### Scorers (5 endpoints)

| Method | Path | Response |
|--------|------|----------|
| POST | `/api/scorers/create` | Created scorer spec |
| GET | `/api/scorers` | Scorer list |
| GET | `/api/scorers/{name}` | Scorer spec |
| POST | `/api/scorers/{name}/refine` | Refined spec |
| POST | `/api/scorers/{name}/test` | Test results |

#### Context (3 endpoints)

| Method | Path | Response |
|--------|------|----------|
| GET | `/api/context/analysis/{trace_id}` | Context analysis |
| POST | `/api/context/simulate` | Simulation results |
| GET | `/api/context/report` | Health report |

#### Registry (6 endpoints)

| Method | Path | Response |
|--------|------|----------|
| GET | `/api/registry/search` | Search results |
| POST | `/api/registry/import` | Import results |
| GET | `/api/registry/{type}` | Item list |
| GET | `/api/registry/{type}/{name}` | Item detail |
| GET | `/api/registry/{type}/{name}/diff` | Version diff |
| POST | `/api/registry/{type}` | Created item |

#### Events (1 endpoint)

| Method | Path | Response |
|--------|------|----------|
| GET | `/api/events` | Event list |

#### WebSocket (1 endpoint)

| Protocol | Path | Description |
|----------|------|-------------|
| WS | `/ws` | Real-time progress updates |

#### Server-level (6 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Root redirect to SPA |
| GET | `/api/tasks/{task_id}` | Background task status |
| GET | `/api/tasks` | List background tasks |
| GET | `/app` | Serve SPA root |
| GET | `/app/{path}` | SPA catch-all (HTML5 history) |
| WS | `/ws` | WebSocket endpoint |

---

## 6. Test Architecture

### 6.1 Organization

All tests live in `tests/` (flat directory, no subdirectories).

**59 test files | 1,203 test functions | 19,060 lines**

**Conventions:**
- File naming: `test_{module_name}.py`
- Function naming: `def test_{behavior}__{scenario}()` or `def test_{behavior}()`
- Fixtures: `conftest.py` provides shared fixtures (tmp directories, mock stores, sample data)
- Helpers: `helpers.py` provides test utility functions

### 6.2 Test Count by Feature Area

| Feature Area | Test Files | Test Count |
|--------------|-----------|------------|
| **Core types & domain** | test_core_types.py | 56 |
| **Merge / integration** | test_merge_modules.py | 69 |
| **Trace grading** | test_trace_grading.py | 61 |
| **Registry** | test_registry.py, test_tool_contracts.py | 76 |
| **NL scorer** | test_nl_scorer.py, test_eval_compiler.py | 80 |
| **Context** | test_context.py | 50 |
| **AutoFix** | test_autofix.py | 39 |
| **API** | test_api.py, test_api_new_features.py, test_api_control_events.py | 89 |
| **Judge ops** | test_judge_ops.py, test_judges.py, test_judge_variance.py | 89 |
| **Pro-mode** | test_mipro.py, test_bootstrap_fewshot.py, test_gepa.py, test_simba.py, test_pro_strategy.py | 89 |
| **Anti-Goodhart** | test_anti_goodhart_integration.py, test_holdout.py | 51 |
| **Search & bandit** | test_search.py, test_adaptive_search.py, test_bandit.py | 63 |
| **CLI** | test_cli_commands.py, test_cli_control.py | 48 |
| **Human control & cost** | test_human_control.py, test_cost_tracker.py | 52 |
| **Curriculum** | test_curriculum.py | 27 |
| **Event log** | test_event_log.py | 24 |
| **Tracing** | test_tracing.py, test_traces.py | 28 |
| **Other** | remaining files | ~112 |

### 6.3 Mock Patterns

- **Mock LLM Provider**: `optimizer.providers.MockProvider` returns deterministic responses based on keyword matching. Used throughout tests.
- **Mock Proposer**: `optimizer.proposer.Proposer._mock_propose()` provides deterministic heuristic-based proposals without LLM calls.
- **In-memory databases**: SQLite `:memory:` databases used in tests via `tmp_path` fixtures.
- **Temporary directories**: `pytest` `tmp_path` fixture for config files, checkpoints, and state.
- **Eval fixtures**: `evals.fixtures.mock_data` provides sample eval cases and scores.

### 6.4 Running Tests

```bash
# All tests
pytest tests/

# Specific module
pytest tests/test_judges.py

# Specific test
pytest tests/test_judges.py::test_deterministic_judge_regex

# By keyword
pytest -k "goodhart"

# With coverage
pytest --cov=. tests/

# Parallel (if pytest-xdist installed)
pytest -n auto tests/
```

---

## 7. Deployment Architecture

### 7.1 Container Image

**Dockerfile** (69 lines, multi-stage build):

```
Stage 1: node:20-slim
  - Build React frontend with Vite
  - Output: /app/web/dist/

Stage 2: python:3.11-slim
  - Install Python dependencies
  - Copy built frontend
  - Create non-root user (appuser)
  - Health check: curl localhost:8000/api/health/ready
  - Expose: 8000
  - CMD: uvicorn api.server:app --host 0.0.0.0 --port 8000
```

### 7.2 Cloud Run Configuration

**deploy/cloud-run-service.yaml** (49 lines):
- Container: 512Mi memory, 1 CPU
- Min instances: 0, Max instances: 10
- Liveness probe: `/api/health/ready`
- Startup probe: `/api/health/ready` (30s initial delay)
- Environment variables: GOOGLE_API_KEY (from Secret Manager), LOG_LEVEL, PYTHONUNBUFFERED

**deploy/cloudbuild.yaml** (47 lines):
- Step 1: Docker build → Artifact Registry push
- Step 2: Cloud Run deploy with `--allow-unauthenticated`

**deploy/deploy.sh** (61 lines):
- One-command GCP deployment
- Creates Artifact Registry repo if needed
- Builds and pushes Docker image
- Deploys to Cloud Run

### 7.3 Alternative Platforms

**Fly.io** (`deploy/fly.toml`, 31 lines):
- Auto-scaling: min_machines_running = 0
- Health check: `/api/health/ready` every 10s
- Volume mount for persistent data

**Railway** (`deploy/railway.toml`, 11 lines):
- Dockerfile builder
- Start command: uvicorn

### 7.4 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | One API key required | — | Google Gemini API key |
| `OPENAI_API_KEY` | One API key required | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | One API key required | — | Anthropic API key |
| `AUTOAGENT_DB` | No | conversations.db | Conversation store path |
| `AUTOAGENT_CONFIGS` | No | configs | Config directory path |
| `AUTOAGENT_MEMORY_DB` | No | optimizer_memory.db | Optimizer memory path |
| `AUTOAGENT_REGISTRY_DB` | No | registry.db | Registry store path |
| `AUTOAGENT_TRACE_DB` | No | traces.db | Trace store path |
| `AUTOAGENT_EVAL_HISTORY_DB` | No | eval_history.db | Eval history path |
| `HOST` | No | 0.0.0.0 | API server host |
| `PORT` | No | 8000 | API server port |
| `LOG_LEVEL` | No | INFO | Logging level |

### 7.5 Database Considerations

**Current state:** SQLite for all persistence. Simple, zero-config, but:
- Single-writer limitation (no concurrent write scaling)
- File-based (ephemeral on Cloud Run without volume mounts)
- No built-in replication

**Migration path to Postgres:**
- All stores use `sqlite3` module directly (no ORM)
- `data/repositories.py` defines `TraceRepository` and `ArtifactRepository` protocols
- Migration requires: protocol implementations for Postgres, connection pooling, schema migration scripts
- Estimated effort: 2-3 weeks for a senior engineer

### 7.6 Scaling Characteristics

- **Vertical**: Single-process; benefits from more CPU/memory up to ~4 vCPU / 2 GB
- **Horizontal**: Not currently supported (SQLite file locking). Requires Postgres migration.
- **API**: FastAPI async handlers; good for I/O-bound workloads
- **WebSocket**: Single-instance broadcast; would need Redis pub/sub for multi-instance
- **Background tasks**: In-process threading; not distributed. Would need Celery/CloudTasks for scale.

---

## 8. Research Lineage

### 8.1 Version Evolution

| Version | Codename | Key Innovation | Lines | Tests |
|---------|----------|---------------|-------|-------|
| v1 | — | Basic prompt optimization loop | ~5K | ~50 |
| v2 | — | Typed mutations, experiment cards, trace engine | ~15K | ~200 |
| v3 | — | 9-dimension evaluation, Pareto archive, hybrid search | ~25K | ~500 |
| v5 | — | Judge subsystem, 4-layer metrics, release manager, v4 research port | ~35K | ~800 |
| VNext | — | AutoFix, Judge Ops, Context Workbench, pro-mode | ~42K | ~950 |
| VNextCC | Current | Modular registry, trace grading, NL scorer, production deployment | ~55K | 1,203 |

### 8.2 Key Research Inputs

**CI/CD-for-Agents Thesis:**
The foundational insight that agent optimization should follow the same rigor as software deployment: eval suites as test suites, statistical gating as CI checks, canary deployment as staged rollout, rollback as revert. This maps directly to the `EvalRunner → Gates → Deployer → CanaryManager` pipeline.

**Radical Simplicity Thesis:**
The counterbalancing force: every feature must justify its complexity. This led to the deterministic mock proposer (no LLM needed for basic optimization), SQLite over Postgres (sufficient for single-machine), flat test directory (no test hierarchy), and the deliberate absence of an ORM.

### 8.3 Academic References

**DSPy / MIPROv2:**
- Khattab et al., "DSPy: Compiling Declarative Language Model Calls into State-of-the-Art Pipelines" (2023)
- MIPROv2 implementation adapted for agent config optimization (not just prompt optimization)
- Key adaptation: surrogate operates over (instruction, example_set) pairs rather than arbitrary program parameters

**Anti-Goodhart / Metric Gaming:**
- Goodhart's Law: "When a measure becomes a target, it ceases to be a good measure"
- Implementation: holdout rotation (optimizer never sees holdout scores), drift detection (early vs recent baseline comparison), judge variance estimation (confidence intervals on improvements)
- Novel: three-mechanism defense integrated into the optimization loop rather than post-hoc auditing

**Evolutionary Prompt Optimization:**
- GEPA draws from evolutionary strategies (tournament selection, crossover, mutation)
- Key adaptation: LLM-based genetic operators (crossover = "merge these two prompts", mutation = "slightly modify this prompt")
- Novel: fitness function is a composite eval score rather than a single metric

**Bandit-Based Operator Selection:**
- UCB1 (Auer et al., 2002) and Thompson Sampling (Thompson, 1933) for selecting which mutation operator to apply
- Novel: arms are (operator, failure_family) pairs, allowing the system to learn which operators work best for which failure types

### 8.4 Novel Contributions

1. **Typed mutation registry with risk classification** — No prior system classifies prompt/config changes by risk class and gates deployment accordingly
2. **Multi-layer metric hierarchy** — Hard gates vs outcomes vs SLOs vs diagnostics is novel for agent optimization
3. **Experiment cards as audit trail** — 34-field audit records for every optimization attempt
4. **Span-level trace grading with blame map** — Grading individual agent decisions (routing, tool selection) rather than just final output
5. **NL-to-scorer compilation** — Converting natural language evaluation criteria to structured scorer specs
6. **Budget-aware algorithm selection** — Pro-mode routes to cheaper algorithms when budget is limited
7. **Curriculum-based optimization scheduling** — Easy → medium → hard progression for eval cases

---

## 9. Gaps, Risks, and Roadmap Candidates

### 9.1 Known Architectural Limitations

| Limitation | Impact | Severity |
|-----------|--------|----------|
| SQLite single-writer | Cannot scale horizontally | High |
| In-process background tasks | Tasks lost on crash; no distribution | Medium |
| No authentication/authorization | Any client can mutate state | Critical |
| No multi-tenancy | Single-user, single-agent assumption | High |
| WebSocket single-instance | No cross-instance broadcast | Medium |
| File-based config state | Ephemeral on serverless platforms | High |

### 9.2 Features That Are Stubs or Incomplete

| Feature | Status | Location | Notes |
|---------|--------|----------|-------|
| Google Vertex AI operators | Stub (`ready=False`) | `optimizer/mutations_google.py` | 3 operators: zero-shot, few-shot, data-driven |
| Topology mutation operators | Stub (`supports_autodeploy=False`) | `optimizer/mutations_topology.py` | 3 operators: loop detection, parallelism reduction, deterministic steps |
| Vertex Prompt Optimizer | Stub | `optimizer/autofix_vertex.py` | `is_available` returns False |
| Training escalation | Logic complete, no training runtime | `optimizer/training_escalation.py` | Recommends SFT/DPO/RFT but can't execute |
| ADK agent runtime | Reference implementation only | `agent/` | Demo customer-support agent, not production |

### 9.3 Scalability Concerns

- **Database**: SQLite locks on write. At >100 concurrent conversations, write contention will bottleneck. Postgres migration is the clear path.
- **Eval runs**: Currently synchronous within loop cycle. Long eval suites block the optimization loop. Need async eval with result polling.
- **LLM API calls**: Rate limiter is per-provider, single-process. No distributed rate limiting.
- **Trace storage**: Unbounded growth. No TTL or archival policy.
- **Pareto archive**: In-memory. Lost on restart unless serialized to checkpoint.

### 9.4 Security Gaps

| Gap | Risk | Mitigation Path |
|-----|------|-----------------|
| No API authentication | Anyone with network access can modify agent config | Add OAuth2/API key middleware |
| No RBAC | No distinction between read-only and admin | Add role-based access control |
| No input validation on inject endpoint | Arbitrary mutation injection | Add schema validation |
| No audit log for API mutations | No accountability for config changes | Event log partially covers this |
| SQLite files world-readable | Data exposure on shared hosts | File permissions + encryption at rest |
| No CORS restriction in dev | Cross-origin requests possible | Configure allowed origins |

### 9.5 Integration Opportunities

| Integration | Value | Effort |
|-------------|-------|--------|
| **CX Agent Studio** | Direct optimization of production CX agents | Medium (API adapter) |
| **Vertex AI** | Enable Google mutation operators, model garden | Medium (complete stubs) |
| **Cloud SQL** | Replace SQLite for production scalability | Medium (protocol implementations) |
| **Cloud Tasks / Pub/Sub** | Distributed background task execution | Medium |
| **BigQuery** | Long-term analytics on optimization history | Low (export pipeline) |
| **Datadog / Cloud Monitoring** | Production observability integration | Low (metrics export) |
| **Git-backed config** | Version control for config changes | Low (git commit on save) |
| **Slack / PagerDuty** | Alert on safety violations, drift, budget exceeded | Low (webhook integration) |

### 9.6 Suggested Roadmap

#### P0 — Must Have for Production

| Item | Effort | Rationale |
|------|--------|-----------|
| API authentication (OAuth2/API keys) | 1-2 weeks | Security: unauthenticated API is a blocker |
| Postgres migration | 2-3 weeks | Scalability: SQLite won't handle production load |
| Distributed task execution | 2-3 weeks | Reliability: in-process tasks lost on crash |
| CORS and input validation hardening | 1 week | Security: prevent injection and cross-origin attacks |
| Persistent Pareto archive | 1 week | Reliability: archive lost on restart |

#### P1 — Should Have for Scale

| Item | Effort | Rationale |
|------|--------|-----------|
| Multi-tenancy | 3-4 weeks | Multiple teams/agents sharing one instance |
| Complete Vertex AI operators | 2-3 weeks | Enable Google-native prompt optimization |
| Async eval execution | 2 weeks | Unblock optimization loop during long evals |
| Trace TTL and archival | 1 week | Prevent unbounded storage growth |
| WebSocket scaling (Redis pub/sub) | 1 week | Multi-instance real-time updates |
| Monitoring integration (Cloud Monitoring) | 1 week | Production observability |

#### P2 — Nice to Have

| Item | Effort | Rationale |
|------|--------|-----------|
| Git-backed config versioning | 1 week | Familiar version control for config |
| CX Agent Studio integration | 2-3 weeks | Direct production agent optimization |
| Training execution runtime | 4-6 weeks | Execute SFT/DPO/RFT recommendations |
| Topology mutation execution | 3-4 weeks | Automated agent graph restructuring |
| A/B testing framework | 2-3 weeks | Real traffic comparison (beyond canary) |
| Plugin system for custom graders | 2 weeks | Extensibility for domain-specific evaluation |
| Dashboard role-based views | 1-2 weeks | Different views for different personas |
| Batch import/export for experiments | 1 week | Cross-instance experiment sharing |

---

## Appendix A: File Index

### Python Source Files by Package

**core/** (3 files, 1,079 lines)
- `core/__init__.py` (33 lines)
- `core/types.py` (902 lines)
- `core/handoff.py` (147 lines)

**data/** (3 files, 242 lines)
- `data/__init__.py` (1 line)
- `data/repositories.py` (102 lines)
- `data/event_log.py` (141 lines)

**control/** (2 files, 35 lines)
- `control/__init__.py` (1 line)
- `control/governance.py` (34 lines)

**logger/** (4 files, 337 lines)
- `logger/__init__.py` (6 lines)
- `logger/structured.py` (69 lines)
- `logger/middleware.py` (96 lines)
- `logger/store.py` (170 lines)

**observer/** (9 files, 2,052 lines)
- `observer/__init__.py` (57 lines)
- `observer/metrics.py` (57 lines)
- `observer/classifier.py` (78 lines)
- `observer/anomaly.py` (86 lines)
- `observer/opportunities.py` (~370 lines)
- `observer/traces.py` (~520 lines)
- `observer/trace_grading.py` (~500 lines)
- `observer/trace_graph.py` (192 lines)
- `observer/blame_map.py` (188 lines)

**graders/** (6 files, 412 lines)
- `graders/__init__.py` (19 lines)
- `graders/deterministic.py` (72 lines)
- `graders/similarity.py` (36 lines)
- `graders/llm_judge.py` (128 lines)
- `graders/calibration.py` (83 lines)
- `graders/stack.py` (80 lines)

**judges/** (10 files, 1,450 lines)
- `judges/__init__.py` (23 lines)
- `judges/deterministic.py` (122 lines)
- `judges/rule_based.py` (109 lines)
- `judges/llm_judge.py` (209 lines)
- `judges/audit_judge.py` (81 lines)
- `judges/grader_stack.py` (210 lines)
- `judges/calibration.py` (147 lines)
- `judges/versioning.py` (190 lines)
- `judges/drift_monitor.py` (193 lines)
- `judges/human_feedback.py` (176 lines)

**evals/** (13+ files, 4,555 lines)
- `evals/scorer.py`, `evals/scorer_spec.py`, `evals/nl_compiler.py`, `evals/nl_scorer.py`
- `evals/runner.py`, `evals/statistics.py`, `evals/anti_goodhart.py`
- `evals/history.py`, `evals/data_engine.py`, `evals/replay.py`, `evals/side_effects.py`
- `evals/fixtures/mock_data.py`

**context/** (4 files, 517 lines)
- `context/__init__.py` (6 lines)
- `context/analyzer.py` (273 lines)
- `context/metrics.py` (74 lines)
- `context/simulator.py` (168 lines)

**registry/** (7 files, 669 lines)
- `registry/__init__.py` (19 lines)
- `registry/store.py` (185 lines)
- `registry/skills.py` (88 lines)
- `registry/policies.py` (75 lines)
- `registry/tool_contracts.py` (83 lines)
- `registry/handoff_schemas.py` (104 lines)
- `registry/importer.py` (122 lines)

**optimizer/** (22 files, 6,643 lines)
- `optimizer/loop.py`, `optimizer/proposer.py` (286 lines), `optimizer/gates.py` (102 lines)
- `optimizer/search.py`, `optimizer/mutations.py`, `optimizer/experiments.py` (240 lines)
- `optimizer/memory.py` (174 lines), `optimizer/bandit.py` (171 lines)
- `optimizer/pareto.py` (522 lines), `optimizer/holdout.py` (248 lines)
- `optimizer/providers.py` (480 lines), `optimizer/reliability.py` (325 lines)
- `optimizer/cost_tracker.py` (191 lines), `optimizer/curriculum.py` (190 lines)
- `optimizer/human_control.py` (101 lines), `optimizer/training_escalation.py` (174 lines)
- `optimizer/autofix.py`, `optimizer/autofix_proposers.py`, `optimizer/autofix_vertex.py` (29 lines)
- `optimizer/mutations_google.py` (164 lines), `optimizer/mutations_topology.py` (139 lines)

**optimizer/prompt_opt/** (8 files, 1,357 lines)
- `optimizer/prompt_opt/types.py` (102 lines)
- `optimizer/prompt_opt/mipro.py` (294 lines)
- `optimizer/prompt_opt/bootstrap_fewshot.py` (241 lines)
- `optimizer/prompt_opt/gepa.py` (302 lines)
- `optimizer/prompt_opt/simba.py` (214 lines)
- `optimizer/prompt_opt/strategy.py` (82 lines)
- `optimizer/prompt_opt/surrogate.py` (107 lines)

**deployer/** (4 files, 622 lines)
- `deployer/__init__.py` (5 lines)
- `deployer/versioning.py` (152 lines)
- `deployer/canary.py` (169 lines)
- `deployer/release_manager.py` (300 lines)

**agent/** (17 files, 921 lines)
- `agent/root_agent.py` (59 lines), `agent/server.py` (263 lines), `agent/tracing.py` (306 lines)
- `agent/dashboard_data.py` (~200 lines)
- `agent/config/schema.py` (155 lines), `agent/config/loader.py` (63 lines), `agent/config/runtime.py` (111 lines)
- `agent/tools/catalog.py` (~123 lines), `agent/tools/faq.py` (78 lines), `agent/tools/orders_db.py` (~137 lines)
- `agent/specialists/orders.py` (33 lines), `agent/specialists/recommendations.py` (30 lines), `agent/specialists/support.py` (33 lines)

**api/** (6 core files, 935 lines)
- `api/server.py` (325 lines), `api/models.py` (426 lines), `api/tasks.py` (131 lines), `api/websocket.py` (48 lines)

**api/routes/** (17 files, 2,453 lines)
- See Section 5.2 for endpoint details per file

**runner.py** (1 file, 2,223 lines)

---

*This document was generated on 2026-03-24 from a complete reading of every source file, test file, configuration, and documentation artifact in the AutoAgent VNextCC repository.*

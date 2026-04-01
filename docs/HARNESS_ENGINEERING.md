# Harness Engineering for AgentLab

Last updated: 2026-03-27

## Why this document exists

"Harness engineering" is the discipline of building the infrastructure around model calls so evaluations are trustworthy, reproducible, cost-aware, and fast enough to use continuously. This document captures:

- The external best practices we benchmarked against
- How AgentLab’s eval stack maps to those practices
- What was improved in this implementation pass
- How to design high-signal evals in this codebase

## External best-practice baseline

This pass synthesizes practices from:

- OpenAI harness engineering: https://openai.com/index/harness-engineering/
- OpenAI graders guide: https://developers.openai.com/api/docs/guides/graders
- Anthropic eval design guidance: https://platform.claude.com/docs/en/test-and-evaluate/develop-tests
- Anthropic robust evaluation design: https://www.anthropic.com/engineering/AI-resistant-technical-evaluations
- Google DeepMind evals: https://deepmind.google/research/evals/
- EleutherAI lm-evaluation-harness: https://github.com/EleutherAI/lm-evaluation-harness
- METR autonomy eval resources: https://evaluations.metr.org/
- Braintrust eval + annotation docs:
  - https://www.braintrust.dev/docs/evaluate/run-evaluations
  - https://www.braintrust.dev/docs/annotate/labels
- LangSmith evaluation quickstart: https://docs.langchain.com/langsmith/evaluation-quickstart
- W&B Weave evaluations: https://docs.wandb.ai/weave/guides/core-types/evaluations/

## Best-practice checklist

We used the following checklist for audit and implementation prioritization:

1. Dataset lifecycle and versioning
2. Dataset contamination/leakage controls
3. Deterministic split strategy
4. Reproducible run identity and provenance
5. Scoring stack design (deterministic + model judges + human loop)
6. Statistical rigor (confidence intervals, significance tests)
7. Regression/guardrail gating
8. Eval pipeline performance (cache reuse)
9. Cost-aware eval accounting
10. Debuggability (case-level traces/reasons)
11. Continuous evaluation and drift signals

## AgentLab eval architecture

### Core modules

- `evals/runner.py`
  - Loads test suites and datasets
  - Executes case-level evaluations
  - Produces `CompositeScore`
  - Persists run history/provenance
  - Now handles cache reuse, dataset integrity checks, and run fingerprints

- `evals/scorer.py`
  - Computes aggregate quality/safety/latency/cost/composite scores
  - Supports constrained and layered scoring modes
  - Now includes bootstrap confidence intervals and run token/cost metadata

- `evals/statistics.py`
  - Paired significance test
  - Clustered bootstrap and sequential testing
  - Multiple hypothesis correction
  - Power/sample-size and safety-bound utilities

- `evals/history.py`
  - Persistent run and case-level score history in SQLite

- `evals/data_engine.py`
  - Eval set management with set version hashes
  - Trace-to-eval conversion pipeline

- `evals/cache.py` (new)
  - Persistent cache for identical eval+config executions
  - Keyed by deterministic eval fingerprint

### Supporting modules

- `graders/` + `judges/`
  - Deterministic checks, similarity checks, LLM-judge stack
  - Judge calibration, drift monitoring, versioning, and human feedback loops

- `optimizer/holdout.py` + `evals/anti_goodhart.py`
  - Holdout rotation, anti-overfit controls, and regression guardrails

- `observer/`
  - Trace ingestion and analysis for eval debugging and failure diagnosis

## Gap analysis and outcomes

| Best Practice | Before | After |
|---|---|---|
| Eval dataset versioning | Present via `EvalSetManager` hash versioning | Unchanged (kept) |
| Contamination checks | Missing in eval execution path | Added duplicate-ID and cross-split contamination checks in `EvalRunner` |
| Deterministic run identity | Partial provenance only | Added config/dataset/case/eval fingerprints + seed metadata |
| Eval caching | Missing | Added SQLite eval cache with cache hit/miss provenance |
| Confidence intervals in outputs | Stats existed but not surfaced | Added bootstrap CIs for quality/safety/latency/cost/composite |
| Cost accounting at eval-run level | Token counts existed per case; no run-level estimate | Added `total_tokens` and `estimated_cost_usd` at run level |
| Runtime configurability of harness controls | Limited | Added runtime eval config for cache, integrity strictness, seed, and token pricing |

## Implemented changes

### 1) Deterministic eval caching

Files:
- `evals/cache.py`
- `evals/runner.py`

Behavior:
- Reuses prior results when eval inputs are identical (dataset, config, split/category, eval mode, seed, case set fingerprint, agent identity).
- Records provenance fields:
  - `eval_fingerprint`
  - `cache_key`
  - `cache_hit` (`true`/`false`)

Impact:
- Faster repeated eval runs
- Lower compute/cost overhead
- Better CI and local iteration throughput

### 2) Dataset integrity and contamination checks

Files:
- `evals/runner.py`

Behavior:
- Evaluates dataset rows for:
  - duplicate case IDs
  - cross-split duplicate prompts (train/test leakage)
  - canary marker presence signal
- Exposes findings in run provenance and warnings.
- Optional strict mode (`dataset_strict_integrity`) blocks execution on contamination.

Impact:
- Reduces false confidence from train/test leakage
- Makes dataset hygiene explicit at eval runtime

### 3) Confidence intervals on headline metrics

Files:
- `evals/scorer.py`

Behavior:
- `CompositeScorer` now computes bootstrap 95% confidence intervals for:
  - `quality`
  - `safety`
  - `latency`
  - `cost`
  - `composite`
- CIs are attached to `CompositeScore.confidence_intervals` and surfaced in CLI/API outputs.

Impact:
- Moves reporting from point estimates to uncertainty-aware estimates
- Supports safer promotion/gating decisions

### 4) Reproducibility and cost provenance

Files:
- `evals/runner.py`
- `evals/scorer.py`

Behavior:
- Adds run fingerprints and seed to provenance.
- Adds run-level:
  - `total_tokens`
  - `estimated_cost_usd` (from configurable per-1k token rate)

Impact:
- Easier run replay/comparison
- Transparent cost-quality tradeoff tracking

### 5) Runtime wiring and API surfacing

Files:
- `agent/config/runtime.py`
- `agentlab.yaml`
- `runner.py`
- `api/server.py`
- `api/routes/eval.py`
- `api/models.py`
- `mcp_server/tools.py`

Behavior:
- Eval runtime now supports:
  - `cache_enabled`
  - `cache_db_path`
  - `dataset_strict_integrity`
  - `random_seed`
  - `token_cost_per_1k`
- CLI/API/MCP instantiate `EvalRunner` with these controls.
- Eval responses now include CIs, token totals, estimated cost, and warnings.

## How to write high-signal evals in AgentLab

### 1) Use real task slices and explicit categories

For each case, set:
- `category`: (`happy_path`, `edge_case`, `safety`, `regression`, etc.)
- `expected_specialist`
- `expected_behavior`
- `expected_keywords`
- `expected_tool` when tool behavior matters

Why:
- Enables targeted regressions and scoped diagnostics
- Supports category-level analysis and guardrails

### 2) Keep splits deterministic and leakage-resistant

Guidelines:
- Prefer explicit `split` labels in source datasets.
- If missing, AgentLab uses deterministic split assignment from case ID hash.
- Avoid duplicate prompts crossing train/test boundaries.
- Use strict integrity mode for critical CI gates.

### 3) Treat metrics as a hierarchy

Recommended policy:
- Primary metric:
  - `composite` (or a layer-specific objective if using constrained modes)
- Secondary metrics:
  - `quality`, `latency`, `cost`, `tool_use_accuracy`
- Guardrails:
  - safety failures, P0 regression cases, holdout behavior, drift alerts

### 4) Log enough detail to debug failures quickly

AgentLab already stores case-level payloads and details. Keep detail strings informative:
- What was expected
- What was observed
- Which dimension failed (routing, tool use, safety, etc.)

### 5) Use confidence intervals for shipping decisions

Do not approve/deny based only on tiny point-estimate deltas.
Require improvement that is meaningful relative to uncertainty.

## Dataset management guidelines

Use this policy for eval data lifecycle:

- Source quality:
  - Prefer production-like traces and real failure examples.
- Versioning:
  - Treat set versions as artifacts; track hashes and metadata.
- Curation:
  - Preserve a balanced mix of happy-path and hard edge/safety cases.
- Leakage prevention:
  - Run contamination checks on every dataset run.
- Canarying:
  - Include canary markers for sensitive datasets that must never enter training corpora.

## Scoring and grading patterns

### Recommended stack in AgentLab

1. Deterministic graders first
2. Similarity/heuristic graders second
3. LLM-as-judge graders third
4. Human review on disagreement/borderline/high-risk slices

This mirrors industry patterns where deterministic checks anchor reliability and LLM judges cover semantic nuance.

## LLM judge vs rule-based grader

Use rule-based graders when:
- Ground truth is explicit and deterministic
- Failure should be binary and auditable
- You need low-latency, low-cost evals

Use LLM judges when:
- Quality is semantic or subjective
- There are multiple acceptable outputs
- You need nuanced scoring dimensions (tone, groundedness, relevance)

Use both when:
- You want robust hybrid scoring
- Deterministic checks catch hard failures
- LLM judges rank nuanced quality among acceptable outputs

Add human review when:
- Judge disagreement rises
- Drift/bias alerts trigger
- Decisions are high-impact (policy, safety, legal, healthcare, finance)

## Operational runbook

### CLI eval run

```bash
agentlab eval run --dataset path/to/eval.jsonl --split test --output results.json
```

### Runtime eval controls (`agentlab.yaml`)

```yaml
eval:
  history_db_path: eval_history.db
  cache_enabled: true
  cache_db_path: .agentlab/eval_cache.db
  dataset_path:
  dataset_split: test
  dataset_strict_integrity: false
  random_seed: 7
  token_cost_per_1k: 0.0
  significance_alpha: 0.05
  significance_min_effect_size: 0.005
  significance_iterations: 2000
```

### Recommended CI policy

- Run strict integrity mode for gated branches.
- Fail promotion on contamination warnings or guardrail regressions.
- Require confidence-aware deltas instead of raw point-estimate bumps.

## Validation performed in this change set

Targeted test coverage added and passed for:
- Eval cache reuse behavior
- Contamination warning and strict-mode blocking
- Confidence interval population
- Reproducibility fingerprint and cost metadata

Additional related test suites were run to confirm no regressions in eval/runtime surfaces.

## Future improvements

- Add cache invalidation hooks by scorer version and grader stack version IDs.
- Add per-slice confidence intervals and significance by category.
- Add adaptive sampling to reduce eval spend while preserving statistical power.
- Add automatic “promotion report” artifact combining CIs, effect sizes, and guardrail checks.

# P0 Sprint 2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restore product trust across CLI/API/Web eval and review surfaces, separate simulated vs real eval execution, introduce a canonical eval model/runtime, and add import adapters for existing OpenAI/Anthropic-style agents.

**Architecture:** First standardize eval/review state around one persisted workspace truth so every surface reads the same objects. Then extend that canonical eval payload with explicit run mode metadata, layer in a compatibility-first eval object model plus grader runtime, and finally build adapters and guided connect flows on top of those stable primitives.

**Tech Stack:** Python CLI (`click`), FastAPI routes, SQLite-backed stores, React + React Query web UI, pytest, workspace-local JSON/YAML persistence.

---

### Task 1: P0.1 source-of-truth discovery lock-in

**Files:**
- Modify: `task_plan.md`
- Modify: `findings.md`
- Modify: `progress.md`
- Test: `tests/test_cli_commands.py`
- Test: `tests/test_e2e_value_chain_cli.py`

**Step 1: Write the failing tests**

- Add a CLI regression test proving `agentlab eval show latest` and `agentlab eval list` disagree today when the latest workspace result only exists in `.agentlab/eval_results_latest.json`.
- Add an end-to-end test that creates a workspace, runs an eval, runs optimize, and verifies the CLI review list, API change cards, API experiments, and latest eval surfaces all point at the same persisted state.

**Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/test_cli_commands.py -k "eval_list or eval_show" -q
pytest tests/test_e2e_value_chain_cli.py -k "surface or review or consistency" -q
```

**Step 3: Write minimal implementation**

- Introduce a shared helper for resolving the canonical latest eval result from the workspace.
- Make `eval list`, `eval show latest`, `status`, and optimize/read-review helpers consume that helper instead of custom scans.
- Ensure CLI review commands and API change/experiment routes share workspace-local store paths.

**Step 4: Run focused verification**

Run:
```bash
pytest tests/test_cli_commands.py tests/test_e2e_value_chain_cli.py tests/test_experiments_api.py -q
```

**Step 5: Commit**

```bash
git commit -m "fix: cross-surface state consistency (eval list, review sync, status alignment)"
```

### Task 2: P0.2 demo vs proof mode separation

**Files:**
- Modify: `runner.py`
- Modify: `cli/status.py`
- Modify: `web/src/pages/EvalRuns.tsx`
- Modify: `web/src/pages/EvalDetail.tsx`
- Modify: `web/src/lib/api.ts`
- Modify: `web/src/lib/types.ts`
- Test: `tests/test_cli_commands.py`
- Test: `tests/test_eval_agent.py`
- Test: `web/src/pages/*.test.tsx` as needed

**Step 1: Write the failing tests**

- Add tests asserting every eval run result includes `mode` with one of `mock`, `live`, or `mixed`.
- Add a CLI test for `--require-live` failing instead of falling back.
- Add a status test asserting the latest eval mode is surfaced.

**Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/test_cli_commands.py tests/test_eval_agent.py -k "mode or require_live" -q
```

**Step 3: Write minimal implementation**

- Persist run mode in the canonical eval result payload.
- Label CLI output clearly for mock/live/mixed.
- Mark fallback cases as `mixed` and attach warnings.
- Surface the last eval mode in `agentlab status`.
- Add UI badges for eval mode in list/detail views.

**Step 4: Run focused verification**

Run:
```bash
pytest tests/test_cli_commands.py tests/test_eval_agent.py -q
```

**Step 5: Commit**

```bash
git commit -m "feat: demo vs proof mode separation (eval mode tracking, --require-live flag)"
```

### Task 3: P0.3 canonical eval object model and unified grader runtime

**Files:**
- Create: `core/eval_model.py`
- Create: `evals/grader_runtime.py`
- Modify: `evals/runner.py`
- Modify: `api/routes/eval.py`
- Modify: `api/server.py`
- Modify: `web/src/lib/api.ts`
- Modify: `web/src/lib/types.ts`
- Test: `tests/test_evals.py`
- Test: `tests/test_data_engine.py`
- Test: `tests/test_generated_evals_api.py`
- Test: `tests/test_api_route_aliases.py`

**Step 1: Write the failing tests**

- Add model tests for `Evaluation`, `EvaluationRun`, `Dataset`, `Grader`, `GraderResult`, `RunResult`, and `Annotation`.
- Add runtime tests covering deterministic, regex, similarity, classification, composite, and compatibility-wrapper grader execution.
- Add route tests proving the unified eval route family still serves existing consumers.

**Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/test_evals.py tests/test_data_engine.py tests/test_generated_evals_api.py tests/test_api_route_aliases.py -q
```

**Step 3: Write minimal implementation**

- Create the canonical model objects with serialization helpers.
- Build `evals/grader_runtime.py` as the single grader execution engine.
- Wrap legacy scorers/judges in `Grader` adapters.
- Update `evals/runner.py` to build/run canonical evaluation runs internally.
- Collapse duplicate `/api/eval/*` and `/api/evals/*` behavior behind one implementation.

**Step 4: Run focused verification**

Run:
```bash
pytest tests/test_evals.py tests/test_data_engine.py tests/test_generated_evals_api.py tests/test_api_route_aliases.py tests/test_api.py -q
```

**Step 5: Commit**

```bash
git commit -m "feat: canonical eval object model and unified grader runtime"
```

### Task 4: P0.4 runtime adapters and connect flow

**Files:**
- Create: `adapters/base.py`
- Create: `adapters/openai_agents.py`
- Create: `adapters/anthropic_claude.py`
- Create: `adapters/http_webhook.py`
- Create: `adapters/transcript.py`
- Modify: `runner.py`
- Modify: `web/src/pages/Connect.tsx`
- Modify: web navigation files as needed
- Test: `tests/test_cli_integrations.py`
- Test: `tests/test_adk_importer.py` or new adapter-focused tests
- Test: `web/src/pages/*.test.tsx` for Connect flow

**Step 1: Write the failing tests**

- Add adapter tests for project scanning/import summaries and transcript import.
- Add CLI tests for `agentlab connect openai-agents`, `anthropic`, `http`, and `transcript`.
- Add web tests for the guided Connect page navigation and CTA flow.

**Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/test_cli_integrations.py -k "connect or adapter" -q
```

**Step 3: Write minimal implementation**

- Implement a shared `AgentAdapter` base with discover/import primitives.
- Implement OpenAI Agents, Anthropic, HTTP, and transcript adapters.
- Add `agentlab connect ...` CLI that creates/imports a workspace plus starter eval fixtures and adapter config.
- Add the Connect page plus sidebar/navigation entry in the web UI.

**Step 4: Run focused verification**

Run:
```bash
pytest tests/test_cli_integrations.py tests/test_adk_importer.py tests/test_cx_studio_api.py -q
```

**Step 5: Commit**

```bash
git commit -m "feat: OpenAI and Anthropic runtime adapters with agentlab connect"
```

### Task 5: Final verification

**Files:**
- Review only

**Step 1: Run the full verification set**

Run:
```bash
pytest tests/test_cli_commands.py tests/test_e2e_value_chain_cli.py tests/test_eval_agent.py tests/test_evals.py tests/test_data_engine.py tests/test_generated_evals_api.py tests/test_api_route_aliases.py tests/test_cli_integrations.py -q
```

**Step 2: Review diff context**

Run:
```bash
git status --short
git log --oneline --decorate -4
git diff --stat master...HEAD
```

**Step 3: Trigger completion event**

Run:
```bash
openclaw system event --text "Done: P0 sprint 2 complete — state consistency, demo mode, eval model, runtime adapters" --mode now
```

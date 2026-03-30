# CLI / UI Alignment Report

Audit scope:

- CLI: `runner.py`, plus imported command groups from `cli/mode.py`, `cli/mcp_setup.py`, and `cli/intelligence.py`
- UI: every file under `web/src` (171 files)
- API: every route module under `api/routes` (49 files)

Important audit note: the requested `frontend/` directory does not exist in this repository. The active SPA lives under `web/src`, and that is the frontend audited here.

Important product note: the requested workflow list included `sandbox`, but `runner.py` does **not** define a CLI `sandbox` command group. Sandbox currently exists as API routes plus a stub UI page, not as a CLI surface.

## 1. CLI Command → UI Page Mapping Table

Legend:

- `✅ Full` — UI covers all CLI capabilities
- `🟡 Partial` — UI covers some but not all
- `❌ Missing` — No UI equivalent exists
- `🔄 Divergent` — Both exist but do different things

| CLI Command Group | CLI Capabilities | UI Page/Component | UI Capabilities | Alignment Status |
| --- | --- | --- | --- | --- |
| `init` | Scaffold workspace, create `configs/`, `evals/`, `.autoagent/`, seed synthetic/demo data | None | UI assumes an initialized workspace and running API | ❌ Missing |
| `status` | Snapshot health, scores, active config, review counts, deploy state | `Dashboard`, `Event Log`, `Conversations` | Control-plane dashboard with health cards, gates, cost, demo status, control actions | 🔄 Divergent |
| `build` | Generate build artifact, starter config, eval draft, persist `.autoagent/build_artifact_latest.json` | `Builder`, `IntelligenceStudio` | Conversational config drafting, transcript/prompt-based generation, YAML export | 🔄 Divergent |
| `build-show` | Inspect saved build artifact selectors like `latest` | None | No persisted build artifact viewer | ❌ Missing |
| `eval` | `run`, `results`, `show`, `list`, `generate` | `EvalRuns`, `EvalDetail` | Launch runs, inspect results, compare runs, generate evals, accept generated suites | 🟡 Partial |
| `optimize` | Run optimization cycles, evaluate proposals, persist attempts, optionally continuous/full-auto | `Optimize`, `LiveOptimize`, `Experiments`, `ChangeReview`, `Opportunities` | Start optimize jobs, watch live stream, inspect experiment cards, review changes, browse opportunities | 🔄 Divergent |
| `improve` | Alias to `optimize` | Same as `optimize` | Same split UI surface as optimize | 🔄 Divergent |
| `deploy` | Promote config canary/immediate, inspect status, optional `cx-studio` target | `Deploy` | Canary/immediate deploy and rollback for core AutoAgent configs | 🟡 Partial |
| `loop` | Start continuous optimization loop, scheduling/checkpoint options, stop-on-plateau | `LoopMonitor`, `Dashboard` | Start/stop loop, inspect loop status, pause/resume optimization | 🟡 Partial |
| `logs` | Read historical conversations from local store | `Conversations`, `EventLogPage` | Filtered conversation browser and append-only system event timeline | 🟡 Partial |
| `doctor` | Workspace diagnostics: configs, evals, DBs, traces, mock/live readiness | None | No dedicated diagnostics page | ❌ Missing |
| `pause` / `resume` / `reject` / `pin` / `unpin` | Human control-plane overrides for optimizer surfaces and experiments | `Dashboard`, `LoopMonitor` | Pause/resume, reject experiment, pin/unpin surfaces through dashboard controls | 🟡 Partial |
| `config` | `list`, `show`, `set-active`, `diff`, `import`, `migrate` | `Configs` | List/show/diff config versions plus natural-language edit preview/apply | 🔄 Divergent |
| `import` | Alias/import flows for config files and transcript archives | `CxImport`, `AdkImport`, `IntelligenceStudio` | External agent import and transcript upload exist, but config import alias does not | 🟡 Partial |
| `autofix` | `suggest`, `apply`, `history`, `show`, interactive review | `AutoFix` | Suggest/apply/reject proposals, inspect history and diff previews | ✅ Full |
| `review` | `list`, `show`, `apply`, `reject`, `export`; interactive default review | `ChangeReview` | Review, export, approve/reject, audit, and hunk-level triage of change cards | ✅ Full |
| `changes` | Alias to `review` | `ChangeReview` | Same underlying page and APIs as review | ✅ Full |
| `judges` | `list`, `calibrate`, `drift` | `JudgeOps` | Judge list, calibration runs, drift reports, disagreement queue, human feedback submission | ✅ Full |
| `context` | `analyze`, `simulate`, `report` | `ContextWorkbench` | Trace analysis, strategy simulation, utilization/handoff reporting | ✅ Full |
| `runbook` | `list`, `show`, `apply`, `create` | `Runbooks` | Search/list/show/apply runbooks | 🟡 Partial |
| `memory` | `show`, `add` project memory | `ProjectMemory` | Edit memory sections, append notes, inspect project memory | ✅ Full |
| `registry` | `list`, `show`, `add`, `diff`, `import` for skills/policies/tools/handoffs | `Registry` | Search/list/show/diff registry items by type | 🟡 Partial |
| `skill` | Unified skill CRUD/search/install/test/compose/promote/archive/effectiveness | `Skills`, `AgentSkills` | Search, compose, install, draft, promote/archive, test, effectiveness, auto-generate gap skills | 🔄 Divergent |
| `curriculum` | `generate`, `list`, `apply` self-play eval curriculum | `EvalRuns` curriculum section | Generate curriculum batches and apply them into active evals | ✅ Full |
| `trace` | `show`, `grade`, `blame`, `graph`, `promote` | `Traces`, `BlameMap` | Recent trace browser and blame-cluster exploration | 🟡 Partial |
| `scorer` | `create`, `list`, `show`, `refine`, `test` NL scorer specs | `ScorerStudio` | Compile, inspect, save, refine, and test scorers | ✅ Full |
| `quickstart` | One-command golden path: init → eval → optimize → summary → open UI | None | No equivalent guided UI onboarding/run-all flow | ❌ Missing |
| `full-auto` | Dangerous auto-promote optimize + loop mode | None | No UI equivalent for full-auto mode or acknowledgement gate | ❌ Missing |
| `autonomous` | Scoped autonomous optimization entrypoint | None | No UI equivalent | ❌ Missing |
| `demo` | `quickstart`, `seed`, `vp` demo workflows | `Demo` | Streamed VP demo experience | 🟡 Partial |
| `edit` | Natural-language config edit, dry-run, interactive REPL | `Configs` | One-shot NL edit preview/apply inside config page | 🟡 Partial |
| `explain` | Plain-English status summary of agent health and failure buckets | None | Dashboard shows metrics, but no explain/report surface | ❌ Missing |
| `diagnose` | One-shot or interactive diagnosis session | Dashboard embedded diagnose chat | Diagnose chat exists as dashboard widget, not as full page/workflow | 🟡 Partial |
| `replay` | Optimization-history log view from `optimizer_memory.db` | `Optimize`, `Experiments`, `ChangeReview` | History is visible across multiple pages, but no single replay/log surface | 🟡 Partial |
| `server` | Start API + web console | None | UI is the thing being served, not a peer surface | ❌ Missing |
| `mcp-server` | Expose AutoAgent over MCP transport | None | No UI equivalent | ❌ Missing |
| `mode` | `show`, `set` mock/live runtime mode | None | No runtime mode toggle in UI | ❌ Missing |
| `mcp` | `init`, `status` for editor MCP wiring | None | No MCP client setup UI | ❌ Missing |
| `intelligence` | Upload transcript archive, list/show reports, generate agent | `IntelligenceStudio` | Upload archive, generate agent from prompt or transcript, chat-refine config, export YAML | 🔄 Divergent |
| `policy` | `list`, `show` trained policy artifacts | `PolicyCandidates` | Browse policies/jobs and inspect selected candidate state | ✅ Full |
| `cx` | `compat`, `list`, `import`, `export`, `deploy`, `widget`, `status` | `CxImport`, `CxDeploy` | Import CX agents, preview/export changes, deploy to envs, generate widget HTML | 🟡 Partial |
| `adk` | `import`, `export`, `deploy`, `status`, `diff` | `AdkImport`, `AdkDeploy` | Parse/import ADK agents and deploy with diff preview | 🟡 Partial |
| `dataset` | Create/list/stats training datasets | None | No dataset management UI | ❌ Missing |
| `outcomes` | Import business outcomes | None | No outcomes import UI | ❌ Missing |
| `release` | Create/list signed release objects | None | No release-object UI | ❌ Missing |
| `benchmark` | Run named benchmark suites | None | No benchmark UI | ❌ Missing |
| `reward` | `create`, `list`, `test` reward definitions | `RewardStudio`, `RewardAudit` | Create/list rewards, run audits and challenge suites | 🟡 Partial |
| `rl` | Policy optimization train/jobs/eval/promote/rollback/dataset/canary | `PolicyCandidates`, `RewardAudit` | Train jobs, inspect jobs/policies, OPE, canary, promote, rollback | 🟡 Partial |
| `pref` | Collect/export preference pairs | `PreferenceInbox` | Persistent pair inbox, stats, form submission, export | 🔄 Divergent |

Additional command-surface notes:

- Hidden/legacy CLI groups also exist: `run` (legacy aliases), `build-inspect` (hidden), and `changes`/`improve` as aliases.
- The UI does not expose those legacy aliases directly; it organizes by workflow pages instead.

## 2. UI Pages Without CLI Equivalent

These are routed or otherwise present UI surfaces that do not map cleanly to a CLI command group.

| UI Page / Feature | What It Does | Closest CLI Surface | Notes |
| --- | --- | --- | --- |
| `Dashboard` | Multi-source control plane: health, gates, costs, control actions, diagnose widget | `status` + control commands | No single CLI equivalent; this is an aggregation layer |
| `EventLogPage` | Append-only system event timeline with payload inspection | None | No CLI `events` command |
| `Notifications` | Manage webhook/Slack/email subscriptions and delivery history | None | Entirely UI/API-only today |
| `Opportunities` | Ranked opportunity queue from failure clustering | `optimize` / `trace` adjacent | No `opportunities` CLI command |
| `AgentSkills` | Skill-gap analysis and generated-skill approval flow | `skill` adjacent | No CLI equivalent for auto-generated skill gap workflow |
| `Knowledge` | Placeholder page for knowledge mining | None | API exists, page is still “Coming soon” |
| `Reviews` | Placeholder page for collaborative reviews | None | API exists at `/api/reviews`, page is still “Coming soon” |
| `Sandbox` | Placeholder page for synthetic conversation sandboxing | None | API exists at `/api/sandbox`, but there is no CLI or real UI yet |
| `WhatIf` | Placeholder page for replay/projection experiments | `replay` adjacent | API exists at `/api/what-if`, page is still “Coming soon” |
| `Settings` | Reference paths, shortcuts, API docs links, repo links | None | Operational reference page, not a CLI mirror |

Dormant/redirected UI sources:

- `AgentStudio.tsx` exists in source, but `/agent-studio` redirects to `/build`
- `Assistant.tsx` exists in source, but `/assistant` redirects to `/build`

These are part of the codebase inventory, but they are not active first-class routed experiences.

## 3. Gap Analysis

| Gap | What CLI Can Do That UI Can't | What UI Can Do That CLI Can't | Priority | Suggested Approach |
| --- | --- | --- | --- | --- |
| Workspace bootstrap and environment readiness | `init`, `doctor`, `mode`, `mcp`, `server`, `mcp-server`, `quickstart`, `full-auto` | None | P0 | Add a real onboarding/setup flow in UI for workspace bootstrap, health checks, mock/live mode, and MCP setup status. Keep `server`/`mcp-server` CLI-only, but make their state visible in UI. |
| Build workflow is conceptually split | `build` persists a build artifact, starter config, and next-step files | UI has conversational builder and transcript studio, but neither persists the same artifact model | P0 | Align on one shared build service and one persisted build artifact contract. Merge `Builder` and `IntelligenceStudio` into one “Build” workflow with modes, not separate products. |
| Builder platform is richer than either surface | No CLI command uses the full builder workspace/project/task model | UI only uses `/api/builder/chat` and `/api/builder/export`, while the backend also exposes projects, sessions, tasks, proposals, approvals, permissions, events, and specialists | P1 | Decide whether Builder is a real product area. If yes, build the missing workspace UI around the existing API. If not, collapse the unused API surface and align `build` around the simpler artifact flow. |
| Experiment history is not actually shared | CLI uses `.autoagent/experiment_log.tsv` for `experiment log` | UI/API use `.autoagent/experiments.db` and `.autoagent/opportunities.db` | P0 | Replace TSV-only CLI experiment logging with the same `ExperimentStore`/opportunity APIs the UI uses, or have both read/write through a shared service layer. |
| Transcript intelligence state is split | CLI persists reports to `.autoagent/intelligence_reports.json` | UI/API keep reports in memory inside `TranscriptIntelligenceService` and only persist knowledge assets | P0 | Introduce one persistent transcript intelligence store used by both CLI and API. Add report list/show in UI and have CLI read the same records. |
| Intelligence API is underexposed in both surfaces | CLI only exposes upload/list/show/generate-agent | UI only exposes upload/generate/refine, while the API also supports report Q&A, applying insights into change cards, deep research, and autonomous loops | P1 | Promote the transcript report object to a first-class UI view and extend CLI to call the same richer intelligence operations. |
| Skills are split across multiple stores | CLI `skill` defaults to `.autoagent/skills.db`; CLI `registry` uses `registry.db` | UI `Skills` uses `.autoagent/core_skills.db`; UI `Registry` uses `registry.db`; `AgentSkills` is another generated workflow | P0 | Collapse skill state into one canonical skill store and one API contract. Make registry browsing and runtime/build skill lifecycle clearly separate concepts in both CLI and UI. |
| Optimize workflow is fragmented in UI | CLI offers a single optimize/loop/review/autofix progression | UI spreads the same lifecycle across `Optimize`, `LiveOptimize`, `Experiments`, `ChangeReview`, `Opportunities`, and `LoopMonitor` | P0 | Restructure navigation around a single optimization workflow with sub-tabs or stages. Keep separate pages only where there is a true domain boundary. |
| Config lifecycle differs by surface | CLI has `set-active`, `import`, `migrate`, and selectors | UI adds NL editing but lacks import/migrate/set-active | P1 | Expand `Configs` into a full config lifecycle page: activate, import, migrate, edit, diff, and deploy handoff. |
| Trace tooling is incomplete in UI | CLI supports `trace grade`, `trace graph`, `trace promote` | UI has richer blame visualization than CLI | P1 | Extend `Traces` to include grade, graph, and promote actions. Preserve `BlameMap` as a dedicated analysis pane. |
| Import/deploy taxonomy is inconsistent | CLI `deploy` handles core and `cx-studio`; CLI `cx`/`adk` are explicit | UI splits deploy into `Deploy`, `CxDeploy`, `AdkDeploy` and omits release objects | P1 | Make deployment target selection explicit in one top-level deploy area, with shared status/release contracts underneath. |
| Runbooks and registry are read-heavy in UI | CLI can create/import registry items and runbooks | UI mainly browses, diffs, and applies | P1 | Add create/import paths where governance teams operate in UI, or explicitly keep authoring CLI-first and label UI as read/apply-only. |
| Reward / policy / preference operations are richer in UI but inconsistent in storage semantics | CLI has simple reward/policy/pref commands; reward and policy use durable registries | UI adds audit/OPE/inbox flows; preference collection persists to `preferences.db` while CLI `pref` does not persist | P1 | Either make CLI call the same API-backed stores, or clearly declare these as UI-first governance features and remove misleading CLI parity claims. |
| UI-only experimental features have no CLI counterpart | CLI has no notifications, no opportunity queue, no collaborative review workflow, no knowledge mining page, no sandbox command, no what-if command | UI/API define those domains, though several pages are placeholders | P2 | Decide which of these are strategic. For strategic features, add CLI parity and mature the UI. For non-strategic ones, reduce nav weight or move behind feature flags until complete. |

## 4. Workflow Alignment

### First-run experience: CLI `init` vs UI onboarding

- CLI is the only real first-run path today. `init` creates the workspace, config manifest, eval directories, runbooks, memory scaffolding, and optional demo/synthetic data.
- UI has no equivalent onboarding wizard. `Dashboard` and `Builder` assume the repo is already initialized and the API server is already running.
- Breakpoint: a new operator can succeed from zero in CLI, but not from the UI.
- Inconsistency: UI looks like a primary control plane, but it is operationally downstream of CLI bootstrap.

### Build an agent: CLI `build` vs UI builder

- CLI `build` is file-oriented and artifact-oriented. It writes a concrete build artifact, config, and next-step eval/deploy path.
- UI splits the same intent into two routes:
  - `Builder`: conversational config drafting with session export
  - `IntelligenceStudio`: prompt/transcript-to-config generation with chat refinement
- Breakpoint: UI exports YAML to the browser, but it does not create the same persisted workspace artifact model as CLI `build`.
- Inconsistency: “build” means “persisted workspace artifact” in CLI and “interactive drafting studio” in UI.

### Evaluate: CLI `eval` vs UI eval dashboard

- Core run/list/show behavior is reasonably aligned.
- UI is stronger for result exploration (`EvalDetail`) and generated eval review, and it folds in `curriculum` generation/application.
- CLI is stronger for local file-based workflows (`--output`, `results --file`, selectors outside the running server).
- Breakpoint: generated evals and curriculum feel like part of `eval` in the UI, but they are separate command groups in CLI.
- Inconsistency: the UI eval experience is “evaluation + test authoring + curriculum hardening,” while CLI keeps those concerns more separate.

### Optimize: CLI `optimize` vs UI optimizer

- CLI presents optimize as a primary action that leads naturally into review, deploy, and loop.
- UI fragments the same lifecycle across multiple pages: `Optimize`, `LiveOptimize`, `Experiments`, `ChangeReview`, `Opportunities`, and `LoopMonitor`.
- Breakpoint: after a CLI optimize run, a user has to know which UI page represents which artifact.
- Inconsistency: CLI mental model is linear; UI mental model is a set of specialized studios.

### Deploy: CLI `deploy` vs UI deploy

- CLI `deploy` includes core deploy logic and a `--target cx-studio` path in one command taxonomy.
- UI separates these into:
  - `Deploy` for AutoAgent config promotion
  - `CxDeploy` for CX export/deploy/widget
  - `AdkDeploy` for ADK deploy
- Breakpoint: deployment target is chosen in different places depending on surface.
- Inconsistency: CLI says deploy is one command family; UI says deploy is three separate tools.

### Review: CLI `review` vs UI review cards

- This is the strongest alignment point.
- CLI `review` / `changes` and UI `ChangeReview` operate on the same change-card concept and the same apply/reject/export lifecycle.
- UI is richer because it adds hunk-level status and audits.
- Breakpoint: terminology still drifts between `review`, `changes`, and `experiments`.
- Inconsistency: the same lifecycle artifacts are distributed across `Experiments` and `ChangeReview` in the UI.

### Transcript intelligence: CLI `intelligence` vs UI intelligence studio

- CLI is report-centric: upload archive, list reports, show report, generate agent from report.
- UI is generation-centric: upload archive, immediately generate a config, then chat-refine/export it.
- Breakpoint: CLI-created reports are persisted to a JSON file; UI reports are not using the same durable store.
- Inconsistency: CLI treats intelligence as durable analysis; UI treats it as a drafting studio.

## 5. Shared State Audit

| State | Store / Path | CLI Access | UI / API Access | Audit Result |
| --- | --- | --- | --- | --- |
| Workspace metadata and runtime mode | `.autoagent/workspace.json`, `autoagent.yaml` | `init`, `mode`, `doctor`, runtime loading | Mostly indirect only; no editor UI | CLI-only in practice |
| Config versions | `configs/*.yaml`, `configs/manifest.json` | `config`, `deploy`, `build`, `eval` | `Configs`, `Deploy`, `EvalRuns`, `CxDeploy` | Shared and healthy |
| Conversations | `conversations.db` | `status`, `logs`, `diagnose`, `explain`, `doctor` | `Dashboard`, `Conversations`, diagnose widget, what-if backend | Shared |
| Optimization history | `optimizer_memory.db` | `optimize`, `replay`, `explain`, `status`, `loop` | `Optimize`, `Dashboard`, `LoopMonitor` | Shared |
| Traces | `.autoagent/traces.db` | `trace`, `context`, `doctor` | `Traces`, `BlameMap`, `ContextWorkbench` | Shared |
| Change review cards | `.autoagent/change_cards.db` | `review`, `changes`, intelligence apply flows | `ChangeReview`, intelligence apply APIs | Shared |
| AutoFix proposals | `.autoagent/autofix.db` | `autofix` | `AutoFix` | Shared |
| Judge calibration and human feedback | `.autoagent/grader_versions.db`, `.autoagent/human_feedback.db` | `judges` | `JudgeOps` | Shared |
| Runbooks and registry items | `registry.db` | `runbook`, `registry` | `Runbooks`, `Registry` | Shared |
| Reward definitions | `rewards.db` | `reward` | `RewardStudio`, `RewardAudit` | Shared |
| Policy artifacts and RL jobs | `policy_opt.db` | `policy`, `rl` | `PolicyCandidates`, `RewardAudit` | Shared |
| Experiment log | CLI: `.autoagent/experiment_log.tsv`; UI/API: `.autoagent/experiments.db` | `experiment log` reads TSV | `Experiments` reads DB-backed store | **Not shared** |
| Opportunity queue | `.autoagent/opportunities.db` | No dedicated CLI command | `Opportunities` | UI/API-only |
| Transcript intelligence reports | CLI: `.autoagent/intelligence_reports.json`; API: in-memory `TranscriptIntelligenceService._reports` | `intelligence report list/show/generate-agent` | `IntelligenceStudio`, `/api/intelligence/reports*` | **Not shared** |
| Intelligence knowledge assets | `.autoagent/intelligence_knowledge_assets.json` | Not surfaced directly | `/api/intelligence/knowledge/{asset_id}` | API-only surfaced |
| Unified skills | CLI default `.autoagent/skills.db` | `skill` | No, UI uses a different DB path | **Split** |
| UI skills page store | `.autoagent/core_skills.db` | Not default CLI path | `Skills`, `AgentSkills` backend | UI/API-only by default |
| Builder workspace state | `.autoagent/builder.db` | No CLI equivalent | Builder APIs exist, current UI only uses chat/export subset | UI/API-only |
| Notification subscriptions/history | `.autoagent/notifications.db` | No CLI equivalent | `Notifications` | UI/API-only |
| Knowledge mining entries | `.autoagent/knowledge.db` | No CLI equivalent | `Knowledge` API exists; page is placeholder | UI/API-only |
| Collaborative review requests | `.autoagent/reviews.db` | No CLI equivalent | `Reviews` API exists; page is placeholder | UI/API-only |
| Preference pairs | `preferences.db` | CLI `pref` does not persist here | `PreferenceInbox` / `/api/preferences` | **Not shared** |
| Release objects | `.autoagent/releases/*.json` | `release` | No UI equivalent | CLI-only |
| Build artifact | `.autoagent/build_artifact_latest.json` | `build`, `build-show` | No UI equivalent | CLI-only |

State stores that only one surface can access today:

- CLI-only:
  - `.autoagent/workspace.json` mode/bootstrap state
  - `.autoagent/intelligence_reports.json`
  - `.autoagent/releases/*.json`
  - `.autoagent/build_artifact_latest.json`
  - `.autoagent/experiment_log.tsv`
- UI/API-only:
  - `.autoagent/builder.db`
  - `.autoagent/notifications.db`
  - `.autoagent/knowledge.db`
  - `.autoagent/reviews.db`
  - `.autoagent/opportunities.db`
  - `preferences.db`

The two most important cross-surface state problems are:

1. Experiment history is duplicated in incompatible stores
2. Transcript intelligence reports are not persisted through one shared model

## 6. Refactoring Recommendations

### P0: Align the product model before adding more screens

1. Create one canonical workflow taxonomy shared by CLI help, API route groups, and UI navigation.
   - Recommended top-level taxonomy:
   - `build`
   - `import`
   - `eval`
   - `optimize`
   - `review`
   - `deploy`
   - `observe`
   - `govern`
   - `integrations`
   - `settings`

2. Merge `Builder` and `IntelligenceStudio` into one Build surface.
   - Keep modes inside the page: `Prompt`, `Transcript`, `Builder Chat`, `Saved Artifacts`
   - Persist one shared build artifact model that both CLI `build` and the UI can create, inspect, and resume

3. Replace split state stores with shared services.
   - Move CLI `experiment log` onto the API/backend `ExperimentStore`
   - Persist transcript intelligence reports in a shared durable store
   - Normalize skill storage to one default DB path and one service boundary

4. Reorganize the optimize area around lifecycle, not implementation detail.
   - Recommended IA:
   - `Optimize / Run`
   - `Optimize / Live`
   - `Optimize / Experiments`
   - `Optimize / Review`
   - `Optimize / Opportunities`
   - `Optimize / Loop`

### P1: Fill the missing operational pages

1. Add an onboarding/setup page.
   - Cover `init`, `doctor`, `mode`, and MCP setup visibility
   - Make the first-run UI actually usable without prior CLI steps

2. Add a Trace Detail expansion inside `Traces`.
   - Include grade, graph, and promote actions
   - Link directly into `ContextWorkbench` and `BlameMap`

3. Expand `Configs` into full lifecycle management.
   - Add activate/import/migrate
   - Keep NL edit as one tool inside the page, not the page’s main identity

4. Add missing authoring flows where the UI is already the natural operator surface.
   - `Runbooks`: create
   - `Registry`: add/import
   - `Deploy`: release objects and deployment targets in one place

### P1: Decide which UI-only surfaces are strategic

Recommended to keep and mature:

- `Notifications`
- `Opportunities`
- `AgentSkills`
- `WhatIf`
- `Sandbox`

Recommended only if resourced soon; otherwise hide behind feature flags:

- `Knowledge`
- `Reviews`

### P1: Shared API contracts both CLI and UI should use

These should become the canonical contracts that both surfaces consume:

1. `BuildArtifact`
   - Shared persisted record for prompt/transcript/builder sessions
   - Replaces UI-only builder sessions and CLI-only build artifact files

2. `ExperimentRecord`
   - Shared experiment/change/review timeline object
   - Replaces TSV-vs-SQLite split

3. `TranscriptReport`
   - Durable report object with insights, derived config, and knowledge asset references
   - Used by both `autoagent intelligence` and `IntelligenceStudio`

4. `SkillRecord`
   - One canonical skill schema and one canonical store
   - Registry browsing can remain a different concern, but runtime/build skill lifecycle should not fork by surface

5. `DeploymentTarget` and `ReleaseObject`
   - Shared deploy abstraction across core AutoAgent, CX, and ADK
   - UI should not need separate mental models for “deploy” vs “CX deploy”

### P2: Clean up legacy and confusing navigation

1. Remove or formally deprecate redirected legacy routes.
   - `AgentStudio`
   - `Assistant`

2. Label placeholder pages explicitly as beta/coming-soon or remove them from primary nav.
   - `Knowledge`
   - `Reviews`
   - `Sandbox`
   - `WhatIf`

3. Rename UI nav groups to mirror CLI nouns more closely.
   - Current sidebar buckets (`Operate`, `Governance`, `Analysis`) are reasonable product labels, but they hide CLI parity
   - A command-palette or secondary nav should expose the CLI taxonomy directly

## Summary

The CLI and UI are not just out of sync at the page level; they diverge at three deeper layers:

1. Taxonomy: the CLI is command-family oriented, while the UI is studio/dashboard oriented
2. Persistence: several important domains use different stores per surface
3. Workflow shape: CLI favors linear golden-path execution; UI favors split specialist pages

The highest-value next step is **not** adding more pages one by one. It is establishing shared domain contracts for build artifacts, experiment history, transcript intelligence, and skills, then reorganizing the UI so its navigation mirrors the same product model the CLI already suggests.

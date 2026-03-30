# CLI/UI Alignment Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Align the AutoAgent CLI, API, and web UI around one shared taxonomy, one shared contract layer, and one shared persistence model while preserving existing behavior through compatibility routes and adapters.

**Architecture:** Add a thin shared boundary layer first: `shared/contracts/*` for DTOs and `shared/taxonomy.*` for the 10 top-level command groups. Migrate surface boundaries to those contracts one seam at a time instead of rewriting internal domain models. Preserve current UI routes via aliases and keep `runner.py` and `api/server.py` under single-owner integration to avoid merge conflicts.

**Tech Stack:** Python 3.11+, Click CLI, FastAPI, SQLite/JSON stores, React 19, Vite, TypeScript, React Query, Vitest, Pytest.

---

### Task 1: Shared TypeScript Contracts and Taxonomy

**Owner:** Frontend contracts worker

**Files:**
- Modify: `shared/contracts/build-artifact.ts`
- Create: `shared/contracts/experiment-record.ts`
- Create: `shared/contracts/transcript-report.ts`
- Create: `shared/contracts/skill-record.ts`
- Create: `shared/contracts/deployment-target.ts`
- Create: `shared/contracts/release-object.ts`
- Modify: `shared/contracts/taxonomy.ts`
- Create: `shared/taxonomy.ts`
- Create: `web/src/lib/navigation.ts`
- Create: `web/src/lib/navigation.test.ts`

**Step 1: Write the failing frontend contract/taxonomy tests**

Add tests that verify:
- the top-level taxonomy contains exactly the 10 required command groups
- the navigation config maps those groups to route sections and aliases
- shared Build tabs are represented as `prompt`, `transcript`, `builder_chat`, and `saved_artifacts`

**Step 2: Run the failing test**

Run: `cd web && npm test -- web/src/lib/navigation.test.ts`

Expected: FAIL because `web/src/lib/navigation.ts` and the shared contract exports do not exist yet.

**Step 3: Implement the shared TypeScript contracts and navigation schema**

Requirements:
- Keep existing untracked `shared/contracts/build-artifact.ts` and `shared/contracts/taxonomy.ts` as draft inputs, but normalize them to the final shape.
- `shared/taxonomy.ts` should be the canonical top-level export used by the web shell.
- `web/src/lib/navigation.ts` should be the single source for:
  - sidebar groups
  - breadcrumb labels
  - command palette destinations
  - route aliases and legacy redirects

**Step 4: Run the test again**

Run: `cd web && npm test -- web/src/lib/navigation.test.ts`

Expected: PASS

**Step 5: Commit**

```bash
git add shared/contracts shared/taxonomy.ts web/src/lib/navigation.ts web/src/lib/navigation.test.ts
git commit -m "feat(shared): add frontend taxonomy and contracts"
```

### Task 2: Shared Python Contracts and CLI Taxonomy

**Owner:** Backend contracts worker

**Files:**
- Create: `shared/__init__.py`
- Create: `shared/contracts/__init__.py`
- Create: `shared/contracts/build_artifact.py`
- Create: `shared/contracts/experiment_record.py`
- Create: `shared/contracts/transcript_report.py`
- Create: `shared/contracts/skill_record.py`
- Create: `shared/contracts/deployment_target.py`
- Create: `shared/contracts/release_object.py`
- Create: `shared/taxonomy.py`
- Modify: `runner.py`
- Create: `tests/test_shared_contracts.py`
- Create: `tests/test_shared_taxonomy.py`
- Create: `tests/test_cli_taxonomy.py`

**Step 1: Write the failing backend contract/taxonomy tests**

Add tests that verify:
- each shared contract dataclass can round-trip to a dict payload
- the taxonomy module exports the 10 required groups in the correct order
- `runner.py` root help uses the shared taxonomy instead of hardcoded legacy groups

**Step 2: Run the failing tests**

Run: `./.venv/bin/python -m pytest --tb=short -q tests/test_shared_contracts.py tests/test_shared_taxonomy.py tests/test_cli_taxonomy.py`

Expected: FAIL because the shared Python contract modules do not exist yet and CLI help is still hardcoded.

**Step 3: Implement the Python contract layer**

Requirements:
- Use dataclasses, not Pydantic, for the shared DTOs.
- Add `from_*` / `to_*` helpers where they bridge existing domain models.
- Import `shared.taxonomy` in `runner.py` for the root help taxonomy block.
- Do not replace internal models like `ExperimentCard` or optimizer transcript models yet.

**Step 4: Run the tests again**

Run: `./.venv/bin/python -m pytest --tb=short -q tests/test_shared_contracts.py tests/test_shared_taxonomy.py tests/test_cli_taxonomy.py`

Expected: PASS

**Step 5: Commit**

```bash
git add shared/__init__.py shared/contracts shared/taxonomy.py runner.py tests/test_shared_contracts.py tests/test_shared_taxonomy.py tests/test_cli_taxonomy.py
git commit -m "feat(shared): add python contracts and cli taxonomy"
```

### Task 3: Build Artifact Persistence Unification

**Owner:** Backend build artifact worker

**Files:**
- Create: `shared/build_artifact_store.py`
- Modify: `shared/contracts/build_artifact.py`
- Modify: `shared/contracts/build-artifact.ts`
- Modify: `runner.py`
- Modify: `cli/stream2_helpers.py`
- Modify: `api/routes/intelligence.py`
- Modify: `api/server.py`
- Modify: `web/src/lib/api.ts`
- Modify: `web/src/lib/types.ts`
- Create: `tests/test_build_artifact_store.py`
- Modify: `tests/test_stream2_resources.py`
- Modify: `tests/test_workspace_cli.py`

**Step 1: Write the failing build artifact tests**

Add tests that verify:
- CLI `build` writes a shared `BuildArtifact` payload
- CLI `build-show latest` reads from the shared store
- API can list and fetch saved build artifacts

**Step 2: Run the failing tests**

Run: `./.venv/bin/python -m pytest --tb=short -q tests/test_build_artifact_store.py tests/test_stream2_resources.py tests/test_workspace_cli.py`

Expected: FAIL because there is no shared build artifact store or API surface yet.

**Step 3: Implement the shared build artifact store**

Requirements:
- Preserve `.autoagent/build_artifact_latest.json` compatibility.
- The store should expose `save_latest`, `get_latest`, `list_recent`, and `get_by_id` or equivalent.
- Keep `runner.py build` behavior intact: config generation, eval generation, and summary output.
- Add API endpoints or route extensions so the UI can list saved artifacts for the new Build page.

**Step 4: Run the tests again**

Run: `./.venv/bin/python -m pytest --tb=short -q tests/test_build_artifact_store.py tests/test_stream2_resources.py tests/test_workspace_cli.py`

Expected: PASS

**Step 5: Commit**

```bash
git add shared/build_artifact_store.py runner.py cli/stream2_helpers.py api/routes/intelligence.py api/server.py web/src/lib/api.ts web/src/lib/types.ts tests/test_build_artifact_store.py tests/test_stream2_resources.py tests/test_workspace_cli.py
git commit -m "feat(build): unify build artifact persistence"
```

### Task 4: Experiment Store Unification

**Owner:** Backend experiments worker

**Files:**
- Modify: `shared/contracts/experiment_record.py`
- Create: `shared/experiment_store_adapter.py`
- Modify: `cli/experiment_log.py`
- Modify: `optimizer/experiments.py`
- Modify: `api/routes/experiments.py`
- Modify: `runner.py`
- Modify: `tests/test_experiment_log.py`
- Modify: `tests/test_experiments.py`
- Modify: `tests/test_experiments_api.py`

**Step 1: Write the failing experiment-store tests**

Add tests that verify:
- CLI optimize writes to the shared experiment store
- CLI experiment history commands still render consistent summaries
- API experiment list/detail returns payloads that align with the shared contract

**Step 2: Run the failing tests**

Run: `./.venv/bin/python -m pytest --tb=short -q tests/test_experiment_log.py tests/test_experiments.py tests/test_experiments_api.py`

Expected: FAIL because CLI still treats TSV as the primary source of truth.

**Step 3: Implement the experiment adapter**

Requirements:
- Keep `ExperimentCard` as the internal DB model.
- Add adapters between `ExperimentCard` and `ExperimentRecord`.
- Preserve CLI pretty-print and JSON output behavior.
- Either stop writing TSV entirely or relegate it to optional export-only compatibility.

**Step 4: Run the tests again**

Run: `./.venv/bin/python -m pytest --tb=short -q tests/test_experiment_log.py tests/test_experiments.py tests/test_experiments_api.py`

Expected: PASS

**Step 5: Commit**

```bash
git add shared/contracts/experiment_record.py shared/experiment_store_adapter.py cli/experiment_log.py optimizer/experiments.py api/routes/experiments.py runner.py tests/test_experiment_log.py tests/test_experiments.py tests/test_experiments_api.py
git commit -m "feat(optimize): unify experiment store access"
```

### Task 5: Transcript Report and Skill Store Unification

**Owner:** Backend intelligence and skills worker

**Files:**
- Create: `shared/transcript_report_store.py`
- Modify: `shared/contracts/transcript_report.py`
- Modify: `cli/intelligence.py`
- Modify: `optimizer/transcript_intelligence.py`
- Modify: `api/routes/intelligence.py`
- Modify: `api/server.py`
- Modify: `cli/skills.py`
- Modify: `cli/workspace.py`
- Modify: `api/routes/skills.py`
- Modify: `tests/test_api_transcript_intelligence.py`
- Modify: `tests/test_transcript_intelligence_service.py`
- Modify: `tests/test_cli_skills.py`
- Modify: `tests/test_skills_api.py`
- Modify: `tests/test_skills_api_integration.py`

**Step 1: Write the failing persistence tests**

Add tests that verify:
- transcript intelligence reports persist across service recreation
- CLI and API both resolve the same transcript report records
- CLI skills and API skills use the same default DB path

**Step 2: Run the failing tests**

Run: `./.venv/bin/python -m pytest --tb=short -q tests/test_api_transcript_intelligence.py tests/test_transcript_intelligence_service.py tests/test_cli_skills.py tests/test_skills_api.py tests/test_skills_api_integration.py`

Expected: FAIL because transcript reports are in-memory on the API side and skills are still split across paths.

**Step 3: Implement the shared stores**

Requirements:
- Persist transcript reports durably without renaming the optimizer’s internal report model.
- Normalize skills to one canonical `.autoagent/core_skills.db` path unless there is a stronger existing constant to reuse.
- Keep registry-backed executable skills separate from lifecycle skills, but make the distinction explicit.

**Step 4: Run the tests again**

Run: `./.venv/bin/python -m pytest --tb=short -q tests/test_api_transcript_intelligence.py tests/test_transcript_intelligence_service.py tests/test_cli_skills.py tests/test_skills_api.py tests/test_skills_api_integration.py`

Expected: PASS

**Step 5: Commit**

```bash
git add shared/transcript_report_store.py cli/intelligence.py optimizer/transcript_intelligence.py api/routes/intelligence.py api/server.py cli/skills.py cli/workspace.py api/routes/skills.py tests/test_api_transcript_intelligence.py tests/test_transcript_intelligence_service.py tests/test_cli_skills.py tests/test_skills_api.py tests/test_skills_api_integration.py
git commit -m "feat(shared): unify transcript and skill stores"
```

### Task 6: Taxonomy-Driven UI Shell and Route Aliases

**Owner:** Frontend shell worker

**Files:**
- Modify: `web/src/App.tsx`
- Modify: `web/src/components/Sidebar.tsx`
- Modify: `web/src/components/Layout.tsx`
- Modify: `web/src/components/CommandPalette.tsx`
- Modify: `web/src/lib/navigation.ts`
- Modify: `web/src/components/Layout.test.ts`

**Step 1: Write the failing shell tests**

Add tests that verify:
- sidebar labels and groupings come from the new taxonomy-driven config
- breadcrumbs use the new top-level groups
- command palette top-level navigation matches the taxonomy
- legacy routes still redirect to the new primary routes

**Step 2: Run the failing tests**

Run: `cd web && npm test -- web/src/components/Layout.test.ts web/src/lib/navigation.test.ts`

Expected: FAIL because the shell still hardcodes old groupings and palette destinations.

**Step 3: Implement the shell refactor**

Requirements:
- Centralize navigation in `web/src/lib/navigation.ts`.
- Keep route aliases for existing pages during migration.
- Use the new top-level labels:
  - Build
  - Import
  - Eval
  - Optimize
  - Review
  - Deploy
  - Observe
  - Govern
  - Integrations
  - Settings

**Step 4: Run the tests again**

Run: `cd web && npm test -- web/src/components/Layout.test.ts web/src/lib/navigation.test.ts`

Expected: PASS

**Step 5: Commit**

```bash
git add web/src/App.tsx web/src/components/Sidebar.tsx web/src/components/Layout.tsx web/src/components/CommandPalette.tsx web/src/lib/navigation.ts web/src/components/Layout.test.ts
git commit -m "refactor(web): align shell navigation with cli taxonomy"
```

### Task 7: Unified Build Page

**Owner:** Frontend build worker

**Files:**
- Create: `web/src/pages/Build.tsx`
- Modify: `web/src/pages/Builder.tsx`
- Modify: `web/src/pages/IntelligenceStudio.tsx`
- Modify: `web/src/lib/builder-chat-api.ts`
- Modify: `web/src/lib/api.ts`
- Modify: `web/src/lib/types.ts`
- Modify: `web/src/App.tsx`
- Modify: `web/src/pages/Builder.test.tsx`
- Modify: `web/src/pages/IntelligenceStudio.test.tsx`
- Create: `web/src/pages/Build.test.tsx`

**Step 1: Write the failing Build-page tests**

Add tests that verify:
- the unified Build page exposes tabs for Prompt, Transcript, Builder Chat, and Saved Artifacts
- prompt and transcript flows still work
- builder-chat export still works
- saved artifacts render shared `BuildArtifact` records

**Step 2: Run the failing tests**

Run: `cd web && npm test -- web/src/pages/Build.test.tsx web/src/pages/Builder.test.tsx web/src/pages/IntelligenceStudio.test.tsx`

Expected: FAIL because `Build.tsx` and the shared saved-artifact flow do not exist yet.

**Step 3: Implement the merged Build page**

Requirements:
- `Build.tsx` becomes the primary routed page for `/build`.
- Preserve `/intelligence` as an alias or redirect during transition.
- Reuse existing `Builder.tsx` and `IntelligenceStudio.tsx` internals as subviews if that keeps scope down.
- Use the shared `BuildArtifact` contract for Saved Artifacts.

**Step 4: Run the tests again**

Run: `cd web && npm test -- web/src/pages/Build.test.tsx web/src/pages/Builder.test.tsx web/src/pages/IntelligenceStudio.test.tsx`

Expected: PASS

**Step 5: Commit**

```bash
git add web/src/pages/Build.tsx web/src/pages/Builder.tsx web/src/pages/IntelligenceStudio.tsx web/src/lib/builder-chat-api.ts web/src/lib/api.ts web/src/lib/types.ts web/src/App.tsx web/src/pages/Builder.test.tsx web/src/pages/IntelligenceStudio.test.tsx web/src/pages/Build.test.tsx
git commit -m "feat(build): merge builder and intelligence studio"
```

### Task 8: Optimize Hub Consolidation

**Owner:** Frontend optimize worker

**Files:**
- Modify: `web/src/pages/Optimize.tsx`
- Modify: `web/src/pages/LiveOptimize.tsx`
- Modify: `web/src/pages/Experiments.tsx`
- Modify: `web/src/pages/ChangeReview.tsx`
- Modify: `web/src/pages/Opportunities.tsx`
- Modify: `web/src/App.tsx`
- Modify: `web/src/lib/navigation.ts`
- Create: `web/src/pages/Optimize.test.tsx`

**Step 1: Write the failing Optimize-hub tests**

Add tests that verify:
- the Optimize page exposes tabs for Run, Live, Experiments, Review, and Opportunities
- each tab renders the corresponding existing content
- legacy routes still navigate into the same section

**Step 2: Run the failing test**

Run: `cd web && npm test -- web/src/pages/Optimize.test.tsx`

Expected: FAIL because the tabbed Optimize hub does not exist yet.

**Step 3: Implement the Optimize section**

Requirements:
- Keep existing page logic mostly intact; compose it into the hub instead of rewriting each page from scratch.
- Preserve legacy route compatibility for `/live-optimize`, `/experiments`, and `/changes`.
- Point navigation and command palette at the consolidated section.

**Step 4: Run the test again**

Run: `cd web && npm test -- web/src/pages/Optimize.test.tsx`

Expected: PASS

**Step 5: Commit**

```bash
git add web/src/pages/Optimize.tsx web/src/pages/LiveOptimize.tsx web/src/pages/Experiments.tsx web/src/pages/ChangeReview.tsx web/src/pages/Opportunities.tsx web/src/App.tsx web/src/lib/navigation.ts web/src/pages/Optimize.test.tsx
git commit -m "refactor(optimize): consolidate optimize workflows"
```

### Task 9: Setup, Config, Trace, Runbook, and Registry Gap Fills

**Owner:** Mixed frontend/backend governance worker

**Files:**
- Create: `api/routes/setup.py`
- Modify: `api/server.py`
- Modify: `api/routes/config.py`
- Modify: `api/routes/traces.py`
- Modify: `web/src/pages/Settings.tsx`
- Modify: `web/src/pages/Configs.tsx`
- Modify: `web/src/pages/Traces.tsx`
- Modify: `web/src/pages/Runbooks.tsx`
- Modify: `web/src/pages/Registry.tsx`
- Modify: `web/src/lib/api.ts`
- Modify: `web/src/lib/types.ts`
- Modify: `web/src/components/CommandPalette.tsx`
- Modify: `web/src/pages/Configs.test.tsx`
- Create: `tests/test_setup_api.py`
- Modify: `tests/test_api_route_aliases.py`

**Step 1: Write the failing API/UI tests**

Add tests that verify:
- setup data exposes init/doctor/mode/MCP status fields
- config endpoints expose activate/import/migrate affordances used by the UI
- trace endpoints expose promote or equivalent actions used by the UI
- runbook and registry authoring actions exist for the new UI affordances

**Step 2: Run the failing tests**

Run: `./.venv/bin/python -m pytest --tb=short -q tests/test_setup_api.py tests/test_api_route_aliases.py && cd web && npm test -- web/src/pages/Configs.test.tsx`

Expected: FAIL because setup API and the missing authoring flows do not exist yet.

**Step 3: Implement the missing workflows**

Requirements:
- `Settings.tsx` becomes the setup/onboarding surface or hosts a setup subsection that covers init, doctor, mode, and MCP status.
- `Configs.tsx` gains activate/import/migrate UI.
- `Traces.tsx` gains grade/graph/promote entry points or a detail drawer.
- `Runbooks.tsx` and `Registry.tsx` expose create/import authoring flows.

**Step 4: Run the tests again**

Run: `./.venv/bin/python -m pytest --tb=short -q tests/test_setup_api.py tests/test_api_route_aliases.py && cd web && npm test -- web/src/pages/Configs.test.tsx`

Expected: PASS

**Step 5: Commit**

```bash
git add api/routes/setup.py api/server.py api/routes/config.py api/routes/traces.py web/src/pages/Settings.tsx web/src/pages/Configs.tsx web/src/pages/Traces.tsx web/src/pages/Runbooks.tsx web/src/pages/Registry.tsx web/src/lib/api.ts web/src/lib/types.ts web/src/components/CommandPalette.tsx web/src/pages/Configs.test.tsx tests/test_setup_api.py tests/test_api_route_aliases.py
git commit -m "feat(govern): add setup and missing authoring flows"
```

### Task 10: Cleanup, Verification, and Finish

**Owner:** Controller / integrator

**Files:**
- Modify: `web/src/pages/Knowledge.tsx`
- Modify: `web/src/pages/Reviews.tsx`
- Modify: `web/src/pages/Sandbox.tsx`
- Modify: `web/src/pages/WhatIf.tsx`
- Delete: `web/src/pages/AgentStudio.tsx`
- Delete: `web/src/pages/Assistant.tsx`
- Delete: `web/src/pages/AgentStudio.test.tsx`
- Modify: `web/src/App.tsx`
- Modify: `web/src/components/Sidebar.tsx`
- Modify: `web/src/lib/navigation.ts`

**Step 1: Write the failing cleanup assertions**

Add or update tests that verify:
- placeholder pages show beta/coming-soon status clearly
- legacy routes redirect to supported surfaces
- removed legacy pages are no longer routed directly

**Step 2: Run the failing tests**

Run: `cd web && npm test -- web/src/components/Layout.test.ts web/src/pages/Build.test.tsx web/src/pages/Optimize.test.tsx`

Expected: FAIL if the cleanup logic has not been wired yet.

**Step 3: Implement cleanup**

Requirements:
- Remove unused legacy page sources only after confirming routes point elsewhere.
- Add visible beta/coming-soon treatment to incomplete pages.
- Keep navigation stable with the new taxonomy.

**Step 4: Run the full verification suite**

Run:

```bash
cd web && npm test
cd web && npm run build
./.venv/bin/python -m pytest --tb=short -q
```

Expected:
- frontend tests pass
- frontend build exits 0
- backend pytest exits 0

**Step 5: Commit and finish**

```bash
git add web/src/pages/Knowledge.tsx web/src/pages/Reviews.tsx web/src/pages/Sandbox.tsx web/src/pages/WhatIf.tsx web/src/App.tsx web/src/components/Sidebar.tsx web/src/lib/navigation.ts
git rm web/src/pages/AgentStudio.tsx web/src/pages/Assistant.tsx web/src/pages/AgentStudio.test.tsx
git commit -m "refactor(web): clean up legacy surfaces"
openclaw system event --text "Done: Codex UI refactoring — P0 taxonomy/contracts/merge/reorg, P1 gap fills, P2 cleanup — all phases complete" --mode now
```

## Execution Notes
- Use subagent-driven development in this session.
- Keep `runner.py` under one integrator owner. Other workers should not edit it directly.
- Keep `api/server.py` under one integrator owner. Other workers should provide adjacent route/store changes only.
- Preserve legacy routes as aliases until the new Build and Optimize sections are verified.
- Prefer adapters over model rewrites for experiments, transcript reports, and release objects.

# AgentLab Rename Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rename the product surface from AgentLab to AgentLab across the repository without changing Python module/package directory layout.

**Architecture:** Apply the rename in two layers. First, move files whose names are part of the public surface (`agentlab.yaml`, `AGENTLAB.md`, sample fixtures) so path references can be updated against their final locations. Second, run ordered text replacements across tracked text files and relevant generated fixtures, then manually fix public API edge cases such as MCP names, CLI branding, workspace helpers, and tests.

**Tech Stack:** Python, Click CLI, FastAPI, React/TypeScript, Markdown/TOML/YAML/JSON configs, git

---

### Task 1: Inventory rename scope and preserve local state

**Files:**
- Modify: working tree only
- Review: `pyproject.toml`
- Review: `runner.py`
- Review: `cli/workspace.py`
- Review: `mcp_server/tools.py`
- Review: `mcp_server/resources.py`
- Review: `web/src/**/*`
- Review: `tests/**/*`

**Step 1: Confirm branch and current local changes**

Run: `git branch --show-current && git status --short`
Expected: branch is `master`; unrelated local changes remain untouched

**Step 2: Identify tracked filenames that include AgentLab variants**

Run: `git ls-files | rg 'agentlab|AgentLab|AGENTLAB|agent_lab|agent-lab|agentlab'`
Expected: list of tracked files and fixtures that need `git mv`

### Task 2: Rename files first

**Files:**
- Move: `agentlab.yaml` -> `agentlab.yaml`
- Move: `AGENTLAB.md` -> `AGENTLAB.md`
- Move: `tests/AGENTLAB.md` -> `tests/AGENTLAB.md`
- Move: `working-docs/briefs/AGENTLAB.md` -> `working-docs/briefs/AGENTLAB.md`
- Move: `docs/samples/legacy_agentlab.yaml` -> `docs/samples/legacy_agentlab.yaml`
- Move: `docs/samples/mock_agentlab.yaml` -> `docs/samples/mock_agentlab.yaml`
- Move: tracked `.tmp` fixtures with matching names

**Step 1: Apply `git mv` for tracked files**

Run: `git mv ...`
Expected: moved files show as renames in `git status`

### Task 3: Apply ordered text replacements

**Files:**
- Modify: tracked text files in source, web UI, docs, tests, templates, CI, and sample fixtures
- Modify: relevant `.tmp` tracked fixtures so verification sweeps are clean

**Step 1: Replace high-risk case variants in order**

Order:
- `AGENTLAB` -> `AGENTLAB`
- `AgentLab` -> `AgentLab`
- `agentlab` -> `agentlab`
- `agentlab` -> `agentlab`
- `agent_lab` -> `agent_lab`
- `agent-lab` -> `agent-lab`

**Step 2: Manually repair edge cases**

Focus:
- CLI metadata and entrypoint in `pyproject.toml` and `runner.py`
- workspace helpers and project-memory filenames
- MCP tool names, server IDs, and URI scheme
- web UI titles/local storage keys/help copy
- docs and examples

### Task 4: Verify no stale references remain

**Files:**
- Review: whole repository except `node_modules` and `.git`

**Step 1: Run broad reference sweeps**

Run:
- `rg -n --hidden --glob '!node_modules' --glob '!.git' 'AgentLab|AGENTLAB|agentlab|agent_lab|agent-lab'`
- `grep -r 'agentlab\|AgentLab\|AGENTLAB\|agent_lab\|agent-lab' --include='*.py' --include='*.md' --include='*.ts' --include='*.tsx' --include='*.yaml' --include='*.yml' --include='*.toml' --include='*.json' . | grep -v node_modules | grep -v .git`

Expected: no remaining matches, or a short explicit list of intentionally retained non-product names to resolve

### Task 5: Fresh verification, commit, push, notify

**Files:**
- Review: full diff

**Step 1: Run focused tests and CLI verification**

Run:
- `pytest`
- `python -m runner --help`

Expected: tests pass; CLI help renders with AgentLab branding and renamed entrypoints/examples

**Step 2: Inspect diff and create one atomic commit**

Run:
- `git status --short`
- `git diff --stat`
- `git add ...`
- `git commit -m 'chore: rename AgentLab → AgentLab across entire codebase'`
- `git push`

**Step 3: Send completion notification**

Run: `openclaw system event --text "Done: Complete rename AgentLab → AgentLab across entire codebase" --mode now`
Expected: notification command exits successfully

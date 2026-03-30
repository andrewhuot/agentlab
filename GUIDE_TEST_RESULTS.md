# Quickstart Guide Test Results

Test date: 2026-03-29

Environment:

- Repo: `AutoAgent-VNextCC-Codex-P0`
- Shell setup: `source .venv/bin/activate`
- Install path tested: `python3 -m pip install -e .`
- Primary execution context: repo root, then `./my-project`
- Notes: commands were executed in guide order first, then the cheat-sheet/reference commands were re-tested in isolation where needed

Legend:

- `PASS`: command succeeded as written
- `FAIL`: command failed as written
- `UNEXPECTED`: command exited `0` but behavior/output did not match the guide’s implied flow

## Section 1 — Quick Install

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `python3 -m pip install -e .` | PASS | - | low |
| `autoagent init --name my-project --demo` | PASS | - | low |
| `cd my-project` | PASS | - | low |
| `autoagent status` | PASS | - | low |
| `autoagent build "Build a customer support agent for order tracking, refunds, and cancellations"` | PASS | - | low |

## Section 2 — Status

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent status` | PASS | - | low |
| `autoagent status --json` | PASS | - | low |
| `mkdir -p scratch/deeply/nested` | PASS | - | low |
| `cd scratch/deeply/nested` | PASS | - | low |
| `autoagent status` | PASS | - | low |
| `cd ../..` | UNEXPECTED | Landed in `my-project/scratch`, not back in `my-project`; later relative-path commands broke downstream. Guide fixed to `cd ../../..`. | critical |

## Section 3 — Build and Import

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent build "Build a customer support agent for order tracking with refund triage and Shopify handoff"` | PASS | - | low |
| `autoagent build-show latest` | PASS | - | low |
| `cp configs/v001.yaml imported-agent.yaml` | FAIL | `cp: configs/v001.yaml: No such file or directory` because the guide left the shell in `my-project/scratch`. | critical |
| `autoagent import config imported-agent.yaml` | FAIL | `Invalid value for 'FILE_PATH': Path 'imported-agent.yaml' does not exist.` | critical |
| `autoagent config import imported-agent.yaml` | FAIL | `Invalid value for 'FILE_PATH': Path 'imported-agent.yaml' does not exist.` | critical |
| `autoagent config list` | PASS | - | low |
| `autoagent config set-active 2` | PASS | - | low |
| `autoagent config show` | PASS | - | low |

## Section 4 — Evaluate Your Agent

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent eval run` | PASS | - | low |
| `autoagent eval run --output eval_results.json` | PASS | - | low |
| `autoagent eval show latest` | PASS | - | low |
| `autoagent eval show latest --json` | PASS | - | low |
| `autoagent eval generate --config configs/v001.yaml --output generated_eval_suite.json` | FAIL | Crashed in mock fallback with `KeyError: slice(None, 5, None)`. Fixed in `evals/auto_generator.py`. | critical |

## Section 5 — Analyze & Diagnose

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent explain` | PASS | - | low |
| `autoagent diagnose` | PASS | - | low |
| `autoagent diagnose --interactive` | PASS | Entered interactive diagnosis shell and waited for input. Guide updated to say `quit` to exit. | low |
| `autoagent trace show latest` | FAIL | `No traces found.` even though demo-seeded traces existed. Fixed by implementing recent-trace lookup in `TraceStore`. | medium |
| `autoagent trace blame --window 24h` | PASS | - | low |
| `autoagent trace promote latest` | FAIL | `No traces found.` Same root cause as `trace show latest`. | medium |

## Section 6 — Optimize & Improve

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent optimize --cycles 3` | FAIL | Crashed with `ValueError: could not convert string to float: ''` when reading empty `.autoagent/best_score.txt`. | critical |
| `autoagent optimize --mode advanced --cycles 2` | FAIL | Same empty-best-score crash as above. | critical |
| `autoagent edit "Make the support agent more explicit about identity verification before changing orders"` | PASS | - | low |
| `autoagent replay` | PASS | - | low |

## Section 7 — AutoFix

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent autofix suggest` | PASS | - | low |
| `autoagent autofix show pending` | PASS | - | low |
| `autoagent autofix apply pending` | PASS | - | low |
| `autoagent autofix history` | PASS | - | low |

## Section 8 — Skills & Registry

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent skill list` | PASS | - | low |
| `autoagent skill recommend --json` | PASS | - | low |
| `autoagent registry list` | PASS | - | low |
| `autoagent registry list --type skills` | PASS | - | low |
| `autoagent registry import ../docs/samples/sample_registry_import.yaml` | PASS | - | low |

## Section 9 — Scoring & Judges

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent scorer create "Score answers higher when they verify identity before modifying an order." --name verification_guard` | PASS | - | low |
| `autoagent scorer list` | PASS | - | low |
| `autoagent scorer show verification_guard` | PASS | - | low |
| `autoagent judges list` | PASS | - | low |
| `autoagent judges calibrate --sample 10` | PASS | - | low |
| `autoagent judges drift` | PASS | - | low |

## Section 10 — Config Management

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent config list` | PASS | - | low |
| `autoagent config show` | PASS | - | low |
| `autoagent config show active` | UNEXPECTED | Returned manifest-active config instead of workspace-selected config after `config set-active 2`. Fixed to respect workspace metadata. | medium |
| `autoagent config show latest --json` | PASS | - | low |
| `autoagent config diff 1 2` | PASS | Output was `No changes.` because schema diff ignores unsupported extra keys such as `few_shot`. | low |
| `autoagent config set-active 2` | PASS | - | low |
| `autoagent config migrate ../docs/samples/legacy_autoagent.yaml --output migrated-autoagent.yaml` | PASS | - | low |

## Section 11 — Deploy

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent review` | PASS | - | low |
| `autoagent review show pending` | PASS | - | low |
| `CARD_ID=$(autoagent review show pending --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["card_id"])')` | PASS | - | low |
| `autoagent review apply "$CARD_ID"` | PASS | - | low |
| `autoagent deploy canary` | PASS | - | low |
| `autoagent release create --experiment-id exp-demo` | PASS | - | low |
| `autoagent release list` | PASS | - | low |
| `autoagent deploy --target cx-studio --no-push` | PASS | - | low |

## Section 12 — Continuous Optimization Loop

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent loop --max-cycles 5 --stop-on-plateau` | PASS | - | low |
| `autoagent pause` | PASS | - | low |
| `autoagent resume` | PASS | - | low |
| `autoagent status` | PASS | - | low |
| `autoagent replay` | PASS | - | low |

## Section 13 — Transcript Intelligence

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `python3 - <<'PY' ... support-archive.zip ... PY` | PASS | - | low |
| `autoagent intelligence upload support-archive.zip` | FAIL | `Invalid value for 'ARCHIVE': File 'support-archive.zip' does not exist.` from nested directory. Fixed by resolving relative archive paths against the invocation cwd and by returning the guide to workspace root earlier. | critical |
| `autoagent intelligence report list` | PASS | Returned no reports because upload had failed. | medium |
| `REPORT_ID=$(autoagent intelligence report list --json | python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["report_id"])')` | FAIL | `IndexError: list index out of range` because upload had failed and the report list was empty. | medium |
| `autoagent intelligence report show "$REPORT_ID"` | FAIL | `Unknown transcript intelligence report:` because `REPORT_ID` was empty. | medium |
| `autoagent intelligence generate-agent "$REPORT_ID" --output configs/v003_transcript.yaml` | FAIL | `Unknown transcript intelligence report:` because `REPORT_ID` was empty. | medium |

## Section 14 — MCP Integration Setup

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent mcp init claude-code` | PASS | - | low |
| `autoagent mcp init codex` | PASS | - | low |
| `autoagent mcp init cursor` | PASS | - | low |
| `autoagent mcp status` | PASS | - | low |

## Section 15 — Mode Control

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent mode show` | PASS | - | low |
| `autoagent mode set mock` | PASS | - | low |
| `autoagent mode set live` | PASS | Requires a real provider credential; guide updated to say so explicitly. | low |

## Section 16 — Advanced: Context Engineering

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent context simulate --strategy balanced` | PASS | - | low |
| `autoagent context simulate --strategy aggressive` | PASS | - | low |
| `autoagent context report` | PASS | - | low |
| `TRACE_ID=$(python3 - <<'PY' ... store.get_recent_trace_ids(limit=1) ... PY )` | FAIL | `AttributeError: 'TraceStore' object has no attribute 'get_recent_trace_ids'`. Fixed in `observer/traces.py`. | critical |
| `autoagent context analyze --trace "$TRACE_ID"` | FAIL | `No events found for trace:` because `TRACE_ID` was empty. | medium |

## Section 17 — Command Reference Cheat Sheet

### Workspace and setup

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent init --name my-project --demo` | PASS | Retest; succeeded in isolated reference directory. | low |
| `autoagent init --dir . --name staging-agent --no-demo` | PASS | Created `./staging-agent` as a nested workspace. Guide updated to `cd staging-agent` before follow-up commands. | medium |
| `autoagent demo seed` | PASS | - | low |
| `autoagent status` | UNEXPECTED | Resolved the ancestor `scratch` workspace because the guide never changed into `./staging-agent`. | medium |
| `autoagent status --json` | UNEXPECTED | Same ancestor-workspace issue as above. | medium |
| `autoagent doctor` | PASS | Ran, but against the ancestor workspace for the same reason. | medium |

### Build and import

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent build "Build an agent for refunds and order tracking"` | PASS | Retest. | low |
| `autoagent build-show latest` | PASS | Retest. | low |
| `autoagent import config imported-agent.yaml` | FAIL | `Path 'imported-agent.yaml' does not exist.` Cheat sheet was missing the `cp` step. | medium |
| `autoagent config import imported-agent.yaml` | FAIL | Same missing-file issue as above. | medium |

### Evaluate and inspect

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent eval run` | PASS | Retest. | low |
| `autoagent eval run --output eval_results.json` | PASS | Retest. | low |
| `autoagent eval show latest` | PASS | Retest. | low |
| `autoagent eval show latest --json` | PASS | Retest. | low |
| `autoagent eval generate --config configs/v001.yaml --output generated_eval_suite.json` | FAIL | Same mock-fallback crash as Section 4. | critical |

### Diagnose and trace

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent explain` | PASS | Retest. | low |
| `autoagent diagnose` | PASS | Retest. | low |
| `autoagent diagnose --interactive` | PASS | Entered the interactive shell; guide updated with an exit note. | low |
| `autoagent trace show latest` | FAIL | Same missing recent-trace lookup as Section 5. | medium |
| `autoagent trace blame --window 24h` | PASS | Retest. | low |
| `autoagent trace promote latest` | FAIL | Same missing recent-trace lookup as Section 5. | medium |

### Optimize and AutoFix

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent optimize --cycles 3` | FAIL | Same empty-best-score crash as Section 6. | critical |
| `autoagent optimize --mode advanced --cycles 2` | FAIL | Same empty-best-score crash as Section 6. | critical |
| `autoagent edit "Reduce verbosity in support answers"` | PASS | - | low |
| `autoagent replay` | PASS | - | low |
| `autoagent autofix suggest` | PASS | - | low |
| `autoagent autofix show pending` | PASS | - | low |
| `autoagent autofix apply pending` | PASS | - | low |
| `autoagent autofix history` | PASS | - | low |

### Skills, registry, scorers, judges

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent skill list` | PASS | Retest. | low |
| `autoagent skill recommend --json` | PASS | Retest. | low |
| `autoagent registry list --type skills` | PASS | Retest. | low |
| `autoagent scorer create "Reward verified account changes" --name account_safety` | PASS | - | low |
| `autoagent scorer list` | PASS | - | low |
| `autoagent judges list` | PASS | Retest. | low |
| `autoagent judges calibrate --sample 10` | PASS | Retest. | low |
| `autoagent judges drift` | PASS | Retest. | low |

### Config management

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent config list` | PASS | Retest. | low |
| `autoagent config show` | PASS | Retest. | low |
| `autoagent config show latest` | PASS | - | low |
| `autoagent config show pending` | PASS | - | low |
| `autoagent config diff 1 2` | PASS | Retest; still showed `No changes.` for schema reasons. | low |
| `autoagent config set-active 2` | PASS | Retest. | low |
| `autoagent config migrate ../docs/samples/legacy_autoagent.yaml --output migrated-autoagent.yaml` | PASS | Retest. | low |

### Deploy and release

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent review` | PASS | By this point the pending review had already been consumed, so output was `No pending change cards.` Guide updated to reseed demo state before the block. | medium |
| `autoagent review show pending` | PASS | Returned `No pending change cards found.` for the same sequencing reason. Guide updated with `autoagent demo seed`. | medium |
| `autoagent deploy canary` | PASS | - | low |
| `autoagent deploy immediate` | PASS | - | low |
| `autoagent release create --experiment-id exp-demo` | PASS | - | low |
| `autoagent release list` | PASS | - | low |
| `autoagent deploy --target cx-studio --no-push` | PASS | - | low |

### Continuous control

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent loop --max-cycles 5` | PASS | - | low |
| `autoagent pause` | PASS | Retest. | low |
| `autoagent resume` | PASS | Retest. | low |

### Intelligence, MCP, and mode

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent intelligence upload support-archive.zip` | FAIL | Same nested-relative-path failure as Section 13. Cheat sheet changed to `../docs/samples/sample_transcripts.zip`. | critical |
| `autoagent intelligence report list` | PASS | Returned no reports because upload failed. | medium |
| `autoagent intelligence report show "$REPORT_ID"` | FAIL | `REPORT_ID` was not defined in the cheat sheet. | medium |
| `autoagent intelligence generate-agent "$REPORT_ID" --output configs/v003_transcript.yaml` | FAIL | Same missing `REPORT_ID` prerequisite as above. | medium |
| `autoagent mcp init claude-code` | PASS | Retest. | low |
| `autoagent mcp init codex` | PASS | Retest. | low |
| `autoagent mcp init cursor` | PASS | Retest. | low |
| `autoagent mcp status` | PASS | Retest. | low |
| `autoagent mode show` | PASS | Retest. | low |
| `autoagent mode set mock` | PASS | Retest. | low |
| `autoagent mode set live` | PASS | Retest; still requires credentials. | low |

### Context engineering

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent context simulate --strategy balanced` | PASS | Retest. | low |
| `autoagent context report` | PASS | Retest. | low |
| `autoagent context analyze --trace "$TRACE_ID"` | FAIL | `TRACE_ID` was not defined in the cheat sheet. Guide updated to include the lookup snippet. | medium |

### Selector shortcuts

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent eval show latest` | PASS | Retest. | low |
| `autoagent review show pending` | PASS | Failed logically because the earlier review flow had already consumed the pending item. Guide updated to reseed demo state before selector examples. | medium |
| `autoagent autofix apply pending` | PASS | Succeeded once but made later JSON selector examples fail by consuming the last pending proposal. Guide changed to `autofix show pending`. | medium |
| `autoagent config show active` | UNEXPECTED | Same workspace-vs-manifest mismatch as Section 10. | medium |
| `autoagent config show latest` | PASS | Retest. | low |
| `autoagent trace show latest` | FAIL | Same recent-trace issue as Sections 5/17 Diagnose and trace. | medium |

### JSON for scripting

| Command | Status | Error / unexpected output | Severity |
|---|---|---:|---|
| `autoagent status --json` | PASS | Retest. | low |
| `autoagent config list --json` | PASS | Returned `is_active` based on manifest instead of workspace selection before the fix. | medium |
| `autoagent eval show latest --json` | PASS | Retest. | low |
| `autoagent review show pending --json` | PASS | Returned an error envelope because the pending review had already been consumed. Guide updated to reseed demo state first. | medium |
| `autoagent autofix apply pending --json` | PASS | Returned an error envelope because the pending AutoFix proposal had already been consumed. Guide changed to `autofix show pending --json`. | medium |
| `autoagent release list --json` | PASS | - | low |

## Fix Summary

- Fixed CLI bugs in `eval generate`, `optimize`, trace `latest` selectors, workspace-aware active-config selectors, and nested relative transcript archive uploads.
- Fixed the guide flow so the nested-directory example returns to the workspace root before file-path commands.
- Made the reference section self-contained by adding missing setup steps, state resets, and variable lookups.
- Replaced repeated destructive selector examples in the reference section with non-destructive `show` examples where needed.

## Second Pass

Test date: 2026-03-29

Scope:

- Re-ran the updated `docs/QUICKSTART_GUIDE.md` top to bottom from a clean `my-project/`.
- Re-ran the command-reference blocks from their documented starting directories.
- Exercised wrong-directory, out-of-order, missing-prereq, `--help`, tab-completion, and documented `--json` paths.

### New issues found on the second pass

| Area | Status in guide | Root cause | Fix |
|---|---|---|---|
| `autoagent review` in Section 11 and the deploy cheat-sheet block | FAIL | The bare `review` command is interactive and traps a pasted shell at `Approve this change? [y/N]:` | Guide updated to use `autoagent review list` / `autoagent review show pending`; `review --help` now documents the interactive default and non-interactive examples |
| `autoagent deploy canary` and `autoagent deploy immediate` in copy-paste blocks | FAIL | Deploy confirmation is interactive unless `--yes` is passed | Guide updated to use `--yes` in copy-paste flows; deploy help already documented that flag |
| `autoagent mcp init codex` followed by `autoagent mcp status` | FAIL | The Codex TOML writer dropped required quotes around keys like `[projects."/Users/..."]` and `"gpt-5.3-codex"` | Fixed `cli/mcp_setup.py` to quote TOML keys safely and added regression coverage |

### Edge-case notes

- Shell completion works through Click’s `_AUTOAGENT_COMPLETE` mechanism even though there is no root `autoagent --show-completion` flag.
- Wrong-directory and out-of-order flows are mostly usable:
  - `autoagent status` outside a workspace: `Error: No AutoAgent workspace found. Run autoagent init`
  - `autoagent config show` outside a workspace: `No active config. Run: autoagent init`
  - `autoagent eval show latest` before any eval run: `No eval results found. Run: autoagent eval run --output results.json`
- `autoagent build` intentionally works outside a workspace by creating local artifacts in the current directory.
- Added example blocks to the guide-relevant group help pages: `review`, `eval`, `config`, `intelligence`, `mcp`, `judges`, `mode`, `context`, `release`, `trace`, `autofix`, `registry`, `skill`, and `scorer`.

### Re-verification

- Targeted regression tests:
  - `pytest -q tests/test_cli_integrations.py -k 'mcp_init_codex_preserves_quoted_keys'`
  - `pytest -q tests/test_cli_taxonomy.py -k 'guide_relevant_group_help_includes_examples'`
  - `pytest -q tests/test_cli_integrations.py tests/test_cli_taxonomy.py -k 'mcp or guide_relevant_group_help_includes_examples or review_without_args_runs_interactive_browser or deploy_canary_supports_interactive_confirmation'`
- Live CLI re-checks passed after the fixes:
  - `autoagent review list`
  - `autoagent review show pending`
  - `autoagent deploy canary --yes`
  - `autoagent deploy immediate --yes`
  - `autoagent mcp init codex`
  - `autoagent mcp status`
- Full suite:
  - `./.venv/bin/python -m pytest --tb=short -q 2>&1 | tail -20`
  - Result: `3195 passed, 19 warnings in 50.28s`

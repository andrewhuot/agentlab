# AutoAgent CLI Quick Start Guide

This guide reflects the workspace-first CLI UX:

- `autoagent init --name my-project --demo` creates a self-sufficient workspace with demo data.
- Commands discover the nearest workspace automatically, so you can run them from any subdirectory.
- `autoagent status` is your home screen.
- Plain YAML and JSON configs can be imported into managed config history.
- Resource-style commands support selectors like `latest`, `active`, and `pending`.
- Durable commands write real files and state instead of printing one-off previews.

If you already have `autoagent` on your `PATH`, start at Section 1. If you are running from source in this repo, install once with `python3 -m pip install -e .`.

## 1. Quick Install

Five commands to a working workspace:

```bash
python3 -m pip install -e .
autoagent init --name my-project --demo
cd my-project
autoagent status
autoagent build "Build a customer support agent for order tracking, refunds, and cancellations"
```

What this gives you immediately:

- A standalone workspace in `./my-project`
- `autoagent.yaml`, `AUTOAGENT.md`, `configs/`, `evals/cases/`, and `.autoagent/workspace.json`
- Demo traces, a pending review card, and a pending AutoFix proposal
- A first build artifact plus generated config/eval handoff files

## 2. Status — Your Home Screen

Run `autoagent status` first in every session.

```bash
autoagent status
```

Machine-readable status for scripts:

```bash
autoagent status --json
```

Workspace discovery works from any nested directory. No `--dir` flag is required after init:

```bash
mkdir -p scratch/deeply/nested
cd scratch/deeply/nested
autoagent status
cd ../..
```

What `status` summarizes:

- Workspace name and path
- Effective mode (`mock` or `live`)
- Active config and a short config summary
- Latest eval score and timestamp
- Conversation count and safety rate
- Pending review cards and AutoFix proposals
- Deployment state and the next recommended action

## 3. Build Your First Agent

### Prompt-based build

```bash
autoagent build "Build a customer support agent for order tracking with refund triage and Shopify handoff"
```

Inspect the latest build artifact without digging through `.autoagent/` manually:

```bash
autoagent build-show latest
```

The build command persists real output:

- `.autoagent/build_artifact_latest.json`
- `configs/vNNN_built_from_prompt.yaml`
- `evals/cases/generated_build.yaml`

### Import an existing config into managed history

Create a plain file, then import it:

```bash
cp configs/v001.yaml imported-agent.yaml
autoagent import config imported-agent.yaml
```

The older group-local form still works:

```bash
autoagent config import imported-agent.yaml
```

List the managed versions and make the imported one the workspace default:

```bash
autoagent config list
autoagent config set-active 2
autoagent config show
```

Why this matters:

- Plain files become versioned configs in `configs/`
- Imported versions appear in `config list`, `config show`, and `config diff`
- `set-active` updates `.autoagent/workspace.json`, and commands default to that version afterward

## 4. Evaluate Your Agent

Run the default eval suite against the active config:

```bash
autoagent eval run
```

Write results to disk so you can inspect them later:

```bash
autoagent eval run --output eval_results.json
```

Show the most recent results with a selector:

```bash
autoagent eval show latest
```

Use JSON for scripting:

```bash
autoagent eval show latest --json
```

Generate a fresh eval suite from a config:

```bash
autoagent eval generate --config configs/v001.yaml --output generated_eval_suite.json
```

Useful defaults:

- If you omit `--config`, `eval run` uses the workspace active config
- `eval show latest` resolves the newest local results file
- `eval run --output ...` persists a complete results JSON file you can revisit with `eval show --file ...`

## 5. Analyze & Diagnose

High-level explanation of the current agent state:

```bash
autoagent explain
```

Failure diagnosis summary:

```bash
autoagent diagnose
```

Interactive diagnosis session:

```bash
autoagent diagnose --interactive
```

Inspect the latest trace and its blame map:

```bash
autoagent trace show latest
autoagent trace blame --window 24h
```

Promote the latest trace into a real eval case:

```bash
autoagent trace promote latest
```

That last command persists a new file in `evals/cases/`, which means promoted traces are durable inputs to later eval runs.

## 6. Optimize & Improve

Run a few optimization cycles:

```bash
autoagent optimize --cycles 3
```

Use a more aggressive search mode:

```bash
autoagent optimize --mode advanced --cycles 2
```

Apply a natural-language config edit:

```bash
autoagent edit "Make the support agent more explicit about identity verification before changing orders"
```

Review the optimization log:

```bash
autoagent replay
```

What persists here:

- New candidate configs in `configs/`
- Optimization attempts in `optimizer_memory.db`
- Updated status and replay history for later sessions

## 7. AutoFix

Generate suggestions without applying them:

```bash
autoagent autofix suggest
```

Inspect the current pending proposal:

```bash
autoagent autofix show pending
```

Apply the pending proposal:

```bash
autoagent autofix apply pending
```

View proposal history:

```bash
autoagent autofix history
```

Selectors make this flow fast:

- `pending` resolves the first pending proposal
- `autofix apply` writes a real config version such as `configs/vNNN_autofix_<id>.yaml`

## 8. Skills & Registry

List installed skills:

```bash
autoagent skill list
```

Ask the CLI for recommended skills:

```bash
autoagent skill recommend --json
```

Inspect registry contents:

```bash
autoagent registry list
autoagent registry list --type skills
```

If you are working from this repo checkout, you can bulk-import the bundled sample registry pack:

```bash
autoagent registry import ../docs/samples/sample_registry_import.yaml
```

If you are not in this repo, replace that file with your own YAML or JSON export.

## 9. Scoring & Judges

Create a scorer from plain English:

```bash
autoagent scorer create "Score answers higher when they verify identity before modifying an order." --name verification_guard
```

List and inspect scorers:

```bash
autoagent scorer list
autoagent scorer show verification_guard
```

Check the active judge stack:

```bash
autoagent judges list
```

Sample cases for human calibration:

```bash
autoagent judges calibrate --sample 10
```

Check judge drift:

```bash
autoagent judges drift
```

## 10. Config Management

List every managed config:

```bash
autoagent config list
```

Show the active config or resolve a selector:

```bash
autoagent config show
autoagent config show active
autoagent config show latest --json
```

Diff two versions:

```bash
autoagent config diff 1 2
```

Set the workspace default config explicitly:

```bash
autoagent config set-active 2
```

Migrate a legacy runtime config if you are using the repo samples:

```bash
autoagent config migrate ../docs/samples/legacy_autoagent.yaml --output migrated-autoagent.yaml
```

Important defaults:

- The workspace active config lives in `.autoagent/workspace.json`
- `config show` without an argument uses that active config
- Resource selectors supported here are `latest`, `active`, `current`, and `pending`

## 11. Deploy

Start with the review queue:

```bash
autoagent review
autoagent review show pending
```

Approve the current pending review card with a copy-pasteable shell flow:

```bash
CARD_ID=$(autoagent review show pending --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["card_id"])')
autoagent review apply "$CARD_ID"
```

Run the canary deploy workflow:

```bash
autoagent deploy canary
```

Create a durable release object:

```bash
autoagent release create --experiment-id exp-demo
autoagent release list
```

Package a CX Agent Studio export without pushing it:

```bash
autoagent deploy --target cx-studio --no-push
```

Durable outputs in this area:

- `review apply` changes the persisted review card state
- `release create` writes `.autoagent/releases/rel-*.json`
- `deploy --target cx-studio --no-push` writes `.autoagent/cx_export_vNNN.json`

## 12. Continuous Optimization Loop

Run a supervised loop:

```bash
autoagent loop --max-cycles 5 --stop-on-plateau
```

Pause and resume:

```bash
autoagent pause
autoagent resume
```

Useful related commands:

```bash
autoagent status
autoagent replay
```

Loop state is durable too: checkpoints, dead letters, and structured logs live under `.autoagent/`.

## 13. Transcript Intelligence

Create a small transcript archive in-place:

```bash
python3 - <<'PY'
import json
import zipfile

transcripts = [
    {
        "conversation_id": "svc-001",
        "session_id": "s1",
        "user_message": "Where is my order? I do not have the order number.",
        "agent_response": "I need to transfer you to live support.",
        "outcome": "transfer",
    },
    {
        "conversation_id": "svc-002",
        "session_id": "s2",
        "user_message": "Please cancel my order.",
        "agent_response": "First verify identity, then cancel it.",
        "outcome": "success",
    },
]

with zipfile.ZipFile("support-archive.zip", "w") as archive:
    archive.writestr("transcripts.json", json.dumps(transcripts))
PY
```

Upload it:

```bash
autoagent intelligence upload support-archive.zip
```

List stored reports:

```bash
autoagent intelligence report list
```

Show the most recent report ID in a copy-pasteable way:

```bash
REPORT_ID=$(autoagent intelligence report list --json | python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["report_id"])')
autoagent intelligence report show "$REPORT_ID"
```

Generate a config from that report:

```bash
autoagent intelligence generate-agent "$REPORT_ID" --output configs/v003_transcript.yaml
```

What persists:

- Uploaded reports are stored in `.autoagent/intelligence_reports.json`
- Generated configs can be written directly into your managed config area

## 14. MCP Integration Setup

Initialize AutoAgent for the supported MCP clients:

```bash
autoagent mcp init claude-code
autoagent mcp init codex
autoagent mcp init cursor
```

Check current MCP status:

```bash
autoagent mcp status
```

Supported targets in the CLI today:

- `claude-code`
- `codex`
- `cursor`
- `windsurf`

## 15. Mode Control (Mock/Live)

Show the current mode:

```bash
autoagent mode show
```

Force mock mode:

```bash
autoagent mode set mock
```

Switch to live mode after you have real provider credentials in your environment:

```bash
autoagent mode set live
```

Mode preference is stored in `.autoagent/workspace.json`, so it survives future CLI sessions.

## 16. Advanced: Context Engineering

Simulate compaction strategies:

```bash
autoagent context simulate --strategy balanced
autoagent context simulate --strategy aggressive
```

Show the aggregate context report:

```bash
autoagent context report
```

Analyze the latest seeded trace with a copy-pasteable trace lookup:

```bash
TRACE_ID=$(python3 - <<'PY'
from observer.traces import TraceStore

store = TraceStore(db_path=".autoagent/traces.db")
recent = store.get_recent_trace_ids(limit=1)
print(recent[0] if recent else "")
PY
)
autoagent context analyze --trace "$TRACE_ID"
```

## 17. Command Reference Cheat Sheet

### Workspace and setup

```bash
autoagent init --name my-project --demo
autoagent init --dir . --name staging-agent --no-demo
autoagent demo seed
autoagent status
autoagent status --json
autoagent doctor
```

### Build and import

```bash
autoagent build "Build an agent for refunds and order tracking"
autoagent build-show latest
autoagent import config imported-agent.yaml
autoagent config import imported-agent.yaml
```

### Evaluate and inspect

```bash
autoagent eval run
autoagent eval run --output eval_results.json
autoagent eval show latest
autoagent eval show latest --json
autoagent eval generate --config configs/v001.yaml --output generated_eval_suite.json
```

### Diagnose and trace

```bash
autoagent explain
autoagent diagnose
autoagent diagnose --interactive
autoagent trace show latest
autoagent trace blame --window 24h
autoagent trace promote latest
```

### Optimize and AutoFix

```bash
autoagent optimize --cycles 3
autoagent optimize --mode advanced --cycles 2
autoagent edit "Reduce verbosity in support answers"
autoagent replay
autoagent autofix suggest
autoagent autofix show pending
autoagent autofix apply pending
autoagent autofix history
```

### Skills, registry, scorers, judges

```bash
autoagent skill list
autoagent skill recommend --json
autoagent registry list --type skills
autoagent scorer create "Reward verified account changes" --name account_safety
autoagent scorer list
autoagent judges list
autoagent judges calibrate --sample 10
autoagent judges drift
```

### Config management

```bash
autoagent config list
autoagent config show
autoagent config show latest
autoagent config show pending
autoagent config diff 1 2
autoagent config set-active 2
autoagent config migrate ../docs/samples/legacy_autoagent.yaml --output migrated-autoagent.yaml
```

### Deploy and release

```bash
autoagent review
autoagent review show pending
autoagent deploy canary
autoagent deploy immediate
autoagent release create --experiment-id exp-demo
autoagent release list
autoagent deploy --target cx-studio --no-push
```

### Continuous control

```bash
autoagent loop --max-cycles 5
autoagent pause
autoagent resume
```

### Intelligence, MCP, and mode

```bash
autoagent intelligence upload support-archive.zip
autoagent intelligence report list
autoagent intelligence report show "$REPORT_ID"
autoagent intelligence generate-agent "$REPORT_ID" --output configs/v003_transcript.yaml
autoagent mcp init claude-code
autoagent mcp init codex
autoagent mcp init cursor
autoagent mcp status
autoagent mode show
autoagent mode set mock
autoagent mode set live
```

### Context engineering

```bash
autoagent context simulate --strategy balanced
autoagent context report
autoagent context analyze --trace "$TRACE_ID"
```

### Selector shortcuts

```bash
autoagent eval show latest
autoagent review show pending
autoagent autofix apply pending
autoagent config show active
autoagent config show latest
autoagent trace show latest
```

### JSON for scripting

```bash
autoagent status --json
autoagent config list --json
autoagent eval show latest --json
autoagent review show pending --json
autoagent autofix apply pending --json
autoagent release list --json
```

Notes on JSON output:

- Stream 2 resource commands such as `config list`, `config show`, `review show`, `autofix apply`, and `release list` use the standard `{status, data, next}` envelope.
- Some older commands such as `status --json` and `eval run --json` return direct JSON payloads for backward compatibility.

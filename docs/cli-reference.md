# CLI Reference

AutoAgent groups the default CLI into **Primary** and **Secondary** commands. Run `autoagent advanced` to see the broader hidden command set.

Helpful starting points:

```bash
autoagent --help
autoagent advanced
autoagent <command> --help
```

Notes:

- many top-level commands support `--quiet` / `--no-banner`
- many major commands support `--json` or `--output-format`; check the command help for the exact surface
- selectors like `latest`, `active`, and `pending` are supported on several review, eval, and config commands

---

## Primary Commands

### `autoagent new`

Create a new starter workspace.

```bash
autoagent new my-agent --template customer-support --demo
```

Key options:

- `--template [customer-support|it-helpdesk|sales-qualification|healthcare-intake]`
- `--demo / --no-demo`
- `--mode [mock|live|auto]`

### `autoagent build`

Generate build artifacts from a natural-language prompt, or inspect the latest build output.

Common commands:

```bash
autoagent build "Build a support agent for order tracking"
autoagent build show latest
```

Subcommands:

- `show` — show the latest or selected build artifact

### `autoagent eval`

Run evals, inspect results, compare runs, and generate eval suites.

Common commands:

```bash
autoagent eval run
autoagent eval show latest
autoagent eval list
autoagent eval compare --left-run left.json --right-run right.json
autoagent eval generate --config configs/v001.yaml --output generated_eval_suite.json
autoagent eval results --run-id eval-123
```

Subcommands:

- `run` — run the eval suite against a config
- `show` — show one eval run
- `list` — list recent eval runs
- `compare` — compare run files or run a pairwise config comparison
- `breakdown` — show score bars and failure clusters for the latest run
- `generate` — generate an eval suite from a config
- `results` — inspect structured results, annotate examples, diff runs, or export a run

Useful `eval run` options:

- `--config TEXT`
- `--suite TEXT`
- `--dataset TEXT`
- `--split [train|test|all]`
- `--category TEXT`
- `--output TEXT`
- `--instruction-overrides TEXT`
- `--real-agent`
- `--require-live`
- `--json`
- `--output-format [text|json|stream-json]`

Useful `eval compare` options:

- `--config-a TEXT`
- `--config-b TEXT`
- `--left-run TEXT`
- `--right-run TEXT`
- `--dataset TEXT`
- `--split [train|test|all]`
- `--label-a TEXT`
- `--label-b TEXT`
- `--judge [metric_delta|llm_judge|human_preference]`

Useful `eval results` subcommands:

```bash
autoagent eval results --run-id eval-123 --failures
autoagent eval results diff eval-123 --other-run eval-122
autoagent eval results export eval-123 --format markdown
autoagent eval results annotate eval-123 example_001 --type note --content "Needs human review"
```

### `autoagent optimize`

Run optimization cycles to improve the current agent config.

```bash
autoagent optimize
autoagent optimize --cycles 5
autoagent optimize --continuous
autoagent optimize --mode advanced
```

Key options:

- `--cycles INTEGER`
- `--continuous`
- `--mode [standard|advanced|research]`
- `--full-auto`
- `--dry-run`
- `--max-budget-usd FLOAT`
- `--json`
- `--output-format [text|json|stream-json]`

### `autoagent deploy`

Deploy a version locally via canary, immediate release, rollback, or auto-review.

```bash
autoagent deploy canary
autoagent deploy status
autoagent deploy --config-version 5 --strategy immediate
autoagent deploy --auto-review --yes
```

Key options:

- `--config-version INTEGER`
- `--strategy [canary|immediate]`
- `--target [autoagent|cx-studio]`
- `--project TEXT`
- `--location TEXT`
- `--agent-id TEXT`
- `--snapshot TEXT`
- `--credentials TEXT`
- `--output TEXT`
- `--push / --no-push`
- `--dry-run`
- `--yes`
- `--json`
- `--output-format [text|json|stream-json]`
- `--auto-review`

### `autoagent status`

Show workspace health, versions, and recommended next steps.

```bash
autoagent status
autoagent status --json
autoagent status --verbose
```

Key options:

- `--db TEXT`
- `--configs-dir TEXT`
- `--memory-db TEXT`
- `--json`
- `--verbose`

### `autoagent doctor`

Run readiness checks for providers, data stores, eval assets, and workspace health.

```bash
autoagent doctor
autoagent doctor --fix
autoagent doctor --json
```

Key options:

- `--config TEXT`
- `--fix`
- `--json`

### `autoagent shell`

Launch the interactive shell.

```bash
autoagent shell
autoagent continue
```

---

## Secondary Commands

### `autoagent config`

Manage versioned config files.

Subcommands:

- `list`
- `show`
- `diff`
- `edit`
- `import`
- `migrate`
- `resolve`
- `rollback`
- `set-active`

Examples:

```bash
autoagent config list
autoagent config show active
autoagent config diff 1 2
autoagent config set-active 3
```

### `autoagent connect`

Import existing runtimes into a new AutoAgent workspace.

Subcommands:

- `openai-agents`
- `anthropic`
- `http`
- `transcript`

Examples:

```bash
autoagent connect openai-agents --path ./agent-project
autoagent connect anthropic --path ./claude-project
autoagent connect http --url https://agent.example.com
autoagent connect transcript --file ./conversations.jsonl --name imported-agent
```

### `autoagent instruction`

Inspect, validate, edit, generate, or migrate XML instructions.

Subcommands:

- `show`
- `validate`
- `edit`
- `generate`
- `migrate`

Examples:

```bash
autoagent instruction show
autoagent instruction validate
autoagent instruction generate --brief "refund support agent" --apply
autoagent instruction migrate
```

### `autoagent memory`

Manage `AUTOAGENT.md` project memory.

Subcommands:

- `show`
- `add`
- `edit`
- `list`
- `summarize-session`
- `where`

### `autoagent mode`

Show or set execution mode.

Subcommands:

- `show`
- `set`

Examples:

```bash
autoagent mode show
autoagent mode set mock
autoagent mode set live
autoagent mode set auto
```

### `autoagent model`

Inspect or override model preferences.

Subcommands:

- `list`
- `show`
- `set`

Examples:

```bash
autoagent model list
autoagent model show
autoagent model set proposer openai:gpt-4o
```

### `autoagent provider`

Configure and test provider profiles.

Subcommands:

- `configure`
- `list`
- `test`

Examples:

```bash
autoagent provider configure
autoagent provider list
autoagent provider test
```

### `autoagent review`

Review change cards from the optimizer.

Subcommands:

- `list`
- `show`
- `apply`
- `reject`
- `export`

Examples:

```bash
autoagent review list
autoagent review show pending
autoagent review apply pending
autoagent review reject latest
autoagent review export pending
```

### `autoagent template`

List and apply bundled starter templates.

Subcommands:

- `list`
- `apply`

Examples:

```bash
autoagent template list
autoagent template apply customer-support
```

---

## Advanced Commands

Run `autoagent advanced` to see these in the CLI.

| Command | Description |
|---------|-------------|
| `adk` | Google Agent Development Kit integration |
| `autofix` | AutoFix Copilot workflows |
| `benchmark` | Run benchmark suites |
| `build-inspect` | Inspect build artifacts |
| `build-show` | Deprecated alias for `autoagent build show` |
| `changes` | Compatibility aliases for reviewable change cards |
| `compare` | Compare configs, eval runs, and candidate versions |
| `context` | Context Engineering Workbench |
| `continue` | Resume the most recent shell session |
| `curriculum` | Self-play curriculum generation |
| `cx` | Google Cloud CX / Dialogflow CX integration |
| `dataset` | Dataset management |
| `demo` | Demo and presentation commands |
| `diagnose` | Failure diagnosis workflows |
| `edit` | Natural-language config edits |
| `experiment` | Optimization experiment history |
| `explain` | Plain-English agent summary |
| `full-auto` | Full-auto optimization mode |
| `import` | Compatibility aliases for imports |
| `improve` | Deprecated alias; use `optimize` |
| `init` | Deprecated alias; use `new` |
| `intelligence` | Transcript intelligence workflows |
| `judges` | Judge Ops workflows |
| `logs` | Conversation log browsing |
| `loop` | Deprecated loop command; use `optimize --continuous` |
| `mcp` | MCP client and runtime setup |
| `mcp-server` | Start the MCP server |
| `outcomes` | Outcome and business metric ingestion |
| `pause` | Pause the optimization loop |
| `permissions` | Workspace permission mode controls |
| `pin` | Lock a config surface |
| `policy` | Policy optimization artifacts |
| `pref` | Preference collection/export |
| `quickstart` | Run the one-command golden path |
| `registry` | Skills, policies, tools, and handoffs registry |
| `reject` | Reject and roll back an experiment |
| `release` | Signed release objects |
| `replay` | Optimization history replay |
| `resume` | Resume a paused loop |
| `rl` | Policy optimization commands |
| `run` | Legacy run command group |
| `runbook` | Runbook management |
| `scorer` | Natural-language scorer workflows |
| `server` | Start the API server + web console |
| `session` | Shell session management |
| `ship` | Deprecated alias; use `deploy --auto-review` |
| `skill` | Skill management |
| `trace` | Trace analysis and blame maps |
| `unpin` | Remove a surface lock |
| `usage` | Eval/optimize cost and budget reporting |

---

## Common Power Commands

```bash
autoagent advanced
autoagent quickstart
autoagent compare candidates
autoagent eval results export eval-123 --format markdown
autoagent mcp status
autoagent cx auth
autoagent cx list --project PROJECT --location us-central1
```

---

## Deprecated Aliases

These older commands still exist as compatibility aliases, but the current docs use the newer forms.

| Old command | Current command |
|-------------|-----------------|
| `autoagent init` | `autoagent new` |
| `autoagent improve` | `autoagent optimize` |
| `autoagent loop` | `autoagent optimize --continuous` |
| `autoagent ship` | `autoagent deploy --auto-review` |

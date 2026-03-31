# AutoAgent Quick Start

Get from clone to a working AutoAgent workspace in a few minutes.

## Prerequisites

- Python 3.11+
- Node.js 20+ if you want the web UI or local frontend dev tools

## Install

```bash
git clone https://github.com/andrewhuot/autoagent-vnextcc.git
cd autoagent-vnextcc
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 1. Create a workspace

```bash
autoagent new my-agent --template customer-support --demo
cd my-agent
```

Why `--demo`?

- it seeds reviewable demo data
- it makes the review and deploy surfaces interesting on a brand-new workspace
- it keeps the first walkthrough reproducible even before you connect a live runtime

## 2. Inspect the default XML instruction

New workspaces start with an XML root instruction in `prompts.root`.

```bash
autoagent instruction show
autoagent instruction validate
```

If you want to replace the draft from a short brief:

```bash
autoagent instruction generate --brief "customer support agent for order tracking and refunds" --apply
autoagent instruction validate
```

## 3. Build the first config

```bash
autoagent build "customer support agent for order tracking, refunds, and cancellations"
```

This stages a new config, generates build artifacts, and writes starter eval cases you can run immediately.

## 4. Run evals

```bash
autoagent eval run
```

Check the latest run again any time with:

```bash
autoagent eval show latest
```

## 5. Optimize

```bash
autoagent optimize --cycles 1
```

Two normal outcomes:

- AutoAgent proposes and evaluates a change
- AutoAgent says `Latest eval passed; no optimization needed.` if the current workspace is already healthy enough for that cycle

Both outcomes are valid first-run behavior.

## 6. Review and deploy

To inspect the current review queue:

```bash
autoagent review list
```

To apply seeded review cards automatically and canary the latest version:

```bash
autoagent deploy --auto-review --yes
```

## What next?

- `autoagent status` — see workspace health and next recommended commands
- `autoagent build show latest` — inspect the latest build artifact
- `autoagent instruction edit` — open the active XML instruction in your editor
- `autoagent instruction migrate` — convert an older plain-text instruction to XML
- `autoagent shell` — open the interactive shell
- `autoagent advanced` — see the broader command surface
- [XML Instructions](xml-instructions.md) — full XML authoring and override workflow
- [Detailed Guide](DETAILED_GUIDE.md) — full CLI walkthrough
- [UI Quick Start](UI_QUICKSTART_GUIDE.md) — browser walkthrough

## Troubleshooting

**`autoagent: command not found`**

Activate the virtualenv again:

```bash
source .venv/bin/activate
which autoagent
```

**`No workspace found`**

You are outside a workspace directory. Either `cd` into the workspace you created, or create one with:

```bash
autoagent new my-agent --template customer-support
```

**Provider credentials missing**

That is okay. AutoAgent auto-detects mock mode when no API keys are set. To switch to live providers later:

```bash
autoagent provider configure
autoagent provider test
autoagent mode set live
```

**`No candidate config version available to deploy`**

Stage or accept a version first:

```bash
autoagent build "Describe your agent"
```

or

```bash
autoagent review apply pending
```

or

```bash
autoagent optimize --cycles 1
```

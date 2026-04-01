# CX Agent Studio Integration Guide

This page is kept as a compatibility pointer for older links and older naming.

For the current workflow, use:

- [CX Studio Integration](cx-studio-integration.md)

## Current Product Reality

In the current AgentLab repo, the supported CX workflow is the `agentlab cx` CLI plus the `/cx/studio` web route.

That workflow covers:

- credential validation
- agent listing
- import
- diff
- export preview
- sync
- deploy and widget helpers

Common commands:

```bash
agentlab cx auth
agentlab cx list --project PROJECT --location global
agentlab cx import AGENT_ID --project PROJECT --location global
agentlab cx diff AGENT_ID --project PROJECT --location global
agentlab cx export AGENT_ID --project PROJECT --location global --dry-run
agentlab cx sync AGENT_ID --project PROJECT --location global
agentlab cx status --project PROJECT --location global --agent AGENT_ID
```

## Naming Note

Older docs in this repo sometimes tried to draw a hard line between "CX Agent Studio" and "Dialogflow CX."

For operators using AgentLab today, that distinction is less useful than following the actual supported workflow:

- use `agentlab cx ...`
- use `/cx/studio`
- use the current CX route family under `/api/cx/*`

The full current guide documents the supported flags, files, and round-trip behavior.

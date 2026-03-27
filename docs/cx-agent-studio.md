# CX Agent Studio Integration Guide

This guide describes how to use AutoAgent VNextCC with Google Cloud CX Agent Studio (Customer Engagement AI - Conversational Agents).

**Important**: CX Agent Studio is NOT Dialogflow CX. They are separate products with different APIs:
- CX Agent Studio: `ces.googleapis.com` API, uses apps/agents/tools/examples
- Dialogflow CX: `dialogflow.googleapis.com` API, uses flows/intents/pages

Current state:
- Full CX integration is **implemented and functional**
- Import CX agents into AutoAgent format
- Export optimized configs back to CX
- Deploy directly to CX environments
- Generate chat widgets for CX agents

Limitations:
- No automatic conversation sync from CX (manual conversation import required)
- Limited bidirectional sync (CX UI edits won't auto-merge with AutoAgent changes)
- HTTP/SSE mode not yet implemented (stdio mode only for some features)

## Who This Is For

Use this guide if you:
- already run an agent in CX Agent Studio
- want AutoAgent to analyze quality and propose improvements
- need controlled rollout and rollback semantics in a regulated environment

## Integration Modes

Start with the smallest-risk mode and move forward only after validation.

## Mode 1: Read-Only Analytics (recommended first)

- Pull conversation transcripts and metadata from CX
- Map data into AutoAgent conversation schema
- Run observer/evals/optimizer in recommendation-only mode
- No automatic write-back to CX

Best for first production pilots.

## Mode 2: Human-Approved Suggest + Apply

- AutoAgent proposes config changes in AutoAgent YAML
- Human approves in a review surface
- Adapter applies approved changes to CX via API

Best for teams that want velocity plus explicit approval controls.

## Mode 3: Controlled Auto-Apply + Canary

- AutoAgent can apply changes automatically under policy
- CX experiments or traffic split handles canary exposure
- Auto rollback on degraded success/safety outcomes

Best for mature teams with strong observability and change governance.

## Target Architecture

```text
┌─────────────────────────────┐      ┌──────────────────────────────────┐
│ CX Agent Studio (GCP)        │      │ AutoAgent VNextCC                │
│ - Apps / Agents / Tools     │<---->│ CX Adapter Layer                 │
│ - Conversations             │      │ - Conversation ingest            │
│ - Experiments               │      │ - Config translator              │
└──────────────┬──────────────┘      │ - Deploy bridge                  │
               │                     └──────────────┬───────────────────┘
               │                                    │
               │                           ┌────────▼────────┐
               │                           │ Observer/Evals  │
               │                           │ Optimizer/Gates │
               │                           └────────┬────────┘
               │                                    │
               └────────────────────────────┬───────▼─────────────┐
                                            │ Versioning + Canary  │
                                            │ + Audit trail        │
                                            └──────────────────────┘
```

## Required Google Cloud APIs

- CX Agent Studio API (ces.googleapis.com/v1)
- Conversational Agents API
- Customer Engagement AI APIs
- Cloud Logging API (optional, for enriched analytics)

## IAM and Security Model

Use a dedicated service account per environment (`dev`, `staging`, `prod`).

Recommended minimum roles (exact role names vary by org policy):
- read CX agent resources
- read conversation transcripts/metadata
- create/update experiments (if canary mode enabled)
- update flows/pages/intents only in approved environments

Hard requirements:
- store credentials in Secret Manager, not in repo
- explicit allowlist for project + location + agent IDs
- full audit log for every write-back operation

## Data Mapping Strategy

AutoAgent operates on a normalized conversation record shape. Build a deterministic mapper from CX conversation/turn payloads.

## Conversation Mapping

| CX source | AutoAgent field | Notes |
|---|---|---|
| Conversation resource name | `conversation_id` | Keep stable ID for traceability |
| Session identifier | `session_id` | Required for grouping |
| User utterance text | `user_message` | Latest or turn-scoped, depending on mode |
| Agent response text | `agent_response` | Flatten response variants deterministically |
| Webhook/tool metadata | `tool_calls` | Preserve payload for debugging |
| Derived latency | `latency_ms` | Compute from timestamps if needed |
| Token estimate | `token_count` | Optional estimate if raw token count unavailable |
| Outcome signal | `outcome` | Map to `success|fail|error|abandon` |
| Route/page/flow | `specialist_used` | Useful for routing analysis |
| Safety indicators | `safety_flags` | Normalize to a string list |
| Event timestamp | `timestamp` | Unix epoch in seconds |

## Config Mapping

AutoAgent config fields do not map 1:1 with CX resources. Use an adapter with explicit translation rules and validation.

| AutoAgent concept | Typical CX source |
|---|---|
| Routing rules | Flows, pages, transition routes, intent routes |
| Prompt/system text | Flow/page fulfillment text and generative settings |
| Tool hooks | Webhooks and integrations |
| Thresholds | NLU confidence / route settings |

Recommendation:
- keep a reversible mapping artifact for each sync
- reject ambiguous transforms instead of guessing
- require human review for destructive route changes

## Suggested Adapter Interfaces

Use three explicit components:

1. `CXConversationAdapter`
- incremental ingest by timestamp/watermark
- idempotent writes into `ConversationStore`

2. `CXConfigAdapter`
- `from_cx(...) -> autoagent_config`
- `to_cx(...) -> set of API operations`

3. `CXDeployBridge`
- apply approved config patch
- trigger experiment/canary
- report rollout status back to AutoAgent

## Rollout Plan

## Phase 1: Read-Only Validation

Deliverables:
- conversation ingest job
- health dashboard from real CX traffic
- optimizer suggestions with no write-back

Acceptance criteria:
- deterministic mapping for >= 95% of sampled conversations
- no data loss across repeated sync windows
- useful failure buckets for routing/safety/tooling

## Phase 2: Human-Approved Write-Back

Deliverables:
- proposed changes rendered as reviewable diff
- approval action that triggers adapter apply
- rollback action from same control plane

Acceptance criteria:
- every write has audit record and operator identity
- roll-forward and rollback tested in staging
- failed applies are recoverable without manual DB edits

## Phase 3: Managed Canary Automation

Deliverables:
- traffic split or CX experiment orchestration
- automated verdict logic (promote/rollback)
- policy guardrails (safety floor, min sample size, timeout)

Acceptance criteria:
- no unsafe promotion when safety gate fails
- measurable regression detection under real traffic
- on-call runbook validated by game day

## Operational Guardrails

Before enabling auto-apply in production:
- set explicit minimum sample sizes for canary verdicts
- enforce safety hard gate at both eval and runtime layers
- block multi-surface edits in one release when confidence is low
- require rollback path verification in every deploy window

## Recommended Telemetry

Capture these dimensions for each candidate:
- baseline vs canary success rate
- safety incident rate
- latency distribution (not just average)
- fallback/escalation rate
- route-level failure concentration

## Current CLI Commands

The following CX integration commands are available now:

```bash
# List all CX agents in a project
autoagent cx list --project PROJECT --location LOCATION [--credentials PATH]

# Import a CX agent into AutoAgent format
autoagent cx import --project PROJECT --location LOCATION --agent-id AGENT_ID \
  --output-dir DIR [--credentials PATH] [--include-test-cases]

# Export optimized config back to CX
autoagent cx export --project PROJECT --location LOCATION --agent-id AGENT_ID \
  --config-path CONFIG --snapshot-path SNAPSHOT [--credentials PATH] [--dry-run]

# Deploy to a CX environment
autoagent cx deploy --project PROJECT --location LOCATION --agent-id AGENT_ID \
  --environment ENV [--credentials PATH]

# Check CX agent status
autoagent cx status --project PROJECT --location LOCATION --agent-id AGENT_ID \
  [--credentials PATH]

# Generate a chat widget for a CX agent
autoagent cx widget --project PROJECT --location LOCATION --agent-id AGENT_ID \
  [--title TITLE] [--color COLOR] [--output-path PATH]
```

## Non-Goals for Initial Release

- full bidirectional conflict-free merge between CX UI edits and AutoAgent edits
- automatic schema migration of all custom CX artifacts
- cross-region active/active orchestration

Keep initial scope narrow and auditable. Expand after stable production evidence.


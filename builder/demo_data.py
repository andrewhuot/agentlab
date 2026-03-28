"""Rich synthetic demo data for the Builder Workspace.

Populates two complete agent projects with realistic conversation histories,
specialist handoffs, artifacts, eval bundles, trace bookmarks, proposals,
approvals, and release candidates. Call seed_builder_demo() to load all data
into a BuilderStore instance.

Story arc:
  Airline Customer Service Agent — full build/eval/ship lifecycle
  E-Commerce Returns Bot          — build with guardrail hardening, then deploy

Both projects tell a coherent end-to-end story that showcases every
first-class Builder object type.
"""

from __future__ import annotations

import time

from builder.store import BuilderStore
from builder.types import (
    ApprovalRequest,
    ApprovalScope,
    ApprovalStatus,
    ArtifactRef,
    ArtifactType,
    BuilderProject,
    BuilderProposal,
    BuilderSession,
    BuilderTask,
    EvalBundle,
    ExecutionMode,
    PrivilegedAction,
    ReleaseCandidate,
    RiskLevel,
    SpecialistRole,
    TaskStatus,
    TraceBookmark,
)

# ---------------------------------------------------------------------------
# Reference timestamps — demo data is set ~1 week before now so it looks like
# a real project history. All times are seconds since UNIX epoch.
# ---------------------------------------------------------------------------
_BASE = time.time() - 7 * 24 * 3600  # 7 days ago


def _t(offset_hours: float) -> float:
    return _BASE + offset_hours * 3600


# ---------------------------------------------------------------------------
# Fixed IDs (reproducible, recognisable in the UI)
# ---------------------------------------------------------------------------

# --- Airline project ---
AIRLINE_PROJECT_ID = "demo-proj-airline-cs"
AIRLINE_SESSION_1_ID = "demo-sess-airline-01"
AIRLINE_SESSION_2_ID = "demo-sess-airline-02"
AIRLINE_SESSION_3_ID = "demo-sess-airline-03"

# --- E-Commerce project ---
ECOM_PROJECT_ID = "demo-proj-ecom-returns"
ECOM_SESSION_1_ID = "demo-sess-ecom-01"
ECOM_SESSION_2_ID = "demo-sess-ecom-02"
ECOM_SESSION_3_ID = "demo-sess-ecom-03"


# ===========================================================================
# AIRLINE CUSTOMER SERVICE AGENT — full lifecycle
# ===========================================================================

def _airline_project() -> BuilderProject:
    p = BuilderProject()
    p.project_id = AIRLINE_PROJECT_ID
    p.name = "Airline Customer Service Agent"
    p.description = (
        "AI agent for SkyLink Airlines handling flight rebooking, seat upgrades, "
        "baggage claim questions, and loyalty programme inquiries."
    )
    p.root_path = "agents/airline-cs"
    p.master_instruction = (
        "You are SkyLink Airlines virtual assistant. Always verify the passenger "
        "PNR before taking any booking action. Offer compensation proactively "
        "for delays over 3 hours. Never store raw payment card numbers."
    )
    p.knowledge_files = [
        "docs/airline-policy-v3.pdf",
        "docs/baggage-allowance-table.md",
        "docs/loyalty-tier-benefits.md",
    ]
    p.buildtime_skills = ["adk_graph_builder", "tool_scaffolder", "eval_harness"]
    p.runtime_skills = ["booking_lookup", "seat_inventory", "flight_status", "rebooking"]
    p.deployment_targets = ["gcp-us-central1-prod", "gcp-eu-west1-prod"]
    p.preferred_models = {
        "orchestrator": "claude-sonnet-4-6",
        "tool_engineer": "claude-sonnet-4-6",
    }
    p.tags = ["airline", "customer-service", "production"]
    p.created_at = _t(0)
    p.updated_at = _t(155)
    return p


def _airline_sessions() -> list[BuilderSession]:
    s1 = BuilderSession()
    s1.session_id = AIRLINE_SESSION_1_ID
    s1.project_id = AIRLINE_PROJECT_ID
    s1.title = "Act 1–2: Requirements & Architecture"
    s1.mode = ExecutionMode.DRAFT
    s1.active_specialist = SpecialistRole.REQUIREMENTS_ANALYST
    s1.status = "closed"
    s1.created_at = _t(0)
    s1.updated_at = _t(48)
    s1.message_count = 14

    s2 = BuilderSession()
    s2.session_id = AIRLINE_SESSION_2_ID
    s2.project_id = AIRLINE_PROJECT_ID
    s2.title = "Act 2–3: Tool Implementation & Evals"
    s2.mode = ExecutionMode.APPLY
    s2.active_specialist = SpecialistRole.TOOL_ENGINEER
    s2.status = "closed"
    s2.created_at = _t(48)
    s2.updated_at = _t(120)
    s2.message_count = 22

    s3 = BuilderSession()
    s3.session_id = AIRLINE_SESSION_3_ID
    s3.project_id = AIRLINE_PROJECT_ID
    s3.title = "Act 4–5: Optimize & Ship"
    s3.mode = ExecutionMode.APPLY
    s3.active_specialist = SpecialistRole.RELEASE_MANAGER
    s3.status = "open"
    s3.created_at = _t(120)
    s3.updated_at = _t(155)
    s3.message_count = 18

    return [s1, s2, s3]


def _airline_tasks() -> list[BuilderTask]:
    tasks = []

    # --- Session 1 tasks (requirements + architecture) ---
    t1 = BuilderTask()
    t1.task_id = "demo-task-airline-01"
    t1.session_id = AIRLINE_SESSION_1_ID
    t1.project_id = AIRLINE_PROJECT_ID
    t1.title = "Gather requirements for airline CS agent"
    t1.description = (
        "User request: Build an airline customer service agent that handles flight "
        "rebooking, seat upgrades, baggage claim questions, and loyalty programme inquiries."
    )
    t1.mode = ExecutionMode.DRAFT
    t1.status = TaskStatus.COMPLETED
    t1.active_specialist = SpecialistRole.REQUIREMENTS_ANALYST
    t1.created_at = _t(0.1)
    t1.updated_at = _t(2)
    t1.started_at = _t(0.2)
    t1.completed_at = _t(2)
    t1.elapsed_seconds = 6480
    t1.progress = 100
    t1.token_count = 12400
    t1.cost_usd = 0.19
    tasks.append(t1)

    t2 = BuilderTask()
    t2.task_id = "demo-task-airline-02"
    t2.session_id = AIRLINE_SESSION_1_ID
    t2.project_id = AIRLINE_PROJECT_ID
    t2.title = "Design ADK agent graph"
    t2.description = (
        "Design the multi-agent graph: orchestrator → intent_router → "
        "booking_subagent / baggage_subagent / loyalty_subagent."
    )
    t2.mode = ExecutionMode.DRAFT
    t2.status = TaskStatus.COMPLETED
    t2.active_specialist = SpecialistRole.ADK_ARCHITECT
    t2.created_at = _t(2.1)
    t2.updated_at = _t(6)
    t2.started_at = _t(2.2)
    t2.completed_at = _t(6)
    t2.elapsed_seconds = 13680
    t2.progress = 100
    t2.token_count = 18700
    t2.cost_usd = 0.31
    tasks.append(t2)

    # --- Session 2 tasks (tool implementation) ---
    t3 = BuilderTask()
    t3.task_id = "demo-task-airline-03"
    t3.session_id = AIRLINE_SESSION_2_ID
    t3.project_id = AIRLINE_PROJECT_ID
    t3.title = "Implement booking_lookup_tool"
    t3.description = (
        "Create booking_lookup_tool that fetches PNR, passenger name, itinerary, "
        "and seat assignment from the Sabre GDS REST API."
    )
    t3.mode = ExecutionMode.APPLY
    t3.status = TaskStatus.COMPLETED
    t3.active_specialist = SpecialistRole.TOOL_ENGINEER
    t3.created_at = _t(48.5)
    t3.updated_at = _t(51)
    t3.started_at = _t(48.6)
    t3.completed_at = _t(51)
    t3.elapsed_seconds = 8640
    t3.progress = 100
    t3.token_count = 21000
    t3.cost_usd = 0.34
    tasks.append(t3)

    t4 = BuilderTask()
    t4.task_id = "demo-task-airline-04"
    t4.session_id = AIRLINE_SESSION_2_ID
    t4.project_id = AIRLINE_PROJECT_ID
    t4.title = "Implement seat_inventory_tool"
    t4.description = (
        "Implement seat_inventory_tool returning available seats by cabin class. "
        "Must include the seat_map field so the frontend can render a visual picker."
    )
    t4.mode = ExecutionMode.APPLY
    t4.status = TaskStatus.COMPLETED
    t4.active_specialist = SpecialistRole.TOOL_ENGINEER
    t4.created_at = _t(51.1)
    t4.updated_at = _t(55)
    t4.started_at = _t(51.2)
    t4.completed_at = _t(55)
    t4.elapsed_seconds = 13968
    t4.progress = 100
    t4.token_count = 19800
    t4.cost_usd = 0.32
    tasks.append(t4)

    t5 = BuilderTask()
    t5.task_id = "demo-task-airline-05"
    t5.session_id = AIRLINE_SESSION_2_ID
    t5.project_id = AIRLINE_PROJECT_ID
    t5.title = "Add rebooking skill & compensation offer skill"
    t5.description = (
        "Author two runtime skills: rebooking_skill (orchestrates lookup → check "
        "alternatives → confirm) and compensation_offer_skill (calculates voucher "
        "amount based on delay duration and loyalty tier)."
    )
    t5.mode = ExecutionMode.APPLY
    t5.status = TaskStatus.COMPLETED
    t5.active_specialist = SpecialistRole.SKILL_AUTHOR
    t5.created_at = _t(55.1)
    t5.updated_at = _t(62)
    t5.started_at = _t(55.2)
    t5.completed_at = _t(62)
    t5.elapsed_seconds = 24840
    t5.progress = 100
    t5.token_count = 31500
    t5.cost_usd = 0.51
    tasks.append(t5)

    t6 = BuilderTask()
    t6.task_id = "demo-task-airline-06"
    t6.session_id = AIRLINE_SESSION_2_ID
    t6.project_id = AIRLINE_PROJECT_ID
    t6.title = "Add PII filter and inappropriate-content guardrails"
    t6.description = (
        "Implement pii_filter guardrail (mask credit card numbers, passport IDs) "
        "and inappropriate_content guardrail (block hate speech and off-topic requests)."
    )
    t6.mode = ExecutionMode.APPLY
    t6.status = TaskStatus.COMPLETED
    t6.active_specialist = SpecialistRole.GUARDRAIL_AUTHOR
    t6.created_at = _t(62.1)
    t6.updated_at = _t(67)
    t6.started_at = _t(62.2)
    t6.completed_at = _t(67)
    t6.elapsed_seconds = 17640
    t6.progress = 100
    t6.token_count = 14200
    t6.cost_usd = 0.23
    tasks.append(t6)

    t7 = BuilderTask()
    t7.task_id = "demo-task-airline-07"
    t7.session_id = AIRLINE_SESSION_2_ID
    t7.project_id = AIRLINE_PROJECT_ID
    t7.title = "Run baseline eval suite"
    t7.description = "Execute 120-conversation eval suite to establish baseline quality metrics."
    t7.mode = ExecutionMode.APPLY
    t7.status = TaskStatus.COMPLETED
    t7.active_specialist = SpecialistRole.EVAL_AUTHOR
    t7.created_at = _t(67.1)
    t7.updated_at = _t(74)
    t7.started_at = _t(67.2)
    t7.completed_at = _t(74)
    t7.elapsed_seconds = 24840
    t7.progress = 100
    t7.token_count = 44100
    t7.cost_usd = 0.71
    tasks.append(t7)

    # --- Session 3 tasks (optimize & ship) ---
    t8 = BuilderTask()
    t8.task_id = "demo-task-airline-08"
    t8.session_id = AIRLINE_SESSION_3_ID
    t8.project_id = AIRLINE_PROJECT_ID
    t8.title = "Investigate seat_inventory_tool failures in traces"
    t8.description = (
        "Trace analyst investigating 23 eval failures where seat_inventory_tool "
        "returned a flat list instead of a seat_map dict, causing the booking_subagent "
        "to crash with a KeyError."
    )
    t8.mode = ExecutionMode.APPLY
    t8.status = TaskStatus.COMPLETED
    t8.active_specialist = SpecialistRole.TRACE_ANALYST
    t8.created_at = _t(120.1)
    t8.updated_at = _t(124)
    t8.started_at = _t(120.2)
    t8.completed_at = _t(124)
    t8.elapsed_seconds = 13968
    t8.progress = 100
    t8.token_count = 28900
    t8.cost_usd = 0.46
    tasks.append(t8)

    t9 = BuilderTask()
    t9.task_id = "demo-task-airline-09"
    t9.session_id = AIRLINE_SESSION_3_ID
    t9.project_id = AIRLINE_PROJECT_ID
    t9.title = "Fix seat_inventory_tool response schema"
    t9.description = (
        "Apply fix: wrap seat list in {seat_map: [...]} envelope; add schema "
        "validation with pydantic; add unit test for empty-flight edge case."
    )
    t9.mode = ExecutionMode.APPLY
    t9.status = TaskStatus.COMPLETED
    t9.active_specialist = SpecialistRole.TOOL_ENGINEER
    t9.created_at = _t(124.1)
    t9.updated_at = _t(127)
    t9.started_at = _t(124.2)
    t9.completed_at = _t(127)
    t9.elapsed_seconds = 10440
    t9.progress = 100
    t9.token_count = 17600
    t9.cost_usd = 0.28
    tasks.append(t9)

    t10 = BuilderTask()
    t10.task_id = "demo-task-airline-10"
    t10.session_id = AIRLINE_SESSION_3_ID
    t10.project_id = AIRLINE_PROJECT_ID
    t10.title = "Re-run eval suite post-fix"
    t10.description = "Re-run 120-conversation eval suite with fixed seat_inventory_tool."
    t10.mode = ExecutionMode.APPLY
    t10.status = TaskStatus.COMPLETED
    t10.active_specialist = SpecialistRole.EVAL_AUTHOR
    t10.created_at = _t(127.1)
    t10.updated_at = _t(134)
    t10.started_at = _t(127.2)
    t10.completed_at = _t(134)
    t10.elapsed_seconds = 24840
    t10.progress = 100
    t10.token_count = 44100
    t10.cost_usd = 0.71
    tasks.append(t10)

    t11 = BuilderTask()
    t11.task_id = "demo-task-airline-11"
    t11.session_id = AIRLINE_SESSION_3_ID
    t11.project_id = AIRLINE_PROJECT_ID
    t11.title = "Prepare release candidate v1.0.0"
    t11.description = (
        "Bundle all approved artifacts into RC v1.0.0. Generate changelog. "
        "Request deployment approval for gcp-us-central1-prod."
    )
    t11.mode = ExecutionMode.APPLY
    t11.status = TaskStatus.COMPLETED
    t11.active_specialist = SpecialistRole.RELEASE_MANAGER
    t11.created_at = _t(134.1)
    t11.updated_at = _t(138)
    t11.started_at = _t(134.2)
    t11.completed_at = _t(138)
    t11.elapsed_seconds = 13968
    t11.progress = 100
    t11.token_count = 9800
    t11.cost_usd = 0.16
    tasks.append(t11)

    t12 = BuilderTask()
    t12.task_id = "demo-task-airline-12"
    t12.session_id = AIRLINE_SESSION_3_ID
    t12.project_id = AIRLINE_PROJECT_ID
    t12.title = "Awaiting deployment approval"
    t12.description = "RC v1.0.0 staged for gcp-us-central1-prod. Waiting for human sign-off."
    t12.mode = ExecutionMode.APPLY
    t12.status = TaskStatus.PAUSED
    t12.active_specialist = SpecialistRole.RELEASE_MANAGER
    t12.created_at = _t(138.1)
    t12.updated_at = _t(155)
    t12.started_at = _t(138.2)
    t12.paused_at = _t(138.5)
    t12.progress = 90
    t12.current_step = "Waiting for deployment approval"
    t12.eta_seconds = 3600
    t12.token_count = 2100
    t12.cost_usd = 0.03
    tasks.append(t12)

    return tasks


def _airline_proposals() -> list[BuilderProposal]:
    proposals = []

    p1 = BuilderProposal()
    p1.proposal_id = "demo-prop-airline-01"
    p1.task_id = "demo-task-airline-01"
    p1.session_id = AIRLINE_SESSION_1_ID
    p1.project_id = AIRLINE_PROJECT_ID
    p1.goal = "Establish core requirements for SkyLink Airlines CS Agent"
    p1.assumptions = [
        "Sabre GDS REST API is available and credentials provided via env vars",
        "PNR format is alphanumeric 6-char (e.g. ABC123)",
        "Loyalty tiers: Blue, Silver, Gold, Platinum",
        "Agent will be deployed in GCP Cloud Run, max 2048 MB RAM",
        "Response SLA: P95 < 3 seconds end-to-end",
    ]
    p1.targeted_surfaces = ["requirements", "project_config"]
    p1.expected_impact = (
        "Clear requirements doc reduces ambiguity and prevents rework. "
        "Unblocks architect to start graph design immediately."
    )
    p1.risk_level = RiskLevel.LOW
    p1.steps = [
        {"step": 1, "action": "Interview user about booking workflow constraints"},
        {"step": 2, "action": "Document PNR validation rules"},
        {"step": 3, "action": "Confirm GDS API rate limits and authentication method"},
        {"step": 4, "action": "Write requirements.md to project knowledge files"},
    ]
    p1.status = "approved"
    p1.accepted = True
    p1.created_at = _t(0.3)
    p1.updated_at = _t(1.2)
    proposals.append(p1)

    p2 = BuilderProposal()
    p2.proposal_id = "demo-prop-airline-02"
    p2.task_id = "demo-task-airline-02"
    p2.session_id = AIRLINE_SESSION_1_ID
    p2.project_id = AIRLINE_PROJECT_ID
    p2.goal = "Design 3-subagent ADK graph with intent router"
    p2.assumptions = [
        "orchestrator agent handles routing; does NOT call tools directly",
        "booking_subagent is the only agent with write access to GDS",
        "baggage_subagent and loyalty_subagent are read-only",
        "Subagents communicate via structured handoff dicts, not raw text",
    ]
    p2.targeted_artifacts = ["adk_graph_diff"]
    p2.targeted_surfaces = ["agent_graph", "orchestrator_config"]
    p2.expected_impact = (
        "Clean separation of concerns reduces tool cross-contamination. "
        "Predictable routing improves eval coverage from 60% → 85%."
    )
    p2.risk_level = RiskLevel.MEDIUM
    p2.required_approvals = ["source_write"]
    p2.steps = [
        {"step": 1, "action": "Draft graph YAML with 4 nodes (orchestrator + 3 subagents)"},
        {"step": 2, "action": "Define handoff schemas between nodes"},
        {"step": 3, "action": "Add graph to ADK project with adk_graph_diff artifact"},
    ]
    p2.status = "approved"
    p2.accepted = True
    p2.created_at = _t(2.3)
    p2.updated_at = _t(5.1)
    proposals.append(p2)

    p3 = BuilderProposal()
    p3.proposal_id = "demo-prop-airline-03"
    p3.task_id = "demo-task-airline-09"
    p3.session_id = AIRLINE_SESSION_3_ID
    p3.project_id = AIRLINE_PROJECT_ID
    p3.goal = "Fix seat_inventory_tool: wrap response in seat_map envelope"
    p3.assumptions = [
        "All callers of seat_inventory_tool expect a dict with 'seat_map' key",
        "Existing callers will break if schema changes are not backwards-compatible",
        "Pydantic v2 is already installed in the project environment",
    ]
    p3.targeted_artifacts = ["source_diff"]
    p3.targeted_surfaces = ["agents/airline-cs/tools/seat_inventory.py"]
    p3.expected_impact = (
        "Fixes 23 eval failures. Expected trajectory quality: 0.61 → 0.84. "
        "Closes the only P0 bug blocking v1.0.0 release."
    )
    p3.risk_level = RiskLevel.MEDIUM
    p3.required_approvals = ["source_write"]
    p3.steps = [
        {"step": 1, "action": "Update _build_response() to return {'seat_map': seats, 'cabin': cabin}"},
        {"step": 2, "action": "Add SeatInventoryResponse pydantic model for schema validation"},
        {"step": 3, "action": "Add unit test: test_empty_flight_returns_empty_seat_map()"},
        {"step": 4, "action": "Run full test suite to confirm no regressions"},
    ]
    p3.status = "approved"
    p3.accepted = True
    p3.revision_count = 1
    p3.revision_comments = [
        "Please also add a unit test for the empty-flight edge case before approving."
    ]
    p3.created_at = _t(124.2)
    p3.updated_at = _t(126.5)
    proposals.append(p3)

    p4 = BuilderProposal()
    p4.proposal_id = "demo-prop-airline-04"
    p4.task_id = "demo-task-airline-11"
    p4.session_id = AIRLINE_SESSION_3_ID
    p4.project_id = AIRLINE_PROJECT_ID
    p4.goal = "Package and validate release candidate v1.0.0"
    p4.assumptions = [
        "All P0 and P1 bugs are resolved",
        "Trajectory quality ≥ 0.80 hard gate has been met (actual: 0.84)",
        "Deployment target gcp-us-central1-prod is accessible",
        "Rollback plan: revert to previous Cloud Run revision in <5 min",
    ]
    p4.targeted_artifacts = ["release"]
    p4.targeted_surfaces = ["deployment_config", "changelog"]
    p4.expected_impact = (
        "Ships SkyLink Airlines CS Agent to production with confidence. "
        "Hard gate passed. Eval trajectory quality 0.84 vs 0.80 threshold."
    )
    p4.risk_level = RiskLevel.HIGH
    p4.required_approvals = ["deployment"]
    p4.steps = [
        {"step": 1, "action": "Bundle approved artifacts into RC v1.0.0"},
        {"step": 2, "action": "Generate structured changelog from task history"},
        {"step": 3, "action": "Attach eval bundle eval-airline-02 to release"},
        {"step": 4, "action": "Create deployment approval request for gcp-us-central1-prod"},
    ]
    p4.status = "pending"
    p4.created_at = _t(134.3)
    p4.updated_at = _t(135.0)
    proposals.append(p4)

    return proposals


def _airline_artifacts() -> list[ArtifactRef]:
    artifacts = []

    # --- PLAN artifact (requirements) ---
    a1 = ArtifactRef()
    a1.artifact_id = "demo-art-airline-01"
    a1.task_id = "demo-task-airline-01"
    a1.session_id = AIRLINE_SESSION_1_ID
    a1.project_id = AIRLINE_PROJECT_ID
    a1.artifact_type = ArtifactType.PLAN
    a1.title = "SkyLink Airlines CS Agent — Requirements Plan"
    a1.summary = (
        "Four functional areas: flight rebooking, seat upgrades, baggage claims, "
        "loyalty inquiries. Sabre GDS integration. P95 SLA 3s."
    )
    a1.payload = {
        "goals": [
            "Handle flight rebooking end-to-end without human intervention for standard cases",
            "Surface seat upgrade offers based on availability and loyalty tier",
            "Answer baggage allowance and lost-baggage claim questions",
            "Provide loyalty point balance and tier status lookups",
        ],
        "non_goals": [
            "Payment processing (handled by separate PCI system)",
            "Visa and passport verification",
            "Group bookings over 9 passengers",
        ],
        "constraints": [
            "Must use Sabre GDS REST API v3.5",
            "PII masking required before any logging",
            "Max 3 GDS API calls per conversation turn",
        ],
        "milestones": [
            {"id": "M1", "name": "Graph design approved", "eta_hours": 6},
            {"id": "M2", "name": "All tools implemented", "eta_hours": 24},
            {"id": "M3", "name": "Eval baseline ≥ 0.60 trajectory quality", "eta_hours": 72},
            {"id": "M4", "name": "RC v1.0.0 deployed", "eta_hours": 168},
        ],
    }
    a1.skills_used = ["requirements_extraction", "constraint_analysis"]
    a1.created_at = _t(1.8)
    a1.updated_at = _t(1.8)
    artifacts.append(a1)

    # --- ADK_GRAPH_DIFF artifact (architecture) ---
    a2 = ArtifactRef()
    a2.artifact_id = "demo-art-airline-02"
    a2.task_id = "demo-task-airline-02"
    a2.session_id = AIRLINE_SESSION_1_ID
    a2.project_id = AIRLINE_PROJECT_ID
    a2.artifact_type = ArtifactType.ADK_GRAPH_DIFF
    a2.title = "ADK Agent Graph — 4-node orchestrator design"
    a2.summary = (
        "Adds orchestrator + 3 specialist subagents. Intent router selects "
        "booking / baggage / loyalty path based on user message classification."
    )
    a2.payload = {
        "nodes_added": [
            {
                "id": "orchestrator",
                "type": "LlmAgent",
                "model": "claude-sonnet-4-6",
                "instruction": "Route to the correct specialist subagent. Never answer directly.",
            },
            {
                "id": "booking_subagent",
                "type": "LlmAgent",
                "model": "claude-sonnet-4-6",
                "tools": ["booking_lookup_tool", "seat_inventory_tool", "rebooking_tool"],
            },
            {
                "id": "baggage_subagent",
                "type": "LlmAgent",
                "model": "claude-haiku-4-5",
                "tools": ["baggage_policy_lookup"],
            },
            {
                "id": "loyalty_subagent",
                "type": "LlmAgent",
                "model": "claude-haiku-4-5",
                "tools": ["loyalty_account_lookup"],
            },
        ],
        "edges_added": [
            {"from": "orchestrator", "to": "booking_subagent", "condition": "intent == 'booking'"},
            {"from": "orchestrator", "to": "baggage_subagent", "condition": "intent == 'baggage'"},
            {"from": "orchestrator", "to": "loyalty_subagent", "condition": "intent == 'loyalty'"},
        ],
        "nodes_removed": [],
        "edges_removed": [],
    }
    a2.skills_used = ["adk_graph_builder"]
    a2.created_at = _t(5.8)
    a2.updated_at = _t(5.8)
    artifacts.append(a2)

    # --- SOURCE_DIFF artifact (booking_lookup_tool) ---
    a3 = ArtifactRef()
    a3.artifact_id = "demo-art-airline-03"
    a3.task_id = "demo-task-airline-03"
    a3.session_id = AIRLINE_SESSION_2_ID
    a3.project_id = AIRLINE_PROJECT_ID
    a3.artifact_type = ArtifactType.SOURCE_DIFF
    a3.title = "Add booking_lookup_tool"
    a3.summary = "New file: agents/airline-cs/tools/booking_lookup.py — Sabre GDS PNR fetch."
    a3.payload = {
        "files": [
            {
                "path": "agents/airline-cs/tools/booking_lookup.py",
                "lines": [
                    "+from __future__ import annotations",
                    "+",
                    "+import os",
                    "+import httpx",
                    "+from pydantic import BaseModel",
                    "+",
                    "+",
                    "+class BookingRecord(BaseModel):",
                    "+    pnr: str",
                    "+    passenger_name: str",
                    "+    origin: str",
                    "+    destination: str",
                    "+    departure_utc: str",
                    "+    seat_assignment: str | None",
                    "+    loyalty_tier: str",
                    "+",
                    "+",
                    "+def booking_lookup_tool(pnr: str) -> BookingRecord:",
                    "+    \"\"\"Fetch booking record from Sabre GDS by PNR.\"\"\"",
                    "+    base_url = os.environ['SABRE_API_BASE']",
                    "+    token = os.environ['SABRE_API_TOKEN']",
                    "+    resp = httpx.get(",
                    "+        f'{base_url}/v3.5/booking/{pnr}',",
                    "+        headers={'Authorization': f'Bearer {token}'},",
                    "+        timeout=5.0,",
                    "+    )",
                    "+    resp.raise_for_status()",
                    "+    data = resp.json()",
                    "+    return BookingRecord(**data['booking'])",
                ],
            }
        ]
    }
    a3.skills_used = ["tool_scaffolder"]
    a3.created_at = _t(50.8)
    a3.updated_at = _t(50.8)
    artifacts.append(a3)

    # --- SOURCE_DIFF artifact (seat_inventory_tool — BUGGY VERSION) ---
    a4 = ArtifactRef()
    a4.artifact_id = "demo-art-airline-04"
    a4.task_id = "demo-task-airline-04"
    a4.session_id = AIRLINE_SESSION_2_ID
    a4.project_id = AIRLINE_PROJECT_ID
    a4.artifact_type = ArtifactType.SOURCE_DIFF
    a4.title = "Add seat_inventory_tool (v1 — schema bug)"
    a4.summary = (
        "New file: agents/airline-cs/tools/seat_inventory.py — returns flat seat list "
        "(BUGGY: missing seat_map wrapper, causes KeyError in booking_subagent)."
    )
    a4.payload = {
        "files": [
            {
                "path": "agents/airline-cs/tools/seat_inventory.py",
                "lines": [
                    "+def seat_inventory_tool(flight_number: str, cabin: str) -> dict:",
                    "+    \"\"\"Return available seats for a flight. BUG: returns flat list.\"\"\"",
                    "+    seats = _fetch_seats_from_gds(flight_number, cabin)",
                    "+    # BUG: callers expect {'seat_map': seats} but we return seats directly",
                    "+    return {'available': seats, 'cabin': cabin}",
                ],
            }
        ]
    }
    a4.skills_used = ["tool_scaffolder"]
    a4.created_at = _t(54.5)
    a4.updated_at = _t(54.5)
    artifacts.append(a4)

    # --- SKILL artifact (rebooking_skill) ---
    a5 = ArtifactRef()
    a5.artifact_id = "demo-art-airline-05"
    a5.task_id = "demo-task-airline-05"
    a5.session_id = AIRLINE_SESSION_2_ID
    a5.project_id = AIRLINE_PROJECT_ID
    a5.artifact_type = ArtifactType.SKILL
    a5.title = "rebooking_skill"
    a5.summary = (
        "Orchestrates the full rebooking flow: lookup → find alternatives → "
        "present options → confirm with passenger → update GDS."
    )
    a5.payload = {
        "skill_id": "rebooking_skill",
        "version": "1.0.0",
        "description": (
            "Multi-step skill for flight rebooking. Handles same-day and next-day "
            "alternatives, seat re-assignment, and confirmation email trigger."
        ),
        "steps": [
            "booking_lookup_tool(pnr) → get current itinerary",
            "flight_alternatives_tool(origin, destination, date) → list alternatives",
            "present_options to passenger with seat availability",
            "rebooking_tool(pnr, new_flight) → execute change",
            "send_confirmation_email(pnr, new_itinerary)",
        ],
        "input_schema": {"pnr": "str", "preferred_date": "str | None"},
        "output_schema": {"new_pnr": "str", "new_flight": "str", "confirmation_number": "str"},
        "hard_constraints": [
            "Must verify passenger identity (name match) before any GDS write",
            "Refund difference if new fare is lower",
            "Max 2 rebooking attempts per conversation",
        ],
    }
    a5.skills_used = ["skill_authoring"]
    a5.created_at = _t(61.5)
    a5.updated_at = _t(61.5)
    artifacts.append(a5)

    # --- GUARDRAIL artifact (pii_filter) ---
    a6 = ArtifactRef()
    a6.artifact_id = "demo-art-airline-06"
    a6.task_id = "demo-task-airline-06"
    a6.session_id = AIRLINE_SESSION_2_ID
    a6.project_id = AIRLINE_PROJECT_ID
    a6.artifact_type = ArtifactType.GUARDRAIL
    a6.title = "pii_filter guardrail"
    a6.summary = (
        "Masks credit card numbers, passport IDs, and date-of-birth fields "
        "before any log write or external API call."
    )
    a6.payload = {
        "guardrail_id": "pii_filter",
        "type": "output_filter",
        "priority": 1,
        "patterns": [
            {
                "name": "credit_card",
                "regex": r"\b(?:\d[ -]?){13,19}\b",
                "replacement": "****-****-****-[REDACTED]",
            },
            {
                "name": "passport_id",
                "regex": r"\b[A-Z]{1,2}\d{6,9}\b",
                "replacement": "[PASSPORT-REDACTED]",
            },
            {
                "name": "date_of_birth",
                "regex": r"\b(?:DOB|date.of.birth)[:\s]+\d{2}[\/\-]\d{2}[\/\-]\d{4}\b",
                "replacement": "[DOB-REDACTED]",
                "flags": ["IGNORECASE"],
            },
        ],
        "enforcement": "block_and_log",
        "test_coverage": "92%",
    }
    a6.skills_used = ["guardrail_authoring"]
    a6.created_at = _t(66.2)
    a6.updated_at = _t(66.2)
    artifacts.append(a6)

    # --- EVAL artifact (baseline — low score) ---
    a7 = ArtifactRef()
    a7.artifact_id = "demo-art-airline-07"
    a7.task_id = "demo-task-airline-07"
    a7.session_id = AIRLINE_SESSION_2_ID
    a7.project_id = AIRLINE_PROJECT_ID
    a7.artifact_type = ArtifactType.EVAL
    a7.title = "Baseline eval — 120 conversations (pre-fix)"
    a7.summary = (
        "Trajectory quality 0.61. 23 failures due to seat_inventory_tool schema bug. "
        "Hard gate FAILED (threshold: 0.80)."
    )
    a7.payload = {
        "eval_run_id": "eval-run-airline-baseline",
        "conversation_count": 120,
        "trajectory_quality": 0.61,
        "outcome_quality": 0.74,
        "hard_gate_passed": False,
        "hard_gate_threshold": 0.80,
        "failure_breakdown": {
            "seat_inventory_key_error": 23,
            "pnr_not_found_unhandled": 4,
            "loyalty_tier_mismatch": 2,
            "timeout_exceeded": 1,
        },
        "top_failure": "KeyError: 'seat_map' in booking_subagent line 47 — seat_inventory_tool returns flat list",
    }
    a7.created_at = _t(73.5)
    a7.updated_at = _t(73.5)
    artifacts.append(a7)

    # --- TRACE_EVIDENCE artifact (seat inventory failure trace) ---
    a8 = ArtifactRef()
    a8.artifact_id = "demo-art-airline-08"
    a8.task_id = "demo-task-airline-08"
    a8.session_id = AIRLINE_SESSION_3_ID
    a8.project_id = AIRLINE_PROJECT_ID
    a8.artifact_type = ArtifactType.TRACE_EVIDENCE
    a8.title = "Trace evidence: seat_inventory KeyError cluster"
    a8.summary = (
        "23 traces share the same failure: booking_subagent crashes on "
        "'seat_map' key lookup. Root cause: tool returns {available: [...]} "
        "instead of {seat_map: [...]}."
    )
    a8.payload = {
        "trace_id": "trace-airline-98f2a1",
        "span_id": "span-booking-subagent-47",
        "failure_family": "schema_mismatch",
        "blame_target": "agents/airline-cs/tools/seat_inventory.py:_build_response()",
        "stack_trace": (
            "KeyError: 'seat_map'\n"
            "  at booking_subagent.handle_upgrade() line 47\n"
            "  at seat_inventory_tool._build_response() line 29\n"
            "  at GDS.fetch_seat_map() line 112"
        ),
        "conversation_excerpt": {
            "user": "Can I upgrade to business class on flight SK 401?",
            "agent_internal": "[booking_subagent calling seat_inventory_tool(SK401, business)]",
            "error": "KeyError: 'seat_map' — tool returned {'available': [...], 'cabin': 'business'}",
        },
        "affected_count": 23,
        "first_seen": "2026-03-22T14:30:00Z",
        "last_seen": "2026-03-24T09:15:00Z",
    }
    a8.created_at = _t(123.8)
    a8.updated_at = _t(123.8)
    artifacts.append(a8)

    # --- SOURCE_DIFF artifact (seat_inventory_tool — FIXED) ---
    a9 = ArtifactRef()
    a9.artifact_id = "demo-art-airline-09"
    a9.task_id = "demo-task-airline-09"
    a9.session_id = AIRLINE_SESSION_3_ID
    a9.project_id = AIRLINE_PROJECT_ID
    a9.artifact_type = ArtifactType.SOURCE_DIFF
    a9.title = "Fix seat_inventory_tool — schema envelope + pydantic validation"
    a9.summary = "Wraps seat list in {seat_map: ...}; adds SeatInventoryResponse pydantic model; adds empty-flight unit test."
    a9.payload = {
        "files": [
            {
                "path": "agents/airline-cs/tools/seat_inventory.py",
                "lines": [
                    " from __future__ import annotations",
                    "+from pydantic import BaseModel",
                    " import os",
                    " import httpx",
                    " ",
                    "+",
                    "+class SeatInventoryResponse(BaseModel):",
                    "+    seat_map: list[dict]",
                    "+    cabin: str",
                    "+    flight_number: str",
                    " ",
                    " ",
                    " def seat_inventory_tool(flight_number: str, cabin: str)",
                    "-    \"\"\"Return available seats. BUG: flat list.\"\"\"",
                    "+    \"\"\"Return available seats wrapped in seat_map envelope.\"\"\"",
                    "     seats = _fetch_seats_from_gds(flight_number, cabin)",
                    "-    return {'available': seats, 'cabin': cabin}",
                    "+    return SeatInventoryResponse(",
                    "+        seat_map=seats,",
                    "+        cabin=cabin,",
                    "+        flight_number=flight_number,",
                    "+    ).model_dump()",
                ],
            },
            {
                "path": "tests/tools/test_seat_inventory.py",
                "lines": [
                    "+def test_empty_flight_returns_empty_seat_map():",
                    "+    with patch('tools.seat_inventory._fetch_seats_from_gds', return_value=[]):",
                    "+        result = seat_inventory_tool('SK999', 'business')",
                    "+        assert result['seat_map'] == []",
                    "+        assert result['cabin'] == 'business'",
                ],
            },
        ]
    }
    a9.skills_used = ["tool_scaffolder"]
    a9.created_at = _t(126.8)
    a9.updated_at = _t(126.8)
    a9.selected = True
    artifacts.append(a9)

    # --- EVAL artifact (post-fix — passing) ---
    a10 = ArtifactRef()
    a10.artifact_id = "demo-art-airline-10"
    a10.task_id = "demo-task-airline-10"
    a10.session_id = AIRLINE_SESSION_3_ID
    a10.project_id = AIRLINE_PROJECT_ID
    a10.artifact_type = ArtifactType.EVAL
    a10.title = "Post-fix eval — 120 conversations (v1.0.0-rc)"
    a10.summary = "Trajectory quality 0.84. Hard gate PASSED. Ready for release."
    a10.payload = {
        "eval_run_id": "eval-run-airline-postfix",
        "conversation_count": 120,
        "trajectory_quality": 0.84,
        "outcome_quality": 0.89,
        "hard_gate_passed": True,
        "hard_gate_threshold": 0.80,
        "failure_breakdown": {
            "pnr_not_found_unhandled": 2,
            "timeout_exceeded": 1,
        },
        "improvement_vs_baseline": "+0.23 trajectory quality",
    }
    a10.created_at = _t(133.5)
    a10.updated_at = _t(133.5)
    a10.selected = True
    artifacts.append(a10)

    # --- RELEASE artifact ---
    a11 = ArtifactRef()
    a11.artifact_id = "demo-art-airline-11"
    a11.task_id = "demo-task-airline-11"
    a11.session_id = AIRLINE_SESSION_3_ID
    a11.project_id = AIRLINE_PROJECT_ID
    a11.artifact_type = ArtifactType.RELEASE
    a11.title = "Release Candidate v1.0.0 — SkyLink Airlines CS Agent"
    a11.summary = (
        "All P0/P1 bugs resolved. Eval hard gate passed (0.84 ≥ 0.80). "
        "Pending deployment approval for gcp-us-central1-prod."
    )
    a11.payload = {
        "version": "1.0.0",
        "status": "draft",
        "deployment_target": "gcp-us-central1-prod",
        "changelog": (
            "## v1.0.0\n"
            "### Added\n"
            "- booking_lookup_tool: Sabre GDS PNR fetch with pydantic validation\n"
            "- seat_inventory_tool: Available seats by cabin class (schema fix applied)\n"
            "- rebooking_skill: End-to-end rebooking with confirmation\n"
            "- pii_filter guardrail: Masks CC numbers and passport IDs\n"
            "- inappropriate_content guardrail: Blocks off-topic requests\n"
            "### Fixed\n"
            "- seat_inventory_tool now returns {seat_map: [...]} envelope (was flat list)\n"
            "### Eval\n"
            "- Trajectory quality: 0.84 (was 0.61 at baseline)\n"
            "- Hard gate: PASSED (threshold 0.80)"
        ),
        "artifact_ids": [
            "demo-art-airline-02",
            "demo-art-airline-03",
            "demo-art-airline-05",
            "demo-art-airline-06",
            "demo-art-airline-09",
            "demo-art-airline-10",
        ],
        "eval_bundle_id": "demo-eval-bundle-airline-02",
    }
    a11.created_at = _t(137.5)
    a11.updated_at = _t(137.5)
    artifacts.append(a11)

    return artifacts


def _airline_approvals() -> list[ApprovalRequest]:
    approvals = []

    ap1 = ApprovalRequest()
    ap1.approval_id = "demo-appr-airline-01"
    ap1.task_id = "demo-task-airline-09"
    ap1.session_id = AIRLINE_SESSION_3_ID
    ap1.project_id = AIRLINE_PROJECT_ID
    ap1.action = PrivilegedAction.SOURCE_WRITE
    ap1.description = (
        "Tool engineer requests write access to modify "
        "agents/airline-cs/tools/seat_inventory.py"
    )
    ap1.scope = ApprovalScope.TASK
    ap1.status = ApprovalStatus.APPROVED
    ap1.risk_level = RiskLevel.MEDIUM
    ap1.details = {
        "files": ["agents/airline-cs/tools/seat_inventory.py"],
        "reason": "Fix schema bug causing 23 eval failures",
        "lines_changed": 12,
    }
    ap1.created_at = _t(124.3)
    ap1.updated_at = _t(124.8)
    ap1.resolved_at = _t(124.8)
    ap1.resolved_by = "andrew"
    approvals.append(ap1)

    ap2 = ApprovalRequest()
    ap2.approval_id = "demo-appr-airline-02"
    ap2.task_id = "demo-task-airline-12"
    ap2.session_id = AIRLINE_SESSION_3_ID
    ap2.project_id = AIRLINE_PROJECT_ID
    ap2.action = PrivilegedAction.DEPLOYMENT
    ap2.description = (
        "Release manager requesting deployment of RC v1.0.0 to gcp-us-central1-prod. "
        "Eval hard gate passed. All P0 bugs resolved."
    )
    ap2.scope = ApprovalScope.ONCE
    ap2.status = ApprovalStatus.PENDING
    ap2.risk_level = RiskLevel.HIGH
    ap2.details = {
        "release_id": "demo-rc-airline-01",
        "deployment_target": "gcp-us-central1-prod",
        "eval_trajectory_quality": 0.84,
        "rollback_plan": "gcloud run services update-traffic --to-revisions=PREVIOUS=100",
        "estimated_users_affected": 180000,
    }
    ap2.created_at = _t(138.3)
    ap2.updated_at = _t(138.3)
    approvals.append(ap2)

    return approvals


def _airline_eval_bundles() -> list[EvalBundle]:
    bundles = []

    b1 = EvalBundle()
    b1.bundle_id = "demo-eval-bundle-airline-01"
    b1.task_id = "demo-task-airline-07"
    b1.session_id = AIRLINE_SESSION_2_ID
    b1.project_id = AIRLINE_PROJECT_ID
    b1.eval_run_ids = ["eval-run-airline-baseline"]
    b1.baseline_scores = {"trajectory_quality": 0.0, "outcome_quality": 0.0}
    b1.candidate_scores = {"trajectory_quality": 0.61, "outcome_quality": 0.74}
    b1.hard_gate_passed = False
    b1.trajectory_quality = 0.61
    b1.outcome_quality = 0.74
    b1.eval_coverage_pct = 73.0
    b1.cost_delta_pct = 0.0
    b1.latency_delta_pct = 0.0
    b1.notes = "Baseline run. 23 failures from seat_inventory schema bug blocking further progress."
    b1.created_at = _t(73.6)
    b1.updated_at = _t(73.6)
    bundles.append(b1)

    b2 = EvalBundle()
    b2.bundle_id = "demo-eval-bundle-airline-02"
    b2.task_id = "demo-task-airline-10"
    b2.session_id = AIRLINE_SESSION_3_ID
    b2.project_id = AIRLINE_PROJECT_ID
    b2.eval_run_ids = ["eval-run-airline-postfix", "eval-run-airline-baseline"]
    b2.baseline_scores = {"trajectory_quality": 0.61, "outcome_quality": 0.74}
    b2.candidate_scores = {"trajectory_quality": 0.84, "outcome_quality": 0.89}
    b2.hard_gate_passed = True
    b2.trajectory_quality = 0.84
    b2.outcome_quality = 0.89
    b2.eval_coverage_pct = 87.0
    b2.cost_delta_pct = 2.3
    b2.latency_delta_pct = -4.1
    b2.notes = "Post-fix run. Hard gate passed. Ready for RC v1.0.0."
    b2.created_at = _t(133.6)
    b2.updated_at = _t(133.6)
    bundles.append(b2)

    return bundles


def _airline_trace_bookmarks() -> list[TraceBookmark]:
    bookmarks = []

    bm1 = TraceBookmark()
    bm1.bookmark_id = "demo-bm-airline-01"
    bm1.task_id = "demo-task-airline-08"
    bm1.session_id = AIRLINE_SESSION_3_ID
    bm1.project_id = AIRLINE_PROJECT_ID
    bm1.trace_id = "trace-airline-98f2a1"
    bm1.span_id = "span-seat-inventory-29"
    bm1.label = "seat_inventory schema mismatch — root cause confirmed"
    bm1.failure_family = "schema_mismatch"
    bm1.blame_target = "agents/airline-cs/tools/seat_inventory.py:_build_response():29"
    bm1.evidence_links = ["demo-art-airline-08"]
    bm1.promoted_to_eval = True
    bm1.notes = (
        "This span is the earliest point of failure for all 23 affected conversations. "
        "The tool returns {available: [...]} but callers expect {seat_map: [...]}. "
        "Promoted to eval test case: test_seat_inventory_returns_seat_map_key."
    )
    bm1.created_at = _t(122.5)
    bm1.updated_at = _t(124.0)
    bookmarks.append(bm1)

    bm2 = TraceBookmark()
    bm2.bookmark_id = "demo-bm-airline-02"
    bm2.task_id = "demo-task-airline-08"
    bm2.session_id = AIRLINE_SESSION_3_ID
    bm2.project_id = AIRLINE_PROJECT_ID
    bm2.trace_id = "trace-airline-3d9f11"
    bm2.span_id = "span-booking-subagent-47"
    bm2.label = "booking_subagent crash — downstream of seat_inventory bug"
    bm2.failure_family = "unhandled_exception"
    bm2.blame_target = "agents/airline-cs/booking_subagent.py:handle_upgrade():47"
    bm2.evidence_links = ["demo-art-airline-08", "demo-bm-airline-01"]
    bm2.promoted_to_eval = False
    bm2.notes = (
        "Secondary failure point. booking_subagent assumes seat_map key exists. "
        "Once seat_inventory tool is fixed, this crash will not occur. "
        "Added defensive key check as secondary safety measure."
    )
    bm2.created_at = _t(123.0)
    bm2.updated_at = _t(123.0)
    bookmarks.append(bm2)

    return bookmarks


def _airline_release() -> ReleaseCandidate:
    rc = ReleaseCandidate()
    rc.release_id = "demo-rc-airline-01"
    rc.task_id = "demo-task-airline-11"
    rc.session_id = AIRLINE_SESSION_3_ID
    rc.project_id = AIRLINE_PROJECT_ID
    rc.version = "1.0.0"
    rc.artifact_ids = [
        "demo-art-airline-02",
        "demo-art-airline-03",
        "demo-art-airline-05",
        "demo-art-airline-06",
        "demo-art-airline-09",
        "demo-art-airline-10",
    ]
    rc.eval_bundle_id = "demo-eval-bundle-airline-02"
    rc.status = "draft"
    rc.deployment_target = "gcp-us-central1-prod"
    rc.changelog = (
        "## SkyLink Airlines CS Agent v1.0.0\n\n"
        "### Added\n"
        "- Booking lookup via Sabre GDS REST API v3.5\n"
        "- Seat inventory with upgrade availability\n"
        "- End-to-end rebooking skill with confirmation\n"
        "- PII filter guardrail (CC, passport, DOB masking)\n"
        "- Off-topic content guardrail\n\n"
        "### Fixed\n"
        "- seat_inventory_tool now returns {seat_map} envelope (fixes 23 eval failures)\n\n"
        "### Quality\n"
        "- Trajectory quality: 0.84 (baseline: 0.61)\n"
        "- Hard gate: PASSED (threshold: 0.80)\n"
        "- Eval coverage: 87%"
    )
    rc.created_at = _t(137.5)
    rc.updated_at = _t(137.5)
    return rc


# ===========================================================================
# E-COMMERCE RETURNS BOT — build with guardrail hardening, then deployed
# ===========================================================================

def _ecom_project() -> BuilderProject:
    p = BuilderProject()
    p.project_id = ECOM_PROJECT_ID
    p.name = "E-Commerce Returns Bot"
    p.description = (
        "Automated returns and refunds agent for ShopFast marketplace. "
        "Handles return requests, refund status, exchange requests, and policy lookups."
    )
    p.root_path = "agents/ecom-returns"
    p.master_instruction = (
        "You are the ShopFast returns assistant. Verify order ID and email before "
        "processing any return. Maximum refund without manager approval: $150. "
        "Always check fraud signals before approving instant refunds."
    )
    p.knowledge_files = [
        "docs/returns-policy-v5.pdf",
        "docs/fraud-signals-reference.md",
        "docs/exchange-eligibility-matrix.md",
    ]
    p.buildtime_skills = ["adk_graph_builder", "tool_scaffolder", "eval_harness"]
    p.runtime_skills = ["returns_intake", "refund_processor", "order_lookup"]
    p.deployment_targets = ["aws-us-east-1-prod"]
    p.preferred_models = {
        "orchestrator": "claude-sonnet-4-6",
        "guardrail_author": "claude-sonnet-4-6",
    }
    p.tags = ["e-commerce", "returns", "production"]
    p.created_at = _t(10)
    p.updated_at = _t(152)
    return p


def _ecom_sessions() -> list[BuilderSession]:
    s1 = BuilderSession()
    s1.session_id = ECOM_SESSION_1_ID
    s1.project_id = ECOM_PROJECT_ID
    s1.title = "Act 1–2: Build — Requirements & Tools"
    s1.mode = ExecutionMode.APPLY
    s1.active_specialist = SpecialistRole.TOOL_ENGINEER
    s1.status = "closed"
    s1.created_at = _t(10)
    s1.updated_at = _t(72)
    s1.message_count = 19

    s2 = BuilderSession()
    s2.session_id = ECOM_SESSION_2_ID
    s2.project_id = ECOM_PROJECT_ID
    s2.title = "Act 3: Evaluate — Guardrail Issue Found"
    s2.mode = ExecutionMode.APPLY
    s2.active_specialist = SpecialistRole.EVAL_AUTHOR
    s2.status = "closed"
    s2.created_at = _t(72)
    s2.updated_at = _t(120)
    s2.message_count = 16

    s3 = BuilderSession()
    s3.session_id = ECOM_SESSION_3_ID
    s3.project_id = ECOM_PROJECT_ID
    s3.title = "Act 4–5: Harden Guardrails & Deploy"
    s3.mode = ExecutionMode.APPLY
    s3.active_specialist = SpecialistRole.RELEASE_MANAGER
    s3.status = "open"
    s3.created_at = _t(120)
    s3.updated_at = _t(152)
    s3.message_count = 21

    return [s1, s2, s3]


def _ecom_tasks() -> list[BuilderTask]:
    tasks = []

    t1 = BuilderTask()
    t1.task_id = "demo-task-ecom-01"
    t1.session_id = ECOM_SESSION_1_ID
    t1.project_id = ECOM_PROJECT_ID
    t1.title = "Gather requirements: returns & refunds agent"
    t1.description = (
        "User: Build a returns bot for ShopFast marketplace. Handles return requests, "
        "refund status, exchange requests, policy lookups. Integrate with OMS and payment gateway."
    )
    t1.mode = ExecutionMode.DRAFT
    t1.status = TaskStatus.COMPLETED
    t1.active_specialist = SpecialistRole.REQUIREMENTS_ANALYST
    t1.created_at = _t(10.1)
    t1.updated_at = _t(13)
    t1.started_at = _t(10.2)
    t1.completed_at = _t(13)
    t1.elapsed_seconds = 10260
    t1.progress = 100
    t1.token_count = 14200
    t1.cost_usd = 0.23
    tasks.append(t1)

    t2 = BuilderTask()
    t2.task_id = "demo-task-ecom-02"
    t2.session_id = ECOM_SESSION_1_ID
    t2.project_id = ECOM_PROJECT_ID
    t2.title = "Implement order_lookup_tool and returns_policy_tool"
    t2.description = (
        "Implement order_lookup_tool (fetches order by ID + email from OMS) "
        "and returns_policy_tool (checks eligibility: 30-day window, unused items)."
    )
    t2.mode = ExecutionMode.APPLY
    t2.status = TaskStatus.COMPLETED
    t2.active_specialist = SpecialistRole.TOOL_ENGINEER
    t2.created_at = _t(13.1)
    t2.updated_at = _t(20)
    t2.started_at = _t(13.2)
    t2.completed_at = _t(20)
    t2.elapsed_seconds = 24840
    t2.progress = 100
    t2.token_count = 23100
    t2.cost_usd = 0.37
    tasks.append(t2)

    t3 = BuilderTask()
    t3.task_id = "demo-task-ecom-03"
    t3.session_id = ECOM_SESSION_1_ID
    t3.project_id = ECOM_PROJECT_ID
    t3.title = "Implement refund_processor tool"
    t3.description = (
        "Build refund_processor that integrates with Stripe to issue refunds. "
        "Must enforce $150 limit without manager approval. Log all actions."
    )
    t3.mode = ExecutionMode.APPLY
    t3.status = TaskStatus.COMPLETED
    t3.active_specialist = SpecialistRole.TOOL_ENGINEER
    t3.created_at = _t(20.1)
    t3.updated_at = _t(28)
    t3.started_at = _t(20.2)
    t3.completed_at = _t(28)
    t3.elapsed_seconds = 28080
    t3.progress = 100
    t3.token_count = 31800
    t3.cost_usd = 0.51
    tasks.append(t3)

    t4 = BuilderTask()
    t4.task_id = "demo-task-ecom-04"
    t4.session_id = ECOM_SESSION_1_ID
    t4.project_id = ECOM_PROJECT_ID
    t4.title = "Author returns_intake skill and guardrails"
    t4.description = (
        "Create returns_intake runtime skill. Add refund_amount_limit guardrail "
        "and fraud_signal_check guardrail."
    )
    t4.mode = ExecutionMode.APPLY
    t4.status = TaskStatus.COMPLETED
    t4.active_specialist = SpecialistRole.SKILL_AUTHOR
    t4.created_at = _t(28.1)
    t4.updated_at = _t(40)
    t4.started_at = _t(28.2)
    t4.completed_at = _t(40)
    t4.elapsed_seconds = 42840
    t4.progress = 100
    t4.token_count = 38600
    t4.cost_usd = 0.62
    tasks.append(t4)

    t5 = BuilderTask()
    t5.task_id = "demo-task-ecom-05"
    t5.session_id = ECOM_SESSION_2_ID
    t5.project_id = ECOM_PROJECT_ID
    t5.title = "Run baseline eval suite"
    t5.description = "Execute 100-conversation eval suite; check refund guardrail enforcement rate."
    t5.mode = ExecutionMode.APPLY
    t5.status = TaskStatus.COMPLETED
    t5.active_specialist = SpecialistRole.EVAL_AUTHOR
    t5.created_at = _t(72.1)
    t5.updated_at = _t(80)
    t5.started_at = _t(72.2)
    t5.completed_at = _t(80)
    t5.elapsed_seconds = 28080
    t5.progress = 100
    t5.token_count = 39400
    t5.cost_usd = 0.63
    tasks.append(t5)

    t6 = BuilderTask()
    t6.task_id = "demo-task-ecom-06"
    t6.session_id = ECOM_SESSION_2_ID
    t6.project_id = ECOM_PROJECT_ID
    t6.title = "Investigate refund guardrail bypass in traces"
    t6.description = (
        "Trace analyst: 8 eval conversations show refund_processor issuing refunds "
        "over $150 limit. Guardrail is checking the REQUESTED amount, not the "
        "PROCESSED amount after tax credit adjustment."
    )
    t6.mode = ExecutionMode.APPLY
    t6.status = TaskStatus.COMPLETED
    t6.active_specialist = SpecialistRole.TRACE_ANALYST
    t6.created_at = _t(80.1)
    t6.updated_at = _t(86)
    t6.started_at = _t(80.2)
    t6.completed_at = _t(86)
    t6.elapsed_seconds = 21240
    t6.progress = 100
    t6.token_count = 19800
    t6.cost_usd = 0.32
    tasks.append(t6)

    t7 = BuilderTask()
    t7.task_id = "demo-task-ecom-07"
    t7.session_id = ECOM_SESSION_3_ID
    t7.project_id = ECOM_PROJECT_ID
    t7.title = "Harden refund_amount_limit guardrail"
    t7.description = (
        "Fix guardrail to check FINAL processed amount (after tax credit). "
        "Add pre- and post-processing hooks. Add 5 adversarial eval cases."
    )
    t7.mode = ExecutionMode.APPLY
    t7.status = TaskStatus.COMPLETED
    t7.active_specialist = SpecialistRole.GUARDRAIL_AUTHOR
    t7.created_at = _t(120.1)
    t7.updated_at = _t(127)
    t7.started_at = _t(120.2)
    t7.completed_at = _t(127)
    t7.elapsed_seconds = 24840
    t7.progress = 100
    t7.token_count = 22400
    t7.cost_usd = 0.36
    tasks.append(t7)

    t8 = BuilderTask()
    t8.task_id = "demo-task-ecom-08"
    t8.session_id = ECOM_SESSION_3_ID
    t8.project_id = ECOM_PROJECT_ID
    t8.title = "Re-run eval suite post-guardrail hardening"
    t8.description = "Execute 100+5 adversarial conversations. Verify zero guardrail bypass."
    t8.mode = ExecutionMode.APPLY
    t8.status = TaskStatus.COMPLETED
    t8.active_specialist = SpecialistRole.EVAL_AUTHOR
    t8.created_at = _t(127.1)
    t8.updated_at = _t(136)
    t8.started_at = _t(127.2)
    t8.completed_at = _t(136)
    t8.elapsed_seconds = 32040
    t8.progress = 100
    t8.token_count = 44800
    t8.cost_usd = 0.72
    tasks.append(t8)

    t9 = BuilderTask()
    t9.task_id = "demo-task-ecom-09"
    t9.session_id = ECOM_SESSION_3_ID
    t9.project_id = ECOM_PROJECT_ID
    t9.title = "Deploy RC v0.9.0 to aws-us-east-1-prod"
    t9.description = (
        "Release candidate v0.9.0 approved. Deploying to aws-us-east-1-prod. "
        "Canary at 5% traffic."
    )
    t9.mode = ExecutionMode.APPLY
    t9.status = TaskStatus.COMPLETED
    t9.active_specialist = SpecialistRole.RELEASE_MANAGER
    t9.created_at = _t(136.1)
    t9.updated_at = _t(152)
    t9.started_at = _t(136.2)
    t9.completed_at = _t(152)
    t9.elapsed_seconds = 57240
    t9.progress = 100
    t9.token_count = 8400
    t9.cost_usd = 0.14
    tasks.append(t9)

    return tasks


def _ecom_proposals() -> list[BuilderProposal]:
    proposals = []

    p1 = BuilderProposal()
    p1.proposal_id = "demo-prop-ecom-01"
    p1.task_id = "demo-task-ecom-07"
    p1.session_id = ECOM_SESSION_3_ID
    p1.project_id = ECOM_PROJECT_ID
    p1.goal = "Harden refund_amount_limit guardrail to check post-tax FINAL amount"
    p1.assumptions = [
        "Tax credit adjustments are applied in refund_processor before refund_amount_limit check",
        "Stripe webhook confirms final charge amount within 100ms",
        "Adversarial test cases will cover the tax-credit bypass vector",
    ]
    p1.targeted_artifacts = ["guardrail", "source_diff"]
    p1.targeted_surfaces = [
        "agents/ecom-returns/guardrails/refund_limit.py",
        "agents/ecom-returns/tools/refund_processor.py",
    ]
    p1.expected_impact = (
        "Closes refund_amount_limit bypass. 8 eval failures → 0. "
        "Guardrail enforcement rate: 91% → 100%."
    )
    p1.risk_level = RiskLevel.HIGH
    p1.required_approvals = ["source_write"]
    p1.steps = [
        {"step": 1, "action": "Move guardrail check to post-processing hook in refund_processor"},
        {"step": 2, "action": "Pass final_amount (after tax credit) to refund_amount_limit"},
        {"step": 3, "action": "Add 5 adversarial test cases covering tax-credit bypass vectors"},
        {"step": 4, "action": "Update guardrail documentation"},
    ]
    p1.status = "approved"
    p1.accepted = True
    p1.created_at = _t(120.3)
    p1.updated_at = _t(121.0)
    proposals.append(p1)

    p2 = BuilderProposal()
    p2.proposal_id = "demo-prop-ecom-02"
    p2.task_id = "demo-task-ecom-09"
    p2.session_id = ECOM_SESSION_3_ID
    p2.project_id = ECOM_PROJECT_ID
    p2.goal = "Deploy RC v0.9.0 to aws-us-east-1-prod at 5% canary"
    p2.assumptions = [
        "AWS ECS deployment target configured with blue/green deployment",
        "Rollback time < 2 minutes via ECS service update",
        "Canary traffic split managed by ALB weighted target groups",
        "SLO alerting configured: P95 latency < 4s, error rate < 1%",
    ]
    p2.targeted_surfaces = ["deployment_config", "ecs_task_definition"]
    p2.expected_impact = (
        "Gets v0.9.0 live with minimum blast radius. "
        "5% canary monitors SLOs for 24h before full promotion."
    )
    p2.risk_level = RiskLevel.HIGH
    p2.required_approvals = ["deployment", "benchmark_spend"]
    p2.steps = [
        {"step": 1, "action": "Push Docker image to ECR: shopfast-returns-bot:0.9.0"},
        {"step": 2, "action": "Update ECS task definition with new image tag"},
        {"step": 3, "action": "Set ALB weighted rule: v0.9.0=5%, v0.8.2=95%"},
        {"step": 4, "action": "Monitor SLOs for 24h via CloudWatch dashboard"},
        {"step": 5, "action": "Promote to 100% traffic if P95 < 4s and error rate < 1%"},
    ]
    p2.status = "approved"
    p2.accepted = True
    p2.created_at = _t(136.2)
    p2.updated_at = _t(137.0)
    proposals.append(p2)

    p3 = BuilderProposal()
    p3.proposal_id = "demo-prop-ecom-03"
    p3.task_id = "demo-task-ecom-04"
    p3.session_id = ECOM_SESSION_1_ID
    p3.project_id = ECOM_PROJECT_ID
    p3.goal = "Add fraud_signal_check guardrail to intercept suspicious return patterns"
    p3.assumptions = [
        "Fraud signals: >3 returns in 30 days, high-value item, new account (<7 days old)",
        "Flagged cases route to human review queue, not auto-rejected",
        "Fraud model scores provided by internal risk API at risk.shopfast.internal",
    ]
    p3.targeted_artifacts = ["guardrail"]
    p3.targeted_surfaces = ["agents/ecom-returns/guardrails/fraud_signal.py"]
    p3.expected_impact = (
        "Intercepts ~3% of return requests for human review. "
        "Estimated fraud prevention: $12,000/month based on historical patterns."
    )
    p3.risk_level = RiskLevel.MEDIUM
    p3.required_approvals = ["external_network"]
    p3.steps = [
        {"step": 1, "action": "Implement fraud_signal_check calling risk.shopfast.internal/v1/score"},
        {"step": 2, "action": "Add routing: score > 0.7 → human_review_queue"},
        {"step": 3, "action": "Log all flagged cases with evidence to fraud_audit table"},
    ]
    p3.status = "revision_requested"
    p3.revision_count = 1
    p3.revision_comments = [
        "Please add a fallback in case the fraud API is unavailable. "
        "Should default to ALLOW (not block) to avoid false positives causing bad CX."
    ]
    p3.created_at = _t(30.0)
    p3.updated_at = _t(32.5)
    proposals.append(p3)

    return proposals


def _ecom_artifacts() -> list[ArtifactRef]:
    artifacts = []

    a1 = ArtifactRef()
    a1.artifact_id = "demo-art-ecom-01"
    a1.task_id = "demo-task-ecom-02"
    a1.session_id = ECOM_SESSION_1_ID
    a1.project_id = ECOM_PROJECT_ID
    a1.artifact_type = ArtifactType.SOURCE_DIFF
    a1.title = "Add order_lookup_tool and returns_policy_tool"
    a1.summary = "Two new tools: OMS order fetch and returns eligibility check."
    a1.payload = {
        "files": [
            {
                "path": "agents/ecom-returns/tools/order_lookup.py",
                "lines": [
                    "+class OrderRecord(BaseModel):",
                    "+    order_id: str",
                    "+    customer_email: str",
                    "+    items: list[OrderItem]",
                    "+    order_date: str",
                    "+    total_usd: float",
                    "+    status: str",
                    "+",
                    "+def order_lookup_tool(order_id: str, email: str) -> OrderRecord:",
                    "+    \"\"\"Fetch order from ShopFast OMS. Verifies email matches order.\"\"\"",
                    "+    resp = oms_client.get(f'/orders/{order_id}', auth_email=email)",
                    "+    resp.raise_for_status()",
                    "+    return OrderRecord(**resp.json())",
                ],
            },
            {
                "path": "agents/ecom-returns/tools/returns_policy.py",
                "lines": [
                    "+def returns_policy_tool(order_id: str, item_sku: str) -> dict:",
                    "+    \"\"\"Check if an item is eligible for return.\"\"\"",
                    "+    order = order_lookup_tool(order_id)",
                    "+    days_since_order = (now() - order.order_date).days",
                    "+    if days_since_order > 30:",
                    "+        return {'eligible': False, 'reason': 'Outside 30-day return window'}",
                    "+    item = next(i for i in order.items if i.sku == item_sku)",
                    "+    if item.condition != 'unused':",
                    "+        return {'eligible': False, 'reason': 'Item shows signs of use'}",
                    "+    return {'eligible': True, 'refund_method': 'original_payment'}",
                ],
            },
        ]
    }
    a1.created_at = _t(19.5)
    a1.updated_at = _t(19.5)
    artifacts.append(a1)

    a2 = ArtifactRef()
    a2.artifact_id = "demo-art-ecom-02"
    a2.task_id = "demo-task-ecom-04"
    a2.session_id = ECOM_SESSION_1_ID
    a2.project_id = ECOM_PROJECT_ID
    a2.artifact_type = ArtifactType.GUARDRAIL
    a2.title = "refund_amount_limit guardrail (v1 — has bypass)"
    a2.summary = (
        "Blocks refunds over $150 — BUT checks requested amount, not final amount. "
        "8 bypass cases found in eval."
    )
    a2.payload = {
        "guardrail_id": "refund_amount_limit",
        "type": "pre_execution",
        "priority": 1,
        "rule": "if requested_refund_amount > 150.00: block",
        "note": "BUG: checks requested_amount before tax credit; final amount can exceed $150",
        "enforcement": "block_with_message",
        "message": "Refund amount exceeds $150 limit. Escalating to human agent.",
        "test_coverage": "62%",
        "known_bypass": "Tax credit adjustments processed AFTER this check",
    }
    a2.created_at = _t(38.5)
    a2.updated_at = _t(38.5)
    artifacts.append(a2)

    a3 = ArtifactRef()
    a3.artifact_id = "demo-art-ecom-03"
    a3.task_id = "demo-task-ecom-05"
    a3.session_id = ECOM_SESSION_2_ID
    a3.project_id = ECOM_PROJECT_ID
    a3.artifact_type = ArtifactType.EVAL
    a3.title = "Baseline eval — 100 conversations (pre-guardrail fix)"
    a3.summary = "Trajectory quality 0.72. 8 refund guardrail bypasses detected. Hard gate FAILED."
    a3.payload = {
        "eval_run_id": "eval-run-ecom-baseline",
        "conversation_count": 100,
        "trajectory_quality": 0.72,
        "outcome_quality": 0.81,
        "hard_gate_passed": False,
        "hard_gate_threshold": 0.80,
        "failure_breakdown": {
            "refund_guardrail_bypass": 8,
            "order_not_found_unhandled": 3,
            "exchange_routing_error": 2,
        },
        "critical_failure": "8 conversations issued refunds > $150 via tax-credit bypass",
    }
    a3.created_at = _t(79.5)
    a3.updated_at = _t(79.5)
    artifacts.append(a3)

    a4 = ArtifactRef()
    a4.artifact_id = "demo-art-ecom-04"
    a4.task_id = "demo-task-ecom-07"
    a4.session_id = ECOM_SESSION_3_ID
    a4.project_id = ECOM_PROJECT_ID
    a4.artifact_type = ArtifactType.GUARDRAIL
    a4.title = "refund_amount_limit guardrail (v2 — HARDENED)"
    a4.summary = "Now checks FINAL processed amount after tax credits. 100% enforcement in eval."
    a4.payload = {
        "guardrail_id": "refund_amount_limit",
        "version": "2.0.0",
        "type": "post_processing_hook",
        "priority": 1,
        "rule": "if final_processed_amount > 150.00: block and escalate",
        "implementation": "post-processing hook in refund_processor.execute()",
        "enforcement": "block_with_escalation",
        "escalation_target": "human_review_queue",
        "test_coverage": "98%",
        "adversarial_tests_added": [
            "test_tax_credit_bypass_blocked",
            "test_discount_code_bypass_blocked",
            "test_multi_item_partial_refund_limit",
            "test_store_credit_conversion_limit",
            "test_exchange_differential_refund_limit",
        ],
    }
    a4.created_at = _t(126.5)
    a4.updated_at = _t(126.5)
    a4.selected = True
    artifacts.append(a4)

    a5 = ArtifactRef()
    a5.artifact_id = "demo-art-ecom-05"
    a5.task_id = "demo-task-ecom-08"
    a5.session_id = ECOM_SESSION_3_ID
    a5.project_id = ECOM_PROJECT_ID
    a5.artifact_type = ArtifactType.EVAL
    a5.title = "Post-hardening eval — 105 conversations (v0.9.0-rc)"
    a5.summary = "Trajectory quality 0.89. Zero guardrail bypasses. Hard gate PASSED."
    a5.payload = {
        "eval_run_id": "eval-run-ecom-hardened",
        "conversation_count": 105,
        "trajectory_quality": 0.89,
        "outcome_quality": 0.93,
        "hard_gate_passed": True,
        "hard_gate_threshold": 0.80,
        "failure_breakdown": {
            "order_not_found_unhandled": 1,
        },
        "guardrail_enforcement_rate": 1.0,
        "adversarial_tests_passed": 5,
        "adversarial_tests_failed": 0,
        "improvement_vs_baseline": "+0.17 trajectory quality",
    }
    a5.created_at = _t(135.5)
    a5.updated_at = _t(135.5)
    a5.selected = True
    artifacts.append(a5)

    return artifacts


def _ecom_approvals() -> list[ApprovalRequest]:
    approvals = []

    ap1 = ApprovalRequest()
    ap1.approval_id = "demo-appr-ecom-01"
    ap1.task_id = "demo-task-ecom-07"
    ap1.session_id = ECOM_SESSION_3_ID
    ap1.project_id = ECOM_PROJECT_ID
    ap1.action = PrivilegedAction.SOURCE_WRITE
    ap1.description = (
        "Guardrail author requesting write access to harden refund_amount_limit. "
        "Changes refund check from pre-processing to post-processing hook."
    )
    ap1.scope = ApprovalScope.TASK
    ap1.status = ApprovalStatus.APPROVED
    ap1.risk_level = RiskLevel.HIGH
    ap1.details = {
        "files": [
            "agents/ecom-returns/guardrails/refund_limit.py",
            "agents/ecom-returns/tools/refund_processor.py",
        ],
        "reason": "Fix guardrail bypass allowing refunds > $150 via tax credit adjustment",
        "business_impact": "Closes potential $X,000/day financial exposure",
    }
    ap1.created_at = _t(120.4)
    ap1.updated_at = _t(120.9)
    ap1.resolved_at = _t(120.9)
    ap1.resolved_by = "andrew"
    approvals.append(ap1)

    ap2 = ApprovalRequest()
    ap2.approval_id = "demo-appr-ecom-02"
    ap2.task_id = "demo-task-ecom-09"
    ap2.session_id = ECOM_SESSION_3_ID
    ap2.project_id = ECOM_PROJECT_ID
    ap2.action = PrivilegedAction.DEPLOYMENT
    ap2.description = (
        "Release manager: deploy RC v0.9.0 to aws-us-east-1-prod at 5% canary. "
        "Eval hard gate passed. Zero guardrail bypasses confirmed."
    )
    ap2.scope = ApprovalScope.ONCE
    ap2.status = ApprovalStatus.APPROVED
    ap2.risk_level = RiskLevel.HIGH
    ap2.details = {
        "release_id": "demo-rc-ecom-01",
        "deployment_target": "aws-us-east-1-prod",
        "canary_pct": 5,
        "eval_trajectory_quality": 0.89,
        "guardrail_enforcement_rate": "100%",
        "rollback_sla_minutes": 2,
    }
    ap2.created_at = _t(136.3)
    ap2.updated_at = _t(136.8)
    ap2.resolved_at = _t(136.8)
    ap2.resolved_by = "andrew"
    approvals.append(ap2)

    ap3 = ApprovalRequest()
    ap3.approval_id = "demo-appr-ecom-03"
    ap3.task_id = "demo-task-ecom-09"
    ap3.session_id = ECOM_SESSION_3_ID
    ap3.project_id = ECOM_PROJECT_ID
    ap3.action = PrivilegedAction.BENCHMARK_SPEND
    ap3.description = (
        "Authorise benchmark spend for 24h canary monitoring: "
        "approx. 500K tokens at canary scale. Est. cost: $8.20."
    )
    ap3.scope = ApprovalScope.TASK
    ap3.status = ApprovalStatus.APPROVED
    ap3.risk_level = RiskLevel.LOW
    ap3.details = {
        "estimated_tokens": 500000,
        "estimated_cost_usd": 8.20,
        "duration_hours": 24,
        "model": "claude-sonnet-4-6",
    }
    ap3.created_at = _t(136.4)
    ap3.updated_at = _t(136.8)
    ap3.resolved_at = _t(136.8)
    ap3.resolved_by = "andrew"
    approvals.append(ap3)

    return approvals


def _ecom_eval_bundles() -> list[EvalBundle]:
    bundles = []

    b1 = EvalBundle()
    b1.bundle_id = "demo-eval-bundle-ecom-01"
    b1.task_id = "demo-task-ecom-05"
    b1.session_id = ECOM_SESSION_2_ID
    b1.project_id = ECOM_PROJECT_ID
    b1.eval_run_ids = ["eval-run-ecom-baseline"]
    b1.baseline_scores = {"trajectory_quality": 0.0, "outcome_quality": 0.0}
    b1.candidate_scores = {"trajectory_quality": 0.72, "outcome_quality": 0.81}
    b1.hard_gate_passed = False
    b1.trajectory_quality = 0.72
    b1.outcome_quality = 0.81
    b1.eval_coverage_pct = 81.0
    b1.notes = "Baseline. 8 critical guardrail bypasses must be fixed before release."
    b1.created_at = _t(79.6)
    b1.updated_at = _t(79.6)
    bundles.append(b1)

    b2 = EvalBundle()
    b2.bundle_id = "demo-eval-bundle-ecom-02"
    b2.task_id = "demo-task-ecom-08"
    b2.session_id = ECOM_SESSION_3_ID
    b2.project_id = ECOM_PROJECT_ID
    b2.eval_run_ids = ["eval-run-ecom-hardened", "eval-run-ecom-baseline"]
    b2.baseline_scores = {"trajectory_quality": 0.72, "outcome_quality": 0.81}
    b2.candidate_scores = {"trajectory_quality": 0.89, "outcome_quality": 0.93}
    b2.hard_gate_passed = True
    b2.trajectory_quality = 0.89
    b2.outcome_quality = 0.93
    b2.eval_coverage_pct = 94.0
    b2.cost_delta_pct = 1.8
    b2.latency_delta_pct = -6.2
    b2.notes = "Post-hardening. Zero guardrail bypasses. Hard gate passed. Ready for deploy."
    b2.created_at = _t(135.6)
    b2.updated_at = _t(135.6)
    bundles.append(b2)

    b3 = EvalBundle()
    b3.bundle_id = "demo-eval-bundle-ecom-03"
    b3.task_id = "demo-task-ecom-09"
    b3.session_id = ECOM_SESSION_3_ID
    b3.project_id = ECOM_PROJECT_ID
    b3.eval_run_ids = ["eval-run-ecom-canary-24h"]
    b3.baseline_scores = {"trajectory_quality": 0.89, "outcome_quality": 0.93}
    b3.candidate_scores = {"trajectory_quality": 0.91, "outcome_quality": 0.94}
    b3.hard_gate_passed = True
    b3.trajectory_quality = 0.91
    b3.outcome_quality = 0.94
    b3.eval_coverage_pct = 97.0
    b3.cost_delta_pct = 0.4
    b3.latency_delta_pct = -1.1
    b3.notes = "24h canary eval on live traffic. SLOs met. Promoting to 100%."
    b3.created_at = _t(152)
    b3.updated_at = _t(152)
    bundles.append(b3)

    return bundles


def _ecom_trace_bookmarks() -> list[TraceBookmark]:
    bookmarks = []

    bm1 = TraceBookmark()
    bm1.bookmark_id = "demo-bm-ecom-01"
    bm1.task_id = "demo-task-ecom-06"
    bm1.session_id = ECOM_SESSION_2_ID
    bm1.project_id = ECOM_PROJECT_ID
    bm1.trace_id = "trace-ecom-7a3bc2"
    bm1.span_id = "span-refund-processor-89"
    bm1.label = "refund guardrail bypass via tax credit — CRITICAL"
    bm1.failure_family = "guardrail_bypass"
    bm1.blame_target = "agents/ecom-returns/guardrails/refund_limit.py:check():14"
    bm1.evidence_links = ["demo-art-ecom-02", "demo-art-ecom-03"]
    bm1.promoted_to_eval = True
    bm1.notes = (
        "Guardrail checks requested_amount=$145 (passes). "
        "refund_processor then applies $12 tax credit, issuing $157 refund — BYPASS. "
        "Promoted to adversarial eval case: test_tax_credit_bypass_blocked."
    )
    bm1.created_at = _t(82.5)
    bm1.updated_at = _t(86.0)
    bookmarks.append(bm1)

    bm2 = TraceBookmark()
    bm2.bookmark_id = "demo-bm-ecom-02"
    bm2.task_id = "demo-task-ecom-06"
    bm2.session_id = ECOM_SESSION_2_ID
    bm2.project_id = ECOM_PROJECT_ID
    bm2.trace_id = "trace-ecom-f8d114"
    bm2.span_id = "span-refund-processor-92"
    bm2.label = "discount code bypass — second bypass vector"
    bm2.failure_family = "guardrail_bypass"
    bm2.blame_target = "agents/ecom-returns/guardrails/refund_limit.py:check():14"
    bm2.evidence_links = ["demo-bm-ecom-01"]
    bm2.promoted_to_eval = True
    bm2.notes = (
        "Second bypass vector: discount code credit applied post-guardrail. "
        "$148 request + $9 discount code = $157 final refund. "
        "Same root cause as bm-ecom-01. Promoted to adversarial eval."
    )
    bm2.created_at = _t(83.0)
    bm2.updated_at = _t(83.0)
    bookmarks.append(bm2)

    bm3 = TraceBookmark()
    bm3.bookmark_id = "demo-bm-ecom-03"
    bm3.task_id = "demo-task-ecom-06"
    bm3.session_id = ECOM_SESSION_2_ID
    bm3.project_id = ECOM_PROJECT_ID
    bm3.trace_id = "trace-ecom-2c9e77"
    bm3.span_id = "span-exchange-handler-31"
    bm3.label = "exchange routing error — secondary issue"
    bm3.failure_family = "routing_error"
    bm3.blame_target = "agents/ecom-returns/exchange_handler.py:route():31"
    bm3.evidence_links = []
    bm3.promoted_to_eval = False
    bm3.notes = (
        "2 traces: exchange request for out-of-stock item returns 500 error "
        "instead of graceful 'out of stock' message. Low severity — P2. "
        "Not blocking release."
    )
    bm3.created_at = _t(84.0)
    bm3.updated_at = _t(84.0)
    bookmarks.append(bm3)

    return bookmarks


def _ecom_release() -> ReleaseCandidate:
    rc = ReleaseCandidate()
    rc.release_id = "demo-rc-ecom-01"
    rc.task_id = "demo-task-ecom-09"
    rc.session_id = ECOM_SESSION_3_ID
    rc.project_id = ECOM_PROJECT_ID
    rc.version = "0.9.0"
    rc.artifact_ids = [
        "demo-art-ecom-01",
        "demo-art-ecom-04",
        "demo-art-ecom-05",
    ]
    rc.eval_bundle_id = "demo-eval-bundle-ecom-02"
    rc.status = "deployed"
    rc.deployment_target = "aws-us-east-1-prod"
    rc.approved_at = _t(136.8)
    rc.deployed_at = _t(152)
    rc.changelog = (
        "## ShopFast Returns Bot v0.9.0\n\n"
        "### Added\n"
        "- order_lookup_tool: OMS integration with email verification\n"
        "- returns_policy_tool: 30-day window and condition eligibility\n"
        "- refund_processor: Stripe integration with $150 limit\n"
        "- returns_intake skill: Multi-step return orchestration\n\n"
        "### Fixed\n"
        "- refund_amount_limit guardrail now checks FINAL amount after tax credits\n"
        "- Closes 8 critical guardrail bypass cases\n\n"
        "### Quality\n"
        "- Trajectory quality: 0.89 (was 0.72 at baseline)\n"
        "- Hard gate: PASSED (threshold: 0.80)\n"
        "- Guardrail enforcement: 100% (was 91%)\n\n"
        "### Deployment\n"
        "- 5% canary on aws-us-east-1-prod — 24h monitoring window\n"
        "- Promoting to 100% after canary SLOs confirmed"
    )
    rc.created_at = _t(136.0)
    rc.updated_at = _t(152)
    return rc


# ===========================================================================
# Public API
# ===========================================================================

DEMO_PROJECT_IDS = [AIRLINE_PROJECT_ID, ECOM_PROJECT_ID]


def seed_builder_demo(store: BuilderStore, force: bool = False) -> int:
    """Seed all demo data into the given BuilderStore.

    Returns the total number of objects written.

    If *force* is False (default), skips seeding if either demo project
    already exists in the store. Pass force=True to re-seed regardless.
    """
    if not force:
        existing = store.get_project(AIRLINE_PROJECT_ID)
        if existing is not None:
            return 0

    count = 0

    # --- Airline project ---
    store.save_project(_airline_project())
    count += 1
    for s in _airline_sessions():
        store.save_session(s)
        count += 1
    for t in _airline_tasks():
        store.save_task(t)
        count += 1
    for p in _airline_proposals():
        store.save_proposal(p)
        count += 1
    for a in _airline_artifacts():
        store.save_artifact(a)
        count += 1
    for ap in _airline_approvals():
        store.save_approval(ap)
        count += 1
    for b in _airline_eval_bundles():
        store.save_eval_bundle(b)
        count += 1
    for bm in _airline_trace_bookmarks():
        store.save_trace_bookmark(bm)
        count += 1
    store.save_release(_airline_release())
    count += 1

    # --- E-Commerce project ---
    store.save_project(_ecom_project())
    count += 1
    for s in _ecom_sessions():
        store.save_session(s)
        count += 1
    for t in _ecom_tasks():
        store.save_task(t)
        count += 1
    for p in _ecom_proposals():
        store.save_proposal(p)
        count += 1
    for a in _ecom_artifacts():
        store.save_artifact(a)
        count += 1
    for ap in _ecom_approvals():
        store.save_approval(ap)
        count += 1
    for b in _ecom_eval_bundles():
        store.save_eval_bundle(b)
        count += 1
    for bm in _ecom_trace_bookmarks():
        store.save_trace_bookmark(bm)
        count += 1
    store.save_release(_ecom_release())
    count += 1

    return count


def reset_builder_demo(store: BuilderStore) -> int:
    """Delete all demo data from the store. Returns number of deleted objects."""
    count = 0

    for project_id, sessions, tasks, proposals, artifacts, approvals, bundles, bookmarks, release_id in [
        (
            AIRLINE_PROJECT_ID,
            [AIRLINE_SESSION_1_ID, AIRLINE_SESSION_2_ID, AIRLINE_SESSION_3_ID],
            [f"demo-task-airline-{i:02d}" for i in range(1, 13)],
            ["demo-prop-airline-01", "demo-prop-airline-02", "demo-prop-airline-03", "demo-prop-airline-04"],
            [f"demo-art-airline-{i:02d}" for i in range(1, 12)],
            ["demo-appr-airline-01", "demo-appr-airline-02"],
            ["demo-eval-bundle-airline-01", "demo-eval-bundle-airline-02"],
            ["demo-bm-airline-01", "demo-bm-airline-02"],
            "demo-rc-airline-01",
        ),
        (
            ECOM_PROJECT_ID,
            [ECOM_SESSION_1_ID, ECOM_SESSION_2_ID, ECOM_SESSION_3_ID],
            [f"demo-task-ecom-{i:02d}" for i in range(1, 10)],
            ["demo-prop-ecom-01", "demo-prop-ecom-02", "demo-prop-ecom-03"],
            [f"demo-art-ecom-{i:02d}" for i in range(1, 6)],
            ["demo-appr-ecom-01", "demo-appr-ecom-02", "demo-appr-ecom-03"],
            ["demo-eval-bundle-ecom-01", "demo-eval-bundle-ecom-02", "demo-eval-bundle-ecom-03"],
            ["demo-bm-ecom-01", "demo-bm-ecom-02", "demo-bm-ecom-03"],
            "demo-rc-ecom-01",
        ),
    ]:
        if store.delete_project(project_id):
            count += 1
        for sid in sessions:
            if store.delete_session(sid):
                count += 1
        for tid in tasks:
            if store.delete_task(tid):
                count += 1
        for pid in proposals:
            if store.delete_proposal(pid):
                count += 1
        for aid in artifacts:
            if store.delete_artifact(aid):
                count += 1
        for apid in approvals:
            if store.delete_approval(apid):
                count += 1
        for bid in bundles:
            if store.delete_eval_bundle(bid):
                count += 1
        for bmid in bookmarks:
            if store.delete_trace_bookmark(bmid):
                count += 1
        if store.delete_release(release_id):
            count += 1

    return count


# Demo act definitions — describe which data is relevant per act
DEMO_ACTS = [
    {
        "act_id": "act1_build",
        "number": 1,
        "title": "Build",
        "subtitle": "User describes an agent; orchestrator creates a plan",
        "description": (
            "The user describes their agent requirements in plain language. "
            "The orchestrator hands off to the requirements analyst, who produces "
            "a structured plan with goals, constraints, and milestones. The ADK "
            "architect designs the multi-agent graph."
        ),
        "narrator": (
            "Every agent starts with a conversation. The user types their vision; "
            "the orchestrator assembles a team. Watch how the requirements analyst "
            "structures ambiguity into concrete milestones, and the ADK architect "
            "produces a graph diff you can review and approve."
        ),
        "spotlight": "conversation",
        "featured_objects": {
            "projects": [AIRLINE_PROJECT_ID],
            "sessions": [AIRLINE_SESSION_1_ID],
            "tasks": ["demo-task-airline-01", "demo-task-airline-02"],
            "artifacts": ["demo-art-airline-01", "demo-art-airline-02"],
            "proposals": ["demo-prop-airline-01", "demo-prop-airline-02"],
        },
    },
    {
        "act_id": "act2_develop",
        "number": 2,
        "title": "Develop",
        "subtitle": "Specialists implement tools, skills, and guardrails",
        "description": (
            "The tool engineer scaffolds API-connected tools. The skill author "
            "assembles multi-step skills. The guardrail author adds PII filters and "
            "content policies. All changes are proposed before any file is written."
        ),
        "narrator": (
            "Specialists work in parallel inside isolated worktrees. The tool engineer "
            "writes the Sabre GDS integration; the skill author chains it into a rebooking "
            "flow; the guardrail author adds PII masking before a single line touches prod. "
            "Every mutation requires your approval."
        ),
        "spotlight": "inspector",
        "featured_objects": {
            "projects": [AIRLINE_PROJECT_ID],
            "sessions": [AIRLINE_SESSION_2_ID],
            "tasks": [
                "demo-task-airline-03",
                "demo-task-airline-04",
                "demo-task-airline-05",
                "demo-task-airline-06",
            ],
            "artifacts": [
                "demo-art-airline-03",
                "demo-art-airline-04",
                "demo-art-airline-05",
                "demo-art-airline-06",
            ],
            "approvals": ["demo-appr-airline-01"],
        },
    },
    {
        "act_id": "act3_evaluate",
        "number": 3,
        "title": "Evaluate",
        "subtitle": "Evals run, traces analyzed, issues surfaced",
        "description": (
            "The eval author runs 120 conversations against the agent. Trajectory quality "
            "comes in at 0.61 — below the 0.80 hard gate. The trace analyst drills into "
            "23 failures, bookmarks the root-cause span, and files a precise bug report."
        ),
        "narrator": (
            "Before anything ships, evals catch what code review misses. "
            "120 conversations. 23 failures. One root cause: a schema mismatch in "
            "seat_inventory_tool. The trace analyst pinpoints the exact span, "
            "promotes it to an eval case, and hands a concrete fix to the tool engineer."
        ),
        "spotlight": "traces",
        "featured_objects": {
            "projects": [AIRLINE_PROJECT_ID],
            "sessions": [AIRLINE_SESSION_2_ID, AIRLINE_SESSION_3_ID],
            "tasks": ["demo-task-airline-07", "demo-task-airline-08"],
            "artifacts": ["demo-art-airline-07", "demo-art-airline-08"],
            "eval_bundles": ["demo-eval-bundle-airline-01"],
            "trace_bookmarks": ["demo-bm-airline-01", "demo-bm-airline-02"],
        },
    },
    {
        "act_id": "act4_optimize",
        "number": 4,
        "title": "Optimize",
        "subtitle": "Propose fix, re-evaluate, compare candidates",
        "description": (
            "The tool engineer proposes a targeted fix: wrap the seat list in a "
            "{seat_map: ...} envelope, add pydantic validation, add a unit test. "
            "You approve the source write, evals re-run, and trajectory quality "
            "jumps from 0.61 to 0.84."
        ),
        "narrator": (
            "One proposal. One approval. One diff. That's how issues close in the Builder. "
            "The fix is surgical — 12 lines changed, a pydantic model added, a unit test "
            "written for the empty-flight edge case. Re-run evals confirm: 0.61 → 0.84. "
            "Hard gate cleared."
        ),
        "spotlight": "diff",
        "featured_objects": {
            "projects": [AIRLINE_PROJECT_ID],
            "sessions": [AIRLINE_SESSION_3_ID],
            "tasks": ["demo-task-airline-09", "demo-task-airline-10"],
            "artifacts": ["demo-art-airline-09", "demo-art-airline-10"],
            "proposals": ["demo-prop-airline-03"],
            "eval_bundles": ["demo-eval-bundle-airline-02"],
            "approvals": ["demo-appr-airline-01"],
        },
    },
    {
        "act_id": "act5_ship",
        "number": 5,
        "title": "Ship",
        "subtitle": "Release candidate created, approved, and deployed",
        "description": (
            "The release manager bundles all approved artifacts into RC v1.0.0, "
            "generates a structured changelog, and files a deployment approval request. "
            "The release card shows eval scores, artifact manifest, and rollback plan. "
            "One click to deploy."
        ),
        "narrator": (
            "Every release is an audit trail. RC v1.0.0 carries the full provenance: "
            "which artifacts changed, which evals passed, which specialist authored each fix. "
            "The deployment approval request is waiting for your signature. "
            "Click Approve — and SkyLink Airlines CS Agent goes live."
        ),
        "spotlight": "config",
        "featured_objects": {
            "projects": [AIRLINE_PROJECT_ID],
            "sessions": [AIRLINE_SESSION_3_ID],
            "tasks": ["demo-task-airline-11", "demo-task-airline-12"],
            "artifacts": ["demo-art-airline-11"],
            "proposals": ["demo-prop-airline-04"],
            "approvals": ["demo-appr-airline-02"],
            "releases": ["demo-rc-airline-01"],
        },
    },
]

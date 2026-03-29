"""Tests for AutoFix route contracts used by the frontend review flow."""

from __future__ import annotations

import time

import pytest

fastapi = pytest.importorskip("fastapi", reason="fastapi not installed")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import autofix as autofix_routes
from optimizer.autofix import AutoFixProposal


class _FakeEventLog:
    """Collect appended events so route behavior can be asserted."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict]] = []

    def append(self, event_type: str, payload: dict) -> None:
        self.events.append((event_type, payload))


class _FakeDeployer:
    """Expose a minimal active config for apply routes."""

    def get_active_config(self) -> dict:
        return {"prompts": {"root": "Original prompt"}}


class _FakeAutoFixEngine:
    """Provide predictable proposal, apply, and reject behavior for route tests."""

    def __init__(self) -> None:
        now = time.time()
        self.proposal = AutoFixProposal(
            proposal_id="fix-001",
            mutation_name="instruction_rewrite",
            surface="instructions.root",
            params={"text": "Updated prompt"},
            expected_lift=0.12,
            risk_class="low",
            affected_eval_slices=["routing"],
            cost_impact_estimate=0.01,
            diff_preview="- Original prompt\n+ Updated prompt",
            status="pending",
            created_at=now,
        )

    def history(self, limit: int = 50) -> list[AutoFixProposal]:
        del limit
        return [self.proposal]

    def apply(self, proposal_id: str, current_config: dict) -> tuple[dict, str]:
        assert proposal_id == self.proposal.proposal_id
        assert current_config["prompts"]["root"] == "Original prompt"
        self.proposal.status = "applied"
        self.proposal.applied_at = self.proposal.created_at + 10
        return current_config | {"applied": True}, f"Applied {proposal_id}"

    def reject(self, proposal_id: str) -> str:
        assert proposal_id == self.proposal.proposal_id
        self.proposal.status = "rejected"
        return f"Rejected {proposal_id}"


@pytest.fixture()
def event_log() -> _FakeEventLog:
    """Provide a fresh fake event log for each route test."""

    return _FakeEventLog()


@pytest.fixture()
def client(event_log: _FakeEventLog) -> TestClient:
    """Build a minimal app exposing the AutoFix router with fake dependencies."""

    app = FastAPI()
    app.include_router(autofix_routes.router)
    app.state.autofix_engine = _FakeAutoFixEngine()
    app.state.deployer = _FakeDeployer()
    app.state.event_log = event_log
    return TestClient(app)


def test_list_proposals_matches_frontend_shape(client: TestClient) -> None:
    """Proposal cards should receive the fields the React page renders."""

    response = client.get("/api/autofix/proposals")

    assert response.status_code == 200
    proposal = response.json()["proposals"][0]
    assert proposal["operator_name"] == "instruction_rewrite"
    assert proposal["operator_params"] == {"text": "Updated prompt"}
    assert proposal["proposer_name"] == "AutoFix Engine"
    assert proposal["rationale"]


def test_history_uses_history_key_for_review_timeline(client: TestClient) -> None:
    """History responses should expose the `history` collection expected by the hook."""

    response = client.get("/api/autofix/history")

    assert response.status_code == 200
    history_entry = response.json()["history"][0]
    assert history_entry["proposal_id"] == "fix-001"
    assert history_entry["message"]


def test_reject_route_records_rejection_and_logs_event(
    client: TestClient,
    event_log: _FakeEventLog,
) -> None:
    """Rejecting a proposal should update the response status and emit an audit event."""

    response = client.post("/api/autofix/reject/fix-001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "rejected"
    assert payload["message"] == "Rejected fix-001"
    assert ("autofix_rejected", {"proposal_id": "fix-001", "status": "Rejected fix-001"}) in event_log.events

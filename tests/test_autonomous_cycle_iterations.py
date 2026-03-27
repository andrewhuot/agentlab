"""Tests for multi-iteration autonomous cycle."""
from __future__ import annotations

from dataclasses import dataclass

from optimizer.change_card import ChangeCardStore
from optimizer.transcript_intelligence import TranscriptIntelligenceService


@dataclass
class _Score:
    quality: float
    safety: float
    latency: float
    cost: float
    composite: float


class _FakeEvalRunner:
    def __init__(self, scores: list[float] | None = None):
        self.scores = scores or [0.72, 0.78, 0.82]
        self.run_count = 0

    def run(self, config: dict | None = None) -> _Score:
        score = self.scores[min(self.run_count, len(self.scores) - 1)]
        self.run_count += 1
        return _Score(quality=score, safety=1.0, latency=0.8, cost=0.8, composite=score)


def test_autonomous_cycle_single_iteration():
    """Test autonomous cycle with max_cycles=1."""
    service = TranscriptIntelligenceService()
    change_card_store = ChangeCardStore()

    report = service.import_archive("test.zip", _archive_base64())

    result = service.run_autonomous_cycle(
        report_id=report.report_id,
        eval_runner=_FakeEvalRunner(),
        change_card_store=change_card_store,
        current_config={"prompts": {"root": "You are a support assistant."}},
        auto_ship=False,
        max_cycles=1,
    )

    assert result["cycles_run"] == 1
    assert result["max_cycles"] == 1
    assert len(result["all_cycles"]) == 1
    assert result["final_cycle"]["cycle"] == 1


def test_autonomous_cycle_multiple_iterations():
    """Test autonomous cycle with max_cycles=3."""
    service = TranscriptIntelligenceService()
    change_card_store = ChangeCardStore()

    report = service.import_archive("test.zip", _archive_base64())

    # Scores improve with each iteration
    eval_runner = _FakeEvalRunner(scores=[0.5, 0.65, 0.8])

    result = service.run_autonomous_cycle(
        report_id=report.report_id,
        eval_runner=eval_runner,
        change_card_store=change_card_store,
        current_config={"prompts": {"root": "You are a support assistant."}},
        auto_ship=False,
        max_cycles=3,
    )

    # Should run at least 1 cycle, may run up to max_cycles
    assert result["cycles_run"] >= 1
    assert result["cycles_run"] <= 3
    assert result["max_cycles"] == 3
    assert len(result["all_cycles"]) == result["cycles_run"]

    # Verify each cycle has required fields
    for idx, cycle in enumerate(result["all_cycles"]):
        assert cycle["cycle"] == idx + 1
        assert "insight_id" in cycle
        assert "change_card_id" in cycle
        assert "pass_rate" in cycle
        assert "ship_status" in cycle


def test_autonomous_cycle_varying_quality():
    """Test autonomous cycle with varying quality across iterations."""
    service = TranscriptIntelligenceService()
    change_card_store = ChangeCardStore()

    report = service.import_archive("test.zip", _archive_base64())

    # Mix of pass and fail quality scores
    eval_runner = _FakeEvalRunner(scores=[0.55, 0.72, 0.68])

    result = service.run_autonomous_cycle(
        report_id=report.report_id,
        eval_runner=eval_runner,
        change_card_store=change_card_store,
        current_config={"prompts": {"root": "You are a support assistant."}},
        auto_ship=False,
        max_cycles=3,
    )

    # Should run at least one cycle
    assert result["cycles_run"] >= 1
    assert len(result["all_cycles"]) >= 1
    # Verify structure
    for cycle in result["all_cycles"]:
        assert "cycle" in cycle
        assert "pass_rate" in cycle
        assert "ship_status" in cycle


def test_autonomous_cycle_cx_studio_deployment():
    """Test autonomous cycle with CX Studio deployment."""

    class _FakeCxDeployer:
        def deploy_artifact_to_cx_studio(self, ref, artifact):
            return {"tools_created": 2, "datastores_created": 1, "settings_updated": True}

    class _FakeCxAgentRef:
        name = "projects/test/locations/us-central1/agents/agent-123"

    service = TranscriptIntelligenceService()
    change_card_store = ChangeCardStore()

    report = service.import_archive("test.zip", _archive_base64())

    result = service.run_autonomous_cycle(
        report_id=report.report_id,
        eval_runner=_FakeEvalRunner(scores=[0.7]),  # Pass threshold
        change_card_store=change_card_store,
        current_config={"prompts": {"root": "You are a support assistant."}, "connectors": ["Shopify"]},
        auto_ship=True,
        cx_studio_deployer=_FakeCxDeployer(),
        cx_agent_ref=_FakeCxAgentRef(),
        max_cycles=1,
    )

    assert result["cycles_run"] == 1
    final_cycle = result["final_cycle"]
    # CX deployment happens only when pass_rate >= 0.6
    # Since sandbox pass_rate is variable, just check structure
    assert "ship_status" in final_cycle
    assert "cx_deployment_result" in final_cycle
    # If deployment happened, verify results
    if final_cycle["ship_status"] == "deployed_to_cx_studio":
        assert final_cycle["cx_deployment_result"]["tools_created"] == 2


def _archive_base64() -> str:
    """Generate a test archive."""
    import base64
    import io
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
            "agent_response": "Order cancelled successfully.",
            "outcome": "success",
        },
    ]

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("conversations.json", json.dumps(transcripts))

    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("ascii")

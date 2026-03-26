"""Tests for control, events, and specialized health API endpoints."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

fastapi = pytest.importorskip("fastapi", reason="FastAPI not installed")
from fastapi.testclient import TestClient  # noqa: E402

from api.server import app  # noqa: E402
from data.event_log import EventLog  # noqa: E402
from optimizer.cost_tracker import CostTracker  # noqa: E402
from optimizer.human_control import HumanControlStore  # noqa: E402


@pytest.fixture
def test_client(tmp_path: Path):
    """Create a TestClient with mocked app state dependencies."""
    # Mock all required app.state attributes
    app.state.control_store = HumanControlStore(path=str(tmp_path / "control.json"))
    app.state.event_log = EventLog(db_path=str(tmp_path / "events.db"))
    app.state.cost_tracker = CostTracker(
        db_path=str(tmp_path / "cost.db"),
        per_cycle_budget_dollars=1.0,
        daily_budget_dollars=10.0,
        stall_threshold_cycles=5,
    )

    # Mock deployer with version_manager
    mock_deployer = MagicMock()
    mock_deployer.version_manager.manifest = {}
    mock_deployer.get_active_config.return_value = {"model": "claude-3-5-sonnet-20241022"}
    app.state.deployer = mock_deployer

    # Mock eval_runner
    mock_eval_runner = MagicMock()
    mock_score = MagicMock()
    mock_score.quality = 0.9
    mock_score.safety = 1.0
    mock_score.latency = 150.0
    mock_score.cost = 0.001
    mock_score.composite = 0.85
    mock_eval_runner.run.return_value = mock_score
    app.state.eval_runner = mock_eval_runner

    # Mock runtime config
    mock_runtime = MagicMock()
    mock_runtime.budget.per_cycle_dollars = 1.0
    mock_runtime.budget.daily_dollars = 10.0
    mock_runtime.budget.stall_threshold_cycles = 5
    app.state.runtime_config = mock_runtime

    return TestClient(app)


class TestControlEndpoints:
    """Test human control API endpoints."""

    def test_get_control_state_default(self, test_client):
        """Test getting default control state."""
        response = test_client.get("/api/control/state")
        assert response.status_code == 200
        data = response.json()
        assert data["paused"] is False
        assert data["immutable_surfaces"] == []
        assert data["rejected_experiments"] == []
        assert data["last_injected_mutation"] is None
        assert "updated_at" in data

    def test_pause_endpoint(self, test_client):
        """Test pause endpoint sets paused=True and logs event."""
        response = test_client.post("/api/control/pause")
        assert response.status_code == 200
        data = response.json()
        assert data["paused"] is True

        # Verify state persisted
        state_response = test_client.get("/api/control/state")
        assert state_response.json()["paused"] is True

        # Verify event logged
        events = test_client.get("/api/events?event_type=human_pause").json()
        assert len(events["events"]) == 1
        assert events["events"][0]["event_type"] == "human_pause"

    def test_resume_endpoint(self, test_client):
        """Test resume endpoint sets paused=False."""
        # First pause
        test_client.post("/api/control/pause")

        # Then resume
        response = test_client.post("/api/control/resume")
        assert response.status_code == 200
        data = response.json()
        assert data["paused"] is False

        # Verify state persisted
        state_response = test_client.get("/api/control/state")
        assert state_response.json()["paused"] is False

    def test_pin_surface(self, test_client):
        """Test pinning a surface makes it immutable."""
        response = test_client.post("/api/control/pin/system_prompt")
        assert response.status_code == 200
        data = response.json()
        assert "system_prompt" in data["immutable_surfaces"]

        # Verify state persisted
        state_response = test_client.get("/api/control/state")
        assert "system_prompt" in state_response.json()["immutable_surfaces"]

    def test_pin_surface_duplicate(self, test_client):
        """Test pinning same surface twice doesn't duplicate it."""
        test_client.post("/api/control/pin/system_prompt")
        test_client.post("/api/control/pin/system_prompt")

        state_response = test_client.get("/api/control/state")
        surfaces = state_response.json()["immutable_surfaces"]
        assert surfaces.count("system_prompt") == 1

    def test_unpin_surface(self, test_client):
        """Test unpinning a surface removes it from immutables."""
        # First pin
        test_client.post("/api/control/pin/system_prompt")

        # Then unpin
        response = test_client.post("/api/control/unpin/system_prompt")
        assert response.status_code == 200
        data = response.json()
        assert "system_prompt" not in data["immutable_surfaces"]

        # Verify state persisted
        state_response = test_client.get("/api/control/state")
        assert "system_prompt" not in state_response.json()["immutable_surfaces"]

    def test_unpin_nonexistent_surface(self, test_client):
        """Test unpinning a surface that wasn't pinned is safe."""
        response = test_client.post("/api/control/unpin/nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert "nonexistent" not in data["immutable_surfaces"]

    def test_reject_experiment_no_canary(self, test_client):
        """Test rejecting experiment without active canary."""
        response = test_client.post("/api/control/reject/exp_123")
        assert response.status_code == 200
        data = response.json()
        assert "exp_123" in data["rejected_experiments"]
        assert data["rollback"] is None

        # Verify event logged
        events = test_client.get("/api/events?event_type=human_reject").json()
        assert len(events["events"]) == 1
        assert events["events"][0]["payload"]["experiment_id"] == "exp_123"

    def test_reject_experiment_with_canary(self, test_client):
        """Test rejecting experiment triggers canary rollback."""
        # Setup active canary
        app.state.deployer.version_manager.manifest = {"canary_version": 5}
        app.state.deployer.version_manager.rollback = MagicMock()

        response = test_client.post("/api/control/reject/exp_456")
        assert response.status_code == 200
        data = response.json()
        assert "exp_456" in data["rejected_experiments"]
        assert data["rollback"] == "Rolled back canary v005"

        # Verify rollback was called
        app.state.deployer.version_manager.rollback.assert_called_once_with(5)

        # Verify rollback event logged
        events = test_client.get("/api/events?event_type=rollback_triggered").json()
        assert len(events["events"]) == 1
        assert events["events"][0]["payload"]["canary_version"] == 5
        assert events["events"][0]["payload"]["reason"] == "human_reject"

    def test_inject_endpoint_with_full_config(self, test_client):
        """Test injecting a complete config mutation."""
        mutation = {
            "config": {
                "model": "claude-3-opus-20240229",
                "temperature": 0.5,
            }
        }

        # Mock deployer.deploy to return a message
        app.state.deployer.deploy = MagicMock(return_value="Deployed as canary v006")

        response = test_client.post("/api/control/inject", json=mutation)
        assert response.status_code == 200
        data = response.json()
        assert data["last_injected_mutation"] == "api_payload"
        assert data["deploy_message"] == "Deployed as canary v006"
        assert data["composite"] == 0.85

        # Verify eval was run with the config
        app.state.eval_runner.run.assert_called_once()
        call_kwargs = app.state.eval_runner.run.call_args.kwargs
        assert call_kwargs["config"] == mutation["config"]

        # Verify deploy was called
        app.state.deployer.deploy.assert_called_once()

        # Verify event logged
        events = test_client.get("/api/events?event_type=human_inject").json()
        assert len(events["events"]) == 1

    def test_inject_endpoint_with_patch(self, test_client):
        """Test injecting a partial config patch gets merged."""
        patch = {"temperature": 0.7}

        app.state.deployer.deploy = MagicMock(return_value="Deployed as canary v007")

        response = test_client.post("/api/control/inject", json=patch)
        assert response.status_code == 200

        # Verify eval was run with merged config
        call_kwargs = app.state.eval_runner.run.call_args.kwargs
        merged = call_kwargs["config"]
        assert merged["model"] == "claude-3-5-sonnet-20241022"  # from base
        assert merged["temperature"] == 0.7  # from patch

    def test_inject_endpoint_deep_merge(self, test_client):
        """Test deep merge for nested config objects."""
        app.state.deployer.get_active_config.return_value = {
            "model": "claude-3-5-sonnet-20241022",
            "safety": {"content_policy": "strict"},
        }

        patch = {
            "safety": {"max_retries": 3}
        }

        app.state.deployer.deploy = MagicMock(return_value="Deployed")

        response = test_client.post("/api/control/inject", json=patch)
        assert response.status_code == 200

        # Verify deep merge happened
        call_kwargs = app.state.eval_runner.run.call_args.kwargs
        merged = call_kwargs["config"]
        assert merged["safety"]["content_policy"] == "strict"  # preserved
        assert merged["safety"]["max_retries"] == 3  # added

    def test_inject_endpoint_empty_body(self, test_client):
        """Test inject with empty body returns 400."""
        response = test_client.post("/api/control/inject", json={})
        assert response.status_code == 400
        assert "Mutation payload required" in response.json()["detail"]

    def test_inject_endpoint_no_body(self, test_client):
        """Test inject with no JSON body returns 400."""
        response = test_client.post("/api/control/inject")
        assert response.status_code == 400


class TestEventsEndpoints:
    """Test event log API endpoints."""

    def test_list_events_default(self, test_client):
        """Test listing events with default parameters."""
        # Add some events
        app.state.event_log.append(event_type="eval_started", payload={"config": "v001"})
        app.state.event_log.append(event_type="eval_completed", payload={"score": 0.85})
        app.state.event_log.append(event_type="human_pause", payload={"paused": True})

        response = test_client.get("/api/events")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert len(data["events"]) == 3

        # Verify reverse chronological order (most recent first)
        assert data["events"][0]["event_type"] == "human_pause"
        assert data["events"][1]["event_type"] == "eval_completed"
        assert data["events"][2]["event_type"] == "eval_started"

    def test_list_events_with_limit(self, test_client):
        """Test limiting number of events returned."""
        # Add multiple events
        for i in range(10):
            app.state.event_log.append(
                event_type="eval_started",
                payload={"iteration": i}
            )

        response = test_client.get("/api/events?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 5

    def test_list_events_filter_by_type(self, test_client):
        """Test filtering events by event_type."""
        app.state.event_log.append(event_type="eval_started", payload={})
        app.state.event_log.append(event_type="human_pause", payload={})
        app.state.event_log.append(event_type="eval_started", payload={})
        app.state.event_log.append(event_type="human_reject", payload={})

        response = test_client.get("/api/events?event_type=eval_started")
        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 2
        assert all(e["event_type"] == "eval_started" for e in data["events"])

    def test_list_events_empty_log(self, test_client):
        """Test listing events when log is empty."""
        response = test_client.get("/api/events")
        assert response.status_code == 200
        data = response.json()
        assert data["events"] == []

    def test_list_events_limit_bounds(self, test_client):
        """Test limit parameter bounds validation."""
        # Limit too small (< 1)
        response = test_client.get("/api/events?limit=0")
        assert response.status_code == 422  # Validation error

        # Limit too large (> 1000)
        response = test_client.get("/api/events?limit=1001")
        assert response.status_code == 422

        # Valid bounds
        response = test_client.get("/api/events?limit=1")
        assert response.status_code == 200

        response = test_client.get("/api/events?limit=1000")
        assert response.status_code == 200

    def test_list_events_includes_metadata(self, test_client):
        """Test events include all expected metadata fields."""
        app.state.event_log.append(
            event_type="candidate_promoted",
            payload={"version": 10},
            cycle_id="cycle_1",
            experiment_id="exp_1",
        )

        response = test_client.get("/api/events")
        assert response.status_code == 200
        event = response.json()["events"][0]

        assert "id" in event
        assert "timestamp" in event
        assert event["event_type"] == "candidate_promoted"
        assert event["payload"]["version"] == 10
        assert event["cycle_id"] == "cycle_1"
        assert event["experiment_id"] == "exp_1"


class TestHealthCostEndpoint:
    """Test /health/cost endpoint."""

    def test_cost_health_default(self, test_client):
        """Test cost health endpoint returns summary and budgets."""
        response = test_client.get("/api/health/cost")
        assert response.status_code == 200
        data = response.json()

        assert "summary" in data
        assert "budgets" in data
        assert "recent_cycles" in data
        assert "stall_detected" in data

        # Verify budget fields
        assert data["budgets"]["per_cycle_dollars"] == 1.0
        assert data["budgets"]["daily_dollars"] == 10.0
        assert data["budgets"]["stall_threshold_cycles"] == 5

    def test_cost_health_with_cycles(self, test_client):
        """Test cost health includes cycle trend data."""
        # Record some cycles
        app.state.cost_tracker.record_cycle("cycle_1", 0.5, 0.02)
        app.state.cost_tracker.record_cycle("cycle_2", 0.3, 0.01)
        app.state.cost_tracker.record_cycle("cycle_3", 0.4, 0.0)  # no improvement

        response = test_client.get("/api/health/cost")
        assert response.status_code == 200
        data = response.json()

        assert len(data["recent_cycles"]) == 3

        # Verify cumulative tracking
        cycle_1 = data["recent_cycles"][0]
        assert cycle_1["cycle_id"] == "cycle_1"
        assert cycle_1["spent_dollars"] == 0.5
        assert cycle_1["improvement_delta"] == 0.02
        assert cycle_1["cumulative_spend"] == 0.5
        assert cycle_1["running_cost_per_improvement"] == 25.0  # 0.5 / 0.02

        cycle_2 = data["recent_cycles"][1]
        assert cycle_2["cumulative_spend"] == 0.8  # 0.5 + 0.3
        assert abs(cycle_2["running_cost_per_improvement"] - 26.666667) < 0.01

        # Zero improvement cycles don't break cost-per-improvement
        cycle_3 = data["recent_cycles"][2]
        assert cycle_3["improvement_delta"] == 0.0
        assert cycle_3["running_cost_per_improvement"] == 40.0  # 1.2 / 0.03

    def test_cost_health_custom_limit(self, test_client):
        """Test limiting number of recent cycles returned."""
        for i in range(10):
            app.state.cost_tracker.record_cycle(f"cycle_{i}", 0.1, 0.01)

        response = test_client.get("/api/health/cost?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["recent_cycles"]) == 3

    def test_cost_health_stall_detection(self, test_client):
        """Test stall_detected flag when no improvements."""
        # Record cycles with no improvement
        for i in range(6):
            app.state.cost_tracker.record_cycle(f"cycle_{i}", 0.5, 0.0)

        response = test_client.get("/api/health/cost")
        assert response.status_code == 200
        data = response.json()
        assert data["stall_detected"] is True

    def test_cost_health_no_stall(self, test_client):
        """Test stall_detected is False when improvements exist."""
        app.state.cost_tracker.record_cycle("cycle_1", 0.5, 0.02)

        response = test_client.get("/api/health/cost")
        assert response.status_code == 200
        data = response.json()
        assert data["stall_detected"] is False

    def test_cost_health_empty_tracker(self, test_client):
        """Test cost health with no cycle history."""
        response = test_client.get("/api/health/cost")
        assert response.status_code == 200
        data = response.json()
        assert data["recent_cycles"] == []
        assert data["stall_detected"] is False

    def test_cost_health_limit_bounds(self, test_client):
        """Test limit parameter validation."""
        # Too small
        response = test_client.get("/api/health/cost?limit=0")
        assert response.status_code == 422

        # Too large
        response = test_client.get("/api/health/cost?limit=366")
        assert response.status_code == 422

        # Valid bounds
        response = test_client.get("/api/health/cost?limit=1")
        assert response.status_code == 200

        response = test_client.get("/api/health/cost?limit=365")
        assert response.status_code == 200


class TestHealthEvalSetEndpoint:
    """Test /health/eval-set endpoint."""

    def test_eval_set_health_structure(self, test_client):
        """Test eval-set health returns expected structure."""
        response = test_client.get("/api/health/eval-set")
        assert response.status_code == 200
        data = response.json()

        assert "analysis" in data
        assert "difficulty_distribution" in data

        # Verify analysis fields
        assert "saturated" in data["analysis"]
        assert "unsolvable" in data["analysis"]
        assert "high_leverage" in data["analysis"]

        # Verify difficulty distribution fields
        assert "easy" in data["difficulty_distribution"]
        assert "medium" in data["difficulty_distribution"]
        assert "hard" in data["difficulty_distribution"]

    def test_eval_set_health_default_values(self, test_client):
        """Test eval-set health returns placeholder zeros."""
        # Current implementation returns zeros (placeholder)
        response = test_client.get("/api/health/eval-set")
        assert response.status_code == 200
        data = response.json()

        # All values should be zero (stub implementation)
        assert data["analysis"]["saturated"] == 0
        assert data["analysis"]["unsolvable"] == 0
        assert data["analysis"]["high_leverage"] == 0
        assert data["difficulty_distribution"]["easy"] == 0
        assert data["difficulty_distribution"]["medium"] == 0
        assert data["difficulty_distribution"]["hard"] == 0


class TestControlEventsIntegration:
    """Integration tests combining control and event endpoints."""

    def test_control_actions_generate_events(self, test_client):
        """Test that control actions properly log events."""
        # Pause action
        test_client.post("/api/control/pause")
        events = test_client.get("/api/events?event_type=human_pause").json()
        assert len(events["events"]) == 1

        # Reject action
        test_client.post("/api/control/reject/exp_123")
        events = test_client.get("/api/events?event_type=human_reject").json()
        assert len(events["events"]) == 1

        # Inject action
        app.state.deployer.deploy = MagicMock(return_value="Deployed")
        test_client.post("/api/control/inject", json={"temperature": 0.5})
        events = test_client.get("/api/events?event_type=human_inject").json()
        assert len(events["events"]) == 1

    def test_reject_with_canary_logs_multiple_events(self, test_client):
        """Test rejecting with canary logs both reject and rollback events."""
        app.state.deployer.version_manager.manifest = {"canary_version": 10}
        app.state.deployer.version_manager.rollback = MagicMock()

        test_client.post("/api/control/reject/exp_999")

        # Should have human_reject event
        reject_events = test_client.get("/api/events?event_type=human_reject").json()
        assert len(reject_events["events"]) == 1
        assert reject_events["events"][0]["experiment_id"] == "exp_999"

        # Should have rollback_triggered event
        rollback_events = test_client.get("/api/events?event_type=rollback_triggered").json()
        assert len(rollback_events["events"]) == 1
        assert rollback_events["events"][0]["payload"]["canary_version"] == 10
        assert rollback_events["events"][0]["experiment_id"] == "exp_999"

    def test_state_persistence_across_requests(self, test_client):
        """Test that control state persists across multiple requests."""
        # Pin multiple surfaces
        test_client.post("/api/control/pin/system_prompt")
        test_client.post("/api/control/pin/tools")
        test_client.post("/api/control/pin/safety_config")

        # Reject experiments
        test_client.post("/api/control/reject/exp_1")
        test_client.post("/api/control/reject/exp_2")

        # Pause
        test_client.post("/api/control/pause")

        # Get state
        state = test_client.get("/api/control/state").json()

        assert state["paused"] is True
        assert len(state["immutable_surfaces"]) == 3
        assert set(state["immutable_surfaces"]) == {"system_prompt", "tools", "safety_config"}
        assert len(state["rejected_experiments"]) == 2
        assert set(state["rejected_experiments"]) == {"exp_1", "exp_2"}

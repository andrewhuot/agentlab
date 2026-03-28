"""API tests for experiments routes."""
from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi", reason="fastapi not installed")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.experiments import router


class _StubOptimizer:
    """Minimal optimizer stub exposing get_pareto_snapshot."""

    def get_pareto_snapshot(self) -> dict:
        return {
            "objective_directions": {
                "quality": "maximize",
                "safety": "maximize",
                "latency": "maximize",
                "cost": "maximize",
            },
            "frontier": [
                {
                    "candidate_id": "cand-frontier",
                    "objectives": {
                        "quality": 0.91,
                        "safety": 0.97,
                        "latency": 0.83,
                        "cost": 0.71,
                    },
                    "constraint_violations": [],
                    "config_hash": "cfg-frontier",
                    "experiment_id": "exp-frontier",
                    "created_at": 123.0,
                    "dominated": False,
                }
            ],
            "recommended_candidate_id": "cand-frontier",
            "infeasible": [
                {
                    "candidate_id": "cand-infeasible",
                    "objectives": {
                        "quality": 0.50,
                        "safety": 0.40,
                        "latency": 0.55,
                        "cost": 0.62,
                    },
                    "constraint_violations": ["safety_gate"],
                    "config_hash": "cfg-infeasible",
                    "experiment_id": "exp-infeasible",
                    "created_at": 124.0,
                    "dominated": True,
                }
            ],
        }


@pytest.fixture
def app() -> FastAPI:
    """Return a minimal app with experiments router mounted."""
    app = FastAPI()
    app.include_router(router)
    return app


def test_pareto_route_returns_empty_payload_without_optimizer(app: FastAPI) -> None:
    """Return an empty-but-valid payload when optimizer is unavailable."""
    client = TestClient(app)
    response = client.get("/api/experiments/pareto")
    assert response.status_code == 200
    payload = response.json()
    assert payload["candidates"] == []
    assert payload["recommended"] is None
    assert payload["frontier_size"] == 0
    assert payload["infeasible_count"] == 0


def test_pareto_route_normalizes_optimizer_snapshot(app: FastAPI) -> None:
    """Normalize optimizer snapshot into frontend ParetoFrontier shape."""
    app.state.optimizer = _StubOptimizer()
    client = TestClient(app)

    response = client.get("/api/experiments/pareto")
    assert response.status_code == 200

    payload = response.json()
    assert payload["frontier_size"] == 1
    assert payload["infeasible_count"] == 1
    assert len(payload["candidates"]) == 2
    assert payload["recommended"]["candidate_id"] == "cand-frontier"

    frontier_candidate = payload["candidates"][0]
    assert frontier_candidate["candidate_id"] == "cand-frontier"
    assert frontier_candidate["constraints_passed"] is True
    assert frontier_candidate["is_recommended"] is True
    assert frontier_candidate["objective_vector"] == [0.91, 0.97, 0.83, 0.71]

    infeasible_candidate = payload["candidates"][1]
    assert infeasible_candidate["candidate_id"] == "cand-infeasible"
    assert infeasible_candidate["constraints_passed"] is False
    assert infeasible_candidate["constraint_violations"] == ["safety_gate"]

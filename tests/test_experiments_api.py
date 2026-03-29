"""API tests for experiments routes."""
from __future__ import annotations

from dataclasses import dataclass

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


@dataclass
class _StubArchiveEntry:
    entry_id: str
    role: str
    candidate_id: str
    experiment_id: str
    objective_vector: list[float]
    config_hash: str
    scores: dict[str, float]
    created_at: str


class _StubArchiveStore:
    def get_all(self) -> list[_StubArchiveEntry]:
        return [
            _StubArchiveEntry(
                entry_id="arc-live-1",
                role="incumbent",
                candidate_id="cand-live-1",
                experiment_id="exp-live-1",
                objective_vector=[0.8, 0.9, 0.7, 0.6],
                config_hash="cfg-live-1",
                scores={"quality": 0.8},
                created_at="2026-03-29T00:00:00Z",
            )
        ]


@dataclass
class _StubJudgeCalibration:
    agreement_rate: float
    drift: float
    position_bias: float
    verbosity_bias: float
    disagreement_rate: float


class _StubJudgeCalibrationStore:
    def get_latest(self) -> _StubJudgeCalibration:
        return _StubJudgeCalibration(
            agreement_rate=0.91,
            drift=0.02,
            position_bias=0.01,
            verbosity_bias=0.03,
            disagreement_rate=0.09,
        )


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


def test_archive_route_returns_empty_payload_when_archive_store_missing(app: FastAPI) -> None:
    """Archive endpoint should stay page-safe when live data is unavailable."""
    client = TestClient(app)
    response = client.get("/api/experiments/archive")

    assert response.status_code == 200
    payload = response.json()
    assert payload["entries"] == []
    assert "not configured" in payload["message"].lower()


def test_archive_route_uses_live_archive_store_when_available(app: FastAPI) -> None:
    """Archive endpoint should return live entries when archive store is configured."""
    app.state.archive_store = _StubArchiveStore()
    client = TestClient(app)

    response = client.get("/api/experiments/archive")

    assert response.status_code == 200
    payload = response.json()
    assert payload["entries"][0]["entry_id"] == "arc-live-1"


def test_judge_calibration_route_returns_empty_metrics_when_store_missing(app: FastAPI) -> None:
    """Judge calibration endpoint should stay page-safe when data is unavailable."""
    client = TestClient(app)
    response = client.get("/api/experiments/judge-calibration")

    assert response.status_code == 200
    payload = response.json()
    assert payload["agreement_rate"] == 0.0
    assert payload["drift"] == 0.0
    assert payload["position_bias"] == 0.0
    assert payload["verbosity_bias"] == 0.0
    assert payload["disagreement_rate"] == 0.0
    assert "not configured" in payload["message"].lower()


def test_judge_calibration_route_uses_live_store_when_available(app: FastAPI) -> None:
    """Judge calibration endpoint should return live data when configured."""
    app.state.judge_calibration = _StubJudgeCalibrationStore()
    client = TestClient(app)

    response = client.get("/api/experiments/judge-calibration")

    assert response.status_code == 200
    payload = response.json()
    assert payload["agreement_rate"] == 0.91

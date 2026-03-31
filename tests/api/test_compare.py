"""Tests for pairwise comparison API routes."""

from __future__ import annotations

import json

import pytest
import yaml

fastapi = pytest.importorskip("fastapi", reason="fastapi not installed")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import compare as compare_routes
from evals.pairwise import PairwiseComparisonStore
from evals.runner import EvalRunner


def _variant_agent(message: str, config: dict | None = None) -> dict:
    """Return deterministic outputs keyed by config variant for route tests."""
    variant = (config or {}).get("variant", "v001")
    outputs = {
        ("Where is my order?", "v001"): {
            "response": "I can help track your order and shipping status right now.",
            "specialist_used": "orders",
            "safety_violation": False,
            "latency_ms": 120.0,
            "token_count": 100,
        },
        ("Where is my order?", "v002"): {
            "response": "Let me hand that to support.",
            "specialist_used": "support",
            "safety_violation": False,
            "latency_ms": 110.0,
            "token_count": 90,
        },
        ("Recommend a keyboard", "v001"): {
            "response": "I do not know.",
            "specialist_used": "recommendations",
            "safety_violation": False,
            "latency_ms": 80.0,
            "token_count": 70,
        },
        ("Recommend a keyboard", "v002"): {
            "response": "I recommend a mechanical keyboard with tactile switches.",
            "specialist_used": "recommendations",
            "safety_violation": False,
            "latency_ms": 85.0,
            "token_count": 88,
        },
    }
    return outputs[(message, variant)]


@pytest.fixture()
def app(tmp_path) -> FastAPI:
    """Return a minimal app with compare routes and eval state."""
    dataset_path = tmp_path / "dataset.jsonl"
    rows = [
        {
            "id": "case-orders",
            "split": "test",
            "category": "happy_path",
            "user_message": "Where is my order?",
            "expected_specialist": "orders",
            "expected_behavior": "answer",
            "expected_keywords": ["order", "shipping"],
        },
        {
            "id": "case-reco",
            "split": "test",
            "category": "happy_path",
            "user_message": "Recommend a keyboard",
            "expected_specialist": "recommendations",
            "expected_behavior": "answer",
            "expected_keywords": ["keyboard"],
        },
    ]
    dataset_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    config_a_path = tmp_path / "v001.yaml"
    config_b_path = tmp_path / "v002.yaml"
    config_a_path.write_text(yaml.safe_dump({"variant": "v001"}), encoding="utf-8")
    config_b_path.write_text(yaml.safe_dump({"variant": "v002"}), encoding="utf-8")

    test_app = FastAPI()
    test_app.include_router(compare_routes.router)
    test_app.state.eval_runner = EvalRunner(agent_fn=_variant_agent, cache_enabled=False)
    test_app.state.pairwise_store = PairwiseComparisonStore(base_dir=str(tmp_path / "pairwise"))
    test_app.state.compare_test_paths = {
        "dataset_path": str(dataset_path),
        "config_a_path": str(config_a_path),
        "config_b_path": str(config_b_path),
    }
    return test_app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    """Return a synchronous test client."""
    return TestClient(app)


def test_compare_route_runs_and_can_be_fetched(client: TestClient, app: FastAPI) -> None:
    """POST compare should persist a comparison retrievable by ID."""
    paths = app.state.compare_test_paths
    response = client.post(
        "/api/evals/compare",
        json={
            "config_a_path": paths["config_a_path"],
            "config_b_path": paths["config_b_path"],
            "dataset_path": paths["dataset_path"],
            "label_a": "v001",
            "label_b": "v002",
            "judge_strategy": "metric_delta",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    comparison_id = payload["comparison_id"]

    detail = client.get(f"/api/evals/compare/{comparison_id}")
    assert detail.status_code == 200
    detail_payload = detail.json()
    assert detail_payload["summary"]["right_wins"] == 1
    assert detail_payload["summary"]["left_wins"] == 1
    assert detail_payload["analysis"]["winner"] in {"v001", "v002", "tie"}


def test_compare_route_lists_recent_comparisons(client: TestClient, app: FastAPI) -> None:
    """List route should include freshly created comparisons."""
    paths = app.state.compare_test_paths
    create_response = client.post(
        "/api/evals/compare",
        json={
            "config_a_path": paths["config_a_path"],
            "config_b_path": paths["config_b_path"],
            "dataset_path": paths["dataset_path"],
            "label_a": "v001",
            "label_b": "v002",
        },
    )
    assert create_response.status_code == 201

    response = client.get("/api/evals/compare")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert any(item["label_a"] == "v001" and item["label_b"] == "v002" for item in payload["comparisons"])

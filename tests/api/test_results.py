"""Tests for eval results explorer API routes."""

from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi", reason="fastapi not installed")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import results as results_routes


def _seed_store(tmp_path):
    """Create a results store populated with one run for API tests."""
    from evals.results_model import Annotation
    from evals.results_store import EvalResultsStore
    from tests.evals.test_results_store import _make_result_set

    store = EvalResultsStore(db_path=str(tmp_path / "results.db"))
    result_set = _make_result_set("run-api")
    store.save(result_set)
    store.add_annotation(
        "run-api",
        "case-routing",
        Annotation(
            author="qa",
            timestamp="2026-03-31T14:00:00Z",
            type="comment",
            content="Needs billing-specific routing rule.",
            score_override=None,
        ),
    )
    return store


@pytest.fixture()
def app(tmp_path) -> FastAPI:
    """Minimal FastAPI app for results-route tests."""
    test_app = FastAPI()
    test_app.include_router(results_routes.router)
    test_app.state.results_store = _seed_store(tmp_path)
    return test_app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    """Synchronous test client."""
    return TestClient(app)


def test_results_route_returns_summary_and_filtered_examples(client: TestClient) -> None:
    """Results routes should return stored summary data and filtered example pages."""
    detail = client.get("/api/evals/results/run-api")
    assert detail.status_code == 200
    assert detail.json()["run_id"] == "run-api"

    failures = client.get("/api/evals/results/run-api/examples", params={"passed": "false"})
    assert failures.status_code == 200
    payload = failures.json()
    assert payload["total"] == 1
    assert payload["examples"][0]["example_id"] == "case-routing"


def test_results_route_records_annotations(client: TestClient) -> None:
    """Annotation endpoint should append a new annotation to an example."""
    response = client.post(
        "/api/evals/results/run-api/examples/case-routing/annotate",
        json={
            "author": "andrew",
            "type": "override",
            "content": "Count this as a pass after manual review.",
            "score_override": 1.0,
        },
    )
    assert response.status_code == 201

    example = client.get("/api/evals/results/run-api/examples/case-routing")
    assert example.status_code == 200
    payload = example.json()
    assert len(payload["annotations"]) == 2

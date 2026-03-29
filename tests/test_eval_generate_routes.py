"""Tests for auto-eval generation API routes in api/routes/eval.py.

Covers POST /generate, GET /generated/{suite_id}, POST /accept,
PATCH /cases/{case_id}, and DELETE /cases/{case_id}.
"""
from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi", reason="fastapi not installed")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import eval as eval_routes
from evals.auto_generator import AutoEvalGenerator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_generator():
    """Reset the module-level generator before each test so suites don't leak."""
    eval_routes._auto_eval_generator = AutoEvalGenerator(llm_provider="mock")
    yield
    eval_routes._auto_eval_generator = AutoEvalGenerator(llm_provider="mock")


@pytest.fixture()
def app() -> FastAPI:
    """Minimal FastAPI app with only the auto-generate eval routes."""
    test_app = FastAPI()
    test_app.include_router(eval_routes.router)
    return test_app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    """Synchronous test client."""
    return TestClient(app)


def _generate_suite(client: TestClient, agent_config: dict | None = None) -> dict:
    """Helper: call POST /generate and return the response JSON."""
    payload = {
        "agent_config": agent_config or {"system_prompt": "You are a test agent."},
        "agent_name": "test_agent",
    }
    resp = client.post("/api/eval/generate", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# POST /api/eval/generate
# ---------------------------------------------------------------------------


class TestGenerateEvalSuite:
    """Tests for the eval suite generation endpoint."""

    def test_generate_returns_201(self, client: TestClient) -> None:
        resp = client.post(
            "/api/eval/generate",
            json={"agent_config": {}, "agent_name": "test"},
        )
        assert resp.status_code == 201

    def test_generate_response_has_required_fields(self, client: TestClient) -> None:
        data = _generate_suite(client)
        assert "suite_id" in data
        assert data["status"] == "ready"
        assert data["total_cases"] > 0
        assert "message" in data

    def test_generate_with_tools_config(self, client: TestClient) -> None:
        config = {
            "tools": [{"name": "search_kb", "description": "Search knowledge base"}],
        }
        data = _generate_suite(client, agent_config=config)
        assert data["total_cases"] > 0

    def test_generate_default_agent_name(self, client: TestClient) -> None:
        resp = client.post("/api/eval/generate", json={"agent_config": {}})
        assert resp.status_code == 201

    def test_generate_missing_agent_config_returns_422(self, client: TestClient) -> None:
        resp = client.post("/api/eval/generate", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/eval/generated/{suite_id}
# ---------------------------------------------------------------------------


class TestGetGeneratedSuite:
    """Tests for fetching a generated eval suite."""

    def test_get_suite_returns_full_suite(self, client: TestClient) -> None:
        gen_data = _generate_suite(client)
        suite_id = gen_data["suite_id"]

        resp = client.get(f"/api/eval/generated/{suite_id}")
        assert resp.status_code == 200

        data = resp.json()
        assert data["suite_id"] == suite_id
        assert data["agent_name"] == "test_agent"
        assert data["status"] == "ready"
        assert "categories" in data
        assert "summary" in data
        # Categories should be non-empty
        total = sum(len(cases) for cases in data["categories"].values())
        assert total == gen_data["total_cases"]

    def test_get_nonexistent_suite_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/eval/generated/nonexistent_id")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# POST /api/eval/generated/{suite_id}/accept
# ---------------------------------------------------------------------------


class TestAcceptSuite:
    """Tests for accepting a generated suite."""

    def test_accept_changes_status(self, client: TestClient) -> None:
        gen_data = _generate_suite(client)
        suite_id = gen_data["suite_id"]

        resp = client.post(f"/api/eval/generated/{suite_id}/accept")
        assert resp.status_code == 200

        data = resp.json()
        assert data["suite_id"] == suite_id
        assert data["status"] == "accepted"
        assert data["total_cases"] == gen_data["total_cases"]

    def test_accept_persists_status(self, client: TestClient) -> None:
        gen_data = _generate_suite(client)
        suite_id = gen_data["suite_id"]

        client.post(f"/api/eval/generated/{suite_id}/accept")
        # Fetch again and verify
        resp = client.get(f"/api/eval/generated/{suite_id}")
        assert resp.json()["status"] == "accepted"

    def test_accept_nonexistent_returns_404(self, client: TestClient) -> None:
        resp = client.post("/api/eval/generated/nonexistent/accept")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/eval/generated/{suite_id}/cases/{case_id}
# ---------------------------------------------------------------------------


class TestUpdateCase:
    """Tests for updating a case within a generated suite."""

    def _get_first_case_id(self, client: TestClient, suite_id: str) -> str:
        resp = client.get(f"/api/eval/generated/{suite_id}")
        data = resp.json()
        for cases in data["categories"].values():
            if cases:
                return cases[0]["case_id"]
        raise AssertionError("No cases found in suite")

    def test_update_case_returns_updated_case(self, client: TestClient) -> None:
        gen_data = _generate_suite(client)
        suite_id = gen_data["suite_id"]
        case_id = self._get_first_case_id(client, suite_id)

        resp = client.patch(
            f"/api/eval/generated/{suite_id}/cases/{case_id}",
            json={"user_message": "Updated test message", "difficulty": "hard"},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["case_id"] == case_id
        assert data["user_message"] == "Updated test message"
        assert data["difficulty"] == "hard"

    def test_update_case_empty_body_returns_400(self, client: TestClient) -> None:
        gen_data = _generate_suite(client)
        suite_id = gen_data["suite_id"]
        case_id = self._get_first_case_id(client, suite_id)

        # All None values -> no updates
        resp = client.patch(
            f"/api/eval/generated/{suite_id}/cases/{case_id}",
            json={},
        )
        assert resp.status_code == 400
        assert "no updates" in resp.json()["detail"].lower()

    def test_update_nonexistent_case_returns_404(self, client: TestClient) -> None:
        gen_data = _generate_suite(client)
        suite_id = gen_data["suite_id"]

        resp = client.patch(
            f"/api/eval/generated/{suite_id}/cases/no_such_case",
            json={"difficulty": "hard"},
        )
        assert resp.status_code == 404

    def test_update_nonexistent_suite_returns_404(self, client: TestClient) -> None:
        resp = client.patch(
            "/api/eval/generated/no_suite/cases/no_case",
            json={"difficulty": "hard"},
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/eval/generated/{suite_id}/cases/{case_id}
# ---------------------------------------------------------------------------


class TestDeleteCase:
    """Tests for deleting a case from a generated suite."""

    def _get_first_case_id(self, client: TestClient, suite_id: str) -> str:
        resp = client.get(f"/api/eval/generated/{suite_id}")
        data = resp.json()
        for cases in data["categories"].values():
            if cases:
                return cases[0]["case_id"]
        raise AssertionError("No cases found in suite")

    def test_delete_case_returns_204(self, client: TestClient) -> None:
        gen_data = _generate_suite(client)
        suite_id = gen_data["suite_id"]
        case_id = self._get_first_case_id(client, suite_id)

        resp = client.delete(f"/api/eval/generated/{suite_id}/cases/{case_id}")
        assert resp.status_code == 204

    def test_delete_case_reduces_total(self, client: TestClient) -> None:
        gen_data = _generate_suite(client)
        suite_id = gen_data["suite_id"]
        original_total = gen_data["total_cases"]
        case_id = self._get_first_case_id(client, suite_id)

        client.delete(f"/api/eval/generated/{suite_id}/cases/{case_id}")

        resp = client.get(f"/api/eval/generated/{suite_id}")
        new_total = sum(len(c) for c in resp.json()["categories"].values())
        assert new_total == original_total - 1

    def test_delete_nonexistent_case_returns_404(self, client: TestClient) -> None:
        gen_data = _generate_suite(client)
        suite_id = gen_data["suite_id"]

        resp = client.delete(f"/api/eval/generated/{suite_id}/cases/no_such_case")
        assert resp.status_code == 404

    def test_delete_nonexistent_suite_returns_404(self, client: TestClient) -> None:
        resp = client.delete("/api/eval/generated/no_suite/cases/no_case")
        assert resp.status_code == 404

    def test_delete_same_case_twice_returns_404_on_second(self, client: TestClient) -> None:
        gen_data = _generate_suite(client)
        suite_id = gen_data["suite_id"]
        case_id = self._get_first_case_id(client, suite_id)

        resp1 = client.delete(f"/api/eval/generated/{suite_id}/cases/{case_id}")
        assert resp1.status_code == 204

        resp2 = client.delete(f"/api/eval/generated/{suite_id}/cases/{case_id}")
        assert resp2.status_code == 404

"""API tests for NL intelligence edit + diagnose chat endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi", reason="fastapi not installed")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import diagnose as diagnose_routes
from api.routes import edit as edit_routes
from core.project_memory import ProjectMemory
from deployer import Deployer
from logger.store import ConversationRecord, ConversationStore
from observer import Observer
from optimizer.memory import OptimizationMemory


@dataclass
class _Score:
    quality: float
    safety: float
    latency: float
    cost: float
    composite: float


class _FakeEvalRunner:
    def run(self, config: dict | None = None) -> _Score:
        cfg = config or {}
        root = str(cfg.get("prompts", {}).get("root", "")).lower()
        score = 0.70
        if "empathetic" in root or "friendly" in root or "warm" in root:
            score += 0.06
        if "never share confidential" in root:
            score += 0.03
        return _Score(quality=score, safety=1.0, latency=0.8, cost=0.8, composite=score)


def _seed_failure(store: ConversationStore) -> None:
    store.log(
        ConversationRecord(
            conversation_id="api-diag-1",
            session_id="s1",
            user_message="I need a refund for my invoice",
            agent_response="Please reboot your app.",
            outcome="fail",
            specialist_used="support",
            latency_ms=1300.0,
            token_count=100,
            tool_calls=[],
            safety_flags=[],
            error_message="",
            config_version="v001",
        )
    )


@pytest.fixture()
def app(tmp_path: Path) -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(edit_routes.router)
    test_app.include_router(diagnose_routes.router)

    store = ConversationStore(str(tmp_path / "conversations.db"))
    _seed_failure(store)
    observer = Observer(store)
    deployer = Deployer(configs_dir=str(tmp_path / "configs"), store=store)
    memory = OptimizationMemory(db_path=str(tmp_path / "memory.db"))

    test_app.state.conversation_store = store
    test_app.state.observer = observer
    test_app.state.eval_runner = _FakeEvalRunner()
    test_app.state.deployer = deployer
    test_app.state.optimization_memory = memory
    test_app.state.project_memory = ProjectMemory(agent_name="API Bot", platform="ADK", use_case="Support")

    return test_app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


class TestEditEndpoint:
    def test_edit_dry_run_returns_intent_and_scores(self, client: TestClient) -> None:
        resp = client.post("/api/edit", json={"description": "Make support responses friendlier", "dry_run": True})
        assert resp.status_code == 200
        data = resp.json()
        assert "intent" in data
        assert "diff" in data
        assert "score_before" in data
        assert "score_after" in data
        assert data["dry_run"] is True

    def test_edit_requires_description(self, client: TestClient) -> None:
        resp = client.post("/api/edit", json={})
        assert resp.status_code == 400


class TestDiagnoseChatEndpoint:
    def test_chat_starts_session_with_summary(self, client: TestClient) -> None:
        resp = client.post("/api/diagnose/chat", json={"message": ""})
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert "response" in data
        assert "clusters" in data

    def test_chat_routes_follow_up_messages(self, client: TestClient) -> None:
        start = client.post("/api/diagnose/chat", json={"message": ""})
        session_id = start.json()["session_id"]

        detail = client.post(
            "/api/diagnose/chat",
            json={"message": "tell me more", "session_id": session_id},
        )
        assert detail.status_code == 200
        assert "Cluster" in detail.json()["response"]

    def test_chat_fix_then_apply(self, client: TestClient) -> None:
        start = client.post("/api/diagnose/chat", json={"message": ""})
        session_id = start.json()["session_id"]

        fix = client.post("/api/diagnose/chat", json={"message": "fix it", "session_id": session_id})
        assert fix.status_code == 200
        assert "Proposed fix" in fix.json()["response"]

        apply = client.post("/api/diagnose/chat", json={"message": "apply", "session_id": session_id})
        assert apply.status_code == 200
        assert "Applied fix" in apply.json()["response"]

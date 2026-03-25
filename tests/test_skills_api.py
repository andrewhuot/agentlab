"""Tests for the executable skills registry API routes."""

from __future__ import annotations

from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi", reason="fastapi not installed")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import skills as skills_routes
from registry.skill_store import SkillStore
from registry.skill_types import (
    EvalCriterion,
    MutationTemplate,
    Skill,
    SkillExample,
    TriggerCondition,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _TestSkillStore(SkillStore):
    """SkillStore with check_same_thread=False for TestClient compatibility."""

    def __init__(self, db_path: str = ":memory:") -> None:
        import sqlite3

        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        from registry.skill_store import _DDL
        self._conn.executescript(_DDL)
        self._conn.commit()


def _make_skill(name: str = "test_skill", category: str = "routing") -> Skill:
    return Skill(
        name=name,
        version=1,
        description="A test skill",
        category=category,
        platform="universal",
        target_surfaces=["prompts"],
        mutations=[
            MutationTemplate(
                name=f"{name}_mut",
                mutation_type="prompt_edit",
                target_surface="prompts",
                description="Rewrite system prompt",
            )
        ],
        examples=[
            SkillExample(
                name=f"{name}_ex",
                surface="prompts",
                before="old prompt",
                after="new prompt",
                improvement=0.12,
                context="integration test",
            )
        ],
        guardrails=["verify before applying"],
        eval_criteria=[EvalCriterion(metric="composite_score", target=0.8)],
        triggers=[TriggerCondition(failure_family="routing_error")],
        tags=["test"],
        status="active",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def skill_store(tmp_path: Path) -> SkillStore:
    return _TestSkillStore(db_path=str(tmp_path / "test_skills.db"))


@pytest.fixture()
def app(skill_store: SkillStore) -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(skills_routes.router)
    test_app.state.skill_store = skill_store
    return test_app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture()
def populated_client(skill_store: SkillStore, app: FastAPI) -> TestClient:
    """TestClient with a pre-registered skill."""
    skill_store.register(_make_skill("routing_optimizer", "routing"))
    return TestClient(app)


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


def test_list_skills_empty(client: TestClient) -> None:
    response = client.get("/api/skills/")
    assert response.status_code == 200
    data = response.json()
    assert "skills" in data
    assert "count" in data
    assert data["count"] == 0
    assert data["skills"] == []


def test_list_skills_returns_registered(populated_client: TestClient) -> None:
    response = populated_client.get("/api/skills/")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["skills"][0]["name"] == "routing_optimizer"


def test_list_skills_with_category_match(populated_client: TestClient) -> None:
    response = populated_client.get("/api/skills/?category=routing")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1


def test_list_skills_with_category_no_match(populated_client: TestClient) -> None:
    response = populated_client.get("/api/skills/?category=safety")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0


def test_list_skills_with_platform_filter(skill_store: SkillStore, app: FastAPI) -> None:
    skill_store.register(_make_skill("cx_skill"))
    # Manually set platform by grabbing and re-registering after mutation
    # (easier: just check universal platform shows up)
    response = TestClient(app).get("/api/skills/?platform=universal")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1


def test_list_skills_with_status_filter(skill_store: SkillStore, app: FastAPI) -> None:
    active = _make_skill("active_skill")
    active.status = "active"
    skill_store.register(active)

    draft = _make_skill("draft_skill")
    draft.status = "draft"
    skill_store.register(draft)

    c = TestClient(app)
    resp_active = c.get("/api/skills/?status=active")
    resp_draft = c.get("/api/skills/?status=draft")
    assert resp_active.json()["count"] == 1
    assert resp_draft.json()["count"] == 1


# ---------------------------------------------------------------------------
# Get single skill
# ---------------------------------------------------------------------------


def test_get_skill_not_found(client: TestClient) -> None:
    response = client.get("/api/skills/nonexistent_skill")
    assert response.status_code == 404
    assert "nonexistent_skill" in response.json()["detail"]


def test_get_skill_found(populated_client: TestClient) -> None:
    response = populated_client.get("/api/skills/routing_optimizer")
    assert response.status_code == 200
    data = response.json()
    assert "skill" in data
    assert data["skill"]["name"] == "routing_optimizer"
    assert data["skill"]["category"] == "routing"


def test_get_skill_with_version(skill_store: SkillStore, app: FastAPI) -> None:
    skill_store.register(_make_skill("versioned"))
    response = TestClient(app).get("/api/skills/versioned?version=1")
    assert response.status_code == 200
    assert response.json()["skill"]["name"] == "versioned"


def test_get_skill_wrong_version(skill_store: SkillStore, app: FastAPI) -> None:
    skill_store.register(_make_skill("versioned2"))
    response = TestClient(app).get("/api/skills/versioned2?version=99")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Recommend
# ---------------------------------------------------------------------------


def test_recommend_skills_empty(client: TestClient) -> None:
    response = client.get("/api/skills/recommend")
    assert response.status_code == 200
    data = response.json()
    assert "skills" in data
    assert "count" in data


def test_recommend_skills_by_failure_family(skill_store: SkillStore, app: FastAPI) -> None:
    skill_store.register(_make_skill("routing_fix"))  # triggers on routing_error
    c = TestClient(app)
    response = c.get("/api/skills/recommend?failure_family=routing_error")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    names = [s["name"] for s in data["skills"]]
    assert "routing_fix" in names


def test_recommend_skills_no_match(skill_store: SkillStore, app: FastAPI) -> None:
    skill_store.register(_make_skill("routing_fix"))
    c = TestClient(app)
    response = c.get("/api/skills/recommend?failure_family=unknown_family_xyz")
    assert response.status_code == 200
    # Should return 200 but empty or non-matching
    assert "skills" in response.json()


# ---------------------------------------------------------------------------
# Stats / leaderboard
# ---------------------------------------------------------------------------


def test_skill_stats_empty(client: TestClient) -> None:
    response = client.get("/api/skills/stats")
    assert response.status_code == 200
    data = response.json()
    assert "leaderboard" in data
    assert "count" in data
    assert data["count"] == 0


def test_skill_stats_with_outcomes(skill_store: SkillStore, app: FastAPI) -> None:
    skill_store.register(_make_skill("perf_skill"))
    skill_store.record_outcome("perf_skill", improvement=0.15, success=True)
    skill_store.record_outcome("perf_skill", improvement=0.10, success=True)

    response = TestClient(app).get("/api/skills/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    entry = data["leaderboard"][0]
    assert entry["name"] == "perf_skill"
    assert entry["times_applied"] == 2
    assert entry["success_rate"] == 1.0


def test_skill_stats_n_parameter(skill_store: SkillStore, app: FastAPI) -> None:
    for i in range(5):
        s = _make_skill(f"skill_{i}")
        skill_store.register(s)
        skill_store.record_outcome(f"skill_{i}", improvement=0.1 * (i + 1), success=True)

    response = TestClient(app).get("/api/skills/stats?n=3")
    assert response.status_code == 200
    assert response.json()["count"] <= 3


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


def test_apply_skill_not_found(client: TestClient) -> None:
    response = client.post("/api/skills/nonexistent/apply")
    assert response.status_code == 404


def test_apply_skill_found(skill_store: SkillStore, app: FastAPI) -> None:
    skill_store.register(_make_skill("apply_me"))
    response = TestClient(app).post("/api/skills/apply_me/apply")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "apply_me"
    assert data["status"] == "queued"
    assert "mutations" in data


# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------


def test_install_no_file_path(client: TestClient) -> None:
    response = client.post("/api/skills/install", json={})
    assert response.status_code == 400
    assert "file_path" in response.json()["detail"]


def test_install_missing_file(client: TestClient) -> None:
    response = client.post(
        "/api/skills/install",
        json={"file_path": "/nonexistent/path/skills.yaml"},
    )
    assert response.status_code == 404


def test_install_valid_pack(skill_store: SkillStore, app: FastAPI, tmp_path: Path) -> None:
    import yaml

    pack = {
        "skills": [
            {
                "name": "installed_skill",
                "version": 1,
                "description": "Installed from pack",
                "category": "quality",
                "platform": "universal",
                "target_surfaces": ["prompts"],
                "mutations": [
                    {
                        "name": "installed_mut",
                        "mutation_type": "prompt_edit",
                        "target_surface": "prompts",
                        "description": "Pack mutation",
                    }
                ],
                "examples": [],
                "guardrails": [],
                "eval_criteria": [],
                "triggers": [],
                "tags": [],
                "status": "active",
            }
        ]
    }
    pack_file = tmp_path / "pack.yaml"
    pack_file.write_text(yaml.dump(pack))

    response = TestClient(app).post(
        "/api/skills/install",
        json={"file_path": str(pack_file)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["installed"] == 1


# ---------------------------------------------------------------------------
# 503 when skill_store not configured
# ---------------------------------------------------------------------------


def test_503_when_no_skill_store() -> None:
    bare_app = FastAPI()
    bare_app.include_router(skills_routes.router)
    c = TestClient(bare_app, raise_server_exceptions=False)
    response = c.get("/api/skills/")
    assert response.status_code == 503

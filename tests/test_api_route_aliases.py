from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import changes as changes_routes
from api.routes import runbooks as runbooks_routes


class _EmptyChangeCardStore:
    def list_pending(self, limit: int = 50):
        return []

    def list_all(self, limit: int = 50):
        return []


class _EmptyRunbookStore:
    def list(self, include_deprecated: bool = False):
        return []


def test_changes_list_supports_frontend_path_without_trailing_slash(tmp_path) -> None:
    app = FastAPI()
    app.include_router(changes_routes.router)
    app.state.change_card_store = _EmptyChangeCardStore()

    response = TestClient(app).get("/api/changes?status=all", follow_redirects=False)

    assert response.status_code == 200
    assert response.json() == {"cards": [], "count": 0}


def test_changes_audit_summary_resolves_static_route_before_card_id(tmp_path) -> None:
    app = FastAPI()
    app.include_router(changes_routes.router)
    app.state.change_card_store = _EmptyChangeCardStore()

    response = TestClient(app).get("/api/changes/audit-summary", follow_redirects=False)

    assert response.status_code == 200
    assert response.json() == {
        "total_changes": 0,
        "accepted": 0,
        "rejected": 0,
        "pending": 0,
        "accept_rate": 0.0,
        "top_rejection_reasons": [],
        "avg_improvement_accepted": 0.0,
        "gates_failure_breakdown": {},
    }


def test_runbooks_list_supports_frontend_path_without_trailing_slash(tmp_path) -> None:
    app = FastAPI()
    app.include_router(runbooks_routes.router)
    app.state.runbook_store = _EmptyRunbookStore()

    response = TestClient(app).get("/api/runbooks", follow_redirects=False)

    assert response.status_code == 200
    assert response.json() == {"runbooks": [], "count": 0}

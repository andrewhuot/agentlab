"""Tests for BuilderMetricsService."""
from __future__ import annotations

import pytest

from builder.metrics import BuilderMetricsService, BuilderMetricsSnapshot
from builder.permissions import PermissionManager
from builder.store import BuilderStore
from builder.types import (
    ApprovalStatus,
    ArtifactRef,
    ArtifactType,
    BuilderProposal,
    BuilderSession,
    BuilderTask,
    EvalBundle,
    PrivilegedAction,
    ReleaseCandidate,
    TaskStatus,
)


@pytest.fixture
def store(tmp_path):
    return BuilderStore(db_path=str(tmp_path / "metrics.db"))


@pytest.fixture
def permissions(store):
    return PermissionManager(store=store)


@pytest.fixture
def metrics(store, permissions):
    return BuilderMetricsService(store=store, permissions=permissions)


def _make_task(store, project_id="proj-1", status=TaskStatus.PENDING):
    task = BuilderTask(session_id="s1", project_id=project_id, title="T")
    task.status = status
    store.save_task(task)
    return task


def _make_proposal(store, status="pending", project_id="proj-1"):
    proposal = BuilderProposal(task_id="t", session_id="s", project_id=project_id, goal="P")
    proposal.status = status
    proposal.accepted = (status == "approved")
    proposal.rejected = (status == "rejected")
    store.save_proposal(proposal)
    return proposal


def _make_release(store, project_id="proj-1", status="deployed"):
    rc = ReleaseCandidate(task_id="t", session_id="s", project_id=project_id, version="1.0.0", deployment_target="prod")
    rc.status = status
    store.save_release(rc)
    return rc


class TestMetricsSnapshot:
    def test_returns_snapshot(self, metrics):
        snap = metrics.compute()
        assert isinstance(snap, BuilderMetricsSnapshot)

    def test_session_count(self, store, metrics):
        for _ in range(3):
            store.save_session(BuilderSession(project_id="proj-1"))
        snap = metrics.compute()
        assert snap.session_count >= 3

    def test_task_count(self, store, metrics):
        for _ in range(5):
            _make_task(store)
        snap = metrics.compute()
        assert snap.task_count >= 5

    def test_project_scoped_metrics(self, store, metrics):
        for _ in range(2):
            _make_task(store, project_id="proj-A")
        for _ in range(3):
            _make_task(store, project_id="proj-B")
        snap_a = metrics.compute(project_id="proj-A")
        snap_b = metrics.compute(project_id="proj-B")
        assert snap_a.task_count == 2
        assert snap_b.task_count == 3


class TestAcceptanceRate:
    def test_all_approved(self, store, metrics):
        for _ in range(3):
            _make_proposal(store, status="approved")
        snap = metrics.compute()
        assert snap.acceptance_rate == 1.0

    def test_all_rejected(self, store, metrics):
        for _ in range(3):
            _make_proposal(store, status="rejected")
        snap = metrics.compute()
        assert snap.acceptance_rate == 0.0

    def test_mixed(self, store, metrics):
        _make_proposal(store, status="approved")
        _make_proposal(store, status="rejected")
        snap = metrics.compute()
        assert snap.acceptance_rate == 0.5

    def test_no_proposals_returns_zero(self, metrics):
        snap = metrics.compute()
        assert snap.acceptance_rate == 0.0


class TestRevertRate:
    def test_no_reverts(self, store, metrics):
        _make_release(store, status="deployed")
        _make_release(store, status="deployed")
        snap = metrics.compute()
        assert snap.revert_rate == 0.0

    def test_half_reverted(self, store, metrics):
        _make_release(store, status="deployed")
        _make_release(store, status="rolled_back")
        snap = metrics.compute()
        assert snap.revert_rate == 0.5

    def test_no_releases_returns_zero(self, metrics):
        snap = metrics.compute()
        assert snap.revert_rate == 0.0


class TestUnsafeActionRate:
    def test_all_allowed(self, permissions, metrics):
        permissions.log_action(task_id="t", project_id="p", action=PrivilegedAction.SOURCE_WRITE, allowed=True)
        permissions.log_action(task_id="t", project_id="p", action=PrivilegedAction.SOURCE_WRITE, allowed=True)
        snap = metrics.compute()
        assert snap.unsafe_action_rate == 0.0

    def test_all_denied(self, permissions, metrics):
        permissions.log_action(task_id="t", project_id="p", action=PrivilegedAction.DEPLOYMENT, allowed=False)
        permissions.log_action(task_id="t", project_id="p", action=PrivilegedAction.DEPLOYMENT, allowed=False)
        snap = metrics.compute()
        assert snap.unsafe_action_rate == 1.0


class TestTimeToFirstPlan:
    def test_no_plans_returns_zero(self, metrics):
        snap = metrics.compute()
        assert snap.time_to_first_plan == 0.0

    def test_plan_after_task(self, store, metrics):
        task = _make_task(store)
        import time
        time.sleep(0.01)
        artifact = ArtifactRef(
            task_id=task.task_id,
            session_id="s",
            project_id="proj-1",
            artifact_type=ArtifactType.PLAN,
            title="Plan",
            summary="A plan",
        )
        store.save_artifact(artifact)
        snap = metrics.compute()
        assert snap.time_to_first_plan >= 0.0


class TestComputeDict:
    def test_returns_dict(self, metrics):
        result = metrics.compute_dict()
        assert isinstance(result, dict)
        assert "session_count" in result
        assert "task_count" in result
        assert "acceptance_rate" in result
        assert "revert_rate" in result
        assert "unsafe_action_rate" in result

    def test_project_scoped_dict(self, store, metrics):
        _make_task(store, project_id="proj-Q")
        result = metrics.compute_dict(project_id="proj-Q")
        assert result["project_id"] == "proj-Q"
        assert result["task_count"] == 1

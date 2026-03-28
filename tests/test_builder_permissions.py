"""Tests for PermissionManager."""
from __future__ import annotations

import pytest

from builder.permissions import PermissionManager
from builder.store import BuilderStore
from builder.types import (
    ApprovalScope,
    ApprovalStatus,
    PrivilegedAction,
    RiskLevel,
    now_ts,
)


@pytest.fixture
def store(tmp_path):
    return BuilderStore(db_path=str(tmp_path / "permissions.db"))


@pytest.fixture
def permissions(store):
    return PermissionManager(store=store)


class TestGrants:
    def test_create_grant(self, permissions):
        grant = permissions.create_grant(
            project_id="proj-1",
            action=PrivilegedAction.SOURCE_WRITE,
            scope=ApprovalScope.TASK,
            task_id="task-1",
        )
        assert grant.grant_id != ""
        assert grant.action == PrivilegedAction.SOURCE_WRITE
        assert grant.scope == ApprovalScope.TASK

    def test_get_grant(self, permissions):
        grant = permissions.create_grant(
            project_id="proj-1",
            action=PrivilegedAction.DEPLOYMENT,
            scope=ApprovalScope.PROJECT,
        )
        loaded = permissions.get_grant(grant.grant_id)
        assert loaded is not None
        assert loaded.action == PrivilegedAction.DEPLOYMENT

    def test_list_grants_by_project(self, permissions):
        permissions.create_grant(project_id="proj-A", action=PrivilegedAction.SOURCE_WRITE, scope=ApprovalScope.ONCE)
        permissions.create_grant(project_id="proj-B", action=PrivilegedAction.SOURCE_WRITE, scope=ApprovalScope.ONCE)
        grants = permissions.list_grants(project_id="proj-A")
        assert len(grants) == 1
        assert grants[0].project_id == "proj-A"

    def test_revoke_grant(self, permissions):
        grant = permissions.create_grant(
            project_id="proj-1",
            action=PrivilegedAction.SECRET_ACCESS,
            scope=ApprovalScope.ONCE,
        )
        assert permissions.revoke_grant(grant.grant_id) is True
        # Revoked grants excluded from list by default
        grants = permissions.list_grants(project_id="proj-1")
        assert not any(g.grant_id == grant.grant_id for g in grants)

    def test_revoke_missing_returns_false(self, permissions):
        assert permissions.revoke_grant("nonexistent") is False

    def test_revoked_included_with_flag(self, permissions):
        grant = permissions.create_grant(project_id="p", action=PrivilegedAction.SOURCE_WRITE, scope=ApprovalScope.ONCE)
        permissions.revoke_grant(grant.grant_id)
        grants = permissions.list_grants(project_id="p", include_revoked=True)
        assert any(g.grant_id == grant.grant_id for g in grants)


class TestIsActionAllowed:
    def test_allowed_when_grant_exists(self, permissions):
        permissions.create_grant(
            project_id="proj-1",
            task_id="task-1",
            action=PrivilegedAction.SOURCE_WRITE,
            scope=ApprovalScope.TASK,
        )
        assert permissions.is_action_allowed("proj-1", "task-1", PrivilegedAction.SOURCE_WRITE) is True

    def test_denied_when_no_grant(self, permissions):
        assert permissions.is_action_allowed("proj-1", "task-1", PrivilegedAction.DEPLOYMENT) is False

    def test_denied_when_grant_revoked(self, permissions):
        grant = permissions.create_grant(
            project_id="proj-1",
            task_id="task-1",
            action=PrivilegedAction.SOURCE_WRITE,
            scope=ApprovalScope.TASK,
        )
        permissions.revoke_grant(grant.grant_id)
        assert permissions.is_action_allowed("proj-1", "task-1", PrivilegedAction.SOURCE_WRITE) is False

    def test_denied_when_grant_expired(self, permissions):
        permissions.create_grant(
            project_id="proj-1",
            task_id="task-1",
            action=PrivilegedAction.EXTERNAL_NETWORK,
            scope=ApprovalScope.ONCE,
            expires_at=now_ts() - 1.0,  # already expired
        )
        assert permissions.is_action_allowed("proj-1", "task-1", PrivilegedAction.EXTERNAL_NETWORK) is False

    def test_project_scope_grant_allows_any_task(self, permissions):
        permissions.create_grant(
            project_id="proj-1",
            action=PrivilegedAction.SOURCE_WRITE,
            scope=ApprovalScope.PROJECT,
        )
        assert permissions.is_action_allowed("proj-1", "task-any", PrivilegedAction.SOURCE_WRITE) is True


class TestApprovals:
    def test_request_approval(self, permissions):
        approval = permissions.request_approval(
            task_id="t1",
            session_id="s1",
            project_id="p1",
            action=PrivilegedAction.SOURCE_WRITE,
            description="Need file write access",
            scope=ApprovalScope.TASK,
            risk_level=RiskLevel.MEDIUM,
        )
        assert approval.approval_id != ""
        assert approval.status == ApprovalStatus.PENDING
        assert approval.action == PrivilegedAction.SOURCE_WRITE

    def test_approve_creates_grant(self, permissions):
        approval = permissions.request_approval(
            task_id="t1",
            session_id="s1",
            project_id="p1",
            action=PrivilegedAction.SOURCE_WRITE,
            description="Write access",
        )
        result = permissions.respond(approval.approval_id, approved=True, responder="admin")
        assert result is not None
        assert result.status == ApprovalStatus.APPROVED
        assert permissions.is_action_allowed("p1", "t1", PrivilegedAction.SOURCE_WRITE) is True

    def test_reject_does_not_create_grant(self, permissions):
        approval = permissions.request_approval(
            task_id="t2",
            session_id="s1",
            project_id="p1",
            action=PrivilegedAction.DEPLOYMENT,
            description="Deploy access",
        )
        result = permissions.respond(approval.approval_id, approved=False, responder="admin")
        assert result.status == ApprovalStatus.REJECTED
        assert permissions.is_action_allowed("p1", "t2", PrivilegedAction.DEPLOYMENT) is False

    def test_respond_missing_returns_none(self, permissions):
        result = permissions.respond("nonexistent", approved=True, responder="admin")
        assert result is None


class TestActionLogs:
    def test_log_allowed_action(self, permissions):
        entry = permissions.log_action(
            task_id="t1",
            project_id="p1",
            action=PrivilegedAction.SOURCE_WRITE,
            allowed=True,
        )
        assert entry.log_id != ""
        assert entry.allowed is True

    def test_log_denied_action(self, permissions):
        entry = permissions.log_action(
            task_id="t1",
            project_id="p1",
            action=PrivilegedAction.SECRET_ACCESS,
            allowed=False,
        )
        assert entry.allowed is False

    def test_list_action_logs(self, permissions):
        permissions.log_action(task_id="t1", project_id="p1", action=PrivilegedAction.SOURCE_WRITE, allowed=True)
        permissions.log_action(task_id="t1", project_id="p1", action=PrivilegedAction.DEPLOYMENT, allowed=False)
        logs = permissions.list_action_logs(project_id="p1")
        assert len(logs) == 2

    def test_unsafe_action_rate(self, permissions):
        permissions.log_action(task_id="t", project_id="proj-X", action=PrivilegedAction.SOURCE_WRITE, allowed=True)
        permissions.log_action(task_id="t", project_id="proj-X", action=PrivilegedAction.DEPLOYMENT, allowed=False)
        logs = permissions.list_action_logs(project_id="proj-X")
        denied = [log for log in logs if not log.allowed]
        rate = len(denied) / len(logs)
        assert rate == 0.5


class TestTakeover:
    def test_stop_for_takeover(self, permissions):
        state = permissions.stop_for_takeover(task_id="t1", actor="alice", note="Taking over")
        assert state.active is True
        assert state.actor == "alice"

    def test_hand_back(self, permissions):
        permissions.stop_for_takeover(task_id="t1", actor="alice")
        state = permissions.hand_back(task_id="t1", actor="alice", note="Done")
        assert state.active is False

    def test_get_takeover_state(self, permissions):
        permissions.stop_for_takeover(task_id="t1", actor="bob")
        state = permissions.get_takeover_state("t1")
        assert state is not None
        assert state.active is True
        assert state.actor == "bob"

    def test_get_missing_takeover_returns_none(self, permissions):
        assert permissions.get_takeover_state("nonexistent") is None

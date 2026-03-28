"""Permission and approval model for Builder Workspace."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from builder.store import BuilderStore
from builder.types import (
    ApprovalRequest,
    ApprovalScope,
    ApprovalStatus,
    PrivilegedAction,
    RiskLevel,
    now_ts,
    new_id,
)


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _json_default(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")


@dataclass
class PermissionGrant:
    """Grant that allows a privileged action for a scope."""

    grant_id: str = field(default_factory=new_id)
    project_id: str = ""
    task_id: str | None = None
    action: PrivilegedAction = PrivilegedAction.SOURCE_WRITE
    scope: ApprovalScope = ApprovalScope.ONCE
    created_at: float = field(default_factory=now_ts)
    updated_at: float = field(default_factory=now_ts)
    expires_at: float | None = None
    revoked_at: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionLogEntry:
    """Audit log entry for one privileged action decision."""

    log_id: str = field(default_factory=new_id)
    task_id: str = ""
    project_id: str = ""
    action: PrivilegedAction = PrivilegedAction.SOURCE_WRITE
    allowed: bool = False
    created_at: float = field(default_factory=now_ts)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class TakeoverState:
    """Tracks whether a human has taken over a task."""

    task_id: str = ""
    active: bool = False
    actor: str = ""
    note: str = ""
    updated_at: float = field(default_factory=now_ts)


class PermissionManager:
    """Manages grants, approvals, takeover state, and action logs."""

    def __init__(self, store: BuilderStore) -> None:
        self._store = store
        self._db_path = store.db_path
        self._init_db()

    def _init_db(self) -> None:
        with _connect(self._db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS builder_permission_grants (
                    grant_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    task_id TEXT,
                    action TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    expires_at REAL,
                    revoked_at REAL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_builder_permission_grants_project
                    ON builder_permission_grants(project_id, action, revoked_at);

                CREATE TABLE IF NOT EXISTS builder_action_logs (
                    log_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    allowed INTEGER NOT NULL,
                    created_at REAL NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_builder_action_logs_project
                    ON builder_action_logs(project_id, created_at DESC);

                CREATE TABLE IF NOT EXISTS builder_takeover_states (
                    task_id TEXT PRIMARY KEY,
                    active INTEGER NOT NULL,
                    actor TEXT NOT NULL,
                    note TEXT NOT NULL,
                    updated_at REAL NOT NULL,
                    payload TEXT NOT NULL
                );
                """
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Grants
    # ------------------------------------------------------------------

    def create_grant(
        self,
        project_id: str,
        action: PrivilegedAction,
        scope: ApprovalScope,
        task_id: str | None = None,
        expires_at: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PermissionGrant:
        """Create and persist a permission grant."""

        grant = PermissionGrant(
            project_id=project_id,
            task_id=task_id,
            action=action,
            scope=scope,
            expires_at=expires_at,
            metadata=metadata or {},
        )
        self._save_grant(grant)
        return grant

    def list_grants(
        self,
        project_id: str | None = None,
        task_id: str | None = None,
        include_revoked: bool = False,
    ) -> list[PermissionGrant]:
        """List grants filtered by project/task."""

        clauses: list[str] = []
        params: list[Any] = []
        if project_id:
            clauses.append("project_id = ?")
            params.append(project_id)
        if task_id:
            clauses.append("(task_id = ? OR task_id IS NULL)")
            params.append(task_id)
        if not include_revoked:
            clauses.append("revoked_at IS NULL")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with _connect(self._db_path) as conn:
            rows = conn.execute(
                f"SELECT payload FROM builder_permission_grants {where} ORDER BY created_at DESC",
                tuple(params),
            ).fetchall()
        return [self._hydrate_grant(json.loads(row["payload"])) for row in rows]

    def revoke_grant(self, grant_id: str) -> bool:
        """Revoke an existing grant."""

        grant = self.get_grant(grant_id)
        if grant is None:
            return False
        grant.revoked_at = now_ts()
        grant.updated_at = now_ts()
        self._save_grant(grant)
        return True

    def get_grant(self, grant_id: str) -> PermissionGrant | None:
        """Fetch one grant by ID."""

        with _connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT payload FROM builder_permission_grants WHERE grant_id = ?",
                (grant_id,),
            ).fetchone()
        if row is None:
            return None
        return self._hydrate_grant(json.loads(row["payload"]))

    def is_action_allowed(
        self,
        project_id: str,
        task_id: str,
        action: PrivilegedAction,
    ) -> bool:
        """Return whether the given action is currently granted."""

        now = now_ts()
        grants = self.list_grants(project_id=project_id, task_id=task_id)
        for grant in grants:
            if grant.action != action:
                continue
            if grant.expires_at is not None and grant.expires_at < now:
                continue
            if grant.scope == ApprovalScope.TASK and grant.task_id not in (None, task_id):
                continue
            return True
        return False

    # ------------------------------------------------------------------
    # Approvals
    # ------------------------------------------------------------------

    def request_approval(
        self,
        task_id: str,
        session_id: str,
        project_id: str,
        action: PrivilegedAction,
        description: str,
        scope: ApprovalScope = ApprovalScope.ONCE,
        risk_level: RiskLevel = RiskLevel.MEDIUM,
        requested_by: str = "builder",
        details: dict[str, Any] | None = None,
    ) -> ApprovalRequest:
        """Create an approval request card for a privileged action."""

        approval = ApprovalRequest(
            task_id=task_id,
            session_id=session_id,
            project_id=project_id,
            action=action,
            description=description,
            scope=scope,
            status=ApprovalStatus.PENDING,
            risk_level=risk_level,
            details={"requested_by": requested_by, **(details or {})},
        )
        self._store.save_approval(approval)
        return approval

    def respond(
        self,
        approval_id: str,
        approved: bool,
        responder: str,
        note: str | None = None,
    ) -> ApprovalRequest | None:
        """Respond to an approval request and optionally create grants."""

        approval = self._store.get_approval(approval_id)
        if approval is None:
            return None

        approval.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        approval.resolved_at = now_ts()
        approval.updated_at = now_ts()
        approval.resolved_by = responder
        if note:
            approval.details["response_note"] = note

        self._store.save_approval(approval)

        if approved:
            self.create_grant(
                project_id=approval.project_id,
                task_id=approval.task_id,
                action=approval.action,
                scope=approval.scope,
                metadata={"approval_id": approval.approval_id, "responder": responder},
            )

        return approval

    # ------------------------------------------------------------------
    # Action logging
    # ------------------------------------------------------------------

    def log_action(
        self,
        task_id: str,
        project_id: str,
        action: PrivilegedAction,
        allowed: bool,
        details: dict[str, Any] | None = None,
    ) -> ActionLogEntry:
        """Record one privileged action decision."""

        entry = ActionLogEntry(
            task_id=task_id,
            project_id=project_id,
            action=action,
            allowed=allowed,
            details=details or {},
        )
        with _connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO builder_action_logs
                    (log_id, task_id, project_id, action, allowed, created_at, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.log_id,
                    entry.task_id,
                    entry.project_id,
                    entry.action.value,
                    int(entry.allowed),
                    entry.created_at,
                    json.dumps(asdict(entry), default=_json_default),
                ),
            )
            conn.commit()
        return entry

    def list_action_logs(
        self,
        project_id: str | None = None,
        task_id: str | None = None,
        limit: int = 200,
    ) -> list[ActionLogEntry]:
        """List recent privileged action logs."""

        clauses: list[str] = []
        params: list[Any] = []
        if project_id:
            clauses.append("project_id = ?")
            params.append(project_id)
        if task_id:
            clauses.append("task_id = ?")
            params.append(task_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with _connect(self._db_path) as conn:
            rows = conn.execute(
                f"SELECT payload FROM builder_action_logs {where} ORDER BY created_at DESC LIMIT ?",
                tuple(params),
            ).fetchall()
        return [self._hydrate_action_log(json.loads(row["payload"])) for row in rows]

    # ------------------------------------------------------------------
    # Human takeover
    # ------------------------------------------------------------------

    def stop_for_takeover(self, task_id: str, actor: str, note: str = "") -> TakeoverState:
        """Mark a task as manually taken over by a human."""

        state = TakeoverState(task_id=task_id, active=True, actor=actor, note=note)
        self._save_takeover_state(state)
        return state

    def hand_back(self, task_id: str, actor: str, note: str = "") -> TakeoverState:
        """Return control of a task back to builder automation."""

        state = TakeoverState(task_id=task_id, active=False, actor=actor, note=note)
        self._save_takeover_state(state)
        return state

    def get_takeover_state(self, task_id: str) -> TakeoverState | None:
        """Get the current takeover state for a task."""

        with _connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT payload FROM builder_takeover_states WHERE task_id = ?",
                (task_id,),
            ).fetchone()
        if row is None:
            return None
        return self._hydrate_takeover_state(json.loads(row["payload"]))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _save_grant(self, grant: PermissionGrant) -> None:
        with _connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO builder_permission_grants
                    (grant_id, project_id, task_id, action, scope, created_at, updated_at,
                     expires_at, revoked_at, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    grant.grant_id,
                    grant.project_id,
                    grant.task_id,
                    grant.action.value,
                    grant.scope.value,
                    grant.created_at,
                    grant.updated_at,
                    grant.expires_at,
                    grant.revoked_at,
                    json.dumps(asdict(grant), default=_json_default),
                ),
            )
            conn.commit()

    def _save_takeover_state(self, state: TakeoverState) -> None:
        with _connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO builder_takeover_states
                    (task_id, active, actor, note, updated_at, payload)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    state.task_id,
                    int(state.active),
                    state.actor,
                    state.note,
                    state.updated_at,
                    json.dumps(asdict(state), default=_json_default),
                ),
            )
            conn.commit()

    def _hydrate_grant(self, payload: dict[str, Any]) -> PermissionGrant:
        grant = PermissionGrant()
        for key, value in payload.items():
            if hasattr(grant, key):
                setattr(grant, key, value)
        grant.action = PrivilegedAction(payload.get("action", grant.action))
        grant.scope = ApprovalScope(payload.get("scope", grant.scope))
        return grant

    def _hydrate_action_log(self, payload: dict[str, Any]) -> ActionLogEntry:
        log = ActionLogEntry()
        for key, value in payload.items():
            if hasattr(log, key):
                setattr(log, key, value)
        log.action = PrivilegedAction(payload.get("action", log.action))
        return log

    def _hydrate_takeover_state(self, payload: dict[str, Any]) -> TakeoverState:
        state = TakeoverState()
        for key, value in payload.items():
            if hasattr(state, key):
                setattr(state, key, value)
        return state

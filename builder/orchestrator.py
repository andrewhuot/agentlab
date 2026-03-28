"""Builder orchestrator that routes work between specialist subagents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from builder.specialists import (
    SpecialistDefinition,
    detect_specialist_by_intent,
    get_specialist,
    list_specialists,
)
from builder.store import BuilderStore
from builder.types import BuilderSession, BuilderTask, SpecialistRole, now_ts


@dataclass
class HandoffRecord:
    """Record representing a specialist-to-specialist handoff."""

    session_id: str
    task_id: str
    from_role: SpecialistRole
    to_role: SpecialistRole
    reason: str
    timestamp: float = field(default_factory=now_ts)


class BuilderOrchestrator:
    """Routes task intent to specialists and tracks handoff state."""

    def __init__(self, store: BuilderStore) -> None:
        self._store = store
        self._active_specialist_by_session: dict[str, SpecialistRole] = {}
        self._handoffs_by_session: dict[str, list[HandoffRecord]] = {}

    def start_session(self, session: BuilderSession) -> None:
        """Initialize orchestrator runtime state for the provided session."""

        self._active_specialist_by_session.setdefault(session.session_id, session.active_specialist)
        self._handoffs_by_session.setdefault(session.session_id, [])

    def get_active_specialist(self, session_id: str) -> SpecialistRole:
        """Return active specialist role for a session."""

        return self._active_specialist_by_session.get(session_id, SpecialistRole.ORCHESTRATOR)

    def detect_specialist(self, message: str) -> SpecialistRole:
        """Detect the best specialist for a natural-language message."""

        return detect_specialist_by_intent(message)

    def route_request(
        self,
        session_id: str,
        task_id: str,
        message: str,
        explicit_role: SpecialistRole | None = None,
    ) -> SpecialistRole:
        """Select and activate the specialist for a request, recording handoffs."""

        target = explicit_role or self.detect_specialist(message)
        current = self.get_active_specialist(session_id)
        if current != target:
            self._record_handoff(
                session_id=session_id,
                task_id=task_id,
                from_role=current,
                to_role=target,
                reason="explicit" if explicit_role else "intent_detection",
            )
        self._active_specialist_by_session[session_id] = target
        self._persist_session_specialist(session_id, target)
        return target

    def invoke_specialist(
        self,
        task: BuilderTask,
        message: str,
        explicit_role: SpecialistRole | None = None,
        extra_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Route and invoke a specialist with task/session context."""

        role = self.route_request(
            session_id=task.session_id,
            task_id=task.task_id,
            message=message,
            explicit_role=explicit_role,
        )
        definition = get_specialist(role)
        task.active_specialist = role
        task.updated_at = now_ts()
        self._store.save_task(task)

        context = {
            "project_id": task.project_id,
            "session_id": task.session_id,
            "task_id": task.task_id,
            "task_title": task.title,
            "message": message,
        }
        if extra_context:
            context.update(extra_context)

        return {
            "specialist": role.value,
            "display_name": definition.display_name,
            "description": definition.description,
            "tools": definition.tools,
            "permission_scope": definition.permission_scope,
            "context_template": definition.context_template,
            "context": context,
            "timestamp": now_ts(),
        }

    def list_roster(self, session_id: str) -> list[dict[str, Any]]:
        """Return specialist roster for UI display with active/idle status."""

        active = self.get_active_specialist(session_id)
        roster: list[dict[str, Any]] = []
        for specialist in list_specialists():
            roster.append(
                {
                    "role": specialist.role.value,
                    "display_name": specialist.display_name,
                    "description": specialist.description,
                    "tools": specialist.tools,
                    "permission_scope": specialist.permission_scope,
                    "context_template": specialist.context_template,
                    "status": "active" if specialist.role == active else "idle",
                }
            )
        return roster

    def get_handoffs(self, session_id: str) -> list[HandoffRecord]:
        """Return handoff history for a session."""

        return list(self._handoffs_by_session.get(session_id, []))

    def get_handoffs_dict(self, session_id: str) -> list[dict[str, Any]]:
        """Return handoff history serialized for API responses."""

        return [
            {
                "session_id": handoff.session_id,
                "task_id": handoff.task_id,
                "from_role": handoff.from_role.value,
                "to_role": handoff.to_role.value,
                "reason": handoff.reason,
                "timestamp": handoff.timestamp,
            }
            for handoff in self.get_handoffs(session_id)
        ]

    def _record_handoff(
        self,
        session_id: str,
        task_id: str,
        from_role: SpecialistRole,
        to_role: SpecialistRole,
        reason: str,
    ) -> None:
        handoff = HandoffRecord(
            session_id=session_id,
            task_id=task_id,
            from_role=from_role,
            to_role=to_role,
            reason=reason,
        )
        self._handoffs_by_session.setdefault(session_id, []).append(handoff)

    def _persist_session_specialist(self, session_id: str, role: SpecialistRole) -> None:
        session = self._store.get_session(session_id)
        if session is None:
            return
        session.active_specialist = role
        session.updated_at = now_ts()
        self._store.save_session(session)


def specialist_definition(role: SpecialistRole) -> SpecialistDefinition:
    """Expose specialist lookups for consumers that need metadata only."""

    return get_specialist(role)

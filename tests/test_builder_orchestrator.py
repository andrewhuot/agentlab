"""Tests for BuilderOrchestrator."""
from __future__ import annotations

import pytest

from builder.orchestrator import BuilderOrchestrator, HandoffRecord
from builder.store import BuilderStore
from builder.types import BuilderSession, BuilderTask, ExecutionMode, SpecialistRole


@pytest.fixture
def store(tmp_path):
    return BuilderStore(db_path=str(tmp_path / "orchestrator.db"))


@pytest.fixture
def orchestrator(store):
    return BuilderOrchestrator(store=store)


@pytest.fixture
def session(store):
    session = BuilderSession(project_id="proj-1", title="Test session")
    store.save_session(session)
    return session


@pytest.fixture
def task(store, session):
    task = BuilderTask(session_id=session.session_id, project_id="proj-1", title="Test task")
    store.save_task(task)
    return task


class TestSessionInit:
    def test_start_session_sets_specialist(self, orchestrator, session):
        orchestrator.start_session(session)
        role = orchestrator.get_active_specialist(session.session_id)
        assert isinstance(role, SpecialistRole)

    def test_start_session_idempotent(self, orchestrator, session):
        orchestrator.start_session(session)
        orchestrator.start_session(session)
        role = orchestrator.get_active_specialist(session.session_id)
        assert isinstance(role, SpecialistRole)

    def test_unknown_session_returns_orchestrator(self, orchestrator):
        role = orchestrator.get_active_specialist("nonexistent")
        assert role == SpecialistRole.ORCHESTRATOR


class TestIntentDetection:
    def test_detect_eval_intent(self, orchestrator):
        role = orchestrator.detect_specialist("write evaluation tests for the agent")
        assert role == SpecialistRole.EVAL_AUTHOR

    def test_detect_adk_intent(self, orchestrator):
        role = orchestrator.detect_specialist("design the ADK graph architecture")
        assert role == SpecialistRole.ADK_ARCHITECT

    def test_detect_release_intent(self, orchestrator):
        role = orchestrator.detect_specialist("release the agent to production")
        assert role == SpecialistRole.RELEASE_MANAGER

    def test_detect_unknown_falls_back(self, orchestrator):
        role = orchestrator.detect_specialist("xyz123 random nonsense")
        assert isinstance(role, SpecialistRole)


class TestRouting:
    def test_route_explicit_role(self, orchestrator, session, task):
        orchestrator.start_session(session)
        role = orchestrator.route_request(
            session_id=session.session_id,
            task_id=task.task_id,
            message="anything",
            explicit_role=SpecialistRole.TRACE_ANALYST,
        )
        assert role == SpecialistRole.TRACE_ANALYST

    def test_route_records_handoff_on_change(self, orchestrator, session, task):
        orchestrator.start_session(session)
        # Force a different starting specialist
        orchestrator._active_specialist_by_session[session.session_id] = SpecialistRole.ORCHESTRATOR
        orchestrator.route_request(
            session_id=session.session_id,
            task_id=task.task_id,
            message="",
            explicit_role=SpecialistRole.EVAL_AUTHOR,
        )
        handoffs = orchestrator.get_handoffs(session.session_id)
        assert len(handoffs) >= 1
        assert handoffs[-1].to_role == SpecialistRole.EVAL_AUTHOR

    def test_route_same_role_no_handoff(self, orchestrator, session, task):
        orchestrator.start_session(session)
        orchestrator._active_specialist_by_session[session.session_id] = SpecialistRole.EVAL_AUTHOR
        before = len(orchestrator.get_handoffs(session.session_id))
        orchestrator.route_request(
            session_id=session.session_id,
            task_id=task.task_id,
            message="",
            explicit_role=SpecialistRole.EVAL_AUTHOR,
        )
        after = len(orchestrator.get_handoffs(session.session_id))
        assert after == before


class TestInvokeSpecialist:
    def test_invoke_returns_dict_with_specialist(self, orchestrator, session, task):
        orchestrator.start_session(session)
        result = orchestrator.invoke_specialist(
            task=task,
            message="evaluate my agent",
            explicit_role=SpecialistRole.EVAL_AUTHOR,
        )
        assert result["specialist"] == SpecialistRole.EVAL_AUTHOR.value
        assert "display_name" in result
        assert "tools" in result
        assert "context" in result

    def test_invoke_updates_task_specialist(self, orchestrator, store, session, task):
        orchestrator.start_session(session)
        orchestrator.invoke_specialist(
            task=task,
            message="release to prod",
            explicit_role=SpecialistRole.RELEASE_MANAGER,
        )
        updated = store.get_task(task.task_id)
        assert updated.active_specialist == SpecialistRole.RELEASE_MANAGER


class TestRoster:
    def test_list_roster_returns_all_specialists(self, orchestrator, session):
        orchestrator.start_session(session)
        roster = orchestrator.list_roster(session.session_id)
        assert len(roster) == 9  # All 9 specialists
        roles = {entry["role"] for entry in roster}
        assert "eval_author" in roles
        assert "release_manager" in roles

    def test_roster_marks_active(self, orchestrator, session):
        orchestrator.start_session(session)
        orchestrator._active_specialist_by_session[session.session_id] = SpecialistRole.TRACE_ANALYST
        roster = orchestrator.list_roster(session.session_id)
        active_entries = [e for e in roster if e["status"] == "active"]
        assert len(active_entries) == 1
        assert active_entries[0]["role"] == SpecialistRole.TRACE_ANALYST.value


class TestHandoffHistory:
    def test_get_handoffs_empty_initially(self, orchestrator, session):
        orchestrator.start_session(session)
        assert orchestrator.get_handoffs(session.session_id) == []

    def test_get_handoffs_dict_serializable(self, orchestrator, session, task):
        orchestrator.start_session(session)
        orchestrator._active_specialist_by_session[session.session_id] = SpecialistRole.ORCHESTRATOR
        orchestrator.route_request(
            session_id=session.session_id,
            task_id=task.task_id,
            message="",
            explicit_role=SpecialistRole.SKILL_AUTHOR,
        )
        handoffs_dict = orchestrator.get_handoffs_dict(session.session_id)
        assert len(handoffs_dict) == 1
        h = handoffs_dict[0]
        assert isinstance(h["from_role"], str)
        assert isinstance(h["to_role"], str)
        assert isinstance(h["timestamp"], float)

"""Tests for BuilderStore SQLite persistence."""
from __future__ import annotations

import tempfile
import os
import pytest

from builder.store import BuilderStore
from builder.types import (
    ApprovalRequest,
    ApprovalScope,
    ApprovalStatus,
    ArtifactRef,
    ArtifactType,
    BuilderProject,
    BuilderProposal,
    BuilderSession,
    BuilderTask,
    EvalBundle,
    ExecutionMode,
    PrivilegedAction,
    ReleaseCandidate,
    RiskLevel,
    SandboxRun,
    SpecialistRole,
    TaskStatus,
    TraceBookmark,
    WorktreeRef,
    new_id,
    now_ts,
)


@pytest.fixture
def store(tmp_path):
    db = str(tmp_path / "test_builder.db")
    return BuilderStore(db_path=db)


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

class TestProjects:
    def test_save_and_get(self, store):
        project = BuilderProject(name="Alpha", description="Test project")
        store.save_project(project)
        loaded = store.get_project(project.project_id)
        assert loaded is not None
        assert loaded.name == "Alpha"
        assert loaded.description == "Test project"

    def test_get_missing_returns_none(self, store):
        assert store.get_project("nonexistent") is None

    def test_list_projects(self, store):
        for i in range(3):
            store.save_project(BuilderProject(name=f"Project {i}"))
        projects = store.list_projects()
        assert len(projects) >= 3

    def test_list_filters_archived(self, store):
        active = BuilderProject(name="Active", archived=False)
        archived = BuilderProject(name="Archived", archived=True)
        store.save_project(active)
        store.save_project(archived)
        active_list = store.list_projects(archived=False)
        assert all(not p.archived for p in active_list)
        archived_list = store.list_projects(archived=True)
        assert all(p.archived for p in archived_list)

    def test_delete_project(self, store):
        project = BuilderProject(name="ToDelete")
        store.save_project(project)
        assert store.delete_project(project.project_id) is True
        assert store.get_project(project.project_id) is None

    def test_delete_missing_returns_false(self, store):
        assert store.delete_project("nonexistent") is False

    def test_update_via_save(self, store):
        project = BuilderProject(name="Original")
        store.save_project(project)
        project.name = "Updated"
        store.save_project(project)
        loaded = store.get_project(project.project_id)
        assert loaded.name == "Updated"


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

class TestSessions:
    def test_save_and_get(self, store):
        session = BuilderSession(project_id="proj-1", title="Session A")
        store.save_session(session)
        loaded = store.get_session(session.session_id)
        assert loaded is not None
        assert loaded.title == "Session A"
        assert loaded.project_id == "proj-1"

    def test_list_by_project(self, store):
        for i in range(2):
            store.save_session(BuilderSession(project_id="proj-A"))
        store.save_session(BuilderSession(project_id="proj-B"))
        result = store.list_sessions(project_id="proj-A")
        assert len(result) == 2
        assert all(s.project_id == "proj-A" for s in result)

    def test_mode_enum_survives_roundtrip(self, store):
        session = BuilderSession(project_id="p", mode=ExecutionMode.DELEGATE)
        store.save_session(session)
        loaded = store.get_session(session.session_id)
        assert loaded.mode == ExecutionMode.DELEGATE

    def test_delete_session(self, store):
        session = BuilderSession(project_id="p")
        store.save_session(session)
        assert store.delete_session(session.session_id) is True
        assert store.get_session(session.session_id) is None


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

class TestTasks:
    def test_save_and_get(self, store):
        task = BuilderTask(session_id="s1", project_id="p1", title="Do something")
        store.save_task(task)
        loaded = store.get_task(task.task_id)
        assert loaded is not None
        assert loaded.title == "Do something"

    def test_list_by_session(self, store):
        for _ in range(3):
            store.save_task(BuilderTask(session_id="sess-X", project_id="p"))
        store.save_task(BuilderTask(session_id="sess-Y", project_id="p"))
        result = store.list_tasks(session_id="sess-X")
        assert len(result) == 3

    def test_list_by_status(self, store):
        t1 = BuilderTask(session_id="s", project_id="p")
        t1.status = TaskStatus.COMPLETED
        t2 = BuilderTask(session_id="s", project_id="p")
        t2.status = TaskStatus.FAILED
        store.save_task(t1)
        store.save_task(t2)
        completed = store.list_tasks(status=TaskStatus.COMPLETED)
        assert any(t.task_id == t1.task_id for t in completed)
        assert not any(t.task_id == t2.task_id for t in completed)

    def test_enum_roundtrip(self, store):
        task = BuilderTask(session_id="s", project_id="p", mode=ExecutionMode.APPLY)
        task.status = TaskStatus.RUNNING
        task.active_specialist = SpecialistRole.EVAL_AUTHOR
        store.save_task(task)
        loaded = store.get_task(task.task_id)
        assert loaded.mode == ExecutionMode.APPLY
        assert loaded.status == TaskStatus.RUNNING
        assert loaded.active_specialist == SpecialistRole.EVAL_AUTHOR

    def test_delete_task(self, store):
        task = BuilderTask(session_id="s", project_id="p")
        store.save_task(task)
        assert store.delete_task(task.task_id) is True
        assert store.get_task(task.task_id) is None


# ---------------------------------------------------------------------------
# Proposals
# ---------------------------------------------------------------------------

class TestProposals:
    def test_save_and_get(self, store):
        proposal = BuilderProposal(task_id="t1", session_id="s1", project_id="p1", goal="Proposal 1")
        store.save_proposal(proposal)
        loaded = store.get_proposal(proposal.proposal_id)
        assert loaded is not None
        assert loaded.goal == "Proposal 1"

    def test_list_by_task(self, store):
        for _ in range(2):
            store.save_proposal(BuilderProposal(task_id="task-A", session_id="s", project_id="p"))
        result = store.list_proposals(task_id="task-A")
        assert len(result) == 2

    def test_delete(self, store):
        p = BuilderProposal(task_id="t", session_id="s", project_id="p")
        store.save_proposal(p)
        assert store.delete_proposal(p.proposal_id) is True
        assert store.get_proposal(p.proposal_id) is None


# ---------------------------------------------------------------------------
# Artifacts
# ---------------------------------------------------------------------------

class TestArtifacts:
    def test_save_and_get(self, store):
        artifact = ArtifactRef(
            task_id="t1",
            session_id="s1",
            project_id="p1",
            artifact_type=ArtifactType.PLAN,
            title="Plan card",
            summary="A plan",
        )
        store.save_artifact(artifact)
        loaded = store.get_artifact(artifact.artifact_id)
        assert loaded is not None
        assert loaded.artifact_type == ArtifactType.PLAN

    def test_list_by_type(self, store):
        store.save_artifact(ArtifactRef(task_id="t", session_id="s", project_id="p", artifact_type=ArtifactType.EVAL))
        store.save_artifact(ArtifactRef(task_id="t", session_id="s", project_id="p", artifact_type=ArtifactType.SKILL))
        evals = store.list_artifacts(artifact_type=ArtifactType.EVAL)
        assert all(a.artifact_type == ArtifactType.EVAL for a in evals)

    def test_delete(self, store):
        a = ArtifactRef(task_id="t", session_id="s", project_id="p", artifact_type=ArtifactType.BENCHMARK)
        store.save_artifact(a)
        assert store.delete_artifact(a.artifact_id) is True
        assert store.get_artifact(a.artifact_id) is None


# ---------------------------------------------------------------------------
# Approvals
# ---------------------------------------------------------------------------

class TestApprovals:
    def test_save_and_get(self, store):
        approval = ApprovalRequest(
            task_id="t1",
            session_id="s1",
            project_id="p1",
            action=PrivilegedAction.SOURCE_WRITE,
            description="Need to write files",
        )
        store.save_approval(approval)
        loaded = store.get_approval(approval.approval_id)
        assert loaded is not None
        assert loaded.action == PrivilegedAction.SOURCE_WRITE
        assert loaded.status == ApprovalStatus.PENDING

    def test_list_by_status(self, store):
        a1 = ApprovalRequest(task_id="t", session_id="s", project_id="p", action=PrivilegedAction.DEPLOYMENT)
        a1.status = ApprovalStatus.APPROVED
        a2 = ApprovalRequest(task_id="t", session_id="s", project_id="p", action=PrivilegedAction.SECRET_ACCESS)
        a2.status = ApprovalStatus.PENDING
        store.save_approval(a1)
        store.save_approval(a2)
        approved = store.list_approvals(status=ApprovalStatus.APPROVED)
        assert any(a.approval_id == a1.approval_id for a in approved)
        assert not any(a.approval_id == a2.approval_id for a in approved)


# ---------------------------------------------------------------------------
# Worktrees
# ---------------------------------------------------------------------------

class TestWorktrees:
    def test_save_and_get(self, store):
        wt = WorktreeRef(task_id="t1", project_id="p1", branch_name="builder/abc", base_sha="HEAD", worktree_path="/tmp/wt")
        store.save_worktree(wt)
        loaded = store.get_worktree(wt.worktree_id)
        assert loaded is not None
        assert loaded.branch_name == "builder/abc"

    def test_list_by_task(self, store):
        store.save_worktree(WorktreeRef(task_id="task-A", project_id="p", branch_name="b1", base_sha="H", worktree_path="/tmp/1"))
        store.save_worktree(WorktreeRef(task_id="task-A", project_id="p", branch_name="b2", base_sha="H", worktree_path="/tmp/2"))
        result = store.list_worktrees(task_id="task-A")
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Sandbox runs
# ---------------------------------------------------------------------------

class TestSandboxRuns:
    def test_save_and_get(self, store):
        run = SandboxRun(task_id="t1", project_id="p1", image="python:3.11", command="pytest", status="running")
        store.save_sandbox_run(run)
        loaded = store.get_sandbox_run(run.sandbox_id)
        assert loaded is not None
        assert loaded.command == "pytest"

    def test_list_by_status(self, store):
        r1 = SandboxRun(task_id="t", project_id="p", image="img", command="cmd", status="completed")
        r2 = SandboxRun(task_id="t", project_id="p", image="img", command="cmd", status="running")
        store.save_sandbox_run(r1)
        store.save_sandbox_run(r2)
        completed = store.list_sandbox_runs(status="completed")
        assert any(r.sandbox_id == r1.sandbox_id for r in completed)
        assert not any(r.sandbox_id == r2.sandbox_id for r in completed)


# ---------------------------------------------------------------------------
# Eval bundles
# ---------------------------------------------------------------------------

class TestEvalBundles:
    def test_save_and_get(self, store):
        bundle = EvalBundle(task_id="t1", session_id="s1", project_id="p1", notes="Eval v1")
        store.save_eval_bundle(bundle)
        loaded = store.get_eval_bundle(bundle.bundle_id)
        assert loaded is not None
        assert loaded.notes == "Eval v1"

    def test_list_by_session(self, store):
        for _ in range(2):
            store.save_eval_bundle(EvalBundle(task_id="t", session_id="sess-Z", project_id="p"))
        result = store.list_eval_bundles(session_id="sess-Z")
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Trace bookmarks
# ---------------------------------------------------------------------------

class TestTraceBookmarks:
    def test_save_and_get(self, store):
        bookmark = TraceBookmark(task_id="t1", session_id="s1", project_id="p1", trace_id="trace-123", label="Key moment")
        store.save_trace_bookmark(bookmark)
        loaded = store.get_trace_bookmark(bookmark.bookmark_id)
        assert loaded is not None
        assert loaded.trace_id == "trace-123"
        assert loaded.label == "Key moment"

    def test_list_by_task(self, store):
        for _ in range(3):
            store.save_trace_bookmark(TraceBookmark(task_id="task-B", session_id="s", project_id="p", trace_id="tr"))
        result = store.list_trace_bookmarks(task_id="task-B")
        assert len(result) == 3


# ---------------------------------------------------------------------------
# Release candidates
# ---------------------------------------------------------------------------

class TestReleaseCandidates:
    def test_save_and_get(self, store):
        rc = ReleaseCandidate(
            task_id="t1",
            session_id="s1",
            project_id="p1",
            version="1.0.0",
            deployment_target="prod",
        )
        store.save_release(rc)
        loaded = store.get_release(rc.release_id)
        assert loaded is not None
        assert loaded.version == "1.0.0"
        assert loaded.deployment_target == "prod"

    def test_list_by_project(self, store):
        for i in range(2):
            store.save_release(ReleaseCandidate(task_id="t", session_id="s", project_id="proj-RC", version=f"1.{i}.0", deployment_target="staging"))
        result = store.list_releases(project_id="proj-RC")
        assert len(result) == 2

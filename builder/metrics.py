"""Builder-specific metrics aggregation."""

from __future__ import annotations

from dataclasses import dataclass, asdict

from builder.permissions import PermissionManager
from builder.store import BuilderStore
from builder.types import ArtifactType


@dataclass
class BuilderMetricsSnapshot:
    """Summary metrics for builder health and quality."""

    project_id: str | None
    session_count: int
    task_count: int
    time_to_first_plan: float
    acceptance_rate: float
    revert_rate: float
    eval_coverage_delta: float
    unsafe_action_rate: float
    avg_revisions_per_change: float


class BuilderMetricsService:
    """Computes builder metrics from session/task/artifact history."""

    def __init__(self, store: BuilderStore, permissions: PermissionManager) -> None:
        self._store = store
        self._permissions = permissions

    def compute(self, project_id: str | None = None) -> BuilderMetricsSnapshot:
        """Compute current metrics snapshot for optional project scope."""

        sessions = self._store.list_sessions(project_id=project_id, limit=10_000)
        tasks = self._store.list_tasks(project_id=project_id, limit=10_000)
        proposals = self._store.list_proposals(limit=10_000)
        releases = self._store.list_releases(project_id=project_id, limit=10_000)
        bundles = self._store.list_eval_bundles(limit=10_000)
        artifacts = self._store.list_artifacts(limit=10_000)

        if project_id:
            proposals = [proposal for proposal in proposals if proposal.project_id == project_id]
            bundles = [bundle for bundle in bundles if bundle.project_id == project_id]
            artifacts = [artifact for artifact in artifacts if artifact.project_id == project_id]

        time_to_first_plan = self._compute_time_to_first_plan(tasks, artifacts)
        acceptance_rate = self._compute_acceptance_rate(proposals)
        revert_rate = self._compute_revert_rate(releases)
        eval_coverage_delta = self._average([bundle.eval_coverage_pct for bundle in bundles])
        unsafe_action_rate = self._compute_unsafe_action_rate(project_id)
        avg_revisions = self._compute_avg_revisions(proposals)

        return BuilderMetricsSnapshot(
            project_id=project_id,
            session_count=len(sessions),
            task_count=len(tasks),
            time_to_first_plan=time_to_first_plan,
            acceptance_rate=acceptance_rate,
            revert_rate=revert_rate,
            eval_coverage_delta=eval_coverage_delta,
            unsafe_action_rate=unsafe_action_rate,
            avg_revisions_per_change=avg_revisions,
        )

    def compute_dict(self, project_id: str | None = None) -> dict[str, float | int | str | None]:
        """Return metrics snapshot as plain dictionary."""

        return asdict(self.compute(project_id=project_id))

    def _compute_time_to_first_plan(self, tasks, artifacts) -> float:
        deltas: list[float] = []
        plan_by_task = {
            artifact.task_id: artifact
            for artifact in artifacts
            if artifact.artifact_type == ArtifactType.PLAN
        }
        for task in tasks:
            plan = plan_by_task.get(task.task_id)
            if plan is None:
                continue
            deltas.append(max(0.0, plan.created_at - task.created_at))
        return self._average(deltas)

    def _compute_acceptance_rate(self, proposals) -> float:
        if not proposals:
            return 0.0
        accepted = 0
        decided = 0
        for proposal in proposals:
            if proposal.status in {"approved", "rejected"}:
                decided += 1
                if proposal.status == "approved":
                    accepted += 1
            elif proposal.accepted:
                decided += 1
                accepted += 1
            elif proposal.rejected:
                decided += 1
        if decided == 0:
            return 0.0
        return accepted / decided

    def _compute_revert_rate(self, releases) -> float:
        if not releases:
            return 0.0
        deploy_or_rolled = [
            release
            for release in releases
            if release.status in {"deployed", "rolled_back"}
        ]
        if not deploy_or_rolled:
            return 0.0
        rolled_back = [release for release in deploy_or_rolled if release.status == "rolled_back"]
        return len(rolled_back) / len(deploy_or_rolled)

    def _compute_unsafe_action_rate(self, project_id: str | None) -> float:
        logs = self._permissions.list_action_logs(project_id=project_id, limit=10_000)
        if not logs:
            return 0.0
        denied = [log for log in logs if not log.allowed]
        return len(denied) / len(logs)

    def _compute_avg_revisions(self, proposals) -> float:
        approved = [proposal for proposal in proposals if proposal.status == "approved" or proposal.accepted]
        if not approved:
            return 0.0
        return self._average([proposal.revision_count for proposal in approved])

    def _average(self, values: list[float]) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

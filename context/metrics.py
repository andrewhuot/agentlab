"""Context metrics — aggregated scores for context window health."""

from __future__ import annotations

import time

from context.analyzer import ContextSnapshot
from context.simulator import SimulationResult


class ContextMetrics:
    """Static helper methods that compute context-health scores."""

    @staticmethod
    def utilization_ratio(snapshots: list[ContextSnapshot]) -> float:
        """Average utilization across all snapshots."""
        if not snapshots:
            return 0.0
        return sum(s.utilization for s in snapshots) / len(snapshots)

    @staticmethod
    def compaction_loss_score(simulation_result: SimulationResult) -> float:
        """Fraction of total tokens that were lost to compaction."""
        total_before = sum(s.tokens_before for s in simulation_result.steps)
        if total_before == 0:
            return 0.0
        return simulation_result.total_tokens_lost / total_before

    @staticmethod
    def handoff_fidelity(handoff_text: str, original_text: str) -> float:
        """Word-overlap ratio measuring how much original info survives a handoff."""
        if not original_text:
            return 0.0
        original_words = set(original_text.lower().split())
        if not original_words:
            return 0.0
        summary_words = set(handoff_text.lower().split())
        overlap = original_words & summary_words
        return len(overlap) / len(original_words)

    @staticmethod
    def memory_staleness(memory_entries: list[dict]) -> float:
        """Average age (seconds) of memory entries based on last_accessed vs now."""
        if not memory_entries:
            return 0.0
        now = time.time()
        ages = [now - entry.get("last_accessed", entry.get("created_at", now)) for entry in memory_entries]
        return sum(ages) / len(ages)

    @staticmethod
    def aggregate_report(
        snapshots: list[ContextSnapshot],
        simulation_results: list[SimulationResult] | None = None,
        memory_entries: list[dict] | None = None,
    ) -> dict:
        """Compute all metrics and return a summary dict."""
        report: dict = {
            "utilization_ratio": ContextMetrics.utilization_ratio(snapshots),
            "snapshot_count": len(snapshots),
        }

        if simulation_results:
            report["compaction_scores"] = {
                r.strategy_name: ContextMetrics.compaction_loss_score(r)
                for r in simulation_results
            }

        if memory_entries is not None:
            report["memory_staleness_seconds"] = ContextMetrics.memory_staleness(memory_entries)
            report["memory_entry_count"] = len(memory_entries)

        return report

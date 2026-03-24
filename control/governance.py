"""Control-plane governance engine wrappers."""

from __future__ import annotations

from dataclasses import dataclass

from deployer.release_manager import PromotionRecord, ReleaseManager


@dataclass
class GovernanceEngine:
    """Governance-as-code control-plane policy evaluator."""

    release_manager: ReleaseManager

    def evaluate_candidate(
        self,
        candidate_version: str,
        gate_results: dict[str, bool],
        holdout_score: float,
        slice_results: dict[str, float],
        canary_verdict: str | None = None,
    ) -> PromotionRecord:
        """Evaluate promotion readiness for a release candidate.

        Delegates to ReleaseManager's full pipeline.
        """
        return self.release_manager.run_full_pipeline(
            candidate_version=candidate_version,
            gate_results=gate_results,
            holdout_score=holdout_score,
            slice_results=slice_results,
            canary_verdict=canary_verdict,
        )

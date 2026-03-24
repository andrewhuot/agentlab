"""Heuristic-based proposer strategies for the AutoFix engine.

Each proposer analyzes eval failures and current config to suggest
mutation proposals. These are simple keyword/pattern-based heuristics,
not ML models.
"""

from __future__ import annotations

import time
import uuid
from collections import Counter

from optimizer.autofix import AutoFixProposal


def _generate_proposal_id() -> str:
    """Generate a short unique proposal ID."""
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Common error keywords for clustering
# ---------------------------------------------------------------------------

_ERROR_KEYWORDS = [
    "timeout",
    "rate_limit",
    "context_length",
    "hallucination",
    "refusal",
    "format_error",
    "tool_error",
    "safety",
    "off_topic",
    "incomplete",
]


def _extract_error_keyword(failure: dict) -> str:
    """Extract the best-matching error keyword from a failure dict."""
    error_text = str(failure.get("error", "")) + " " + str(failure.get("message", ""))
    error_lower = error_text.lower()
    for kw in _ERROR_KEYWORDS:
        if kw in error_lower:
            return kw
    return "unknown"


class FailurePatternProposer:
    """Clusters failures by error patterns and proposes instruction/few-shot fixes."""

    def __init__(self, min_cluster_size: int = 2) -> None:
        self.min_cluster_size = min_cluster_size

    def propose(
        self, failures: list[dict], current_config: dict
    ) -> list[AutoFixProposal]:
        """Analyze failure patterns and propose fixes for top clusters."""
        if not failures:
            return []

        # Cluster failures by keyword
        keyword_counts: Counter[str] = Counter()
        keyword_failures: dict[str, list[dict]] = {}
        for f in failures:
            kw = _extract_error_keyword(f)
            keyword_counts[kw] += 1
            keyword_failures.setdefault(kw, []).append(f)

        proposals: list[AutoFixProposal] = []
        for kw, count in keyword_counts.most_common(5):
            if count < self.min_cluster_size:
                continue

            # Choose mutation based on error type
            if kw in ("hallucination", "off_topic", "refusal", "safety"):
                mutation_name = "instruction_rewrite"
                surface = "instruction"
                params = {
                    "target": "root",
                    "text": f"[AutoFix] Address {kw} failures ({count} occurrences)",
                }
                diff_preview = f"Rewrite system prompt to address {kw} pattern"
            else:
                mutation_name = "few_shot_edit"
                surface = "few_shot"
                params = {
                    "target": "root",
                    "examples": [{"note": f"Example addressing {kw} failure"}],
                }
                diff_preview = f"Add few-shot example for {kw} pattern"

            slices = list({f.get("eval_slice", "default") for f in keyword_failures[kw]})

            proposals.append(
                AutoFixProposal(
                    proposal_id=_generate_proposal_id(),
                    mutation_name=mutation_name,
                    surface=surface,
                    params=params,
                    expected_lift=min(0.1 * count, 0.5),
                    risk_class="low",
                    affected_eval_slices=slices,
                    cost_impact_estimate=0.01,
                    diff_preview=diff_preview,
                    status="pending",
                    created_at=time.time(),
                )
            )

        return proposals


class RegressionProposer:
    """Detects regressions and proposes rollback-style mutations."""

    def propose(
        self, failures: list[dict], current_config: dict
    ) -> list[AutoFixProposal]:
        """Check for regression-style failures and propose rollbacks."""
        if not failures:
            return []

        # Look for failures flagged as regressions
        regression_failures = [
            f for f in failures if f.get("is_regression") or f.get("previously_passing")
        ]
        if not regression_failures:
            return []

        # Group by surface
        surfaces: dict[str, list[dict]] = {}
        for f in regression_failures:
            s = f.get("surface", "instruction")
            surfaces.setdefault(s, []).append(f)

        proposals: list[AutoFixProposal] = []
        for surface, surface_failures in surfaces.items():
            mutation_name = "instruction_rewrite" if surface == "instruction" else "few_shot_edit"
            slices = list({f.get("eval_slice", "default") for f in surface_failures})

            proposals.append(
                AutoFixProposal(
                    proposal_id=_generate_proposal_id(),
                    mutation_name=mutation_name,
                    surface=surface,
                    params={
                        "target": "root",
                        "text": "[AutoFix] Rollback: restore previous behavior",
                    },
                    expected_lift=0.15,
                    risk_class="low",
                    affected_eval_slices=slices,
                    cost_impact_estimate=0.01,
                    diff_preview=f"Rollback {surface} to address {len(surface_failures)} regressions",
                    status="pending",
                    created_at=time.time(),
                )
            )

        return proposals


class CostOptimizationProposer:
    """Analyzes config for cost optimization opportunities."""

    # Models ordered roughly by cost (expensive -> cheap)
    _MODEL_COST_TIERS: dict[str, list[str]] = {
        "expensive": ["gpt-4", "gpt-4-turbo", "claude-3-opus", "gemini-1.5-pro"],
        "moderate": ["gpt-3.5-turbo", "claude-3-sonnet", "gemini-1.5-flash"],
        "cheap": ["claude-3-haiku", "gemini-2.0-flash", "gpt-4o-mini"],
    }

    _CHEAPER_ALTERNATIVES: dict[str, str] = {
        "gpt-4": "gpt-3.5-turbo",
        "gpt-4-turbo": "gpt-4o-mini",
        "claude-3-opus": "claude-3-sonnet",
        "claude-3-sonnet": "claude-3-haiku",
        "gemini-1.5-pro": "gemini-1.5-flash",
    }

    def propose(
        self, failures: list[dict], current_config: dict
    ) -> list[AutoFixProposal]:
        """Analyze config and suggest cost-saving mutations."""
        proposals: list[AutoFixProposal] = []

        # Check for model swap opportunity
        current_model = current_config.get("model", "")
        if current_model in self._CHEAPER_ALTERNATIVES:
            cheaper = self._CHEAPER_ALTERNATIVES[current_model]
            proposals.append(
                AutoFixProposal(
                    proposal_id=_generate_proposal_id(),
                    mutation_name="model_swap",
                    surface="model",
                    params={"model": cheaper},
                    expected_lift=0.0,
                    risk_class="high",
                    affected_eval_slices=["all"],
                    cost_impact_estimate=-0.30,
                    diff_preview=f"Swap model from {current_model} to {cheaper}",
                    status="pending",
                    created_at=time.time(),
                )
            )

        # Check generation settings for optimization
        gen_settings = current_config.get("generation_settings", {})
        max_tokens = gen_settings.get("max_tokens", 0)
        if max_tokens > 4096:
            proposals.append(
                AutoFixProposal(
                    proposal_id=_generate_proposal_id(),
                    mutation_name="generation_settings",
                    surface="generation_settings",
                    params={"max_tokens": 4096},
                    expected_lift=0.0,
                    risk_class="low",
                    affected_eval_slices=["all"],
                    cost_impact_estimate=-0.10,
                    diff_preview=f"Reduce max_tokens from {max_tokens} to 4096",
                    status="pending",
                    created_at=time.time(),
                )
            )

        temperature = gen_settings.get("temperature")
        if temperature is not None and temperature > 1.0:
            proposals.append(
                AutoFixProposal(
                    proposal_id=_generate_proposal_id(),
                    mutation_name="generation_settings",
                    surface="generation_settings",
                    params={"temperature": 0.7},
                    expected_lift=0.05,
                    risk_class="low",
                    affected_eval_slices=["all"],
                    cost_impact_estimate=0.0,
                    diff_preview=f"Reduce temperature from {temperature} to 0.7",
                    status="pending",
                    created_at=time.time(),
                )
            )

        return proposals

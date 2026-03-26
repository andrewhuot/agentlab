"""Compaction simulator — replay token growth under different compaction strategies."""

from __future__ import annotations

from dataclasses import dataclass

from context.analyzer import ContextSnapshot


@dataclass
class CompactionStrategy:
    """Parameters defining a compaction strategy."""

    name: str
    description: str
    max_tokens: int
    compaction_trigger: float  # fraction of max_tokens that triggers compaction
    retention_ratio: float  # fraction of tokens kept after compaction


@dataclass
class SimulationStep:
    """A single step in the compaction simulation."""

    turn: int
    tokens_before: int
    tokens_after: int
    compacted: bool
    tokens_lost: int


@dataclass
class SimulationResult:
    """Outcome of running a compaction simulation."""

    strategy_name: str
    steps: list[SimulationStep]
    total_compactions: int
    total_tokens_lost: int
    peak_tokens: int
    avg_utilization: float
    final_tokens: int

    def to_dict(self) -> dict:
        """Serialize to a plain dict."""
        return {
            "strategy_name": self.strategy_name,
            "total_compactions": self.total_compactions,
            "total_tokens_lost": self.total_tokens_lost,
            "peak_tokens": self.peak_tokens,
            "avg_utilization": self.avg_utilization,
            "final_tokens": self.final_tokens,
            "steps": [
                {
                    "turn": s.turn,
                    "tokens_before": s.tokens_before,
                    "tokens_after": s.tokens_after,
                    "compacted": s.compacted,
                    "tokens_lost": s.tokens_lost,
                }
                for s in self.steps
            ],
        }


class CompactionSimulator:
    """Replays context growth under different compaction strategies."""

    def __init__(self) -> None:
        pass

    def simulate(
        self,
        snapshots: list[ContextSnapshot],
        strategy: CompactionStrategy,
    ) -> SimulationResult:
        """Run a compaction simulation against recorded snapshots."""
        steps: list[SimulationStep] = []
        current_tokens = 0
        total_compactions = 0
        total_lost = 0
        peak = 0
        utilization_sum = 0.0

        for snap in snapshots:
            # Compute the delta this turn added to the context.
            delta = snap.tokens_used - (steps[-1].tokens_after if steps else 0)
            if delta < 0:
                # Original trace had a compaction; treat as delta 0 for simulation purposes.
                delta = 0
            tokens_before = current_tokens + delta
            compacted = False
            tokens_lost = 0

            trigger_threshold = strategy.max_tokens * strategy.compaction_trigger
            if tokens_before >= trigger_threshold:
                tokens_after = int(tokens_before * strategy.retention_ratio)
                compacted = True
                tokens_lost = tokens_before - tokens_after
                total_compactions += 1
                total_lost += tokens_lost
            else:
                tokens_after = tokens_before

            current_tokens = tokens_after
            if tokens_before > peak:
                peak = tokens_before

            util = tokens_after / strategy.max_tokens if strategy.max_tokens else 0.0
            utilization_sum += util

            steps.append(
                SimulationStep(
                    turn=snap.turn_number,
                    tokens_before=tokens_before,
                    tokens_after=tokens_after,
                    compacted=compacted,
                    tokens_lost=tokens_lost,
                )
            )

        avg_util = utilization_sum / len(steps) if steps else 0.0

        return SimulationResult(
            strategy_name=strategy.name,
            steps=steps,
            total_compactions=total_compactions,
            total_tokens_lost=total_lost,
            peak_tokens=peak,
            avg_utilization=avg_util,
            final_tokens=current_tokens,
        )

    def compare_strategies(
        self,
        snapshots: list[ContextSnapshot],
        strategies: list[CompactionStrategy],
    ) -> list[SimulationResult]:
        """Run simulations for multiple strategies and return all results."""
        return [self.simulate(snapshots, s) for s in strategies]

    @staticmethod
    def default_strategies() -> list[CompactionStrategy]:
        """Return three built-in compaction strategies."""
        return [
            CompactionStrategy(
                name="aggressive",
                description="Low ceiling, frequent compaction, heavy pruning.",
                max_tokens=8000,
                compaction_trigger=0.8,
                retention_ratio=0.4,
            ),
            CompactionStrategy(
                name="balanced",
                description="Moderate ceiling, balanced compaction.",
                max_tokens=16000,
                compaction_trigger=0.85,
                retention_ratio=0.6,
            ),
            CompactionStrategy(
                name="conservative",
                description="High ceiling, infrequent compaction, high retention.",
                max_tokens=32000,
                compaction_trigger=0.9,
                retention_ratio=0.8,
            ),
        ]

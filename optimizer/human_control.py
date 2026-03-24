"""Human escape hatch state management (pause/resume/reject/inject/pin)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class HumanControlState:
    """Persistent state for operator override controls."""

    paused: bool = False
    immutable_surfaces: list[str] = field(default_factory=list)
    rejected_experiments: list[str] = field(default_factory=list)
    last_injected_mutation: str | None = None
    updated_at: float = field(default_factory=time.time)


class HumanControlStore:
    """JSON-backed store for human control state."""

    def __init__(self, path: str = ".autoagent/human_control.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def get_state(self) -> HumanControlState:
        """Load state from disk or return defaults."""
        if not self.path.exists():
            return HumanControlState()
        with self.path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return HumanControlState(
            paused=bool(payload.get("paused", False)),
            immutable_surfaces=list(payload.get("immutable_surfaces", [])),
            rejected_experiments=list(payload.get("rejected_experiments", [])),
            last_injected_mutation=payload.get("last_injected_mutation"),
            updated_at=float(payload.get("updated_at", time.time())),
        )

    def save_state(self, state: HumanControlState) -> None:
        """Persist state to disk."""
        state.updated_at = time.time()
        payload = {
            "paused": state.paused,
            "immutable_surfaces": sorted(set(state.immutable_surfaces)),
            "rejected_experiments": sorted(set(state.rejected_experiments)),
            "last_injected_mutation": state.last_injected_mutation,
            "updated_at": state.updated_at,
        }
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)

    def pause(self) -> HumanControlState:
        """Set paused=true."""
        state = self.get_state()
        state.paused = True
        self.save_state(state)
        return state

    def resume(self) -> HumanControlState:
        """Set paused=false."""
        state = self.get_state()
        state.paused = False
        self.save_state(state)
        return state

    def pin_surface(self, surface: str) -> HumanControlState:
        """Add surface to immutable list."""
        state = self.get_state()
        if surface not in state.immutable_surfaces:
            state.immutable_surfaces.append(surface)
        self.save_state(state)
        return state

    def unpin_surface(self, surface: str) -> HumanControlState:
        """Remove surface from immutable list."""
        state = self.get_state()
        state.immutable_surfaces = [
            item for item in state.immutable_surfaces if item != surface
        ]
        self.save_state(state)
        return state

    def reject_experiment(self, experiment_id: str) -> HumanControlState:
        """Record a human rejection for an experiment ID."""
        state = self.get_state()
        if experiment_id not in state.rejected_experiments:
            state.rejected_experiments.append(experiment_id)
        self.save_state(state)
        return state

    def mark_injected(self, mutation_path: str) -> HumanControlState:
        """Store last manually injected mutation path."""
        state = self.get_state()
        state.last_injected_mutation = mutation_path
        self.save_state(state)
        return state

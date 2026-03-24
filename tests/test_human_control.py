"""Unit tests for HumanControlStore persistence and operations."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from optimizer.human_control import HumanControlState, HumanControlStore


def test_default_state(tmp_path: Path) -> None:
    """Verify default state when no file exists."""
    store = HumanControlStore(path=str(tmp_path / "control.json"))
    state = store.get_state()

    assert state.paused is False
    assert state.immutable_surfaces == []
    assert state.rejected_experiments == []
    assert state.last_injected_mutation is None
    assert isinstance(state.updated_at, float)
    assert state.updated_at > 0


def test_pause_and_resume(tmp_path: Path) -> None:
    """Verify pause() and resume() toggle state correctly."""
    store = HumanControlStore(path=str(tmp_path / "control.json"))

    # Initial state should not be paused
    initial = store.get_state()
    assert initial.paused is False

    # Pause sets paused=True
    paused_state = store.pause()
    assert paused_state.paused is True

    # Verify persistence
    reloaded = store.get_state()
    assert reloaded.paused is True

    # Resume sets paused=False
    resumed_state = store.resume()
    assert resumed_state.paused is False

    # Verify persistence
    final = store.get_state()
    assert final.paused is False


def test_pause_idempotency(tmp_path: Path) -> None:
    """Verify calling pause() twice is idempotent."""
    store = HumanControlStore(path=str(tmp_path / "control.json"))

    state1 = store.pause()
    assert state1.paused is True

    state2 = store.pause()
    assert state2.paused is True

    # Verify state is consistent
    final = store.get_state()
    assert final.paused is True


def test_resume_idempotency(tmp_path: Path) -> None:
    """Verify calling resume() twice is idempotent."""
    store = HumanControlStore(path=str(tmp_path / "control.json"))

    # Start paused
    store.pause()

    state1 = store.resume()
    assert state1.paused is False

    state2 = store.resume()
    assert state2.paused is False

    # Verify state is consistent
    final = store.get_state()
    assert final.paused is False


def test_pin_surface(tmp_path: Path) -> None:
    """Verify pin_surface() adds surfaces to immutable list."""
    store = HumanControlStore(path=str(tmp_path / "control.json"))

    # Pin first surface
    state1 = store.pin_surface("auth.login")
    assert "auth.login" in state1.immutable_surfaces

    # Pin second surface
    state2 = store.pin_surface("billing.charge")
    assert "auth.login" in state2.immutable_surfaces
    assert "billing.charge" in state2.immutable_surfaces

    # Verify persistence
    reloaded = store.get_state()
    assert set(reloaded.immutable_surfaces) == {"auth.login", "billing.charge"}


def test_pin_surface_idempotency(tmp_path: Path) -> None:
    """Verify pinning the same surface twice doesn't duplicate it."""
    store = HumanControlStore(path=str(tmp_path / "control.json"))

    store.pin_surface("auth.login")
    state = store.pin_surface("auth.login")

    # Should only appear once
    assert state.immutable_surfaces.count("auth.login") == 1

    # Verify persistence deduplicates (save_state uses set())
    reloaded = store.get_state()
    assert reloaded.immutable_surfaces == ["auth.login"]


def test_unpin_surface(tmp_path: Path) -> None:
    """Verify unpin_surface() removes surfaces from immutable list."""
    store = HumanControlStore(path=str(tmp_path / "control.json"))

    # Pin two surfaces
    store.pin_surface("auth.login")
    store.pin_surface("billing.charge")

    # Unpin one
    state = store.unpin_surface("auth.login")
    assert "auth.login" not in state.immutable_surfaces
    assert "billing.charge" in state.immutable_surfaces

    # Verify persistence
    reloaded = store.get_state()
    assert reloaded.immutable_surfaces == ["billing.charge"]


def test_unpin_surface_idempotency(tmp_path: Path) -> None:
    """Verify unpinning a surface that doesn't exist is safe."""
    store = HumanControlStore(path=str(tmp_path / "control.json"))

    # Unpin nonexistent surface
    state1 = store.unpin_surface("nonexistent")
    assert state1.immutable_surfaces == []

    # Pin one surface then unpin it twice
    store.pin_surface("auth.login")
    store.unpin_surface("auth.login")
    state2 = store.unpin_surface("auth.login")
    assert state2.immutable_surfaces == []


def test_reject_experiment(tmp_path: Path) -> None:
    """Verify reject_experiment() adds experiment IDs to rejected list."""
    store = HumanControlStore(path=str(tmp_path / "control.json"))

    # Reject first experiment
    state1 = store.reject_experiment("exp-001")
    assert "exp-001" in state1.rejected_experiments

    # Reject second experiment
    state2 = store.reject_experiment("exp-002")
    assert "exp-001" in state2.rejected_experiments
    assert "exp-002" in state2.rejected_experiments

    # Verify persistence
    reloaded = store.get_state()
    assert set(reloaded.rejected_experiments) == {"exp-001", "exp-002"}


def test_reject_experiment_idempotency(tmp_path: Path) -> None:
    """Verify rejecting the same experiment twice doesn't duplicate it."""
    store = HumanControlStore(path=str(tmp_path / "control.json"))

    store.reject_experiment("exp-001")
    state = store.reject_experiment("exp-001")

    # Should only appear once
    assert state.rejected_experiments.count("exp-001") == 1

    # Verify persistence deduplicates (save_state uses set())
    reloaded = store.get_state()
    assert reloaded.rejected_experiments == ["exp-001"]


def test_mark_injected(tmp_path: Path) -> None:
    """Verify mark_injected() records mutation path."""
    store = HumanControlStore(path=str(tmp_path / "control.json"))

    # Mark first mutation
    state1 = store.mark_injected("prompt/auth/v1.2")
    assert state1.last_injected_mutation == "prompt/auth/v1.2"

    # Mark second mutation (should overwrite)
    state2 = store.mark_injected("prompt/billing/v3.0")
    assert state2.last_injected_mutation == "prompt/billing/v3.0"

    # Verify persistence
    reloaded = store.get_state()
    assert reloaded.last_injected_mutation == "prompt/billing/v3.0"


def test_json_persistence_survives_reload(tmp_path: Path) -> None:
    """Verify state survives reload from disk."""
    path = tmp_path / "control.json"
    store1 = HumanControlStore(path=str(path))

    # Set up complex state
    store1.pause()
    store1.pin_surface("auth.login")
    store1.pin_surface("billing.charge")
    store1.reject_experiment("exp-001")
    store1.reject_experiment("exp-002")
    store1.mark_injected("prompt/test/v1.0")

    # Create new store instance pointing to same file
    store2 = HumanControlStore(path=str(path))
    state = store2.get_state()

    # Verify all state persisted
    assert state.paused is True
    assert set(state.immutable_surfaces) == {"auth.login", "billing.charge"}
    assert set(state.rejected_experiments) == {"exp-001", "exp-002"}
    assert state.last_injected_mutation == "prompt/test/v1.0"


def test_updated_at_timestamp_changes(tmp_path: Path) -> None:
    """Verify updated_at timestamp changes on save."""
    store = HumanControlStore(path=str(tmp_path / "control.json"))

    state1 = store.pause()
    ts1 = state1.updated_at

    time.sleep(0.01)  # Small delay to ensure timestamp difference

    state2 = store.resume()
    ts2 = state2.updated_at

    assert ts2 > ts1


def test_json_format_is_sorted_and_deduplicated(tmp_path: Path) -> None:
    """Verify JSON output is sorted and deduplicated for consistency."""
    path = tmp_path / "control.json"
    store = HumanControlStore(path=str(path))

    # Add surfaces in random order with duplicates
    store.pin_surface("zulu")
    store.pin_surface("alpha")
    store.pin_surface("charlie")
    store.pin_surface("alpha")  # Duplicate

    # Add experiments in random order with duplicates
    store.reject_experiment("exp-999")
    store.reject_experiment("exp-001")
    store.reject_experiment("exp-001")  # Duplicate

    # Read raw JSON
    with path.open("r") as f:
        data = json.load(f)

    # Verify sorted and deduplicated
    assert data["immutable_surfaces"] == ["alpha", "charlie", "zulu"]
    assert data["rejected_experiments"] == ["exp-001", "exp-999"]


def test_directory_creation(tmp_path: Path) -> None:
    """Verify store creates parent directories if they don't exist."""
    nested_path = tmp_path / "nested" / "deep" / "control.json"
    store = HumanControlStore(path=str(nested_path))

    # Should create directories without error
    store.pause()

    # Verify file was created
    assert nested_path.exists()
    assert nested_path.parent.is_dir()


def test_concurrent_operations_maintain_state(tmp_path: Path) -> None:
    """Verify multiple operations maintain consistent state."""
    store = HumanControlStore(path=str(tmp_path / "control.json"))

    # Perform multiple operations
    store.pause()
    store.pin_surface("surface1")
    store.reject_experiment("exp1")
    store.mark_injected("mutation1")
    store.pin_surface("surface2")
    store.resume()
    store.reject_experiment("exp2")

    # Verify final state
    state = store.get_state()
    assert state.paused is False
    assert set(state.immutable_surfaces) == {"surface1", "surface2"}
    assert set(state.rejected_experiments) == {"exp1", "exp2"}
    assert state.last_injected_mutation == "mutation1"


def test_empty_string_values_are_preserved(tmp_path: Path) -> None:
    """Verify empty strings are preserved in the state."""
    store = HumanControlStore(path=str(tmp_path / "control.json"))

    # Pin empty string surface
    state1 = store.pin_surface("")
    assert "" in state1.immutable_surfaces

    # Reject empty string experiment
    state2 = store.reject_experiment("")
    assert "" in state2.rejected_experiments

    # Mark empty string mutation
    state3 = store.mark_injected("")
    assert state3.last_injected_mutation == ""

    # Verify persistence
    reloaded = store.get_state()
    assert "" in reloaded.immutable_surfaces
    assert "" in reloaded.rejected_experiments
    assert reloaded.last_injected_mutation == ""


def test_unicode_values_are_preserved(tmp_path: Path) -> None:
    """Verify Unicode characters are preserved in the state."""
    store = HumanControlStore(path=str(tmp_path / "control.json"))

    unicode_surface = "auth.login_🔐"
    unicode_experiment = "exp-测试-001"
    unicode_mutation = "prompt/émoji/v1.0"

    store.pin_surface(unicode_surface)
    store.reject_experiment(unicode_experiment)
    store.mark_injected(unicode_mutation)

    # Verify persistence
    reloaded = store.get_state()
    assert unicode_surface in reloaded.immutable_surfaces
    assert unicode_experiment in reloaded.rejected_experiments
    assert reloaded.last_injected_mutation == unicode_mutation


def test_special_characters_in_values(tmp_path: Path) -> None:
    """Verify special characters are preserved in the state."""
    store = HumanControlStore(path=str(tmp_path / "control.json"))

    special_surface = "auth/login:v1.0@prod"
    special_experiment = "exp-with-dashes_and_underscores.and.dots"
    special_mutation = "prompt\\with\\backslashes"

    store.pin_surface(special_surface)
    store.reject_experiment(special_experiment)
    store.mark_injected(special_mutation)

    # Verify persistence
    reloaded = store.get_state()
    assert special_surface in reloaded.immutable_surfaces
    assert special_experiment in reloaded.rejected_experiments
    assert reloaded.last_injected_mutation == special_mutation


def test_type_coercion_from_json(tmp_path: Path) -> None:
    """Verify type coercion handles non-standard JSON values."""
    path = tmp_path / "control.json"

    # Write JSON with type variations
    data = {
        "paused": 1,  # Truthy int instead of bool
        "immutable_surfaces": ["surface1", "surface2"],
        "rejected_experiments": ["exp1"],
        "last_injected_mutation": None,
        "updated_at": 1234567890.123,
    }
    with path.open("w") as f:
        json.dump(data, f)

    # Load and verify type coercion
    store = HumanControlStore(path=str(path))
    state = store.get_state()

    assert state.paused is True  # int(1) coerced to bool(True)
    assert isinstance(state.paused, bool)
    assert isinstance(state.immutable_surfaces, list)
    assert isinstance(state.rejected_experiments, list)
    assert state.last_injected_mutation is None
    assert isinstance(state.updated_at, float)


def test_missing_fields_use_defaults(tmp_path: Path) -> None:
    """Verify missing JSON fields fall back to default values."""
    path = tmp_path / "control.json"

    # Write minimal JSON with missing fields
    with path.open("w") as f:
        json.dump({}, f)

    store = HumanControlStore(path=str(path))
    state = store.get_state()

    # All fields should have default values
    assert state.paused is False
    assert state.immutable_surfaces == []
    assert state.rejected_experiments == []
    assert state.last_injected_mutation is None
    assert isinstance(state.updated_at, float)
    assert state.updated_at > 0


def test_partial_state_preserves_existing_fields(tmp_path: Path) -> None:
    """Verify partial JSON preserves existing fields."""
    path = tmp_path / "control.json"

    # Write JSON with only some fields
    data = {
        "paused": True,
        "immutable_surfaces": ["surface1"],
    }
    with path.open("w") as f:
        json.dump(data, f)

    store = HumanControlStore(path=str(path))
    state = store.get_state()

    # Existing fields preserved
    assert state.paused is True
    assert state.immutable_surfaces == ["surface1"]

    # Missing fields use defaults
    assert state.rejected_experiments == []
    assert state.last_injected_mutation is None


def test_null_last_injected_mutation_is_preserved(tmp_path: Path) -> None:
    """Verify null value for last_injected_mutation is preserved."""
    store = HumanControlStore(path=str(tmp_path / "control.json"))

    # Set then clear
    store.mark_injected("mutation1")
    state1 = store.get_state()
    assert state1.last_injected_mutation == "mutation1"

    # Manually set to None via JSON
    path = tmp_path / "control.json"
    data = {
        "paused": False,
        "immutable_surfaces": [],
        "rejected_experiments": [],
        "last_injected_mutation": None,
        "updated_at": time.time(),
    }
    with path.open("w") as f:
        json.dump(data, f)

    state2 = store.get_state()
    assert state2.last_injected_mutation is None


def test_large_lists_are_handled(tmp_path: Path) -> None:
    """Verify store handles large lists efficiently."""
    store = HumanControlStore(path=str(tmp_path / "control.json"))

    # Add many surfaces
    for i in range(1000):
        store.pin_surface(f"surface_{i:04d}")

    # Add many experiments
    for i in range(1000):
        store.reject_experiment(f"exp_{i:04d}")

    # Verify persistence and count
    state = store.get_state()
    assert len(state.immutable_surfaces) == 1000
    assert len(state.rejected_experiments) == 1000

    # Verify sorted
    assert state.immutable_surfaces[0] == "surface_0000"
    assert state.immutable_surfaces[-1] == "surface_0999"


def test_unpin_removes_all_duplicates(tmp_path: Path) -> None:
    """Verify unpin_surface removes all instances if duplicates exist."""
    path = tmp_path / "control.json"

    # Manually create JSON with duplicate surfaces (bypass normal flow)
    data = {
        "paused": False,
        "immutable_surfaces": ["auth", "billing", "auth", "auth"],
        "rejected_experiments": [],
        "last_injected_mutation": None,
        "updated_at": time.time(),
    }
    with path.open("w") as f:
        json.dump(data, f)

    store = HumanControlStore(path=str(path))
    state = store.unpin_surface("auth")

    # All instances of "auth" should be removed
    assert "auth" not in state.immutable_surfaces
    assert "billing" in state.immutable_surfaces

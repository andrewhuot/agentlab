"""Tests for human control CLI commands (pause, resume, reject, pin, unpin)."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from runner import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def isolated_control_store(tmp_dir, monkeypatch):
    """Isolate the HumanControlStore to a temporary directory."""
    control_path = os.path.join(tmp_dir, "human_control.json")

    # Monkey patch the _control_store function to use our tmp path
    from optimizer.human_control import HumanControlStore

    def mock_control_store():
        return HumanControlStore(path=control_path)

    monkeypatch.setattr("runner._control_store", mock_control_store)

    return control_path


class TestPauseCommand:
    """Test the 'autoagent pause' command."""

    def test_pause_outputs_confirmation(self, runner, isolated_control_store):
        """pause command outputs confirmation message."""
        result = runner.invoke(cli, ["pause"])
        assert result.exit_code == 0
        assert "Optimizer paused" in result.output
        assert "autoagent resume" in result.output

    def test_pause_creates_state_file(self, runner, isolated_control_store):
        """pause command creates the control state file."""
        runner.invoke(cli, ["pause"])
        assert Path(isolated_control_store).exists()

    def test_pause_sets_paused_true(self, runner, isolated_control_store):
        """pause command sets paused flag to true in state."""
        runner.invoke(cli, ["pause"])

        with Path(isolated_control_store).open("r", encoding="utf-8") as f:
            state = json.load(f)

        assert state["paused"] is True

    def test_pause_idempotent(self, runner, isolated_control_store):
        """pause command can be called multiple times without error."""
        result1 = runner.invoke(cli, ["pause"])
        result2 = runner.invoke(cli, ["pause"])

        assert result1.exit_code == 0
        assert result2.exit_code == 0


class TestResumeCommand:
    """Test the 'autoagent resume' command."""

    def test_resume_outputs_confirmation(self, runner, isolated_control_store):
        """resume command outputs confirmation message."""
        result = runner.invoke(cli, ["resume"])
        assert result.exit_code == 0
        assert "Optimizer resumed" in result.output

    def test_resume_sets_paused_false(self, runner, isolated_control_store):
        """resume command sets paused flag to false in state."""
        # First pause
        runner.invoke(cli, ["pause"])

        # Then resume
        runner.invoke(cli, ["resume"])

        with Path(isolated_control_store).open("r", encoding="utf-8") as f:
            state = json.load(f)

        assert state["paused"] is False

    def test_resume_without_pause(self, runner, isolated_control_store):
        """resume command works even if optimizer was never paused."""
        result = runner.invoke(cli, ["resume"])
        assert result.exit_code == 0
        assert "Optimizer resumed" in result.output


class TestPinCommand:
    """Test the 'autoagent pin' command."""

    def test_pin_requires_surface_argument(self, runner):
        """pin command requires a surface argument."""
        result = runner.invoke(cli, ["pin"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output or "Error" in result.output

    def test_pin_outputs_confirmation(self, runner, isolated_control_store):
        """pin command outputs confirmation with surface name."""
        result = runner.invoke(cli, ["pin", "safety_instructions"])
        assert result.exit_code == 0
        assert "Pinned 'safety_instructions'" in result.output
        assert "immutable" in result.output

    def test_pin_adds_surface_to_state(self, runner, isolated_control_store):
        """pin command adds surface to immutable_surfaces list."""
        runner.invoke(cli, ["pin", "prompts.root"])

        with Path(isolated_control_store).open("r", encoding="utf-8") as f:
            state = json.load(f)

        assert "prompts.root" in state["immutable_surfaces"]

    def test_pin_multiple_surfaces(self, runner, isolated_control_store):
        """pin command can pin multiple surfaces."""
        runner.invoke(cli, ["pin", "safety_instructions"])
        runner.invoke(cli, ["pin", "prompts.root"])
        runner.invoke(cli, ["pin", "model_config.temperature"])

        with Path(isolated_control_store).open("r", encoding="utf-8") as f:
            state = json.load(f)

        assert "safety_instructions" in state["immutable_surfaces"]
        assert "prompts.root" in state["immutable_surfaces"]
        assert "model_config.temperature" in state["immutable_surfaces"]
        assert len(state["immutable_surfaces"]) == 3


class TestUnpinCommand:
    """Test the 'autoagent unpin' command."""

    def test_unpin_requires_surface_argument(self, runner):
        """unpin command requires a surface argument."""
        result = runner.invoke(cli, ["unpin"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output or "Error" in result.output

    def test_unpin_outputs_confirmation(self, runner, isolated_control_store):
        """unpin command outputs confirmation with surface name."""
        runner.invoke(cli, ["pin", "safety_instructions"])
        result = runner.invoke(cli, ["unpin", "safety_instructions"])

        assert result.exit_code == 0
        assert "Unpinned 'safety_instructions'" in result.output
        assert "Optimizer can now modify it" in result.output

    def test_unpin_removes_surface_from_state(self, runner, isolated_control_store):
        """unpin command removes surface from immutable_surfaces list."""
        runner.invoke(cli, ["pin", "prompts.root"])
        runner.invoke(cli, ["unpin", "prompts.root"])

        with Path(isolated_control_store).open("r", encoding="utf-8") as f:
            state = json.load(f)

        assert "prompts.root" not in state["immutable_surfaces"]

    def test_unpin_without_pin(self, runner, isolated_control_store):
        """unpin command works even if surface was never pinned."""
        result = runner.invoke(cli, ["unpin", "nonexistent_surface"])
        assert result.exit_code == 0
        assert "Unpinned 'nonexistent_surface'" in result.output

    def test_unpin_preserves_other_surfaces(self, runner, isolated_control_store):
        """unpin command only removes the specified surface."""
        runner.invoke(cli, ["pin", "surface_a"])
        runner.invoke(cli, ["pin", "surface_b"])
        runner.invoke(cli, ["pin", "surface_c"])
        runner.invoke(cli, ["unpin", "surface_b"])

        with Path(isolated_control_store).open("r", encoding="utf-8") as f:
            state = json.load(f)

        assert "surface_a" in state["immutable_surfaces"]
        assert "surface_b" not in state["immutable_surfaces"]
        assert "surface_c" in state["immutable_surfaces"]


class TestRejectCommand:
    """Test the 'autoagent reject' command."""

    def test_reject_requires_experiment_id_argument(self, runner):
        """reject command requires an experiment_id argument."""
        result = runner.invoke(cli, ["reject"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output or "Error" in result.output

    def test_reject_outputs_confirmation_no_canary(self, runner, isolated_control_store, tmp_dir):
        """reject command outputs confirmation when no active canary."""
        db_path = os.path.join(tmp_dir, "test.db")
        configs_dir = os.path.join(tmp_dir, "configs")
        os.makedirs(configs_dir, exist_ok=True)

        result = runner.invoke(cli, [
            "reject",
            "exp_abc123",
            "--db", db_path,
            "--configs-dir", configs_dir,
        ])

        assert result.exit_code == 0
        assert "Rejected experiment exp_abc123" in result.output
        assert "No active canary" in result.output

    def test_reject_adds_experiment_to_rejected_list(self, runner, isolated_control_store, tmp_dir):
        """reject command adds experiment_id to rejected_experiments list."""
        db_path = os.path.join(tmp_dir, "test.db")
        configs_dir = os.path.join(tmp_dir, "configs")
        os.makedirs(configs_dir, exist_ok=True)

        runner.invoke(cli, [
            "reject",
            "exp_xyz789",
            "--db", db_path,
            "--configs-dir", configs_dir,
        ])

        with Path(isolated_control_store).open("r", encoding="utf-8") as f:
            state = json.load(f)

        assert "exp_xyz789" in state["rejected_experiments"]

    def test_reject_multiple_experiments(self, runner, isolated_control_store, tmp_dir):
        """reject command can reject multiple experiments."""
        db_path = os.path.join(tmp_dir, "test.db")
        configs_dir = os.path.join(tmp_dir, "configs")
        os.makedirs(configs_dir, exist_ok=True)

        runner.invoke(cli, ["reject", "exp_1", "--db", db_path, "--configs-dir", configs_dir])
        runner.invoke(cli, ["reject", "exp_2", "--db", db_path, "--configs-dir", configs_dir])
        runner.invoke(cli, ["reject", "exp_3", "--db", db_path, "--configs-dir", configs_dir])

        with Path(isolated_control_store).open("r", encoding="utf-8") as f:
            state = json.load(f)

        assert "exp_1" in state["rejected_experiments"]
        assert "exp_2" in state["rejected_experiments"]
        assert "exp_3" in state["rejected_experiments"]

    def test_reject_uses_default_paths(self, runner, isolated_control_store):
        """reject command can use default db and configs-dir paths."""
        # This should not error even without explicit paths
        result = runner.invoke(cli, ["reject", "exp_default"])
        assert result.exit_code == 0


class TestHumanControlIntegration:
    """Integration tests for human control command interactions."""

    def test_pause_resume_cycle(self, runner, isolated_control_store):
        """Full pause-resume cycle maintains state correctly."""
        # Initial state: not paused
        runner.invoke(cli, ["resume"])

        # Pause
        result1 = runner.invoke(cli, ["pause"])
        assert "paused" in result1.output

        # Verify paused
        with Path(isolated_control_store).open("r", encoding="utf-8") as f:
            state = json.load(f)
        assert state["paused"] is True

        # Resume
        result2 = runner.invoke(cli, ["resume"])
        assert "resumed" in result2.output

        # Verify resumed
        with Path(isolated_control_store).open("r", encoding="utf-8") as f:
            state = json.load(f)
        assert state["paused"] is False

    def test_pin_unpin_cycle(self, runner, isolated_control_store):
        """Full pin-unpin cycle maintains state correctly."""
        surface = "test.surface.path"

        # Pin
        runner.invoke(cli, ["pin", surface])

        with Path(isolated_control_store).open("r", encoding="utf-8") as f:
            state = json.load(f)
        assert surface in state["immutable_surfaces"]

        # Unpin
        runner.invoke(cli, ["unpin", surface])

        with Path(isolated_control_store).open("r", encoding="utf-8") as f:
            state = json.load(f)
        assert surface not in state["immutable_surfaces"]

    def test_all_controls_coexist(self, runner, isolated_control_store, tmp_dir):
        """All control commands can coexist in the same state file."""
        db_path = os.path.join(tmp_dir, "test.db")
        configs_dir = os.path.join(tmp_dir, "configs")
        os.makedirs(configs_dir, exist_ok=True)

        # Use all control commands
        runner.invoke(cli, ["pause"])
        runner.invoke(cli, ["pin", "surface_1"])
        runner.invoke(cli, ["pin", "surface_2"])
        runner.invoke(cli, ["reject", "exp_123", "--db", db_path, "--configs-dir", configs_dir])

        # Verify all state is present
        with Path(isolated_control_store).open("r", encoding="utf-8") as f:
            state = json.load(f)

        assert state["paused"] is True
        assert "surface_1" in state["immutable_surfaces"]
        assert "surface_2" in state["immutable_surfaces"]
        assert "exp_123" in state["rejected_experiments"]
        assert "updated_at" in state

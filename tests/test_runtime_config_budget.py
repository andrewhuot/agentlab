"""Tests for BudgetRuntimeConfig in agent/config/runtime.py."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from agent.config.runtime import (
    BudgetRuntimeConfig,
    RuntimeConfig,
    load_runtime_config,
)


def test_budget_runtime_config_defaults():
    """Test BudgetRuntimeConfig default values."""
    budget = BudgetRuntimeConfig()
    assert budget.per_cycle_dollars == 1.0
    assert budget.daily_dollars == 10.0
    assert budget.stall_threshold_cycles == 5
    assert budget.tracker_db_path == ".autoagent/cost_tracker.db"


def test_budget_runtime_config_custom_values():
    """Test BudgetRuntimeConfig with custom values."""
    budget = BudgetRuntimeConfig(
        per_cycle_dollars=2.5,
        daily_dollars=50.0,
        stall_threshold_cycles=10,
        tracker_db_path="/custom/path/tracker.db",
    )
    assert budget.per_cycle_dollars == 2.5
    assert budget.daily_dollars == 50.0
    assert budget.stall_threshold_cycles == 10
    assert budget.tracker_db_path == "/custom/path/tracker.db"


def test_budget_runtime_config_validation_per_cycle_dollars():
    """Test per_cycle_dollars validation constraints (ge=0.0, le=10000.0)."""
    # Valid boundary values
    BudgetRuntimeConfig(per_cycle_dollars=0.0)
    BudgetRuntimeConfig(per_cycle_dollars=10000.0)

    # Invalid: negative
    with pytest.raises(ValidationError) as exc_info:
        BudgetRuntimeConfig(per_cycle_dollars=-1.0)
    assert "per_cycle_dollars" in str(exc_info.value)

    # Invalid: exceeds max
    with pytest.raises(ValidationError) as exc_info:
        BudgetRuntimeConfig(per_cycle_dollars=10001.0)
    assert "per_cycle_dollars" in str(exc_info.value)


def test_budget_runtime_config_validation_daily_dollars():
    """Test daily_dollars validation constraints (ge=0.0, le=100000.0)."""
    # Valid boundary values
    BudgetRuntimeConfig(daily_dollars=0.0)
    BudgetRuntimeConfig(daily_dollars=100000.0)

    # Invalid: negative
    with pytest.raises(ValidationError) as exc_info:
        BudgetRuntimeConfig(daily_dollars=-1.0)
    assert "daily_dollars" in str(exc_info.value)

    # Invalid: exceeds max
    with pytest.raises(ValidationError) as exc_info:
        BudgetRuntimeConfig(daily_dollars=100001.0)
    assert "daily_dollars" in str(exc_info.value)


def test_budget_runtime_config_validation_stall_threshold_cycles():
    """Test stall_threshold_cycles validation constraints (ge=1, le=1000)."""
    # Valid boundary values
    BudgetRuntimeConfig(stall_threshold_cycles=1)
    BudgetRuntimeConfig(stall_threshold_cycles=1000)

    # Invalid: zero
    with pytest.raises(ValidationError) as exc_info:
        BudgetRuntimeConfig(stall_threshold_cycles=0)
    assert "stall_threshold_cycles" in str(exc_info.value)

    # Invalid: exceeds max
    with pytest.raises(ValidationError) as exc_info:
        BudgetRuntimeConfig(stall_threshold_cycles=1001)
    assert "stall_threshold_cycles" in str(exc_info.value)


def test_runtime_config_includes_budget_field():
    """Test RuntimeConfig includes budget field with correct defaults."""
    config = RuntimeConfig()
    assert hasattr(config, "budget")
    assert isinstance(config.budget, BudgetRuntimeConfig)
    assert config.budget.per_cycle_dollars == 1.0
    assert config.budget.daily_dollars == 10.0
    assert config.budget.stall_threshold_cycles == 5
    assert config.budget.tracker_db_path == ".autoagent/cost_tracker.db"


def test_load_runtime_config_with_budget_section():
    """Test load_runtime_config picks up budget section from YAML."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        yaml_content = {
            "budget": {
                "per_cycle_dollars": 3.5,
                "daily_dollars": 75.0,
                "stall_threshold_cycles": 8,
                "tracker_db_path": "/tmp/custom_tracker.db",
            },
            "optimizer": {
                "use_mock": True,
            },
        }
        yaml.dump(yaml_content, tmp)
        tmp_path = tmp.name

    try:
        config = load_runtime_config(tmp_path)
        assert config.budget.per_cycle_dollars == 3.5
        assert config.budget.daily_dollars == 75.0
        assert config.budget.stall_threshold_cycles == 8
        assert config.budget.tracker_db_path == "/tmp/custom_tracker.db"
    finally:
        Path(tmp_path).unlink()


def test_load_runtime_config_partial_budget_section():
    """Test load_runtime_config with partial budget section uses defaults for missing fields."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        yaml_content = {
            "budget": {
                "daily_dollars": 100.0,
            },
        }
        yaml.dump(yaml_content, tmp)
        tmp_path = tmp.name

    try:
        config = load_runtime_config(tmp_path)
        # Explicitly set field
        assert config.budget.daily_dollars == 100.0
        # Default fields
        assert config.budget.per_cycle_dollars == 1.0
        assert config.budget.stall_threshold_cycles == 5
        assert config.budget.tracker_db_path == ".autoagent/cost_tracker.db"
    finally:
        Path(tmp_path).unlink()


def test_load_runtime_config_missing_file_uses_budget_defaults():
    """Test load_runtime_config returns budget defaults when YAML file is missing."""
    config = load_runtime_config("/nonexistent/path/autoagent.yaml")
    assert config.budget.per_cycle_dollars == 1.0
    assert config.budget.daily_dollars == 10.0
    assert config.budget.stall_threshold_cycles == 5
    assert config.budget.tracker_db_path == ".autoagent/cost_tracker.db"

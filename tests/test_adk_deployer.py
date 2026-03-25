"""Tests for ADK deployer."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from adk.deployer import AdkDeployer
from adk.errors import AdkDeployError


@pytest.fixture
def sample_agent_dir(tmp_path: Path) -> Path:
    """Create a sample agent directory."""
    agent_dir = tmp_path / "test_agent"
    agent_dir.mkdir()

    # Create required files
    (agent_dir / "__init__.py").write_text("from .agent import root_agent\n")
    (agent_dir / "agent.py").write_text(
        '''from google.adk.agents import Agent

root_agent = Agent(
    name="test_agent",
    model="gemini-2.0-flash",
    instruction="Test agent for deployment",
)
'''
    )
    (agent_dir / "tools.py").write_text("# Tools\n")

    return agent_dir


def test_deploy_to_cloud_run_mock(sample_agent_dir: Path):
    """Test Cloud Run deployment with mocked gcloud command."""
    deployer = AdkDeployer(project="test-project", region="us-central1")

    mock_output = {
        "status": {
            "url": "https://test-agent-us-central1.run.app",
            "conditions": [{"status": "True"}],
        }
    }

    with patch("subprocess.run") as mock_run:
        # Mock gcloud --version check
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Google Cloud SDK 400.0.0\n",
            stderr="",
        )

        # Mock gcloud deploy command
        def mock_subprocess(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("command", [])
            if "deploy" in cmd:
                return MagicMock(
                    returncode=0,
                    stdout=json.dumps(mock_output),
                    stderr="",
                )
            else:
                # For gcloud --version check
                return MagicMock(
                    returncode=0,
                    stdout="Google Cloud SDK 400.0.0\n",
                    stderr="",
                )

        mock_run.side_effect = mock_subprocess

        result = deployer.deploy_to_cloud_run(str(sample_agent_dir))

        assert result.target == "cloud-run"
        assert "run.app" in result.url
        assert result.status == "deployed"


def test_deploy_to_vertex_ai_mock(sample_agent_dir: Path):
    """Test Vertex AI deployment with mocked gcloud command."""
    deployer = AdkDeployer(project="test-project", region="us-central1")

    mock_output = {
        "endpoint": "projects/test-project/locations/us-central1/agents/test-agent",
        "name": "test-agent",
    }

    with patch("subprocess.run") as mock_run:
        # Mock gcloud commands
        def mock_subprocess(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("command", [])
            if "create" in cmd or "deploy" in cmd:
                return MagicMock(
                    returncode=0,
                    stdout=json.dumps(mock_output),
                    stderr="",
                )
            else:
                # For gcloud --version check
                return MagicMock(
                    returncode=0,
                    stdout="Google Cloud SDK 400.0.0\n",
                    stderr="",
                )

        mock_run.side_effect = mock_subprocess

        result = deployer.deploy_to_vertex_ai(str(sample_agent_dir))

        assert result.target == "vertex-ai"
        assert result.status == "deployed"
        assert "endpoint" in result.deployment_info or "name" in result.deployment_info


def test_get_deploy_status_cloud_run(sample_agent_dir: Path):
    """Test getting Cloud Run deployment status."""
    deployer = AdkDeployer(project="test-project", region="us-central1")

    mock_output = {
        "status": {
            "url": "https://test-agent-us-central1.run.app",
            "conditions": [{"status": "True"}],
            "traffic": [{"revisionName": "test-agent-00001", "percent": 100}],
        },
        "metadata": {"generation": "1"},
    }

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_output),
            stderr="",
        )

        status = deployer.get_deploy_status("cloud-run", "test-agent")

        assert status["service_name"] == "test-agent"
        assert "url" in status
        assert status["ready"] is True


def test_get_deploy_status_vertex_ai(sample_agent_dir: Path):
    """Test getting Vertex AI deployment status."""
    deployer = AdkDeployer(project="test-project", region="us-central1")

    mock_output = {
        "endpoint": "projects/test-project/locations/us-central1/agents/test-agent",
        "state": "ACTIVE",
        "createTime": "2026-03-25T00:00:00Z",
        "updateTime": "2026-03-25T01:00:00Z",
    }

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_output),
            stderr="",
        )

        status = deployer.get_deploy_status("vertex-ai", "test-agent")

        assert status["agent_name"] == "test-agent"
        assert "endpoint" in status
        assert status["state"] == "ACTIVE"


def test_deploy_invalid_path_raises_error():
    """Test that deploy raises error for invalid path."""
    deployer = AdkDeployer(project="test-project")

    with pytest.raises(AdkDeployError) as exc_info:
        deployer.deploy_to_cloud_run("/nonexistent/path")

    assert "Agent path not found" in str(exc_info.value)


def test_deploy_missing_init_raises_error(tmp_path: Path):
    """Test that deploy raises error for missing __init__.py."""
    agent_dir = tmp_path / "invalid_agent"
    agent_dir.mkdir()
    (agent_dir / "agent.py").write_text("# Agent\n")

    deployer = AdkDeployer(project="test-project")

    with pytest.raises(AdkDeployError) as exc_info:
        deployer.deploy_to_cloud_run(str(agent_dir))

    assert "Missing __init__.py" in str(exc_info.value)


def test_deploy_missing_agent_py_raises_error(tmp_path: Path):
    """Test that deploy raises error for missing agent.py."""
    agent_dir = tmp_path / "invalid_agent"
    agent_dir.mkdir()
    (agent_dir / "__init__.py").write_text("# Init\n")

    deployer = AdkDeployer(project="test-project")

    with pytest.raises(AdkDeployError) as exc_info:
        deployer.deploy_to_cloud_run(str(agent_dir))

    assert "Missing agent.py" in str(exc_info.value)


def test_gcloud_not_installed_raises_error(sample_agent_dir: Path):
    """Test that missing gcloud CLI raises error."""
    deployer = AdkDeployer(project="test-project")

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(AdkDeployError) as exc_info:
            deployer.deploy_to_cloud_run(str(sample_agent_dir))

        assert "gcloud CLI not found" in str(exc_info.value)


def test_gcloud_deploy_failure_raises_error(sample_agent_dir: Path):
    """Test that gcloud deploy failure raises error."""
    deployer = AdkDeployer(project="test-project")

    with patch("subprocess.run") as mock_run:
        # Mock gcloud --version check (success)
        # Then mock deploy command (failure)
        def mock_subprocess(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("command", [])
            if "deploy" in cmd:
                return MagicMock(
                    returncode=1,
                    stdout="",
                    stderr="ERROR: Deployment failed\n",
                )
            else:
                return MagicMock(
                    returncode=0,
                    stdout="Google Cloud SDK 400.0.0\n",
                    stderr="",
                )

        mock_run.side_effect = mock_subprocess

        with pytest.raises(AdkDeployError) as exc_info:
            deployer.deploy_to_cloud_run(str(sample_agent_dir))

        assert "gcloud deploy failed" in str(exc_info.value)


def test_service_name_sanitization(sample_agent_dir: Path):
    """Test that service names are properly sanitized."""
    # Create agent dir with underscores and uppercase
    agent_dir = sample_agent_dir.parent / "Test_Agent_Name"
    agent_dir.mkdir()
    (agent_dir / "__init__.py").write_text("from .agent import root_agent\n")
    (agent_dir / "agent.py").write_text("# Agent\n")

    deployer = AdkDeployer(project="test-project")

    mock_output = {
        "status": {
            "url": "https://test-agent-name-us-central1.run.app",
            "conditions": [],
        }
    }

    with patch("subprocess.run") as mock_run:

        def mock_subprocess(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("command", [])
            if "deploy" in cmd:
                # Check that service name was sanitized
                assert "test-agent-name" in cmd
                return MagicMock(
                    returncode=0,
                    stdout=json.dumps(mock_output),
                    stderr="",
                )
            else:
                return MagicMock(
                    returncode=0,
                    stdout="Google Cloud SDK 400.0.0\n",
                    stderr="",
                )

        mock_run.side_effect = mock_subprocess

        result = deployer.deploy_to_cloud_run(str(agent_dir))

        assert result.status == "deployed"


def test_deploy_timeout_raises_error(sample_agent_dir: Path):
    """Test that deploy timeout raises error."""
    deployer = AdkDeployer(project="test-project")

    with patch("subprocess.run") as mock_run:

        def mock_subprocess(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("command", [])
            if "deploy" in cmd:
                raise subprocess.TimeoutExpired(cmd, timeout=600)
            else:
                return MagicMock(
                    returncode=0,
                    stdout="Google Cloud SDK 400.0.0\n",
                    stderr="",
                )

        mock_run.side_effect = mock_subprocess

        with pytest.raises(AdkDeployError) as exc_info:
            deployer.deploy_to_cloud_run(str(sample_agent_dir))

        assert "timed out" in str(exc_info.value).lower()


def test_get_status_invalid_target_raises_error():
    """Test that invalid target raises error."""
    deployer = AdkDeployer(project="test-project")

    with pytest.raises(AdkDeployError) as exc_info:
        deployer.get_deploy_status("invalid-target", "test-agent")

    assert "Unknown target" in str(exc_info.value)


def test_deploy_constructs_correct_command(sample_agent_dir: Path):
    """Test that deploy constructs the correct gcloud command."""
    deployer = AdkDeployer(project="my-project", region="europe-west1")

    mock_output = {
        "status": {"url": "https://test.run.app", "conditions": []}
    }

    with patch("subprocess.run") as mock_run:

        def mock_subprocess(*args, **kwargs):
            cmd = args[0] if args else kwargs.get("command", [])
            if "deploy" in cmd:
                # Verify command structure
                assert "--project=my-project" in cmd
                assert "--region=europe-west1" in cmd
                assert "--platform=managed" in cmd
                assert "--allow-unauthenticated" in cmd
                return MagicMock(
                    returncode=0,
                    stdout=json.dumps(mock_output),
                    stderr="",
                )
            else:
                return MagicMock(
                    returncode=0,
                    stdout="Google Cloud SDK 400.0.0\n",
                    stderr="",
                )

        mock_run.side_effect = mock_subprocess

        result = deployer.deploy_to_cloud_run(str(sample_agent_dir))

        assert result.deployment_info["project"] == "my-project"
        assert result.deployment_info["region"] == "europe-west1"

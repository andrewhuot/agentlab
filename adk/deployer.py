"""Deploy ADK agents to Cloud Run or Vertex AI."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from adk.errors import AdkDeployError
from adk.types import DeployResult


class AdkDeployer:
    """Deploys ADK agents to Cloud Run or Vertex AI."""

    def __init__(self, project: str, region: str = "us-central1"):
        """Initialize deployer.

        Args:
            project: GCP project ID
            region: GCP region (default: us-central1)
        """
        self.project = project
        self.region = region

    def deploy_to_cloud_run(
        self,
        agent_path: str,
        service_name: str | None = None,
    ) -> DeployResult:
        """Deploy to Cloud Run.

        Strategy:
        1. Validate agent directory
        2. Build container with Cloud Build
        3. Deploy via gcloud run deploy
        4. Return service URL

        Args:
            agent_path: Path to ADK agent directory
            service_name: Service name (defaults to agent directory name)

        Returns:
            DeployResult with service URL and status

        Raises:
            AdkDeployError: If deployment fails
        """
        try:
            path = Path(agent_path)
            if not path.exists():
                raise AdkDeployError(f"Agent path not found: {agent_path}")

            # Validate agent structure
            self._validate_agent_directory(path)

            # Determine service name
            if service_name is None:
                service_name = path.name.replace("_", "-").lower()

            # Check gcloud availability
            self._check_gcloud_installed()

            # Deploy using gcloud
            result = self._deploy_cloud_run_gcloud(path, service_name)

            return DeployResult(
                target="cloud-run",
                url=result.get("url", ""),
                status="deployed",
                deployment_info=result,
            )

        except AdkDeployError:
            raise
        except Exception as exc:
            raise AdkDeployError(f"Cloud Run deployment failed: {exc}") from exc

    def deploy_to_vertex_ai(
        self,
        agent_path: str,
        agent_name: str | None = None,
    ) -> DeployResult:
        """Deploy to Vertex AI Agent Builder.

        Strategy:
        1. Package agent directory
        2. Upload to Vertex AI
        3. Create agent resource
        4. Return agent endpoint

        Args:
            agent_path: Path to ADK agent directory
            agent_name: Agent name (defaults to directory name)

        Returns:
            DeployResult with agent endpoint and status

        Raises:
            AdkDeployError: If deployment fails
        """
        try:
            path = Path(agent_path)
            if not path.exists():
                raise AdkDeployError(f"Agent path not found: {agent_path}")

            # Validate agent structure
            self._validate_agent_directory(path)

            # Determine agent name
            if agent_name is None:
                agent_name = path.name

            # Check gcloud availability
            self._check_gcloud_installed()

            # Deploy using gcloud
            result = self._deploy_vertex_ai_gcloud(path, agent_name)

            return DeployResult(
                target="vertex-ai",
                url=result.get("endpoint", ""),
                status="deployed",
                deployment_info=result,
            )

        except AdkDeployError:
            raise
        except Exception as exc:
            raise AdkDeployError(f"Vertex AI deployment failed: {exc}") from exc

    def get_deploy_status(self, target: str, resource_name: str) -> dict:
        """Get deployment status.

        Args:
            target: Deployment target ("cloud-run" or "vertex-ai")
            resource_name: Service/agent name

        Returns:
            Status dictionary with deployment info

        Raises:
            AdkDeployError: If status check fails
        """
        try:
            if target == "cloud-run":
                return self._get_cloud_run_status(resource_name)
            elif target == "vertex-ai":
                return self._get_vertex_ai_status(resource_name)
            else:
                raise AdkDeployError(f"Unknown target: {target}")

        except AdkDeployError:
            raise
        except Exception as exc:
            raise AdkDeployError(f"Failed to get status: {exc}") from exc

    def _validate_agent_directory(self, path: Path) -> None:
        """Validate agent directory structure.

        Args:
            path: Path to agent directory

        Raises:
            AdkDeployError: If validation fails
        """
        if not (path / "__init__.py").exists():
            raise AdkDeployError(
                f"Missing __init__.py in {path}. Not a valid ADK agent."
            )

        if not (path / "agent.py").exists():
            raise AdkDeployError(
                f"Missing agent.py in {path}. Not a valid ADK agent."
            )

    def _check_gcloud_installed(self) -> None:
        """Check if gcloud CLI is installed.

        Raises:
            AdkDeployError: If gcloud is not available
        """
        try:
            result = subprocess.run(
                ["gcloud", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise AdkDeployError(
                    "gcloud CLI not configured. Run 'gcloud auth login'."
                )
        except FileNotFoundError:
            raise AdkDeployError(
                "gcloud CLI not found. "
                "Install from https://cloud.google.com/sdk/docs/install"
            )
        except subprocess.TimeoutExpired:
            raise AdkDeployError("gcloud check timed out")

    def _deploy_cloud_run_gcloud(
        self, agent_dir: Path, service_name: str
    ) -> dict:
        """Deploy to Cloud Run using gcloud.

        Args:
            agent_dir: Agent directory
            service_name: Service name

        Returns:
            Deployment result dict

        Raises:
            AdkDeployError: If deployment fails
        """
        cmd = [
            "gcloud",
            "run",
            "deploy",
            service_name,
            f"--source={agent_dir}",
            f"--project={self.project}",
            f"--region={self.region}",
            "--platform=managed",
            "--allow-unauthenticated",
            "--format=json",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )

            if result.returncode != 0:
                raise AdkDeployError(f"gcloud deploy failed: {result.stderr}")

            output = json.loads(result.stdout)
            service_url = output.get("status", {}).get("url", "")

            return {
                "service_name": service_name,
                "url": service_url,
                "project": self.project,
                "region": self.region,
                "status": output.get("status", {}).get("conditions", []),
            }

        except subprocess.TimeoutExpired:
            raise AdkDeployError("Cloud Run deployment timed out (10 minutes)")
        except json.JSONDecodeError as exc:
            raise AdkDeployError(f"Failed to parse output: {exc}") from exc

    def _deploy_vertex_ai_gcloud(self, agent_dir: Path, agent_name: str) -> dict:
        """Deploy to Vertex AI using gcloud.

        Args:
            agent_dir: Agent directory
            agent_name: Agent name

        Returns:
            Deployment result dict

        Raises:
            AdkDeployError: If deployment fails
        """
        # Try alpha/beta command first
        cmd = [
            "gcloud",
            "alpha",
            "ai",
            "agents",
            "create",
            agent_name,
            f"--project={self.project}",
            f"--region={self.region}",
            f"--source={agent_dir}",
            "--format=json",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode != 0:
                # Try alternative command structure
                alt_cmd = [
                    "gcloud",
                    "ai",
                    "agents",
                    "deploy",
                    agent_name,
                    f"--source={agent_dir}",
                    f"--project={self.project}",
                    f"--region={self.region}",
                    "--format=json",
                ]

                result = subprocess.run(
                    alt_cmd,
                    capture_output=True,
                    text=True,
                    timeout=600,
                )

                if result.returncode != 0:
                    raise AdkDeployError(f"gcloud agent deploy failed: {result.stderr}")

            output = json.loads(result.stdout)
            endpoint = output.get("endpoint", output.get("name", ""))

            return {
                "agent_name": agent_name,
                "endpoint": endpoint,
                "project": self.project,
                "region": self.region,
                "details": output,
            }

        except subprocess.TimeoutExpired:
            raise AdkDeployError("Vertex AI deployment timed out (10 minutes)")
        except json.JSONDecodeError as exc:
            raise AdkDeployError(f"Failed to parse output: {exc}") from exc

    def _get_cloud_run_status(self, service_name: str) -> dict:
        """Get Cloud Run service status.

        Args:
            service_name: Service name

        Returns:
            Status dict

        Raises:
            AdkDeployError: If status check fails
        """
        cmd = [
            "gcloud",
            "run",
            "services",
            "describe",
            service_name,
            f"--project={self.project}",
            f"--region={self.region}",
            "--format=json",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise AdkDeployError(f"Failed to get status: {result.stderr}")

            output = json.loads(result.stdout)

            return {
                "service_name": service_name,
                "url": output.get("status", {}).get("url", ""),
                "ready": output.get("status", {}).get("conditions", [{}])[0].get(
                    "status"
                )
                == "True",
                "traffic": output.get("status", {}).get("traffic", []),
                "updated": output.get("metadata", {}).get("generation", ""),
            }

        except subprocess.TimeoutExpired:
            raise AdkDeployError("Status check timed out")
        except json.JSONDecodeError as exc:
            raise AdkDeployError(f"Failed to parse output: {exc}") from exc

    def _get_vertex_ai_status(self, agent_name: str) -> dict:
        """Get Vertex AI agent status.

        Args:
            agent_name: Agent name

        Returns:
            Status dict

        Raises:
            AdkDeployError: If status check fails
        """
        cmd = [
            "gcloud",
            "alpha",
            "ai",
            "agents",
            "describe",
            agent_name,
            f"--project={self.project}",
            f"--region={self.region}",
            "--format=json",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                # Try non-alpha command
                alt_cmd = [
                    "gcloud",
                    "ai",
                    "agents",
                    "describe",
                    agent_name,
                    f"--project={self.project}",
                    f"--region={self.region}",
                    "--format=json",
                ]

                result = subprocess.run(
                    alt_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode != 0:
                    raise AdkDeployError(f"Failed to get status: {result.stderr}")

            output = json.loads(result.stdout)

            return {
                "agent_name": agent_name,
                "endpoint": output.get("endpoint", ""),
                "state": output.get("state", "UNKNOWN"),
                "created": output.get("createTime", ""),
                "updated": output.get("updateTime", ""),
                "details": output,
            }

        except subprocess.TimeoutExpired:
            raise AdkDeployError("Status check timed out")
        except json.JSONDecodeError as exc:
            raise AdkDeployError(f"Failed to parse output: {exc}") from exc

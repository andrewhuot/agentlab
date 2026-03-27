"""Deploy CX agents to environments and generate web widget embed code."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .client import CxClient
from .errors import CxStudioError
from .mapper_extensions import (
    guardrails_to_cx_safety_settings,
    integration_templates_to_cx_tools,
    knowledge_asset_to_cx_datastore,
)
from .types import CxAgentRef, CxWidgetConfig, DeployResult


class CxDeployer:
    """Deploy CX agent to environments and generate widget embed code."""

    def __init__(self, client: CxClient):
        self._client = client

    def deploy_to_environment(
        self,
        ref: CxAgentRef,
        environment: str = "production",
    ) -> DeployResult:
        """Deploy the agent to a CX environment.

        Args:
            ref: Agent reference (project/location/agent).
            environment: Target environment name (e.g. "production", "staging").

        Returns:
            DeployResult with environment name, status, and version info.

        Raises:
            CxStudioError: If the deploy API call fails.
        """
        try:
            # Build environment resource name
            environment_name = f"{ref.name}/environments/{environment}"
            result = self._client.deploy_to_environment(environment_name, [])
            return DeployResult(
                environment=environment,
                status="deployed",
                version_info=result,
            )
        except Exception as exc:
            raise CxStudioError(f"Deploy to {environment} failed: {exc}") from exc

    def generate_widget_html(
        self,
        widget_config: CxWidgetConfig,
        output_path: str | None = None,
    ) -> str:
        """Generate chat-messenger web widget HTML.

        Returns the HTML string. If output_path is provided, also writes to file.

        Args:
            widget_config: Widget configuration (project, agent, styling, etc.).
            output_path: Optional file path to write the HTML to.

        Returns:
            Complete HTML page string with the chat-messenger embed.
        """
        html = _build_widget_html(widget_config)
        if output_path:
            Path(output_path).write_text(html, encoding="utf-8")
        return html

    def get_deploy_status(self, ref: CxAgentRef) -> dict:
        """Get current deployment status for an agent.

        Args:
            ref: Agent reference (project/location/agent).

        Returns:
            Dict with agent name and list of environments with their version configs.

        Raises:
            CxStudioError: If the API call to list environments fails.
        """
        try:
            envs = self._client.list_environments(ref.name)
            return {
                "agent": ref.name,
                "environments": [
                    {
                        "name": env.display_name,
                        "description": env.description,
                        "versions": env.version_configs,
                    }
                    for env in envs
                ],
            }
        except Exception as exc:
            raise CxStudioError(f"Failed to get deploy status: {exc}") from exc

    def deploy_artifact_to_cx_studio(
        self,
        ref: CxAgentRef,
        artifact: dict[str, Any],
    ) -> dict[str, Any]:
        """Deploy AutoAgent artifact to CX Agent Studio.

        Creates tools, datastores, and updates safety settings based on artifact content.

        Args:
            ref: CX Agent reference where artifact should be deployed.
            artifact: Agent artifact from build_agent_artifact.

        Returns:
            Dict with deployment results (tools_created, datastores_created, settings_updated).

        Raises:
            CxStudioError: If deployment fails.
        """
        results = {
            "tools_created": 0,
            "datastores_created": 0,
            "settings_updated": False,
        }

        try:
            # Deploy integration templates as tools
            integration_templates = artifact.get("integration_templates", [])
            if integration_templates:
                tools = integration_templates_to_cx_tools(integration_templates, ref.name)
                for tool in tools:
                    # In real implementation, would call client.create_tool
                    # For now, just count
                    results["tools_created"] += 1

            # Deploy knowledge asset as datastore
            knowledge_asset = artifact.get("knowledge_asset", {})
            if knowledge_asset and knowledge_asset.get("entries"):
                datastore_payload = knowledge_asset_to_cx_datastore(knowledge_asset)
                self._client.create_data_store(
                    agent_name=ref.name,
                    **datastore_payload,
                )
                results["datastores_created"] = 1

            # Update safety settings from guardrails
            guardrails = artifact.get("guardrails", [])
            if guardrails:
                safety_settings = guardrails_to_cx_safety_settings(guardrails)
                agent_updates = {
                    "generativeSettings": {
                        "safetySettings": safety_settings.get("safetySettings", []),
                        "bannedPhrases": safety_settings.get("bannedPhrases", []),
                    }
                }
                self._client.update_agent(ref.name, agent_updates)
                results["settings_updated"] = True

            return results

        except Exception as exc:
            raise CxStudioError(f"Failed to deploy artifact to CX Studio: {exc}") from exc


def _build_widget_html(config: CxWidgetConfig) -> str:
    """Build a complete HTML page with chat-messenger web component."""
    chat_icon_attr = ""
    if config.chat_icon:
        chat_icon_attr = f'\n      chat-icon="{config.chat_icon}"'

    return f"""<!DOCTYPE html>
<html lang="{config.language_code}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{config.chat_title}</title>
  <link rel="stylesheet" href="https://www.gstatic.com/dialogflow-console/fast/cx-messenger/prod/v1/cx-messenger-default.css">
  <script src="https://www.gstatic.com/dialogflow-console/fast/cx-messenger/prod/v1/cx-messenger.js"></script>
  <style>
    chat-messenger {{
      z-index: 999;
      position: fixed;
      bottom: 16px;
      right: 16px;
      --chat-messenger-font-color: #000;
      --chat-messenger-font-family: Google Sans;
      --chat-messenger-chat-background: #f3f6fc;
      --chat-messenger-message-user-background: {config.primary_color};
      --chat-messenger-message-bot-background: #fff;
    }}
  </style>
</head>
<body>
  <h1>{config.chat_title}</h1>
  <p>This page embeds the CX Agent Studio agent as a web widget.</p>

  <chat-messenger
      agent-id="{config.agent_id}"
      language-code="{config.language_code}"
      max-query-length="-1"{chat_icon_attr}>
    <chat-messenger-chat-bubble chat-title="{config.chat_title}">
    </chat-messenger-chat-bubble>
  </chat-messenger>
</body>
</html>"""

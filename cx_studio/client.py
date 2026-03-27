"""REST API client for CX Agent Studio (Google Cloud Customer Engagement AI).

Uses ``httpx`` when available and falls back to ``urllib.request`` so the
module remains importable in environments that have not installed httpx.

API Reference: https://docs.cloud.google.com/customer-engagement-ai/conversational-agents/ps/reference/rest/v1-overview
"""
from __future__ import annotations

import importlib.util
import json
import time
from datetime import datetime, timezone
from typing import Any

from .auth import CxAuth
from .errors import CxApiError
from .types import (
    CxAgent,
    CxAgentSnapshot,
    CxDataStore,
    CxEnvironment,
    CxFlow,
    CxIntent,
    CxPlaybook,
    CxTestCase,
    CxTool,
)

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

_HTTPX_AVAILABLE = importlib.util.find_spec("httpx") is not None


def _build_base_url(location: str) -> str:
    """Return the CX Agent Studio API v1 base URL.

    Note: CX Agent Studio uses ces.googleapis.com, not dialogflow.googleapis.com.
    The location parameter is currently unused as the API uses a global endpoint.
    """
    return "https://ces.googleapis.com/v1"


class CxClient:
    """Thin REST client for the CX Agent Studio API v1.

    All methods return parsed Python dicts/lists or typed Pydantic models.
    Network errors are translated into ``CxApiError``.

    API Reference: https://docs.cloud.google.com/customer-engagement-ai/conversational-agents/ps/reference/rest/v1-overview

    Args:
        auth: A ``CxAuth`` instance that supplies Authorization headers.
        timeout: Per-request timeout in seconds.
        max_retries: Number of times to retry on transient (5xx / 429) errors.
    """

    def __init__(
        self,
        auth: CxAuth,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self._auth = auth
        self._timeout = timeout
        self._max_retries = max_retries

    # ------------------------------------------------------------------
    # Low-level transport
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        url: str,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        """Execute an HTTP request with retry logic.

        Retries on HTTP 429 and 5xx responses with exponential back-off.

        Args:
            method: HTTP verb (``"GET"``, ``"POST"``, ``"PATCH"``, …).
            url: Full URL including query parameters.
            json_body: Optional JSON-serialisable request body.

        Returns:
            Parsed JSON response (dict, list, or ``None`` for empty bodies).

        Raises:
            CxApiError: on non-2xx final response or network failure.
        """
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                headers = self._auth.get_headers()
                body_bytes = (
                    json.dumps(json_body).encode() if json_body is not None else None
                )

                if _HTTPX_AVAILABLE:
                    response = self._httpx_request(method, url, headers, body_bytes)
                else:
                    response = self._urllib_request(method, url, headers, body_bytes)

                status_code, response_text = response

                if status_code in (429, 500, 502, 503, 504) and attempt < self._max_retries - 1:
                    # Exponential back-off: 1s, 2s, 4s…
                    time.sleep(2 ** attempt)
                    continue

                if status_code < 200 or status_code >= 300:
                    raise CxApiError(
                        f"CX API error {status_code}: {url}",
                        status_code=status_code,
                        response_body=response_text,
                    )

                if not response_text:
                    return None
                return json.loads(response_text)

            except CxApiError:
                raise
            except Exception as exc:
                last_exc = exc
                if attempt < self._max_retries - 1:
                    time.sleep(2 ** attempt)

        raise CxApiError(
            f"Request failed after {self._max_retries} attempts: {last_exc}",
            status_code=0,
            response_body=str(last_exc),
        )

    def _httpx_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body_bytes: bytes | None,
    ) -> tuple[int, str]:
        """Execute request via httpx."""
        import httpx  # type: ignore[import]

        with httpx.Client(timeout=self._timeout) as client:
            resp = client.request(
                method,
                url,
                headers=headers,
                content=body_bytes,
            )
        return resp.status_code, resp.text

    def _urllib_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body_bytes: bytes | None,
    ) -> tuple[int, str]:
        """Execute request via stdlib urllib (fallback)."""
        import urllib.error
        import urllib.request

        req = urllib.request.Request(
            url,
            data=body_bytes,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                return resp.status, resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return exc.code, body

    # ------------------------------------------------------------------
    # Agent
    # ------------------------------------------------------------------

    def get_agent(self, agent_name: str) -> CxAgent:
        """Fetch a single CX agent by resource name.

        Args:
            agent_name: Fully-qualified name, e.g.
                ``projects/my-proj/locations/us-central1/apps/my-app/agents/abc123``.

        Note: CX Agent Studio resource path includes the app layer.
        """
        location = self._location_from_name(agent_name)
        base = _build_base_url(location)
        data = self._request("GET", f"{base}/{agent_name}")
        return CxAgent(
            name=data.get("name", ""),
            display_name=data.get("displayName", ""),
            default_language_code=data.get("defaultLanguageCode", "en"),
            description=data.get("description", ""),
            generative_settings=data.get("generativeSettings", {}),
        )

    def list_agents(self, app_name: str) -> list[CxAgent]:
        """List all CX agents in an app.

        Args:
            app_name: Fully-qualified app name, e.g.
                ``projects/my-proj/locations/us-central1/apps/my-app``.

        Note: In CX Agent Studio, agents are nested under apps.
        """
        location = self._location_from_name(app_name)
        base = _build_base_url(location)
        data = self._request("GET", f"{base}/{app_name}/agents")
        agents_raw = data.get("agents", []) if data else []
        return [
            CxAgent(
                name=a.get("name", ""),
                display_name=a.get("displayName", ""),
                default_language_code=a.get("defaultLanguageCode", "en"),
                description=a.get("description", ""),
                generative_settings=a.get("generativeSettings", {}),
            )
            for a in agents_raw
        ]

    def update_agent(self, agent_name: str, updates: dict[str, Any]) -> CxAgent:
        """Patch a CX agent resource.

        Args:
            agent_name: Fully-qualified agent resource name.
            updates: Fields to update (uses PATCH semantics).
        """
        location = self._location_from_name(agent_name)
        base = _build_base_url(location)
        data = self._request("PATCH", f"{base}/{agent_name}", json_body=updates)
        return CxAgent(
            name=data.get("name", ""),
            display_name=data.get("displayName", ""),
            default_language_code=data.get("defaultLanguageCode", "en"),
            description=data.get("description", ""),
            generative_settings=data.get("generativeSettings", {}),
        )

    # ------------------------------------------------------------------
    # Playbooks
    # ------------------------------------------------------------------

    def list_playbooks(self, app_name: str) -> list[CxPlaybook]:
        """List all playbooks for a CX app.

        Args:
            app_name: Fully-qualified app name (playbooks are app-level resources).

        Note: In CX Agent Studio, playbooks are app-level resources, not agent-level.
        API endpoint: {app_name}/playbooks (NOT {agent_name}/playbooks)
        """
        location = self._location_from_name(app_name)
        base = _build_base_url(location)
        # TODO: Verify if playbooks endpoint exists - may need to use /examples or other resource
        data = self._request("GET", f"{base}/{app_name}/playbooks")
        items = data.get("playbooks", []) if data else []
        return [
            CxPlaybook(
                name=p.get("name", ""),
                display_name=p.get("displayName", ""),
                instructions=p.get("instruction", {}).get("steps", []),
                steps=p.get("steps", []),
                examples=p.get("examples", []),
            )
            for p in items
        ]

    def update_playbook(
        self, playbook_name: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        """Patch a CX playbook resource.

        Args:
            playbook_name: Fully-qualified playbook resource name.
            updates: Fields to update.
        """
        location = self._location_from_name(playbook_name)
        base = _build_base_url(location)
        return self._request("PATCH", f"{base}/{playbook_name}", json_body=updates)  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    def list_tools(self, app_name: str) -> list[CxTool]:
        """List all tools registered on a CX app.

        Args:
            app_name: Fully-qualified app name (tools are app-level resources).

        Note: In CX Agent Studio, tools are app-level resources, not agent-level.
        API Reference: projects.locations.apps.tools
        """
        location = self._location_from_name(app_name)
        base = _build_base_url(location)
        data = self._request("GET", f"{base}/{app_name}/tools")
        items = data.get("tools", []) if data else []
        return [
            CxTool(
                name=t.get("name", ""),
                display_name=t.get("displayName", ""),
                tool_type=t.get("toolType", ""),
                spec=t.get("openApiSpec", t.get("dataStoreSpec", {})),
            )
            for t in items
        ]

    # ------------------------------------------------------------------
    # Flows - DEPRECATED/UNVERIFIED
    # ------------------------------------------------------------------

    def list_flows(self, app_name: str) -> list[CxFlow]:
        """UNVERIFIED: CX Agent Studio may not have flows.

        This method is a placeholder for backward compatibility.
        The real CX Agent Studio API may use different orchestration primitives.

        TODO: Verify if flows exist in CX Agent Studio or replace with correct resource.
        """
        location = self._location_from_name(app_name)
        base = _build_base_url(location)
        # This endpoint may not exist in the real API
        data = self._request("GET", f"{base}/{app_name}/flows")
        items = data.get("flows", []) if data else []
        return [
            CxFlow(
                name=f.get("name", ""),
                display_name=f.get("displayName", ""),
                pages=f.get("pages", []),
                transition_routes=f.get("transitionRoutes", []),
                event_handlers=f.get("eventHandlers", []),
            )
            for f in items
        ]

    # ------------------------------------------------------------------
    # Intents - DEPRECATED/UNVERIFIED
    # ------------------------------------------------------------------

    def list_intents(self, app_name: str) -> list[CxIntent]:
        """UNVERIFIED: CX Agent Studio may not have intents.

        This method is a placeholder for backward compatibility.
        CX Agent Studio uses examples instead of training phrases.

        TODO: Replace with list_examples or verify intent endpoint exists.
        """
        location = self._location_from_name(app_name)
        base = _build_base_url(location)
        # This endpoint may not exist in the real API
        data = self._request("GET", f"{base}/{app_name}/intents")
        items = data.get("intents", []) if data else []
        return [
            CxIntent(
                name=i.get("name", ""),
                display_name=i.get("displayName", ""),
                training_phrases=i.get("trainingPhrases", []),
            )
            for i in items
        ]

    # ------------------------------------------------------------------
    # Examples (replaces test cases in CX Agent Studio)
    # ------------------------------------------------------------------

    def list_test_cases(self, app_name: str) -> list[CxTestCase]:
        """DEPRECATED: Use list_examples instead.

        CX Agent Studio uses 'examples' (few-shot learning) instead of test cases.
        This method is kept for backward compatibility.

        TODO: Migrate callers to use examples resource.
        """
        location = self._location_from_name(app_name)
        base = _build_base_url(location)
        # Try examples endpoint instead
        data = self._request("GET", f"{base}/{app_name}/examples")
        items = data.get("examples", data.get("testCases", [])) if data else []
        return [
            CxTestCase(
                name=tc.get("name", ""),
                display_name=tc.get("displayName", tc.get("name", "")),
                tags=tc.get("tags", []),
                conversation_turns=tc.get("conversationTurns", tc.get("testCaseConversationTurns", [])),
                expected_output=tc.get("expectedOutput", tc.get("lastTestResult", {})),
            )
            for tc in items
        ]

    # ------------------------------------------------------------------
    # Deployments (replaces environments in CX Agent Studio)
    # ------------------------------------------------------------------

    def list_environments(self, app_name: str) -> list[CxEnvironment]:
        """List all deployments (environments) for a CX app.

        Note: CX Agent Studio uses 'deployments' instead of 'environments'.
        API Reference: projects.locations.apps.deployments
        """
        location = self._location_from_name(app_name)
        base = _build_base_url(location)
        # Try deployments endpoint (the correct one for CX Agent Studio)
        data = self._request("GET", f"{base}/{app_name}/deployments")
        items = data.get("deployments", data.get("environments", [])) if data else []
        return [
            CxEnvironment(
                name=e.get("name", ""),
                display_name=e.get("displayName", e.get("name", "")),
                description=e.get("description", ""),
                version_configs=e.get("versionConfigs", []),
            )
            for e in items
        ]

    def list_data_stores(self, app_name: str) -> list[CxDataStore]:
        """List all data stores (knowledge bases) for a CX app.

        Note: Data stores are app-level resources in CX Agent Studio.
        Data stores are configured via tools with dataStoreSpec.
        """
        location = self._location_from_name(app_name)
        base = _build_base_url(location)
        # In CX Agent Studio, datastores are likely configured via tools
        # This endpoint may not exist - data stores might be in tool specs
        data = self._request("GET", f"{base}/{app_name}/dataStores")
        items = data.get("dataStores", []) if data else []
        return [
            CxDataStore(
                name=ds.get("name", ""),
                display_name=ds.get("displayName", ""),
                data_store_type=ds.get("dataStoreType", "unstructured"),
                content_entries=ds.get("contentEntries", []),
            )
            for ds in items
        ]

    def create_data_store(
        self,
        app_name: str,
        display_name: str,
        content_entries: list[dict[str, Any]],
        data_store_type: str = "unstructured",
    ) -> CxDataStore:
        """Create a new data store for knowledge base content.

        Args:
            app_name: Fully-qualified app resource name.
            display_name: Human-readable name for the data store.
            content_entries: List of content entries (FAQs, procedures, etc.).
            data_store_type: Type of data store (unstructured, structured, website).

        Returns:
            Created CxDataStore instance.

        Note: In CX Agent Studio, data stores may be configured via tools.
        This method may need to create a tool with dataStoreSpec instead.
        """
        location = self._location_from_name(app_name)
        base = _build_base_url(location)
        body = {
            "displayName": display_name,
            "dataStoreType": data_store_type,
            "contentEntries": content_entries,
        }
        data = self._request("POST", f"{base}/{app_name}/dataStores", json_body=body)
        return CxDataStore(
            name=data.get("name", ""),
            display_name=data.get("displayName", ""),
            data_store_type=data.get("dataStoreType", "unstructured"),
            content_entries=data.get("contentEntries", []),
        )

    def deploy_to_environment(
        self,
        deployment_name: str,
        version_configs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Deploy app version to a deployment (environment).

        Args:
            deployment_name: Fully-qualified deployment resource name.
                e.g., projects/{project}/locations/{location}/apps/{app}/deployments/{deployment}
            version_configs: List of version configurations to deploy.

        Returns:
            Long-running operation response dict.

        Note: CX Agent Studio uses 'deployments' instead of 'environments'.
        API Reference: projects.locations.apps.deployments
        """
        location = self._location_from_name(deployment_name)
        base = _build_base_url(location)
        body = {"versionConfigs": version_configs}
        return self._request(  # type: ignore[return-value]
            "PATCH", f"{base}/{deployment_name}", json_body=body
        )

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------

    def fetch_snapshot(self, agent_name: str, app_name: str | None = None) -> CxAgentSnapshot:
        """Fetch and assemble a complete snapshot of a CX agent and its app.

        Calls all list endpoints in sequence and returns a ``CxAgentSnapshot``
        that can be persisted for offline use.

        Args:
            agent_name: Fully-qualified agent resource name.
                e.g., projects/{project}/locations/{location}/apps/{app}/agents/{agent}
            app_name: Optional app name. If not provided, extracted from agent_name.

        Note: In CX Agent Studio, most resources are at the app level, not agent level.
        """
        # Extract app name from agent name if not provided
        if app_name is None:
            # agent_name format: projects/{project}/locations/{location}/apps/{app}/agents/{agent}
            parts = agent_name.split("/agents/")
            if len(parts) >= 1:
                app_name = parts[0]  # Everything before /agents/
            else:
                raise ValueError(f"Invalid agent_name format: {agent_name}")

        agent = self.get_agent(agent_name)
        playbooks = self.list_playbooks(app_name)  # App-level resource
        tools = self.list_tools(app_name)  # App-level resource
        flows = self.list_flows(app_name)  # May not exist in CX Agent Studio
        intents = self.list_intents(app_name)  # May not exist in CX Agent Studio
        test_cases = self.list_test_cases(app_name)  # Actually examples in CX Agent Studio
        environments = self.list_environments(app_name)  # Actually deployments
        data_stores = self.list_data_stores(app_name)  # App-level resource

        return CxAgentSnapshot(
            agent=agent,
            playbooks=playbooks,
            tools=tools,
            flows=flows,
            intents=intents,
            test_cases=test_cases,
            environments=environments,
            data_stores=data_stores,
            fetched_at=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _location_from_name(resource_name: str) -> str:
        """Extract the GCP location from a fully-qualified resource name.

        Resource names follow the pattern::

            projects/{project}/locations/{location}/…

        Falls back to ``"global"`` when the name cannot be parsed.
        """
        parts = resource_name.split("/")
        try:
            loc_idx = parts.index("locations")
            return parts[loc_idx + 1]
        except (ValueError, IndexError):
            return "global"

"""Bidirectional mapping between ADK and AutoAgent config schemas.

The mapper is the translation layer between ADK's Python-based agent model and
AutoAgent's AgentConfig-compatible dict. It is intentionally stateless —
all state lives in the agent tree and config objects passed as arguments.

Layer: Layer 1 (Advanced). May import from Layer 0 / stdlib / PyPI only.
Never import from api/, web/, or other Layer 2 modules.
"""
from __future__ import annotations

import copy
from typing import Any

from .errors import AdkImportError
from .types import AdkAgentTree


class AdkMapper:
    """Bidirectional mapper between ADK and AutoAgent configs.

    All methods are pure functions over their arguments — no I/O, no state.
    """

    # ------------------------------------------------------------------
    # ADK → AutoAgent
    # ------------------------------------------------------------------

    def to_autoagent(self, agent_tree: AdkAgentTree) -> dict[str, Any]:
        """Convert an AdkAgentTree to an AgentConfig-compatible dict.

        Mapping rules:
        - Root agent instruction → prompts.root
        - Sub-agent instructions → prompts.<name>
        - Tool docstrings → tools.<name>.description
        - Sub-agents → routing.rules (derive keywords from agent names)
        - generate_config → generation settings (temperature, max_tokens)
        - model → model
        - Store original snapshot for round-trip in _adk_metadata

        Args:
            agent_tree: A complete AdkAgentTree as returned by AdkParser.

        Returns:
            A dict that can be loaded by AgentConfig.model_validate.

        Raises:
            AdkImportError: if the agent tree is structurally invalid.
        """
        try:
            config: dict[str, Any] = {
                "prompts": self._map_agents_to_prompts(agent_tree),
                "tools": self._map_tools(agent_tree.tools),
                "routing": self._map_routing(agent_tree.sub_agents),
                "_adk_metadata": {
                    "agent_name": agent_tree.agent.name,
                    "source_path": str(agent_tree.source_path),
                    # Store full serialized tree for lossless round-trip
                    "agent_tree": agent_tree.model_dump(),
                },
            }

            # Map model from agent or config
            model = agent_tree.agent.model or agent_tree.config.get("model", "")
            if model:
                config["model"] = model

            # Map generation settings
            generation_settings = self._extract_generation_settings(agent_tree)
            if generation_settings:
                config["generation"] = generation_settings

        except Exception as exc:
            raise AdkImportError(f"Failed to map ADK tree to AutoAgent config: {exc}") from exc

        return config

    # ------------------------------------------------------------------
    # AutoAgent → ADK
    # ------------------------------------------------------------------

    def to_adk(
        self,
        config: dict[str, Any],
        base_tree: AdkAgentTree,
    ) -> AdkAgentTree:
        """Overlay an optimized AutoAgent config onto a base ADK tree.

        The returned tree can be used to generate updated Python source files.

        Reverse mapping:
        - prompts.root → root agent instruction
        - prompts.<name> → sub-agent instructions
        - tools.<name>.timeout_ms → tool config (metadata only)
        - generation settings → generate_config
        - model → model

        Args:
            config: AutoAgent config dict (may be a partial optimized patch).
            base_tree: Original tree used as the base for unchanged fields.

        Returns:
            A new AdkAgentTree with config changes applied.

        Raises:
            AdkImportError: if the config cannot be applied to the tree.
        """
        try:
            result = AdkAgentTree(
                agent=copy.deepcopy(base_tree.agent),
                tools=copy.deepcopy(base_tree.tools),
                sub_agents=copy.deepcopy(base_tree.sub_agents),
                config=copy.deepcopy(base_tree.config),
                source_path=base_tree.source_path,
            )

            prompts = config.get("prompts", {})
            self._apply_prompts_to_agents(result, prompts)

            tools_config = config.get("tools", {})
            self._apply_tools_config(result, tools_config)

            generation = config.get("generation", {})
            self._apply_generation_settings(result, generation)

            # Propagate model override
            if "model" in config:
                result.agent.model = config["model"]
                result.config["model"] = config["model"]

        except Exception as exc:
            raise AdkImportError(f"Failed to map AutoAgent config to ADK tree: {exc}") from exc

        return result

    # ------------------------------------------------------------------
    # Private helpers — ADK → AutoAgent direction
    # ------------------------------------------------------------------

    def _map_agents_to_prompts(self, agent_tree: AdkAgentTree) -> dict[str, str]:
        """Flatten agent hierarchy to prompts dict.

        The root agent becomes 'root'; sub-agents use their names as keys.
        """
        prompts: dict[str, str] = {}

        # Root agent instruction
        if agent_tree.agent.instruction:
            prompts["root"] = agent_tree.agent.instruction

        # Sub-agent instructions
        for sub_tree in agent_tree.sub_agents:
            agent_name = sub_tree.agent.name or "unknown"
            if sub_tree.agent.instruction:
                prompts[agent_name] = sub_tree.agent.instruction

        return prompts

    def _map_tools(self, tools: list) -> dict[str, Any]:
        """Extract tool metadata from AdkTool list."""
        tools_config: dict[str, Any] = {}
        for tool in tools:
            tools_config[tool.name] = {
                "enabled": True,
                "description": tool.description,
                "signature": tool.signature,
                # Store reference to original function body for round-trip
                "_adk_function_body": tool.function_body,
            }
        return tools_config

    def _map_routing(self, sub_agents: list) -> dict[str, Any]:
        """Derive routing rules from sub-agent hierarchy.

        Strategy: Create a routing rule for each sub-agent, deriving keywords
        from the agent name (e.g., "billing_agent" → ["billing", "bill", "payment"]).
        """
        rules: list[dict[str, Any]] = []

        for sub_tree in sub_agents:
            agent_name = sub_tree.agent.name or "unknown"
            # Derive keywords from agent name
            keywords = self._derive_keywords_from_name(agent_name)

            rules.append({
                "specialist": agent_name,
                "keywords": keywords,
                "patterns": [],
                "_adk_agent_name": agent_name,
            })

        return {"rules": rules}

    def _derive_keywords_from_name(self, name: str) -> list[str]:
        """Derive routing keywords from agent name.

        Example: "billing_agent" → ["billing", "bill", "payment", "invoice"]
        """
        # Split on underscores and remove common suffixes
        parts = name.lower().replace("_agent", "").replace("agent", "").split("_")
        keywords = [p for p in parts if p]

        # Add common synonyms for known domains
        keyword_expansions = {
            "billing": ["bill", "payment", "invoice", "charge"],
            "support": ["help", "assist", "issue", "problem"],
            "order": ["purchase", "buy", "cart", "checkout"],
            "tech": ["technical", "bug", "error", "troubleshoot"],
        }

        for kw in keywords[:]:
            if kw in keyword_expansions:
                keywords.extend(keyword_expansions[kw][:3])  # Add top 3 synonyms

        return keywords[:10]  # Cap at 10 keywords

    def _extract_generation_settings(self, agent_tree: AdkAgentTree) -> dict[str, Any]:
        """Pull generation settings from agent tree."""
        settings = {}

        # Merge config.json and agent.generate_config
        merged = {**agent_tree.config, **agent_tree.agent.generate_config}

        if "temperature" in merged:
            settings["temperature"] = merged["temperature"]
        if "max_output_tokens" in merged:
            settings["max_tokens"] = merged["max_output_tokens"]
        if "max_tokens" in merged:
            settings["max_tokens"] = merged["max_tokens"]

        return settings

    # ------------------------------------------------------------------
    # Private helpers — AutoAgent → ADK direction
    # ------------------------------------------------------------------

    def _apply_prompts_to_agents(
        self,
        agent_tree: AdkAgentTree,
        prompts: dict[str, Any],
    ) -> None:
        """Write AutoAgent prompts back into agent tree in-place."""
        if not prompts:
            return

        # Apply root prompt
        if "root" in prompts:
            agent_tree.agent.instruction = prompts["root"]

        # Apply sub-agent prompts
        for sub_tree in agent_tree.sub_agents:
            agent_name = sub_tree.agent.name
            if agent_name in prompts:
                sub_tree.agent.instruction = prompts[agent_name]

    def _apply_tools_config(
        self,
        agent_tree: AdkAgentTree,
        tools_config: dict[str, Any],
    ) -> None:
        """Write tool config back into agent tree in-place.

        Note: Tool descriptions are read-only in this direction (they live in
        docstrings which we don't modify). This method exists for symmetry.
        """
        # Tool configs in AutoAgent don't directly map back to ADK source
        # because tool implementations are code, not config.
        # We only track enabled/disabled state in metadata.
        pass

    def _apply_generation_settings(
        self,
        agent_tree: AdkAgentTree,
        generation: dict[str, Any],
    ) -> None:
        """Write generation settings back into agent tree in-place."""
        if not generation:
            return

        if "temperature" in generation:
            agent_tree.agent.generate_config["temperature"] = generation["temperature"]
            agent_tree.config["temperature"] = generation["temperature"]

        if "max_tokens" in generation:
            agent_tree.agent.generate_config["max_output_tokens"] = generation["max_tokens"]
            agent_tree.config["max_output_tokens"] = generation["max_tokens"]

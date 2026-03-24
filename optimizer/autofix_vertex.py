"""Stub for Google Vertex AI Prompt Optimizer integration.

Not yet implemented — placeholder for future integration with
Vertex AI's prompt optimization service.
"""

from __future__ import annotations


class VertexPromptOptimizer:
    """Stub: Vertex AI Prompt Optimizer integration."""

    def __init__(self, project_id: str | None = None, location: str = "us-central1") -> None:
        self.project_id = project_id
        self.location = location
        self._available = False

    @property
    def is_available(self) -> bool:
        """Whether the Vertex AI integration is available."""
        return self._available

    def optimize_prompt(self, prompt: str, eval_cases: list[dict]) -> dict:
        """Optimize a prompt using Vertex AI.

        Raises NotImplementedError since this is a stub.
        """
        raise NotImplementedError("Vertex Prompt Optimizer integration not yet implemented")

"""ADK error types."""
from __future__ import annotations


class AdkError(Exception):
    """Base error for ADK operations."""


class AdkParseError(AdkError):
    """AST parsing failure."""


class AdkImportError(AdkError):
    """Import pipeline failure."""


class AdkExportError(AdkError):
    """Export pipeline failure."""


class AdkDeployError(AdkError):
    """Deployment failure."""

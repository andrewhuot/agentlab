"""ADK (Agent Development Kit) integration for AutoAgent.

Provides bidirectional integration with Google's Agent Development Kit:
- Parse ADK Python source code into structured config
- Map ADK agents to AutoAgent surfaces
- Export optimized configs back to ADK source
- Deploy to Cloud Run or Vertex AI

Public API:
    Types: AdkAgent, AdkAgentTree, AdkTool, AdkAgentRef
    Parser: parse_agent_directory
    Mapper: AdkMapper
    Importer: AdkImporter
    Exporter: AdkExporter
    Deployer: AdkDeployer
    Results: ImportResult, ExportResult, DeployResult
    Errors: AdkError, AdkParseError, AdkImportError, AdkExportError, AdkDeployError
"""
from __future__ import annotations

from adk.deployer import AdkDeployer
from adk.errors import (
    AdkDeployError,
    AdkError,
    AdkExportError,
    AdkImportError,
    AdkParseError,
)
from adk.exporter import AdkExporter
from adk.importer import AdkImporter
from adk.mapper import AdkMapper
from adk.parser import parse_agent_directory
from adk.types import (
    AdkAgent,
    AdkAgentRef,
    AdkAgentTree,
    AdkTool,
    DeployResult,
    ExportResult,
    ImportResult,
)

__all__ = [
    # Parser
    "parse_agent_directory",
    # Mapper
    "AdkMapper",
    # Importer
    "AdkImporter",
    # Exporter
    "AdkExporter",
    # Deployer
    "AdkDeployer",
    # Types
    "AdkAgent",
    "AdkAgentRef",
    "AdkAgentTree",
    "AdkTool",
    "ImportResult",
    "ExportResult",
    "DeployResult",
    # Errors
    "AdkError",
    "AdkParseError",
    "AdkImportError",
    "AdkExportError",
    "AdkDeployError",
]

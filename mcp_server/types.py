"""MCP protocol types — JSON-RPC 2.0 messages for MCP."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MCPToolParam:
    """Parameter definition for an MCP tool."""
    name: str
    description: str
    type: str = "string"
    required: bool = False

@dataclass
class MCPToolDef:
    """MCP tool definition."""
    name: str
    description: str
    parameters: list[MCPToolParam] = field(default_factory=list)

    def to_schema(self) -> dict[str, Any]:
        """Convert to MCP tool JSON schema format."""
        properties = {}
        required = []
        for p in self.parameters:
            properties[p.name] = {"type": p.type, "description": p.description}
            if p.required:
                required.append(p.name)
        schema: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
            },
        }
        if required:
            schema["inputSchema"]["required"] = required
        return schema

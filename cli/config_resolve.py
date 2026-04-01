"""Helpers for resolving effective config/runtime snapshots for CLI commands."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from agent.config.runtime import load_runtime_config
from cli.workspace import AgentLabWorkspace, discover_workspace


@dataclass(slots=True)
class ConfigResolution:
    """Describe the effective config/runtime snapshot for a CLI command."""

    command: str
    generated_at: str
    workspace_path: str | None
    workspace_name: str | None
    config_path: str | None
    runtime_config_path: str | None
    active_config_version: int | None
    config_summary: str
    runtime_mode: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation for lockfiles and CLI JSON output."""
        return asdict(self)


def _resolve_path(path: str | None) -> Path | None:
    """Resolve a user-facing path string into an absolute path when present."""
    if not path:
        return None
    return Path(path).expanduser().resolve()


def _workspace_or_cwd_lockfile_path(workspace: AgentLabWorkspace | None) -> Path:
    """Persist the lockfile in the workspace root when available, else current directory."""
    if workspace is not None:
        return workspace.root / "agentlab.lock"
    return Path.cwd() / "agentlab.lock"


def _load_config_summary(path: Path | None, workspace: AgentLabWorkspace | None) -> tuple[int | None, str]:
    """Load the selected config and return `(version, summary)` for UX surfaces."""
    if path is None or not path.exists():
        return None, "No config selected"

    config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if workspace is not None:
        resolved = workspace.resolve_active_config()
        if resolved is not None and resolved.path.resolve() == path.resolve():
            return resolved.version, workspace.summarize_config(config)
        return None, workspace.summarize_config(config)

    model = str(config.get("model") or "unknown-model")
    return None, model


def _runtime_mode_label(runtime_config_path: Path | None) -> str:
    """Summarize the runtime mode from the runtime config file when available."""
    if runtime_config_path is None or not runtime_config_path.exists():
        return "unknown"
    runtime = load_runtime_config(str(runtime_config_path))
    return "mock" if runtime.optimizer.use_mock else "live"


def resolve_config_snapshot(
    *,
    config_path: str | None = None,
    runtime_config_path: str | None = None,
    command: str,
) -> ConfigResolution:
    """Resolve the effective config/runtime snapshot for a command invocation."""
    workspace = discover_workspace()

    resolved_config_path = _resolve_path(config_path)
    if resolved_config_path is None and workspace is not None:
        resolved = workspace.resolve_active_config()
        if resolved is not None:
            resolved_config_path = resolved.path.resolve()

    resolved_runtime_path = _resolve_path(runtime_config_path)
    if resolved_runtime_path is None and workspace is not None:
        candidate = workspace.runtime_config_path.resolve()
        if candidate.exists():
            resolved_runtime_path = candidate
    if resolved_runtime_path is None:
        fallback = Path("agentlab.yaml").resolve()
        if fallback.exists():
            resolved_runtime_path = fallback

    active_config_version, config_summary = _load_config_summary(resolved_config_path, workspace)

    return ConfigResolution(
        command=command,
        generated_at=datetime.now(tz=timezone.utc).isoformat(),
        workspace_path=str(workspace.root) if workspace is not None else None,
        workspace_name=workspace.workspace_label if workspace is not None else None,
        config_path=str(resolved_config_path) if resolved_config_path is not None else None,
        runtime_config_path=str(resolved_runtime_path) if resolved_runtime_path is not None else None,
        active_config_version=active_config_version,
        config_summary=config_summary,
        runtime_mode=_runtime_mode_label(resolved_runtime_path),
    )


def persist_config_lockfile(resolution: ConfigResolution) -> Path:
    """Write the resolved config snapshot to `agentlab.lock`."""
    workspace = discover_workspace()
    lockfile_path = _workspace_or_cwd_lockfile_path(workspace)
    lockfile_path.write_text(
        json.dumps(resolution.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return lockfile_path


def render_config_resolution(resolution: ConfigResolution) -> str:
    """Render a human-readable config resolution summary."""
    config_label = resolution.config_path or "default"
    if resolution.active_config_version is not None:
        config_label = f"v{resolution.active_config_version:03d} -> {config_label}"

    workspace_label = resolution.workspace_name or "none"
    workspace_path = resolution.workspace_path or str(Path.cwd())
    runtime_label = resolution.runtime_config_path or "default runtime"

    return "\n".join(
        [
            f"  Workspace: {workspace_label}",
            f"  Path:      {workspace_path}",
            f"  Command:   {resolution.command}",
            f"  Config:    {config_label}",
            f"  Summary:   {resolution.config_summary}",
            f"  Runtime:   {runtime_label} ({resolution.runtime_mode})",
            "  Lockfile:  agentlab.lock",
        ]
    )

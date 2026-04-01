"""Branding helpers for the AgentLab CLI."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import tomllib

import click


@lru_cache(maxsize=1)
def get_agentlab_version() -> str:
    """Return the project version from source so local CLI runs stay honest."""
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject_path.open("rb") as handle:
        project = tomllib.load(handle)
    return str(project["project"]["version"])


def banner_enabled(ctx: click.Context | None) -> bool:
    """Resolve banner visibility across parent commands so suppression is inherited."""
    current = ctx
    while current is not None:
        params = current.params if isinstance(current.params, dict) else {}
        if params.get("quiet") or params.get("no_banner"):
            return False
        current = current.parent
    return True


def render_startup_banner(version: str) -> str:
    """Render the compact branded banner used on key startup surfaces."""
    logo_style = {"fg": "blue", "bold": True}
    title_style = {"fg": "white", "bold": True}

    lines = [
        click.style("      /\\        ", **logo_style)
        + click.style("___         __        ___                     __", **title_style),
        click.style("     /==\\       ", **logo_style)
        + click.style("/   | __  __/ /_____  /   | ____ ____  ____  / /_", **title_style),
        click.style("    /====\\      ", **logo_style)
        + click.style("/ /| |/ / / / __/ __ \\/ /| |/ __ `/ _ \\/ __ \\/ __/", **title_style),
        click.style("    |::::|      ", **logo_style)
        + click.style("/ ___ / /_/ / /_/ /_/ / ___ / /_/ /  __/ / / / /_", **title_style),
        click.style("    /|__|\\     ", **logo_style)
        + click.style("/_/  |_|\\__,_/\\__/\\____/_/  |_|\\__, /\\___/_/ /_/\\__/", **title_style),
        click.style("      ||        ", **logo_style)
        + click.style("                         /____/", fg="white", bold=True),
        click.style("      ||        ", **logo_style)
        + click.style("Continuous Agent Optimization Platform", fg="cyan", bold=True)
        + click.style(f"   v{version}", fg="cyan", bold=True),
        click.style("      ||        ", **logo_style)
        + click.style("Created by Andrew Huot", dim=True),
        click.style("  " + "-" * 72, dim=True),
    ]
    return "\n".join(lines)


def echo_startup_banner(ctx: click.Context | None) -> None:
    """Print the branded banner only when the active command tree allows it."""
    if banner_enabled(ctx):
        click.echo(render_startup_banner(get_agentlab_version()))

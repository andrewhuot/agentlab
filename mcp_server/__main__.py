"""Module entrypoint for starting the AgentLab MCP server."""
from __future__ import annotations

import argparse

from mcp_server.server import run_http
from mcp_server.server import run_stdio


def main() -> None:
    """Start the MCP server in stdio mode by default, or HTTP when a port is supplied."""
    parser = argparse.ArgumentParser(
        prog="python -m mcp_server",
        description="Start the AgentLab MCP server for stdio or streamable HTTP clients.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host/interface for HTTP mode. Ignored in stdio mode.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Start streamable HTTP mode on this port. If omitted, stdio mode is used.",
    )
    args = parser.parse_args()

    if args.port is None:
        run_stdio()
        return
    run_http(host=args.host, port=args.port)


if __name__ == "__main__":
    main()

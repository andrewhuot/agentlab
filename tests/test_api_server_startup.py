"""Regression tests for importing the full API server."""

from __future__ import annotations

import importlib
import sys


def test_api_server_imports_cleanly() -> None:
    """`api.server` should import without FastAPI route-construction errors."""
    sys.modules.pop("api.server", None)
    sys.modules.pop("api.routes.eval", None)
    sys.modules.pop("api.routes.compare", None)
    sys.modules.pop("api.routes.results", None)

    module = importlib.import_module("api.server")

    assert hasattr(module, "app")


def test_compare_and_results_routes_import_cleanly() -> None:
    """New compare/results routes should import without missing model errors."""
    sys.modules.pop("api.routes.compare", None)
    sys.modules.pop("api.routes.results", None)

    compare_module = importlib.import_module("api.routes.compare")
    results_module = importlib.import_module("api.routes.results")

    assert hasattr(compare_module, "router")
    assert hasattr(results_module, "router")

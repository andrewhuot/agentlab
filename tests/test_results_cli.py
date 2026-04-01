"""CLI tests for structured eval results exploration workflows."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from evals.results_store import EvalResultsStore
from runner import cli
from tests.evals.test_results_store import _make_result_set


@pytest.fixture()
def runner() -> CliRunner:
    """Return a Click CLI runner."""
    return CliRunner()


def test_eval_results_show_and_annotate_latest_run(runner: CliRunner) -> None:
    """`agentlab eval results` should show structured runs and persist annotations."""
    with runner.isolated_filesystem():
        store = EvalResultsStore(db_path=".agentlab/eval_results.db")
        store.save(_make_result_set("run-results-1"))

        show_result = runner.invoke(cli, ["eval", "results", "--failures"])
        assert show_result.exit_code == 0, show_result.output
        assert "Results Explorer — run-results-1" in show_result.output
        assert "case-routing" in show_result.output
        assert "case-orders" not in show_result.output

        annotate_result = runner.invoke(
            cli,
            [
                "eval",
                "results",
                "annotate",
                "case-routing",
                "--run-id",
                "run-results-1",
                "--comment",
                "Manual review says this should pass.",
            ],
        )
        assert annotate_result.exit_code == 0, annotate_result.output

        reloaded = store.get_example("run-results-1", "case-routing")
        assert reloaded is not None
        assert reloaded.annotations[-1].content == "Manual review says this should pass."


def test_eval_results_export_and_diff_commands(runner: CliRunner) -> None:
    """`agentlab eval results export/diff` should surface explorer-friendly artifacts."""
    with runner.isolated_filesystem():
        store = EvalResultsStore(db_path=".agentlab/eval_results.db")
        baseline = _make_result_set("run-baseline")
        candidate = _make_result_set("run-candidate")
        candidate.examples[0].passed = False
        candidate.examples[0].failure_reasons = ["latency regression"]
        candidate.examples[1].passed = True
        candidate.examples[1].failure_reasons = []
        store.save(baseline)
        store.save(candidate)

        export_path = Path("run-candidate.md")
        export_result = runner.invoke(
            cli,
            [
                "eval",
                "results",
                "export",
                "run-candidate",
                "--format",
                "markdown",
                "--output",
                str(export_path),
            ],
        )
        assert export_result.exit_code == 0, export_result.output
        assert export_path.exists()
        assert "# Eval Results: run-candidate" in export_path.read_text(encoding="utf-8")

        diff_result = runner.invoke(
            cli,
            ["eval", "results", "diff", "run-baseline", "run-candidate"],
        )
        assert diff_result.exit_code == 0, diff_result.output
        assert "Run Diff — run-baseline -> run-candidate" in diff_result.output
        assert "case-orders" in diff_result.output
        assert "case-routing" in diff_result.output

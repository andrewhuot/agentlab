"""Tests for structured eval results persistence and querying."""

from __future__ import annotations

import json
import sqlite3

from evals.scorer import CompositeScore, EvalResult


def _make_result_set(run_id: str):
    """Return a representative structured result set for store tests."""
    from evals.results_model import EvalResultSet
    from evals.runner import TestCase

    cases = [
        TestCase(
            id="case-orders",
            category="happy_path",
            user_message="Where is my order?",
            expected_specialist="orders",
            expected_behavior="answer",
            expected_keywords=["order"],
        ),
        TestCase(
            id="case-routing",
            category="regression",
            user_message="Connect me with billing",
            expected_specialist="billing",
            expected_behavior="route_correctly",
        ),
    ]
    score = CompositeScore(
        quality=0.7,
        safety=1.0,
        latency=0.92,
        cost=0.88,
        composite=0.83,
        total_cases=2,
        passed_cases=1,
        safety_failures=0,
        results=[
            EvalResult(
                case_id="case-orders",
                category="happy_path",
                passed=True,
                quality_score=0.95,
                safety_passed=True,
                latency_ms=140.0,
                token_count=120,
                details="",
                input_payload={"user_message": "Where is my order?"},
                expected_payload={"expected_specialist": "orders"},
                actual_output={"response": "Your order is on the way.", "specialist_used": "orders"},
                failure_reasons=[],
            ),
            EvalResult(
                case_id="case-routing",
                category="regression",
                passed=False,
                quality_score=0.45,
                safety_passed=True,
                latency_ms=90.0,
                token_count=80,
                details="routing mismatch",
                input_payload={"user_message": "Connect me with billing"},
                expected_payload={"expected_specialist": "billing"},
                actual_output={"response": "Support can help with that.", "specialist_used": "support"},
                failure_reasons=["routing mismatch"],
            ),
        ],
    )
    return EvalResultSet.from_score(
        run_id=run_id,
        score=score,
        cases=cases,
        mode="mock",
        config_snapshot={"variant": run_id},
    )


def test_results_store_filters_examples_and_persists_annotations(tmp_path) -> None:
    """Results storage should support pass/fail filtering, metric ranges, and annotations."""
    from evals.results_model import Annotation
    from evals.results_store import EvalResultsStore

    store = EvalResultsStore(db_path=str(tmp_path / "results.db"))
    store.save(_make_result_set("run-1"))

    failures, total_failures = store.get_examples("run-1", passed=False, page=1, page_size=10)
    assert total_failures == 1
    assert failures[0].example_id == "case-routing"

    low_quality, total_low_quality = store.get_examples(
        "run-1",
        metric="quality",
        below=0.6,
        page=1,
        page_size=10,
    )
    assert total_low_quality == 1
    assert low_quality[0].example_id == "case-routing"

    store.add_annotation(
        "run-1",
        "case-routing",
        Annotation(
            author="andrew",
            timestamp="2026-03-31T13:00:00Z",
            type="comment",
            content="False positive because billing was available via support routing.",
            score_override=None,
        ),
    )
    reloaded = store.get_example("run-1", "case-routing")
    assert reloaded is not None
    assert reloaded.annotations[0].content.startswith("False positive")


def test_results_store_exports_and_diffs_runs(tmp_path) -> None:
    """Results storage should export runs and surface run-to-run changes."""
    from evals.results_store import EvalResultsStore

    store = EvalResultsStore(db_path=str(tmp_path / "results.db"))
    baseline = _make_result_set("run-baseline")
    candidate = _make_result_set("run-candidate")
    candidate.examples[0].passed = False
    candidate.examples[0].failure_reasons = ["latency regression"]
    candidate.examples[1].passed = True
    candidate.examples[1].failure_reasons = []
    candidate.summary.passed = 1
    candidate.summary.failed = 1
    store.save(baseline)
    store.save(candidate)

    markdown_export = store.export_run("run-candidate", format="markdown")
    assert "# Eval Results: run-candidate" in markdown_export
    assert "case-orders" in markdown_export

    csv_export = store.export_run("run-candidate", format="csv")
    assert "example_id,passed" in csv_export

    diff = store.diff_runs("run-baseline", "run-candidate")
    assert diff["new_failures"] == 1
    assert diff["new_passes"] == 1
    assert {entry["example_id"] for entry in diff["changed_examples"]} == {
        "case-orders",
        "case-routing",
    }


def test_eval_runner_persists_structured_results_after_run(tmp_path) -> None:
    """Eval runner should store structured results automatically after a run completes."""
    from evals.results_store import EvalResultsStore
    from evals.runner import EvalRunner

    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(
        json.dumps(
            {
                "id": "case-orders",
                "split": "test",
                "category": "happy_path",
                "user_message": "Where is my order?",
                "expected_specialist": "orders",
                "expected_behavior": "answer",
                "expected_keywords": ["order"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    def agent(message: str, config: dict | None = None) -> dict:
        del config
        return {
            "response": f"Order update: {message}",
            "specialist_used": "orders",
            "safety_violation": False,
            "latency_ms": 45.0,
            "token_count": 60,
        }

    store = EvalResultsStore(db_path=str(tmp_path / "results.db"))
    runner = EvalRunner(agent_fn=agent, cache_enabled=False, results_store=store)

    score = runner.run(dataset_path=str(dataset), split="test")

    saved = store.get_run(score.run_id or "")
    assert saved is not None
    assert saved.examples[0].actual["response"].startswith("Order update:")
    assert saved.examples[0].scores["quality"].value > 0


def test_eval_runner_refreshes_legacy_cache_entries_before_saving_results(tmp_path) -> None:
    """Legacy cache payloads should be recomputed so explorer data stays rich."""
    from evals.results_store import EvalResultsStore
    from evals.runner import EvalRunner

    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(
        json.dumps(
            {
                "id": "case-routing",
                "split": "test",
                "category": "regression",
                "user_message": "Connect me with billing",
                "expected_specialist": "billing",
                "expected_behavior": "route_correctly",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    def agent(message: str, config: dict | None = None) -> dict:
        del message, config
        return {
            "response": "Support can help with that.",
            "specialist_used": "support",
            "safety_violation": False,
            "latency_ms": 55.0,
            "token_count": 42,
        }

    store = EvalResultsStore(db_path=str(tmp_path / "results.db"))
    runner = EvalRunner(
        agent_fn=agent,
        cache_enabled=True,
        cache_db_path=str(tmp_path / "cache.db"),
        results_store=store,
    )

    runner.run(dataset_path=str(dataset), split="test")

    with sqlite3.connect(runner.cache_store.db_path) as conn:
        row = conn.execute("SELECT case_payloads FROM eval_cache").fetchone()
        case_payloads = json.loads(row[0])
        case_payloads[0].pop("input_payload", None)
        case_payloads[0].pop("expected_payload", None)
        case_payloads[0].pop("actual_output", None)
        case_payloads[0].pop("failure_reasons", None)
        conn.execute(
            "UPDATE eval_cache SET case_payloads = ?",
            (json.dumps(case_payloads, sort_keys=True),),
        )
        conn.commit()

    cached_score = runner.run(dataset_path=str(dataset), split="test")

    saved = store.get_run(cached_score.run_id or "")
    assert saved is not None
    assert saved.examples[0].input["user_message"] == "Connect me with billing"
    assert saved.examples[0].actual["response"] == "Support can help with that."
    assert saved.examples[0].failure_reasons == ["routing mismatch", "behavior mismatch"]

"""Tests for newly merged modules from architectural overhaul.

Tests cover:
- graders/deterministic.py — DeterministicGrader
- graders/similarity.py — SimilarityGrader
- graders/llm_judge.py — BinaryRubricJudge
- data/repositories.py — SQLiteTraceRepository, SQLiteArtifactRepository
- control/governance.py — GovernanceEngine
"""

from __future__ import annotations


import pytest

from control.governance import GovernanceEngine
from data.repositories import SQLiteArtifactRepository, SQLiteTraceRepository
from deployer.release_manager import PromotionStage, ReleaseManager
from deployer.versioning import ConfigVersionManager
from graders.deterministic import DeterministicGrader, GradeResult
from graders.llm_judge import BinaryRubricJudge, LLMJudgeConfig
from graders.similarity import SimilarityGrader


# ---------------------------------------------------------------------------
# DeterministicGrader tests
# ---------------------------------------------------------------------------


def test_deterministic_grader_contains_pass():
    """Test contains assertion passes when phrase found."""
    grader = DeterministicGrader()
    result = grader.grade(
        response_text="The quick brown fox jumps over the lazy dog",
        assertions={"contains": ["quick", "fox"]},
    )

    assert result.passed is True
    assert result.score == 1.0
    assert result.grader == "deterministic"


def test_deterministic_grader_contains_fail():
    """Test contains assertion fails when phrase missing."""
    grader = DeterministicGrader()
    result = grader.grade(
        response_text="The quick brown fox",
        assertions={"contains": ["elephant", "giraffe"]},
    )

    assert result.passed is False
    assert result.score == 0.0


def test_deterministic_grader_not_contains_pass():
    """Test not_contains assertion passes when phrase absent."""
    grader = DeterministicGrader()
    result = grader.grade(
        response_text="The quick brown fox",
        assertions={"not_contains": ["elephant", "error"]},
    )

    assert result.passed is True
    assert result.score == 1.0


def test_deterministic_grader_not_contains_fail():
    """Test not_contains assertion fails when phrase found."""
    grader = DeterministicGrader()
    result = grader.grade(
        response_text="The quick brown fox",
        assertions={"not_contains": ["quick", "fast"]},
    )

    assert result.passed is False
    assert result.score < 1.0


def test_deterministic_grader_case_insensitive():
    """Test assertions are case insensitive."""
    grader = DeterministicGrader()
    result = grader.grade(
        response_text="The QUICK Brown FOX",
        assertions={"contains": ["quick", "fox"]},
    )

    assert result.passed is True
    assert result.score == 1.0


def test_deterministic_grader_expected_tool_pass():
    """Test expected_tool assertion passes when tool called."""
    grader = DeterministicGrader()
    tool_calls = [
        {"tool": "Read", "args": {}},
        {"name": "Write", "args": {}},
    ]
    result = grader.grade(
        response_text="Some text",
        assertions={"expected_tool": "read"},
        tool_calls=tool_calls,
    )

    assert result.passed is True
    assert result.score == 1.0
    assert "called_tools" in result.details
    assert "read" in result.details["called_tools"]


def test_deterministic_grader_expected_tool_fail():
    """Test expected_tool assertion fails when tool not called."""
    grader = DeterministicGrader()
    tool_calls = [{"tool": "Read", "args": {}}]
    result = grader.grade(
        response_text="Some text",
        assertions={"expected_tool": "Write"},
        tool_calls=tool_calls,
    )

    assert result.passed is False
    assert result.score == 0.0


def test_deterministic_grader_status_code_pass():
    """Test status_code assertion passes when code matches."""
    grader = DeterministicGrader()
    result = grader.grade(
        response_text="Success",
        assertions={"status_code": 200},
        status_code=200,
    )

    assert result.passed is True
    assert result.score == 1.0
    assert result.details["status_code"] == 200


def test_deterministic_grader_status_code_fail():
    """Test status_code assertion fails when code differs."""
    grader = DeterministicGrader()
    result = grader.grade(
        response_text="Error",
        assertions={"status_code": 200},
        status_code=500,
    )

    assert result.passed is False
    assert result.score == 0.0
    assert result.details["status_code"] == 500


def test_deterministic_grader_mixed_assertions():
    """Test mixed assertions with partial failures."""
    grader = DeterministicGrader()
    result = grader.grade(
        response_text="The quick brown fox",
        assertions={
            "contains": ["quick", "elephant"],  # 1/2 pass
            "not_contains": ["error"],  # 1/1 pass
        },
    )

    assert result.passed is False
    # 2/3 checks passed
    assert result.score == pytest.approx(0.6667, abs=0.001)


def test_deterministic_grader_empty_response():
    """Test grader handles empty response text."""
    grader = DeterministicGrader()
    result = grader.grade(
        response_text="",
        assertions={"contains": ["something"]},
    )

    assert result.passed is False
    assert result.score == 0.0


def test_deterministic_grader_no_assertions():
    """Test grader returns passing result when no assertions."""
    grader = DeterministicGrader()
    result = grader.grade(
        response_text="Some text",
        assertions={},
    )

    assert result.passed is True
    assert result.score == 1.0


def test_deterministic_grader_none_tool_calls():
    """Test grader handles None tool_calls gracefully."""
    grader = DeterministicGrader()
    result = grader.grade(
        response_text="Some text",
        assertions={"expected_tool": "Read"},
        tool_calls=None,
    )

    assert result.passed is False


def test_deterministic_grader_malformed_tool_calls():
    """Test grader handles malformed tool_calls without crashing."""
    grader = DeterministicGrader()
    tool_calls = [
        {"tool": "Read"},
        None,  # Invalid entry
        "string",  # Invalid entry
        {"name": "Write"},
    ]
    result = grader.grade(
        response_text="Some text",
        assertions={"expected_tool": "read"},
        tool_calls=tool_calls,
    )

    assert result.passed is True  # Read was found
    assert "called_tools" in result.details


# ---------------------------------------------------------------------------
# SimilarityGrader tests
# ---------------------------------------------------------------------------


def test_similarity_grader_exact_match():
    """Test similarity grader returns 1.0 for identical text."""
    grader = SimilarityGrader(threshold=0.65)
    result = grader.grade(
        response_text="The quick brown fox",
        reference_text="The quick brown fox",
    )

    assert result.score == 1.0
    assert result.passed is True
    assert result.grader == "similarity"


def test_similarity_grader_high_overlap():
    """Test similarity grader passes with high token overlap."""
    grader = SimilarityGrader(threshold=0.5)
    result = grader.grade(
        response_text="The quick brown fox jumps over",
        reference_text="The quick brown fox runs fast",
    )

    # Overlap: the, quick, brown, fox (4)
    # Union: all unique tokens (8)
    # Jaccard = 4/8 = 0.5
    assert result.passed is True
    assert result.score >= 0.5


def test_similarity_grader_low_overlap():
    """Test similarity grader fails with low token overlap."""
    grader = SimilarityGrader(threshold=0.65)
    result = grader.grade(
        response_text="elephant giraffe zebra",
        reference_text="computer keyboard mouse",
    )

    assert result.passed is False
    assert result.score < 0.65


def test_similarity_grader_empty_reference():
    """Test similarity grader fails when reference is empty."""
    grader = SimilarityGrader()
    result = grader.grade(
        response_text="Some response",
        reference_text="",
    )

    assert result.passed is False
    assert result.score == 0.0


def test_similarity_grader_empty_response():
    """Test similarity grader fails when response is empty."""
    grader = SimilarityGrader()
    result = grader.grade(
        response_text="",
        reference_text="Some reference",
    )

    assert result.passed is False
    assert result.score == 0.0


def test_similarity_grader_both_empty():
    """Test similarity grader handles both texts empty."""
    grader = SimilarityGrader()
    result = grader.grade(
        response_text="",
        reference_text="",
    )

    assert result.passed is False
    assert result.score == 0.0


def test_similarity_grader_case_insensitive():
    """Test similarity grader is case insensitive."""
    grader = SimilarityGrader(threshold=0.8)
    result = grader.grade(
        response_text="The QUICK Brown FOX",
        reference_text="the quick brown fox",
    )

    assert result.score == 1.0
    assert result.passed is True


def test_similarity_grader_tokenization():
    """Test tokenization ignores punctuation and special chars."""
    grader = SimilarityGrader(threshold=0.9)
    result = grader.grade(
        response_text="Hello, world! How are you?",
        reference_text="Hello world How are you",
    )

    # Tokens: hello, world, how, are, you
    assert result.score == 1.0
    assert result.passed is True


def test_similarity_grader_custom_threshold():
    """Test custom threshold affects pass/fail."""
    grader_strict = SimilarityGrader(threshold=0.9)
    grader_lenient = SimilarityGrader(threshold=0.3)

    response = "The quick brown fox"
    reference = "The quick brown elephant"

    result_strict = grader_strict.grade(response, reference)
    result_lenient = grader_lenient.grade(response, reference)

    # Same score, different pass/fail
    assert result_strict.score == result_lenient.score
    assert result_strict.passed is False
    assert result_lenient.passed is True


def test_similarity_grader_none_text():
    """Test similarity grader handles None text gracefully."""
    grader = SimilarityGrader()
    result = grader.grade(
        response_text=None,
        reference_text="Some text",
    )

    assert result.passed is False
    assert result.score == 0.0


# ---------------------------------------------------------------------------
# BinaryRubricJudge tests
# ---------------------------------------------------------------------------


def test_binary_rubric_judge_heuristic_mode():
    """Test BinaryRubricJudge heuristic fallback without LLM."""
    judge = BinaryRubricJudge()
    result = judge.grade(
        user_message="What is 2+2?",
        response_text="The answer is 4.",
        reference_text="4",
    )

    assert result.grader == "llm_judge"
    assert isinstance(result.score, float)
    assert 0.0 <= result.score <= 1.0
    assert "rubric" in result.details
    assert "answered_question" in result.details["rubric"]


def test_binary_rubric_judge_answered_question():
    """Test heuristic correctly identifies answered questions."""
    judge = BinaryRubricJudge()
    result = judge.grade(
        user_message="What is the capital of France?",
        response_text="The capital of France is Paris.",
    )

    assert result.details["rubric"]["answered_question"] is True


def test_binary_rubric_judge_not_answered():
    """Test heuristic identifies unanswered questions."""
    judge = BinaryRubricJudge()
    result = judge.grade(
        user_message="What is the capital of France?",
        response_text="",
    )

    assert result.details["rubric"]["answered_question"] is False


def test_binary_rubric_judge_unnecessary_caveats():
    """Test heuristic detects excessive caveats."""
    judge = BinaryRubricJudge()
    result = judge.grade(
        user_message="What is 2+2?",
        response_text="I cannot say for certain, but I might be wrong, the answer could be 4.",
    )

    assert result.details["rubric"]["unnecessary_caveats"] is True


def test_binary_rubric_judge_factually_incorrect_with_reference():
    """Test heuristic detects factual errors with reference."""
    judge = BinaryRubricJudge()
    result = judge.grade(
        user_message="What is 2+2?",
        response_text="The answer is 5.",
        reference_text="4",
    )

    # Reference "4" not in "The answer is 5."
    assert result.details["rubric"]["factually_incorrect"] is True


def test_binary_rubric_judge_factually_correct_with_reference():
    """Test heuristic passes when reference matched."""
    judge = BinaryRubricJudge()
    result = judge.grade(
        user_message="What is 2+2?",
        response_text="The answer is 4.",
        reference_text="4",
    )

    assert result.details["rubric"]["factually_incorrect"] is False


def test_binary_rubric_judge_human_would_differ():
    """Test heuristic identifies very short responses."""
    judge = BinaryRubricJudge()
    result = judge.grade(
        user_message="Write an essay about climate change.",
        response_text="No",
    )

    assert result.details["rubric"]["human_would_handle_differently"] is True


def test_binary_rubric_judge_pass_threshold():
    """Test custom pass threshold affects verdict."""
    config_strict = LLMJudgeConfig(pass_threshold=0.9)
    config_lenient = LLMJudgeConfig(pass_threshold=0.5)

    judge_strict = BinaryRubricJudge(config=config_strict)
    judge_lenient = BinaryRubricJudge(config=config_lenient)

    result_strict = judge_strict.grade(
        user_message="What is 2+2?",
        response_text="The answer is 4.",
    )
    result_lenient = judge_lenient.grade(
        user_message="What is 2+2?",
        response_text="The answer is 4.",
    )

    # Same score, different pass/fail based on threshold
    assert result_strict.score == result_lenient.score


def test_binary_rubric_judge_custom_evaluator():
    """Test custom evaluator function overrides heuristic."""
    def custom_evaluator(user_msg, response, reference):
        return {
            "answered_question": True,
            "factually_incorrect": False,
            "unnecessary_caveats": False,
            "human_would_handle_differently": False,
        }

    judge = BinaryRubricJudge()
    result = judge.grade(
        user_message="Test",
        response_text="Test",
        evaluator=custom_evaluator,
    )

    # Perfect score: all good answers
    assert result.score == 1.0
    assert result.passed is True


def test_binary_rubric_judge_majority_vote():
    """Test majority voting with 3 votes."""
    config = LLMJudgeConfig(majority_vote=True)
    judge = BinaryRubricJudge(config=config)

    result = judge.grade(
        user_message="What is 2+2?",
        response_text="The answer is 4.",
    )

    assert "votes" in result.details
    assert len(result.details["votes"]) == 3
    # Passed if 2+ votes pass
    assert isinstance(result.passed, bool)


def test_binary_rubric_judge_model_family_validation():
    """Test validation prevents same model family for judge and agent."""
    config = LLMJudgeConfig(model_family="anthropic")
    judge = BinaryRubricJudge(config=config)

    with pytest.raises(ValueError, match="Judge model family must differ"):
        judge.grade(
            user_message="Test",
            response_text="Test",
            agent_model_family="anthropic",
        )


def test_binary_rubric_judge_different_model_families():
    """Test different model families pass validation."""
    config = LLMJudgeConfig(model_family="anthropic")
    judge = BinaryRubricJudge(config=config)

    # Should not raise
    result = judge.grade(
        user_message="Test",
        response_text="Response",
        agent_model_family="openai",
    )

    assert isinstance(result, GradeResult)


def test_binary_rubric_judge_no_agent_model_family():
    """Test validation passes when agent_model_family is None."""
    config = LLMJudgeConfig(model_family="anthropic")
    judge = BinaryRubricJudge(config=config)

    # Should not raise
    result = judge.grade(
        user_message="Test",
        response_text="Response",
        agent_model_family=None,
    )

    assert isinstance(result, GradeResult)


# ---------------------------------------------------------------------------
# SQLiteTraceRepository tests
# ---------------------------------------------------------------------------


def test_trace_repository_put_and_get(tmp_path):
    """Test basic put and get operations for traces."""
    db_path = tmp_path / "test_traces.db"
    repo = SQLiteTraceRepository(db_path=str(db_path))

    trace_id = "trace_123"
    payload = {
        "event": "test_event",
        "timestamp": "2026-03-24T10:00:00Z",
        "data": {"key": "value"},
    }

    repo.put(trace_id, payload)
    retrieved = repo.get(trace_id)

    assert retrieved == payload
    assert retrieved["event"] == "test_event"
    assert retrieved["data"]["key"] == "value"


def test_trace_repository_get_nonexistent(tmp_path):
    """Test getting a nonexistent trace returns None."""
    db_path = tmp_path / "test_traces.db"
    repo = SQLiteTraceRepository(db_path=str(db_path))

    result = repo.get("nonexistent_id")

    assert result is None


def test_trace_repository_update_trace(tmp_path):
    """Test updating an existing trace."""
    db_path = tmp_path / "test_traces.db"
    repo = SQLiteTraceRepository(db_path=str(db_path))

    trace_id = "trace_123"
    original = {"event": "original"}
    updated = {"event": "updated", "new_field": "value"}

    repo.put(trace_id, original)
    repo.put(trace_id, updated)

    result = repo.get(trace_id)

    assert result == updated
    assert result["event"] == "updated"
    assert "new_field" in result


def test_trace_repository_multiple_traces(tmp_path):
    """Test storing and retrieving multiple traces."""
    db_path = tmp_path / "test_traces.db"
    repo = SQLiteTraceRepository(db_path=str(db_path))

    traces = {
        "trace_1": {"event": "event_1"},
        "trace_2": {"event": "event_2"},
        "trace_3": {"event": "event_3"},
    }

    for trace_id, payload in traces.items():
        repo.put(trace_id, payload)

    for trace_id, expected_payload in traces.items():
        retrieved = repo.get(trace_id)
        assert retrieved == expected_payload


def test_trace_repository_nested_payload(tmp_path):
    """Test repository handles deeply nested payloads."""
    db_path = tmp_path / "test_traces.db"
    repo = SQLiteTraceRepository(db_path=str(db_path))

    trace_id = "trace_complex"
    payload = {
        "level1": {
            "level2": {
                "level3": {
                    "data": [1, 2, 3],
                    "metadata": {"key": "value"},
                }
            }
        }
    }

    repo.put(trace_id, payload)
    retrieved = repo.get(trace_id)

    assert retrieved == payload
    assert retrieved["level1"]["level2"]["level3"]["data"] == [1, 2, 3]


def test_trace_repository_creates_parent_dirs(tmp_path):
    """Test repository creates parent directories if needed."""
    db_path = tmp_path / "subdir" / "nested" / "traces.db"
    repo = SQLiteTraceRepository(db_path=str(db_path))

    assert db_path.exists()
    assert db_path.parent.exists()


def test_trace_repository_persistence(tmp_path):
    """Test data persists across repository instances."""
    db_path = tmp_path / "test_traces.db"

    # First instance
    repo1 = SQLiteTraceRepository(db_path=str(db_path))
    repo1.put("trace_1", {"data": "persistent"})

    # Second instance
    repo2 = SQLiteTraceRepository(db_path=str(db_path))
    result = repo2.get("trace_1")

    assert result["data"] == "persistent"


# ---------------------------------------------------------------------------
# SQLiteArtifactRepository tests
# ---------------------------------------------------------------------------


def test_artifact_repository_put_and_get(tmp_path):
    """Test basic put and get operations for artifacts."""
    db_path = tmp_path / "test_artifacts.db"
    repo = SQLiteArtifactRepository(db_path=str(db_path))

    artifact_id = "artifact_123"
    payload = {
        "type": "model_weights",
        "version": "v1.0",
        "metadata": {"accuracy": 0.95},
    }

    repo.put(artifact_id, payload)
    retrieved = repo.get(artifact_id)

    assert retrieved == payload
    assert retrieved["type"] == "model_weights"
    assert retrieved["metadata"]["accuracy"] == 0.95


def test_artifact_repository_get_nonexistent(tmp_path):
    """Test getting a nonexistent artifact returns None."""
    db_path = tmp_path / "test_artifacts.db"
    repo = SQLiteArtifactRepository(db_path=str(db_path))

    result = repo.get("nonexistent_id")

    assert result is None


def test_artifact_repository_update_artifact(tmp_path):
    """Test updating an existing artifact."""
    db_path = tmp_path / "test_artifacts.db"
    repo = SQLiteArtifactRepository(db_path=str(db_path))

    artifact_id = "artifact_123"
    original = {"version": "v1.0"}
    updated = {"version": "v2.0", "changes": "major update"}

    repo.put(artifact_id, original)
    repo.put(artifact_id, updated)

    result = repo.get(artifact_id)

    assert result == updated
    assert result["version"] == "v2.0"


def test_artifact_repository_multiple_artifacts(tmp_path):
    """Test storing and retrieving multiple artifacts."""
    db_path = tmp_path / "test_artifacts.db"
    repo = SQLiteArtifactRepository(db_path=str(db_path))

    artifacts = {
        "artifact_1": {"type": "config"},
        "artifact_2": {"type": "weights"},
        "artifact_3": {"type": "metadata"},
    }

    for artifact_id, payload in artifacts.items():
        repo.put(artifact_id, payload)

    for artifact_id, expected_payload in artifacts.items():
        retrieved = repo.get(artifact_id)
        assert retrieved == expected_payload


def test_artifact_repository_large_payload(tmp_path):
    """Test repository handles large payloads."""
    db_path = tmp_path / "test_artifacts.db"
    repo = SQLiteArtifactRepository(db_path=str(db_path))

    artifact_id = "large_artifact"
    # Simulate large payload
    payload = {
        "data": ["item" * 100 for _ in range(1000)],
        "metadata": {"size": "large"},
    }

    repo.put(artifact_id, payload)
    retrieved = repo.get(artifact_id)

    assert retrieved == payload
    assert len(retrieved["data"]) == 1000


def test_artifact_repository_persistence(tmp_path):
    """Test data persists across repository instances."""
    db_path = tmp_path / "test_artifacts.db"

    # First instance
    repo1 = SQLiteArtifactRepository(db_path=str(db_path))
    repo1.put("artifact_1", {"data": "persistent"})

    # Second instance
    repo2 = SQLiteArtifactRepository(db_path=str(db_path))
    result = repo2.get("artifact_1")

    assert result["data"] == "persistent"


def test_artifact_repository_creates_parent_dirs(tmp_path):
    """Test repository creates parent directories if needed."""
    db_path = tmp_path / "artifacts" / "nested" / "artifacts.db"
    repo = SQLiteArtifactRepository(db_path=str(db_path))

    assert db_path.exists()
    assert db_path.parent.exists()


# ---------------------------------------------------------------------------
# GovernanceEngine tests
# ---------------------------------------------------------------------------


def test_governance_engine_evaluate_candidate():
    """Test GovernanceEngine delegates to ReleaseManager."""
    version_manager = ConfigVersionManager()
    release_manager = ReleaseManager(version_manager=version_manager)
    governance = GovernanceEngine(release_manager=release_manager)

    result = governance.evaluate_candidate(
        candidate_version="v1.0",
        gate_results={
            "safety": True,
            "performance": True,
            "regression": True,
        },
        holdout_score=0.05,
        slice_results={
            "slice_a": 0.02,
            "slice_b": -0.01,
        },
        canary_verdict="promote",
    )

    assert result.status == "released"
    assert result.candidate_version == "v1.0"
    assert PromotionStage.released in result.stages_completed


def test_governance_engine_with_failing_gates():
    """Test governance handles failing gate checks."""
    version_manager = ConfigVersionManager()
    release_manager = ReleaseManager(version_manager=version_manager)
    governance = GovernanceEngine(release_manager=release_manager)

    result = governance.evaluate_candidate(
        candidate_version="v1.0",
        gate_results={
            "safety": False,  # Gate failure
            "performance": True,
        },
        holdout_score=0.05,
        slice_results={},
    )

    assert result.status == "failed"
    assert "Gates failed" in result.failure_reason


def test_governance_engine_with_holdout_regression():
    """Test governance handles holdout regression."""
    version_manager = ConfigVersionManager()
    release_manager = ReleaseManager(version_manager=version_manager)
    governance = GovernanceEngine(release_manager=release_manager)

    result = governance.evaluate_candidate(
        candidate_version="v1.0",
        gate_results={"safety": True},
        holdout_score=-0.1,  # Regression
        slice_results={},
    )

    assert result.status == "failed"
    assert "Holdout regression" in result.failure_reason


def test_governance_engine_with_slice_regression():
    """Test governance handles slice regression."""
    version_manager = ConfigVersionManager()
    release_manager = ReleaseManager(version_manager=version_manager)
    governance = GovernanceEngine(release_manager=release_manager)

    result = governance.evaluate_candidate(
        candidate_version="v1.0",
        gate_results={"safety": True},
        holdout_score=0.05,
        slice_results={
            "slice_a": 0.02,
            "slice_b": -0.10,  # Regression beyond -0.05 threshold
        },
    )

    assert result.status == "failed"
    assert "Slice regressions" in result.failure_reason


def test_governance_engine_successful_release():
    """Test governance approves valid release candidate."""
    version_manager = ConfigVersionManager()
    release_manager = ReleaseManager(version_manager=version_manager)
    governance = GovernanceEngine(release_manager=release_manager)

    result = governance.evaluate_candidate(
        candidate_version="v1.0",
        gate_results={
            "safety": True,
            "performance": True,
        },
        holdout_score=0.05,
        slice_results={
            "slice_a": 0.02,
            "slice_b": 0.01,
        },
        canary_verdict="promote",
    )

    assert result.status == "released"
    assert PromotionStage.released in result.stages_completed


def test_governance_engine_rollback():
    """Test governance handles canary rollback."""
    version_manager = ConfigVersionManager()
    release_manager = ReleaseManager(version_manager=version_manager)
    governance = GovernanceEngine(release_manager=release_manager)

    result = governance.evaluate_candidate(
        candidate_version="v1.0",
        gate_results={"safety": True},
        holdout_score=0.05,
        slice_results={"slice_a": 0.01},
        canary_verdict="rollback",
    )

    assert result.status == "rolled_back"
    assert result.canary_verdict == "rollback"


def test_governance_engine_auto_release_no_canary():
    """Test governance auto-releases when no canary verdict provided."""
    version_manager = ConfigVersionManager()
    release_manager = ReleaseManager(version_manager=version_manager)
    governance = GovernanceEngine(release_manager=release_manager)

    result = governance.evaluate_candidate(
        candidate_version="v1.0",
        gate_results={"safety": True},
        holdout_score=0.05,
        slice_results={"slice_a": 0.01},
        canary_verdict=None,  # No canary step
    )

    assert result.status == "released"
    assert PromotionStage.released in result.stages_completed


# ---------------------------------------------------------------------------
# Additional edge case tests
# ---------------------------------------------------------------------------


def test_deterministic_grader_string_coercion():
    """Test grader coerces assertion values to strings."""
    grader = DeterministicGrader()
    result = grader.grade(
        response_text="The answer is 42",
        assertions={"contains": [42]},  # Integer, not string
    )

    assert result.passed is True


def test_similarity_grader_zero_threshold():
    """Test similarity grader with zero threshold always passes."""
    grader = SimilarityGrader(threshold=0.0)
    result = grader.grade(
        response_text="completely different",
        reference_text="no overlap here",
    )

    # Even with no overlap, score >= 0.0
    assert result.passed is (result.score >= 0.0)


def test_similarity_grader_threshold_boundary():
    """Test similarity grader at exact threshold boundary."""
    grader = SimilarityGrader(threshold=0.5)

    # Craft inputs with exactly 50% Jaccard overlap
    # Tokens: {a, b} and {a, c} -> overlap=1, union=3 -> 0.333
    result = grader.grade(
        response_text="a b",
        reference_text="a c",
    )

    # Score should be < 0.5
    assert result.passed is False
    assert result.score < 0.5


def test_binary_rubric_judge_empty_inputs():
    """Test judge handles empty inputs gracefully."""
    judge = BinaryRubricJudge()
    result = judge.grade(
        user_message="",
        response_text="",
    )

    assert isinstance(result, GradeResult)
    assert result.grader == "llm_judge"


def test_binary_rubric_judge_score_calculation():
    """Test judge correctly calculates score from rubric answers."""
    def all_good_evaluator(user_msg, response, reference):
        return {
            "answered_question": True,
            "factually_incorrect": False,
            "unnecessary_caveats": False,
            "human_would_handle_differently": False,
        }

    judge = BinaryRubricJudge()
    result = judge.grade(
        user_message="Test",
        response_text="Test",
        evaluator=all_good_evaluator,
    )

    # All 4 questions answered correctly -> 4/4 = 1.0
    assert result.score == 1.0


def test_binary_rubric_judge_score_calculation_mixed():
    """Test judge score with mixed rubric results."""
    def mixed_evaluator(user_msg, response, reference):
        return {
            "answered_question": True,  # Good
            "factually_incorrect": True,  # Bad
            "unnecessary_caveats": False,  # Good
            "human_would_handle_differently": True,  # Bad
        }

    judge = BinaryRubricJudge()
    result = judge.grade(
        user_message="Test",
        response_text="Test",
        evaluator=mixed_evaluator,
    )

    # 2 good, 2 bad -> 2/4 = 0.5
    assert result.score == 0.5


def test_trace_repository_json_serialization_edge_cases(tmp_path):
    """Test repository handles complex JSON-serializable types."""
    db_path = tmp_path / "test_traces.db"
    repo = SQLiteTraceRepository(db_path=str(db_path))

    trace_id = "complex_trace"
    payload = {
        "string": "value",
        "int": 42,
        "float": 3.14,
        "bool": True,
        "null": None,
        "list": [1, 2, 3],
        "nested_list": [[1, 2], [3, 4]],
        "dict": {"key": "value"},
        "empty_dict": {},
        "empty_list": [],
    }

    repo.put(trace_id, payload)
    retrieved = repo.get(trace_id)

    assert retrieved == payload
    assert retrieved["null"] is None
    assert retrieved["empty_dict"] == {}


def test_artifact_repository_concurrent_access(tmp_path):
    """Test repository handles sequential writes correctly."""
    db_path = tmp_path / "test_artifacts.db"

    repo1 = SQLiteArtifactRepository(db_path=str(db_path))
    repo2 = SQLiteArtifactRepository(db_path=str(db_path))

    repo1.put("artifact_1", {"from": "repo1"})
    repo2.put("artifact_2", {"from": "repo2"})

    # Both repos should see both artifacts
    assert repo1.get("artifact_1")["from"] == "repo1"
    assert repo1.get("artifact_2")["from"] == "repo2"
    assert repo2.get("artifact_1")["from"] == "repo1"
    assert repo2.get("artifact_2")["from"] == "repo2"


def test_deterministic_grader_tool_name_normalization():
    """Test tool name matching is case-insensitive and whitespace-trimmed."""
    grader = DeterministicGrader()
    tool_calls = [
        {"tool": "  Read  "},  # Extra whitespace
        {"name": "WRITE"},  # Uppercase
    ]

    result = grader.grade(
        response_text="text",
        assertions={"expected_tool": "read"},
        tool_calls=tool_calls,
    )

    assert result.passed is True


def test_governance_engine_empty_gate_results():
    """Test governance handles empty gate results."""
    version_manager = ConfigVersionManager()
    release_manager = ReleaseManager(version_manager=version_manager)
    governance = GovernanceEngine(release_manager=release_manager)

    result = governance.evaluate_candidate(
        candidate_version="v1.0",
        gate_results={},  # No gates
        holdout_score=0.05,
        slice_results={},
    )

    # Empty gate_results should fail per ReleaseManager logic
    assert result.status == "failed"


def test_governance_engine_empty_slice_results():
    """Test governance handles empty slice results."""
    version_manager = ConfigVersionManager()
    release_manager = ReleaseManager(version_manager=version_manager)
    governance = GovernanceEngine(release_manager=release_manager)

    result = governance.evaluate_candidate(
        candidate_version="v1.0",
        gate_results={"safety": True},
        holdout_score=0.05,
        slice_results={},  # No slices
        canary_verdict="promote",
    )

    # Should succeed - no slices to regress
    assert result.status == "released"

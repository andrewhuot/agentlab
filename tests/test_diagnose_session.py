"""Tests for DiagnoseSession (optimizer.diagnose_session)."""

from __future__ import annotations

from unittest.mock import MagicMock


from optimizer.diagnose_session import DiagnoseCluster, DiagnoseSession


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _session(**kwargs) -> DiagnoseSession:
    """Return a fresh DiagnoseSession with no dependencies unless overridden."""
    return DiagnoseSession(**kwargs)


def _mock_observer(failure_buckets: dict[str, int], total_conversations: int = 100):
    """Build a minimal mock observer that returns a HealthReport-like object."""
    metrics = MagicMock()
    metrics.total_conversations = total_conversations

    report = MagicMock()
    report.failure_buckets = failure_buckets
    report.metrics = metrics

    observer = MagicMock()
    observer.observe.return_value = report
    return observer


# ---------------------------------------------------------------------------
# TestDiagnoseSession
# ---------------------------------------------------------------------------

class TestDiagnoseSession:

    # ------------------------------------------------------------------
    # start()
    # ------------------------------------------------------------------

    def test_start_creates_clusters_without_observer(self):
        """Mock mode: two default clusters created when observer is None."""
        s = _session()
        summary = s.start()

        assert len(s.clusters) == 2
        types = {c.failure_type for c in s.clusters}
        assert "routing_error" in types
        assert "unhelpful_response" in types
        assert "AgentLab Diagnosis" in summary

    def test_start_focuses_first_cluster(self):
        """After start(), focused_cluster is set to the highest-count cluster."""
        s = _session()
        s.start()

        assert s.focused_cluster is not None
        # First cluster should be the one with the highest count.
        assert s.focused_cluster is s.clusters[0]
        assert s.focused_index == 0

    def test_start_with_observer_builds_from_failure_buckets(self):
        """When an observer is provided its failure_buckets become clusters."""
        observer = _mock_observer(
            {"tool_error": 20, "routing_mismatch": 5},
            total_conversations=200,
        )
        s = _session(observer=observer)
        s.start()

        assert len(s.clusters) == 2
        # Clusters sorted by count descending — tool_error leads.
        assert s.clusters[0].failure_type == "tool_error"
        assert s.clusters[0].count == 20
        assert abs(s.clusters[0].impact_score - 0.10) < 1e-9

    def test_start_observer_falls_back_to_mock_on_empty_buckets(self):
        """Empty failure_buckets from observer triggers mock fallback."""
        observer = _mock_observer({})
        s = _session(observer=observer)
        s.start()

        assert len(s.clusters) == 2  # mock clusters

    def test_start_observer_exception_falls_back_to_mock(self):
        """If observer.observe() raises, mock clusters are used."""
        observer = MagicMock()
        observer.observe.side_effect = RuntimeError("db offline")
        s = _session(observer=observer)
        s.start()

        assert len(s.clusters) == 2

    def test_start_summary_lists_all_clusters(self):
        """Start summary mentions every cluster failure type."""
        s = _session()
        summary = s.start()

        for c in s.clusters:
            assert c.failure_type in summary

    # ------------------------------------------------------------------
    # _classify_input()
    # ------------------------------------------------------------------

    def test_classify_input_drill_down_bare_number(self):
        s = _session()
        assert s._classify_input("1") == "drill_down"
        assert s._classify_input("cluster 2") == "drill_down"
        assert s._classify_input("#3") == "drill_down"

    def test_classify_input_drill_down_keywords(self):
        s = _session()
        assert s._classify_input("tell me more") == "drill_down"
        assert s._classify_input("details please") == "drill_down"

    def test_classify_input_fix(self):
        s = _session()
        assert s._classify_input("fix this") == "fix"
        assert s._classify_input("resolve the issue") == "fix"

    def test_classify_input_apply(self):
        s = _session()
        assert s._classify_input("apply") == "apply"
        assert s._classify_input("yes") == "apply"
        assert s._classify_input("ship it") == "apply"

    def test_classify_input_next(self):
        s = _session()
        assert s._classify_input("next") == "next"
        assert s._classify_input("move on") == "next"

    def test_classify_input_skip(self):
        s = _session()
        assert s._classify_input("skip") == "skip"
        assert s._classify_input("ignore this one") == "skip"

    def test_classify_input_summary(self):
        s = _session()
        assert s._classify_input("summary") == "summary"
        assert s._classify_input("status") == "summary"

    def test_classify_input_quit(self):
        s = _session()
        assert s._classify_input("quit") == "quit"
        assert s._classify_input("exit") == "quit"
        assert s._classify_input("done") == "quit"

    def test_classify_input_unknown(self):
        s = _session()
        assert s._classify_input("what is the meaning of life") == "unknown"
        assert s._classify_input("") == "unknown"

    # ------------------------------------------------------------------
    # handle_input() — individual intent handlers
    # ------------------------------------------------------------------

    def test_handle_drill_down_by_number(self):
        s = _session()
        s.start()
        response = s.handle_input("cluster 2")

        assert s.focused_index == 1
        assert s.focused_cluster is s.clusters[1]
        assert "## Cluster:" in response
        assert s.clusters[1].failure_type in response

    def test_handle_drill_down_no_clusters(self):
        s = _session()
        # Don't start — no clusters loaded.
        response = s.handle_input("cluster 1")
        assert "No clusters available" in response

    def test_handle_show_examples_no_cluster(self):
        s = _session()
        response = s.handle_input("show examples")
        assert "No cluster selected" in response

    def test_handle_show_examples_with_example_ids(self):
        s = _session()
        s.start()
        s.focused_cluster.example_ids = ["conv-abc", "conv-def"]
        response = s.handle_input("show examples")
        assert "conv-abc" in response

    def test_handle_show_examples_no_example_ids(self):
        s = _session()
        s.start()
        # Default mock clusters have no example_ids.
        response = s.handle_input("show examples")
        assert "No example conversations available" in response

    def test_handle_fix_generates_proposal(self):
        s = _session()
        s.start()
        response = s.handle_input("fix")

        assert s.pending_change is not None
        assert "Proposed fix" in response
        assert "apply" in response.lower()

    def test_handle_fix_no_cluster(self):
        s = _session()
        response = s.handle_input("fix")
        assert "No cluster selected" in response

    def test_handle_apply_clears_pending(self):
        s = _session()
        s.start()
        s.handle_input("fix")
        assert s.pending_change is not None

        response = s.handle_input("apply")
        assert s.pending_change is None
        assert "Applied" in response

    def test_handle_apply_without_pending(self):
        s = _session()
        s.start()
        response = s.handle_input("apply")
        assert "No pending fix" in response

    def test_handle_next_advances_index(self):
        s = _session()
        s.start()
        assert s.focused_index == 0

        response = s.handle_input("next")
        assert s.focused_index == 1
        assert "Next issue" in response

    def test_handle_next_past_end(self):
        s = _session()
        s.start()
        # Exhaust clusters.
        for _ in s.clusters:
            response = s.handle_input("next")
        assert "No more clusters" in response

    def test_handle_skip_advances_index(self):
        s = _session()
        s.start()
        s.handle_input("skip")
        assert s.focused_index == 1

    def test_handle_summary(self):
        s = _session()
        s.start()
        response = s.handle_input("summary")

        assert "## Diagnosis Summary" in response
        assert s.session_id in response
        for c in s.clusters:
            assert c.failure_type in response

    def test_handle_summary_empty(self):
        s = _session()
        # No clusters.
        response = s.handle_input("summary")
        assert "healthy" in response.lower() or "No issues" in response

    def test_handle_quit(self):
        s = _session()
        response = s.handle_input("quit")
        assert "Session ended" in response or "Goodbye" in response

    def test_handle_unknown(self):
        s = _session()
        response = s.handle_input("what colour is the sky")
        assert "didn't understand" in response.lower() or "cluster N" in response

    # ------------------------------------------------------------------
    # to_dict()
    # ------------------------------------------------------------------

    def test_session_to_dict(self):
        s = _session()
        s.start()
        d = s.to_dict()

        assert d["session_id"] == s.session_id
        assert isinstance(d["clusters"], list)
        assert len(d["clusters"]) == len(s.clusters)
        assert d["focused_cluster"] is not None
        assert d["has_pending_change"] is False
        assert isinstance(d["history"], list)

    def test_session_to_dict_with_pending_change(self):
        s = _session()
        s.start()
        s.handle_input("fix")
        d = s.to_dict()
        assert d["has_pending_change"] is True

    # ------------------------------------------------------------------
    # Full conversation flow
    # ------------------------------------------------------------------

    def test_full_conversation_flow(self):
        """start → drill down → fix → apply → next → quit."""
        s = _session()
        summary = s.start()
        assert "AgentLab Diagnosis" in summary
        assert len(s.clusters) > 0

        # Drill into cluster 1
        r1 = s.handle_input("cluster 1")
        assert "## Cluster:" in r1
        assert s.focused_index == 0

        # Fix it
        r2 = s.handle_input("fix")
        assert "Proposed fix" in r2
        assert s.pending_change is not None

        # Apply
        r3 = s.handle_input("apply")
        assert "Applied" in r3
        assert s.pending_change is None

        # Move to next
        r4 = s.handle_input("next")
        assert s.focused_index == 1

        # Quit
        r5 = s.handle_input("quit")
        assert "Goodbye" in r5 or "Session ended" in r5

        # History should have recorded all turns.
        user_turns = [h for h in s.history if h["role"] == "user"]
        assert len(user_turns) == 5

    # ------------------------------------------------------------------
    # DiagnoseCluster.to_dict()
    # ------------------------------------------------------------------

    def test_cluster_to_dict_fields(self):
        c = DiagnoseCluster(
            cluster_id="abc123",
            failure_type="routing_error",
            count=7,
            impact_score=0.07,
            description="Test description",
            example_ids=["id-1"],
            trend="rising",
        )
        d = c.to_dict()
        assert d["cluster_id"] == "abc123"
        assert d["failure_type"] == "routing_error"
        assert d["count"] == 7
        assert d["impact_score"] == 0.07
        assert d["description"] == "Test description"
        assert d["example_ids"] == ["id-1"]
        assert d["trend"] == "rising"

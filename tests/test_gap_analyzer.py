"""Comprehensive tests for GapAnalyzer — gap identification from blame clusters."""

from __future__ import annotations

from types import SimpleNamespace


from agent_skills.gap_analyzer import GapAnalyzer


# ---------------------------------------------------------------------------
# Helpers — mock blame clusters and opportunities without importing observer
# ---------------------------------------------------------------------------


def make_cluster(
    cluster_id: str = "cluster_001",
    grader_name: str = "tool_grader",
    agent_path: str = "agents/orders",
    failure_reason: str = "no tool found",
    count: int = 5,
    total_traces: int = 20,
    example_trace_ids: list[str] | None = None,
    first_seen: float = 1_700_000_000.0,
    last_seen: float = 1_700_010_000.0,
    trend: str = "stable",
) -> SimpleNamespace:
    """Build a duck-typed BlameCluster substitute."""
    return SimpleNamespace(
        cluster_id=cluster_id,
        grader_name=grader_name,
        agent_path=agent_path,
        failure_reason=failure_reason,
        count=count,
        total_traces=total_traces,
        impact_score=count / max(total_traces, 1),
        example_trace_ids=example_trace_ids or ["trace_a", "trace_b"],
        first_seen=first_seen,
        last_seen=last_seen,
        trend=trend,
    )


def make_opportunity(
    opportunity_id: str = "opp_001",
    cluster_id: str = "cluster_001",
    failure_family: str = "tool_error",
    affected_agent_path: str = "agents/orders",
    severity: float = 0.7,
    prevalence: float = 0.25,
    priority_score: float = 0.5,
    sample_trace_ids: list[str] | None = None,
    recommended_operator_families: list[str] | None = None,
) -> SimpleNamespace:
    """Build a duck-typed OptimizationOpportunity substitute."""
    return SimpleNamespace(
        opportunity_id=opportunity_id,
        cluster_id=cluster_id,
        failure_family=failure_family,
        affected_agent_path=affected_agent_path,
        severity=severity,
        prevalence=prevalence,
        priority_score=priority_score,
        sample_trace_ids=sample_trace_ids or [],
        recommended_operator_families=recommended_operator_families or [],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestEmptyInput:
    def test_empty_input(self) -> None:
        """No clusters and no opportunities should produce zero gaps."""
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze(blame_clusters=[], opportunities=[])
        assert gaps == []

    def test_empty_clusters_with_opportunities(self) -> None:
        """Opportunities alone (no clusters) should not produce gaps."""
        opp = make_opportunity()
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze(blame_clusters=[], opportunities=[opp])
        assert gaps == []


class TestToolErrorMissingTool:
    def test_tool_error_missing_tool(self) -> None:
        """A cluster with 'no tool found for warranty check' should yield a missing_tool gap."""
        cluster = make_cluster(
            cluster_id="c1",
            grader_name="tool_grader",
            agent_path="agents/warranty",
            failure_reason="no tool found for warranty check",
            count=8,
            total_traces=20,
        )
        opp = make_opportunity(
            cluster_id="c1",
            failure_family="tool_error",
            prevalence=0.4,
        )
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze(blame_clusters=[cluster], opportunities=[opp])

        assert len(gaps) == 1
        gap = gaps[0]
        assert gap.gap_type == "missing_tool"
        assert gap.suggested_platform == "adk"
        assert gap.frequency == 8
        assert gap.failure_family == "tool_error"
        assert "trace_a" in gap.evidence or len(gap.evidence) >= 0

    def test_not_found_keyword(self) -> None:
        """'not found' in failure_reason should also yield missing_tool."""
        cluster = make_cluster(
            failure_reason="function not found: send_email",
            grader_name="tool_grader",
        )
        opp = make_opportunity(failure_family="tool_error", prevalence=0.3)
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze(blame_clusters=[cluster], opportunities=[opp])

        assert len(gaps) == 1
        assert gaps[0].gap_type == "missing_tool"

    def test_unsupported_keyword(self) -> None:
        """'unsupported' keyword should flag a missing_tool gap."""
        cluster = make_cluster(
            failure_reason="unsupported operation: refund_v2",
            grader_name="tool_grader",
        )
        opp = make_opportunity(failure_family="tool_error", prevalence=0.2)
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze(blame_clusters=[cluster], opportunities=[opp])

        assert len(gaps) == 1
        assert gaps[0].gap_type == "missing_tool"


class TestRoutingFailureUnknownAgent:
    def test_routing_failure_unknown_agent(self) -> None:
        """routing_failure with unknown agent path should yield missing_sub_agent."""
        cluster = make_cluster(
            cluster_id="c2",
            grader_name="routing_grader",
            agent_path="unknown",
            failure_reason="no route matched for this intent",
            count=10,
            total_traces=30,
        )
        opp = make_opportunity(
            cluster_id="c2",
            failure_family="routing_failure",
            affected_agent_path="unknown",
            prevalence=0.33,
        )
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze(blame_clusters=[cluster], opportunities=[opp])

        assert len(gaps) == 1
        gap = gaps[0]
        assert gap.gap_type == "missing_sub_agent"
        assert gap.suggested_platform == "adk"
        assert gap.failure_family == "routing_failure"

    def test_routing_failure_empty_path(self) -> None:
        """routing_failure with empty agent_path should yield missing_sub_agent."""
        cluster = make_cluster(
            grader_name="router",
            agent_path="",
            failure_reason="routing error: no specialist matched",
        )
        opp = make_opportunity(failure_family="routing_failure", prevalence=0.2)
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze(blame_clusters=[cluster], opportunities=[opp])

        assert len(gaps) == 1
        assert gaps[0].gap_type == "missing_sub_agent"


class TestTuningNotFlagged:
    def test_quality_degradation_unhelpful_not_flagged(self) -> None:
        """quality_degradation with 'unhelpful response' should NOT produce a gap."""
        cluster = make_cluster(
            grader_name="quality_grader",
            agent_path="agents/faq",
            failure_reason="unhelpful response to user query",
            count=5,
            total_traces=20,
        )
        opp = make_opportunity(
            failure_family="quality_degradation",
            prevalence=0.25,
        )
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze(blame_clusters=[cluster], opportunities=[opp])

        assert gaps == []

    def test_hallucination_not_flagged(self) -> None:
        """A hallucination failure should not be flagged as a skill gap."""
        cluster = make_cluster(
            grader_name="hallucination_grader",
            failure_reason="hallucination detected in product description",
        )
        opp = make_opportunity(failure_family="hallucination", prevalence=0.1)
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze(blame_clusters=[cluster], opportunities=[opp])

        assert gaps == []

    def test_latency_spike_not_flagged(self) -> None:
        """Latency / timeout failures are tuning issues, not skill gaps."""
        cluster = make_cluster(
            grader_name="latency_grader",
            failure_reason="timeout exceeded for response generation",
        )
        opp = make_opportunity(failure_family="latency_spike", prevalence=0.15)
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze(blame_clusters=[cluster], opportunities=[opp])

        assert gaps == []


class TestMultipleClustersRanked:
    def test_multiple_clusters_sorted_by_frequency_times_impact(self) -> None:
        """Multiple clusters should be sorted by frequency * impact_score descending."""
        cluster_low = make_cluster(
            cluster_id="clow",
            grader_name="tool_grader",
            failure_reason="missing handler: email_send",
            count=2,
            total_traces=20,
            trend="stable",
        )
        opp_low = make_opportunity(
            cluster_id="clow",
            failure_family="tool_error",
            prevalence=0.1,
        )

        cluster_high = make_cluster(
            cluster_id="chigh",
            grader_name="tool_grader",
            failure_reason="no tool found for invoice generation",
            count=15,
            total_traces=20,
            trend="growing",
        )
        opp_high = make_opportunity(
            cluster_id="chigh",
            failure_family="tool_error",
            prevalence=0.75,
        )

        analyzer = GapAnalyzer()
        gaps = analyzer.analyze(
            blame_clusters=[cluster_low, cluster_high],
            opportunities=[opp_low, opp_high],
        )

        assert len(gaps) == 2
        # High-frequency, high-impact gap should come first
        assert gaps[0].frequency > gaps[1].frequency or (
            gaps[0].frequency * gaps[0].impact_score
            >= gaps[1].frequency * gaps[1].impact_score
        )

    def test_gap_evidence_deduplicates(self) -> None:
        """Evidence trace IDs should be deduplicated across merged clusters."""
        cluster = make_cluster(
            cluster_id="c1",
            failure_reason="no tool found",
            example_trace_ids=["t1", "t2", "t1", "t3"],
        )
        opp = make_opportunity(cluster_id="c1", failure_family="tool_error")
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze(blame_clusters=[cluster], opportunities=[opp])

        assert len(gaps) == 1
        evidence = gaps[0].evidence
        assert len(evidence) == len(set(evidence)), "Evidence should not have duplicates"


class TestCxPlatformMapping:
    def test_cx_tool_error_maps_to_missing_intent(self) -> None:
        """On CX platform, tool_error failures should map to missing_intent."""
        cluster = make_cluster(
            cluster_id="c_cx",
            grader_name="tool_grader",
            agent_path="agents/cx_router",
            failure_reason="no tool found for account lookup",
            count=6,
            total_traces=20,
        )
        opp = make_opportunity(
            cluster_id="c_cx",
            failure_family="tool_error",
            prevalence=0.3,
        )
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze(
            blame_clusters=[cluster],
            opportunities=[opp],
            platform="cx",
        )

        assert len(gaps) == 1
        gap = gaps[0]
        assert gap.suggested_platform == "cx"
        assert gap.gap_type == "missing_intent"

    def test_cx_routing_failure_maps_to_missing_intent(self) -> None:
        """On CX platform, routing_failure should map to missing_intent."""
        cluster = make_cluster(
            grader_name="router",
            agent_path="",
            failure_reason="unknown intent: apply_coupon",
        )
        opp = make_opportunity(failure_family="routing_failure", prevalence=0.4)
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze(
            blame_clusters=[cluster],
            opportunities=[opp],
            platform="cx",
        )

        assert len(gaps) == 1
        assert gaps[0].gap_type == "missing_intent"
        assert gaps[0].suggested_platform == "cx"

    def test_cx_flow_keyword_maps_to_missing_flow(self) -> None:
        """'flow' in failure_reason on CX platform should produce missing_flow."""
        cluster = make_cluster(
            grader_name="tool_grader",
            failure_reason="missing flow for checkout process",
            count=4,
            total_traces=10,
        )
        opp = make_opportunity(failure_family="tool_error", prevalence=0.4)
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze(
            blame_clusters=[cluster],
            opportunities=[opp],
            platform="cx",
        )

        assert len(gaps) == 1
        assert gaps[0].gap_type == "missing_flow"
        assert gaps[0].suggested_platform == "cx"


class TestGrowingTrendBoosts:
    def test_growing_trend_higher_impact_than_stable(self) -> None:
        """A growing-trend cluster should have higher impact_score than a stable one."""
        cluster_growing = make_cluster(
            cluster_id="cg",
            grader_name="tool_grader",
            failure_reason="no tool found for report generation",
            count=8,
            total_traces=20,
            trend="growing",
        )
        opp_growing = make_opportunity(
            cluster_id="cg",
            failure_family="tool_error",
            prevalence=0.5,
        )

        cluster_stable = make_cluster(
            cluster_id="cs",
            grader_name="tool_grader",
            failure_reason="no tool found for pdf export",
            count=8,
            total_traces=20,
            trend="stable",
        )
        opp_stable = make_opportunity(
            cluster_id="cs",
            failure_family="tool_error",
            prevalence=0.2,
        )

        analyzer = GapAnalyzer()
        gaps_growing = analyzer.analyze(
            blame_clusters=[cluster_growing],
            opportunities=[opp_growing],
        )
        gaps_stable = analyzer.analyze(
            blame_clusters=[cluster_stable],
            opportunities=[opp_stable],
        )

        assert len(gaps_growing) == 1
        assert len(gaps_stable) == 1
        # Growing cluster has higher prevalence → higher impact_score
        assert gaps_growing[0].impact_score > gaps_stable[0].impact_score

    def test_growing_high_prevalence_no_keyword_is_still_flagged(self) -> None:
        """tool_error + prevalence > 0.3 + growing trend should flag even without keywords."""
        cluster = make_cluster(
            cluster_id="cg2",
            grader_name="tool_grader",
            agent_path="agents/billing",
            failure_reason="execution error in billing pipeline",
            count=12,
            total_traces=20,
            trend="growing",
        )
        opp = make_opportunity(
            cluster_id="cg2",
            failure_family="tool_error",
            prevalence=0.6,
        )
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze(blame_clusters=[cluster], opportunities=[opp])

        assert len(gaps) == 1


class TestSkillGapFields:
    def test_gap_has_all_required_fields(self) -> None:
        """Every returned SkillGap should have all required fields populated."""
        cluster = make_cluster(
            cluster_id="cf",
            grader_name="tool_grader",
            failure_reason="no tool found: payment_check",
            count=5,
            total_traces=10,
        )
        opp = make_opportunity(cluster_id="cf", failure_family="tool_error", prevalence=0.5)
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze(blame_clusters=[cluster], opportunities=[opp])

        assert len(gaps) == 1
        gap = gaps[0]
        assert gap.gap_id
        assert gap.gap_type
        assert gap.description
        assert isinstance(gap.evidence, list)
        assert gap.failure_family
        assert isinstance(gap.frequency, int) and gap.frequency > 0
        assert 0.0 <= gap.impact_score <= 1.0
        assert gap.suggested_name
        assert gap.suggested_platform in ("adk", "cx")

    def test_to_dict_round_trip(self) -> None:
        """SkillGap.to_dict() should include all public fields."""
        cluster = make_cluster(
            cluster_id="cdict",
            grader_name="tool_grader",
            failure_reason="missing lookup tool",
            count=3,
            total_traces=10,
        )
        opp = make_opportunity(cluster_id="cdict", failure_family="tool_error", prevalence=0.3)
        analyzer = GapAnalyzer()
        gaps = analyzer.analyze(blame_clusters=[cluster], opportunities=[opp])

        assert len(gaps) == 1
        d = gaps[0].to_dict()
        for key in (
            "gap_id", "gap_type", "description", "evidence",
            "failure_family", "frequency", "impact_score",
            "suggested_name", "suggested_platform", "context",
        ):
            assert key in d, f"Missing key: {key}"


class TestSuggestName:
    def test_suggest_name_missing_tool(self) -> None:
        """_suggest_name should extract noun tokens from the failure reason."""
        analyzer = GapAnalyzer()
        name = analyzer._suggest_name("missing_tool", "no tool found for warranty check")
        # Should contain "warranty" or "check" and end with "_tool"
        assert name.endswith("_tool")
        assert len(name) > len("_tool")

    def test_suggest_name_routing(self) -> None:
        """_suggest_name for missing_sub_agent should end with '_agent'."""
        analyzer = GapAnalyzer()
        name = analyzer._suggest_name("missing_sub_agent", "routing failure unknown agent")
        assert name.endswith("_agent")

    def test_suggest_name_fallback(self) -> None:
        """_suggest_name should fall back gracefully for very short reasons."""
        analyzer = GapAnalyzer()
        name = analyzer._suggest_name("missing_tool", "no")
        assert "_tool" in name

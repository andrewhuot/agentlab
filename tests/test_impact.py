"""Tests for multi-agent impact analyzer."""

from __future__ import annotations

from multi_agent.agent_tree import AgentDependency, AgentNode, AgentTree
from multi_agent.impact_analyzer import ImpactAnalyzer, ImpactPrediction


def build_sample_agent_tree() -> AgentTree:
    """Build a sample agent tree for testing."""
    tree = AgentTree()

    # Add orchestrator
    root = AgentNode(
        agent_id="orchestrator",
        agent_type="orchestrator",
        dependencies=[],
        shared_components=["safety_policy"],
    )
    tree.add_node(root)

    # Add specialists
    support = AgentNode(
        agent_id="support",
        agent_type="specialist",
        dependencies=["orchestrator"],
        shared_components=["safety_policy", "ticketing_tool"],
    )
    tree.add_node(support)

    sales = AgentNode(
        agent_id="sales",
        agent_type="specialist",
        dependencies=["orchestrator"],
        shared_components=["safety_policy"],
    )
    tree.add_node(sales)

    orders = AgentNode(
        agent_id="orders",
        agent_type="specialist",
        dependencies=["support"],
        shared_components=["ticketing_tool"],
    )
    tree.add_node(orders)

    # Add routing dependencies
    tree.add_dependency(
        AgentDependency(
            from_agent="orchestrator",
            to_agent="support",
            dependency_type="routing",
        )
    )
    tree.add_dependency(
        AgentDependency(
            from_agent="orchestrator",
            to_agent="sales",
            dependency_type="routing",
        )
    )
    tree.add_dependency(
        AgentDependency(
            from_agent="support",
            to_agent="orders",
            dependency_type="routing",
        )
    )

    return tree


# ---------------------------------------------------------------------------
# AgentTree tests
# ---------------------------------------------------------------------------


def test_agent_tree_add_and_get_node() -> None:
    """AgentTree should store and retrieve nodes."""
    tree = AgentTree()
    node = AgentNode(
        agent_id="test1",
        agent_type="specialist",
        dependencies=[],
        shared_components=[],
    )
    tree.add_node(node)

    retrieved = tree.nodes.get("test1")
    assert retrieved is not None
    assert retrieved.agent_id == "test1"
    assert retrieved.agent_type == "specialist"


def test_agent_tree_get_dependents() -> None:
    """AgentTree should return agents that depend on this agent."""
    tree = build_sample_agent_tree()

    # In the simplified model, get_dependents returns agents where from_agent == target
    # So for orchestrator, it returns agents that depend ON orchestrator
    orchestrator_dependents = tree.get_dependents("orchestrator")
    # These should be empty because nothing routes TO orchestrator
    assert len(orchestrator_dependents) == 0

    # Support has dependents (orchestrator routes to it)
    support_dependents = tree.get_dependents("support")
    assert "orchestrator" in support_dependents


def test_agent_tree_get_dependencies_of() -> None:
    """AgentTree should return dependencies of an agent."""
    tree = build_sample_agent_tree()

    support_deps = tree.get_dependencies_of("support")
    assert "orders" in support_deps


def test_agent_tree_get_shared_components() -> None:
    """AgentTree should return shared components."""
    tree = build_sample_agent_tree()

    support_components = tree.get_shared_components("support")
    assert "safety_policy" in support_components
    assert "ticketing_tool" in support_components


def test_agent_tree_from_config() -> None:
    """AgentTree should parse from configuration."""
    config = {
        "orchestrator": {"name": "Main"},
        "specialists": {
            "support": {"tools": ["faq"]},
            "sales": {"tools": ["catalog"]},
        },
    }

    tree = AgentTree.from_config(config)
    assert "orchestrator" in tree.nodes
    assert "support" in tree.nodes
    assert "sales" in tree.nodes

    # Should have routing dependencies
    support_deps = tree.get_dependencies_of("orchestrator")
    assert "support" in support_deps
    assert "sales" in support_deps


# ---------------------------------------------------------------------------
# ImpactAnalyzer tests
# ---------------------------------------------------------------------------


def test_impact_analyzer_analyze_dependencies() -> None:
    """ImpactAnalyzer should compute dependency map."""
    tree = build_sample_agent_tree()
    analyzer = ImpactAnalyzer(agent_tree=tree)

    dep_map = analyzer.analyze_dependencies()

    assert "orchestrator" in dep_map
    assert "support" in dep_map
    assert "dependents" in dep_map["orchestrator"]
    assert "dependencies" in dep_map["orchestrator"]


def test_impact_analyzer_predict_impact() -> None:
    """ImpactAnalyzer should predict impact of changes."""
    tree = build_sample_agent_tree()
    analyzer = ImpactAnalyzer(agent_tree=tree)

    mutation = {
        "target_agent": "orchestrator",
        "type": "config_change",
    }

    predictions = analyzer.predict_impact(mutation, tree)

    assert len(predictions) > 0
    # Should predict impact on orchestrator itself
    orch_predictions = [p for p in predictions if p.agent_id == "orchestrator"]
    assert len(orch_predictions) > 0
    assert orch_predictions[0].affected is True


def test_impact_analyzer_cross_agent_eval() -> None:
    """ImpactAnalyzer should evaluate mutations across agents."""
    tree = build_sample_agent_tree()
    analyzer = ImpactAnalyzer(agent_tree=tree)

    mutation = {"target_agent": "support"}
    affected_agents = ["support", "orders"]

    results = analyzer.cross_agent_eval(mutation, affected_agents)

    assert "support" in results
    assert "orders" in results
    assert "quality" in results["support"]
    assert "latency" in results["support"]
    assert "cost" in results["support"]


def test_impact_analyzer_generate_impact_report() -> None:
    """ImpactAnalyzer should generate structured impact report."""
    tree = build_sample_agent_tree()
    analyzer = ImpactAnalyzer(agent_tree=tree)

    # generate_impact_report expects a dict where values have .get() method
    results = {
        "support": {"affected": True, "quality": 0.9, "latency": 100.0},
        "orders": {"affected": True, "quality": 0.85, "latency": 120.0},
    }

    report = analyzer.generate_impact_report(results)

    assert isinstance(report, dict)
    assert "summary" in report
    assert "agent_results" in report
    assert "recommendations" in report


def test_impact_prediction_structure() -> None:
    """ImpactPrediction should have correct structure."""
    prediction = ImpactPrediction(
        agent_id="test",
        affected=True,
        predicted_delta=0.05,
        confidence=0.8,
        reason="Test reason",
    )

    assert prediction.agent_id == "test"
    assert prediction.affected is True
    assert prediction.predicted_delta == 0.05
    assert prediction.confidence == 0.8


def test_agent_dependency_structure() -> None:
    """AgentDependency should have correct structure."""
    dep = AgentDependency(
        from_agent="agent1",
        to_agent="agent2",
        dependency_type="routing",
    )

    assert dep.from_agent == "agent1"
    assert dep.to_agent == "agent2"
    assert dep.dependency_type == "routing"


def test_agent_node_defaults() -> None:
    """AgentNode should have correct defaults."""
    node = AgentNode(
        agent_id="test",
        agent_type="specialist",
    )

    assert node.agent_id == "test"
    assert node.agent_type == "specialist"
    assert node.dependencies == []
    assert node.shared_components == []
    assert node.config == {}

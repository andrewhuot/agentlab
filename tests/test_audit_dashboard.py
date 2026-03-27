"""Tests for audit dashboard (change tracking with transparency)."""

import time
import pytest
from optimizer.change_card import ProposedChangeCard, ConfidenceInfo, DiffHunk


def test_change_card_with_audit_fields():
    """Test that change cards support audit fields."""
    card = ProposedChangeCard(
        card_id="test_card",
        title="Test change",
        why="Improve routing",
        status="applied",
        dimension_breakdown={
            "safety": {"before": 0.85, "after": 0.90, "delta": 0.05},
            "quality": {"before": 0.75, "after": 0.87, "delta": 0.12},
            "latency": {"before": 850.0, "after": 820.0, "delta": -30.0},
        },
        gate_results=[
            {"gate": "significance", "passed": True, "reason": "p=0.01 < 0.05"},
            {"gate": "safety", "passed": True, "reason": "No safety regression"},
            {"gate": "cost", "passed": True, "reason": "Cost delta within budget"},
        ],
        adversarial_results={
            "passed": True,
            "score_drop": 0.02,
            "num_cases": 20,
        },
        composite_breakdown={
            "weights": {"safety": 0.4, "quality": 0.4, "latency": 0.2},
            "components": {"safety": 0.90, "quality": 0.87, "latency": 0.82},
            "contributions": {"safety": 0.36, "quality": 0.348, "latency": 0.164},
        },
        timeline=[
            {"phase": "proposed", "timestamp": 1234567890.0, "status": "pending"},
            {"phase": "evaluated", "timestamp": 1234567891.0, "status": "in_progress"},
            {"phase": "gated", "timestamp": 1234567892.0, "status": "passed"},
            {"phase": "accepted", "timestamp": 1234567893.0, "status": "applied"},
        ],
    )

    # Test to_dict includes audit fields
    card_dict = card.to_dict()
    assert "dimension_breakdown" in card_dict
    assert "gate_results" in card_dict
    assert "adversarial_results" in card_dict
    assert "composite_breakdown" in card_dict
    assert "timeline" in card_dict

    # Verify dimension breakdown structure
    assert "safety" in card_dict["dimension_breakdown"]
    assert card_dict["dimension_breakdown"]["safety"]["delta"] == 0.05
    assert card_dict["dimension_breakdown"]["quality"]["delta"] == 0.12

    # Verify gate results
    assert len(card_dict["gate_results"]) == 3
    assert card_dict["gate_results"][0]["gate"] == "significance"
    assert card_dict["gate_results"][0]["passed"] is True

    # Verify adversarial results
    assert card_dict["adversarial_results"]["passed"] is True
    assert card_dict["adversarial_results"]["num_cases"] == 20

    # Verify composite breakdown
    assert "weights" in card_dict["composite_breakdown"]
    assert card_dict["composite_breakdown"]["weights"]["safety"] == 0.4

    # Verify timeline
    assert len(card_dict["timeline"]) == 4
    assert card_dict["timeline"][0]["phase"] == "proposed"
    assert card_dict["timeline"][-1]["phase"] == "accepted"


def test_change_card_from_dict_with_audit():
    """Test deserializing change card with audit fields."""
    data = {
        "card_id": "test_card",
        "title": "Test",
        "why": "Because",
        "diff_hunks": [],
        "metrics_before": {},
        "metrics_after": {},
        "metrics_by_slice": {},
        "confidence": {},
        "status": "applied",
        "dimension_breakdown": {
            "safety": {"before": 0.8, "after": 0.9, "delta": 0.1},
        },
        "gate_results": [
            {"gate": "test_gate", "passed": True, "reason": "OK"},
        ],
        "adversarial_results": {
            "passed": True,
            "score_drop": 0.01,
        },
        "composite_breakdown": {
            "weights": {"safety": 1.0},
        },
        "timeline": [
            {"phase": "proposed", "timestamp": 123.0},
        ],
    }

    card = ProposedChangeCard.from_dict(data)
    assert card.card_id == "test_card"
    assert len(card.dimension_breakdown) == 1
    assert len(card.gate_results) == 1
    assert card.adversarial_results is not None
    assert card.composite_breakdown is not None
    assert len(card.timeline) == 1


def test_rejected_card_with_failed_gates():
    """Test a rejected change with gate failures."""
    card = ProposedChangeCard(
        card_id="rejected_card",
        title="Failed change",
        why="Attempted improvement",
        status="rejected",
        rejection_reason="safety_regression",
        dimension_breakdown={
            "safety": {"before": 0.90, "after": 0.75, "delta": -0.15},  # Regression!
            "quality": {"before": 0.80, "after": 0.85, "delta": 0.05},
        },
        gate_results=[
            {"gate": "significance", "passed": True, "reason": "p=0.02 < 0.05"},
            {"gate": "safety", "passed": False, "reason": "Safety regression detected: -0.15"},
            {"gate": "cost", "passed": True, "reason": "Cost delta OK"},
        ],
        adversarial_results={
            "passed": False,
            "score_drop": 0.25,
            "num_cases": 15,
        },
        timeline=[
            {"phase": "proposed", "timestamp": 1234567890.0, "status": "pending"},
            {"phase": "evaluated", "timestamp": 1234567891.0, "status": "in_progress"},
            {"phase": "gated", "timestamp": 1234567892.0, "status": "failed"},
            {"phase": "rejected", "timestamp": 1234567893.0, "status": "rejected"},
        ],
    )

    # Verify rejection details
    assert card.status == "rejected"
    assert card.rejection_reason == "safety_regression"

    # Verify gate failures
    failed_gates = [g for g in card.gate_results if not g["passed"]]
    assert len(failed_gates) == 1
    assert failed_gates[0]["gate"] == "safety"

    # Verify adversarial failure
    assert card.adversarial_results["passed"] is False
    assert card.adversarial_results["score_drop"] == 0.25

    # Verify timeline shows rejection
    assert card.timeline[-1]["status"] == "rejected"


def test_card_without_adversarial_results():
    """Test card that didn't run adversarial simulation."""
    card = ProposedChangeCard(
        card_id="no_adversarial",
        title="Test",
        why="Test",
        status="applied",
        adversarial_results=None,  # Not run
    )

    card_dict = card.to_dict()
    assert card_dict["adversarial_results"] is None


def test_dimension_breakdown_calculations():
    """Test that dimension breakdowns show correct deltas."""
    dimension_breakdown = {
        "safety": {"before": 0.80, "after": 0.85, "delta": 0.05},
        "quality": {"before": 0.70, "after": 0.90, "delta": 0.20},
        "latency": {"before": 1000.0, "after": 800.0, "delta": -200.0},
        "cost": {"before": 0.50, "after": 0.48, "delta": -0.02},
    }

    card = ProposedChangeCard(
        card_id="deltas",
        title="Test deltas",
        why="Test",
        dimension_breakdown=dimension_breakdown,
    )

    # Verify all deltas
    assert card.dimension_breakdown["safety"]["delta"] == 0.05  # Improvement
    assert card.dimension_breakdown["quality"]["delta"] == 0.20  # Big improvement
    assert card.dimension_breakdown["latency"]["delta"] == -200.0  # Faster (improvement)
    assert card.dimension_breakdown["cost"]["delta"] == -0.02  # Cheaper (improvement)


def test_composite_breakdown_weighted_contributions():
    """Test composite score breakdown with weighted contributions."""
    composite = {
        "weights": {
            "safety": 0.4,
            "quality": 0.4,
            "latency": 0.2,
        },
        "components": {
            "safety": 0.90,
            "quality": 0.85,
            "latency": 0.75,
        },
        "contributions": {
            "safety": 0.36,   # 0.90 * 0.4
            "quality": 0.34,  # 0.85 * 0.4
            "latency": 0.15,  # 0.75 * 0.2
        },
    }

    card = ProposedChangeCard(
        card_id="composite",
        title="Test composite",
        why="Test",
        composite_breakdown=composite,
    )

    # Verify structure
    assert "weights" in card.composite_breakdown
    assert "components" in card.composite_breakdown
    assert "contributions" in card.composite_breakdown

    # Verify contributions sum correctly
    total_contribution = sum(card.composite_breakdown["contributions"].values())
    assert abs(total_contribution - 0.85) < 0.01  # Should be ~0.85


def test_timeline_phases():
    """Test that timeline tracks all optimization phases."""
    timeline = [
        {"phase": "proposed", "timestamp": 1000.0, "status": "pending"},
        {"phase": "evaluated", "timestamp": 1001.0, "status": "in_progress"},
        {"phase": "gated", "timestamp": 1002.0, "status": "passed"},
        {"phase": "accepted", "timestamp": 1003.0, "status": "applied"},
    ]

    card = ProposedChangeCard(
        card_id="timeline_test",
        title="Test timeline",
        why="Test",
        timeline=timeline,
    )

    assert len(card.timeline) == 4

    # Verify phase order
    phases = [entry["phase"] for entry in card.timeline]
    assert phases == ["proposed", "evaluated", "gated", "accepted"]

    # Verify timestamps are ordered
    timestamps = [entry["timestamp"] for entry in card.timeline]
    assert timestamps == sorted(timestamps)


def test_empty_audit_fields():
    """Test card with minimal/empty audit fields."""
    card = ProposedChangeCard(
        card_id="minimal",
        title="Minimal card",
        why="Test",
    )

    # Should have empty defaults
    assert card.dimension_breakdown == {}
    assert card.gate_results == []
    assert card.adversarial_results is None
    assert card.composite_breakdown is None
    assert card.timeline == []

    # Should serialize without errors
    card_dict = card.to_dict()
    assert "dimension_breakdown" in card_dict

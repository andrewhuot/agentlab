"""Tests for CX Studio integration features."""
from __future__ import annotations

from cx_studio.mapper_extensions import (
    guardrails_to_cx_safety_settings,
    integration_templates_to_cx_tools,
    knowledge_asset_to_cx_datastore,
)


def test_integration_templates_to_cx_tools():
    """Test converting integration templates to CX Tool definitions."""
    templates = [
        {
            "connector": "Shopify",
            "name": "shopify_order_lookup",
            "method": "GET",
            "endpoint": "/admin/api/2024-10/orders/{order_id}.json",
            "auth_strategy": "shopify_admin_access_token",
        },
        {
            "connector": "Zendesk",
            "name": "zendesk_create_ticket",
            "method": "POST",
            "endpoint": "/api/v2/tickets.json",
            "auth_strategy": "zendesk_api_token",
        },
    ]

    agent_name = "projects/test/locations/us-central1/agents/agent-123"
    tools = integration_templates_to_cx_tools(templates, agent_name)

    assert len(tools) == 2
    assert tools[0].display_name == "Shopify: shopify_order_lookup"
    assert tools[0].tool_type == "OPEN_API"
    assert "openapi" in tools[0].spec["schema"]
    assert tools[1].display_name == "Zendesk: zendesk_create_ticket"


def test_knowledge_asset_to_cx_datastore():
    """Test converting knowledge asset to CX DataStore payload."""
    knowledge_asset = {
        "asset_id": "kb-123",
        "entries": [
            {
                "type": "faq",
                "intent": "order_tracking",
                "question": "Where is my order?",
                "answer": "You can track your order using the tracking number.",
            },
            {
                "type": "procedure",
                "intent": "cancellation",
                "steps": ["Verify customer identity", "Check order status", "Process cancellation"],
            },
            {
                "type": "workflow",
                "title": "Escalation Workflow",
                "description": "Transfer to live support with context.",
            },
        ],
    }

    payload = knowledge_asset_to_cx_datastore(knowledge_asset, "Test Knowledge Base")

    assert payload["display_name"] == "Test Knowledge Base"
    assert payload["data_store_type"] == "unstructured"
    assert len(payload["content_entries"]) == 3

    # Check FAQ entry
    faq_entry = payload["content_entries"][0]
    assert faq_entry["contentType"] == "FAQ"
    assert faq_entry["question"] == "Where is my order?"

    # Check procedure entry
    procedure_entry = payload["content_entries"][1]
    assert procedure_entry["contentType"] == "DOCUMENT"
    assert "Verify customer identity" in procedure_entry["content"]

    # Check workflow entry
    workflow_entry = payload["content_entries"][2]
    assert workflow_entry["contentType"] == "DOCUMENT"
    assert workflow_entry["title"] == "Escalation Workflow"


def test_guardrails_to_cx_safety_settings():
    """Test converting guardrails to CX safety settings."""
    guardrails = [
        "Never disclose internal notes or pricing artifacts.",
        "Require verification before modifying orders or personal details.",
        "Do not share customer email addresses with third parties.",
    ]

    safety_settings = guardrails_to_cx_safety_settings(guardrails)

    assert "internal notes" in safety_settings["bannedPhrases"]
    assert "pricing" in safety_settings["bannedPhrases"]
    assert len(safety_settings["safetySettings"]) > 0
    assert safety_settings["safetySettings"][0]["threshold"] == "BLOCK_LOW_AND_ABOVE"


def test_guardrails_to_cx_safety_settings_empty():
    """Test guardrails conversion with empty input."""
    safety_settings = guardrails_to_cx_safety_settings([])

    assert safety_settings["bannedPhrases"] == []
    assert safety_settings["safetySettings"] == []

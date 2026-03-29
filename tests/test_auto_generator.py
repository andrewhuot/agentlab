"""Comprehensive tests for evals/auto_generator.py — AI-powered eval suite generator.

Covers data structures (GeneratedEvalCase, GeneratedEvalSuite), mock generation,
suite management operations, context extraction, LLM response parsing, and prompt
construction.
"""
from __future__ import annotations

import json
import uuid

import pytest

from evals.auto_generator import (
    EVAL_CATEGORIES,
    EXPECTED_BEHAVIORS,
    DIFFICULTY_LEVELS,
    AutoEvalGenerator,
    GeneratedEvalCase,
    GeneratedEvalSuite,
    _build_generation_prompt,
    _parse_llm_response,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_case(**overrides) -> GeneratedEvalCase:
    """Return a minimal GeneratedEvalCase for testing."""
    defaults = {
        "case_id": f"test_{uuid.uuid4().hex[:8]}",
        "category": "happy_path",
        "user_message": "Hello, how are you?",
        "expected_behavior": "answer",
        "expected_specialist": "general_agent",
        "expected_keywords": ["hello"],
        "expected_tool": None,
        "safety_probe": False,
        "difficulty": "easy",
        "rationale": "Test case",
        "split": "tuning",
    }
    defaults.update(overrides)
    return GeneratedEvalCase(**defaults)


def _make_suite(**overrides) -> GeneratedEvalSuite:
    """Return a minimal GeneratedEvalSuite for testing."""
    defaults = {
        "suite_id": f"suite_{uuid.uuid4().hex[:12]}",
        "agent_name": "test_agent",
        "created_at": "2026-01-01T00:00:00+00:00",
        "status": "ready",
        "categories": {
            "happy_path": [_make_case(category="happy_path")],
            "safety": [_make_case(category="safety", safety_probe=True, expected_behavior="refuse")],
        },
        "summary": {},
    }
    defaults.update(overrides)
    return GeneratedEvalSuite(**defaults)


# ---------------------------------------------------------------------------
# GeneratedEvalCase serialization
# ---------------------------------------------------------------------------


class TestGeneratedEvalCase:
    """Tests for GeneratedEvalCase to_dict, from_dict, and to_test_case_dict."""

    def test_to_dict_contains_all_fields(self) -> None:
        case = _make_case()
        d = case.to_dict()
        assert d["case_id"] == case.case_id
        assert d["category"] == "happy_path"
        assert d["user_message"] == "Hello, how are you?"
        assert d["expected_behavior"] == "answer"
        assert d["expected_specialist"] == "general_agent"
        assert d["expected_keywords"] == ["hello"]
        assert d["expected_tool"] is None
        assert d["safety_probe"] is False
        assert d["difficulty"] == "easy"
        assert d["rationale"] == "Test case"
        assert d["split"] == "tuning"

    def test_from_dict_round_trip(self) -> None:
        original = _make_case(expected_tool="search_kb", safety_probe=True)
        d = original.to_dict()
        restored = GeneratedEvalCase.from_dict(d)
        assert restored.to_dict() == d

    def test_from_dict_handles_missing_keys(self) -> None:
        """from_dict should apply sensible defaults for missing keys."""
        case = GeneratedEvalCase.from_dict({"user_message": "test"})
        assert case.case_id == ""
        assert case.category == "happy_path"
        assert case.expected_behavior == "answer"
        assert case.expected_keywords == []
        assert case.expected_tool is None
        assert case.difficulty == "medium"
        assert case.split == "tuning"

    def test_from_dict_handles_none_keywords(self) -> None:
        """expected_keywords=None in source dict should become empty list."""
        case = GeneratedEvalCase.from_dict({"expected_keywords": None})
        assert case.expected_keywords == []

    def test_to_test_case_dict_format(self) -> None:
        case = _make_case(case_id="auto_happy_path_001", expected_tool="lookup_order")
        tc = case.to_test_case_dict()
        assert tc["id"] == "auto_happy_path_001"
        assert tc["category"] == "happy_path"
        assert tc["user_message"] == case.user_message
        assert tc["expected_specialist"] == "general_agent"
        assert tc["expected_behavior"] == "answer"
        assert tc["safety_probe"] is False
        assert tc["expected_keywords"] == ["hello"]
        assert tc["expected_tool"] == "lookup_order"
        assert tc["split"] == "tuning"
        assert tc["reference_answer"] == ""

    def test_to_test_case_dict_round_trip_via_from_dict(self) -> None:
        """to_dict -> from_dict -> to_test_case_dict should be consistent."""
        original = _make_case()
        restored = GeneratedEvalCase.from_dict(original.to_dict())
        assert restored.to_test_case_dict() == original.to_test_case_dict()


# ---------------------------------------------------------------------------
# GeneratedEvalSuite serialization
# ---------------------------------------------------------------------------


class TestGeneratedEvalSuite:
    """Tests for GeneratedEvalSuite serialization and helpers."""

    def test_total_cases(self) -> None:
        suite = _make_suite()
        assert suite.total_cases == 2

    def test_all_cases_returns_flat_list(self) -> None:
        suite = _make_suite()
        all_c = suite.all_cases()
        assert len(all_c) == 2
        categories = {c.category for c in all_c}
        assert "happy_path" in categories
        assert "safety" in categories

    def test_all_cases_includes_nonstandard_categories(self) -> None:
        """Categories not in EVAL_CATEGORIES should still appear in all_cases."""
        case = _make_case(category="custom_category")
        suite = _make_suite(categories={"custom_category": [case]})
        assert len(suite.all_cases()) == 1
        assert suite.all_cases()[0].category == "custom_category"

    def test_to_dict_round_trip(self) -> None:
        suite = _make_suite()
        d = suite.to_dict()
        restored = GeneratedEvalSuite.from_dict(d)
        assert restored.suite_id == suite.suite_id
        assert restored.agent_name == suite.agent_name
        assert restored.status == suite.status
        assert restored.total_cases == suite.total_cases

    def test_from_dict_defaults(self) -> None:
        suite = GeneratedEvalSuite.from_dict({})
        assert suite.suite_id == ""
        assert suite.agent_name == ""
        assert suite.status == "ready"
        assert suite.total_cases == 0

    def test_to_test_cases(self) -> None:
        suite = _make_suite()
        test_cases = suite.to_test_cases()
        assert len(test_cases) == 2
        # Each element should have the test-case shape
        for tc in test_cases:
            assert "id" in tc
            assert "user_message" in tc
            assert "expected_behavior" in tc
            assert "reference_answer" in tc


# ---------------------------------------------------------------------------
# AutoEvalGenerator — mock generation
# ---------------------------------------------------------------------------


class TestMockGeneration:
    """Tests for AutoEvalGenerator with provider='mock'."""

    @pytest.fixture()
    def generator(self) -> AutoEvalGenerator:
        return AutoEvalGenerator(llm_provider="mock")

    def test_generate_returns_ready_suite(self, generator: AutoEvalGenerator) -> None:
        suite = generator.generate(agent_config={}, agent_name="test")
        assert suite.status == "ready"
        assert suite.suite_id.startswith("suite_")
        assert suite.agent_name == "test"

    def test_generate_covers_all_eight_categories(self, generator: AutoEvalGenerator) -> None:
        suite = generator.generate(agent_config={}, agent_name="test")
        for cat in EVAL_CATEGORIES:
            assert cat in suite.categories, f"Missing category: {cat}"
            assert len(suite.categories[cat]) >= 1, f"Category {cat} has no cases"

    def test_all_cases_have_valid_fields(self, generator: AutoEvalGenerator) -> None:
        suite = generator.generate(agent_config={}, agent_name="test")
        for case in suite.all_cases():
            assert case.category in EVAL_CATEGORIES, f"Invalid category: {case.category}"
            assert case.expected_behavior in EXPECTED_BEHAVIORS, f"Invalid behavior: {case.expected_behavior}"
            assert case.difficulty in DIFFICULTY_LEVELS, f"Invalid difficulty: {case.difficulty}"
            assert case.case_id, "case_id must not be empty"
            assert isinstance(case.user_message, str)
            assert isinstance(case.expected_keywords, list)
            assert isinstance(case.safety_probe, bool)

    def test_safety_cases_are_marked_as_probes(self, generator: AutoEvalGenerator) -> None:
        suite = generator.generate(agent_config={}, agent_name="test")
        for case in suite.categories.get("safety", []):
            assert case.safety_probe is True

    def test_summary_has_expected_keys(self, generator: AutoEvalGenerator) -> None:
        suite = generator.generate(agent_config={}, agent_name="test")
        summary = suite.summary
        assert "total_cases" in summary
        assert "categories" in summary
        assert "difficulty_distribution" in summary
        assert "behavior_distribution" in summary
        assert "safety_probes" in summary
        assert summary["total_cases"] == suite.total_cases

    def test_config_with_tools_generates_tool_usage_cases(self, generator: AutoEvalGenerator) -> None:
        config = {
            "tools": [
                {"name": "search_kb", "description": "Search knowledge base"},
                {"name": "create_ticket", "description": "Create support ticket"},
            ]
        }
        suite = generator.generate(agent_config=config, agent_name="test")
        tool_cases = suite.categories.get("tool_usage", [])
        # Should have cases for both tools plus a negative case
        assert len(tool_cases) >= 3
        tool_names = [c.expected_tool for c in tool_cases if c.expected_tool]
        assert "search_kb" in tool_names
        assert "create_ticket" in tool_names

    def test_config_with_routing_rules_generates_routing_cases(self, generator: AutoEvalGenerator) -> None:
        config = {
            "routing_rules": [
                {"pattern": "billing", "target": "billing_agent"},
                {"pattern": "technical", "target": "tech_agent"},
            ]
        }
        suite = generator.generate(agent_config=config, agent_name="test")
        routing_cases = suite.categories.get("routing", [])
        assert len(routing_cases) >= 2
        specialists = {c.expected_specialist for c in routing_cases}
        assert "billing_agent" in specialists
        assert "tech_agent" in specialists

    def test_config_with_policies_generates_policy_cases(self, generator: AutoEvalGenerator) -> None:
        config = {
            "policies": [
                {"name": "no_pii", "description": "Never share PII"},
            ]
        }
        suite = generator.generate(agent_config=config, agent_name="test")
        policy_cases = suite.categories.get("policy_compliance", [])
        assert len(policy_cases) >= 1
        # Policy violation cases should expect refusal
        for case in policy_cases:
            assert case.expected_behavior == "refuse"

    def test_config_with_specialists_generates_routing_cases(self, generator: AutoEvalGenerator) -> None:
        config = {"specialists": ["billing_agent", "tech_agent"]}
        suite = generator.generate(agent_config=config, agent_name="test")
        routing_cases = suite.categories.get("routing", [])
        assert len(routing_cases) >= 2

    def test_total_cases_matches_summary(self, generator: AutoEvalGenerator) -> None:
        suite = generator.generate(agent_config={}, agent_name="test")
        assert suite.total_cases == suite.summary["total_cases"]
        cat_sum = sum(suite.summary["categories"].values())
        assert cat_sum == suite.total_cases


# ---------------------------------------------------------------------------
# AutoEvalGenerator — suite management
# ---------------------------------------------------------------------------


class TestSuiteManagement:
    """Tests for get_suite, accept_suite, update_case, delete_case."""

    @pytest.fixture()
    def generator_with_suite(self) -> tuple[AutoEvalGenerator, GeneratedEvalSuite]:
        gen = AutoEvalGenerator(llm_provider="mock")
        suite = gen.generate(agent_config={}, agent_name="mgmt_test")
        return gen, suite

    def test_get_suite_returns_none_for_unknown_id(self) -> None:
        gen = AutoEvalGenerator(llm_provider="mock")
        assert gen.get_suite("nonexistent_id") is None

    def test_get_suite_returns_generated_suite(self, generator_with_suite) -> None:
        gen, suite = generator_with_suite
        fetched = gen.get_suite(suite.suite_id)
        assert fetched is not None
        assert fetched.suite_id == suite.suite_id

    def test_accept_suite_changes_status(self, generator_with_suite) -> None:
        gen, suite = generator_with_suite
        assert suite.status == "ready"
        result = gen.accept_suite(suite.suite_id)
        assert result is not None
        assert result.status == "accepted"
        # Verify persistence
        assert gen.get_suite(suite.suite_id).status == "accepted"

    def test_accept_suite_returns_none_for_unknown_id(self) -> None:
        gen = AutoEvalGenerator(llm_provider="mock")
        assert gen.accept_suite("nonexistent") is None

    def test_update_case_modifies_fields(self, generator_with_suite) -> None:
        gen, suite = generator_with_suite
        first_case = suite.all_cases()[0]
        updated = gen.update_case(
            suite.suite_id,
            first_case.case_id,
            {"user_message": "Updated message", "difficulty": "hard"},
        )
        assert updated is not None
        assert updated.user_message == "Updated message"
        assert updated.difficulty == "hard"
        assert updated.case_id == first_case.case_id  # ID unchanged

    def test_update_case_cannot_change_case_id(self, generator_with_suite) -> None:
        gen, suite = generator_with_suite
        first_case = suite.all_cases()[0]
        original_id = first_case.case_id
        gen.update_case(suite.suite_id, original_id, {"case_id": "hacked_id"})
        assert first_case.case_id == original_id

    def test_update_case_refreshes_summary(self, generator_with_suite) -> None:
        gen, suite = generator_with_suite
        first_case = suite.all_cases()[0]
        old_summary = dict(suite.summary)
        gen.update_case(suite.suite_id, first_case.case_id, {"difficulty": "hard"})
        # Summary should have been refreshed (may or may not change values)
        assert "total_cases" in suite.summary

    def test_update_case_returns_none_for_unknown_case(self, generator_with_suite) -> None:
        gen, suite = generator_with_suite
        assert gen.update_case(suite.suite_id, "no_such_case", {"difficulty": "hard"}) is None

    def test_update_case_returns_none_for_unknown_suite(self) -> None:
        gen = AutoEvalGenerator(llm_provider="mock")
        assert gen.update_case("no_suite", "no_case", {}) is None

    def test_delete_case_removes_case(self, generator_with_suite) -> None:
        gen, suite = generator_with_suite
        total_before = suite.total_cases
        first_case = suite.all_cases()[0]
        assert gen.delete_case(suite.suite_id, first_case.case_id) is True
        assert suite.total_cases == total_before - 1

    def test_delete_case_refreshes_summary(self, generator_with_suite) -> None:
        gen, suite = generator_with_suite
        first_case = suite.all_cases()[0]
        gen.delete_case(suite.suite_id, first_case.case_id)
        assert suite.summary["total_cases"] == suite.total_cases

    def test_delete_case_removes_empty_category(self, generator_with_suite) -> None:
        gen, suite = generator_with_suite
        # Delete all cases from a category with exactly one case
        # Find a category with one case or create one
        for cat, cases in list(suite.categories.items()):
            if len(cases) == 1:
                gen.delete_case(suite.suite_id, cases[0].case_id)
                assert cat not in suite.categories
                break

    def test_delete_case_returns_false_for_unknown_case(self, generator_with_suite) -> None:
        gen, suite = generator_with_suite
        assert gen.delete_case(suite.suite_id, "no_such_case") is False

    def test_delete_case_returns_false_for_unknown_suite(self) -> None:
        gen = AutoEvalGenerator(llm_provider="mock")
        assert gen.delete_case("no_suite", "no_case") is False


# ---------------------------------------------------------------------------
# _extract_analysis_context — key normalization
# ---------------------------------------------------------------------------


class TestExtractAnalysisContext:
    """Tests for _extract_analysis_context key normalization."""

    def _extract(self, config: dict) -> dict:
        gen = AutoEvalGenerator(llm_provider="mock")
        return gen._extract_analysis_context(config)

    def test_system_prompt_key_variants(self) -> None:
        for key in ("system_prompt", "systemPrompt", "prompt", "instructions"):
            ctx = self._extract({key: "You are a helpful assistant."})
            assert ctx["system_prompt"] == "You are a helpful assistant.", f"Failed for key: {key}"

    def test_tools_key_variants(self) -> None:
        tools = [{"name": "search"}]
        for key in ("tools", "functions", "available_tools"):
            ctx = self._extract({key: tools})
            assert ctx["tools"] == tools, f"Failed for key: {key}"

    def test_routing_rules_key_variants(self) -> None:
        rules = [{"pattern": "billing", "target": "billing_agent"}]
        for key in ("routing_rules", "routingRules", "routes", "routing"):
            ctx = self._extract({key: rules})
            assert ctx["routing_rules"] == rules, f"Failed for key: {key}"

    def test_policies_key_variants(self) -> None:
        policies = [{"name": "no_pii"}]
        for key in ("policies", "guardrails", "safety_rules", "rules"):
            ctx = self._extract({key: policies})
            assert ctx["policies"] == policies, f"Failed for key: {key}"

    def test_specialists_key_variants(self) -> None:
        specialists = ["billing_agent"]
        for key in ("specialists", "agents", "sub_agents"):
            ctx = self._extract({key: specialists})
            assert ctx["specialists"] == specialists, f"Failed for key: {key}"

    def test_empty_config_returns_empty_context(self) -> None:
        ctx = self._extract({})
        assert ctx == {}

    def test_first_matching_key_wins(self) -> None:
        """When multiple variants are present, the first one checked wins."""
        ctx = self._extract({"system_prompt": "first", "prompt": "second"})
        assert ctx["system_prompt"] == "first"


# ---------------------------------------------------------------------------
# _parse_llm_response
# ---------------------------------------------------------------------------


class TestParseLlmResponse:
    """Tests for _parse_llm_response handling various LLM output formats."""

    def test_valid_json_array(self) -> None:
        raw = json.dumps([{"case_id": "1", "category": "happy_path"}])
        result = _parse_llm_response(raw)
        assert len(result) == 1
        assert result[0]["case_id"] == "1"

    def test_json_with_markdown_fences(self) -> None:
        raw = "```json\n[{\"case_id\": \"1\"}]\n```"
        result = _parse_llm_response(raw)
        assert len(result) == 1
        assert result[0]["case_id"] == "1"

    def test_json_with_bare_markdown_fences(self) -> None:
        raw = "```\n[{\"case_id\": \"2\"}]\n```"
        result = _parse_llm_response(raw)
        assert len(result) == 1

    def test_wrapped_object_with_cases_key(self) -> None:
        raw = json.dumps({"cases": [{"case_id": "1"}, {"case_id": "2"}]})
        result = _parse_llm_response(raw)
        assert len(result) == 2

    def test_single_dict_without_cases_key(self) -> None:
        raw = json.dumps({"case_id": "single"})
        result = _parse_llm_response(raw)
        assert len(result) == 1
        assert result[0]["case_id"] == "single"

    def test_invalid_json_returns_empty(self) -> None:
        result = _parse_llm_response("this is not json at all {{{")
        assert result == []

    def test_embedded_array_extraction(self) -> None:
        raw = 'Here are the cases:\n[{"case_id": "1"}]\nDone!'
        result = _parse_llm_response(raw)
        assert len(result) == 1

    def test_empty_string_returns_empty(self) -> None:
        result = _parse_llm_response("")
        assert result == []

    def test_whitespace_only_returns_empty(self) -> None:
        result = _parse_llm_response("   \n\n  ")
        assert result == []


# ---------------------------------------------------------------------------
# _build_generation_prompt
# ---------------------------------------------------------------------------


class TestBuildGenerationPrompt:
    """Tests for _build_generation_prompt context-aware sections."""

    def test_includes_system_prompt_section(self) -> None:
        ctx = {"system_prompt": "You are a billing assistant."}
        prompt = _build_generation_prompt(ctx, "billing_bot")
        assert "You are a billing assistant." in prompt
        assert "Agent System Prompt" in prompt

    def test_no_system_prompt_uses_agent_name(self) -> None:
        prompt = _build_generation_prompt({}, "my_agent")
        assert "my_agent" in prompt
        assert "no system prompt provided" in prompt

    def test_includes_tools_section(self) -> None:
        ctx = {"tools": [{"name": "search_kb", "description": "Search docs"}]}
        prompt = _build_generation_prompt(ctx, "agent")
        assert "Available Tools" in prompt
        assert "search_kb" in prompt
        assert "Search docs" in prompt

    def test_includes_tools_with_function_key(self) -> None:
        ctx = {"tools": [{"function": {"name": "my_fn", "description": "Does stuff"}}]}
        prompt = _build_generation_prompt(ctx, "agent")
        assert "my_fn" in prompt

    def test_includes_string_tools(self) -> None:
        ctx = {"tools": ["search", "create_ticket"]}
        prompt = _build_generation_prompt(ctx, "agent")
        assert "search" in prompt
        assert "create_ticket" in prompt

    def test_includes_routing_rules_section(self) -> None:
        ctx = {"routing_rules": [{"pattern": "billing", "target": "billing_agent"}]}
        prompt = _build_generation_prompt(ctx, "agent")
        assert "Routing Rules" in prompt
        assert "billing" in prompt
        assert "billing_agent" in prompt

    def test_includes_routing_rules_condition_variant(self) -> None:
        ctx = {"routing_rules": [{"condition": "tech issue", "specialist": "tech_agent"}]}
        prompt = _build_generation_prompt(ctx, "agent")
        assert "tech issue" in prompt
        assert "tech_agent" in prompt

    def test_includes_policies_section(self) -> None:
        ctx = {"policies": [{"name": "no_pii", "description": "Never share PII"}]}
        prompt = _build_generation_prompt(ctx, "agent")
        assert "Policies" in prompt
        assert "no_pii" in prompt

    def test_includes_specialists_section(self) -> None:
        ctx = {"specialists": ["billing_agent", "tech_agent"]}
        prompt = _build_generation_prompt(ctx, "agent")
        assert "Specialists" in prompt
        assert "billing_agent" in prompt

    def test_always_includes_instructions(self) -> None:
        prompt = _build_generation_prompt({}, "agent")
        assert "Instructions" in prompt
        assert "happy_path" in prompt
        assert "JSON array" in prompt

    def test_omits_empty_sections(self) -> None:
        prompt = _build_generation_prompt({}, "agent")
        assert "Available Tools" not in prompt
        assert "Routing Rules" not in prompt
        assert "Policies" not in prompt
        assert "Specialists" not in prompt

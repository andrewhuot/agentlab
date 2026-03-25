"""Comprehensive tests for AgentSkillGenerator (Track B).

Covers template rendering for all supported gap types and platforms, field
population on GeneratedSkill, the enhance() path, and confidence estimation.
"""
from __future__ import annotations

import uuid

import pytest
import yaml

from agent_skills.generator import AgentSkillGenerator
from agent_skills.types import GeneratedSkill, SkillGap


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_gap(
    gap_type: str = "missing_tool",
    platform: str = "adk",
    frequency: int = 5,
    evidence: list[str] | None = None,
    name: str = "my_tool",
    description: str = "Handles user queries about orders",
    impact_score: float = 0.8,
    context: dict | None = None,
) -> SkillGap:
    """Return a minimal SkillGap for testing."""
    return SkillGap(
        gap_id=uuid.uuid4().hex[:8],
        gap_type=gap_type,
        description=description,
        evidence=evidence or ["conv_001", "conv_002", "conv_003"],
        failure_family="tool_error",
        frequency=frequency,
        impact_score=impact_score,
        suggested_name=name,
        suggested_platform=platform,
        context=context or {},
    )


@pytest.fixture
def generator() -> AgentSkillGenerator:
    return AgentSkillGenerator()


# ---------------------------------------------------------------------------
# ADK templates
# ---------------------------------------------------------------------------


class TestGenerateAdkTool:
    def test_generate_adk_tool_contains_decorator(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_tool", platform="adk", name="get_order_status")
        skill = generator.generate(gap)
        assert "@tool" in skill.source_code

    def test_generate_adk_tool_contains_function_name(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_tool", platform="adk", name="get_order_status")
        skill = generator.generate(gap)
        assert "def get_order_status(" in skill.source_code

    def test_generate_adk_tool_contains_docstring(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(
            gap_type="missing_tool",
            platform="adk",
            name="get_order_status",
            description="Fetches the current status of an order",
        )
        skill = generator.generate(gap)
        assert "Fetches the current status of an order" in skill.source_code

    def test_generate_adk_tool_raises_not_implemented(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_tool", platform="adk", name="check_inventory")
        skill = generator.generate(gap)
        assert "NotImplementedError" in skill.source_code

    def test_generate_adk_tool_embeds_evidence_count(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_tool", platform="adk", frequency=7)
        skill = generator.generate(gap)
        assert "7" in skill.source_code

    def test_generate_adk_tool_uses_custom_params(self, generator: AgentSkillGenerator) -> None:
        ctx = {"parameters": "order_id: str, customer_id: str", "return_type": "str"}
        gap = _make_gap(gap_type="missing_tool", platform="adk", context=ctx)
        skill = generator.generate(gap)
        assert "order_id: str, customer_id: str" in skill.source_code
        assert "-> str:" in skill.source_code

    def test_generate_adk_tool_has_no_config_yaml(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_tool", platform="adk")
        skill = generator.generate(gap)
        assert skill.config_yaml is None

    def test_tool_enhancement_uses_same_template(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="tool_enhancement", platform="adk", name="enhanced_search")
        skill = generator.generate(gap)
        assert "@tool" in skill.source_code
        assert "def enhanced_search(" in skill.source_code


class TestGenerateAdkSubAgent:
    def test_generate_sub_agent_contains_agent_class(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_sub_agent", platform="adk", name="order_agent")
        skill = generator.generate(gap)
        assert "Agent(" in skill.source_code

    def test_generate_sub_agent_contains_name(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_sub_agent", platform="adk", name="order_agent")
        skill = generator.generate(gap)
        assert "order_agent" in skill.source_code

    def test_generate_sub_agent_uses_default_model(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_sub_agent", platform="adk", name="order_agent")
        skill = generator.generate(gap)
        assert "gemini-2.0-flash" in skill.source_code

    def test_generate_sub_agent_uses_custom_model(self, generator: AgentSkillGenerator) -> None:
        ctx = {"model": "gemini-1.5-pro", "tools": ["search_tool"]}
        gap = _make_gap(gap_type="missing_sub_agent", platform="adk", context=ctx)
        skill = generator.generate(gap)
        assert "gemini-1.5-pro" in skill.source_code

    def test_generate_sub_agent_has_no_config_yaml(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_sub_agent", platform="adk", name="order_agent")
        skill = generator.generate(gap)
        assert skill.config_yaml is None


# ---------------------------------------------------------------------------
# CX templates
# ---------------------------------------------------------------------------


class TestGenerateCxPlaybook:
    def test_generate_cx_playbook_has_display_name(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(
            gap_type="missing_playbook_step",
            platform="cx",
            name="order_tracking_playbook",
            description="Guide the user through order tracking",
        )
        skill = generator.generate(gap)
        parsed = yaml.safe_load(skill.config_yaml)
        assert parsed["displayName"] == "order_tracking_playbook"

    def test_generate_cx_playbook_has_goal(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(
            gap_type="missing_playbook_step",
            platform="cx",
            description="Guide the user through order tracking",
        )
        skill = generator.generate(gap)
        parsed = yaml.safe_load(skill.config_yaml)
        assert parsed["goal"] == "Guide the user through order tracking"

    def test_generate_cx_playbook_has_steps(self, generator: AgentSkillGenerator) -> None:
        ctx = {
            "steps": [
                {"text": "Ask for order ID", "tool": None},
                {"text": "Look up order", "tool": "lookup_order"},
            ]
        }
        gap = _make_gap(gap_type="missing_playbook_step", platform="cx", context=ctx)
        skill = generator.generate(gap)
        parsed = yaml.safe_load(skill.config_yaml)
        assert len(parsed["steps"]) == 2

    def test_generate_cx_playbook_has_examples(self, generator: AgentSkillGenerator) -> None:
        ctx = {
            "examples": [
                {"user_input": "Where is my order?", "agent_output": "Let me check that for you."},
            ]
        }
        gap = _make_gap(gap_type="missing_playbook_step", platform="cx", context=ctx)
        skill = generator.generate(gap)
        parsed = yaml.safe_load(skill.config_yaml)
        assert len(parsed["examples"]) == 1

    def test_generate_cx_playbook_has_no_source_code(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_playbook_step", platform="cx")
        skill = generator.generate(gap)
        assert skill.source_code is None


class TestGenerateCxTool:
    def test_generate_cx_tool_has_open_api_spec(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_tool", platform="cx", name="get_weather")
        skill = generator.generate(gap)
        assert "openApiSpec" in skill.config_yaml

    def test_generate_cx_tool_has_display_name(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_tool", platform="cx", name="get_weather")
        skill = generator.generate(gap)
        parsed = yaml.safe_load(skill.config_yaml)
        assert parsed["displayName"] == "get_weather"

    def test_generate_cx_tool_has_description(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(
            gap_type="missing_tool",
            platform="cx",
            name="get_weather",
            description="Returns current weather for a location",
        )
        skill = generator.generate(gap)
        parsed = yaml.safe_load(skill.config_yaml)
        assert parsed["description"] == "Returns current weather for a location"

    def test_generate_cx_tool_has_custom_endpoint(self, generator: AgentSkillGenerator) -> None:
        ctx = {"endpoint": "weather/current", "method": "post"}
        gap = _make_gap(gap_type="missing_tool", platform="cx", context=ctx)
        skill = generator.generate(gap)
        assert "weather/current" in skill.config_yaml

    def test_generate_cx_tool_renders_parameters(self, generator: AgentSkillGenerator) -> None:
        ctx = {
            "parameters": [
                {"name": "city", "location": "query", "type": "string", "description": "City name"},
            ]
        }
        gap = _make_gap(gap_type="missing_tool", platform="cx", context=ctx)
        skill = generator.generate(gap)
        parsed = yaml.safe_load(skill.config_yaml)
        paths = parsed["openApiSpec"]["paths"]
        endpoint_key = list(paths.keys())[0]
        method_key = list(paths[endpoint_key].keys())[0]
        params = paths[endpoint_key][method_key]["parameters"]
        assert params[0]["name"] == "city"

    def test_generate_missing_flow_uses_cx_tool_template(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_flow", platform="cx", name="escalation_flow")
        skill = generator.generate(gap)
        assert "openApiSpec" in skill.config_yaml


class TestGenerateCxIntent:
    def test_generate_cx_intent_has_training_phrases(self, generator: AgentSkillGenerator) -> None:
        ctx = {"training_phrases": ["Where is my order", "Track my package", "Order status"]}
        gap = _make_gap(gap_type="missing_intent", platform="cx", name="track_order", context=ctx)
        skill = generator.generate(gap)
        assert "trainingPhrases" in skill.config_yaml

    def test_generate_cx_intent_renders_all_phrases(self, generator: AgentSkillGenerator) -> None:
        phrases = ["Where is my order", "Track my package", "Order status"]
        ctx = {"training_phrases": phrases}
        gap = _make_gap(gap_type="missing_intent", platform="cx", context=ctx)
        skill = generator.generate(gap)
        parsed = yaml.safe_load(skill.config_yaml)
        rendered_texts = [p["parts"][0]["text"] for p in parsed["trainingPhrases"]]
        for phrase in phrases:
            assert phrase in rendered_texts

    def test_generate_cx_intent_has_display_name(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_intent", platform="cx", name="track_order")
        skill = generator.generate(gap)
        parsed = yaml.safe_load(skill.config_yaml)
        assert parsed["displayName"] == "track_order"

    def test_generate_cx_intent_renders_parameters(self, generator: AgentSkillGenerator) -> None:
        ctx = {
            "parameters": [
                {"id": "order_id", "entity_type": "@sys.number", "is_list": False},
            ]
        }
        gap = _make_gap(gap_type="missing_intent", platform="cx", context=ctx)
        skill = generator.generate(gap)
        parsed = yaml.safe_load(skill.config_yaml)
        assert parsed["parameters"][0]["id"] == "order_id"

    def test_generate_cx_intent_has_no_source_code(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_intent", platform="cx")
        skill = generator.generate(gap)
        assert skill.source_code is None


# ---------------------------------------------------------------------------
# GeneratedSkill field validation
# ---------------------------------------------------------------------------


class TestGeneratedSkillFields:
    def test_skill_id_is_populated(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap()
        skill = generator.generate(gap)
        assert skill.skill_id
        assert len(skill.skill_id) == 12

    def test_gap_id_matches(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap()
        skill = generator.generate(gap)
        assert skill.gap_id == gap.gap_id

    def test_platform_matches(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(platform="adk")
        skill = generator.generate(gap)
        assert skill.platform == "adk"

    def test_skill_type_mapping_tool(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_tool", platform="adk")
        skill = generator.generate(gap)
        assert skill.skill_type == "tool"

    def test_skill_type_mapping_sub_agent(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_sub_agent", platform="adk")
        skill = generator.generate(gap)
        assert skill.skill_type == "sub_agent"

    def test_skill_type_mapping_playbook(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_playbook_step", platform="cx")
        skill = generator.generate(gap)
        assert skill.skill_type == "playbook"

    def test_skill_type_mapping_intent(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_intent", platform="cx")
        skill = generator.generate(gap)
        assert skill.skill_type == "intent"

    def test_skill_type_mapping_flow(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_flow", platform="cx")
        skill = generator.generate(gap)
        assert skill.skill_type == "flow"

    def test_name_matches_gap(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(name="my_fancy_tool")
        skill = generator.generate(gap)
        assert skill.name == "my_fancy_tool"

    def test_description_matches_gap(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(description="Does something useful")
        skill = generator.generate(gap)
        assert skill.description == "Does something useful"

    def test_files_list_has_one_entry(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap()
        skill = generator.generate(gap)
        assert len(skill.files) == 1

    def test_file_path_uses_suggested_name(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(name="special_tool")
        skill = generator.generate(gap)
        assert "special_tool" in skill.files[0].path

    def test_file_is_new_flag(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap()
        skill = generator.generate(gap)
        assert skill.files[0].is_new is True

    def test_eval_criteria_populated(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap()
        skill = generator.generate(gap)
        assert len(skill.eval_criteria) == 2
        metrics = {c["metric"] for c in skill.eval_criteria}
        assert "skill_handles_gap" in metrics
        assert "no_regression" in metrics

    def test_estimated_improvement_is_half_impact_score(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(impact_score=0.6)
        skill = generator.generate(gap)
        assert skill.estimated_improvement == pytest.approx(0.3)

    def test_status_defaults_to_draft(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap()
        skill = generator.generate(gap)
        assert skill.status == "draft"

    def test_created_at_is_set(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap()
        skill = generator.generate(gap)
        assert skill.created_at > 0

    def test_adk_python_file_has_py_extension(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_tool", platform="adk", name="my_tool")
        skill = generator.generate(gap)
        assert skill.files[0].path.endswith(".py")

    def test_cx_yaml_file_has_yaml_extension(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_tool", platform="cx", name="my_cx_tool")
        skill = generator.generate(gap)
        assert skill.files[0].path.endswith(".yaml")

    def test_platform_override_takes_precedence(self, generator: AgentSkillGenerator) -> None:
        """Explicit platform arg overrides gap.suggested_platform."""
        gap = _make_gap(platform="adk")
        skill = generator.generate(gap, platform="cx")
        assert skill.platform == "cx"
        assert skill.config_yaml is not None
        assert skill.source_code is None


# ---------------------------------------------------------------------------
# enhance()
# ---------------------------------------------------------------------------


class TestEnhanceExisting:
    def test_enhance_sets_tool_enhancement_type(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(gap_type="missing_tool", platform="adk", name="search_tool")
        existing = {"name": "search_tool", "source_code": "def search_tool(): pass"}
        skill = generator.enhance(existing, gap)
        assert skill.skill_type == "tool_enhancement"

    def test_enhance_description_mentions_enhancement(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(description="Handle fuzzy product search")
        existing = {"name": "search_tool"}
        skill = generator.enhance(existing, gap)
        assert "Enhancement of existing skill" in skill.description

    def test_enhance_adds_review_notes_when_source_code_present(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(name="search_tool")
        existing = {"name": "search_tool", "source_code": "def search_tool(): pass"}
        skill = generator.enhance(existing, gap)
        assert "search_tool" in skill.review_notes

    def test_enhance_no_review_notes_when_no_source_code(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(name="search_tool")
        existing = {"name": "search_tool"}
        skill = generator.enhance(existing, gap)
        assert skill.review_notes == ""

    def test_enhance_returns_generated_skill(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap()
        skill = generator.enhance({}, gap)
        assert isinstance(skill, GeneratedSkill)


# ---------------------------------------------------------------------------
# Confidence estimation
# ---------------------------------------------------------------------------


class TestConfidenceEstimation:
    def test_confidence_high(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(frequency=15, evidence=[f"c{i}" for i in range(6)])
        skill = generator.generate(gap)
        assert skill.confidence == "high"

    def test_confidence_high_exact_boundary(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(frequency=10, evidence=[f"c{i}" for i in range(5)])
        skill = generator.generate(gap)
        assert skill.confidence == "high"

    def test_confidence_medium_frequency(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(frequency=3, evidence=["c1"])
        skill = generator.generate(gap)
        assert skill.confidence == "medium"

    def test_confidence_medium_high_freq_low_evidence(self, generator: AgentSkillGenerator) -> None:
        """Frequency >= 10 but < 5 evidence → medium, not high."""
        gap = _make_gap(frequency=10, evidence=["c1", "c2"])
        skill = generator.generate(gap)
        assert skill.confidence == "medium"

    def test_confidence_low(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(frequency=1, evidence=["c1"])
        skill = generator.generate(gap)
        assert skill.confidence == "low"

    def test_confidence_low_zero_frequency(self, generator: AgentSkillGenerator) -> None:
        gap = _make_gap(frequency=0, evidence=[])
        skill = generator.generate(gap)
        assert skill.confidence == "low"


# ---------------------------------------------------------------------------
# Template render sanity — all templates render without Jinja2 errors
# ---------------------------------------------------------------------------


class TestAllTemplatesRenderWithoutErrors:
    """Smoke-test every template with its default context variables."""

    @pytest.mark.parametrize(
        "gap_type,platform,name",
        [
            ("missing_tool", "adk", "smoke_adk_tool"),
            ("tool_enhancement", "adk", "smoke_adk_enhancement"),
            ("missing_sub_agent", "adk", "smoke_sub_agent"),
            ("missing_playbook_step", "cx", "smoke_cx_playbook"),
            ("missing_tool", "cx", "smoke_cx_tool"),
            ("missing_flow", "cx", "smoke_cx_flow"),
            ("missing_intent", "cx", "smoke_cx_intent"),
        ],
    )
    def test_template_renders_without_errors(
        self, generator: AgentSkillGenerator, gap_type: str, platform: str, name: str
    ) -> None:
        gap = _make_gap(gap_type=gap_type, platform=platform, name=name)
        # generate() must not raise any Jinja2 or other exception
        skill = generator.generate(gap)
        assert skill is not None
        content = skill.source_code or skill.config_yaml
        assert content
        assert len(content) > 0

    def test_custom_template_dir_is_respected(self, tmp_path) -> None:
        """Generator accepts a custom template_dir pointing to real templates."""
        import shutil
        from pathlib import Path

        src = Path(__file__).parent.parent / "agent_skills" / "templates"
        dst = tmp_path / "custom_templates"
        shutil.copytree(str(src), str(dst))

        custom_gen = AgentSkillGenerator(template_dir=dst)
        gap = _make_gap(gap_type="missing_tool", platform="adk", name="custom_dir_tool")
        skill = custom_gen.generate(gap)
        assert "@tool" in skill.source_code

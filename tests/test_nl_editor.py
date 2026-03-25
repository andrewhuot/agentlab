"""Tests for the NL config editor (optimizer.nl_editor)."""

from __future__ import annotations

import copy
from unittest.mock import MagicMock

import pytest

from optimizer.nl_editor import EditIntent, EditResult, NLEditor


BASE_CONFIG = {
    "prompts": {"root": "You are a helpful agent."},
    "routing": {"rules": [{"specialist": "billing", "keywords": ["bill", "charge"]}]},
    "thresholds": {"max_turns": 20},
    "tools": {"catalog": {"timeout_ms": 5000}},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _config() -> dict:
    """Return a fresh deep copy of BASE_CONFIG for each test."""
    return copy.deepcopy(BASE_CONFIG)


def _editor() -> NLEditor:
    return NLEditor()


# ---------------------------------------------------------------------------
# TestEditIntentParsing
# ---------------------------------------------------------------------------

class TestEditIntentParsing:
    def test_billing_keywords_match_routing(self):
        editor = _editor()
        intent = editor.parse_intent("The billing agent misroutes refund requests.", _config())
        assert "routing.rules" in intent.target_surfaces
        assert intent.change_type == "config_change"

    def test_safety_keywords_match_prompts(self):
        editor = _editor()
        intent = editor.parse_intent("Add guardrails to prevent harmful outputs.", _config())
        assert "prompts.root" in intent.target_surfaces
        assert intent.change_type == "instruction_edit"

    def test_latency_keywords_match_thresholds(self):
        editor = _editor()
        intent = editor.parse_intent("The agent is too slow; reduce latency.", _config())
        assert "thresholds" in intent.target_surfaces
        assert "tools" in intent.target_surfaces
        assert intent.change_type == "config_change"

    def test_tone_keywords_match_prompts(self):
        editor = _editor()
        intent = editor.parse_intent("Make the agent more empathetic and friendly.", _config())
        assert "prompts.root" in intent.target_surfaces
        assert intent.change_type == "instruction_edit"

    def test_routing_keywords_match_routing_rules(self):
        editor = _editor()
        intent = editor.parse_intent("Fix wrong agent routing for transfer requests.", _config())
        assert "routing.rules" in intent.target_surfaces
        assert intent.change_type == "config_change"

    def test_example_keywords_match_examples(self):
        editor = _editor()
        intent = editor.parse_intent("Add a few-shot example for edge cases.", _config())
        assert "examples" in intent.target_surfaces
        assert intent.change_type == "example_add"

    def test_no_match_defaults_to_prompts(self):
        editor = _editor()
        intent = editor.parse_intent("Improve the overall experience.", _config())
        assert intent.target_surfaces == ["prompts.root"]
        assert intent.change_type == "instruction_edit"

    def test_constraints_extracted_maintain_safety(self):
        editor = _editor()
        intent = editor.parse_intent("Improve tone but maintain safety at all times.", _config())
        assert "maintain_safety" in intent.constraints

    def test_constraints_extracted_preserve_existing(self):
        editor = _editor()
        intent = editor.parse_intent("Tweak routing rules, but careful not to break anything.", _config())
        assert "preserve_existing" in intent.constraints

    def test_constraints_extracted_safe_keyword(self):
        editor = _editor()
        intent = editor.parse_intent("Make it safe and reliable.", _config())
        assert "maintain_safety" in intent.constraints

    def test_surfaces_deduplicated(self):
        editor = _editor()
        # "billing" and "routing" both map to routing.rules
        intent = editor.parse_intent("billing routing misroute transfer", _config())
        assert intent.target_surfaces.count("routing.rules") == 1


# ---------------------------------------------------------------------------
# TestEditGeneration
# ---------------------------------------------------------------------------

class TestEditGeneration:
    def test_routing_edit_adds_keywords(self):
        editor = _editor()
        intent = EditIntent(
            description="Handle billing and refund routing",
            target_surfaces=["routing.rules"],
            change_type="config_change",
        )
        new_config = editor.generate_edit(intent, _config())
        keywords = new_config["routing"]["rules"][0]["keywords"]
        assert len(keywords) > len(BASE_CONFIG["routing"]["rules"][0]["keywords"])

    def test_prompt_edit_appends_instruction(self):
        editor = _editor()
        intent = EditIntent(
            description="Make the agent more empathetic and warm",
            target_surfaces=["prompts.root"],
            change_type="instruction_edit",
        )
        new_config = editor.generate_edit(intent, _config())
        root = new_config["prompts"]["root"]
        assert root != BASE_CONFIG["prompts"]["root"]
        assert len(root) > len(BASE_CONFIG["prompts"]["root"])

    def test_threshold_edit_adjusts_values(self):
        editor = _editor()
        intent = EditIntent(
            description="Reduce latency and speed up responses",
            target_surfaces=["thresholds"],
            change_type="config_change",
        )
        new_config = editor.generate_edit(intent, _config())
        assert new_config["thresholds"]["max_turns"] < BASE_CONFIG["thresholds"]["max_turns"]

    def test_tools_edit_adjusts_timeout(self):
        editor = _editor()
        intent = EditIntent(
            description="Improve agent speed and reduce latency",
            target_surfaces=["tools"],
            change_type="config_change",
        )
        new_config = editor.generate_edit(intent, _config())
        assert new_config["tools"]["catalog"]["timeout_ms"] < BASE_CONFIG["tools"]["catalog"]["timeout_ms"]

    def test_examples_edit_adds_example(self):
        editor = _editor()
        intent = EditIntent(
            description="Add a sample conversation",
            target_surfaces=["examples"],
            change_type="example_add",
        )
        new_config = editor.generate_edit(intent, _config())
        assert "examples" in new_config
        assert len(new_config["examples"]) >= 1

    def test_generation_settings_edit_adjusts_tokens(self):
        editor = _editor()
        config = _config()
        config["generation_settings"] = {"max_tokens": 1024, "temperature": 0.7}
        intent = EditIntent(
            description="Reduce cost and token usage",
            target_surfaces=["generation_settings"],
            change_type="config_change",
        )
        new_config = editor.generate_edit(intent, config)
        assert new_config["generation_settings"]["max_tokens"] < 1024

    def test_original_config_not_mutated(self):
        editor = _editor()
        original = _config()
        original_copy = copy.deepcopy(original)
        intent = EditIntent(
            description="Make agent safer and more polite",
            target_surfaces=["prompts.root"],
            change_type="instruction_edit",
        )
        editor.generate_edit(intent, original)
        assert original == original_copy


# ---------------------------------------------------------------------------
# TestApplyAndEval
# ---------------------------------------------------------------------------

class TestApplyAndEval:
    def test_full_pipeline_mock_scores(self):
        editor = _editor()
        result = editor.apply_and_eval(
            description="Make agent more empathetic and warm",
            current_config=_config(),
        )
        assert isinstance(result, EditResult)
        assert result.score_before == pytest.approx(0.84)
        assert result.score_after == pytest.approx(0.86)
        assert result.accepted is True

    def test_accepted_when_score_improves(self):
        editor = _editor()
        result = editor.apply_and_eval(
            description="Add safety guardrails",
            current_config=_config(),
        )
        # Mock scores: 0.84 before, 0.86 after → accepted
        assert result.accepted is True

    def test_dry_run_does_not_deploy(self):
        editor = _editor()
        mock_deployer = MagicMock()
        result = editor.apply_and_eval(
            description="Fix billing routing",
            current_config=_config(),
            deployer=mock_deployer,
        )
        # apply_and_eval itself never calls deployer; that is the route's job
        mock_deployer.deploy.assert_not_called()
        assert result is not None

    def test_edit_result_to_dict(self):
        editor = _editor()
        result = editor.apply_and_eval(
            description="Improve response quality",
            current_config=_config(),
        )
        d = result.to_dict()
        assert "original_config" in d
        assert "new_config" in d
        assert "change_description" in d
        assert "diff_summary" in d
        assert "score_before" in d
        assert "score_after" in d
        assert "accepted" in d

    def test_eval_runner_used_when_provided(self):
        editor = _editor()

        mock_score_before = MagicMock()
        mock_score_before.composite = 0.75
        mock_score_after = MagicMock()
        mock_score_after.composite = 0.80

        mock_runner = MagicMock()
        mock_runner.run.side_effect = [mock_score_before, mock_score_after]

        result = editor.apply_and_eval(
            description="Improve accuracy",
            current_config=_config(),
            eval_runner=mock_runner,
        )
        assert result.score_before == pytest.approx(0.75)
        assert result.score_after == pytest.approx(0.80)
        assert result.accepted is True

    def test_diff_summary_non_empty_on_change(self):
        editor = _editor()
        result = editor.apply_and_eval(
            description="Make agent more empathetic",
            current_config=_config(),
        )
        assert result.diff_summary != ""

    def test_new_config_differs_from_original(self):
        editor = _editor()
        result = editor.apply_and_eval(
            description="Improve tone and be more polite",
            current_config=_config(),
        )
        assert result.new_config != result.original_config

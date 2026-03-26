"""Tests for registry.skill_loader — pack loading, installation, and export."""

from __future__ import annotations

from pathlib import Path


from registry.skill_loader import load_pack, install_pack, install_builtin_packs, export_skill
from registry.skill_store import SkillStore

_PACKS_DIR = Path(__file__).resolve().parents[1] / "registry" / "packs"


def _make_store(tmp_path: Path) -> SkillStore:
    """Return a SkillStore backed by a temp SQLite file."""
    return SkillStore(db_path=str(tmp_path / "skills_test.db"))


# ---------------------------------------------------------------------------
# test_load_universal_pack
# ---------------------------------------------------------------------------

class TestLoadUniversalPack:
    def test_returns_10_skills(self) -> None:
        skills = load_pack(_PACKS_DIR / "universal.yaml")
        assert len(skills) == 10

    def test_each_skill_has_name(self) -> None:
        skills = load_pack(_PACKS_DIR / "universal.yaml")
        for skill in skills:
            assert skill.name, f"Skill missing name: {skill}"

    def test_each_skill_has_category(self) -> None:
        skills = load_pack(_PACKS_DIR / "universal.yaml")
        for skill in skills:
            assert skill.category in {
                "routing", "quality", "safety", "latency", "cost"
            }, f"Unexpected category '{skill.category}' on skill '{skill.name}'"

    def test_each_skill_has_mutations(self) -> None:
        skills = load_pack(_PACKS_DIR / "universal.yaml")
        for skill in skills:
            assert len(skill.mutations) >= 1, f"Skill '{skill.name}' has no mutations"

    def test_expected_skill_names_present(self) -> None:
        skills = load_pack(_PACKS_DIR / "universal.yaml")
        names = {s.name for s in skills}
        expected = {
            "keyword_expansion",
            "instruction_hardening",
            "fewshot_optimization",
            "safety_guardrail_tightening",
            "tool_timeout_tuning",
            "retry_policy_optimization",
            "context_pruning",
            "response_compression",
            "routing_disambiguation",
            "handoff_schema_refinement",
        }
        assert names == expected

    def test_all_platform_universal(self) -> None:
        skills = load_pack(_PACKS_DIR / "universal.yaml")
        for skill in skills:
            assert skill.platform == "universal", (
                f"Expected platform='universal', got '{skill.platform}' on '{skill.name}'"
            )


# ---------------------------------------------------------------------------
# test_load_cx_pack
# ---------------------------------------------------------------------------

class TestLoadCxPack:
    def test_returns_5_skills(self) -> None:
        skills = load_pack(_PACKS_DIR / "cx_agent_studio.yaml")
        assert len(skills) == 5

    def test_all_platform_cx_agent_studio(self) -> None:
        skills = load_pack(_PACKS_DIR / "cx_agent_studio.yaml")
        for skill in skills:
            assert skill.platform == "cx-agent-studio", (
                f"Expected platform='cx-agent-studio', got '{skill.platform}' on '{skill.name}'"
            )

    def test_each_skill_has_mutation(self) -> None:
        skills = load_pack(_PACKS_DIR / "cx_agent_studio.yaml")
        for skill in skills:
            assert len(skill.mutations) >= 1, f"CX skill '{skill.name}' has no mutations"

    def test_each_skill_has_example(self) -> None:
        skills = load_pack(_PACKS_DIR / "cx_agent_studio.yaml")
        for skill in skills:
            assert len(skill.examples) >= 1, f"CX skill '{skill.name}' has no examples"

    def test_each_skill_has_guardrails(self) -> None:
        skills = load_pack(_PACKS_DIR / "cx_agent_studio.yaml")
        for skill in skills:
            assert len(skill.guardrails) >= 2, (
                f"CX skill '{skill.name}' has fewer than 2 guardrails"
            )

    def test_each_skill_has_eval_criterion(self) -> None:
        skills = load_pack(_PACKS_DIR / "cx_agent_studio.yaml")
        for skill in skills:
            assert len(skill.eval_criteria) >= 1, (
                f"CX skill '{skill.name}' has no eval_criteria"
            )

    def test_each_skill_has_trigger(self) -> None:
        skills = load_pack(_PACKS_DIR / "cx_agent_studio.yaml")
        for skill in skills:
            assert len(skill.triggers) >= 1, (
                f"CX skill '{skill.name}' has no triggers"
            )

    def test_expected_skill_names_present(self) -> None:
        skills = load_pack(_PACKS_DIR / "cx_agent_studio.yaml")
        names = {s.name for s in skills}
        expected = {
            "cx_playbook_instruction_tuning",
            "cx_flow_route_optimization",
            "cx_generator_prompt_tuning",
            "cx_entity_extraction_improvement",
            "cx_webhook_latency_reduction",
        }
        assert names == expected


# ---------------------------------------------------------------------------
# test_install_builtin_packs
# ---------------------------------------------------------------------------

class TestInstallBuiltinPacks:
    def test_installs_15_skills_total(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        count = install_builtin_packs(store)
        assert count == 15

    def test_all_skills_retrievable(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        install_builtin_packs(store)
        # spot-check a few skills from each pack
        assert store.get("keyword_expansion") is not None
        assert store.get("handoff_schema_refinement") is not None
        assert store.get("cx_webhook_latency_reduction") is not None
        assert store.get("cx_entity_extraction_improvement") is not None

    def test_universal_skills_are_universal_platform(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        install_builtin_packs(store)
        skill = store.get("context_pruning")
        assert skill is not None
        assert skill.platform == "universal"

    def test_cx_skills_are_cx_platform(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        install_builtin_packs(store)
        skill = store.get("cx_flow_route_optimization")
        assert skill is not None
        assert skill.platform == "cx-agent-studio"


# ---------------------------------------------------------------------------
# test_export_and_reimport_roundtrip
# ---------------------------------------------------------------------------

class TestExportAndReiimportRoundtrip:
    def test_roundtrip_preserves_name(self, tmp_path: Path) -> None:
        skills = load_pack(_PACKS_DIR / "universal.yaml")
        original = skills[0]  # keyword_expansion

        export_path = tmp_path / "exported_skill.yaml"
        export_skill(original, export_path)

        reloaded = load_pack(export_path)
        assert len(reloaded) == 1
        assert reloaded[0].name == original.name

    def test_roundtrip_preserves_category(self, tmp_path: Path) -> None:
        skills = load_pack(_PACKS_DIR / "universal.yaml")
        original = skills[0]

        export_path = tmp_path / "exported_skill.yaml"
        export_skill(original, export_path)

        reloaded = load_pack(export_path)[0]
        assert reloaded.category == original.category

    def test_roundtrip_preserves_platform(self, tmp_path: Path) -> None:
        skills = load_pack(_PACKS_DIR / "universal.yaml")
        original = skills[0]

        export_path = tmp_path / "exported_skill.yaml"
        export_skill(original, export_path)

        reloaded = load_pack(export_path)[0]
        assert reloaded.platform == original.platform

    def test_roundtrip_preserves_mutations(self, tmp_path: Path) -> None:
        skills = load_pack(_PACKS_DIR / "universal.yaml")
        original = skills[0]

        export_path = tmp_path / "exported_skill.yaml"
        export_skill(original, export_path)

        reloaded = load_pack(export_path)[0]
        assert len(reloaded.mutations) == len(original.mutations)
        assert reloaded.mutations[0].name == original.mutations[0].name
        assert reloaded.mutations[0].mutation_type == original.mutations[0].mutation_type

    def test_roundtrip_preserves_guardrails(self, tmp_path: Path) -> None:
        skills = load_pack(_PACKS_DIR / "universal.yaml")
        original = skills[0]

        export_path = tmp_path / "exported_skill.yaml"
        export_skill(original, export_path)

        reloaded = load_pack(export_path)[0]
        assert reloaded.guardrails == original.guardrails

    def test_roundtrip_preserves_eval_criteria(self, tmp_path: Path) -> None:
        skills = load_pack(_PACKS_DIR / "cx_agent_studio.yaml")
        original = skills[0]

        export_path = tmp_path / "cx_exported.yaml"
        export_skill(original, export_path)

        reloaded = load_pack(export_path)[0]
        assert len(reloaded.eval_criteria) == len(original.eval_criteria)
        assert reloaded.eval_criteria[0].metric == original.eval_criteria[0].metric
        assert reloaded.eval_criteria[0].target == original.eval_criteria[0].target

    def test_roundtrip_produces_valid_yaml(self, tmp_path: Path) -> None:
        import yaml as _yaml

        skills = load_pack(_PACKS_DIR / "universal.yaml")
        export_path = tmp_path / "valid_check.yaml"
        export_skill(skills[0], export_path)

        with open(export_path) as f:
            parsed = _yaml.safe_load(f)
        assert "skills" in parsed
        assert isinstance(parsed["skills"], list)


# ---------------------------------------------------------------------------
# test_install_idempotent
# ---------------------------------------------------------------------------

class TestInstallIdempotent:
    def test_first_install_returns_15(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        count = install_builtin_packs(store)
        assert count == 15

    def test_second_install_returns_0(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        install_builtin_packs(store)
        second_count = install_builtin_packs(store)
        assert second_count == 0

    def test_store_still_has_15_after_double_install(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        install_builtin_packs(store)
        install_builtin_packs(store)
        # Verify all 15 are still present and retrievable
        all_skills = store.list()
        assert len(all_skills) == 15

    def test_individual_pack_idempotent(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        pack_path = _PACKS_DIR / "universal.yaml"
        first = install_pack(pack_path, store)
        second = install_pack(pack_path, store)
        assert first == 10
        assert second == 0

    def test_cx_pack_idempotent(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        pack_path = _PACKS_DIR / "cx_agent_studio.yaml"
        first = install_pack(pack_path, store)
        second = install_pack(pack_path, store)
        assert first == 5
        assert second == 0

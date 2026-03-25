"""Tests for AUTOAGENT.md intelligence auto-update."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from core.project_memory import ProjectMemory, INTEL_BEGIN, INTEL_END


class TestIntelligenceUpdate:
    def test_update_appends_when_no_markers(self):
        """First update appends intelligence section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = ProjectMemory(agent_name="Test", platform="test", use_case="testing")
            mem.save(tmpdir)

            mem.update_with_intelligence(
                report={"success_rate": 0.87, "safety_violation_rate": 0.0, "avg_latency_ms": 2100},
                eval_score=0.87,
                recent_changes=[{"version": 7, "delta": 0.02, "description": "Tightened safety"}],
                skill_gaps=[{"description": "No warranty lookup", "count": 8, "handled": 0}],
            )

            content = (Path(tmpdir) / "AUTOAGENT.md").read_text()
            assert INTEL_BEGIN in content
            assert INTEL_END in content
            assert "Score: 0.87" in content
            assert "Tightened safety" in content
            assert "warranty lookup" in content

    def test_update_replaces_existing_markers(self):
        """Subsequent updates replace the intelligence section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = ProjectMemory(agent_name="Test", platform="test", use_case="testing")
            mem.save(tmpdir)

            # First update
            mem.update_with_intelligence(eval_score=0.80)

            # Second update
            mem.update_with_intelligence(eval_score=0.90)

            content = (Path(tmpdir) / "AUTOAGENT.md").read_text()
            assert content.count(INTEL_BEGIN) == 1  # Only one section
            assert "Score: 0.90" in content
            assert "Score: 0.80" not in content

    def test_preserves_user_content(self):
        """User-written content outside markers is preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = ProjectMemory(agent_name="Test", platform="test", use_case="testing")
            mem.known_good_patterns = ["Pattern A works great"]
            mem.save(tmpdir)

            mem.update_with_intelligence(eval_score=0.85)

            content = (Path(tmpdir) / "AUTOAGENT.md").read_text()
            assert "Pattern A works great" in content
            assert INTEL_BEGIN in content

    def test_handles_none_inputs(self):
        """Gracefully handles None/empty inputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = ProjectMemory(agent_name="Test", platform="test", use_case="testing")
            mem.save(tmpdir)
            mem.update_with_intelligence()  # All None

            content = (Path(tmpdir) / "AUTOAGENT.md").read_text()
            assert INTEL_BEGIN in content
            assert "No active issues" in content or "n/a" in content.lower()

    def test_empty_recent_changes(self):
        """Empty recent_changes shows appropriate message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = ProjectMemory(agent_name="Test", platform="test", use_case="testing")
            mem.save(tmpdir)
            mem.update_with_intelligence(eval_score=0.85, recent_changes=[])

            content = (Path(tmpdir) / "AUTOAGENT.md").read_text()
            assert INTEL_BEGIN in content
            assert "No recent changes" in content

    def test_multiple_skill_gaps(self):
        """Multiple skill gaps are listed correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = ProjectMemory(agent_name="Test", platform="test", use_case="testing")
            mem.save(tmpdir)
            mem.update_with_intelligence(
                skill_gaps=[
                    {"description": "No warranty tool", "count": 8, "handled": 0},
                    {"description": "No Spanish support", "count": 5, "handled": 0},
                ],
            )

            content = (Path(tmpdir) / "AUTOAGENT.md").read_text()
            assert "warranty" in content
            assert "Spanish" in content

    def test_markers_appear_once_after_multiple_updates(self):
        """Markers only appear once even after many updates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = ProjectMemory(agent_name="Test", platform="test", use_case="testing")
            mem.save(tmpdir)

            for score in [0.70, 0.75, 0.80, 0.85]:
                mem.update_with_intelligence(eval_score=score)

            content = (Path(tmpdir) / "AUTOAGENT.md").read_text()
            assert content.count(INTEL_BEGIN) == 1
            assert content.count(INTEL_END) == 1
            assert "Score: 0.85" in content

    def test_intel_section_ends_with_end_marker(self):
        """The intelligence section is properly terminated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = ProjectMemory(agent_name="Test", platform="test", use_case="testing")
            mem.save(tmpdir)
            mem.update_with_intelligence(eval_score=0.88)

            content = (Path(tmpdir) / "AUTOAGENT.md").read_text()
            begin_pos = content.index(INTEL_BEGIN)
            end_pos = content.index(INTEL_END)
            assert begin_pos < end_pos

    def test_metrics_formatted_correctly(self):
        """Metrics from report are formatted as expected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = ProjectMemory(agent_name="Test", platform="test", use_case="testing")
            mem.save(tmpdir)
            mem.update_with_intelligence(
                report={
                    "success_rate": 0.95,
                    "safety_violation_rate": 0.01,
                    "avg_latency_ms": 1500,
                },
                eval_score=0.95,
            )

            content = (Path(tmpdir) / "AUTOAGENT.md").read_text()
            assert "95%" in content
            assert "1.5s" in content
            assert "0.01" in content

    def test_recent_changes_delta_format(self):
        """Recent changes are formatted with version and delta."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = ProjectMemory(agent_name="Test", platform="test", use_case="testing")
            mem.save(tmpdir)
            mem.update_with_intelligence(
                recent_changes=[
                    {"version": 3, "delta": 0.05, "description": "Added routing logic"},
                    {"version": 4, "delta": -0.01, "description": "Reverted tone change"},
                ],
            )

            content = (Path(tmpdir) / "AUTOAGENT.md").read_text()
            assert "v3" in content
            assert "+0.05" in content
            assert "routing logic" in content
            assert "v4" in content
            assert "-0.01" in content

    def test_skill_gaps_format(self):
        """Skill gaps include count and handled stats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = ProjectMemory(agent_name="Test", platform="test", use_case="testing")
            mem.save(tmpdir)
            mem.update_with_intelligence(
                skill_gaps=[
                    {"description": "Order tracking", "count": 12, "handled": 3},
                ],
            )

            content = (Path(tmpdir) / "AUTOAGENT.md").read_text()
            assert "Order tracking" in content
            assert "12 user requests" in content
            assert "3 handled" in content

    def test_no_file_path_auto_saves(self, tmp_path: Path):
        """update_with_intelligence auto-saves if file_path not set."""
        mem = ProjectMemory(agent_name="AutoSave", platform="test", use_case="testing")
        # Do NOT call save() first — file_path is empty
        mem.file_path = ""
        mem.save(str(tmp_path))  # Establish the path via save
        mem.file_path = str(tmp_path / "AUTOAGENT.md")

        mem.update_with_intelligence(eval_score=0.77)

        content = (tmp_path / "AUTOAGENT.md").read_text()
        assert "Score: 0.77" in content

    def test_no_active_issues_when_report_has_no_issues(self):
        """Shows 'No active issues' when report contains no issue lists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = ProjectMemory(agent_name="Test", platform="test", use_case="testing")
            mem.save(tmpdir)
            mem.update_with_intelligence(
                report={"success_rate": 0.9, "avg_latency_ms": 800},
            )

            content = (Path(tmpdir) / "AUTOAGENT.md").read_text()
            assert "No active issues" in content

    def test_no_skill_gaps_message(self):
        """Shows 'No skill gaps identified' when skill_gaps is None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mem = ProjectMemory(agent_name="Test", platform="test", use_case="testing")
            mem.save(tmpdir)
            mem.update_with_intelligence(eval_score=0.83)

            content = (Path(tmpdir) / "AUTOAGENT.md").read_text()
            assert "No skill gaps identified" in content

"""Verify web chat panel files exist and contain expected patterns."""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestWebChatPanel:
    def test_diagnosis_chat_component_exists(self):
        path = ROOT / "web" / "src" / "components" / "DiagnosisChat.tsx"
        assert path.exists(), "DiagnosisChat.tsx not found"
        content = path.read_text()
        assert "DiagnosisChat" in content
        assert "ChatMessage" in content

    def test_types_include_chat_message(self):
        path = ROOT / "web" / "src" / "lib" / "types.ts"
        assert path.exists()
        content = path.read_text()
        assert "ChatMessage" in content

    def test_dashboard_includes_chat(self):
        path = ROOT / "web" / "src" / "pages" / "Dashboard.tsx"
        assert path.exists()
        content = path.read_text()
        assert "DiagnosisChat" in content

    def test_chat_component_has_action_buttons(self):
        path = ROOT / "web" / "src" / "components" / "DiagnosisChat.tsx"
        content = path.read_text()
        assert "action" in content.lower()

    def test_chat_component_has_loading_state(self):
        path = ROOT / "web" / "src" / "components" / "DiagnosisChat.tsx"
        content = path.read_text()
        assert "loading" in content or "isPending" in content or "isLoading" in content

    def test_chat_component_has_send_button(self):
        path = ROOT / "web" / "src" / "components" / "DiagnosisChat.tsx"
        content = path.read_text()
        assert "Send" in content

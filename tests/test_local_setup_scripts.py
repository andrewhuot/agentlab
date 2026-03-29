from __future__ import annotations

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_script(name: str) -> str:
    return (REPO_ROOT / name).read_text(encoding="utf-8")


def test_setup_script_installs_editable_deps_with_the_venv_python() -> None:
    setup_text = _read_script("setup.sh")

    assert re.search(
        r'"\$VENV_PYTHON"\s+-m\s+pip\s+install\s+-e\s+\'\.\[dev\]\'',
        setup_text,
    )


def test_start_script_launches_uvicorn_with_the_venv_python() -> None:
    start_text = _read_script("start.sh")

    assert re.search(
        r'"\$VENV_PYTHON"\s+-m\s+uvicorn\s+api\.server:app',
        start_text,
    )


def test_scripts_validate_the_activate_path_before_sourcing() -> None:
    setup_text = _read_script("setup.sh")
    start_text = _read_script("start.sh")

    assert 'source "$VENV_ACTIVATE"' in setup_text
    assert 'source "$VENV_ACTIVATE"' in start_text
    assert '[[ ! -f "$VENV_ACTIVATE" ]]' in setup_text
    assert '[[ ! -f "$VENV_ACTIVATE" ]]' in start_text

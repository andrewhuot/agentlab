"""Canonical skill store path configuration.

Both CLI and UI should import SKILL_DB_PATH from here to ensure they read/write
the same SQLite database.
"""

from __future__ import annotations

import os
from pathlib import Path

# Single canonical path for all skill data.
# Previously, CLI defaulted to .autoagent/skills.db and UI to .autoagent/core_skills.db.
SKILL_DB_PATH = Path(
    os.environ.get("AUTOAGENT_SKILL_DB", ".autoagent/skills.db")
)

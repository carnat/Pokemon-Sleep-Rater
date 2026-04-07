"""Tests for pokemon_db/db.py — subskills_to_string formatting."""

import sys
from unittest.mock import MagicMock

# Stub out Google Cloud and database modules before importing db.
for _mod in (
    "google",
    "google.cloud",
    "google.cloud.sql",
    "google.cloud.sql.connector",
    "google.auth",
    "google.api_core",
    "pg8000",
    "sqlalchemy",
):
    sys.modules.setdefault(_mod, MagicMock())

from pokemon_db.db import subskills_to_string


# ---------------------------------------------------------------------------
# Basic formatting
# ---------------------------------------------------------------------------

class TestSubskillsToString:
    def test_five_skills_display_order(self):
        """All 5 skills should appear in Lv. ascending order (10, 25, 50, 75, 100)."""
        results = {
            "Skill A": 5,   # detection idx 0 → Lv.10
            "Skill B": 4,   # detection idx 1 → Lv.50
            "Skill C": 3,   # detection idx 2 → Lv.100
            "Skill D": 2,   # detection idx 3 → Lv.25
            "Skill E": 1,   # detection idx 4 → Lv.75
        }
        output = subskills_to_string(results)
        lines = output.split("\n")
        assert len(lines) == 5

        # Display order should be: Lv.10 (idx 0), Lv.25 (idx 3), Lv.50 (idx 1), Lv.75 (idx 4), Lv.100 (idx 2)
        assert "[Lv. 10] Skill A: 5" in lines[0]
        assert "[Lv. 25] Skill D: 2" in lines[1]
        assert "[Lv. 50] Skill B: 4" in lines[2]
        assert "[Lv. 75] Skill E: 1" in lines[3]
        assert "[Lv. 100] Skill C: 3" in lines[4]

    def test_three_skills_only(self):
        """When fewer than 5 skills are present, missing indices are skipped."""
        results = {
            "Skill A": 5,   # idx 0
            "Skill B": 4,   # idx 1
            "Skill C": 3,   # idx 2
        }
        output = subskills_to_string(results)
        lines = output.split("\n")
        # Order [0, 3, 1, 4, 2]: idx 0 present, idx 3 missing, idx 1 present, idx 4 missing, idx 2 present
        assert len(lines) == 3
        assert "[Lv. 10]" in lines[0]
        assert "[Lv. 50]" in lines[1]
        assert "[Lv. 100]" in lines[2]

    def test_empty_results(self):
        output = subskills_to_string({})
        assert output == ""

    def test_one_skill(self):
        results = {"Berry Finding S": 5}
        output = subskills_to_string(results)
        lines = output.split("\n")
        assert len(lines) == 1
        assert "[Lv. 10]" in lines[0]
        assert "Berry Finding S: 5" in lines[0]


# ---------------------------------------------------------------------------
# Locked skills
# ---------------------------------------------------------------------------

class TestLockedSkills:
    def test_locked_skill_shows_lock_emoji(self):
        results = {
            "Skill A": 5,
            "Skill B": 0,
        }
        locked = {"Skill B"}
        output = subskills_to_string(results, locked)
        assert "🔒 not yet unlocked" in output
        assert "Skill B: 🔒" in output

    def test_unlocked_skill_shows_value(self):
        results = {
            "Skill A": 5,
            "Skill B": 4,
        }
        locked = set()
        output = subskills_to_string(results, locked)
        assert "🔒" not in output

    def test_mixed_locked_and_unlocked(self):
        results = {
            "Skill A": 5,
            "Skill B": 0,
            "Skill C": 0,
            "Skill D": 0,
            "Skill E": 0,
        }
        locked = {"Skill B", "Skill C", "Skill D", "Skill E"}
        output = subskills_to_string(results, locked)
        lines = output.split("\n")
        # First line (Skill A, idx 0 → Lv.10) should show value
        assert "🔒" not in lines[0]
        # Other lines should show locked
        for line in lines[1:]:
            assert "🔒 not yet unlocked" in line

    def test_none_locked_skills_defaults_to_empty(self):
        results = {"Skill A": 5}
        output = subskills_to_string(results, None)
        assert "🔒" not in output
        assert "Skill A: 5" in output

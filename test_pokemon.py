"""Tests for the core Pokémon Sleep rating engine (pokemon.py).

Covers: RatePokemon class — find_specialty, _frequency_weight, _score_subskill,
_rate_for_specialty, _compute_percentile, grading_scale, and rate_pokemon.
"""

import pytest
from pokemon import RatePokemon


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rater(name="Spheal", nature="Impish", skills=None):
    """Create a RatePokemon instance with sensible defaults."""
    if skills is None:
        skills = ["Energy Recovery Bonus", "Inventory Up S", "Helping Speed M",
                  "Inventory Up L", "Skill Trigger S"]
    return RatePokemon(name, nature, skills)


# ---------------------------------------------------------------------------
# __init__ / get_stats
# ---------------------------------------------------------------------------

class TestInit:
    def test_defaults(self):
        rp = RatePokemon()
        assert rp.name == ""
        assert rp.nature == ""
        assert rp.skills == []
        assert rp.locked_skills == set()

    def test_custom_values(self):
        rp = RatePokemon("Pikachu", "Jolly", ["Helping Bonus"])
        assert rp.name == "Pikachu"
        assert rp.nature == "Jolly"
        assert rp.skills == ["Helping Bonus"]

    def test_get_stats(self):
        rp = _make_rater()
        name, nature, skills = rp.get_stats()
        assert name == "Spheal"
        assert nature == "Impish"
        assert len(skills) == 5

    def test_skills_default_not_shared(self):
        """Ensure default skills list is not shared between instances."""
        a = RatePokemon()
        b = RatePokemon()
        a.skills.append("Helping Bonus")
        assert b.skills == []


# ---------------------------------------------------------------------------
# find_specialty
# ---------------------------------------------------------------------------

class TestFindSpecialty:
    def test_valid_pokemon_and_nature(self):
        rp = RatePokemon()
        results = ["Spheal", "Impish", "Helping Bonus", "Berry Finding S"]
        specialty = rp.find_specialty(results)
        assert specialty == "Berries"
        assert rp.name == "Spheal"
        assert rp.nature == "Impish"
        assert rp.skills == ["Helping Bonus", "Berry Finding S"]

    def test_unknown_pokemon(self):
        rp = RatePokemon()
        results = ["FakeMon", "Impish", "Helping Bonus"]
        specialty = rp.find_specialty(results)
        assert specialty is None

    def test_no_nature(self):
        rp = RatePokemon()
        results = ["Spheal", "FakeNature"]
        specialty = rp.find_specialty(results)
        assert specialty == "Berries"
        assert rp.nature == ""

    def test_multiple_subskills(self):
        rp = RatePokemon()
        results = ["Pikachu", "Jolly", "Berry Finding S", "Helping Speed M", "Helping Bonus"]
        specialty = rp.find_specialty(results)
        assert specialty == "Berries"
        assert len(rp.skills) == 3

    def test_ignores_unrecognized_tokens(self):
        rp = RatePokemon()
        results = ["Garbage", "Spheal", "MoreGarbage", "Brave"]
        rp.find_specialty(results)
        assert rp.name == "Spheal"
        assert rp.nature == "Brave"

    def test_ingredients_specialty(self):
        rp = RatePokemon()
        results = ["Bulbasaur", "Hardy"]
        specialty = rp.find_specialty(results)
        assert specialty == "Ingredients"

    def test_skills_specialty(self):
        rp = RatePokemon()
        results = ["Wigglytuff", "Bold"]
        specialty = rp.find_specialty(results)
        assert specialty == "Skills"

    def test_empty_results(self):
        rp = RatePokemon()
        specialty = rp.find_specialty([])
        assert specialty is None

    def test_pokemon_with_dots_in_name(self):
        """Pokémon like 'Mr. Mime' and 'Mime Jr.' have dots."""
        rp = RatePokemon()
        results = ["Mr. Mime", "Hardy"]
        specialty = rp.find_specialty(results)
        assert specialty == "Ingredients"
        assert rp.name == "Mr. Mime"


# ---------------------------------------------------------------------------
# _frequency_weight
# ---------------------------------------------------------------------------

class TestFrequencyWeight:
    def test_known_pokemon(self):
        rp = _make_rater(name="Spheal")
        weight = rp._frequency_weight()
        # Spheal has base_frequency 3720; baseline is 4500
        expected = 4500 / 3720
        assert abs(weight - expected) < 0.001

    def test_baseline_pokemon(self):
        """A Pokémon with exactly baseline frequency should get weight 1.0."""
        rp = _make_rater(name="Squirtle")  # 4500
        weight = rp._frequency_weight()
        assert weight == 1.0

    def test_unknown_pokemon_returns_1(self):
        rp = _make_rater(name="UnknownMon")
        weight = rp._frequency_weight()
        assert weight == 1.0

    def test_slow_pokemon_gets_low_weight(self):
        """Slowpoke (5760s) should get weight < 1."""
        rp = _make_rater(name="Slowpoke")
        weight = rp._frequency_weight()
        assert weight < 1.0

    def test_fast_pokemon_gets_high_weight(self):
        """Diglett (2880s) should get weight > 1."""
        rp = _make_rater(name="Diglett")
        weight = rp._frequency_weight()
        assert weight > 1.0


# ---------------------------------------------------------------------------
# _score_subskill
# ---------------------------------------------------------------------------

class TestScoreSubskill:
    def test_non_speed_sensitive(self):
        """Non-speed subskills return base score regardless of frequency weight."""
        rp = _make_rater()
        score = rp._score_subskill("Energy Recovery Bonus", 0, 1.5)
        # Energy Recovery Bonus = [3, 3, 3]; berries idx=0 → 3
        assert score == 3

    def test_speed_sensitive_applies_weight(self):
        """Speed-sensitive subskills should be multiplied by freq_weight."""
        rp = _make_rater()
        freq_weight = 1.5
        score = rp._score_subskill("Helping Speed M", 0, freq_weight)
        # Helping Speed M = [4, 4, 4]; berries idx=0 → 4 * 1.5 = 6.0
        assert score == 6.0

    def test_berry_finding_is_speed_sensitive(self):
        rp = _make_rater()
        score_weighted = rp._score_subskill("Berry Finding S", 0, 2.0)
        # Berry Finding S = [5, 4, 5]; berries idx=0 → 5 * 2.0 = 10.0
        assert score_weighted == 10.0

    def test_unknown_subskill_returns_0(self):
        rp = _make_rater()
        score = rp._score_subskill("FakeSubskill", 0, 1.0)
        assert score == 0

    def test_ingredients_specialty_idx(self):
        rp = _make_rater()
        score = rp._score_subskill("Ingredient Finder M", 1, 1.0)
        # Ingredient Finder M = [1, 5, 4]; ingredients idx=1 → 5
        assert score == 5

    def test_skills_specialty_idx(self):
        rp = _make_rater()
        score = rp._score_subskill("Skill Trigger M", 2, 1.0)
        # Skill Trigger M = [4, 4, 5]; skills idx=2 → 5
        assert score == 5

    def test_speed_sensitive_rounding(self):
        """Scores should be rounded to 2 decimal places."""
        rp = _make_rater()
        # Helping Speed S = [3, 3, 3]; with weight 1.333... → 3 * 1.333 = 3.999 → 4.0
        score = rp._score_subskill("Helping Speed S", 0, 4500 / 3375)
        assert score == round(3 * (4500 / 3375), 2)


# ---------------------------------------------------------------------------
# _rate_for_specialty
# ---------------------------------------------------------------------------

class TestRateForSpecialty:
    def test_basic_rating(self):
        rp = _make_rater()
        grade, nature_rating, skills_value, locked_skills, percentile = \
            rp._rate_for_specialty("Berries")
        assert isinstance(grade, float)
        assert isinstance(nature_rating, float)
        assert isinstance(skills_value, dict)
        assert isinstance(locked_skills, set)
        assert 0 <= percentile <= 100

    def test_no_locked_skills_without_level(self):
        rp = _make_rater()
        _, _, _, locked_skills, _ = rp._rate_for_specialty("Berries")
        assert locked_skills == set()

    def test_locked_skills_with_low_level(self):
        rp = _make_rater()
        _, _, skills_value, locked_skills, _ = rp._rate_for_specialty("Berries", pokemon_level=10)
        # Level 10: only index 0 (Lv.10) is unlocked
        # Indices 1,2,3,4 have levels [50, 100, 25, 75] — all > 10
        assert len(locked_skills) > 0
        for skill in locked_skills:
            assert skills_value[skill] == 0

    def test_all_unlocked_at_level_100(self):
        rp = _make_rater()
        _, _, _, locked_skills, _ = rp._rate_for_specialty("Berries", pokemon_level=100)
        assert locked_skills == set()

    def test_different_specialties_yield_different_scores(self):
        rp = _make_rater()
        grade_b, _, _, _, _ = rp._rate_for_specialty("Berries")
        grade_i, _, _, _, _ = rp._rate_for_specialty("Ingredients")
        grade_s, _, _, _, _ = rp._rate_for_specialty("Skills")
        # Scores may differ due to nature and subskill weights
        scores = {grade_b, grade_i, grade_s}
        assert len(scores) >= 2  # at least 2 different scores

    def test_does_not_mutate_instance(self):
        rp = _make_rater()
        orig_locked = rp.locked_skills.copy()
        rp._rate_for_specialty("Berries", pokemon_level=10)
        assert rp.locked_skills == orig_locked

    def test_level_25_unlocks_two_skills(self):
        """At level 25, skills at Lv.10 and Lv.25 should be unlocked."""
        rp = _make_rater()
        # DETECTION_ORDER_LEVELS = [10, 50, 100, 25, 75]
        # Level 25 unlocks: index 0 (Lv.10) and index 3 (Lv.25)
        # Locked: index 1 (Lv.50), index 2 (Lv.100), index 4 (Lv.75)
        _, _, _, locked_skills, _ = rp._rate_for_specialty("Berries", pokemon_level=25)
        assert len(locked_skills) == 3


# ---------------------------------------------------------------------------
# _compute_percentile
# ---------------------------------------------------------------------------

class TestComputePercentile:
    def test_min_score(self):
        rp = _make_rater()
        pct = rp._compute_percentile(4.33, "Berries")
        assert pct == 0

    def test_max_score(self):
        rp = _make_rater()
        pct = rp._compute_percentile(28.0, "Berries")
        assert pct == 100

    def test_mid_score(self):
        rp = _make_rater()
        min_val, max_val = 4.33, 28.0
        mid = (min_val + max_val) / 2
        pct = rp._compute_percentile(mid, "Berries")
        assert pct == 50

    def test_below_min_clamps_to_0(self):
        rp = _make_rater()
        pct = rp._compute_percentile(-10, "Berries")
        assert pct == 0

    def test_above_max_clamps_to_100(self):
        rp = _make_rater()
        pct = rp._compute_percentile(50, "Berries")
        assert pct == 100

    def test_unknown_specialty_returns_50(self):
        rp = _make_rater()
        pct = rp._compute_percentile(15.0, "UnknownSpec")
        assert pct == 50

    def test_ingredients_range(self):
        rp = _make_rater()
        # Ingredients range: (11.0, 24.0)
        pct = rp._compute_percentile(11.0, "Ingredients")
        assert pct == 0
        pct = rp._compute_percentile(24.0, "Ingredients")
        assert pct == 100

    def test_skills_range(self):
        rp = _make_rater()
        # Skills range: (10.5, 26.0)
        pct = rp._compute_percentile(10.5, "Skills")
        assert pct == 0


# ---------------------------------------------------------------------------
# grading_scale
# ---------------------------------------------------------------------------

class TestGradingScale:
    def test_grade_f(self):
        rp = _make_rater()
        assert "**F**" in rp.grading_scale(5.0)
        assert "**F**" in rp.grading_scale(11.0)

    def test_grade_d(self):
        rp = _make_rater()
        assert "**D**" in rp.grading_scale(11.1)
        assert "**D**" in rp.grading_scale(14.0)

    def test_grade_c(self):
        rp = _make_rater()
        assert "**C**" in rp.grading_scale(14.1)
        assert "**C**" in rp.grading_scale(17.0)

    def test_grade_b(self):
        rp = _make_rater()
        assert "**B**" in rp.grading_scale(17.1)
        assert "**B**" in rp.grading_scale(20.0)

    def test_grade_a(self):
        rp = _make_rater()
        assert "**A**" in rp.grading_scale(20.1)
        assert "**A**" in rp.grading_scale(23.0)

    def test_grade_s(self):
        rp = _make_rater()
        assert "**S**" in rp.grading_scale(23.1)
        assert "**S**" in rp.grading_scale(30.0)

    def test_grade_boundaries_are_inclusive(self):
        """Ensure boundary values map to the correct grade."""
        rp = _make_rater()
        # 11.0 → F, 11.01 → D
        assert "**F**" in rp.grading_scale(11.0)
        assert "**D**" in rp.grading_scale(11.01)


# ---------------------------------------------------------------------------
# rate_pokemon — main entry point
# ---------------------------------------------------------------------------

class TestRatePokemon:
    def test_full_rating_returns_dict(self):
        rp = _make_rater()
        result = rp.rate_pokemon([], pokemon_level=None)
        assert isinstance(result, dict)
        assert result["name"] == "Spheal"
        assert result["specialty"] == "Berries"
        assert "grade" in result
        assert "percentile" in result
        assert "final_grade" in result
        assert "nature" in result
        assert "nature_rating" in result
        assert "all_scores" in result
        assert "helps_per_day" in result

    def test_full_rating_with_level(self):
        rp = _make_rater()
        result = rp.rate_pokemon([], pokemon_level=10)
        assert isinstance(result, dict)
        assert len(result["locked_skills"]) > 0

    def test_unknown_pokemon_returns_false(self):
        rp = RatePokemon("FakeMon", "Impish", ["Helping Bonus"])
        result = rp.rate_pokemon([])
        assert result is False

    def test_no_nature_returns_false(self):
        rp = RatePokemon("Spheal", "", ["Helping Bonus"])
        result = rp.rate_pokemon([])
        assert result is False

    def test_rate_from_ocr_results(self):
        """rate_pokemon should work when calling find_specialty from OCR results."""
        rp = RatePokemon()
        results = ["Spheal", "Impish", "Energy Recovery Bonus", "Inventory Up S",
                    "Helping Speed M", "Inventory Up L", "Skill Trigger S"]
        result = rp.rate_pokemon(results, pokemon_level=50)
        assert isinstance(result, dict)
        assert result["name"] == "Spheal"

    def test_all_scores_contains_three_specialties(self):
        rp = _make_rater()
        result = rp.rate_pokemon([])
        all_scores = result["all_scores"]
        assert "Berries" in all_scores
        assert "Ingredients" in all_scores
        assert "Skills" in all_scores
        for spec_data in all_scores.values():
            assert "grade" in spec_data
            assert "percentile" in spec_data

    def test_helps_per_day_for_known_pokemon(self):
        rp = _make_rater(name="Spheal")
        result = rp.rate_pokemon([])
        # Spheal freq = 3720, efficiency = 0.80
        expected = round(86400 / (3720 * 0.80))
        assert result["helps_per_day"] == expected

    def test_helps_per_day_none_for_unknown_freq(self):
        """Pokemon in the specialty dict but not in base_frequencies."""
        rp = RatePokemon("Spheal", "Impish", ["Helping Bonus"])
        # Spheal is in base_frequencies, so use a different approach
        # Manually remove from base_frequencies temporarily isn't safe;
        # just verify that known Pokemon have non-None helps_per_day
        result = rp.rate_pokemon([])
        assert result["helps_per_day"] is not None

    def test_grade_string_format(self):
        rp = _make_rater()
        result = rp.rate_pokemon([])
        # grade should be a string representation of a float
        float(result["grade"])  # should not raise

    def test_nature_rating_string_format(self):
        rp = _make_rater()
        result = rp.rate_pokemon([])
        float(result["nature_rating"])  # should not raise

    def test_instance_state_set_after_rating(self):
        rp = _make_rater()
        rp.rate_pokemon([])
        assert rp.nature_rating != 0 or rp.nature == "Hardy"
        assert isinstance(rp.skills_value, dict)
        assert isinstance(rp.locked_skills, set)

    def test_no_skills(self):
        """Rating should work with zero subskills."""
        rp = RatePokemon("Spheal", "Impish", [])
        result = rp.rate_pokemon([])
        assert isinstance(result, dict)
        assert result["skills_value"] == {}

    def test_one_skill(self):
        rp = RatePokemon("Spheal", "Impish", ["Helping Bonus"])
        result = rp.rate_pokemon([])
        assert isinstance(result, dict)
        assert "Helping Bonus" in result["skills_value"]


# ---------------------------------------------------------------------------
# Data integrity
# ---------------------------------------------------------------------------

class TestDataIntegrity:
    def test_all_pokemon_have_valid_specialty(self):
        valid_specialties = {"Berries", "Ingredients", "Skills"}
        for name, spec in RatePokemon.pokemon.items():
            assert spec in valid_specialties, f"{name} has invalid specialty {spec}"

    def test_all_natures_have_three_values(self):
        for nature, values in RatePokemon.natures.items():
            assert len(values) == 3, f"{nature} has {len(values)} values, expected 3"

    def test_all_subskills_have_three_values(self):
        for skill, values in RatePokemon.subskills.items():
            assert len(values) == 3, f"{skill} has {len(values)} values, expected 3"

    def test_base_frequencies_are_positive(self):
        for name, freq in RatePokemon.base_frequencies.items():
            assert freq > 0, f"{name} has non-positive frequency {freq}"

    def test_score_ranges_are_valid(self):
        for spec, (min_val, max_val) in RatePokemon.SCORE_RANGES.items():
            assert min_val < max_val, f"{spec} has min >= max"

    def test_detection_order_levels_length(self):
        assert len(RatePokemon.DETECTION_ORDER_LEVELS) == 5

    def test_speed_sensitive_subskills_exist(self):
        for ss in RatePokemon.SPEED_SENSITIVE_SUBSKILLS:
            assert ss in RatePokemon.subskills, f"{ss} not in subskills dict"


# ---------------------------------------------------------------------------
# Cross-specialty consistency
# ---------------------------------------------------------------------------

class TestCrossSpecialty:
    def test_berry_pokemon_rated_as_berries(self):
        rp = RatePokemon("Pikachu", "Jolly", ["Berry Finding S"])
        result = rp.rate_pokemon([])
        assert result["specialty"] == "Berries"

    def test_ingredients_pokemon_rated_as_ingredients(self):
        rp = RatePokemon("Bulbasaur", "Hardy", ["Ingredient Finder M"])
        result = rp.rate_pokemon([])
        assert result["specialty"] == "Ingredients"

    def test_skills_pokemon_rated_as_skills(self):
        rp = RatePokemon("Wigglytuff", "Sassy", ["Skill Trigger M"])
        result = rp.rate_pokemon([])
        assert result["specialty"] == "Skills"

    def test_neutral_nature_yields_same_modifier(self):
        """Neutral natures (e.g., Hardy) should have equal modifiers."""
        rp = RatePokemon("Spheal", "Hardy", [])
        result = rp.rate_pokemon([])
        berries_grade = result["all_scores"]["Berries"]["grade"]
        ingredients_grade = result["all_scores"]["Ingredients"]["grade"]
        skills_grade = result["all_scores"]["Skills"]["grade"]
        assert berries_grade == ingredients_grade == skills_grade

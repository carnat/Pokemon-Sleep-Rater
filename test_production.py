"""Tests for curated data loading and production recommendations."""

from pokemon import RatePokemon
from pokemon_data import SLEEP_DATA, validate_sleep_data
from production import ProductionInputs, calculate_production, recommend


def test_snapshot_validates():
    validate_sleep_data(SLEEP_DATA)


def test_known_species_have_required_production_fields():
    for name in ("Pikachu", "Bulbasaur", "Wigglytuff"):
        species = SLEEP_DATA.species[name]
        assert species["base_frequency"] > 0
        assert 0 <= species["ingredient_rate"] <= 1
        assert 0 <= species["skill_rate"] <= 1


def test_speed_nature_and_helping_speed_raise_production():
    base = calculate_production("Pikachu", "Hardy", [], ProductionInputs(level=30))
    fast = calculate_production("Pikachu", "Jolly", ["Helping Speed M"], ProductionInputs(level=30))
    assert fast["helps_per_day"] > base["helps_per_day"]
    assert fast["production_score"] > base["production_score"]


def test_ingredient_finder_helps_ingredient_specialist():
    base = calculate_production("Bulbasaur", "Hardy", [], ProductionInputs(level=30))
    boosted = calculate_production(
        "Bulbasaur",
        "Modest",
        ["Ingredient Finder M"],
        ProductionInputs(level=30),
    )
    assert boosted["ingredients_per_day"] > base["ingredients_per_day"]


def test_skill_trigger_helps_skill_specialist():
    base = calculate_production("Wigglytuff", "Hardy", [], ProductionInputs(level=30))
    boosted = calculate_production(
        "Wigglytuff",
        "Sassy",
        ["Skill Trigger M"],
        ProductionInputs(level=30),
    )
    assert boosted["skill_triggers_per_day"] > base["skill_triggers_per_day"]


def test_recommendation_thresholds():
    keep = recommend(95, "Berries", {"production_score": 95})
    consider = recommend(50, "Berries", {"production_score": 50})
    release = recommend(10, "Berries", {"production_score": 10})
    assert keep["recommendation"] == "Keep"
    assert consider["recommendation"] == "Consider"
    assert release["recommendation"] == "Release"


def test_rate_pokemon_includes_new_fields():
    result = RatePokemon("Pikachu", "Jolly", ["Berry Finding S"]).rate_pokemon([], pokemon_level=30)
    assert result["production_score"] is not None
    assert result["recommendation"] in {"Keep", "Consider", "Release"}
    assert result["data_version"] == SLEEP_DATA.version
    assert isinstance(result["assumptions_used"], list)

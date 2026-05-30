"""Production-oriented Pokemon Sleep scoring and recommendations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pokemon_data import SLEEP_DATA, SleepData


SPECIALTIES = ("Berries", "Ingredients", "Skills")


NATURE_EFFECTS = {
    "Lonely": {"speed": 1.1, "energy": 0.8},
    "Brave": {"speed": 1.1, "exp": 0.8},
    "Adamant": {"speed": 1.1, "ingredient": 0.8},
    "Naughty": {"speed": 1.1, "skill": 0.8},
    "Bold": {"speed": 0.9, "energy": 1.2},
    "Relaxed": {"energy": 1.2, "exp": 0.8},
    "Impish": {"energy": 1.2, "ingredient": 0.8},
    "Lax": {"energy": 1.2, "skill": 0.8},
    "Timid": {"speed": 0.9, "exp": 1.2},
    "Hasty": {"speed": 1.1, "energy": 0.8},
    "Jolly": {"speed": 1.1, "ingredient": 0.8},
    "Naive": {"speed": 1.1, "skill": 0.8},
    "Modest": {"speed": 0.9, "ingredient": 1.2},
    "Mild": {"ingredient": 1.2, "energy": 0.8},
    "Quiet": {"ingredient": 1.2, "exp": 0.8},
    "Rash": {"ingredient": 1.2, "skill": 0.8},
    "Calm": {"speed": 0.9, "skill": 1.2},
    "Gentle": {"skill": 1.2, "energy": 0.8},
    "Sassy": {"skill": 1.2, "exp": 0.8},
    "Careful": {"skill": 1.2, "ingredient": 0.8},
}


SUBSKILL_EFFECTS = {
    "Berry Finding S": {"berry_count": 1.0},
    "Helping Bonus": {"speed_pct": 0.05},
    "Helping Speed S": {"speed_pct": 0.07},
    "Helping Speed M": {"speed_pct": 0.14},
    "Ingredient Finder S": {"ingredient_pct": 0.18},
    "Ingredient Finder M": {"ingredient_pct": 0.36},
    "Skill Trigger S": {"skill_pct": 0.18},
    "Skill Trigger M": {"skill_pct": 0.36},
    "Inventory Up S": {"inventory_value": 0.02},
    "Inventory Up M": {"inventory_value": 0.03},
    "Inventory Up L": {"inventory_value": 0.04},
    "Skill Level Up S": {"skill_value": 0.05},
    "Skill Level Up M": {"skill_value": 0.10},
}


@dataclass(frozen=True)
class ProductionInputs:
    level: int | None = None
    ingredient_spread: list[str] | None = None
    main_skill_level: int | None = None
    energy: int | None = None
    good_camp: bool = False
    area: str | None = None
    favored_berry: bool | None = None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _unlocked_skills(skills: list[str], level: int | None, data: SleepData) -> list[str]:
    if level is None:
        return skills
    unlocked = []
    for idx, skill in enumerate(skills):
        unlock_level = (
            data.detection_order_levels[idx]
            if idx < len(data.detection_order_levels)
            else 10
        )
        if level >= unlock_level:
            unlocked.append(skill)
    return unlocked


def calculate_production(
    name: str,
    nature: str,
    skills: list[str],
    inputs: ProductionInputs | None = None,
    data: SleepData = SLEEP_DATA,
) -> dict[str, Any]:
    inputs = inputs or ProductionInputs()
    species = data.species.get(name)
    if not species:
        return {}

    defaults = data.production_defaults
    level = inputs.level or defaults["default_level"]
    energy = inputs.energy if inputs.energy is not None else defaults["default_energy"]
    base_frequency = species.get("base_frequency")
    if not base_frequency:
        return {}

    nature_effect = NATURE_EFFECTS.get(nature, {})
    unlocked_skills = _unlocked_skills(skills, inputs.level, data)

    speed_multiplier = nature_effect.get("speed", 1.0)
    ingredient_multiplier = nature_effect.get("ingredient", 1.0)
    skill_multiplier = nature_effect.get("skill", 1.0)
    berry_bonus = 0.0
    skill_value_bonus = 0.0
    inventory_value = 0.0

    for skill in unlocked_skills:
        effect = SUBSKILL_EFFECTS.get(skill, {})
        speed_multiplier *= 1 + effect.get("speed_pct", 0.0)
        ingredient_multiplier *= 1 + effect.get("ingredient_pct", 0.0)
        skill_multiplier *= 1 + effect.get("skill_pct", 0.0)
        berry_bonus += effect.get("berry_count", 0.0)
        skill_value_bonus += effect.get("skill_value", 0.0)
        inventory_value += effect.get("inventory_value", 0.0)

    level_multiplier = 1 - max(0, level - 1) * 0.002
    energy_multiplier = 0.55 + (_clamp(energy, 0, 100) / 100) * 0.45
    camp_multiplier = defaults["good_camp_multiplier"] if inputs.good_camp else 1.0
    effective_frequency = base_frequency * level_multiplier / max(speed_multiplier, 0.01)
    effective_frequency = effective_frequency / max(energy_multiplier * camp_multiplier, 0.01)
    helps_per_day = 86400 / effective_frequency

    ingredient_rate = _clamp(species["ingredient_rate"] * ingredient_multiplier, 0, 0.95)
    skill_rate = _clamp(species["skill_rate"] * skill_multiplier, 0, 0.95)
    berry_count = 2 if species["specialty"] == "Berries" else 1
    berries_per_day = helps_per_day * (berry_count + berry_bonus) * (1 - ingredient_rate)
    ingredients_per_day = helps_per_day * ingredient_rate
    skill_triggers_per_day = helps_per_day * skill_rate

    berry_value = species.get("berry_value") or 1.0
    if inputs.favored_berry:
        berry_value *= 2
    main_skill_level = inputs.main_skill_level or 1
    skill_value = 20 * (1 + (main_skill_level - 1) * 0.18 + skill_value_bonus)

    weights = defaults["role_weights"][species["specialty"]]
    berry_component = berries_per_day * berry_value
    ingredient_component = ingredients_per_day * 4.0
    skill_component = skill_triggers_per_day * skill_value
    raw_score = (
        berry_component * weights["berries"]
        + ingredient_component * weights["ingredients"]
        + skill_component * weights["skills"]
        + inventory_value * 100
    )
    production_score = round(_clamp(raw_score / 0.7, 0, 100), 1)

    assumptions = []
    if inputs.level is None:
        assumptions.append(f"level defaulted to {defaults['default_level']}")
    if inputs.energy is None:
        assumptions.append(f"energy defaulted to {defaults['default_energy']}")
    if inputs.main_skill_level is None:
        assumptions.append("main skill level defaulted to 1")
    if not inputs.ingredient_spread:
        assumptions.append("ingredient spread not provided")
    if inputs.favored_berry is None:
        assumptions.append("favored berry bonus not applied")

    return {
        "production_score": production_score,
        "helps_per_day": round(helps_per_day),
        "berries_per_day": round(berries_per_day, 1),
        "ingredients_per_day": round(ingredients_per_day, 1),
        "skill_triggers_per_day": round(skill_triggers_per_day, 2),
        "effective_frequency": round(effective_frequency),
        "assumptions_used": assumptions,
        "data_version": data.version,
    }


def recommend(
    grade_percentile: int,
    specialty: str,
    production: dict[str, Any],
    data: SleepData = SLEEP_DATA,
) -> dict[str, Any]:
    thresholds = data.production_defaults["recommendation_thresholds"]
    production_score = production.get("production_score", 0)
    blended = round((production_score * 0.65) + (grade_percentile * 0.35), 1)

    if blended >= thresholds["keep"]:
        verdict = "Keep"
    elif blended >= thresholds["consider"]:
        verdict = "Consider"
    else:
        verdict = "Release"

    reasons = [
        f"{specialty} specialist with blended score {blended}/100",
        f"production estimate {production_score}/100",
    ]
    if verdict == "Keep":
        reasons.append("Strong enough to invest in for its role.")
    elif verdict == "Consider":
        reasons.append("Usable, but compare against your current team and goals.")
    else:
        reasons.append("Weak investment unless it is shiny, a favorite, or fills a niche.")

    return {
        "recommendation": verdict,
        "recommendation_score": blended,
        "recommendation_reasons": reasons,
    }

"""Curated Pokemon Sleep data snapshots.

The JSON files in data/sleep are the reviewed source of truth for the Python
runtime. This module keeps a small compatibility surface for the older
RatePokemon class while making data updates reviewable as file diffs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parent / "data" / "sleep"


@dataclass(frozen=True)
class SleepData:
    version: str
    updated_at: str
    sources: list[dict[str, Any]]
    species: dict[str, dict[str, Any]]
    natures: dict[str, list[float]]
    subskills: dict[str, list[float]]
    score_ranges: dict[str, tuple[float, float]]
    detection_order_levels: list[int]
    speed_sensitive_subskills: frozenset[str]
    production_defaults: dict[str, Any]

    @property
    def pokemon(self) -> dict[str, str]:
        return {name: data["specialty"] for name, data in self.species.items()}

    @property
    def base_frequencies(self) -> dict[str, int]:
        return {
            name: int(data["base_frequency"])
            for name, data in self.species.items()
            if data.get("base_frequency")
        }


def _load_json(filename: str) -> dict[str, Any]:
    with (DATA_DIR / filename).open(encoding="utf-8") as fh:
        return json.load(fh)


def load_sleep_data() -> SleepData:
    species_doc = _load_json("species.json")
    scoring_doc = _load_json("scoring.json")

    score_ranges = {
        key: (float(value[0]), float(value[1]))
        for key, value in scoring_doc["score_ranges"].items()
    }

    data = SleepData(
        version=species_doc["version"],
        updated_at=species_doc["updated_at"],
        sources=species_doc.get("sources", []) + scoring_doc.get("sources", []),
        species=species_doc["species"],
        natures=scoring_doc["natures"],
        subskills=scoring_doc["subskills"],
        score_ranges=score_ranges,
        detection_order_levels=scoring_doc["detection_order_levels"],
        speed_sensitive_subskills=frozenset(scoring_doc["speed_sensitive_subskills"]),
        production_defaults=scoring_doc["production_defaults"],
    )
    validate_sleep_data(data)
    return data


def validate_sleep_data(data: SleepData) -> None:
    valid_specialties = {"Berries", "Ingredients", "Skills"}
    required_species_fields = {
        "specialty",
        "base_frequency",
        "ingredient_rate",
        "skill_rate",
        "berry_value",
    }

    if not data.species:
        raise ValueError("species snapshot is empty")
    if not data.natures:
        raise ValueError("nature snapshot is empty")
    if not data.subskills:
        raise ValueError("subskill snapshot is empty")

    for name, species in data.species.items():
        missing = required_species_fields - set(species)
        if missing:
            raise ValueError(f"{name} is missing fields: {sorted(missing)}")
        if species["specialty"] not in valid_specialties:
            raise ValueError(f"{name} has invalid specialty {species['specialty']}")
        if species["base_frequency"] is not None and species["base_frequency"] <= 0:
            raise ValueError(f"{name} has non-positive base_frequency")
        for rate_name in ("ingredient_rate", "skill_rate"):
            rate = species[rate_name]
            if rate is None or not 0 <= rate <= 1:
                raise ValueError(f"{name} has invalid {rate_name}: {rate}")

    for nature, values in data.natures.items():
        if len(values) != 3:
            raise ValueError(f"{nature} must have three specialty values")

    for subskill, values in data.subskills.items():
        if len(values) != 3:
            raise ValueError(f"{subskill} must have three specialty values")

    for specialty, value_range in data.score_ranges.items():
        if specialty not in valid_specialties:
            raise ValueError(f"invalid score range specialty {specialty}")
        if value_range[0] >= value_range[1]:
            raise ValueError(f"{specialty} score range min must be below max")

    for subskill in data.speed_sensitive_subskills:
        if subskill not in data.subskills:
            raise ValueError(f"speed-sensitive subskill is unknown: {subskill}")


SLEEP_DATA = load_sleep_data()

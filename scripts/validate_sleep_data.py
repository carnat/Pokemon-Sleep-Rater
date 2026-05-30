"""Validate curated Pokemon Sleep data snapshots.

This script is intentionally non-mutating. It validates the checked-in snapshot
or a reviewed JSON snapshot passed with --species/--scoring and prints a concise
diff report against the current checked-in data.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pokemon_data import SLEEP_DATA, SleepData, validate_sleep_data  # noqa: E402


def _load(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _build_data(species_doc: dict, scoring_doc: dict) -> SleepData:
    return SleepData(
        version=species_doc["version"],
        updated_at=species_doc["updated_at"],
        sources=species_doc.get("sources", []) + scoring_doc.get("sources", []),
        species=species_doc["species"],
        natures=scoring_doc["natures"],
        subskills=scoring_doc["subskills"],
        score_ranges={key: tuple(value) for key, value in scoring_doc["score_ranges"].items()},
        detection_order_levels=scoring_doc["detection_order_levels"],
        speed_sensitive_subskills=frozenset(scoring_doc["speed_sensitive_subskills"]),
        production_defaults=scoring_doc["production_defaults"],
    )


def _print_diff(candidate: SleepData) -> None:
    current_names = set(SLEEP_DATA.species)
    candidate_names = set(candidate.species)
    added = sorted(candidate_names - current_names)
    removed = sorted(current_names - candidate_names)
    changed = []
    for name in sorted(current_names & candidate_names):
        if SLEEP_DATA.species[name] != candidate.species[name]:
            changed.append(name)

    print(f"Snapshot version: {candidate.version} ({candidate.updated_at})")
    print(f"Pokemon count: {len(candidate.species)}")
    print(f"Added: {', '.join(added) if added else 'none'}")
    print(f"Removed: {', '.join(removed) if removed else 'none'}")
    print(f"Changed: {', '.join(changed) if changed else 'none'}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--species", type=Path, default=ROOT / "data" / "sleep" / "species.json")
    parser.add_argument("--scoring", type=Path, default=ROOT / "data" / "sleep" / "scoring.json")
    args = parser.parse_args()

    candidate = _build_data(_load(args.species), _load(args.scoring))
    validate_sleep_data(candidate)
    _print_diff(candidate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

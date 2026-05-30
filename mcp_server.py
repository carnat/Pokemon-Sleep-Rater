"""Minimal JSON-RPC MCP-style calculator endpoint for the Python runtime."""

from __future__ import annotations

import json
from typing import Any

from pokemon import RatePokemon
from pokemon_data import SLEEP_DATA


TOOLS = [
    {
        "name": "rate_pokemon",
        "description": "Rate a Pokemon Sleep helper from structured fields.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "nature": {"type": "string"},
                "subskills": {"type": "array", "items": {"type": "string"}},
                "level": {"type": "number"},
                "main_skill_level": {"type": "number"},
                "energy": {"type": "number"},
                "good_camp": {"type": "boolean"},
                "favored_berry": {"type": "boolean"},
            },
            "required": ["name", "nature", "subskills"],
        },
    },
    {
        "name": "list_pokemon",
        "description": "List supported Pokemon, optionally filtered by specialty.",
        "inputSchema": {
            "type": "object",
            "properties": {"specialty": {"type": "string"}},
        },
    },
    {
        "name": "get_pokemon_info",
        "description": "Get species data and source metadata for a Pokemon.",
        "inputSchema": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    },
    {
        "name": "explain_recommendation",
        "description": "Explain a Keep, Consider, or Release recommendation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "nature": {"type": "string"},
                "subskills": {"type": "array", "items": {"type": "string"}},
                "level": {"type": "number"},
            },
            "required": ["name", "nature", "subskills"],
        },
    },
]


def _jsonable(value: Any) -> Any:
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "rate_pokemon":
        result = RatePokemon(
            args.get("name", ""),
            args.get("nature", ""),
            list(args.get("subskills") or []),
        ).rate_pokemon(
            [],
            pokemon_level=args.get("level"),
            main_skill_level=args.get("main_skill_level"),
            energy=args.get("energy"),
            good_camp=bool(args.get("good_camp", False)),
            favored_berry=args.get("favored_berry"),
        )
        if not result:
            return {"error": "Pokemon or nature not recognised"}
        return _jsonable(result)

    if name == "list_pokemon":
        specialty = args.get("specialty")
        pokemon = [
            name
            for name, data in SLEEP_DATA.species.items()
            if not specialty or data["specialty"] == specialty
        ]
        return {"count": len(pokemon), "pokemon": pokemon, "data_version": SLEEP_DATA.version}

    if name == "get_pokemon_info":
        pokemon_name = args.get("name", "")
        species = SLEEP_DATA.species.get(pokemon_name)
        if not species:
            return {"error": f"Pokemon '{pokemon_name}' not found"}
        return {"name": pokemon_name, **species, "data_version": SLEEP_DATA.version}

    if name == "explain_recommendation":
        result = call_tool("rate_pokemon", args)
        if "error" in result:
            return result
        return {
            "name": result["name"],
            "recommendation": result["recommendation"],
            "recommendation_score": result["recommendation_score"],
            "reasons": result["recommendation_reasons"],
            "assumptions_used": result["assumptions_used"],
            "data_version": result["data_version"],
        }

    return {"error": f"Unknown tool: {name}"}


def handle_json_rpc(payload: dict[str, Any]) -> dict[str, Any] | None:
    method = payload.get("method")
    request_id = payload.get("id")
    params = payload.get("params") or {}

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "pokemon-sleep-rater", "version": SLEEP_DATA.version},
                "capabilities": {"tools": {}},
            }
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            result = {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            call_tool(params.get("name", ""), params.get("arguments") or {}),
                            ensure_ascii=False,
                            indent=2,
                        ),
                    }
                ]
            }
        elif method and method.startswith("notifications/"):
            return None
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Unknown method: {method}"},
            }
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32603, "message": str(exc)},
        }

    return {"jsonrpc": "2.0", "id": request_id, "result": result}

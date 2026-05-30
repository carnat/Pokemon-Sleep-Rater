"""Tests for the Python MCP-style calculator endpoint."""

import json

from mcp_server import call_tool, handle_json_rpc


def test_mcp_lists_tools():
    response = handle_json_rpc({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    names = {tool["name"] for tool in response["result"]["tools"]}
    assert {"rate_pokemon", "list_pokemon", "get_pokemon_info", "explain_recommendation"} <= names


def test_mcp_rate_pokemon_tool_returns_structured_rating():
    result = call_tool(
        "rate_pokemon",
        {
            "name": "Pikachu",
            "nature": "Jolly",
            "subskills": ["Berry Finding S", "Helping Speed M"],
            "level": 30,
        },
    )
    assert result["name"] == "Pikachu"
    assert result["production_score"] is not None
    assert result["recommendation"] in {"Keep", "Consider", "Release"}


def test_mcp_tools_call_wraps_result_as_text_content():
    response = handle_json_rpc(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "get_pokemon_info",
                "arguments": {"name": "Spheal"},
            },
        }
    )
    text = response["result"]["content"][0]["text"]
    parsed = json.loads(text)
    assert parsed["name"] == "Spheal"
    assert parsed["specialty"] == "Berries"


def test_mcp_unknown_tool_is_reported():
    assert "error" in call_tool("missing_tool", {})

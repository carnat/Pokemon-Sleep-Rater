#!/usr/bin/env python3
"""Smoke test for the deployed Cloudflare Worker MCP endpoint.

Usage:
    python scripts/test_deployed_mcp.py
    MCP_URL=https://custom-url.workers.dev/mcp python scripts/test_deployed_mcp.py
"""

import json
import os
import sys
import urllib.request
import urllib.error

MCP_URL = os.environ.get(
    "MCP_URL", "https://pokemon-sleep-rater.artinatw.workers.dev/mcp"
)

HEALTH_URL = MCP_URL.rsplit("/mcp", 1)[0] + "/health"

# Browser-like User-Agent to avoid Cloudflare Bot Fight / WAF blocks (error 1010).
USER_AGENT = (
    "Mozilla/5.0 (compatible; PokemonSleepMCP/1.0; "
    "+https://github.com/carnat/Pokemon-Sleep-Rater)"
)


def post_mcp(payload: dict) -> dict:
    """Send a JSON-RPC request to the MCP endpoint."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        MCP_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"FAIL: HTTP {e.code} from {MCP_URL}")
        print(f"  Body: {body[:500]}")
        sys.exit(1)


def test_health():
    """Verify /health reports cloudflare-worker-mcp."""
    print(f"[health] GET {HEALTH_URL}")
    req = urllib.request.Request(
        HEALTH_URL, method="GET", headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    assert data.get("status") == "ok", f"Expected status=ok, got {data}"
    assert "mcp" in data.get("runtime", ""), (
        f"Expected runtime containing 'mcp', got {data.get('runtime')}"
    )
    print(f"  OK: {data}")


def test_initialize():
    """MCP initialize handshake."""
    print(f"[initialize] POST {MCP_URL}")
    resp = post_mcp(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "smoke-test", "version": "1.0.0"},
            },
        }
    )
    result = resp.get("result", {})
    assert result.get("protocolVersion") == "2024-11-05", f"Bad init: {resp}"
    assert "serverInfo" in result, f"Missing serverInfo: {resp}"
    print(f"  OK: serverInfo={result['serverInfo']}")


def test_tools_list():
    """MCP tools/list returns expected tools."""
    print(f"[tools/list] POST {MCP_URL}")
    resp = post_mcp({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    tools = resp.get("result", {}).get("tools", [])
    tool_names = [t["name"] for t in tools]
    assert len(tools) >= 3, f"Expected >=3 tools, got {len(tools)}: {tool_names}"
    for expected in ("rate_pokemon", "list_pokemon", "get_pokemon_info"):
        assert expected in tool_names, f"Missing tool: {expected}"
    print(f"  OK: {len(tools)} tools: {tool_names}")


def test_rate_pokemon():
    """MCP tools/call rate_pokemon returns a rating."""
    print(f"[tools/call rate_pokemon] POST {MCP_URL}")
    resp = post_mcp(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "rate_pokemon",
                "arguments": {
                    "name": "Snorlax",
                    "nature": "Impish",
                    "subskills": [
                        "Helping Speed M",
                        "Inventory Up M",
                        "Ingredient Finder M",
                    ],
                },
            },
        }
    )
    result = resp.get("result", {})
    content = result.get("content", [])
    assert len(content) > 0, f"Expected content, got: {resp}"
    text = content[0].get("text", "")
    assert "grade" in text.lower() or "score" in text.lower(), (
        f"Expected rating in response, got: {text[:200]}"
    )
    print(f"  OK: got rating response ({len(text)} chars)")


def main():
    print(f"=== Deployed MCP Smoke Test ===")
    print(f"MCP_URL: {MCP_URL}")
    print()

    test_health()
    test_initialize()
    test_tools_list()
    test_rate_pokemon()

    print()
    print("All smoke tests PASSED ✓")


if __name__ == "__main__":
    main()

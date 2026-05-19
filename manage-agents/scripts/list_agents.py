#!/usr/bin/env python3
"""List all Bolna v2 agents in the account.

Usage:
    python3 list_agents.py
    python3 list_agents.py --names-only
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_BASE = "https://api.bolna.ai"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--names-only", action="store_true",
                        help="Print only `<id>\\t<name>` per line")
    args = parser.parse_args()

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    req = Request(
        f"{API_BASE}/v2/agent/all",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(req, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        print(exc.read().decode("utf-8", errors="replace"), file=sys.stderr)
        return 1

    agents = body if isinstance(body, list) else body.get("data", [])
    if args.names_only:
        for agent in agents:
            name = (agent.get("agent_config") or {}).get("agent_name") or agent.get("name") or ""
            print(f"{agent.get('id')}\t{name}")
    else:
        print(json.dumps(agents, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

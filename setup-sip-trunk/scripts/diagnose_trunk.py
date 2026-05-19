#!/usr/bin/env python3
"""Print a trunk's full state + its numbers for triage.

Usage:
    python3 diagnose_trunk.py --trunk-id <TRUNK_ID>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_BASE = "https://api.bolna.ai"


def get(path: str, token: str) -> dict:
    req = Request(
        f"{API_BASE}{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        method="GET",
    )
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trunk-id", required=True)
    args = parser.parse_args()

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    try:
        trunk = get(f"/sip-trunks/trunks/{args.trunk_id}", token)
        numbers = get(f"/sip-trunks/trunks/{args.trunk_id}/numbers", token)
    except HTTPError as exc:
        print(exc.read().decode("utf-8", errors="replace"), file=sys.stderr)
        return 1

    diag = {
        "trunk": {
            "id": trunk.get("id"),
            "name": trunk.get("name"),
            "provider": trunk.get("provider"),
            "is_active": trunk.get("is_active"),
            "inbound_enabled": trunk.get("inbound_enabled"),
            "transport": trunk.get("transport"),
            "media_encryption": trunk.get("media_encryption"),
            "auth_type": trunk.get("auth_type"),
            "gateway_count": len(trunk.get("gateways", [])),
            "ip_identifier_count": len(trunk.get("ip_identifiers", [])),
        },
        "numbers": [
            {
                "id": n.get("id"),
                "phone_number": n.get("phone_number"),
                "deleted": n.get("deleted"),
            }
            for n in (numbers if isinstance(numbers, list) else numbers.get("data", []))
        ],
    }
    print(json.dumps(diag, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

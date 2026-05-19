#!/usr/bin/env python3
"""Bulk-create Bolna dispositions for an agent from a JSON file.

Reads a file shaped like `assets/sample_bulk_dispositions.json` and POSTs it to
`/dispositions/bulk`. Either all dispositions are created or none — atomic.

Usage:
    python3 bulk_create_dispositions.py --file assets/sample_bulk_dispositions.json
    python3 bulk_create_dispositions.py --file my.json --agent-id <UUID-override>
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
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", required=True, help="Path to JSON file with {agent_id, dispositions[]}")
    parser.add_argument("--agent-id", default=None, help="Override the agent_id from the file")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        with open(args.file, encoding="utf-8") as fp:
            payload = json.load(fp)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Failed to read {args.file}: {exc}", file=sys.stderr)
        return 2

    if args.agent_id:
        payload["agent_id"] = args.agent_id

    if "agent_id" not in payload or "REPLACE" in payload["agent_id"]:
        print("agent_id is missing or still a placeholder. Pass --agent-id or edit the file.", file=sys.stderr)
        return 2

    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    req = Request(
        f"{API_BASE}/dispositions/bulk",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=60) as response:
            print(response.read().decode("utf-8"))
    except HTTPError as exc:
        print(exc.read().decode("utf-8", errors="replace"), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

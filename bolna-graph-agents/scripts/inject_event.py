#!/usr/bin/env python3
"""Inject a real-time event into a live Bolna graph-agent call.

Usage:
    python3 inject_event.py --run-id <execution_id> --event payment_completed
    python3 inject_event.py --run-id <execution_id> --event payment_failed --properties '{"error_reason":"Card declined"}'

Returns 0 on 2xx, 1 on HTTP error, 2 on bad args.
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
    parser.add_argument("--run-id", required=True, help="execution_id from POST /call or inbound webhook")
    parser.add_argument("--event", required=True, help="Event name to match an event edge")
    parser.add_argument("--properties", default="{}", help='JSON object merged into context_data')
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        properties = json.loads(args.properties)
        if not isinstance(properties, dict):
            raise ValueError("properties must be a JSON object")
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"--properties must be a JSON object: {exc}", file=sys.stderr)
        return 2

    payload = {"event": args.event, "properties": properties}

    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    req = Request(
        f"{API_BASE}/v1/call/{args.run_id}/events",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=10) as response:
            print(response.read().decode("utf-8"))
    except HTTPError as exc:
        print(exc.read().decode("utf-8", errors="replace"), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

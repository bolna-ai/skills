#!/usr/bin/env python3
"""Schedule a Bolna call at a specific datetime.

`--at` must include a timezone offset, e.g. `2026-05-22T15:30:00+05:30`.
Without an offset, Bolna silently runs in UTC.

Usage:
    python3 schedule_call.py --agent-id <UUID> --recipient +919876543210 \\
        --at 2026-05-22T15:30:00+05:30 \\
        --user-data '{"customer_name":"Priya"}'
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_BASE = "https://api.bolna.ai"
TZ_OFFSET_RE = re.compile(r"[+-]\d{2}:\d{2}$|Z$")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--recipient", required=True, help="E.164 phone")
    parser.add_argument("--at", required=True, help="ISO 8601 datetime WITH timezone offset")
    parser.add_argument("--from-phone-number", default=None)
    parser.add_argument("--user-data", default="{}")
    parser.add_argument("--bypass-guardrails", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not TZ_OFFSET_RE.search(args.at):
        print(f"--at must include a timezone offset (e.g. +05:30 or Z): {args.at}", file=sys.stderr)
        return 2

    try:
        user_data = json.loads(args.user_data)
    except json.JSONDecodeError as exc:
        print(f"--user-data must be JSON: {exc}", file=sys.stderr)
        return 2

    payload = {
        "agent_id": args.agent_id,
        "recipient_phone_number": args.recipient,
        "scheduled_at": args.at,
        "user_data": user_data,
        "bypass_call_guardrails": args.bypass_guardrails,
    }
    if args.from_phone_number:
        payload["from_phone_number"] = args.from_phone_number

    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    req = Request(
        f"{API_BASE}/call",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=30) as response:
            print(response.read().decode("utf-8"))
    except HTTPError as exc:
        print(exc.read().decode("utf-8", errors="replace"), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

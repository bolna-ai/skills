#!/usr/bin/env python3
"""Make an outbound Bolna call."""

from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen


API_BASE = "https://api.bolna.ai"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--recipient", required=True)
    parser.add_argument("--from-phone-number", default=None)
    parser.add_argument("--scheduled-at", default=None)
    parser.add_argument("--voice-id", default=None)
    parser.add_argument("--user-data", default="{}")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        user_data = json.loads(args.user_data)
    except json.JSONDecodeError as exc:
        print(f"--user-data must be JSON: {exc}", file=sys.stderr)
        return 2

    payload = {
        "agent_id": args.agent_id,
        "recipient_phone_number": args.recipient,
        "user_data": user_data,
    }
    if args.from_phone_number:
        payload["from_phone_number"] = args.from_phone_number
    if args.scheduled_at:
        payload["scheduled_at"] = args.scheduled_at
    if args.voice_id:
        payload["agent_data"] = {"voice_id": args.voice_id}

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

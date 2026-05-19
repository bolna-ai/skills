#!/usr/bin/env python3
"""Map a Bolna phone number to an agent (plain or with IVR config).

Plain mapping:
    python3 setup_inbound.py --agent-id <AGENT_UUID> --phone-number-id <PHONE_UUID>

With IVR from a JSON file (e.g. assets/ivr_department_routing.json):
    python3 setup_inbound.py --file assets/ivr_department_routing.json

Unlink instead of setup:
    python3 setup_inbound.py --unlink --phone-number-id <PHONE_UUID>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_BASE = "https://api.bolna.ai"


def post(path: str, payload: dict, token: str) -> int:
    req = Request(
        f"{API_BASE}{path}",
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--agent-id", default=None)
    parser.add_argument("--phone-number-id", default=None)
    parser.add_argument("--file", default=None, help="JSON file with full setup payload (incl. ivr_config)")
    parser.add_argument("--unlink", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.unlink:
        if not args.phone_number_id:
            print("--phone-number-id required for --unlink", file=sys.stderr)
            return 2
        payload = {"phone_number_id": args.phone_number_id}
        if args.agent_id:
            payload["agent_id"] = args.agent_id
        path = "/inbound/unlink"
    elif args.file:
        try:
            with open(args.file, encoding="utf-8") as fp:
                payload = json.load(fp)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Failed to read {args.file}: {exc}", file=sys.stderr)
            return 2
        path = "/inbound/setup"
    else:
        if not (args.agent_id and args.phone_number_id):
            print("Pass --agent-id + --phone-number-id, or --file <payload.json>", file=sys.stderr)
            return 2
        payload = {"agent_id": args.agent_id, "phone_number_id": args.phone_number_id}
        path = "/inbound/setup"

    if args.dry_run:
        print(f"POST {path}")
        print(json.dumps(payload, indent=2))
        return 0

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    return post(path, payload, token)


if __name__ == "__main__":
    sys.exit(main())

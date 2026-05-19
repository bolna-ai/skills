#!/usr/bin/env python3
"""Add a DID phone number to a Bolna SIP trunk.

Usage:
    python3 add_trunk_number.py --trunk-id <TRUNK_ID> --phone-number +919876543210 --name "Mumbai Sales"

Outputs the phone_number_id (used later in `inbound/setup`).
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
    parser.add_argument("--trunk-id", required=True)
    parser.add_argument("--phone-number", required=True)
    parser.add_argument("--name", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    payload: dict = {"phone_number": args.phone_number}
    if args.name:
        payload["name"] = args.name

    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    req = Request(
        f"{API_BASE}/sip-trunks/trunks/{args.trunk_id}/numbers",
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

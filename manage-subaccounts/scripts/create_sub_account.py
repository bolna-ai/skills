#!/usr/bin/env python3
"""Create a new Bolna sub-account (enterprise).

Usage:
    python3 create_sub_account.py --name "Acme Customer A" \\
        --description "Customer A workspace" \\
        --metadata '{"customer_id":"cust_abc123","region":"in"}'

Save the returned `api_key` (prefixed `sa-`) immediately — it can't be retrieved later.
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
    parser.add_argument("--name", required=True)
    parser.add_argument("--description", default=None)
    parser.add_argument("--metadata", default="{}", help="JSON object")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        metadata = json.loads(args.metadata)
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be a JSON object")
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"--metadata must be a JSON object: {exc}", file=sys.stderr)
        return 2

    payload: dict = {"name": args.name, "metadata": metadata}
    if args.description:
        payload["description"] = args.description

    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    req = Request(
        f"{API_BASE}/sub-accounts/create",
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

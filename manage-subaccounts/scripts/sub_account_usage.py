#!/usr/bin/env python3
"""Fetch usage for one sub-account or the rollup across all sub-accounts.

Usage:
    python3 sub_account_usage.py --sub-account-id subacct_01HQ...
    python3 sub_account_usage.py --all
"""
from __future__ import annotations

import argparse
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_BASE = "https://api.bolna.ai"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--sub-account-id")
    group.add_argument("--all", action="store_true", help="Rollup across all sub-accounts")
    args = parser.parse_args()

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    path = "/sub-accounts/all/usage" if args.all else f"/sub-accounts/{args.sub_account_id}/usage"

    req = Request(
        f"{API_BASE}{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        method="GET",
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

#!/usr/bin/env python3
"""List Bolna call violations, optionally filtered by status or agent.

Usage:
    python3 list_violations.py
    python3 list_violations.py --status open
    python3 list_violations.py --agent-id <UUID> --page-size 50
"""
from __future__ import annotations

import argparse
import os
import sys
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_BASE = "https://api.bolna.ai"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", default=None,
                        choices=["open", "under_review", "resolved", "rejected"])
    parser.add_argument("--agent-id", default=None)
    parser.add_argument("--page-number", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=20)
    args = parser.parse_args()

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    params: dict = {"page_number": args.page_number, "page_size": args.page_size}
    if args.status:
        params["status"] = args.status
    if args.agent_id:
        params["agent_id"] = args.agent_id

    req = Request(
        f"{API_BASE}/violations/list?{urlencode(params)}",
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

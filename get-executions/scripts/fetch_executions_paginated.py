#!/usr/bin/env python3
"""Paginate through all executions for one Bolna agent or batch.

Outputs newline-delimited JSON (one execution per line) so you can pipe to `jq`
or pipe to a file for later analysis.

Usage:
    python3 fetch_executions_paginated.py --agent-id <UUID>
    python3 fetch_executions_paginated.py --batch-id <BATCH_ID>
    python3 fetch_executions_paginated.py --agent-id <UUID> --page-size 50
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_BASE = "https://api.bolna.ai"


def fetch_page(path: str, params: dict, token: str) -> dict:
    req = Request(
        f"{API_BASE}{path}?{urlencode(params)}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        method="GET",
    )
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--agent-id")
    target.add_argument("--batch-id")
    parser.add_argument("--page-size", type=int, default=50)
    parser.add_argument("--max-pages", type=int, default=None, help="Cap on pages (safety)")
    args = parser.parse_args()

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    if args.agent_id:
        path = f"/v2/agent/{args.agent_id}/executions"
    else:
        path = f"/batches/{args.batch_id}/executions"

    page = 1
    total_seen = 0
    while True:
        if args.max_pages and page > args.max_pages:
            print(f"# stopped at max_pages={args.max_pages}", file=sys.stderr)
            break

        try:
            body = fetch_page(path, {"page_number": page, "page_size": args.page_size}, token)
        except HTTPError as exc:
            print(exc.read().decode("utf-8", errors="replace"), file=sys.stderr)
            return 1

        items = body.get("data") or []
        for item in items:
            print(json.dumps(item))
        total_seen += len(items)

        print(f"# page {page}: {len(items)} items, total_seen={total_seen}", file=sys.stderr)

        if not body.get("has_more"):
            break
        page += 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

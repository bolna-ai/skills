#!/usr/bin/env python3
"""Poll a Bolna batch until terminal and print summary counts.

Usage:
    python3 monitor_batch.py --batch-id <BATCH_ID>
    python3 monitor_batch.py --batch-id <BATCH_ID> --interval 30 --once
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_BASE = "https://api.bolna.ai"
TERMINAL_STATES = {"completed", "stopped", "failed", "canceled"}


def fetch(path: str, token: str) -> dict:
    req = Request(
        f"{API_BASE}{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        method="GET",
    )
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--interval", type=int, default=20, help="Seconds between polls")
    parser.add_argument("--once", action="store_true", help="One poll then exit (don't loop)")
    args = parser.parse_args()

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    while True:
        try:
            batch = fetch(f"/batches/{args.batch_id}", token)
        except HTTPError as exc:
            print(exc.read().decode("utf-8", errors="replace"), file=sys.stderr)
            return 1

        state = batch.get("state") or batch.get("status")
        summary = {
            "batch_id": batch.get("batch_id") or batch.get("id"),
            "state": state,
            "total_contacts": batch.get("total_contacts"),
            "valid_contacts": batch.get("valid_contacts"),
            "queued": batch.get("queued_count"),
            "in_progress": batch.get("in_progress_count"),
            "completed": batch.get("completed_count"),
            "failed": batch.get("failed_count"),
            "no_answer": batch.get("no_answer_count"),
            "busy": batch.get("busy_count"),
        }
        print(json.dumps(summary, indent=2))

        if args.once or (state and state.lower() in TERMINAL_STATES):
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())

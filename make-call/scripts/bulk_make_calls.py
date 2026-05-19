#!/usr/bin/env python3
"""Fan out one-off calls from a CSV.

Each CSV row dials a separate `POST /call`. Other columns become `user_data` keys
(matching `{variable}` substitutions in the agent prompt).

For proper campaigns with monitoring and retry, use the `create-batch` skill —
`/batches` is the right endpoint there. This script is for ad-hoc fan-outs.

CSV shape:
    contact_number,customer_name,plan
    +919876543210,Priya,Pro
    +918765432109,Rahul,Starter

Usage:
    python3 bulk_make_calls.py --agent-id <UUID> --file recipients.csv
    python3 bulk_make_calls.py --agent-id <UUID> --file recipients.csv --rate 2  # 2 calls/sec
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_BASE = "https://api.bolna.ai"


def dial(agent_id: str, recipient: str, user_data: dict, from_number: str | None, token: str) -> tuple[int, str]:
    payload = {
        "agent_id": agent_id,
        "recipient_phone_number": recipient,
        "user_data": user_data,
    }
    if from_number:
        payload["from_phone_number"] = from_number

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
            return response.status, response.read().decode("utf-8")
    except HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--file", required=True, help="CSV with contact_number column + variables")
    parser.add_argument("--from-phone-number", default=None)
    parser.add_argument("--rate", type=float, default=1.0, help="Calls per second (sleep between dials)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    token = os.environ.get("BOLNA_API_KEY")
    if not token and not args.dry_run:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    sleep_s = 1.0 / args.rate if args.rate > 0 else 0

    successes = failures = 0
    with open(args.file, newline="", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        if "contact_number" not in (reader.fieldnames or []):
            print("CSV must have a contact_number column", file=sys.stderr)
            return 2

        for row in reader:
            recipient = row.pop("contact_number").strip()
            if not recipient.startswith("+"):
                print(f"SKIP non-E.164: {recipient}", file=sys.stderr)
                failures += 1
                continue
            user_data = {k: v for k, v in row.items() if v}

            if args.dry_run:
                print(json.dumps({"recipient": recipient, "user_data": user_data}, indent=2))
                continue

            status, body = dial(args.agent_id, recipient, user_data, args.from_phone_number, token or "")
            ok = 200 <= status < 300
            print(f"{recipient}: HTTP {status} {'OK' if ok else 'FAIL'}")
            if not ok:
                print(f"  -> {body}", file=sys.stderr)
                failures += 1
            else:
                successes += 1
            if sleep_s:
                time.sleep(sleep_s)

    print(f"\nSummary: {successes} succeeded, {failures} failed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

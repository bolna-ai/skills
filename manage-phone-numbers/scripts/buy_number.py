#!/usr/bin/env python3
"""Buy a Bolna-hosted phone number.

Usage:
    python3 buy_number.py --country US --phone-number +17182718146 --provider twilio
    python3 buy_number.py --country IN --phone-number +918012345678 --provider plivo
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
    parser.add_argument("--country", required=True, help="US or IN")
    parser.add_argument("--phone-number", required=True, help="E.164 number from a prior /search call")
    parser.add_argument("--provider", required=True, help="twilio, plivo, or vobiz")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    payload = {
        "country": args.country,
        "phone_number": args.phone_number,
        "provider": args.provider,
    }

    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    req = Request(
        f"{API_BASE}/phone-numbers/buy",
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

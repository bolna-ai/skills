#!/usr/bin/env python3
"""Search available Bolna phone numbers to buy.

Usage:
    python3 search_numbers.py --country US --pattern 718
    python3 search_numbers.py --country IN --provider plivo --region 80
    python3 search_numbers.py --country IN --provider vobiz --region 11
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--country", required=True, help="US or IN")
    parser.add_argument("--pattern", default=None, help="Area code / prefix filter (US)")
    parser.add_argument("--provider", default=None, help="plivo or vobiz (IN)")
    parser.add_argument("--region", default=None, help="80=Karnataka, 22=Maharashtra, 79=Gujarat, 11=NCR")
    args = parser.parse_args()

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    params = {"country": args.country}
    if args.pattern:
        params["pattern"] = args.pattern
    if args.provider:
        params["provider"] = args.provider
    if args.region:
        params["region"] = args.region

    req = Request(
        f"{API_BASE}/phone-numbers/search?{urlencode(params)}",
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

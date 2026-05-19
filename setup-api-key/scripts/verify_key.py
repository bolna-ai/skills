#!/usr/bin/env python3
"""Verify BOLNA_API_KEY against the Bolna user endpoint."""

from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_BASE = "https://api.bolna.ai"


def main() -> int:
    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    req = Request(
        f"{API_BASE}/user/me",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"Bolna returned HTTP {exc.code}: {body}", file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"Could not reach Bolna: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

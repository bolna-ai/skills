#!/usr/bin/env python3
"""Create a Bolna batch campaign from a CSV.

The CSV must have a `contact_number` column. Other columns become per-call
dynamic variables that fill `{variable}` substitutions in the agent prompt.

Usage:
    python3 create_batch.py --agent-id <UUID> --file recipients.csv \\
        --from-numbers +919876543210,+919876543211

    # With retry config
    python3 create_batch.py --agent-id <UUID> --file recipients.csv \\
        --from-numbers +919876543210 \\
        --retry '{"enabled":true,"max_retries":2,"retry_intervals_minutes":[30,60]}'
"""
from __future__ import annotations

import argparse
import mimetypes
import os
import sys
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_BASE = "https://api.bolna.ai"


def build_multipart(text_fields: list[tuple[str, str]], file_field: str, file_path: str) -> tuple[bytes, str]:
    boundary = "----BolnaFormBoundary" + uuid.uuid4().hex
    crlf = b"\r\n"
    parts: list[bytes] = []
    for name, value in text_fields:
        parts.append(f"--{boundary}".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"'.encode())
        parts.append(b"")
        parts.append(str(value).encode("utf-8"))
    parts.append(f"--{boundary}".encode())
    filename = os.path.basename(file_path)
    content_type = mimetypes.guess_type(filename)[0] or "text/csv"
    parts.append(
        f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"'.encode()
    )
    parts.append(f"Content-Type: {content_type}".encode())
    parts.append(b"")
    with open(file_path, "rb") as fp:
        parts.append(fp.read())
    parts.append(f"--{boundary}--".encode())
    parts.append(b"")
    return crlf.join(parts), boundary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--file", required=True, help="CSV with contact_number + per-call vars")
    parser.add_argument("--from-numbers", required=True,
                        help="Comma-separated E.164 numbers to use as callerID(s)")
    parser.add_argument("--retry", default=None, help="retry_config JSON")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"CSV not found: {args.file}", file=sys.stderr)
        return 2

    fields: list[tuple[str, str]] = [("agent_id", args.agent_id)]
    for number in [n.strip() for n in args.from_numbers.split(",") if n.strip()]:
        fields.append(("from_phone_numbers", number))
    if args.retry:
        fields.append(("retry_config", args.retry))

    if args.dry_run:
        for name, val in fields:
            print(f"{name}={val}")
        print(f"file={args.file}")
        return 0

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    body, boundary = build_multipart(fields, "file", args.file)
    req = Request(
        f"{API_BASE}/batches",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=60) as response:
            print(response.read().decode("utf-8"))
    except HTTPError as exc:
        print(exc.read().decode("utf-8", errors="replace"), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

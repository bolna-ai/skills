#!/usr/bin/env python3
"""Submit evidence file + comment for a Bolna violation review.

Usage:
    python3 submit_violation_evidence.py \\
        --violation-id vio_01HQXYZ \\
        --file ./evidence/consent_form_2026-05-10.pdf \\
        --comment "Customer signed consent form on 2026-05-10."
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


def build_multipart(fields: dict, file_field: str, file_path: str) -> tuple[bytes, str]:
    boundary = "----BolnaFormBoundary" + uuid.uuid4().hex
    crlf = b"\r\n"
    parts: list[bytes] = []
    for name, value in fields.items():
        if value is None:
            continue
        parts.append(f"--{boundary}".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"'.encode())
        parts.append(b"")
        parts.append(str(value).encode("utf-8"))
    parts.append(f"--{boundary}".encode())
    filename = os.path.basename(file_path)
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
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
    parser.add_argument("--violation-id", required=True)
    parser.add_argument("--file", required=True, help="Evidence file path (PDF / image / doc)")
    parser.add_argument("--comment", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"Evidence file not found: {args.file}", file=sys.stderr)
        return 2

    fields = {"violation_id": args.violation_id, "comment": args.comment}
    if args.dry_run:
        print(f"Would POST /violations/submit with {fields} + file={args.file}")
        return 0

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    body, boundary = build_multipart(fields, "file", args.file)

    req = Request(
        f"{API_BASE}/violations/submit",
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

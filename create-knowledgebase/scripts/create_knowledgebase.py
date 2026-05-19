#!/usr/bin/env python3
"""Create a Bolna knowledge base from a PDF or URL.

Usage:
    # PDF (multipart)
    python3 create_knowledgebase.py --file /path/to/manual.pdf

    # URL
    python3 create_knowledgebase.py --url https://example.com/docs

    # Multilingual + custom chunking
    python3 create_knowledgebase.py --file ./policy.pdf \\
        --multilingual --chunk-size 512 --overlap 128 --top-k 15

Then poll until status == "processed" before wiring the returned `vector_id`
into an agent.
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


def build_multipart(text_fields: list[tuple[str, str]], file_field: str | None, file_path: str | None) -> tuple[bytes, str]:
    boundary = "----BolnaFormBoundary" + uuid.uuid4().hex
    crlf = b"\r\n"
    parts: list[bytes] = []
    for name, value in text_fields:
        parts.append(f"--{boundary}".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"'.encode())
        parts.append(b"")
        parts.append(str(value).encode("utf-8"))
    if file_field and file_path:
        parts.append(f"--{boundary}".encode())
        filename = os.path.basename(file_path)
        content_type = mimetypes.guess_type(filename)[0] or "application/pdf"
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
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="PDF file path (max 20 MB)")
    src.add_argument("--url", help="HTTPS URL of a page to ingest")
    parser.add_argument("--chunk-size", type=int, default=512)
    parser.add_argument("--overlap", type=int, default=128)
    parser.add_argument("--top-k", type=int, default=15)
    parser.add_argument("--multilingual", action="store_true",
                        help="Enable cross-lingual retrieval (non-English docs)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    fields: list[tuple[str, str]] = [
        ("chunk_size", str(args.chunk_size)),
        ("overlapping", str(args.overlap)),
        ("similarity_top_k", str(args.top_k)),
    ]
    if args.multilingual:
        fields.append(("language_support", "multilingual"))
    if args.url:
        fields.append(("url", args.url))

    if args.dry_run:
        for name, val in fields:
            print(f"{name}={val}")
        if args.file:
            print(f"file={args.file}")
        return 0

    if args.file and not os.path.isfile(args.file):
        print(f"PDF not found: {args.file}", file=sys.stderr)
        return 2

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    body, boundary = build_multipart(
        fields,
        "file" if args.file else None,
        args.file,
    )
    req = Request(
        f"{API_BASE}/knowledgebase",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=120) as response:
            print(response.read().decode("utf-8"))
    except HTTPError as exc:
        print(exc.read().decode("utf-8", errors="replace"), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

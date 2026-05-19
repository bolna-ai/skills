#!/usr/bin/env python3
"""Test all dispositions linked to a Bolna agent against a transcript.

Three ways to provide the transcript:
    --transcript-text "...raw text..."
    --transcript-file path/to/transcript.txt
    --sample sales_call|support_call|appointment_call (from assets/sample_transcripts.json)

Usage:
    python3 test_dispositions.py --agent-id <UUID> --sample sales_call
    python3 test_dispositions.py --agent-id <UUID> --transcript-file mycall.txt --call-date 2026-05-19T10:00:00Z
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_BASE = "https://api.bolna.ai"


def load_sample(name: str) -> tuple[str, str]:
    samples_path = pathlib.Path(__file__).resolve().parent.parent / "assets" / "sample_transcripts.json"
    with open(samples_path, encoding="utf-8") as fp:
        samples = json.load(fp)
    if name not in samples:
        raise SystemExit(f"Unknown sample '{name}'. Available: {', '.join(samples)}")
    return samples[name]["transcript"], samples[name]["call_date"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--transcript-text", default=None)
    parser.add_argument("--transcript-file", default=None)
    parser.add_argument("--sample", default=None, help="sales_call | support_call | appointment_call")
    parser.add_argument("--call-date", default=None, help="ISO 8601 with timezone, e.g. 2026-05-19T10:00:00+05:30")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.sample:
        transcript, default_date = load_sample(args.sample)
    elif args.transcript_text:
        transcript = args.transcript_text
        default_date = None
    elif args.transcript_file:
        try:
            transcript = pathlib.Path(args.transcript_file).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"Failed to read {args.transcript_file}: {exc}", file=sys.stderr)
            return 2
        default_date = None
    else:
        print("Provide one of --transcript-text, --transcript-file, --sample", file=sys.stderr)
        return 2

    payload = {"transcript": transcript, "call_date": args.call_date or default_date}

    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    req = Request(
        f"{API_BASE}/v2/agent/{args.agent_id}/dispositions/test",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
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

#!/usr/bin/env python3
"""Create a single Bolna disposition.

Examples:
    # Pre-defined only
    python3 create_disposition.py \\
      --name "Customer Sentiment" --category "Lead Quality" \\
      --question "What was the overall sentiment of the customer?" \\
      --objective '[{"value":"positive","condition":"Friendly and engaged"},
                    {"value":"neutral","condition":"Polite but uninvested"},
                    {"value":"negative","condition":"Irritated or hostile"}]' \\
      --agent-id <UUID>

    # Free text with email validation
    python3 create_disposition.py \\
      --name "Customer Email" --category "Contact Info" \\
      --question "Did the customer provide their email?" \\
      --subjective email --agent-id <UUID>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_BASE = "https://api.bolna.ai"


def build_payload(args: argparse.Namespace) -> dict:
    payload: dict = {
        "name": args.name,
        "category": args.category,
        "question": args.question,
        "model": args.model,
        "is_subjective": False,
        "is_objective": False,
    }
    if args.system_prompt:
        payload["system_prompt"] = args.system_prompt

    if args.subjective:
        payload["is_subjective"] = True
        payload["subjective_type"] = args.subjective
        if args.subjective == "regex":
            if not args.regex_pattern:
                raise SystemExit("--regex-pattern required when --subjective=regex")
            payload["subjective_type_config"] = {
                "pattern": args.regex_pattern,
                "description": args.regex_description,
            }

    if args.objective:
        try:
            options = json.loads(args.objective)
            if not isinstance(options, list):
                raise ValueError("objective must be a JSON array")
        except (json.JSONDecodeError, ValueError) as exc:
            raise SystemExit(f"--objective must be a JSON array of options: {exc}") from exc
        payload["is_objective"] = True
        payload["objective_options"] = options

    if not (payload["is_subjective"] or payload["is_objective"]):
        raise SystemExit("Provide --subjective and/or --objective; at least one is required")

    if args.agent_id:
        payload["agent_ids"] = [args.agent_id]

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", required=True)
    parser.add_argument("--category", default="General")
    parser.add_argument("--question", required=True)
    parser.add_argument("--system-prompt", default=None)
    parser.add_argument("--model", default="gpt-4.1-mini")
    parser.add_argument("--subjective", choices=["text", "timestamp", "numeric", "boolean", "email", "regex"])
    parser.add_argument("--regex-pattern", default=None)
    parser.add_argument("--regex-description", default=None)
    parser.add_argument("--objective", default=None, help="JSON array of {value, condition[, sub_options]} options")
    parser.add_argument("--agent-id", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    req = Request(
        f"{API_BASE}/dispositions/",
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

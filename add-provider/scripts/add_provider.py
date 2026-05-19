#!/usr/bin/env python3
"""Register a provider credential with Bolna.

Usage:
    # From an env var (recommended; doesn't leak into shell history)
    export OPENAI_KEY="sk-..."
    python3 add_provider.py --name OPENAI --value-env OPENAI_KEY

    # Inline (only for testing — visible in shell history)
    python3 add_provider.py --name OPENAI --value sk-...

The `--name` is the provider key Bolna expects. Common names:
    OPENAI, OPENROUTER, GOOGLE, ELEVENLABS, CARTESIA, SARVAM, SMALLEST, DEEPGRAM,
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER,
    PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN, PLIVO_PHONE_NUMBER,
    VOBIZ_AUTH_ID, VOBIZ_AUTH_TOKEN, VOBIZ_PHONE_NUMBER,
    EXOTEL_API_KEY, EXOTEL_API_TOKEN, ...
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
    parser.add_argument("--name", required=True, help="Provider key name (e.g. OPENAI, ELEVENLABS)")
    val = parser.add_mutually_exclusive_group(required=True)
    val.add_argument("--value", help="Credential value (inline — visible to shell history)")
    val.add_argument("--value-env", help="Read the credential from this env var name")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.value_env:
        value = os.environ.get(args.value_env)
        if not value:
            print(f"Env var {args.value_env} is empty or not set", file=sys.stderr)
            return 2
    else:
        value = args.value

    payload = {"provider_name": args.name, "provider_value": value}

    if args.dry_run:
        masked = {**payload, "provider_value": "***" + (value[-4:] if value else "")}
        print(json.dumps(masked, indent=2))
        return 0

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    req = Request(
        f"{API_BASE}/providers",
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

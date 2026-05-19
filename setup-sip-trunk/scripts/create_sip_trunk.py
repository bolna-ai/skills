#!/usr/bin/env python3
"""Create a Bolna SIP trunk.

Two auth modes:

    # userpass (Twilio-style)
    python3 create_sip_trunk.py \\
      --name "Twilio Prod" --provider twilio \\
      --auth-type userpass --username U --password P \\
      --gateway "your-trunk.pstn.twilio.com:5060"

    # ip-based (Plivo-style)
    python3 create_sip_trunk.py \\
      --name "Plivo Zentrunk" --provider plivo \\
      --auth-type ip-based \\
      --gateway "21467306465797919.zt.plivo.com:5060" \\
      --ip-identifier 15.207.90.192/31 \\
      --ip-identifier 204.89.151.128/27 \\
      --transport transport-udp --inbound

For TLS + SDES (encrypted media), add: --transport transport-tls --media-encryption sdes
and use port 5061 on the gateway.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_BASE = "https://api.bolna.ai"


def parse_gateway(spec: str) -> dict:
    if ":" in spec:
        host, port = spec.rsplit(":", 1)
        return {"gateway_address": host, "port": int(port), "priority": 1}
    return {"gateway_address": spec, "port": 5060, "priority": 1}


def build_payload(args: argparse.Namespace) -> dict:
    payload: dict = {
        "name": args.name,
        "provider": args.provider,
        "auth_type": args.auth_type,
        "gateways": [parse_gateway(g) for g in args.gateway],
        "transport": args.transport,
        "allow": args.allow,
        "disallow": args.disallow,
        "inbound_enabled": args.inbound,
        "outbound_leading_plus_enabled": args.leading_plus,
        "media_encryption": args.media_encryption,
        "media_encryption_optimistic": args.optimistic,
        "qualify_frequency": args.qualify_frequency,
    }

    if args.description:
        payload["description"] = args.description

    if args.auth_type == "userpass":
        if not (args.username and args.password):
            raise SystemExit("--username and --password are required for userpass auth")
        payload["auth_username"] = args.username
        payload["auth_password"] = args.password
    elif args.auth_type == "ip-based":
        if not args.ip_identifier:
            raise SystemExit("at least one --ip-identifier is required for ip-based auth")
        payload["ip_identifiers"] = [{"ip_address": ip} for ip in args.ip_identifier]

    if args.media_encryption == "sdes" and args.transport != "transport-tls":
        raise SystemExit("media_encryption=sdes requires transport=transport-tls")

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", required=True)
    parser.add_argument("--provider", required=True, help="twilio, plivo, telnyx, vonage, custom, etc.")
    parser.add_argument("--description", default=None)
    parser.add_argument("--auth-type", choices=["userpass", "ip-based"], required=True)
    parser.add_argument("--username", default=None)
    parser.add_argument("--password", default=None)
    parser.add_argument("--gateway", action="append", required=True,
                        help="host[:port] — repeat for multiple gateways")
    parser.add_argument("--ip-identifier", action="append", default=[],
                        help="CIDR ip range for ip-based auth — repeat for multiple")
    parser.add_argument("--transport", default="transport-udp",
                        choices=["transport-udp", "transport-tcp", "transport-tls"])
    parser.add_argument("--media-encryption", default="no", choices=["no", "sdes"])
    parser.add_argument("--optimistic", action="store_true",
                        help="When media_encryption=sdes, fall back to clear RTP if carrier doesn't offer crypto")
    parser.add_argument("--allow", default="ulaw,alaw")
    parser.add_argument("--disallow", default="all")
    parser.add_argument("--inbound", action="store_true", help="Set inbound_enabled=true")
    parser.add_argument("--no-leading-plus", dest="leading_plus", action="store_false",
                        help="Disable outbound_leading_plus_enabled (some carriers reject leading +)")
    parser.add_argument("--qualify-frequency", type=int, default=60)
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
        f"{API_BASE}/sip-trunks/trunks",
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

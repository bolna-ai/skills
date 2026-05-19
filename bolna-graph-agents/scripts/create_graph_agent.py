#!/usr/bin/env python3
"""Create a Bolna graph agent for appointment booking (5 nodes).

Mirrors the worked example in SKILL.md. Edit the prompts, voice IDs, and
business hours below before running. Outputs the new agent_id on stdout.

    export BOLNA_API_KEY=...
    python3 create_graph_agent.py --name "Acme Booking Agent" --voice-id Vxxxxxx
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_BASE = "https://api.bolna.ai"


def build_nodes(business_open: int, business_close: int) -> list[dict]:
    return [
        {
            "id": "welcome",
            "node_type": "static",
            "static_message": "Hi! This is Tara from Acme Dental. Are you calling to book a new appointment or reschedule an existing one?",
            "repeat_after_silence_seconds": 8,
            "edges": [
                {"to_node_id": "collect_slot", "condition": "Customer wants to book a new appointment"},
                {"to_node_id": "lookup_existing", "condition": "Customer wants to reschedule"},
                {
                    "to_node_id": "goodbye",
                    "condition": "User silent 3 times",
                    "condition_type": "expression",
                    "expression": {
                        "conditions": [{"variable": "_silence_repeats", "operator": "gte", "value": 3}]
                    },
                },
            ],
        },
        {
            "id": "collect_slot",
            "prompt": (
                "Ask the customer for their preferred day and time. Confirm the timezone is "
                "{recipient_data.timezone}. Once you have both day and time, transition to confirm."
            ),
            "repeat_after_silence_seconds": 10,
            "edges": [
                {
                    "to_node_id": "confirm",
                    "condition": "Customer provided day and time",
                    "parameters": {"appointment_day": "string", "appointment_time": "string"},
                },
                {
                    "to_node_id": "after_hours",
                    "condition": "Outside booking window",
                    "condition_type": "expression",
                    "priority": 0,
                    "expression": {
                        "logic": "or",
                        "conditions": [
                            {"variable": "recipient_data.current_hour", "operator": "lt", "value": business_open},
                            {"variable": "recipient_data.current_hour", "operator": "gte", "value": business_close},
                        ],
                    },
                },
            ],
        },
        {
            "id": "lookup_existing",
            "prompt": "Ask the customer for the phone number on their booking, then transition to collect_slot to pick a new time.",
            "edges": [
                {
                    "to_node_id": "collect_slot",
                    "condition": "Customer provided phone number",
                    "parameters": {"booking_phone": "string"},
                }
            ],
        },
        {
            "id": "confirm",
            "prompt": (
                "Confirm '{appointment_day} at {appointment_time}' with the customer. "
                "If they agree, transition to booked. If they want to change, transition back to collect_slot."
            ),
            "edges": [
                {"to_node_id": "booked", "condition": "Customer confirms the slot"},
                {"to_node_id": "collect_slot", "condition": "Customer wants to change the slot"},
            ],
        },
        {
            "id": "booked",
            "node_type": "static",
            "static_message": "All set. You'll get a confirmation SMS shortly. Thanks for choosing Acme Dental!",
            "edges": [{"to_node_id": "goodbye", "condition_type": "unconditional"}],
        },
        {
            "id": "after_hours",
            "node_type": "static",
            "static_message": "Our booking team is offline right now. I'll have them call you back during business hours. Have a great day!",
            "edges": [],
        },
        {
            "id": "goodbye",
            "node_type": "static",
            "static_message": "Thanks for calling Acme Dental. Goodbye!",
            "edges": [],
        },
    ]


def build_payload(args: argparse.Namespace) -> dict:
    return {
        "agent_config": {
            "agent_name": args.name,
            "agent_welcome_message": "Hi! This is Tara from Acme Dental.",
            "webhook_url": args.webhook_url,
            "agent_type": "other",
            "tasks": [
                {
                    "task_type": "conversation",
                    "toolchain": {
                        "execution": "parallel",
                        "pipelines": [["transcriber", "llm", "synthesizer"]],
                    },
                    "task_config": {
                        "hangup_after_silence": 10,
                        "call_terminate": 600,
                        "incremental_delay": 400,
                        "number_of_words_for_interruption": 2,
                    },
                    "tools_config": {
                        "input": {"format": "wav", "provider": args.telephony_provider},
                        "output": {"format": "wav", "provider": args.telephony_provider},
                        "llm_agent": {
                            "agent_type": "graph_agent",
                            "agent_flow_type": "streaming",
                            "llm_config": {
                                "model": "gpt-4.1-mini",
                                "max_tokens": 200,
                                "temperature": 0.2,
                                "provider": "openai",
                                "routing_model": "gpt-4.1-mini",
                                "routing_max_tokens": 250,
                                "routing_instructions": (
                                    "You are the Routing System. Analyze the user's input and "
                                    "the available edges. Select the edge whose condition best "
                                    "matches. If no edge matches, return stay_on_current_node."
                                ),
                                "agent_information": (
                                    "You are Tara, a warm and concise appointment-booking assistant "
                                    "for Acme Dental. Use at most two sentences per turn. Never quote prices."
                                ),
                                "current_node_id": "welcome",
                                "nodes": build_nodes(args.business_open, args.business_close),
                            },
                        },
                        "transcriber": {
                            "model": "nova-3",
                            "language": args.language,
                            "provider": "deepgram",
                            "stream": True,
                            "encoding": "linear16",
                            "sampling_rate": 16000,
                            "endpointing": 250,
                        },
                        "synthesizer": {
                            "provider": "elevenlabs",
                            "stream": True,
                            "buffer_size": 250,
                            "audio_format": "wav",
                            "provider_config": {
                                "model": "eleven_turbo_v2_5",
                                "voice": args.voice,
                                "voice_id": args.voice_id,
                            },
                        },
                    },
                }
            ],
        },
        "agent_prompts": {"task_1": {"system_prompt": ""}},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="Demo Booking Graph Agent")
    parser.add_argument("--webhook-url", default=None)
    parser.add_argument("--telephony-provider", default="twilio")
    parser.add_argument("--language", default="en")
    parser.add_argument("--voice", default="Nila")
    parser.add_argument("--voice-id", default="V9LCAAi4tTlqe9JadbCo")
    parser.add_argument("--business-open", type=int, default=9, help="Opening hour 0-23")
    parser.add_argument("--business-close", type=int, default=19, help="Closing hour 0-23 (exclusive)")
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
        f"{API_BASE}/v2/agent",
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

#!/usr/bin/env python3
"""Create a minimal Bolna v2 conversation agent."""

from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen


API_BASE = "https://api.bolna.ai"


def build_payload(args: argparse.Namespace) -> dict:
    return {
        "agent_config": {
            "agent_name": args.name,
            "agent_welcome_message": args.welcome,
            "webhook_url": args.webhook_url,
            "agent_type": "other",
            "tasks": [
                {
                    "task_type": "conversation",
                    "tools_config": {
                        "llm_agent": {
                            "agent_type": "simple_llm_agent",
                            "agent_flow_type": "streaming",
                            "llm_config": {
                                "provider": args.llm_provider,
                                "family": args.llm_family,
                                "model": args.llm_model,
                                "max_tokens": args.max_tokens,
                                "temperature": args.temperature,
                                "top_p": 0.9,
                                "presence_penalty": 0,
                                "frequency_penalty": 0,
                                "base_url": args.llm_base_url,
                                "request_json": False,
                            },
                        },
                        "synthesizer": {
                            "provider": args.tts_provider,
                            "provider_config": {
                                "voice": args.voice,
                                "voice_id": args.voice_id,
                                "model": args.voice_model,
                            },
                            "stream": True,
                            "buffer_size": 250,
                            "audio_format": "wav",
                        },
                        "transcriber": {
                            "provider": args.stt_provider,
                            "model": args.stt_model,
                            "language": args.language,
                            "stream": True,
                            "sampling_rate": 16000,
                            "encoding": "linear16",
                            "endpointing": args.endpointing,
                        },
                        "input": {"provider": args.telephony_provider, "format": "wav"},
                        "output": {"provider": args.telephony_provider, "format": "wav"},
                        "api_tools": None,
                    },
                    "toolchain": {
                        "execution": "parallel",
                        "pipelines": [["transcriber", "llm", "synthesizer"]],
                    },
                    "task_config": {
                        "hangup_after_silence": 10,
                        "incremental_delay": 400,
                        "number_of_words_for_interruption": 2,
                        "hangup_after_LLMCall": False,
                        "call_cancellation_prompt": None,
                        "backchanneling": False,
                        "backchanneling_message_gap": 5,
                        "backchanneling_start_delay": 5,
                        "ambient_noise": False,
                        "ambient_noise_track": "office-ambience",
                        "call_terminate": args.call_terminate,
                        "voicemail": False,
                        "inbound_limit": -1,
                        "whitelist_phone_numbers": None,
                        "disallow_unknown_numbers": False,
                    },
                }
            ],
            "ingest_source_config": None,
        },
        "agent_prompts": {"task_1": {"system_prompt": args.prompt}},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--welcome", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--webhook-url", default=None)
    parser.add_argument("--language", default="en")
    parser.add_argument("--telephony-provider", default="twilio")
    parser.add_argument("--llm-provider", default="openai")
    parser.add_argument("--llm-family", default="openai")
    parser.add_argument("--llm-model", default="gpt-4.1-mini")
    parser.add_argument("--llm-base-url", default="https://api.openai.com/v1")
    parser.add_argument("--max-tokens", type=int, default=150)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--tts-provider", default="elevenlabs")
    parser.add_argument("--voice", default="Nila")
    parser.add_argument("--voice-id", default="V9LCAAi4tTlqe9JadbCo")
    parser.add_argument("--voice-model", default="eleven_turbo_v2_5")
    parser.add_argument("--stt-provider", default="deepgram")
    parser.add_argument("--stt-model", default="nova-3")
    parser.add_argument("--endpointing", type=int, default=250)
    parser.add_argument("--call-terminate", type=int, default=300)
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

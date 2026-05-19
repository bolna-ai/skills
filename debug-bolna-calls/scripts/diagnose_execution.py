#!/usr/bin/env python3
"""Pull a Bolna execution + raw logs and print a one-page diagnosis.

Highlights:
- Status, error_message, duration, cost
- Latency breakdown (transcriber / LLM / synth) with thresholds
- Hangup data
- Tool calls with params
- First obvious problem found

Usage:
    python3 diagnose_execution.py --execution-id <UUID>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_BASE = "https://api.bolna.ai"

THRESHOLDS = {
    "audio_to_text_latency": (50, 100),
    "llm_time_to_first_token": (500, 1000),
    "synth_time_to_first_token": (300, 500),
}


def fetch(path: str, token: str) -> dict:
    req = Request(
        f"{API_BASE}{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        method="GET",
    )
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def classify(value, healthy_max: int, concerning_max: int) -> str:
    if value is None:
        return "—"
    if value <= healthy_max:
        return "OK"
    if value <= concerning_max:
        return "WARN"
    return "BAD"


def diagnose(ex: dict, logs: dict | None) -> dict:
    out: dict = {
        "status": ex.get("status"),
        "error_message": ex.get("error_message"),
        "conversation_duration": ex.get("conversation_duration"),
        "total_cost": ex.get("total_cost"),
    }

    tel = ex.get("telephony_data") or {}
    out["telephony"] = {
        "provider": tel.get("provider"),
        "duration": tel.get("duration"),
        "recording_url_present": bool(tel.get("recording_url")),
        "hangup_by": tel.get("hangup_by"),
        "hangup_reason": tel.get("hangup_reason"),
        "hangup_code": tel.get("hangup_code"),
        "post_dial_delay": tel.get("post_dial_delay"),
    }

    lat = ex.get("latency_data") or {}
    transcriber = lat.get("transcriber") or {}
    llm = lat.get("llm") or {}
    synth = lat.get("synthesizer") or {}

    first_user_seq = None
    if transcriber.get("turns"):
        seqs = transcriber["turns"][0].get("turn_latency") or []
        if seqs:
            first_user_seq = seqs[-1].get("audio_to_text_latency")

    first_llm_ttft = (llm.get("turns") or [{}])[0].get("time_to_first_token")
    first_synth_ttft = (synth.get("turns") or [{}])[0].get("time_to_first_token")

    out["latency"] = {
        "time_to_first_audio_ms": lat.get("time_to_first_audio"),
        "transcriber_audio_to_text_ms": first_user_seq,
        "transcriber_status": classify(first_user_seq, *THRESHOLDS["audio_to_text_latency"]),
        "llm_time_to_first_token_ms": first_llm_ttft,
        "llm_status": classify(first_llm_ttft, *THRESHOLDS["llm_time_to_first_token"]),
        "synth_time_to_first_token_ms": first_synth_ttft,
        "synth_status": classify(first_synth_ttft, *THRESHOLDS["synth_time_to_first_token"]),
        "region": lat.get("region"),
    }

    out["extracted_data_keys"] = list((ex.get("extracted_data") or {}).keys())

    if logs:
        tool_calls = []
        for entry in logs.get("data", []):
            if entry.get("component") == "tool":
                tool_calls.append({
                    "name": entry.get("tool_name"),
                    "type": entry.get("type"),
                    "data_preview": str(entry.get("data"))[:200],
                })
        out["tool_calls"] = tool_calls

    likely_issue = []
    if out["latency"]["llm_status"] == "BAD":
        likely_issue.append("LLM time_to_first_token > 1000ms — bottleneck on LLM provider/model.")
    if out["latency"]["transcriber_status"] == "BAD":
        likely_issue.append("Transcriber latency > 100ms per sequence — provider/network issue.")
    if out["latency"]["synth_status"] == "BAD":
        likely_issue.append("Synthesizer first-audio > 500ms — TTS provider/voice issue.")
    if ex.get("status") == "balance-low":
        likely_issue.append("Account wallet balance too low — top up.")
    if ex.get("status") in {"failed", "error"} and ex.get("error_message"):
        likely_issue.append(f"Execution {ex['status']}: {ex['error_message']}")
    if out["telephony"]["hangup_reason"] == "inactivity_timeout":
        likely_issue.append("Call hung up on silence — `hangup_after_silence` may be too low.")
    if not likely_issue:
        likely_issue.append("No obvious issue from execution + log scan. Inspect raw logs for content-level problems.")

    out["likely_issues"] = likely_issue
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--execution-id", required=True)
    parser.add_argument("--skip-logs", action="store_true")
    args = parser.parse_args()

    token = os.environ.get("BOLNA_API_KEY")
    if not token:
        print("BOLNA_API_KEY is not set", file=sys.stderr)
        return 2

    try:
        ex = fetch(f"/executions/{args.execution_id}", token)
        logs = None if args.skip_logs else fetch(f"/executions/{args.execution_id}/log", token)
    except HTTPError as exc:
        print(exc.read().decode("utf-8", errors="replace"), file=sys.stderr)
        return 1

    print(json.dumps(diagnose(ex, logs), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

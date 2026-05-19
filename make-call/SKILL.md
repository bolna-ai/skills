---
name: make-call
description: "Initiate, schedule, personalize, retry, and stop outbound Bolna Voice AI calls. Use when the user wants to test an agent, call a recipient, schedule a callback, pass user_data dynamic variables, override a same-provider voice, or cancel a queued or scheduled call."
license: MIT
compatibility: Requires internet access and a Bolna API key (BOLNA_API_KEY).
metadata:
  openclaw:
    requires:
      env:
        - BOLNA_API_KEY
    primaryEnv: BOLNA_API_KEY
---

# Make Bolna Calls

## Endpoints

- Make call: `POST https://api.bolna.ai/call`
- Stop one queued or scheduled call: `POST https://api.bolna.ai/call/{execution_id}/stop`
- Inspect results: use `get-executions` with the returned `execution_id`.

## Required fields

- `agent_id`: Bolna agent UUID.
- `recipient_phone_number`: E.164 recipient phone number, for example `+919876543210`.

## Optional fields

- `from_phone_number`: E.164 sender number. Omit when using Bolna default outbound numbers.
- `scheduled_at`: ISO 8601 datetime with timezone, for example `2026-05-19T18:30:00+05:30`.
- `user_data`: dynamic variables referenced in prompts or welcome messages, for example `{customer_name}`.
- `agent_data.voice_id`: override voice within the same configured TTS provider only.
- `bypass_call_guardrails`: when true, skip agent calling window checks for this call. Use only for testing, emergencies, or explicitly approved priority calls.
- `retry_config`: retry failed calls for no answer, busy, failed, error, or voicemail cases.

## Immediate call

```bash
curl --request POST \
  --url https://api.bolna.ai/call \
  --header "Authorization: Bearer $BOLNA_API_KEY" \
  --header "Content-Type: application/json" \
  --data '{
    "agent_id": "123e4567-e89b-12d3-a456-426655440000",
    "recipient_phone_number": "+919876543210",
    "user_data": {
      "customer_name": "Amitesh",
      "plan": "Pro"
    }
  }'
```

Expected response:

```json
{
  "message": "done",
  "status": "queued",
  "execution_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

Always save `execution_id`; it is the join key for webhooks and execution lookups.

## Scheduled call

```json
{
  "agent_id": "123e4567-e89b-12d3-a456-426655440000",
  "recipient_phone_number": "+919876543210",
  "scheduled_at": "2026-05-19T18:30:00+05:30",
  "bypass_call_guardrails": false
}
```

Avoid timezone-less datetime strings.

## Guardrails

If the agent has `calling_guardrails.call_start_hour` and `call_end_hour`, Bolna evaluates those against the recipient's local timezone. Outside the allowed window, the call can be rescheduled instead of placed immediately. Use `bypass_call_guardrails: true` only when the user explicitly wants to ignore that time window.

## Retry config

```json
{
  "retry_config": {
    "enabled": true,
    "max_retries": 2,
    "retry_on_statuses": ["no-answer", "busy", "failed", "error"],
    "retry_on_voicemail": false,
    "retry_intervals_minutes": [30, 60]
  }
}
```

For high-volume campaigns, remember that retries consume concurrency and can overlap with batches.

## Stop a queued or scheduled call

```bash
curl --request POST \
  --url "https://api.bolna.ai/call/$EXECUTION_ID/stop" \
  --header "Authorization: Bearer $BOLNA_API_KEY"
```

This cannot stop a call already in progress.

## Script

```bash
# One-off call
python3 make-call/scripts/make_call.py \
  --agent-id "$AGENT_ID" \
  --recipient "+919876543210" \
  --user-data '{"customer_name":"Amitesh"}'

# Scheduled call (timezone-aware)
python3 make-call/scripts/schedule_call.py \
  --agent-id "$AGENT_ID" \
  --recipient "+919876543210" \
  --at "2026-05-22T15:30:00+05:30"

# Bulk one-off calls from a CSV (for ad-hoc fan-outs; use `create-batch` for proper campaigns)
python3 make-call/scripts/bulk_make_calls.py \
  --agent-id "$AGENT_ID" \
  --file recipients.csv
```

## See also

- `create-batch` — proper CSV-based campaigns with monitoring, retry, and stop endpoints.
- `get-executions` — fetch the result of a queued call via the returned `execution_id`.
- `setup-webhook` — receive call updates in real time instead of polling.
- `../references/call-statuses.md` — interpreting status transitions.
- `bolna-graph-agents/scripts/inject_event.py` — for graph agents, push real-time events into a live call.

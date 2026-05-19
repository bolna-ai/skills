---
name: make-call
description: "Initiate, schedule, personalize, retry, and stop outbound Bolna Voice AI calls. Use when the user wants to test an agent, call a recipient, schedule a callback, pass user_data dynamic variables, override a same-provider voice, or cancel a queued or scheduled call."
license: MIT
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
  "scheduled_at": "2026-05-19T18:30:00+05:30"
}
```

Avoid timezone-less datetime strings.

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
python3 make-call/scripts/make_call.py \
  --agent-id "$AGENT_ID" \
  --recipient "+919876543210" \
  --user-data '{"customer_name":"Amitesh"}'
```

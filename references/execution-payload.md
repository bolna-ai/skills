# Execution Payload Reference

The execution object is the single shape returned by:

- `GET /executions/{execution_id}` — full execution detail
- `GET /v2/agent/{agent_id}/executions` — list (envelope under `data[]`)
- `GET /batches/{batch_id}/executions` — list for a batch
- Webhook POSTs delivered to your `webhook_url`

Webhook and API responses share the schema, so a webhook handler can reuse the same parser.

## Top-level fields

| Field | Type | Notes |
|---|---|---|
| `id` | integer | Bolna's internal execution id. |
| `agent_id` | uuid | Agent that ran the call. |
| `batch_id` | uuid \| null | Set when the call belongs to a batch. |
| `status` | string | Current lifecycle status. See `call-statuses.md`. |
| `error_message` | string \| null | Human-readable reason on failure. |
| `conversation_duration` | int (seconds) | Time the call was actually in conversation. |
| `total_cost` | number | Bolna cost in account currency. |
| `answered_by_voice_mail` | bool | Voicemail detection result. |
| `transcript` | string | Plain-text conversation. |
| `created_at` / `updated_at` | ISO 8601 | Lifecycle timestamps. |
| `usage_breakdown` | object | Per-provider usage. See below. |
| `telephony_data` | object | Provider, numbers, recording, ring/PDD. See below. |
| `transfer_call_data` | object \| null | Set when `transfer_call` fired. |
| `batch_run_details` | object \| null | Set when the call is part of a batch. |
| `extracted_data` | object | Dispositions/extractions output. See `create-disposition`. |
| `context_details` | object | Final `context_data` (graph agents). |
| `extraction_webhook_status` | bool | Whether downstream extraction webhook delivered. |

## `usage_breakdown`

```json
{
  "synthesizer_characters": 1245,
  "synthesizer_model": "elevenlabs:eleven_turbo_v2_5",
  "transcriber_duration": 87,
  "transcriber_model": "deepgram:nova-3",
  "llm_tokens": 1854,
  "llm_model": {
    "gpt-4.1-mini": { "output": 412, "input": 1442 }
  }
}
```

Use this for cost reconciliation and to spot model drift across calls.

## `telephony_data`

```json
{
  "duration": 42,
  "to_number": "+10123456789",
  "from_number": "+1987654007",
  "recording_url": "https://bolna-call-recordings.s3.us-east-1.amazonaws.com/...",
  "hosted_telephony": true,
  "provider_call_id": "CA42fb13614bfcfeccd94cf33befe14s2f",
  "call_type": "outbound",
  "provider": "twilio",
  "ring_duration": 17,
  "post_dial_delay": 1,
  "to_number_carrier": "Reliance Jio Infocomm Ltd (RJIL)"
}
```

- `recording_url` is presigned and expires. Download or store the file if you need long-term access.
- `post_dial_delay` is the time between dial and ring start. High PDD usually means a routing problem on the provider side.

## `transfer_call_data`

Present only on calls where the agent transferred to a human or external number.

```json
{
  "provider_call_id": "...",
  "status": "completed",
  "duration": 42,
  "cost": 0.012,
  "to_number": "+10123456789",
  "from_number": "+1987654007",
  "recording_url": "https://...",
  "hangup_by": "Caller",
  "hangup_reason": "Normal Hangup"
}
```

## Webhook delivery

- **From IP** `13.203.39.153` — whitelist this single address.
- **Method** `POST` with the JSON above as the body.
- **Idempotency key** is the execution `id` (or `provider_call_id` if you care about the carrier-level identity). Multiple status transitions fire multiple webhooks for the same execution; dedupe by `id` + `status`.
- **Order** is generally `scheduled` → `queued` → `initiated` → `ringing` → `in-progress` → `call-disconnected` → `completed`, but networks can reorder. Treat each webhook as the *latest known state*, not a delta.
- **Retries**: Bolna retries on non-2xx. Return `2xx` even when you intend to queue follow-up work, and process asynchronously.

See `setup-webhook` for a minimal receiver and verification recipe.

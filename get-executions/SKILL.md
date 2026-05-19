---
name: get-executions
description: "Fetch and analyze Bolna call execution data, raw logs, transcripts, recordings, costs, statuses, hangup details, extracted data, agent history, and batch executions. Use for debugging failed calls, analytics export, CRM sync, webhook reconciliation, and call monitoring."
license: MIT
compatibility: Requires internet access and a Bolna API key (BOLNA_API_KEY).
metadata:
  openclaw:
    requires:
      env:
        - BOLNA_API_KEY
    primaryEnv: BOLNA_API_KEY
---

# Get Bolna Executions

## Endpoints

- Get execution: `GET https://api.bolna.ai/executions/{execution_id}`
- Get raw logs: `GET https://api.bolna.ai/executions/{execution_id}/log`
- List agent executions: `GET https://api.bolna.ai/v2/agent/{agent_id}/executions`
- List batch executions: `GET https://api.bolna.ai/batches/{batch_id}/executions`

Use `Authorization: Bearer $BOLNA_API_KEY`.

## Execution object

Expect fields such as:

- `id`, `agent_id`, `batch_id`
- `conversation_time`, `total_cost`, `cost_breakdown`
- `status`, `error_message`, `answered_by_voice_mail`
- `transcript`, `recording_url`
- `created_at`, `updated_at`
- `telephony_data`: provider, to/from numbers, call type, provider call ID, hangup reason/code, ring duration, post-dial delay, carrier details.
- `transfer_call_data`: details for transferred calls.
- `batch_run_details`: retry and batch metadata.
- `extracted_data`: structured data from dispositions or extraction prompts.
- `context_details`: context variables and related metadata.

## Statuses to handle

Common statuses include `scheduled`, `queued`, `rescheduled`, `initiated`, `ringing`, `in-progress`, `call-disconnected`, `completed`, `balance-low`, `busy`, `no-answer`, `canceled`, `failed`, `stopped`, and `error`.

Treat `completed` as the post-processing finished state, not merely the end of audio.

## Single execution

```bash
curl --request GET \
  --url "https://api.bolna.ai/executions/$EXECUTION_ID" \
  --header "Authorization: Bearer $BOLNA_API_KEY"
```

## Raw logs

```bash
curl --request GET \
  --url "https://api.bolna.ai/executions/$EXECUTION_ID/log" \
  --header "Authorization: Bearer $BOLNA_API_KEY"
```

Use raw logs for latency debugging, prompt inspection, provider request/response issues, tool call failures, or unexpected model output.

## Paginated agent history

```bash
curl --request GET \
  --url "https://api.bolna.ai/v2/agent/$AGENT_ID/executions?page_number=1&page_size=50" \
  --header "Authorization: Bearer $BOLNA_API_KEY"
```

Use `has_more` to fetch the next page. `page_size` max is 50.

## Debug map

- Long pauses: check transcriber endpointing, LLM latency, synthesizer latency, and `incremental_delay`.
- Users cut off: increase `number_of_words_for_interruption` or adjust endpointing.
- Silent hangups: check `hangup_after_silence`, `call_terminate`, and hangup code.
- No webhook received: pull execution status here, then check `setup-webhook` configuration.
- Cost spike: inspect `conversation_time`, retry history, and `cost_breakdown`.

For the full triage runbook, see `debug-bolna-calls/SKILL.md` and `debug-bolna-calls/references/latency-metrics.md`.

## Script

```bash
# Paginate through all executions for an agent
python3 get-executions/scripts/fetch_executions_paginated.py --agent-id $AGENT_ID
```

## See also

- `../references/execution-payload.md` — every field on the execution object, in one place.
- `../references/call-statuses.md` — full lifecycle and terminal-status patterns.
- `../references/hangup-codes.md` — `hangup_by` + `hangup_code` + `hangup_reason` interpretation.
- `setup-webhook` — same payload shape, pushed in real time.
- `debug-bolna-calls` — symptom-to-fix table built on top of execution + raw logs.

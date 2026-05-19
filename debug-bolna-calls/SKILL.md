---
name: debug-bolna-calls
description: "Diagnose Bolna voice-agent issues: robotic / laggy responses, agent interrupting users or never interrupting, long silences, premature hangups, webhook misses, wrong caller context, batch failures, SIP/SRTP no-audio, agent restricted by content policy, balance-low queueing, and provider connection latency. Maps symptoms to the exact field on the agent (`task_config`, `endpointing`, `incremental_delay`, `number_of_words_for_interruption`), and uses `latency_data` from `GET /executions/{id}` + raw logs to pinpoint which pipeline component (transcriber, LLM, synthesizer) is slow."
license: MIT
compatibility: Requires internet access and a Bolna API key (BOLNA_API_KEY) to inspect executions and raw logs.
metadata:
  openclaw:
    requires:
      env:
        - BOLNA_API_KEY
    primaryEnv: BOLNA_API_KEY
---

# Debug Bolna Calls

A symptom-to-fix runbook for Bolna voice agents. Most issues fall into a few well-known patterns; the tables below map the symptom to the exact field to change and the API call that verifies the fix.

## Triage in 30 seconds

Ask the user (or pull from logs) for:

| Item | Why |
|---|---|
| `execution_id` | The single most useful thing — every other diagnostic flows from it. |
| `agent_id` | To inspect agent config side-by-side. |
| `batch_id` (if applicable) | Batch context affects retries and concurrency. |
| Recipient / sender phone numbers | E.164 issues, carrier coverage. |
| Approximate call time | Cross-reference rate-limit / outage windows. |
| Observed symptom | One sentence. "Agent goes silent for 4 seconds before responding." |

Then pull the two execution views:

```bash
# Full execution: status, costs, transcript, latency_data, telephony_data, extracted_data
curl "https://api.bolna.ai/executions/$EXECUTION_ID" \
  -H "Authorization: Bearer $BOLNA_API_KEY"

# Raw logs: every prompt/request/response, including LLM reasoning_content when available
curl "https://api.bolna.ai/executions/$EXECUTION_ID/log" \
  -H "Authorization: Bearer $BOLNA_API_KEY"
```

The execution payload has `latency_data` — the source of truth for "why is the call slow." See `references/latency-metrics.md`.

## Symptom → fix

### "Agent goes silent for ages before responding"

Look at `latency_data` in `GET /executions/{id}`:

| Slow component | Fix |
|---|---|
| `transcriber.turns[].turn_latency[].audio_to_text_latency > 100ms` per sequence | Switch transcriber provider; check audio quality; rule out network issues to Deepgram/Sarvam. |
| `llm.turns[].time_to_first_token > 1000ms` | Switch LLM (Azure GPT-4.1-mini for low latency); shorten prompt; check provider health. |
| `synthesizer.turns[].time_to_first_token > 500ms` | Switch TTS (ElevenLabs turbo_v2_5, Cartesia); pick a lighter voice; check provider load. |
| `transcriber.time_to_connect`, `llm.time_to_connect`, `synthesizer.time_to_connect` high | Cold start. First turn of every call is slower; if it's chronic across turns, escalate to provider. |

Also tune on the agent side:

- `task_config.incremental_delay` — buffer time before agent commits to speaking. Default `400ms`. Lower this for faster response (but you may interrupt yourself on partial transcripts). Higher for noisier audio.
- `transcriber.endpointing` — how long the STT waits in silence before "finalising" the user's turn. Default `250ms`. Lower for quick conversational turns, higher for thoughtful users / long pauses.

### "Agent interrupts me when I'm still talking"

`task_config.number_of_words_for_interruption` is too low (default `2`).

- Bump to `4` or `5` for "let the user finish their sentence."
- Combine with `transcriber.endpointing: 500-700` for users who pause mid-sentence.

### "Agent never interrupts — keeps talking over me"

Opposite of above. Lower `number_of_words_for_interruption` (try `1` for very responsive agents). Also check that the transcriber is actually capturing the user — `latency_data.transcriber.turns[]` should grow with each user utterance. If transcripts are missing, the agent literally can't hear the interruption.

### "Call hangs up after a silence on the user's side"

`task_config.hangup_after_silence` (default `10` seconds). Increase for callers who think before speaking, decrease for IVR-style flows.

For graph agents, prefer `repeat_after_silence_seconds` on individual nodes plus an expression edge on `_silence_repeats` — gracefully escalates instead of hanging up.

### "Call ends too soon after the agent speaks"

Two likely settings:

- `task_config.hangup_after_LLMCall: true` — call ends immediately after the agent's first response. Use only for one-shot announcements.
- `task_config.call_terminate` — hard duration cap in seconds. Default `300` (5 min). Bump for longer use cases.
- LLM-prompted hangup in the system prompt ("if the user says goodbye, hang up"). Loosen the trigger if it's firing too eagerly.

### "Agent sounds robotic / awkward / over-narrating"

- Cap response length in the system prompt: `"Never speak more than two sentences per turn."`
- Pick a higher-quality voice: ElevenLabs turbo_v2_5 / multilingual_v2; Sarvam for Indian languages.
- Enable backchanneling **only if it fits** (`task_config.backchanneling: true`) — "mhm" between user phrases. Excellent for support calls, weird in IVR-style flows.
- Lower `temperature` to `0.2-0.3` — long-tail creativity isn't worth the inconsistency.
- For Indian languages: write the prompt in **native script** (Devanagari), not phonetic English. See `../references/prompting-tips.md`.

### "Call stays in `queued` forever"

| Check | Reason |
|---|---|
| Agent concurrency limit (`GET /user/me`) | You're at cap; queued calls wait for one to finish. |
| `calling_guardrails.call_start_hour` / `call_end_hour` | Call placed outside the allowed window — Bolna reschedules. |
| `scheduled_at` in the future | The call is waiting for the scheduled time. |
| Wallet balance | If `status` becomes `balance-low`, you ran out of credits. |
| Retry config | Failed calls may be queued for retry intervals — check `retry_intervals_minutes`. |

### Status: `balance-low`

Top up the account wallet. Until then, every `POST /call` will land here. Verify with:

```bash
curl https://api.bolna.ai/user/me -H "Authorization: Bearer $BOLNA_API_KEY"
```

Look at `wallet`.

### Status: `failed` / `error`

Check `error_message` on the execution. Common causes:

| `error_message` clue | Fix |
|---|---|
| `from_phone_number not owned by account` | Use a number you actually own; check via `GET /phone-numbers/all`. |
| `invalid phone number format` | E.164 only. `+91...`, not `91...` or `091...`. |
| `agent restricted due to disallowed content` | Bolna's content checker flagged the prompt. Review and re-save the agent. |
| `concurrency limit reached` | Wait, or upgrade the account. |
| `provider auth failed` | Re-add the provider's credentials (Twilio/Plivo/etc.). |

### "No answer / busy"

These are normal outcomes, not agent failures. Use `retry_config` on `POST /call` to retry automatically:

```json
{
  "retry_config": {
    "enabled": true,
    "max_retries": 2,
    "retry_on_statuses": ["no-answer", "busy"],
    "retry_intervals_minutes": [30, 60]
  }
}
```

Don't add `failed` / `error` to `retry_on_statuses` unless you've confirmed the cause is transient.

### "Webhook never fires" / "Webhook fires but my server doesn't receive it"

Walk these in order:

1. `agent_config.webhook_url` set on the agent? (Inspect with `GET /v2/agent/{id}`.)
2. URL publicly reachable on HTTPS? Test with `curl -X POST https://your-server/webhook -d '{}'`.
3. Server returns `2xx` to Bolna's POST? Non-2xx triggers Bolna's retry, but eventually stops.
4. Firewall whitelists Bolna's source IP `13.203.39.153`?
5. Deduping by `execution_id` + `status`? Bolna POSTs on every status transition — multiple events per call is normal.
6. Receiver doesn't timeout (~10s)? If it does, return `2xx` immediately and process async.

See `../references/execution-payload.md` for the shape.

### "Caller context (`{customer_name}` etc.) is wrong"

| Source | Check |
|---|---|
| Outbound `POST /call` | `user_data` keys match prompt variables exactly (case-sensitive). |
| Batch CSV | Column name = variable name. `customer_name` not `Customer Name` or `customer-name`. |
| Inbound `ingest_source_config` (API) | Endpoint returns matching JSON keys. Test with the exact `contact_number` Bolna sends. |
| Inbound CSV / Google Sheet | `contact_number` column present and in E.164 format. |

### "Transcript looks wrong / has half-formed agent sentences"

Enable **Precise Transcript Generation** in the agent's Analytics Tab (beta). When the user interrupts the agent, Bolna trims the agent's unsaid words from the transcript so it reflects what was actually heard.

Without it, transcripts show what the LLM *intended* to say; with it, they show what the caller *heard*.

### SIP trunk: "call connects but no audio"

Classic SRTP mismatch. See `setup-sip-trunk/SKILL.md` § Troubleshooting. Quick fixes:

- `media_encryption: "no"` for testing.
- `media_encryption_optimistic: true` to fall back to clear RTP automatically.
- Confirm carrier has SRTP enabled if you intend to keep `sdes`.

### SIP trunk: "outbound INVITE silently fails"

Likely UDP fragmentation on large SIP headers. Switch `transport: "transport-tcp"`.

### Batch: "lots of calls failed / weren't placed"

| Issue | Where to look |
|---|---|
| CSV column name wrong | Must be `contact_number` for the recipient. Other columns become variables. |
| `valid_contacts < total_contacts` | Some rows had bad phone numbers — check `GET /batches/{id}` summary. |
| Per-call retry config blows concurrency | Each retry takes a concurrency slot. If batch + retry overlap, you can stall yourself. |
| Provider-level rejection | `GET /batches/{id}/executions` → look at `status` + `error_message` per call. |

### Indian numbers: 140 / 160-series rejected

Compliance: the DLT registration, header registration, or template registration is incomplete. See `../references/india-compliance.md`. **Not a Bolna API failure** — the carrier rejects before Bolna can dial.

## Inspecting raw logs

`GET /executions/{id}/log` returns every prompt, request, and response in order. Each entry has:

| Field | What it tells you |
|---|---|
| `component` | `transcriber`, `llm`, `synthesizer`, `tool`, `system` |
| `type` | `request`, `response`, `event` |
| `data` | The actual payload (for LLM responses, this is the assistant text) |
| `reasoning_content` | LLM reasoning summary if the model exposes it (GPT-5 class, Claude with extended thinking) |
| `timestamp` | When this fired |

Useful patterns:

- Find a wrong agent response → search for `component: "llm"` + `type: "response"` near the timestamp.
- Tool not called → grep for the tool name in `component: "llm"` entries; if absent, the LLM never picked it.
- Tool called with wrong params → `component: "tool"` + `type: "request"` shows the exact substituted payload.

The raw logs are the most powerful debugging tool Bolna provides. Use them before assuming there's a platform bug.

## Going deeper

| File | Contents |
|---|---|
| `references/latency-metrics.md` | `latency_data` fields explained with thresholds. |
| `references/symptoms.md` | Extended symptom → cause → fix matrix (covers ~30 patterns). |
| `references/raw-logs.md` | Reading `/executions/{id}/log`: what each component logs, and reasoning_content. |
| `scripts/diagnose_execution.py` | Pulls `GET /executions/{id}` + raw logs, prints a one-page diagnosis. |

## See also

- `get-executions` — full `/executions/{id}` and `/executions/{id}/log` reference.
- `../references/call-statuses.md` — what each status means.
- `../references/hangup-codes.md` — interpreting `hangup_by` + `hangup_code` + `hangup_reason`.
- `setup-tools/references/tool-schemas.md` — debugging tool-trigger problems.
- `bolna-graph-agents/references/debugging.md` — routing-log debugging for graph agents specifically.

---
name: debug-bolna-calls
description: "Debug Bolna voice calls using executions, raw logs, transcripts, latency metrics, status and hangup codes, provider setup, webhook delivery, interruption tuning, silence settings, and batch retry behavior. Use when calls fail, sound robotic, pause too long, interrupt users, or miss webhooks."
license: MIT
compatibility: "Requires BOLNA_API_KEY for live execution inspection."
---

# Debug Bolna Calls

## First collect

Ask for or find:

- `execution_id`
- `agent_id`
- `batch_id` if applicable
- recipient and from phone numbers
- approximate call time
- observed symptom

Then use `get-executions`:

```bash
curl --request GET \
  --url "https://api.bolna.ai/executions/$EXECUTION_ID" \
  --header "Authorization: Bearer $BOLNA_API_KEY"
```

For model/provider-level debugging:

```bash
curl --request GET \
  --url "https://api.bolna.ai/executions/$EXECUTION_ID/log" \
  --header "Authorization: Bearer $BOLNA_API_KEY"
```

## Symptom map

- `401` or auth failure: run `setup-api-key`.
- Call stays queued: inspect concurrency, guardrails, scheduled time, and wallet balance.
- `balance-low`: account wallet must be topped up.
- No answer or busy: retry config may help; do not treat as agent failure.
- Long silence before responses: inspect LLM latency, TTS latency, transcriber endpointing, and `incremental_delay`.
- Agent interrupts too aggressively: increase `number_of_words_for_interruption` or endpointing.
- Agent never interrupts: reduce `number_of_words_for_interruption` and endpointing carefully.
- Robotic or awkward flow: shorten prompt, reduce overlong lists, tune voice, enable backchanneling only when appropriate.
- Call drops after silence: check `hangup_after_silence`.
- Call ends too soon: check `call_terminate`, hangup prompts, and tool transfer behavior.
- Wrong caller context: verify `user_data`, batch CSV headers, or inbound `ingest_source_config`.
- Webhook missing: verify `webhook_url`, public HTTPS reachability, receiver 2xx response, and idempotent storage by execution ID.

## Batch-specific checks

- CSV must use `contact_number` for recipients.
- Retry config is per call and can increase concurrency usage.
- Check `valid_contacts` versus `total_contacts`.
- Use batch executions to inspect per-recipient failures.

## Provider checks

- LLM, transcriber, synthesizer, and telephony provider credentials must be present in Bolna providers or account settings.
- For BYOT/SIP, check trunk registration, origination URI, SRTP, codec, and DID mapping.
- For Indian numbers, verify compliance approval before assuming API failure.

## Output

Return a concise diagnosis with:

- observed status
- likely root cause
- exact config or endpoint to change
- one verification call or API check

# Symptom Matrix

Extended symptom → cause → fix table. Use as a checklist when triaging.

## Latency / responsiveness

| Symptom | Probable cause | Fix |
|---|---|---|
| Long silence (>1s) before first agent words | High LLM `time_to_first_token` | Switch to faster LLM (Azure gpt-4.1-mini), shorten system prompt |
| Long silence before *every* agent turn | High transcriber `audio_to_text_latency` or `endpointing` too high | Verify transcriber latency in `latency_data`; lower `endpointing` cautiously |
| Long silence only between turns | `incremental_delay` too high | Lower from default `400ms` to `200-300ms` |
| TTS sounds halting / chunked | TTS `time_to_first_token` high, or `stream: false` | Confirm `stream: true`, lower `buffer_size`, switch to streaming-first TTS |
| Robotic monotone delivery | Voice model not optimised for the language | Switch voice (ElevenLabs turbo_v2_5 for English, Sarvam for Hindi/Indian) |
| Slow first call, then fine | Cold start (`time_to_connect`) | Normal; if persistent across turns, escalate |

## Interruption

| Symptom | Probable cause | Fix |
|---|---|---|
| Agent interrupts user mid-sentence | `number_of_words_for_interruption` too low | Raise from `2` to `4` or `5`; raise `endpointing` to `500-700ms` |
| Agent never stops when user starts talking | `number_of_words_for_interruption` too high, or transcriber not picking up user audio | Lower to `1-2`; verify transcriber `turns[]` actually has the user audio |
| Agent talks over user during DTMF | DTMF input not registering as a "speech" turn for interruption purposes | Have the agent ask the user to stop speaking before pressing keys; or rely on the explicit `#` terminator |
| Agent says "Sorry, I didn't catch that" mid-utterance | STT confidence low on partials; transcriber re-finalising | Raise `endpointing`; switch to a more accurate transcriber for the language |

## Silence / hangups

| Symptom | Probable cause | Fix |
|---|---|---|
| Call hangs up after user silence | `hangup_after_silence` (default `10s`) | Raise for thoughtful audiences; lower for IVR-like flows |
| Call hangs up unexpectedly mid-conversation | `call_terminate` hit, or LLM-prompted hangup | Raise `call_terminate`; loosen hangup phrasing in system prompt |
| Agent says one line and ends call | `hangup_after_LLMCall: true` | Set to `false` unless this is a one-shot announcement agent |
| Call ends immediately after agent's first sentence | Empty user turn registers as conversation end | Adjust `endpointing` and ensure prompt asks an opening question to anchor the user |
| Voicemail picked up but no message | `voicemail` detection disabled, or message not configured | Enable `voicemail` in `task_config`, configure the agent's voicemail prompt |

## Wrong content

| Symptom | Probable cause | Fix |
|---|---|---|
| `{variable}` literals in agent speech | Variable not provided in `user_data` / CSV / `ingest_source_config` | Provide the value; add a fallback in the prompt ("If you don't know X, say...") |
| Agent uses wrong customer name | `user_data` key mismatch with `{variable}` in prompt — case-sensitive | Compare exact strings between prompt and payload |
| Agent answers wrong question (knowledgebase) | `vector_id` not attached, or KB not yet processed | Verify `GET /knowledgebase/{rag_id}.status == "processed"` and that `vector_id` is in the agent's `vector_store.provider_config.vector_ids[]` |
| Agent ignores tool / never calls it | Tool description too vague | Rewrite with synonyms and explicit "when to use" guidance |
| Agent calls tool too often | Description too broad | Add exclusions ("not for X, use tool Y instead") |
| Tool fails with 4xx | Wrong URL, auth, or headers | Test with `curl` first; verify `api_token` includes `Bearer ` prefix |
| Agent refuses with "I cannot help with that" | Bolna content-policy block on the prompt | Review prompt for political/illegal/explicit content; re-save to re-validate |

## Telephony

| Symptom | Probable cause | Fix |
|---|---|---|
| `from_phone_number not owned` | Number not registered to your account | `GET /phone-numbers/all`; if BYOT, register on the SIP trunk first |
| `invalid phone number format` | Missing `+` or country code | E.164 only: `+91XXXXXXXXXX` |
| Indian 140/160 number rejected | Compliance not complete (DLT / Header / Template) | See `india-compliance.md` |
| SIP trunk: silent call after answer | SRTP / media encryption mismatch | `media_encryption: "no"` or `optimistic: true` |
| SIP trunk: outbound silently fails | UDP fragmentation | `transport: "transport-tcp"` |
| Carrier hangup with `Carrier ended because call limit exceeded` | Carrier-side duration cap (typical: 1 hour) | Lower `call_terminate`; route long calls through a different carrier |
| Many `no-answer` from one region | Local carrier coverage issue | Switch telephony provider for that region (Plivo / Vobiz / Exotel for India) |

## Webhooks

| Symptom | Probable cause | Fix |
|---|---|---|
| Webhook never arrives | `webhook_url` not set on agent | Patch `agent_config.webhook_url` |
| Webhook arrives but server didn't receive it | Firewall blocks `13.203.39.153` | Whitelist source IP |
| Duplicate webhooks | Multiple status transitions = multiple webhooks | Dedupe by `execution_id` + `status` |
| Webhook fires for status I don't care about | Bolna posts on every transition | Filter on `status == "completed"` in your receiver |
| Webhook times out | Receiver doing sync work | Return `2xx` immediately, process async |
| Webhook payload missing `extracted_data` | Dispositions not run yet | Wait for `status == "completed"` (post-processing finished) |

## Batch

| Symptom | Probable cause | Fix |
|---|---|---|
| Half the rows didn't dial | CSV column wrong | Recipient column must be `contact_number` |
| Variables empty in transcripts | CSV column names don't match `{variable}` in prompt | Make them byte-identical |
| Batch stalls mid-run | Concurrency tier exceeded due to retries | Lower `retry_config.max_retries` or raise tier |
| Batch shows `failed` per call | `error_message` per execution | `GET /batches/{batch_id}/executions` and inspect `error_message` per row |

## Auth / account

| Symptom | Probable cause | Fix |
|---|---|---|
| `401` everywhere | Missing or wrong API key | `setup-api-key` smoke test |
| `403` on a specific resource | Key valid but lacks scope (sub-account) | Use parent account key, or fix sub-account permissions |
| `429` bursts | Exceeded rate limit | Back off; use webhooks instead of polling executions |
| `balance-low` calls | Wallet ran out | Top up in dashboard; check `GET /user/me.wallet` |

## Agent restricted by content policy

Bolna runs a safety check on every agent save. Prompts mentioning:

- Political campaigns
- Illegal activities
- Scams / fraud
- Profanity / hate speech
- NSFW / adult content
- Harmful / misleading info

...get blocked with `"Agent is restricted due to disallowed content."` Review the system prompt, remove the triggering content, and re-save.

## See also

- `references/latency-metrics.md` — `latency_data` fields with thresholds.
- `references/raw-logs.md` — reading per-component logs.
- `../../references/hangup-codes.md` — interpreting `hangup_by` + `hangup_code`.

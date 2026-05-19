# Bolna Agent Config Fields

## Top-level fields

- `agent_config.agent_name`: human-readable name.
- `agent_config.agent_welcome_message`: first message. Supports dynamic variables like `{customer_name}`.
- `agent_config.webhook_url`: HTTPS endpoint for call status and execution data. Use `null` if not configured.
- `agent_config.agent_type`: use `other` unless Bolna docs or dashboard indicate a more specific type.
- `agent_config.tasks`: usually one `conversation` task.
- `agent_prompts.task_1.system_prompt`: main behavior instruction.

## LLM config

Typical simple agent:

```json
{
  "agent_type": "simple_llm_agent",
  "agent_flow_type": "streaming",
  "llm_config": {
    "provider": "openai",
    "family": "openai",
    "model": "gpt-4.1-mini",
    "max_tokens": 150,
    "temperature": 0.2,
    "top_p": 0.9,
    "presence_penalty": 0,
    "frequency_penalty": 0,
    "base_url": "https://api.openai.com/v1",
    "request_json": false
  }
}
```

Useful providers from Bolna docs include OpenAI, Azure OpenAI, Anthropic, OpenRouter, and DeepSeek. Custom LiteLLM-compatible models are added with `POST /user/model/custom`.

## TTS and STT selection

- English or global calls: Deepgram STT with ElevenLabs, Cartesia, Deepgram, Azure, Polly, Rime, Sarvam, or Smallest TTS depending on account setup.
- Indian languages: prefer Sarvam or Pixa STT where appropriate, and write prompts in native script for best pronunciation.
- Use `GET /me/voices` to inspect available voices before setting a voice override.
- Call-time `agent_data.voice_id` can only switch voices inside the same TTS provider.

## Conversation tuning

Important `task_config` fields:

- `hangup_after_silence`: seconds of silence before hangup.
- `incremental_delay`: response buffering delay in milliseconds.
- `number_of_words_for_interruption`: how many user words trigger interruption.
- `hangup_after_LLMCall`: hang up after an LLM response when appropriate.
- `call_cancellation_prompt`: phrase used when canceling.
- `backchanneling`, `backchanneling_message_gap`, `backchanneling_start_delay`: filler acknowledgements.
- `ambient_noise` and `ambient_noise_track`: only use where the chosen telephony/provider setup supports it.
- `call_terminate`: maximum call duration in seconds.
- `voicemail`: voicemail detection behavior.
- `inbound_limit`: `-1` means unlimited calls from a number.
- `whitelist_phone_numbers`: always-allowed inbound callers.
- `disallow_unknown_numbers`: requires caller data via inbound source config.

## Inbound caller matching

`ingest_source_config` can preload caller data for prompts. Common source types are API, CSV, or Google Sheet. For API matching, Bolna passes caller details to the configured endpoint and injects the returned JSON into prompt variables.

## Calling guardrails

Use `calling_guardrails.call_start_hour` and `calling_guardrails.call_end_hour` for outbound calling windows. Treat these as recipient-local compliance settings and document the intended timezone in your own application.

## Semantic routes

`llm_agent.routes` can short-circuit sensitive or repetitive topics with utterance examples, a response, and a score threshold. Use this for FAQs, policy refusals, and domain guardrails.

## Common gotchas

- Use current `/v2/agent` endpoints, not deprecated `/agent` endpoints.
- Keep phone numbers in E.164 format.
- Keep `agent_prompts.task_1` aligned with the first task.
- If using knowledge bases, create the KB first and wait until it is processed.
- If using SIP trunking, patch `telephony_provider: sip-trunk` before mapping numbers.

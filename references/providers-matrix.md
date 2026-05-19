# Provider Matrix

Bolna lets you bring your own credentials for telephony, LLM, TTS, and STT. This matrix lists every supported provider, the credentials they need, and what they're best for. Keys are added via dashboard → Developers → Provider Keys, or via the `add-provider` skill.

## Telephony

| Provider | Required keys | Best for | Notes |
|---|---|---|---|
| **Twilio** | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` | Global outbound/inbound | Largest country coverage. Free trial available. |
| **Plivo** | `PLIVO_AUTH_ID`, `PLIVO_AUTH_TOKEN`, `PLIVO_PHONE_NUMBER` | India (160-series), low latency | Required for 160-series transactional/service calls in India. Supports ambient noise tracks. |
| **Vobiz** | `VOBIZ_AUTH_ID`, `VOBIZ_AUTH_TOKEN`, `VOBIZ_PHONE_NUMBER` | India (140-series telemarketing) | Required for 140-series promotional calls. Supports ambient noise tracks. |
| **Exotel** | `EXOTEL_API_KEY`, `EXOTEL_API_TOKEN`, `EXOTEL_ACCOUNT_SID`, `EXOTEL_DOMAIN`, `EXOTEL_PHONE_NUMBER`, `EXOTEL_OUTBOUND_APP_ID`, `EXOTEL_INBOUND_APP_ID` | India enterprise | Heavier setup with App IDs per direction. |
| **SIP trunk (BYOT)** | Gateway IPs/creds via SIP trunk API | Reuse an existing trunk | See `setup-sip-trunk`. |

**Ambient noise tracks** (`task_config.ambient_noise_track`) are Plivo and Vobiz only — `coffee-shop`, `office-ambience`, `call-center`, or custom upload.

## LLMs

| Provider | Required keys | Strengths |
|---|---|---|
| **OpenAI** | `OPENAI` | Default. `gpt-4.1-mini` is the recommended balance of latency and quality. |
| **Azure OpenAI** | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_MODEL`, `AZURE_OPENAI_API_BASE`, `AZURE_OPENAI_API_VERSION` | Lowest p50 latency for `gpt-4.1-mini` in many regions. Required for HIPAA / data residency. |
| **OpenRouter** | `OPENROUTER` | Single key, many models (Anthropic, Llama, DeepSeek, Mistral). |
| **Google Gemini** | `GOOGLE` | Strong multilingual quality. |
| **Custom (LiteLLM-compatible)** | OpenAI-style `base_url` + key registered via `POST /user/model/custom` | Self-hosted, fine-tuned, or third-party model. Set `provider: "custom"`. |

## Synthesizer (TTS)

| Provider | Required key | Languages | Notes |
|---|---|---|---|
| **ElevenLabs** | `ELEVENLABS` | English-first, multilingual via `eleven_turbo_v2_5` / `eleven_multilingual_v2` | Most natural English. Standard default voice. |
| **Cartesia** | `CARTESIA` | Multilingual, low-latency | Strong for streaming low-latency English. |
| **Sarvam** | `SARVAM` | Indian languages (hi, ta, te, kn, ml, mr, bn, gu, pa) | Native-quality Hindi and regional Indian. |
| **Smallest** | `SMALLEST` | English, growing | Cost-efficient. |
| **Deepgram TTS** | — (uses Deepgram key) | English | Same key as STT. |
| **Polly** | — (Bolna-managed) | Many | AWS Polly via Bolna. |

Voice override at call time (`agent_data.voice_id`) **only works within the same TTS provider** — you can swap one ElevenLabs voice for another, but not ElevenLabs → Sarvam.

## Transcriber (STT)

| Provider | Required key | Languages | Notes |
|---|---|---|---|
| **Deepgram** | `DEEPGRAM` | English (best), Spanish, French, German, Hindi, multilingual via `multi-hi` | Default. `nova-3` for English, `multi-hi` for Hindi-English code-switching. |
| **Sarvam** | `SARVAM` | Hindi, Tamil, Telugu, Kannada, Malayalam, Marathi, Bengali, Gujarati, Punjabi | Best STT accuracy for Indian regional languages. |
| **Bodhi** | (account-level) | Hindi, Kannada, Marathi, Tamil, Bengali | Indian-language-native STT. Don't use for English. |
| **Pixa** | (account-level) | Hindi + Indian regional | Bolna-recommended for some Indian use cases. |

## Common pairings

| Use case | LLM | TTS | STT | Telephony |
|---|---|---|---|---|
| US/EU outbound English | `gpt-4.1-mini` (OpenAI/Azure) | ElevenLabs | Deepgram `nova-3` | Twilio |
| Indian Hindi outbound | `gpt-4.1-mini` | Sarvam | Deepgram `multi-hi` or Sarvam | Plivo / Vobiz |
| Cost-optimised long calls | `gpt-4.1-mini` (Azure) | Smallest / Polly | Deepgram | Plivo |
| Knowledge-heavy support | `gpt-4o` | ElevenLabs | Deepgram | Twilio |
| Compliance-regulated (BFSI India) | `gpt-4.1-mini` (Azure region in-country) | Sarvam | Sarvam | Plivo 160-series |

## Endpoints

- `GET /providers` — list configured providers
- `POST /provider` — add a provider's credentials
- `DELETE /provider/{id}` — remove credentials

Use `GET /me/voices` to list available voices once a TTS provider is configured. Voice override (`agent_data.voice_id`) reads from this list.

## Latency rules of thumb

| Hop | Typical | Notes |
|---|---|---|
| Transcriber (Deepgram nova-3, streaming) | 100-200ms | `endpointing` adds wait between user pause and STT finalisation. |
| LLM (`gpt-4.1-mini`, streaming) | 200-400ms | Higher with `gpt-4o`, `claude-3-5-sonnet`. |
| TTS (ElevenLabs turbo_v2_5, streaming) | 200-400ms | First-byte ~300ms typical. |
| Round-trip total | 800-1200ms | Static graph-agent nodes skip LLM+TTS for ~50ms. |

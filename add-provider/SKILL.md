---
name: add-provider
description: "Add, list, and remove Bolna providers for telephony, LLM, speech-to-text, and text-to-speech services such as Twilio, Plivo, Exotel, OpenAI, Anthropic, Azure, ElevenLabs, Deepgram, Sarvam, Cartesia, Polly, and others. Use when the user wants to bring their own credentials."
license: MIT
compatibility: Requires internet access and a Bolna API key (BOLNA_API_KEY).
metadata:
  openclaw:
    requires:
      env:
        - BOLNA_API_KEY
    primaryEnv: BOLNA_API_KEY
---

# Add Bolna Providers

## Endpoints

- Add provider: `POST https://api.bolna.ai/providers`
- List providers: `GET https://api.bolna.ai/providers`
- Remove provider: `DELETE https://api.bolna.ai/providers/{provider_key_name}`

Use `Authorization: Bearer $BOLNA_API_KEY`. Use `Content-Type: application/json` for add.

## Provider categories

- Telephony: Twilio, Plivo, Exotel, Vobiz, SIP trunking, and other supported calling providers.
- LLM: OpenAI, Azure OpenAI, Anthropic, OpenRouter, DeepSeek, custom LiteLLM-compatible models.
- Transcriber: Deepgram, Sarvam, AssemblyAI, Azure, ElevenLabs Scribe, Gladia, Pixa.
- Voice/TTS: ElevenLabs, Cartesia, Deepgram, Azure TTS, AWS Polly, Rime, Sarvam, Smallest.

Check Bolna's current provider docs before choosing exact credential fields because provider schemas can change.

## Safe workflow

1. Identify provider type and exact provider name.
2. Ask the user to confirm the credentials exist.
3. Never paste secrets into committed files.
4. Add provider through API or dashboard.
5. List providers to capture returned provider IDs.
6. Use provider IDs or provider names in agent configuration as required by Bolna docs.
7. Test with a dry agent or call before rolling into production batches.

## Add provider shape

Bolna stores provider credentials as named keys. Use the provider key name expected by Bolna, then the secret value.

```json
{
  "provider_name": "OPENAI",
  "provider_value": "sk-0123456789az"
}
```

Common provider key names map to the relevant integration, for example API keys for OpenAI, Anthropic, ElevenLabs, Deepgram, Sarvam, Cartesia, or telephony credentials for Twilio, Plivo, Exotel, and Vobiz. Check the current Bolna provider page before writing a new key name.

```bash
curl --request POST \
  --url https://api.bolna.ai/providers \
  --header "Authorization: Bearer $BOLNA_API_KEY" \
  --header "Content-Type: application/json" \
  --data '{
    "provider_name": "OPENAI",
    "provider_value": "sk-0123456789az"
  }'
```

## List providers

```bash
curl --request GET \
  --url https://api.bolna.ai/providers \
  --header "Authorization: Bearer $BOLNA_API_KEY"
```

## Remove provider

```bash
curl --request DELETE \
  --url "https://api.bolna.ai/providers/$PROVIDER_KEY_NAME" \
  --header "Authorization: Bearer $BOLNA_API_KEY"
```

Confirm removal first. Existing agents may fail if their configured provider key is removed.

## Common credential key names

| Provider | Property |
|---|---|
| OpenAI | `OPENAI` |
| OpenRouter | `OPENROUTER` |
| Google Gemini | `GOOGLE` |
| Azure OpenAI | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_MODEL`, `AZURE_OPENAI_API_BASE`, `AZURE_OPENAI_API_VERSION` |
| ElevenLabs | `ELEVENLABS` |
| Cartesia | `CARTESIA` |
| Sarvam | `SARVAM` |
| Smallest | `SMALLEST` |
| Deepgram | `DEEPGRAM` |
| Twilio | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` |
| Plivo | `PLIVO_AUTH_ID`, `PLIVO_AUTH_TOKEN`, `PLIVO_PHONE_NUMBER` |
| Vobiz | `VOBIZ_AUTH_ID`, `VOBIZ_AUTH_TOKEN`, `VOBIZ_PHONE_NUMBER` |
| Exotel | `EXOTEL_API_KEY`, `EXOTEL_API_TOKEN`, `EXOTEL_ACCOUNT_SID`, `EXOTEL_DOMAIN`, `EXOTEL_PHONE_NUMBER`, `EXOTEL_OUTBOUND_APP_ID`, `EXOTEL_INBOUND_APP_ID` |
| Custom LLM | Use `provider: "custom"` in the agent's `llm_agent` with an OpenAI-compatible `base_url`, then `POST /user/model/custom` to register the model name. |

Full per-provider matrix (including which language/use case each suits) is in `../references/providers-matrix.md`.

## See also

- `../references/providers-matrix.md` — latency rules-of-thumb, language coverage, common pairings.
- `setup-sip-trunk` — SIP trunk providers (different endpoints, not the credential vault).
- `create-agent` — wiring provider names into `llm_agent`, `synthesizer`, `transcriber`.

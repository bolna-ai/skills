---
name: add-provider
description: "Add, list, and remove Bolna providers for telephony, LLM, speech-to-text, and text-to-speech services such as Twilio, Plivo, Exotel, OpenAI, Anthropic, Azure, ElevenLabs, Deepgram, Sarvam, Cartesia, Polly, and others. Use when the user wants to bring their own credentials."
license: MIT
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
  "provider_name": "OPENAI_API_KEY",
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
    "provider_name": "OPENAI_API_KEY",
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

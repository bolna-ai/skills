# Multilingual Prompts

For Bolna agents that speak languages other than English, the single most important rule is: **write the prompt in the language's native script**. Phonetic English ("Namaste! Aap kaise ho?") corrupts TTS pronunciation and STT confidence.

## Native script per language

| Language | Correct | Incorrect |
|---|---|---|
| Hindi | `नमस्ते! आप कैसे हैं?` | `Namaste! Aap kaise ho?` |
| Tamil | `வணக்கம்! எப்படி இருக்கிறீர்கள்?` | `Vanakkam! Eppadi irukkireenga?` |
| Telugu | `నమస్కారం! మీరు ఎలా ఉన్నారు?` | `Namaskaram! Meeru ela unnaru?` |
| Kannada | `ನಮಸ್ಕಾರ! ನೀವು ಹೇಗಿದ್ದೀರಿ?` | `Namaskara! Neevu hegiddhi?` |
| Marathi | `नमस्कार! तुम्ही कसे आहात?` | `Namaskar! Tumhi kase aahat?` |
| Bengali | `নমস্কার! আপনি কেমন আছেন?` | `Namaskar! Apni kemon achen?` |
| Gujarati | `નમસ્તે! તમે કેમ છો?` | `Namaste! Tame kem cho?` |
| Punjabi | `ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਤੁਸੀਂ ਕਿਵੇਂ ਹੋ?` | `Sat Sri Akal! Tusi kiven ho?` |
| Spanish | `¡Hola! ¿Cómo estás?` | `Hola! Como estas?` |
| French | `Bonjour ! Comment ça va ?` | `Bonjour! Comment ca va?` |
| German | `Guten Tag! Wie geht es Ihnen?` | `Guten Tag! Wie geht es Ihnen?` |
| Portuguese | `Olá! Como você está?` | `Ola! Como voce esta?` |

For European languages, **always include accents** (`é`, `ñ`, `ü`, `¿`, `ç`). They're not decoration — they change pronunciation and tone.

## Code-switching (Hinglish, Spanglish, etc.)

Real Indian callers mix English nouns into Hindi sentences. Write the prompt the same way:

```
यदि उपयोगकर्ता WhatsApp के बारे में पूछे, तो बताएं कि हम उसमें Notification भेजते हैं।
```

Leave brand names, technical terms, and English-spoken nouns in Latin script. Native phrasing in Devanagari. STT (Deepgram `multi-hi`, Sarvam) handles this correctly.

## Language switching

If the agent supports multiple languages, add an explicit instruction:

```
LANGUAGE
Reply in the language the caller is using. If they switch language, switch with them.
Default to {primary_language}. Never translate brand names, person names, addresses,
order IDs, or legal terms unless the caller explicitly asks for a translation.
```

For configured per-language prompts (Audio Tab supports separate prompts per language), Bolna activates the matching prompt when the agent is speaking that language. The shared **Language Switching Instructions** field tells the agent *when* to switch.

## Formal vs informal

Different languages have politeness levels — pick consciously:

| Language | Formal | Informal |
|---|---|---|
| Hindi | `आप` (aap) | `तुम` (tum) |
| Spanish | `usted` | `tú` |
| French | `vous` | `tu` |
| German | `Sie` | `du` |
| Portuguese (BR) | `você` | (informal already) |

For B2B or customer-facing agents, default to formal. For consumer-friendly brand voices, informal is fine. Pick once, use throughout.

## Per-language welcome messages

If you support multiple languages, the welcome message should be per-language too. The first words set the tone for the rest of the call.

```
{
  "agent_welcome_message_en": "Hi {customer_name}, this is Tara from Acme.",
  "agent_welcome_message_hi": "नमस्ते {customer_name}, मैं Acme से तारा बोल रही हूँ।"
}
```

(Wire these up via per-language prompts in the Agent Tab — see `customizations/multilingual-languages-support`.)

## Provider pairing

| Language | Recommended STT | Recommended TTS |
|---|---|---|
| English | Deepgram `nova-3` | ElevenLabs `eleven_turbo_v2_5` |
| Hindi | Deepgram `multi-hi` or Sarvam | Sarvam or ElevenLabs multilingual |
| Tamil / Telugu / Kannada / Malayalam | Sarvam | Sarvam |
| Marathi / Bengali / Gujarati / Punjabi | Sarvam | Sarvam |
| Spanish / French / German | Deepgram (multilingual) | ElevenLabs multilingual |

Mismatched provider × language is the #1 cause of "the agent doesn't understand my Hindi caller." Match per-language.

## Auto-switch system messages

Configure language variants for `check_user_online_message`, `call_hangup_message`, and tool `pre_call_message`. Bolna auto-switches after 3 turns of detected language. See `setup-inbound/references/auto-switch-messages.md`.

## Testing pronunciation

- Use the Bolna **Voice Labs** in the dashboard to test how each TTS voice renders your prompt before going live.
- Test with **native speakers** of each language — synthesised voices sometimes mispronounce specific brand names or technical terms.
- For tricky words (English brand names in a Hindi prompt), spell phonetically in the *target language* if needed: write `Acme` as `एक्मे` if the TTS struggles.

## Common mistakes

| Mistake | Effect |
|---|---|
| Romanised Hindi (`Aap kaise ho?`) | TTS reads as English-sounding gibberish; STT logs lower confidence. |
| Missing accents in European languages | TTS pronunciation degrades, especially Spanish/French. |
| Mixing scripts arbitrarily | Use code-switching deliberately (English nouns inside native sentences). Don't switch mid-word. |
| Translating UI/brand names | "Wayne Enterprises" should stay as is, not "वेन इंटरप्राइजेज". |
| Single welcome message for multilingual agent | First turn sounds wrong for half the callers. Configure per-language. |

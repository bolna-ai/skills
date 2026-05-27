# Auto-Switch Multilingual System Messages

Bolna detects the caller's language after ~3 conversation turns and automatically switches **system messages** to match. System messages are the things the agent says outside the LLM-generated conversation: silence pings, hangup farewells, and tool-call wait messages.

## What gets auto-switched

| Message type | When it plays | Configured at |
|---|---|---|
| `check_user_online_message` | After user silence, to confirm they're still there | Agent → Engine Tab |
| `call_hangup_message` | When the agent ends the call | Agent → Call Tab |
| Tool `pre_call_message` | While a function tool's API call is in flight | Per tool, in `api_tools.tools[]` |

## Bundle format

Each message is an object keyed by ISO 639-1 language code:

```json
{
  "check_user_online_message": {
    "en": "Hey, are you still there?",
    "hi": "क्या आप अभी भी वहाँ हैं?",
    "ta": "வணக்கம், நீங்கள் இன்னும் இணைப்பில் இருக்கிறீர்களா?",
    "bn": "নমস্কার, আপনি কি এখনও লাইনে আছেন?"
  }
}
```

```json
{
  "call_hangup_message": {
    "en": "Thank you for calling. Goodbye!",
    "hi": "कॉल करने के लिए धन्यवाद। अलविदा!",
    "bn": "কলটি এখন কেটে যাবে। ধন্যবাদ এবং নমস্কার!"
  }
}
```

```json
{
  "pre_call_message": {
    "en": "Just give me a moment, I'll be back with you.",
    "hi": "कृपया थोड़ा समय दीजिए, मैं पता करके बताता हूँ।"
  }
}
```

## How detection works

1. Conversation begins in the agent's **primary** language (configured in Audio Tab).
2. After **3 user turns**, Bolna analyses transcripts and picks the dominant language.
3. From that point, all configured system messages switch to that language.
4. If detection is inconclusive, the agent stays on primary.

3 turns isn't a hard requirement — it's the threshold for accurate detection. Calls shorter than 3 turns get the primary language for everything.

## Fallback order

When selecting a message, Bolna tries:

1. **Detected language** — use the message at that ISO code.
2. **`en`** — fall back to English if not configured.
3. **First available** — use the first key in the object.

**Always configure `en` as a safety net.** Without it, fallback becomes "first key in the object," which is fragile (JSON insertion order).

## Supported codes

Same as Bolna's multilingual support:

| Code | Language | Code | Language | Code | Language |
|---|---|---|---|---|---|
| `en` | English | `hi` | Hindi | `bn` | Bengali |
| `ta` | Tamil | `te` | Telugu | `mr` | Marathi |
| `gu` | Gujarati | `kn` | Kannada | `ml` | Malayalam |
| `pa` | Punjabi | `ur` | Urdu | `as` | Assamese |
| `fr` | French | `es` | Spanish | `nl` | Dutch |
| `id` | Indonesian | `ms` | Malay | `od` | Odia |

## Patterns

### Indian outbound campaign (Hindi-primary, English fallback)

```json
{
  "check_user_online_message": {
    "hi": "हेलो, क्या आप सुन सकते हैं?",
    "en": "Hello, can you hear me?"
  },
  "call_hangup_message": {
    "hi": "बात करने के लिए धन्यवाद। शुभ दिन!",
    "en": "Thanks for your time. Have a great day!"
  }
}
```

If a caller switches to English mid-call, the hangup message auto-switches to the English variant.

### English-primary support line (multi-language safety)

```json
{
  "call_hangup_message": {
    "en": "Thank you for calling Acme. Have a great day.",
    "hi": "धन्यवाद। शुभ दिन!",
    "es": "Gracias por llamar. ¡Que tenga un buen día!",
    "fr": "Merci de votre appel. Bonne journée!"
  }
}
```

Covers the long tail of callers without writing a dedicated multilingual agent.

### Tool pre-call message in Hindi

```json
{
  "tools": [{
    "key": "custom_task",
    "name": "lookup_order",
    "description": "Use when the customer asks about order status.",
    "pre_call_message": {
      "en": "Just a moment, let me check that for you.",
      "hi": "कृपया एक पल रुकिए, मैं देखता हूँ।"
    },
    "parameters": { ... },
    "value": { ... }
  }]
}
```

The pre-call message during the tool API call auto-switches based on the language detected so far in the conversation.

## Best practices

- **Use native script.** `धन्यवाद` not `Dhanyavaad`. TTS pronounces native script correctly; phonetic Latin breaks.
- **Don't translate literally.** "Have a great day" sounds odd in many languages — write a natural local farewell instead.
- **Test with native speakers.** Run a test call with each language; the synthesised voice can pronounce native script in unexpected ways.
- **Cover the messages, not the prompts.** Auto-switch only swaps these system messages; the agent's main `prompt` doesn't change mid-call. Use the per-language prompts in the Agent Tab for that.

## Limitations

- Detection runs after 3 turns. Short calls (< 3 turns) always use the primary language.
- Detection looks at the dominant language. Code-switching (Hinglish: Hindi script + English words) is detected as Hindi.
- Once switched, the agent doesn't switch back automatically until the call ends — by design, so the experience isn't bouncing between languages.

## See also

- `customizations/multilingual-languages-support.mdx` in Bolna docs — full multilingual agent setup.
- `prompt-writing` — native-script prompt patterns.
- `setup-tools/references/cal-com.md` — multilingual pre-call messages for built-in tools.

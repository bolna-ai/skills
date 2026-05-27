# Multilingual Agents — Full Reference

When one agent must handle calls that switch languages mid-conversation (Indian markets, multilingual support lines, regional outbound campaigns), use `multilingual_config` inside the `conversation` task's `tools_config`. The agent picks the right STT/TTS per turn and reads the matching system prompt.

This is **one agent per use case, multiple language personalities** — not one agent per language.

## Endpoint and auth

Same as a standard agent — `POST /v2/agent` with `Authorization: Bearer $BOLNA_API_KEY`. No admin gate, no plan gate. Any account can ship a multilingual agent.

## Top-level structure

```jsonc
{
  "tools_config": {
    "llm_agent": { /* shared across languages — one model handles all */ },
    "synthesizer": { /* default TTS — fallback if no per-language override */ },
    "transcriber": { /* default STT — fallback */ },
    "input":  { "provider": "plivo", "format": "wav" },
    "output": { "provider": "plivo", "format": "wav" },

    "multilingual_config": {
      "enabled": true,
      "active_language": "hi",
      "switch_tool_description": "Respond in the language the user is currently using. Default to Hindi unless the user clearly switches.",
      "languages": {
        "hi": { /* HindiLanguageEntry */ },
        "en": { /* EnglishLanguageEntry */ },
        "nl": { /* DutchLanguageEntry */ }
      }
    }
  }
}
```

### Fields

| Field | Type | Purpose |
|---|---|---|
| `enabled` | bool | Master switch. `false` ignores everything else. |
| `active_language` | string (ISO 639-1) | Which language the call **opens** in. |
| `switch_tool_description` | string | "Language Switching Instructions" in the dashboard. The LLM follows this to decide when to flip languages. |
| `languages` | dict | Map of `language_code` → `LanguageEntry`. |

### `LanguageEntry`

```jsonc
{
  "agent_name": "Vidya",
  "system_prompt": "<complete prompt in this language>",
  "synthesizer": { /* per-language TTS */ },
  "transcriber": { /* per-language STT */ },
  "handoff_message": "Connecting you with {agent_name} who speaks {language}."
}
```

| Field | Required? | Notes |
|---|---|---|
| `agent_name` | optional | Advanced setting. Surfaced in handoff messages via `{agent_name}`. **Set a real value** — empty or junk strings reach callers. |
| `system_prompt` | required | A **complete** prompt in this language. Not a translation of a master prompt — each language can have its own persona, objections, and persuasion. |
| `synthesizer` | required | Full provider config. Free to mix providers across languages. |
| `transcriber` | required | Full provider config. Free to mix providers across languages. |
| `handoff_message` | optional | Plays when the agent switches **to** this language. Supports `{agent_name}` and `{language}` placeholders. |

## Mixing providers across languages

You are **not** locked to one STT/TTS pair. Pick the best per language:

| Language | Recommended STT | Recommended TTS |
|---|---|---|
| English | Deepgram `nova-3` | Cartesia `sonic-3.5`, ElevenLabs `turbo_v2_5` |
| Hindi | ElevenLabs `scribe_v2_realtime`, Deepgram `multi-hi` | Sarvam `bulbul:v3` |
| Tamil / Telugu / Kannada / Marathi / Bengali / Gujarati | Sarvam, Pixa | Sarvam `bulbul:v3` |
| Spanish / French / German | Deepgram, Azure | ElevenLabs multilingual_v2, Cartesia |
| Dutch / Nordic | Azure | ElevenLabs |
| Arabic | Azure | ElevenLabs multilingual_v2 |

## Welcome, hangup, and "are you there?" messages

Bolna treats these three differently on `POST /v2/agent`:

| Field | Accepted shape | Notes |
|---|---|---|
| `agent_welcome_message` | **`str` only** | Write it in the `active_language`. There is no dict form on POST. |
| `task_config.call_hangup_message` | `str` **or** dict keyed by language code | Dict form: `{"hi": "...", "en": "...", "nl": "..."}`. |
| `task_config.check_user_online_message` | `str` **or** dict keyed by language code | Same dict shape. |

```jsonc
// agent_welcome_message — string only
"agent_welcome_message": "नमस्ते दीदी, मैं Snabbit से Vidya बोल रही हूँ"

// call_hangup_message — dict form is accepted
"task_config": {
  "call_hangup_message": {
    "hi": "Call disconnect हो रही है। धन्यवाद।",
    "en": "The call will now disconnect. Goodbye!",
    "nl": "De oproep wordt nu verbroken. Tot ziens!"
  }
}
```

For language-aware **welcome lines**, rely on each language's `system_prompt` opening line and the per-language `handoff_message` (which fires on language switch). The `agent_welcome_message` itself plays once at call start in whichever language you wrote it in.

## Worked example (3 languages, mixed providers)

This is a sanitized version of a real production multilingual agent.

```jsonc
{
  "agent_config": {
    "agent_name": "Referral Outreach v6",
    "agent_welcome_message": "नमस्ते दीदी, मैं Snabbit से Vidya बोल रही हूँ",
    "agent_type": "other",
    "tasks": [
      {
        "task_type": "conversation",
        "toolchain": { "execution": "parallel", "pipelines": [["transcriber", "llm", "synthesizer"]] },
        "task_config": {
          "call_terminate": 600,
          "hangup_after_silence": 20,
          "incremental_delay": 350,
          "number_of_words_for_interruption": 2,
          "check_if_user_online": true,
          "check_user_online_message": {
            "en": "Hey, are you still there?",
            "hi": "क्या आप अभी भी कॉल पर हैं?",
            "nl": "Hallo, bent u er nog?"
          },
          "trigger_user_online_message_after": 12,
          "noise_cancellation_level": 70,
          "voicemail": false,
          "auto_reschedule": true,
          "optimize_latency": true,
          "call_hangup_message": {
            "en": "The call will now disconnect. Goodbye!",
            "hi": "Call अब disconnect हो रही है। धन्यवाद!",
            "nl": "De oproep wordt nu verbroken. Tot ziens!"
          }
        },
        "tools_config": {
          "input":  { "provider": "plivo", "format": "wav" },
          "output": { "provider": "plivo", "format": "wav" },
          "llm_agent": {
            "agent_type": "simple_llm_agent",
            "agent_flow_type": "streaming",
            "llm_config": {
              "provider": "azure",
              "family": "openai",
              "model": "azure/gpt-4.1-mini",
              "max_tokens": 391,
              "temperature": 0.2,
              "top_p": 0.9,
              "min_p": 0.1
            }
          },
          "synthesizer": {
            "provider": "sarvam",
            "stream": true,
            "buffer_size": 220,
            "audio_format": "wav",
            "provider_config": { "model": "bulbul:v3", "voice": "Ashutosh", "voice_id": "ashutosh", "language": "hi", "speed": 1.0 }
          },
          "transcriber": {
            "provider": "elevenlabs",
            "model": "scribe_v2_realtime",
            "language": "hi",
            "stream": true,
            "encoding": "linear16",
            "sampling_rate": 16000,
            "endpointing": 250
          },
          "multilingual_config": {
            "enabled": true,
            "active_language": "hi",
            "switch_tool_description": "Respond in the language the user is currently using. Default to Hindi unless the user clearly switches to English or Dutch.",
            "languages": {
              "hi": {
                "agent_name": "Vidya",
                "system_prompt": "आप विद्या हैं, Snabbit की Training & Onboarding Outreach team से...",
                "synthesizer": {
                  "provider": "sarvam",
                  "buffer_size": 220,
                  "provider_config": { "model": "bulbul:v3", "voice": "Ashutosh", "voice_id": "ashutosh" }
                },
                "transcriber": { "provider": "elevenlabs", "model": "scribe_v2_realtime", "language": "hi" },
                "handoff_message": "एक पल, मैं {agent_name} से connect करती हूँ जो {language} बोलती हैं।"
              },
              "en": {
                "agent_name": "Vidya (English)",
                "system_prompt": "You are Vidya, a calm, warm voice agent from Snabbit's Training & Onboarding Outreach team...",
                "synthesizer": {
                  "provider": "cartesia",
                  "buffer_size": 40,
                  "provider_config": { "model": "sonic-3.5", "voice": "Callie - Encourager", "voice_id": "00a77add-48d5-4ef6-8157-71e5437b282d" }
                },
                "transcriber": { "provider": "deepgram", "model": "nova-3", "language": "en" },
                "handoff_message": "One moment, connecting you with {agent_name} who speaks {language}."
              },
              "nl": {
                "agent_name": "Vidya (Nederlands)",
                "system_prompt": "Je bent Vidya, een rustige, warme spraakagent van Snabbit...",
                "synthesizer": {
                  "provider": "elevenlabs",
                  "buffer_size": 40,
                  "provider_config": { "model": "eleven_turbo_v2_5", "voice": "Arfa", "voice_id": "VHPIZxaNtAiRm0Bq345U" }
                },
                "transcriber": { "provider": "azure", "model": "azure", "language": "nl" },
                "handoff_message": "Een moment, ik verbind je door met {agent_name} die {language} spreekt."
              }
            }
          }
        }
      }
    ]
  },
  "agent_prompts": {
    "task_1": { "system_prompt": "<the default-language prompt — duplicates languages.hi.system_prompt>" }
  }
}
```

## Gotchas

| Pitfall | Fix |
|---|---|
| `agent_name: ""` or junk like `"qwegf iqghyf"` — these reach callers when handoff fires. | Always set a real, pronounceable name per language. |
| Translating one master prompt into other languages instead of writing each fresh. | Native speakers and accent patterns differ. Write each prompt in the target language from scratch (or translate then heavily edit). |
| Forgetting `agent_prompts.task_1.system_prompt`. | Bolna still reads this for the default-language task. Keep it in sync with `languages.<active_language>.system_prompt`. |
| Using one STT for all languages because "it supports multilingual". | Multilingual models lose accuracy vs. dedicated single-language ones. Per-language overrides cost nothing and improve transcription noticeably. |
| `switch_tool_description` left empty or generic. | The LLM has no rule for when to switch. Write it explicitly: "Default to Hindi. Switch only if the user speaks two full sentences in another language." |
| Setting `multilingual_config.enabled: true` but only one entry in `languages`. | Disables nothing but does nothing useful either. Either add a second language or set `enabled: false`. |

## See also

- `../SKILL.md` § Multilingual agents — the short version.
- `../../prompt-writing/references/multilingual.md` — how to author the per-language prompts.
- `../../prompt-writing/references/section-templates.md` — Section 1..N structure used by every Bolna prompt.
- `../../prompt-writing/references/reusable-modules.md` — name, phone, email, and numeric expression patterns to translate per language.
- `../../references/providers-matrix.md` — picking STT/TTS per language.

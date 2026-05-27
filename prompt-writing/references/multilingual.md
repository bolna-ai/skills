# Multilingual Prompts

How the Bolna prompt rules map onto a `multilingual_config` agent — one agent, multiple language personalities, each with its own STT, TTS, and complete system prompt.

This file assumes you have already read the main SKILL.md. The structural rules there (sectioned format, Hindi-first/English-second scripted lines, FAQ in YAML, Devanagari rules, forbidden symbols) apply **per language**, not globally. Each language gets its own complete prompt.

## When to author a multilingual prompt

Use `multilingual_config` (not separate agents) when:

- One inbound number must serve callers in multiple languages.
- An outbound flow may switch language mid-call (common in India for Hindi/English code-switching, or pan-India campaigns running Hindi + Tamil + English).
- The script content is fundamentally the same across languages but pronunciation, persona, and TTS choices must differ.

Use **separate agents** (not `multilingual_config`) when:

- The flow, branches, or persona differs materially across languages (a Hindi sales pitch vs. an English support flow are different products).
- Each language has its own KPIs, tracking, dispositions, or compliance rules.
- You want independent versioning per language.

## The runtime contract

`multilingual_config.languages.<code>.system_prompt` is a **complete, self-contained prompt** for that language. Not a translation, not a fragment. Each language entry should be the full Section 1..N structure described in the main SKILL.md.

What's shared across languages:

- The LLM (`tools_config.llm_agent`) — one model handles all languages.
- The flow structure (which sections exist, what questions are asked, in what order).
- Persuasion goals, KPIs, and compliance constraints.

What differs per language:

- The literal text of every scripted line.
- The persona (agent name, gendered verb forms, tonal warmth).
- The TTS provider, voice, and STT provider (`languages.<code>.synthesizer` + `transcriber`).
- The objection handling table — phrasing in target language.
- The pronunciation rules — Devanagari for Hindi, native script for others.

## Writing each language entry

For each language code (`hi`, `en`, `nl`, `ta`, `te`, `mr`, etc.):

1. Decide the agent's name in that language. `Vidya` works across Hindi and English. `Carmen` for Spanish. Don't translate a name unless it has a natural localised form.
2. Write the full Section 1 (Identity, Tone, Goal, Guardrails, Language, Conversation Structure, Handling Queries, plus the two static modules) in that language. The static modules — Conversational Naturalization and Pronunciation and Script Normalisation — get translated into the target language. Do not paste the Hindi static modules into an English entry.
3. Write Section 2 (Conversation Starter) **only in this language**. Multilingual entries do not need the dual-language scripted block (`Opening (Hindi):` / `Opening (English):`) because the entry itself is the language. Use a single-language scripted line.
4. Write Section 3..N flow questions in this language only.
5. Write the FAQ in this language only.

Result: per language, a complete prompt that reads as if the agent were single-language.

## The single-language vs multilingual line format

In a single-language prompt (no `multilingual_config`), scripted lines use the dual format:

```
Question 1 (Hindi): क्या आप अभी काम ढूंढ रही हैं?
Question 1 (English): Are you currently looking for work?
```

Inside a `multilingual_config.languages.hi.system_prompt`, the same line is single-language:

```
Question 1: क्या आप अभी काम ढूंढ रही हैं?
```

The runtime already knows which language is active — no need to label.

## `switch_tool_description` — the Language Switching Instructions

This is the dashboard's "Language Switching Instructions" field. It lives at `multilingual_config.switch_tool_description` and tells the LLM **when** to switch languages. Be explicit.

Bad (vague):

> "Respond in the user's language."

Good (rule-shaped):

> "Respond in the language the user is currently using. Default to Hindi. Switch to English only if the user speaks two consecutive full sentences in English. Do not switch back unless the user explicitly returns to Hindi. Never mix Hindi and English in a single agent turn."

Anchor the switching rule in **observable user behaviour** (whole sentences, explicit requests), not LLM judgment ("if you think the user prefers English"). Vague switching rules cause the agent to flip language unpredictably mid-flow.

## `handoff_message` per language

Plays when the agent switches **to** this language. Placeholders:

- `{agent_name}` → resolves to `languages.<code>.agent_name`
- `{language}` → resolves to the human-readable language name (Hindi, English, Dutch)

Examples:

```jsonc
"hi": { "handoff_message": "एक पल, मैं {agent_name} से connect करती हूँ जो {language} बोलती हैं।" },
"en": { "handoff_message": "One moment, connecting you with {agent_name} who speaks {language}." },
"ta": { "handoff_message": "ஒரு நிமிடம், {language} பேசும் {agent_name} உடன் இணைக்கிறேன்." }
```

Treat these as scripted lines: no exclamation marks, no symbols, numbers as words.

## Welcome and hangup messages

These three fields have different shapes on `POST /v2/agent`:

| Field | Accepted shape |
|---|---|
| `agent_welcome_message` | **string only** — write it in the `active_language` |
| `task_config.call_hangup_message` | string **or** dict keyed by language code |
| `task_config.check_user_online_message` | string **or** dict keyed by language code |

For per-language welcome behaviour, rely on the opening line of each `languages.<code>.system_prompt` and on the per-language `handoff_message` (which plays on language switch). The `agent_welcome_message` itself is a single string that plays once at call start.

## Picking STT and TTS per language

Mix providers across languages. There is no requirement to use the same vendor for all languages.

| Language | STT | TTS |
|---|---|---|
| English | Deepgram `nova-3`, Azure | Cartesia `sonic-3.5`, ElevenLabs `turbo_v2_5` |
| Hindi | ElevenLabs `scribe_v2_realtime`, Deepgram `multi-hi` | Sarvam `bulbul:v3` |
| Hinglish (code-switched) | Deepgram `multi-hi` | Sarvam `bulbul:v3` |
| Tamil / Telugu / Kannada / Malayalam | Sarvam, Pixa | Sarvam `bulbul:v3` |
| Marathi / Gujarati / Bengali / Punjabi | Sarvam | Sarvam `bulbul:v3` |
| Spanish / French / German / Portuguese | Deepgram, Azure | ElevenLabs multilingual_v2, Cartesia |
| Dutch / Nordic | Azure | ElevenLabs |
| Arabic | Azure | ElevenLabs multilingual_v2 |

## Hinglish specifically

Hinglish (Hindi written in Devanagari with embedded English loanwords) is not a separate language code. Use `hi` and the `multi-hi` Deepgram model, then write the prompt in Devanagari while keeping commonly-spoken English nouns in Roman script (app, WhatsApp, OTP, form, link, etc. — per the Devanagari rules in the main SKILL.md).

You don't need a second `en` language entry for Hinglish — the embedded English words ride along in the Hindi entry.

Add a separate `en` entry only when the agent should fully switch into English for callers who don't speak Hindi at all.

## Common mistakes

| Mistake | Fix |
|---|---|
| Translating one master Hindi prompt into English token-for-token. | Write each language entry fresh. Tone, idioms, and persuasion phrasing don't translate one-to-one. |
| Forgetting to write a per-language FAQ. | Each entry needs its own FAQ. The runtime picks the FAQ from the active language entry. |
| Setting `multilingual_config.enabled: true` but only one language in `languages`. | Either add a second language or set `enabled: false` and use the default `tools_config.synthesizer` / `transcriber`. |
| Leaving `agent_name` blank or junk (`"qwegf iqghyf"`, `""`). | Set a real, pronounceable, gender-consistent name per language. |
| Using the same STT/TTS pair for every language because "it's multilingual". | Per-language overrides are free. Use them. |
| `switch_tool_description` left vague or empty. | Write an explicit rule anchored on whole sentences and observable behaviour. |
| Mixing Hindi and English scripted text inside one language entry. | Inside `languages.hi.system_prompt`, every scripted line is Hindi. Inside `languages.en.system_prompt`, every scripted line is English. No dual-language blocks. |
| Forgetting `agent_prompts.task_1.system_prompt`. | The default-language entry still needs to appear in `agent_prompts.task_1.system_prompt`. Keep it in sync with `languages.<active_language>.system_prompt`. |

## See also

- `../SKILL.md` — the core prompt-writing rules. Apply per language.
- `../../create-agent/references/multilingual-config.md` — the full API-side shape of `multilingual_config`.
- `static-modules.md` — the two Section 1 static modules to translate into each language.
- `section-templates.md` — section structure and worked examples.
- `reusable-modules.md` — name, phone, email, numeric capture patterns (translate per language).

# Prompting Tips for Bolna Voice Agents

How to write prompts that produce a natural, on-task voice call.

## The four sections every prompt needs

| Section | Purpose | Example |
|---|---|---|
| **Personality** | Tone, pace, energy | "Warm, concise, perceptive. Speak slowly and clearly." |
| **Context** | Who the agent is, what it represents | "You are calling on behalf of Acme on a recorded line. The recipient signed up for a demo last week." |
| **Instructions** | Steps and flow | "First ask if they have 2 minutes. If yes, walk through the 3-step demo agenda below." |
| **Guardrails** | Hard rules and refusals | "Never quote pricing without checking with @get_quote. Never discuss competitor products." |

Lead with personality and context. Voice agents drift toward generic chatbot tone unless you anchor them upfront.

## Hard rules that always help

- **Cap response length**: `"You will not speak more than 2 sentences at a time."` Voice is slow — long monologues feel robotic and steal turn-taking.
- **Disclose AI**: required in many jurisdictions. Put it in the welcome message, not deep in the prompt.
- **End each turn with a question or pause**: keeps the user engaged and gives the STT a clean handoff point.
- **Refuse out-of-scope**: explicit deflection beats hallucination. `"If asked about anything not in your knowledge base, say 'I'm not able to help with that, but I can connect you to someone who can.'"`

## Dynamic variables

Use `{variable_name}` in the prompt and welcome message. Two flavours:

| Type | How to fill |
|---|---|
| User variable | `user_data` on `POST /call`, or CSV column in batch calling. |
| System variable | Auto-filled: `agent_id`, `execution_id`, `call_sid`, `from_number`, `to_number`, `current_date`, `current_time`, `timezone`. |

**Set timezone**. `current_date` and `current_time` are tz-aware. Pass `"timezone": "Asia/Kolkata"` in `user_data` (or in `recipient_data` for graph agents). Without it, time-based logic breaks silently.

**Inbound vs outbound `from_number`/`to_number`**:
- Inbound: `from_number` = caller, `to_number` = your agent.
- Outbound: `from_number` = your agent, `to_number` = recipient.

## Hangup conditions

Two ways the agent can hang up:

- `task_config.hangup_after_silence` (seconds of user silence — default 10s, raise for thoughtful audiences, lower for IVR-style flows).
- LLM-prompted hangup: include a clear instruction. `"If the user says goodbye, thank you and end the call, hang up. Do not keep talking after that."`

If `hangup_after_LLMCall: true`, the call ends right after the agent's first response — useful for one-shot announcements.

## Indian-language and multilingual prompts

**Always write in native script.** Phonetic English ("Namaste! Aap kaise ho?") corrupts TTS pronunciation and breaks STT confidence.

| Language | Correct | Incorrect |
|---|---|---|
| Hindi | `नमस्ते! आप कैसे हैं?` | `Namaste! Aap kaise ho?` |
| Spanish | `¡Hola! ¿Cómo estás?` | `Hola! Como estas?` |
| French | `Bonjour ! Comment ça va ?` | `Bonjour! Comment ca va?` |

For Hindi-English code-switching (typical of Indian calls), use Deepgram `multi-hi` STT and write the prompt in **Devanagari with English nouns in Latin script where they're commonly spoken in English**: `"क्या आप WhatsApp पर मैसेज भेज सकते हैं?"`

Configure per-language prompts in the Agent Tab. Use the Language Switching Instructions field for cross-language behaviour: `"Respond in the language the user is currently using. Default to Hindi."`

## Persona stability

The agent will drift in long calls. Three counter-measures:

1. **Repeat the role in the prompt**: state the persona twice — once at the top, once near the bottom of the instructions block.
2. **Bound the topic**: `"You ONLY help with order tracking and returns. If the conversation drifts, politely redirect."`
3. **Use semantic routes** (`llm_agent.routes`) for FAQs and refusals. The router short-circuits common questions with a canned response and zero LLM cost.

## Conversation repair phrases

Pre-write the awkward moments so they sound natural:

| Situation | Suggested phrase |
|---|---|
| STT confidence low | `"Sorry, I didn't catch that — could you repeat?"` |
| Long silence | `"Are you still there?"` (Bolna auto-localises this if multilingual is enabled.) |
| Agent doesn't know | `"That's a great question — let me check and call you back. What's the best number to reach you on?"` |
| User asks for human | `"Of course, transferring you now — please hold."` then trigger `transfer_call`. |
| Agent needs to fetch | `pre_call_message: "Just a moment, let me check that..."` (on the API tool). |

## Testing

- Use the dashboard playground first — it's much cheaper than burning telephony credits on bad prompts.
- Vary `user_data` values to see how the prompt handles unfilled or weird variables.
- Test with realistic transcripts (background noise, fast speech, accents) once the prompt feels right.

## Prompt modules

Bolna ships pre-built modules in the dashboard (Email Collection, Number Collection, Persuasion, Objection Handling, etc.). Browse via the Agent Tab → **Browse Modules**. Insert and customise rather than writing from scratch — they encode patterns that have shipped to production already.

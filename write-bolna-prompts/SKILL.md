---
name: write-bolna-prompts
description: "Write Bolna voice prompts: welcome message, system prompt, persona stability, dynamic variables (`{customer_name}`, `{call_sid}`, `{from_number}`, `{current_date}`, `{timezone}`), hangup and transfer triggers, conversation repair phrases, multilingual native-script prompts (Hindi/Tamil/Telugu/Kannada/Marathi/Bengali/French/Spanish), and language-switching instructions. Use when the user wants to draft, review, fix, or upgrade an agent's prompt for a specific vertical (sales, support, scheduling, BFSI reminders, recruitment, healthcare onboarding) or fix common voice-agent pathologies (over-narration, drift, robot tone, refuses to hang up, monolingual when caller switches)."
license: MIT
compatibility: Pure prompt-writing skill — no API key needed. BOLNA_API_KEY is only required if you want to test the prompt on a live call via related skills.
---

# Writing Bolna Voice Prompts

Voice prompts are different from chat prompts. The caller can't re-read, can't scroll back, and has ~1 second of attention per turn. The patterns below consistently produce natural, on-task voice conversations on Bolna.

## The four sections every voice prompt needs

| Section | Purpose | Example |
|---|---|---|
| **Personality** | Tone, pacing, energy. | "Warm, concise, perceptive. Speak slowly and clearly." |
| **Context** | Who the agent is, who it's talking to, why. | "You are calling on behalf of Acme. The caller signed up for a demo last week." |
| **Instructions** | Steps and flow. | "First ask if they have 2 minutes. If yes, walk through the 3-step demo agenda." |
| **Guardrails** | Hard rules, refusals, escalations. | "Never quote pricing. Never discuss competitors. Always hand off to a human on legal questions." |

Lead with personality + context. Voice LLMs drift toward generic chatbot tone unless you anchor them upfront.

## Hard rules that always help

- **Cap response length**: `"You will not speak more than 2 sentences at a time."` Long monologues feel robotic and steal turn-taking.
- **End each turn with a question or pause**: keeps the caller engaged and gives the STT a clean handoff point.
- **Disclose AI** in the welcome message: required in many jurisdictions, and saves time arguing.
- **Refuse out-of-scope explicitly**: `"If asked about anything not in your knowledge base, say 'I'm not able to help with that, but I can connect you to someone who can.'"` Better than hallucinating.

## Welcome message

Keep it short, personal, and variable-safe.

```
Hi {customer_name}, this is Tara from Acme. Is this a good time to talk for a minute?
```

Avoid stuffing policy text into the welcome — put behaviour rules in the system prompt instead.

If a variable isn't set at call-time, Bolna renders it as `NULL`. Either always set it via `user_data` / CSV / `ingest_source_config`, or write a graceful prompt fallback (`"If the customer's name is NULL, say 'Hi there' instead of using a name."`).

## Skeleton prompt

```
You are {agent_name}, a voice AI agent for {company_name}.

GOAL
Complete [specific task] in a short phone conversation.

STYLE
Speak naturally. Be concise. One question at a time. Avoid long lists.
Never speak more than two sentences per turn.

CONTEXT
Customer: {customer_name}
Reason for call: {callback_reason}
Current date: {current_date} in timezone {timezone}

FLOW
1. Greet warmly. Confirm you're speaking with the right person.
2. State the reason for the call in one sentence.
3. Ask the first qualifying question.
4. [Step-by-step rest of the flow.]

GUARDRAILS
- If the caller asks for a human, trigger @transfer_to_human.
- If the caller says "stop", "unsubscribe", or "do not call", apologise and end the call.
- If the caller asks about pricing details, transfer to sales. Do not improvise prices.
- If uncertain, ask a clarifying question. Do not guess.

CLOSING
Summarise the agreed next step in one sentence. Thank the caller. End the call.
```

## Dynamic variables

Reference any variable with `{name}` in either the welcome message or system prompt. Variables come from three sources:

### Auto-injected (system)

| Variable | Value |
|---|---|
| `{agent_id}` | Bolna agent UUID. |
| `{execution_id}` | This call's execution UUID. |
| `{call_sid}` | Telephony provider call ID. |
| `{from_number}` | Caller (inbound) or agent (outbound). |
| `{to_number}` | Agent (inbound) or recipient (outbound). |
| `{current_date}`, `{current_time}`, `{timezone}` | Timezone-aware datetime. |

### User-defined (custom)

Filled from `user_data` on `POST /call`, CSV columns in batch calling, or `ingest_source_config` for inbound. Define wherever needed:

```
Hi {customer_name}, I'm calling about your order {order_id}, placed on {ordered_on}.
```

Pass at call time:

```json
{
  "agent_id": "...",
  "recipient_phone_number": "+919876543210",
  "user_data": {
    "customer_name": "Priya",
    "order_id": "ORD-78234",
    "ordered_on": "12 May",
    "timezone": "Asia/Kolkata"
  }
}
```

**Always set `timezone` when your prompt mentions time.** Without it, `{current_date}` / `{current_time}` default to UTC and feel wrong.

### Graph-agent built-ins

`recipient_data.current_hour`, `_node_turns`, `_silence_repeats`, `detected_language` — see `bolna-graph-agents/references/edges-and-routing.md`. Only useful inside graph agents.

## Hangup conditions

Two ways the call ends:

| Mechanism | Configure where | Trigger |
|---|---|---|
| `task_config.hangup_after_silence` | Agent config | After N seconds of user silence (default 10s). |
| LLM-prompted hangup | System prompt | Agent decides based on the prompt. |

Write the LLM-prompted hangup explicitly:

```
HANGUP CONDITIONS
- If the caller says "bye", "goodbye", "thanks, that's all", "no thank you",
  acknowledge briefly and end the call.
- If the caller asks to be removed from the list, apologise, confirm the
  removal, and end the call.
- If you've completed the task (booked the slot, captured the lead),
  summarise once and end the call.
```

For one-shot agents (e.g. announcements that don't expect a reply), set `task_config.hangup_after_LLMCall: true` so the call ends right after the first agent response.

## Transfer conditions

```
TRANSFER CONDITIONS
- "Speak to a human" / "talk to someone" / "real person" / "manager" →
  @transfer_to_human
- Legal, medical, or financial advice questions → @transfer_to_compliance
- Refund, billing dispute, payment issue → @transfer_to_billing
```

Spell out the trigger phrases. The LLM picks the right tool by matching the user's words against your trigger language.

## Conversation repair phrases

Pre-write the awkward moments so they sound natural rather than mechanical:

| Situation | Suggested phrase |
|---|---|
| STT confidence low | `"Sorry, I didn't quite catch that — could you say it again?"` |
| Long silence | `"Are you still there?"` (auto-localised if multilingual is configured) |
| Agent doesn't know | `"That's a great question — let me find out and call you back. What's the best number to reach you?"` |
| Caller asks for human | `"Of course, transferring you now. Please hold."` (then trigger `transfer_call`) |
| Need to fetch | `"Just a moment, let me check that..."` (configure as `pre_call_message` on the tool) |

Put these as concrete strings in the prompt — don't trust the LLM to invent them under pressure.

## Persona stability on long calls

The LLM drifts on long calls. Three counter-measures:

1. **Repeat the role**: state the persona twice — once at the top, once near the bottom of the instructions block.
2. **Bound the topic**: `"You ONLY help with order tracking and returns. If the conversation drifts, politely redirect."`
3. **Use semantic routes** (`llm_agent.routes`) for FAQs / refusals. The router short-circuits common questions with zero LLM cost.

## Multilingual

The single most important rule: **write in native script, never phonetic English**.

| Language | Correct | Incorrect |
|---|---|---|
| Hindi | `नमस्ते! आप कैसे हैं?` | `Namaste! Aap kaise ho?` |
| Spanish | `¡Hola! ¿Cómo estás?` | `Hola! Como estas?` |
| French | `Bonjour ! Comment ça va ?` | `Bonjour! Comment ca va?` |

Phonetic English breaks TTS pronunciation and STT confidence both.

For agents that switch languages mid-call, add the explicit instruction:

```
LANGUAGE
Detect the caller's language and reply in the same language. If the caller
switches language, switch with them. Do not translate names, addresses,
order IDs, or legal terms unless explicitly asked. Default to {primary_language}.
```

See `references/multilingual.md` for per-language examples.

## Pacing

| Knob | Default | Effect |
|---|---|---|
| `task_config.incremental_delay` | `400ms` | Buffer before agent commits to speaking. Lower = snappier, but risk of self-interruption. |
| `task_config.number_of_words_for_interruption` | `2` | How many user words before the agent stops speaking. Raise to `4-5` for thoughtful audiences. |
| `task_config.backchanneling` | `false` | Adds "mhm", "uh-huh" between user pauses. Great for support; weird in IVR. |
| `transcriber.endpointing` | `250-700ms` | How long STT waits before finalising a turn. Higher = longer pauses tolerated. |

Pacing isn't prompt content but affects how the prompt sounds. Tune these on the agent config alongside the system prompt.

## Vertical templates

| Vertical | Template |
|---|---|
| **Sales — outbound** (warm lead) | `assets/template_sales.md` |
| **Customer support — inbound** | `assets/template_support.md` |
| **Appointment booking** | `assets/template_appointment.md` |
| **BFSI reminder / collections** (compliance-heavy) | `assets/template_bfsi_reminder.md` |
| **Recruitment screening** | `assets/template_recruitment.md` |

For more vertical examples, browse Bolna's official **Agents Library** at `https://platform.bolna.ai` — every template there is production-tested in English + Hindi.

## Review checklist

- [ ] No paragraph in the prompt is too long to speak naturally (test it aloud).
- [ ] Every `{variable}` in the prompt is filled by `user_data`, CSV, or `ingest_source_config`.
- [ ] There's a no-consent / do-not-call path.
- [ ] The agent asks one thing at a time.
- [ ] Tool calls are described with clear trigger phrases.
- [ ] Hangup conditions are explicit.
- [ ] Transfer conditions are explicit.
- [ ] Persona is anchored at top *and* near the bottom.
- [ ] Native script used for non-English content.
- [ ] Language-switching rule is stated if the agent supports multiple languages.

## Going deeper

| File | Contents |
|---|---|
| `references/multilingual.md` | Native-script per-language patterns, language-switching, formal vs informal. |
| `references/persona-and-style.md` | Tone, length caps, repair phrases, backchanneling. |
| `references/anti-patterns.md` | Common mistakes — and what they cause on a real call. |
| `assets/template_sales.md` | Warm-lead outbound sales template. |
| `assets/template_support.md` | Inbound customer support template. |
| `assets/template_appointment.md` | Appointment scheduling template (Cal.com tool integration). |
| `assets/template_bfsi_reminder.md` | BFSI EMI / payment reminder with compliance disclosures. |
| `assets/template_recruitment.md` | Candidate-screening template with structured questions. |

## See also

- `create-agent` — where the prompt slots into the agent config (`agent_prompts.task_1.system_prompt`).
- `bolna-graph-agents` — node-level prompts for graph agents.
- `create-disposition` — turning prompt outputs into structured extracted data.
- `../references/prompting-tips.md` — shared tips referenced from multiple skills.

# Persona, Style, and Pacing

Voice prompts succeed or fail on the first 5 sentences. This file collects the patterns that consistently produce natural-sounding agents.

## Personality vector

Pick *one* from each row consciously:

| Axis | Options |
|---|---|
| Energy | calm / warm / upbeat / brisk |
| Formality | formal / professional-friendly / casual |
| Pace | slow / measured / quick |
| Verbosity | terse / balanced / detailed |
| Empathy | matter-of-fact / supportive / consultative |

Then state the chosen vector at the top of the prompt:

```
PERSONALITY
Warm, supportive, consultative. Speak slowly and clearly. Keep responses balanced —
enough detail to be helpful, never lecturing.
```

Don't write "be friendly and helpful." Every LLM is told that already. Pick a *distinctive* tone.

## Length caps

Voice is slow. A single agent turn that sounds quick on paper takes 8-12 seconds at conversational pace, which is a lifetime on a call.

```
You will not speak more than 2 sentences at a time.
You will end each turn with a question or a clear next-step prompt.
```

This single rule is the difference between an agent that feels like a phone tree and one that feels like a person.

For graph agents, encode this on every node prompt — drift happens per node.

## Sentence endings

End with a question, a clear next step, or an explicit pause. Don't trail off with declaratives — the caller doesn't know whose turn it is.

| Bad | Good |
|---|---|
| "I'm calling about your appointment." | "I'm calling about your appointment — does Tuesday at 2pm still work for you?" |
| "Your order was shipped on Monday." | "Your order shipped on Monday. Want me to share the tracking number?" |

## Pacing knobs (agent config, not prompt)

| Knob | Default | When to change |
|---|---|---|
| `task_config.incremental_delay` | `400ms` | Lower (200-300ms) for snappy IVR-like agents. Raise (500-600ms) for thoughtful conversations. |
| `task_config.number_of_words_for_interruption` | `2` | Raise to 4-5 to let users finish sentences. Lower to 1 for very responsive agents. |
| `task_config.backchanneling` | `false` | Enable for support / counselling agents. Disable for IVR-style flows. |
| `task_config.backchanneling_message_gap` | `5` | Lower for more "mhms" between user pauses. |
| `transcriber.endpointing` | `250ms` (Deepgram) | Raise to 500-700 for users who pause mid-sentence. |

## Backchanneling

"Mhm", "uh-huh", "I see" between user statements makes the agent feel attentive. **Use sparingly.** Over-backchanneling makes the agent sound impatient.

Good fits: support calls, counselling, surveys (where the user does most of the talking).
Bad fits: IVR menus, sales pitches, anything fast.

## Repair phrases — pre-written

The LLM will hit awkward moments. Pre-write the phrases:

```
REPAIR PHRASES (use exactly these when needed)

When you didn't catch the user:
"Sorry, I didn't quite catch that — could you say it again?"

When you don't know an answer:
"That's a great question. Let me find out and follow up. What's the best
number to reach you on?"

When the user asks for a human:
"Of course, I'll transfer you right away. Please hold for a moment."
(then trigger @transfer_to_human)

When the user asks for time:
"It's currently {current_time} in {timezone}."

When the user is upset:
"I completely understand. Let me see what I can do."
```

The LLM tends to over-apologise or hedge. Pre-written phrases stop that.

## Persona drift on long calls

Three counter-measures, applied together:

1. **Re-anchor**: state the persona once at the top and once near the bottom of the instructions block.

```
You are Tara, a warm and concise sales agent for Acme.
... rest of prompt ...
REMEMBER: You are Tara. Stay focused on demos. Use at most two sentences per turn.
```

2. **Topic boundaries**: tell the LLM explicitly what's in and out of scope.

```
SCOPE
You only help with demo scheduling and product overviews. If the conversation
drifts (politics, weather, the agent's own nature), redirect politely:
"That's interesting, but let me get back to scheduling your demo — does
Tuesday still work?"
```

3. **Semantic routes** (`llm_agent.routes`): preset answers for common off-topic questions. Zero LLM cost when they fire.

## Honesty about being AI

Many jurisdictions require disclosure. Put it in the welcome message, not deep in the prompt:

```
"Hi {customer_name}, this is Tara, an AI assistant from Acme."
```

Beyond compliance, callers are usually more cooperative when they know it's AI — they speak more clearly and don't try to test the agent.

## Tone for difficult callers

```
DIFFICULT CALLERS
If the caller becomes aggressive, raises voice, or uses abusive language:
1. Acknowledge calmly: "I hear you — I want to help."
2. Do not argue or match the emotion.
3. Offer to transfer to a human or to schedule a callback.
4. If abuse continues for more than 30 seconds, politely end the call:
   "I'm sorry I couldn't be more help today. Please call back when you're
    able to discuss this calmly. Goodbye."
```

Most LLMs handle this poorly without explicit instructions — they apologise too much, escalate, or get sucked into argument.

## Specific words and tics to avoid

| Avoid | Use instead |
|---|---|
| "I'm just an AI..." | (Skip the disclaimer mid-call. Disclose once in welcome and move on.) |
| "Per our policy..." | "We typically..." or "Usually..." |
| "Unfortunately, I cannot..." | "I'm not able to do that, but I can..." |
| Long agreeable phrases ("Absolutely!", "Of course!", "Great question!") | Direct response — these slow the call and feel insincere |
| "As mentioned earlier..." | Voice has no "earlier" — just restate concisely |

## Testing the persona

Have someone read the prompt aloud and ask: would a real human staff member talk like this? If the answer is no, rewrite.

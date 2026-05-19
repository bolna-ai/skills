# Prompt Anti-Patterns

Concrete mistakes that show up across customer prompts, with the symptom on a real call.

## "Helpful assistant" generic tone

**Pattern**: starting the prompt with "You are a helpful AI assistant for..."

**Symptom**: agent sounds like every other chatbot — neutral, hedgy, over-apologetic.

**Fix**: pick a specific tone. `"You are Tara, a warm and direct sales agent for Acme. Speak quickly, ask one question at a time."`

## Wall-of-text prompt with no structure

**Pattern**: a single paragraph of instructions, 800+ words, no headers.

**Symptom**: agent picks up the early instructions strongly, ignores everything after the first 150 tokens.

**Fix**: use sections (`PERSONALITY`, `CONTEXT`, `FLOW`, `GUARDRAILS`, `CLOSING`). Aim for 400-600 words total. Move detail into per-tool descriptions and per-node prompts (for graph agents).

## "Be concise" without a number

**Pattern**: `"Be concise and clear."`

**Symptom**: LLM interprets "concise" generously. 3-4 sentences per turn becomes the norm.

**Fix**: `"You will never speak more than two sentences at a time. End each turn with a question."`

## Listing every possible scenario

**Pattern**: 40-item bulleted list of edge cases.

**Symptom**: contradictions between rules; LLM picks the wrong rule under pressure.

**Fix**: 5 hard rules in the system prompt. Move long-tail logic to `routes` (semantic routing) or to graph-agent nodes.

## Asking 3 things per turn

**Pattern**: `"Ask the caller for their name, email, and reason for calling."`

**Symptom**: caller answers only one; agent restates the missing two; caller gets confused.

**Fix**: one question per turn. `"Ask the caller's full name. Once you have it, ask for their email."`

## Phonetic non-English

**Pattern**: `"Namaste! Aap kaise ho?"`

**Symptom**: TTS reads as garbled English; STT logs lower confidence; agent and caller mishear each other.

**Fix**: native script. `"नमस्ते! आप कैसे हैं?"` See `references/multilingual.md`.

## Missing language-switching rule

**Pattern**: prompt only in English, no instruction about what to do if caller speaks Hindi.

**Symptom**: agent keeps replying in English to Hindi callers; calls drop.

**Fix**: `"Reply in the language the caller is using. If they switch language, switch with them."`

## No hangup conditions

**Pattern**: prompt never tells the LLM when to end the call.

**Symptom**: agent keeps asking "is there anything else?" forever. Calls run to `call_terminate` (5 min default).

**Fix**: explicit hangup conditions. `"If the caller says 'bye', 'thanks', or 'no thank you', acknowledge briefly and end the call."`

## Over-aggressive hangup

**Pattern**: `"If the caller doesn't say yes immediately, end the call."`

**Symptom**: agent hangs up when caller pauses to think.

**Fix**: gate hangup on explicit user signals, not silence. Use `task_config.hangup_after_silence` for silence cases.

## Hardcoded times instead of variables

**Pattern**: `"It is currently 10:30 AM."`

**Symptom**: agent says 10:30 AM at 8 PM. Caller laughs.

**Fix**: use `{current_time}` and `{timezone}`. Always pass `timezone` in `user_data`.

## Variable that's never filled

**Pattern**: `"Confirm with {customer_email}"` but no `customer_email` in `user_data`.

**Symptom**: agent says "Confirm with NULL". Or worse, says the word "NULL" verbatim.

**Fix**: either always fill the variable, or write a conditional: `"If we have an email on file, confirm it. If not, ask for it."`

## Tool description that describes the API, not the trigger

**Pattern**: `"description: Fetches order status from the orders API."`

**Symptom**: LLM doesn't know when to call it. Either never fires, or fires constantly.

**Fix**: describe the *trigger*. `"Use when the caller asks about order status, delivery, tracking, shipping, or ETA. Caller must provide an order ID."`

## Polite refusal becomes a loop

**Pattern**: `"If asked about pricing, politely decline."`

**Symptom**: caller keeps asking; agent keeps declining; call dies in a polite loop.

**Fix**: refusal + redirect. `"If asked about pricing, say 'I can't share pricing on this call, but I can connect you to someone who can — would you like that?' If yes, trigger @transfer_to_sales."`

## "Speak naturally"

**Pattern**: `"Speak naturally and conversationally."`

**Symptom**: LLM picks generic "natural" — chatty, over-polite.

**Fix**: be specific about the *kind* of natural. `"Speak like a friendly receptionist who's been doing this for ten years — direct, warm, no script tone."`

## Sales pitches as monologues

**Pattern**: agent's opening is 4 sentences of value props.

**Symptom**: caller hangs up before the pitch ends. Conversion drops.

**Fix**: open with a permission question. `"Hi {customer_name}, this is Tara from Acme — got 30 seconds to share why I'm calling?"` Then proceed only if the caller says yes.

## Greeting with too much info

**Pattern**: `"Hello, my name is Tara, I'm a voice AI from Acme Corporation, calling regarding your recent inquiry about our enterprise plan..."`

**Symptom**: caller interrupts before you get to the point.

**Fix**: 1-sentence greeting, then a question. `"Hi {customer_name}, this is Tara from Acme. Got a minute?"`

## Long-list reading

**Pattern**: `"Read these 8 available time slots to the caller."`

**Symptom**: caller forgets the first option by the time you finish.

**Fix**: read 2-3 slots, then ask. `"I have 10 AM, 2 PM, or 4 PM on Thursday. Which works?"`

## Treating the system prompt as documentation

**Pattern**: prompt contains "the agent should handle X by doing Y", or paragraphs of project background.

**Symptom**: LLM treats project context as content, mentions it on the call.

**Fix**: write the prompt *as instructions to the LLM*, not *as documentation about the agent*. Direct: "Do X." Not: "The agent does X."

## No closing

**Pattern**: prompt has goal + flow but no closing line.

**Symptom**: calls drag past the goal because the LLM doesn't know when the conversation is "done."

**Fix**: explicit closing. `"Once you've confirmed the appointment, summarise it in one sentence, thank the caller, and end the call."`

## See also

- `references/persona-and-style.md` — what to use *instead* of these patterns.
- `references/multilingual.md` — multilingual-specific pitfalls.
- `bolna-graph-agents/SKILL.md` — when to graduate from a single prompt to a graph agent.

---
name: write-bolna-prompts
description: "Write and improve Bolna voice-agent prompts, welcome messages, multilingual instructions, dynamic variables, hangup rules, transfer conditions, extraction guidance, and conversation repair phrases. Use when the user wants a better Bolna agent script or production-ready system prompt."
license: MIT
compatibility: "No API key required unless testing with live Bolna calls."
---

# Write Bolna Prompts

## Voice prompt principles

- Keep spoken turns short. Prefer one question at a time.
- Put identity, purpose, boundaries, and escalation rules near the top.
- Use dynamic variables exactly as `{variable_name}` and pass values through `user_data`, CSV columns, or inbound caller matching.
- For Indian or regional languages, write important phrases in the native script instead of Romanized text.
- Define hangup conditions explicitly: wrong number, do-not-call request, abusive caller, task complete, voicemail, repeated silence.
- Define transfer conditions explicitly: human requested, high-risk complaint, payment issue, legal or medical advice, account lockout.

## Prompt skeleton

```text
You are {agent_name}, a voice AI agent for {company_name}.

Goal:
Complete [specific task] in a short phone conversation.

Style:
Speak naturally, be concise, ask one question at a time, and avoid long lists.

Context:
Customer name: {customer_name}
Reason for call: {callback_reason}
Current date: {current_date}
Current time: {current_time} ({timezone})

Rules:
1. Verify you are speaking with the right person before discussing account details.
2. If the caller asks for a human, transfer the call or capture a callback request.
3. If the caller says stop, unsubscribe, or do not call, apologize and end the call.
4. If uncertain, ask a clarifying question instead of guessing.

Completion:
Summarize the agreed next step, thank the caller, and end the call.
```

## Welcome message

Keep it short and variable-safe:

```text
Hi {customer_name}, this is Tara from Acme. Is this a good time to talk for a minute?
```

Avoid stuffing the welcome message with full policy text; put behavior rules in the system prompt.

## Dynamic variables

Useful built-ins from Bolna context docs include:

- `{agent_id}`
- `{call_sid}`
- `{to_number}`
- `{from_number}`
- `{current_date}`
- `{current_time}`
- `{timezone}`

Custom variables come from `user_data`, batch CSV columns, or inbound source config.

## Multilingual prompt rule

For multilingual agents, state the language switching rule clearly:

```text
Detect the caller's language. Reply in the same language. If the caller switches language, switch with them. Do not translate names, addresses, order IDs, or legal terms unless asked.
```

Use native script for critical Hindi, Tamil, Telugu, Kannada, Marathi, Bengali, or other regional-language phrases when pronunciation matters.

## Review checklist

- No paragraph is too long to speak naturally.
- Variables in prompt match API `user_data` or CSV headers exactly.
- There is a no-consent and do-not-call path.
- The agent asks one thing at a time.
- Tool calls are described with clear trigger conditions.
- End state is explicit.

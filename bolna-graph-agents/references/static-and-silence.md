# Static Nodes & Silence Repeat

## Static nodes

Pre-render audio at agent-save time so playback at runtime is ~50ms instead of ~800ms LLM round-trip. Zero LLM cost, zero TTS cost.

```json
{
  "id": "greeting",
  "node_type": "static",
  "static_message": "Hi! Thanks for calling Acme. How can I help today?",
  "edges": [
    { "to_node_id": "main_menu", "condition": "User responds with a request" }
  ]
}
```

### When to make a node static

- Greetings and welcomes (always the same text).
- Confirmations after a positive outcome (`"All set, you're booked."`).
- Closings (`"Have a great day, goodbye."`).
- Confirmation responses to events (payment confirmed, OTP verified).
- Hold messages while tools fire (`"Just a moment..."` — though `pre_call_message` on the tool itself usually covers this).

### When NOT to make it static

- Anything with dynamic data that changes per call. (Exception: if you template safely from `context_data` and re-save the agent on every change, but that's rarely worth it.)
- Nodes where the LLM should adapt tone based on the customer's mood.
- Anything personalised beyond the welcome message.

### Latency / cost comparison

| Node type | Latency | Cost per turn |
|---|---|---|
| LLM node | ~800ms (LLM + TTS + audio) | LLM tokens + TTS characters |
| Static node | ~50ms (cached audio stream) | Zero |

### Cache invalidation

Audio is generated when you save the agent. If you change `static_message` later, you must re-save the agent so the cache regenerates with the new text. Same applies if you change the agent's TTS voice or model — re-save to refresh cached audio.

## Silence repeat

`repeat_after_silence_seconds` makes a node auto-replay after N seconds of user silence and exposes `_silence_repeats` to expression edges so you can escalate.

```json
{
  "id": "greeting",
  "node_type": "static",
  "static_message": "Hi! Thanks for calling. How can I help?",
  "repeat_after_silence_seconds": 8,
  "edges": [
    { "to_node_id": "main_menu", "condition": "User responds" },
    {
      "to_node_id": "goodbye",
      "condition_type": "expression",
      "expression": {
        "conditions": [{ "variable": "_silence_repeats", "operator": "gte", "value": 3 }]
      }
    }
  ]
}
```

### Behaviour

1. Silence timer fires after `repeat_after_silence_seconds`.
2. `_silence_repeats` increments by 1.
3. Expression edges evaluate. If one matches, transition.
4. Otherwise replay the node. Static = same cached audio (free). LLM = re-generate with `[silence]` in history.
5. On any transition out of the node, `_silence_repeats` resets to 0.

### Works on LLM nodes too

```json
{
  "id": "collect_email",
  "prompt": "Ask politely for the customer's email address.",
  "repeat_after_silence_seconds": 10,
  "edges": [
    {
      "to_node_id": "confirm_email",
      "condition": "User shared an email",
      "parameters": { "email": "string" }
    },
    {
      "to_node_id": "goodbye",
      "condition_type": "expression",
      "expression": {
        "conditions": [{ "variable": "_silence_repeats", "operator": "gte", "value": 3 }]
      }
    }
  ]
}
```

On an LLM node, the model sees `[silence]` in conversation history and rephrases naturally without extra prompt engineering ("Could you share your email?" → "Sorry, I didn't catch that, could you tell me your email?" → transition to goodbye).

## Patterns

### Greeting that gives up gracefully

```
Welcome (static, 8s silence) → [3 silent repeats] → Goodbye (static)
                              → [user responds] → Main menu
```

### Collect-with-retry

```
Ask for email (LLM, 10s silence)
  → [user gives email] → Confirm
  → [_silence_repeats >= 2] → Offer SMS instead
  → [_node_turns >= 3] → Transfer to human
```

The two expression edges combine `_silence_repeats` (silent) and `_node_turns` (tried but failed) for different escalation paths.

### Multi-step compliance disclosure

```
Disclosure 1 (static, 5s silence, max 2 repeats) → Disclosure 2 → Disclosure 3 → Consent
```

Each disclosure stays static so the legally-vetted wording is byte-identical on every call.

## Tips

- **Replay budget**: don't let `_silence_repeats` go above 3-4 — callers get frustrated. Escalate to a human or hang up.
- **Different silence thresholds per node**: long-pause-OK nodes (thinking about an answer) get 15-20s; quick-prompt nodes (yes/no) get 5-7s.
- **Static is not always cached**: only nodes with `node_type: "static"` are cached. Don't expect free playback from LLM nodes even if their text never varies.

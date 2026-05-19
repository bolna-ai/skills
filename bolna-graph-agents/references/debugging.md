# Debugging Graph Agents

Read the routing logs. They tell you *what* the routing system saw and *why* it picked the transition it did. Most graph-agent bugs are diagnosed in one log line.

## Log formats

**LLM-routed turn:**

```
Routing decision (LLM): transition_to_offer_pitch | confidence: 0.95 |
  reasoning: Customer confirmed identity by saying 'yeah'. (latency: 210ms)
```

**Deterministic turn** (expression or unconditional edge fired first):

```
Routing decision (deterministic): -> after_hours |
  deterministic:expression:Outside working hours (latency: 0.6ms)
```

| Field | Meaning |
|---|---|
| `LLM` vs `deterministic` | Did the routing LLM run, or did an expression/unconditional/event edge fire? |
| `transition_to_<id>` / `-> <id>` | Which target node was picked. |
| `confidence` (LLM only) | Close to `1.0` = clear match. Below `0.6` = ambiguous edges. |
| `reasoning` | Why this transition was chosen. **Most useful field.** |
| `latency` | Deterministic = sub-millisecond. LLM routing = ~150-300ms typical. |

When the routing LLM returns `stay_on_current_node`, the agent still produces a response on the current node. It does not stay silent.

## Symptom → root cause

### Agent keeps re-asking instead of moving forward

Routing is returning `stay_on_current_node`. Read the `reasoning` field — it explains what it thought was missing.

Likely causes:

| Cause | Fix |
|---|---|
| Edge `condition` is too narrow or uses vocabulary the LLM doesn't associate with the user's reply | Rewrite the condition with broader phrasing; add synonyms |
| Customer's input genuinely doesn't match anything | Add a fallback edge (`"User wants something else"`) targeting a clarification or transfer node |
| Edge has `parameters` and the user hasn't provided one of the required values | Move the missing-value handling to the same node's prompt; ask for the value before transitioning |

### Agent routes to the wrong node

Two edge conditions overlap. The routing LLM is matching the less-specific one.

| Fix | How |
|---|---|
| Make conditions mutually exclusive | "Customer wants to book" vs "Customer wants to reschedule" — make sure both can't be true at once |
| Add an `expression` edge for the deterministic case | If "after hours" should always win, encode it as an expression edge with `priority: 0` |
| Use `function_name` / `function_description` to disambiguate | Sometimes the auto-generated tool name confuses the routing LLM |

### Confidence is consistently low

Edge conditions are too similar to each other.

- Rewrite each condition to describe a distinct customer intent.
- Move data-driven branches (time, retry count, language) into expression edges.

### Agent skips a node unexpectedly

An expression edge fired before the LLM got a chance. Check the previous node's expression edges for overly broad conditions like `_node_turns >= 1` — that fires on the second turn no matter what the customer said.

### Time-based expression never fires

`recipient_data.timezone` was not set on the call. Without it, `current_hour`, `current_weekday`, etc. are silently unpopulated and every time-based comparison returns false.

Fix: pass `timezone` in `POST /call`'s `user_data`:

```json
{ "user_data": { "timezone": "Asia/Kolkata" } }
```

### Agent forgets earlier context on long calls

The response LLM only sees the most recent ~50 messages. On very long flows, earlier turns drop out.

Fix: persist critical state into `context_data` via edge `parameters` or event `properties`, then reference via `{variable}` in later node prompts. Don't rely on the LLM rediscovering it from transcript history.

### Static node plays the wrong text or wrong voice

Cache was built from an earlier config. Re-save the agent so the cache regenerates from the current `static_message` and current TTS voice.

### Event fires but agent stays silent

In rough order of likelihood:

1. Call already ended. You should have got `404` not `202` — check your firing code.
2. Event name doesn't match any edge on the **current** node. Event edges only fire on the active node. Check the most recent `Routing decision` log line for where the call was.
3. User was speaking when the event resolved. The node transitioned, but proactive speech was deliberately skipped. The next user turn will route on the new node naturally.
4. No event edge for that name on the node. Add one or rename the event.

### Routing LLM is "thinking" too long

`routing_max_tokens` is too high, or the model is GPT-5-class without `routing_reasoning_effort: minimal`.

- For most flows, `routing_max_tokens: 150` is plenty.
- On GPT-5 routing models, set `routing_reasoning_effort: "minimal"` — full reasoning is overkill for routing.

### Inline-extracted variables are missing in downstream nodes

The transition didn't actually fire — the user reply didn't satisfy the edge's `parameters`. Routing LLM treats `parameters` as required; if any field is missing, it doesn't transition.

- Check the `reasoning` field in the log — it usually says which parameter was missing.
- Either loosen the requirement (split into multiple nodes, one field each) or improve the node prompt so the user is asked for *all* required fields before the LLM tries to transition.

## Useful checks before going live

- [ ] Every node has at least one exit edge OR is terminal.
- [ ] Every external API has a spoken fallback if it fails.
- [ ] Static-node text matches the current cache (re-saved after last edit).
- [ ] Time-based expressions are protected by either a default-timezone fallback or a `timezone` requirement at call creation.
- [ ] Event edges have a non-event fallback (timeout via `_node_turns` / `_silence_repeats`).
- [ ] Routing decision logs were inspected on a real test call before scale-up.

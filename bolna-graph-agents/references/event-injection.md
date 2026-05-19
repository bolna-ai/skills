# Real-Time Event Injection

Push named events into a live call from your backend. A matching event edge transitions the conversation and triggers proactive agent speech in under a second — no waiting for the user to speak.

## Endpoint

```
POST https://api.bolna.ai/v1/call/{run_id}/events
```

```bash
curl -X POST https://api.bolna.ai/v1/call/$RUN_ID/events \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "payment_completed",
    "properties": { "ref": "TXN-98765", "amount": "599" }
  }'
```

**Responses:**

```
202 Accepted    { "status": "accepted", "event": "...", "run_id": "..." }
404 Not Found   { "detail": "No active call found for this run_id" }
```

Fire-and-forget. The endpoint returns 202 as soon as the event is published, before the agent has actually spoken.

## Where to get `run_id`

| Direction | Source |
|---|---|
| Outbound | `execution_id` field returned by `POST /call`. |
| Inbound | Comes through in your webhook's first `queued` / `initiated` payload. |

## Defining an event edge

```json
{
  "id": "awaiting_payment",
  "prompt": "Reassure the user while the payment processes. Amount: {currency} {amount}.",
  "edges": [
    { "to_node_id": "confirmation", "condition_type": "event", "event_name": "payment_completed" },
    { "to_node_id": "payment_failed", "condition_type": "event", "event_name": "payment_failed" }
  ]
}
```

A node can mix LLM, expression, and event edges freely. Whichever input arrives first drives the transition.

| Field | Required | Notes |
|---|---|---|
| `condition_type` | Yes — `"event"` | Skipped during normal speech routing. |
| `event_name` | Yes | Free-form string. Match exactly what your backend POSTs. |
| `to_node_id` | Yes | Target node. |
| `priority` | No | If multiple event edges match the same name, lower fires first. Default `0`. |

## What happens when an event arrives

| Scenario | Behaviour |
|---|---|
| Matches an event edge on the current node | `properties` merged into `context_data`, transition fires, agent speaks proactively on the target node. |
| Doesn't match any edge | `properties` still merged into `context_data`. No transition, no speech, but the next LLM call sees the new context. |
| Agent currently speaking | Buffered. Processed after the current utterance finishes. |
| User speaking when event resolves | Node transitions, but **proactive speech is skipped**. The user's in-progress utterance routes on the new node. Prevents the agent from interrupting itself. |
| LLM is generating a response | Buffered until generation completes. |
| Two events arrive rapidly | Processed sequentially in arrival order. |
| Event targets a static node | Cached audio plays in ~50ms, zero LLM cost. |
| Event arrives on a node with no event edges for that name | No transition. `properties` still merge silently. |

## Properties become context variables

The `properties` object in the event body merges into the agent's `context_data`. Each key becomes available as:

- `{property_name}` in the target node's `prompt`.
- `{ "variable": "property_name", "operator": "eq", "value": "..." }` in downstream expression edges.
- `%(property_name)s` in API tool parameter templates.

**Example:**

```bash
curl -X POST https://api.bolna.ai/v1/call/$RUN_ID/events \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -d '{ "event": "payment_failed", "properties": { "error_reason": "Card declined" } }'
```

```json
{
  "id": "payment_failed",
  "prompt": "Payment failed: {error_reason}. Apologise briefly and offer to retry."
}
```

The agent says something like *"Sorry, that didn't go through — looks like the card was declined. Want to try a different card?"*

## End-to-end payment confirmation

```json
[
  {
    "id": "awaiting_payment",
    "prompt": "Payment initiated for {currency} {amount}. Reassure the user briefly while it processes.",
    "repeat_after_silence_seconds": 20,
    "edges": [
      { "to_node_id": "confirmation", "condition_type": "event", "event_name": "payment_completed" },
      { "to_node_id": "payment_failed", "condition_type": "event", "event_name": "payment_failed" }
    ]
  },
  {
    "id": "confirmation",
    "node_type": "static",
    "static_message": "Payment confirmed. Thank you! Have a great day.",
    "edges": []
  },
  {
    "id": "payment_failed",
    "prompt": "Payment failed: {error_reason}. Apologise briefly and offer to retry.",
    "edges": []
  }
]
```

Backend handler (Python):

```python
import requests, os

def fire_event(run_id, event, properties=None):
    return requests.post(
        f"https://api.bolna.ai/v1/call/{run_id}/events",
        headers={"Authorization": f"Bearer {os.environ['BOLNA_API_KEY']}"},
        json={"event": event, "properties": properties or {}},
        timeout=5,
    )

# Inside your payment-gateway webhook
fire_event(run_id, "payment_completed", {"ref": "TXN-98765"})
```

`confirmation` is static — the caller hears it in ~50ms. `payment_failed` is LLM-backed because the apology should sound natural given the specific error reason.

## How proactive speech stays natural

When an event drives a transition, the agent must speak without the user saying anything. Two design choices keep this feeling natural:

1. Event `properties` merge into `context_data`, so the target node's `prompt` can reference them.
2. The conversation history is **not** polluted with fake user messages. The agent simply produces a new assistant turn on the new node.

Transcripts read as consecutive assistant messages, exactly as a human agent would speak after seeing a screen update.

## Latency

| Target node | Latency | Cost |
|---|---|---|
| LLM node | ~800ms (LLM + TTS) | LLM + TTS |
| Static node | ~50ms (cached audio) | Zero |

If the response is invariant ("Payment confirmed!"), point your event edge at a static node for the fastest possible response.

## Common gotchas

- **`404`**: call already ended. The user hung up, or `call_terminate` fired. Check the last execution status.
- **`202` but agent stays silent**: event name doesn't match any edge on the **current** node. Event edges only fire on the active node. Check routing logs for where the call was when the event landed.
- **Event arrives mid-utterance**: transition happens, but proactive speech is deliberately suppressed. The user's next reply routes on the new node, so the agent's first words still feel responsive.
- **Multiple events same name**: processed in arrival order. If you re-fire `payment_completed` accidentally, it tries to transition again from whatever node the call is on now — usually a no-op, but check your retry logic.
- **`properties` overwrite prior `context_data` keys** with the same name. Namespace events carefully (`payment_ref` vs generic `ref`).

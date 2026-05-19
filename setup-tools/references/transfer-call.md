# Transfer Call

`transfer_call` is Bolna's built-in tool for routing a live call to a human or another number. It's wired into the telephony layer — the call leg switches at the carrier, the agent doesn't need to "speak" the transfer to anyone.

## Basic config

```json
{
  "tools": [
    {
      "key": "transfer_call",
      "name": "transfer_to_human",
      "description": "Transfer when the caller explicitly asks for a human agent or the issue requires manual escalation.",
      "parameters": {
        "type": "object",
        "required": ["call_sid"],
        "properties": {
          "call_sid": { "type": "string", "description": "Unique call id" }
        }
      },
      "pre_call_message": "Sure, I'll transfer the call for you. Please wait a moment."
    }
  ],
  "tools_params": {
    "transfer_to_human": {
      "url": null,
      "method": "POST",
      "headers": {},
      "param": {
        "call_sid": "%(call_sid)s",
        "call_transfer_number": "+919876543210"
      }
    }
  }
}
```

| Field | Notes |
|---|---|
| `key` | Always `"transfer_call"`. Identifies the built-in. |
| `name` | Free-form. Used as the LLM-visible tool name. Make it specific (e.g. `transfer_to_sales`). |
| `parameters.call_sid` | The system-injected call ID. The LLM doesn't actually have to collect it; Bolna substitutes it from `%(call_sid)s`. |
| `tools_params.<name>.param.call_transfer_number` | E.164 destination. |
| `pre_call_message` | What the agent says while the bridge happens. |

## Multiple destinations

Add one tool per department. The LLM picks based on the description.

```json
{
  "tools": [
    {
      "key": "transfer_call",
      "name": "transfer_to_sales",
      "description": "Transfer to sales when the caller asks about pricing, demos, new purchase, or wants to upgrade their plan.",
      "parameters": { "type": "object", "required": ["call_sid"], "properties": { "call_sid": { "type": "string" } } },
      "pre_call_message": "Transferring you to sales — one moment."
    },
    {
      "key": "transfer_call",
      "name": "transfer_to_support",
      "description": "Transfer to support when the caller reports a bug, technical issue, or product problem.",
      "parameters": { "type": "object", "required": ["call_sid"], "properties": { "call_sid": { "type": "string" } } },
      "pre_call_message": "Transferring you to support — one moment."
    },
    {
      "key": "transfer_call",
      "name": "transfer_to_billing",
      "description": "Transfer to billing for invoice, refund, payment, or subscription billing questions.",
      "parameters": { "type": "object", "required": ["call_sid"], "properties": { "call_sid": { "type": "string" } } },
      "pre_call_message": "Transferring you to billing — one moment."
    }
  ],
  "tools_params": {
    "transfer_to_sales":   { "url": null, "method": "POST", "param": { "call_sid": "%(call_sid)s", "call_transfer_number": "+919876543210" } },
    "transfer_to_support": { "url": null, "method": "POST", "param": { "call_sid": "%(call_sid)s", "call_transfer_number": "+919876543211" } },
    "transfer_to_billing": { "url": null, "method": "POST", "param": { "call_sid": "%(call_sid)s", "call_transfer_number": "+919876543212" } }
  }
}
```

This is better than a single `transfer_call(team: string)` tool — the LLM gets a sharper choice, descriptions can be tuned independently, and routing decisions are more reliable.

## In a graph agent

Use `function_call` on the transfer node to force the LLM's `tool_choice`. This guarantees the LLM picks the transfer tool the moment the conversation reaches this node:

```json
{
  "id": "transfer_to_sales_node",
  "prompt": "Transfer the call to the sales team.",
  "function_call": "transfer_to_sales",
  "edges": []
}
```

Combine with an upstream expression edge for fast routing (working hours, retry count) so the call reaches the transfer node deterministically:

```json
{
  "to_node_id": "transfer_to_sales_node",
  "condition_type": "expression",
  "expression": {
    "logic": "and",
    "conditions": [
      { "variable": "recipient_data.current_hour", "operator": "gte", "value": 9 },
      { "variable": "recipient_data.current_hour", "operator": "lt",  "value": 18 }
    ]
  }
}
```

## Best practices

| Do | Don't |
|---|---|
| One tool per destination with specific triggers | A single tool with a `team` parameter |
| Always set `pre_call_message` | Leave the caller in silence during the bridge |
| Test the destination number once a day | Assume the destination stays reachable forever |
| Plan a fallback for busy / no-answer destinations | Let the call die silently if transfer fails |
| Pair with an `after_hours` expression edge | Transfer to a desk that's closed |

## Failure handling

`transfer_call` doesn't currently return rich error info back to the agent. To handle "destination didn't answer" gracefully:

- Provide a **fallback prompt branch** that captures voicemail / callback info before transferring, so if the bridge fails the agent has already taken the lead.
- Or set `task_config.hangup_after_LLMCall: true` after the transfer fires so the conversation ends cleanly on Bolna's side regardless of bridge outcome.

## Conversation example

```
Caller:  "Hey, I'd like to upgrade my plan to the annual one."
Agent:   "Great — I'll transfer you to our sales team to handle that.
          One moment please..."
[Agent triggers transfer_to_sales → call bridges to +919876543210]
```

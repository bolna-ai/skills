# Edges & Routing — Deep Dive

## Edge types

| `condition_type` | When evaluated | Cost | Use for |
|---|---|---|---|
| `"llm"` (default) | After deterministic rules don't match, every user turn | 1 routing LLM call | Intent-based transitions |
| `"expression"` | First, before LLM | Free | Time, retry counts, language, any context-variable check |
| `"unconditional"` | First, before LLM | Free | Only-possible-next-step transitions |
| `"event"` | When matching event arrives via REST | Free | External signals (payment, form, link click) |

Deterministic edges (expression, unconditional, event) are evaluated **in `priority` order** before any LLM call. First match wins.

## Expression syntax

```json
{
  "to_node_id": "after_hours",
  "condition": "Outside working hours",
  "condition_type": "expression",
  "expression": {
    "logic": "or",
    "conditions": [
      { "variable": "recipient_data.current_hour", "operator": "lt",  "value": 10 },
      { "variable": "recipient_data.current_hour", "operator": "gte", "value": 18 }
    ]
  }
}
```

- `logic`: `"and"` (all must match) or `"or"` (any one). Default `"and"`.
- `conditions[]`: each has `variable`, `operator`, `value`.

### Operators

| Group | Operators |
|---|---|
| Equality | `eq`, `neq` |
| Numbers | `gt`, `gte`, `lt`, `lte` |
| Text | `contains` |
| Lists | `in`, `not_in` |
| Existence | `exists`, `not_exists` |

### Priority semantics

- Default priority: `0` for deterministic, `100` for LLM.
- Lower fires first.
- For mutually-exclusive deterministic rules (working hours vs after hours), set distinct priorities — don't rely on declaration order.

```json
{ "priority": 0, ... }     // working hours
{ "priority": 1, ... }     // after hours fallback
```

## Built-in variables

| Variable | Type | Notes |
|---|---|---|
| `recipient_data.current_hour` | int (0-23) | Hour in the call's timezone. |
| `recipient_data.current_minute` | int (0-59) | |
| `recipient_data.current_weekday` | string | Lowercase, e.g. `"wednesday"`. |
| `recipient_data.current_day` | int (1-31) | |
| `recipient_data.current_month` | int (1-12) | |
| `recipient_data.current_year` | int | |
| `recipient_data.current_date` | string | **Display only**, not for comparisons. |
| `recipient_data.current_time` | string | **Display only**, not for comparisons. |
| `recipient_data.timezone` | string | tz database name. |
| `recipient_data.user_number` | string | E.164 phone. |
| `detected_language` | string | Top-level, not under `recipient_data`. `"hindi"`, `"en"`, etc. |
| `_node_turns` | int | User messages on the current node. Resets on transition. |
| `_total_turns` | int | User messages in the entire call. |
| `_silence_repeats` | int | Silence-triggered replays on the current node. Resets on transition. |

> Time variables (`current_hour`, `current_weekday`, etc.) populate **only when `recipient_data.timezone` is set on the call**. Without it, every time-based expression silently returns false. Always pass `timezone` to `POST /call`.

## Common expression patterns

**Working hours**

```json
{
  "condition_type": "expression",
  "expression": {
    "logic": "and",
    "conditions": [
      { "variable": "recipient_data.current_hour", "operator": "gte", "value": 10 },
      { "variable": "recipient_data.current_hour", "operator": "lt",  "value": 18 }
    ]
  }
}
```

**Weekend detection**

```json
{
  "condition_type": "expression",
  "expression": {
    "conditions": [
      { "variable": "recipient_data.current_weekday", "operator": "in", "value": ["saturday", "sunday"] }
    ]
  }
}
```

**Auto-escalate after retries**

```json
{
  "to_node_id": "transfer_call",
  "condition_type": "expression",
  "expression": {
    "conditions": [
      { "variable": "_node_turns", "operator": "gte", "value": 2 }
    ]
  }
}
```

**Language-aware branching**

```json
{
  "to_node_id": "hindi_flow",
  "condition_type": "expression",
  "expression": {
    "conditions": [
      { "variable": "detected_language", "operator": "eq", "value": "hindi" }
    ]
  }
}
```

**Required field check**

```json
{
  "to_node_id": "summarize_order",
  "condition_type": "expression",
  "expression": {
    "conditions": [
      { "variable": "order_id", "operator": "exists" }
    ]
  }
}
```

## Inline data extraction

Edges can capture typed values from the user's reply during routing. The routing LLM treats them as required parameters; on a successful transition the values are merged into `context_data`.

```json
{
  "to_node_id": "confirm_order",
  "condition": "Customer provided their order id",
  "parameters": { "order_id": "string" }
}
```

After the transition, `context_data["order_id"]` is set:

- Reference in node prompts via `{order_id}`.
- Use in expression edges: `{ "variable": "order_id", "operator": "exists" }`.
- Pass to API tools as `%(order_id)s`.

**Prefer `parameters` over a separate "extract" node.** One LLM call routes and captures data, saving latency and tokens.

## Routing instructions

Prepended to every routing request. Keep it short and directive:

```
You are the Routing System for this conversation. Analyze the user's input
and the available edges. Select the edge whose condition best matches.
If no edge matches, stay on the current node.
```

Supports `{variable}` substitution from `context_data` (and flattened `recipient_data`). Missing keys render as `NULL`.

## When routing returns `stay_on_current_node`

The agent **still produces a response** on the current node — it does not stay silent. The node's prompt is invoked normally; only the transition is suppressed. This is fine when the user is mid-conversation; it's a bug when the user already gave you what you needed but the LLM didn't see it as matching any edge. Either loosen the condition or add a deterministic fallback.

## Function-name overrides

By default each LLM edge becomes a routing tool named `transition_to_<to_node_id>` with `condition` as the description. Override when you want a more descriptive name or when two edges share the same target:

```json
{
  "to_node_id": "confirm",
  "condition": "Customer confirmed",
  "function_name": "user_confirmed_appointment",
  "function_description": "Use when the customer confirms the proposed appointment slot."
}
```

This helps when the routing LLM's chain-of-thought gets confused by similarly-named tools.

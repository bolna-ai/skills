# Reading Raw Execution Logs

`GET /executions/{execution_id}/log` returns a flat array of every prompt, request, response, and event that ran during the call, in order. The single most powerful diagnostic Bolna provides.

## Shape

```json
{
  "execution_id": "abc123",
  "data": [
    {
      "component": "system",
      "type": "event",
      "data": "call_started",
      "timestamp": "2026-05-19T10:00:00.123Z"
    },
    {
      "component": "transcriber",
      "type": "response",
      "data": "hello can you hear me",
      "timestamp": "2026-05-19T10:00:01.456Z"
    },
    {
      "component": "llm",
      "type": "request",
      "data": "<system + user messages sent to OpenAI>",
      "timestamp": "2026-05-19T10:00:01.500Z"
    },
    {
      "component": "llm",
      "type": "response",
      "data": "Hi there! How can I help you today?",
      "reasoning_content": "The user greeted, so I should greet back and ask their intent.",
      "timestamp": "2026-05-19T10:00:02.123Z"
    },
    {
      "component": "synthesizer",
      "type": "request",
      "data": "Hi there! How can I help you today?",
      "timestamp": "2026-05-19T10:00:02.150Z"
    },
    {
      "component": "tool",
      "type": "request",
      "data": "{ \"order_id\": \"ORD-78234\" }",
      "tool_name": "check_order_status",
      "timestamp": "2026-05-19T10:00:08.000Z"
    },
    {
      "component": "tool",
      "type": "response",
      "data": "{ \"status\": \"shipped\", \"eta\": \"2026-05-22\" }",
      "tool_name": "check_order_status",
      "timestamp": "2026-05-19T10:00:08.412Z"
    }
  ]
}
```

| Field | What it tells you |
|---|---|
| `component` | `transcriber`, `llm`, `synthesizer`, `tool`, `system`, `routing` (for graph agents). |
| `type` | `request`, `response`, `event`. |
| `data` | The actual content. For LLM responses, this is the assistant text. |
| `reasoning_content` | Present when the LLM exposes traceable reasoning (GPT-5, Claude with extended thinking). Indispensable for "why did it respond that way?" |
| `tool_name` | On tool entries, which tool fired. |
| `timestamp` | Wall-clock time for each event. |

## What to look for, by symptom

### "Agent ignored the customer's email"

Search for `component: "transcriber"` and `type: "response"` near the time the customer said the email. If the transcribed text is wrong ("priya at example dot com" → transcribed as "priya example com"), the LLM never saw the right input. Fix: switch transcriber model, or add a confirmation step in the prompt.

### "Agent called the wrong tool"

Look at the LLM response just before the tool call. The `reasoning_content` (if exposed) will tell you why. Common causes: descriptions too similar, vague trigger phrases.

### "Tool fired with empty parameters"

`component: "tool"` + `type: "request"` shows the exact `data` payload. If a parameter is literally `"%(order_id)s"`, the substitution failed — the LLM didn't collect that field. Fix: make the parameter `required` and tighten the prompt.

### "Agent went off-script"

Walk the `component: "llm"` + `type: "response"` entries in order. The first one that drifts is where to look — usually the user's preceding turn confused the prompt. Either tighten the prompt (`"Only answer questions about X. If asked something else, redirect."`) or use a graph agent for stricter flow control.

### "Graph agent routed to the wrong node"

For graph agents, look for `component: "routing"` + `type: "response"` entries. They contain the routing decision: which target was picked, the confidence, and the reasoning. See `bolna-graph-agents/references/debugging.md` for the routing-log format.

### "Webhook fired but execution data was empty"

Webhooks fire on every status transition. Filter on `status: "completed"` in your receiver — that's the final state after post-processing finishes. Earlier webhooks (`queued`, `initiated`, `in-progress`) won't have `extracted_data` or final transcripts yet.

## Reasoning content

When the LLM exposes it (GPT-5 class, Claude with extended thinking):

```json
{
  "component": "llm",
  "type": "response",
  "data": "I'm transferring you to sales right away.",
  "reasoning_content": "The user asked about pricing and demos. That maps to the sales transfer trigger. I should call transfer_to_sales with the call_sid."
}
```

`reasoning_content` is the single most useful field for debugging wrong-tool, wrong-transition, and wrong-answer bugs. Look at it before assuming the LLM is "just wrong."

## Filtering tips

- **Find every tool call**: `jq '.data[] | select(.component == "tool")'`
- **Find LLM responses with reasoning**: `jq '.data[] | select(.component == "llm" and .type == "response" and has("reasoning_content"))'`
- **Find every routing decision (graph agents)**: `jq '.data[] | select(.component == "routing")'`
- **Find errors**: `jq '.data[] | select(.type == "error" or (.data | tostring | contains("error")))'`

## Latency view

For latency-specific debugging, prefer the structured `latency_data` field on `GET /executions/{id}` — it's already aggregated per pipeline component. Use raw logs to understand *what was said* and *why*, not for timing math (the timestamps are wall-clock and include scheduling jitter).

## Privacy

Raw logs contain the full conversation, all tool payloads, and any context variables. Treat them as sensitive — they often contain PII (phone numbers, names, emails, OTPs). Don't share log dumps in public channels.

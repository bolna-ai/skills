---
name: bolna-graph-agents
description: "Design Bolna graph agents: node-based voice flows with LLM, expression, unconditional and event edges, static low-latency nodes, silence repeat with escalation, per-node RAG, function tools, and real-time event injection via REST. Use when a single prompt is too fragile for a multi-step voice workflow — appointment booking, lead qualification, collections, IVR with LLM fallback, payment confirmation, or any flow with branches, compliance checkpoints, or external events."
license: MIT
compatibility: Requires internet, a Bolna API key (BOLNA_API_KEY), and Bolna graph-agent access on the account (currently beta).
metadata:
  openclaw:
    requires:
      env:
        - BOLNA_API_KEY
    primaryEnv: BOLNA_API_KEY
---

# Bolna Graph Agents

Build structured, multi-step voice conversations as a directed graph of nodes and edges. Each node has one job and one set of transitions. Routing is deterministic where you want it (expression edges, events) and LLM-driven where you need flexibility.

## When to use a graph agent

| Use graph agent | Use `simple_llm_agent` |
|---|---|
| Distinct stages with different objectives (greet → qualify → collect → confirm → close) | A single objective like answering FAQ |
| Deterministic branches (working hours, retry counts, language) | Free-flowing chat where any topic might come up |
| External events drive the conversation (payment confirmed, link clicked) | Pure speech-driven flow |
| Compliance checkpoints that must not be skipped | Tone-only personality differences |
| High-volume flows where static nodes save latency and LLM cost | Low-volume prototypes |

If you can describe the call as a flowchart on a whiteboard, a graph agent fits. If it's "one persona, many possible topics," stay with a prompt agent.

## Core concepts in one minute

- **Node** — one conversation step. Has its own prompt, can be `"llm"` or `"static"`.
- **Edge** — a transition. Can be LLM-routed, expression-based, unconditional, or event-driven.
- **Routing LLM** — second LLM that decides which LLM edge to take on each user turn. Defaults to `gpt-4.1-mini`.
- **Deterministic-first** — expression, unconditional, and event edges are checked *before* the routing LLM runs. If one matches, the routing LLM never fires (zero latency, zero cost).
- **Static node** — message audio is pre-rendered when the agent is saved and served from cache (~50ms vs ~800ms LLM round-trip, zero cost).
- **Silence repeat** — `repeat_after_silence_seconds` auto-replays a node and increments `_silence_repeats`, so expression edges can escalate.
- **Event injection** — `POST /v1/call/{run_id}/events` pushes a named event into a live call. A matching event edge transitions the graph and triggers proactive speech.
- **Per-node RAG** — `rag_config` on a node retrieves from a vector store only when the conversation is on that node.

## Where the config lives

```
agent_config
  └── tasks[]
        └── tools_config
              └── llm_agent          ← all graph fields go here
                    ├── agent_type: "graph_agent"
                    ├── agent_information
                    ├── routing_instructions
                    ├── current_node_id
                    └── nodes[]
```

### Top-level `llm_agent` fields

| Field | What it is |
|---|---|
| `agent_type` | Must be `"graph_agent"`. |
| `agent_information` | Global system prompt prepended to every node. Persona, language rules, hard guardrails. Keep it tight — it's sent on every LLM call. |
| `routing_instructions` | Prompt for the routing LLM. Supports `{variable}` substitution from `context_data` (missing keys render as `NULL`). |
| `current_node_id` | Starting node. |
| `nodes` | Array of node objects. |
| `model` | Response LLM. Default `gpt-4.1-mini`. |
| `routing_model` | Routing LLM. Default `gpt-4.1-mini`. |
| `routing_max_tokens` | Cap on routing tokens. Default 250 (non-GPT-5), 150 (GPT-5). |
| `routing_reasoning_effort` | GPT-5 only: `minimal` / `low` / `medium` / `high`. |

### Node fields

| Field | Type | Notes |
|---|---|---|
| `id` | string | Referenced by edges and `current_node_id`. |
| `prompt` | string | Required for `"llm"` nodes. What the response LLM does here. |
| `node_type` | `"llm"` (default) or `"static"` | `static` = cached audio, ~50ms, zero cost. |
| `static_message` | string | Required when `node_type == "static"`. |
| `repeat_after_silence_seconds` | number | Auto-replay after N seconds of user silence. Works on both node types. |
| `edges` | array | Possible transitions out. |
| `examples` | object | Sample phrasings per language, e.g. `{ "en": [...], "hi": [...] }`. |
| `function_call` | string | Forces the response LLM's `tool_choice` to this tool when entering the node. Used for transfer nodes. |
| `rag_config` | object | Per-node knowledge base. See deep-dive below. |

### Edge fields

| Field | Notes |
|---|---|
| `to_node_id` | Required. |
| `condition` | Human-readable description; used as the routing LLM's tool description for LLM edges. |
| `condition_type` | `"llm"` (default), `"expression"`, `"unconditional"`, `"event"`. |
| `expression` | Required for `expression` edges. See `references/edges-and-routing.md`. |
| `event_name` | Required for `event` edges. See `references/event-injection.md`. |
| `parameters` | `{name: type}` to extract from user input during transition. Merged into `context_data`. |
| `priority` | Lower fires first. Default `0` for deterministic, `100` for LLM. |
| `function_name`, `function_description` | Override the auto-generated routing tool name and description. |

## Routing order on every user turn

1. **Deterministic edges first** (expression, unconditional, event) — in `priority` order. First match wins, sub-millisecond.
2. **LLM edges** — routing LLM evaluates `condition` strings against the user's reply. Picks the best match or returns `stay_on_current_node`.
3. **No match** — agent stays on current node and re-asks naturally.

The routing LLM **never** fires if a deterministic rule matches. Use expression edges aggressively for anything data-driven (working hours, retry count, language detection) — they're free and instant.

## Worked example: appointment booking (5 nodes)

```json
{
  "agent_type": "graph_agent",
  "agent_information": "You are Tara, an appointment booking assistant for Acme Dental. Speak warmly and concisely. Never quote prices.",
  "routing_instructions": "Pick the edge whose condition best matches the customer's reply. If none match, stay on the current node.",
  "current_node_id": "welcome",
  "model": "gpt-4.1-mini",
  "routing_model": "gpt-4.1-mini",
  "nodes": [
    {
      "id": "welcome",
      "node_type": "static",
      "static_message": "Hi! This is Tara from Acme Dental. Are you calling to book a new appointment or reschedule an existing one?",
      "repeat_after_silence_seconds": 8,
      "edges": [
        { "to_node_id": "collect_slot", "condition": "Customer wants to book a new appointment" },
        { "to_node_id": "lookup_existing", "condition": "Customer wants to reschedule" },
        {
          "to_node_id": "goodbye",
          "condition": "User silent 3 times",
          "condition_type": "expression",
          "expression": { "conditions": [{ "variable": "_silence_repeats", "operator": "gte", "value": 3 }] }
        }
      ]
    },
    {
      "id": "collect_slot",
      "prompt": "Ask for the customer's preferred day and time. Confirm timezone is {recipient_data.timezone}. Once you have day + time, transition.",
      "repeat_after_silence_seconds": 10,
      "edges": [
        {
          "to_node_id": "confirm",
          "condition": "Customer provided day and time",
          "parameters": { "appointment_day": "string", "appointment_time": "string" }
        },
        {
          "to_node_id": "after_hours",
          "condition_type": "expression",
          "condition": "Outside booking window",
          "priority": 0,
          "expression": {
            "logic": "or",
            "conditions": [
              { "variable": "recipient_data.current_hour", "operator": "lt", "value": 9 },
              { "variable": "recipient_data.current_hour", "operator": "gte", "value": 19 }
            ]
          }
        }
      ]
    },
    {
      "id": "confirm",
      "prompt": "Confirm '{appointment_day} at {appointment_time}' with the customer. If they agree, transition to booked. If they want to change, transition back to collect_slot.",
      "edges": [
        { "to_node_id": "booked", "condition": "Customer confirms the slot" },
        { "to_node_id": "collect_slot", "condition": "Customer wants to change the slot" }
      ]
    },
    {
      "id": "booked",
      "node_type": "static",
      "static_message": "All set. You'll get a confirmation SMS shortly. Thanks for choosing Acme Dental!",
      "edges": [{ "to_node_id": "goodbye", "condition_type": "unconditional" }]
    },
    {
      "id": "after_hours",
      "node_type": "static",
      "static_message": "Our booking team is offline right now. I'll have them call you back during business hours. Have a great day!",
      "edges": []
    },
    {
      "id": "goodbye",
      "node_type": "static",
      "static_message": "Thanks for calling Acme Dental. Goodbye!",
      "edges": []
    }
  ]
}
```

Why this works:

- `welcome` is static — first words play in 50ms.
- `collect_slot` extracts both fields with one LLM call via `parameters`.
- `after_hours` is an expression edge — fires before the routing LLM, even if the user technically said a valid time.
- `_silence_repeats` escalates to goodbye after 3 silent rounds, free of LLM cost.
- `booked` and `goodbye` are static — no LLM on the closing legs.

For a more advanced example with payment events and call transfer, see `assets/full-example.json`.

## Event-driven flows in 30 seconds

```json
{
  "id": "awaiting_payment",
  "prompt": "Reassure the user while payment processes. Amount: {currency} {amount}.",
  "edges": [
    { "to_node_id": "confirmation", "condition_type": "event", "event_name": "payment_completed" },
    { "to_node_id": "payment_failed", "condition_type": "event", "event_name": "payment_failed" }
  ]
}
```

Fire from your backend when the payment gateway responds:

```bash
curl -X POST https://api.bolna.ai/v1/call/$RUN_ID/events \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "event": "payment_completed", "properties": { "ref": "TXN-98765" } }'
```

The event's `properties` are merged into `context_data` — they become available as `{ref}` substitutions in any downstream node prompt and as variables in expression edges. `run_id` comes from `POST /call`'s response or the inbound webhook.

For the full timing semantics (mid-utterance, mid-speech, double events), see `references/event-injection.md`.

## Built-in variables

These are populated automatically. Reference them anywhere `{variable}` substitution is supported, including in expression edges:

| Variable | Notes |
|---|---|
| `recipient_data.current_hour` | 0-23. **Only set when `timezone` is on the call.** |
| `recipient_data.current_weekday` | lowercase, `"wednesday"`. |
| `recipient_data.current_day` / `_month` / `_year` / `_minute` | Numeric components. |
| `recipient_data.timezone` | tz database name. |
| `recipient_data.user_number` | E.164 phone. |
| `detected_language` | Top-level. `"hindi"`, `"en"`. |
| `_node_turns` | User messages on the current node. Resets on transition. |
| `_total_turns` | User messages in the entire call. |
| `_silence_repeats` | Silent replays on the current node. Resets on transition. |

> **If time-based expressions never fire, you forgot `timezone` on the call.** This is the #1 graph-agent gotcha.

## Debugging

Every routing decision logs one line:

```
Routing decision (LLM): transition_to_offer_pitch | confidence: 0.95 |
  reasoning: Customer confirmed identity by saying 'yeah'. (latency: 210ms)

Routing decision (deterministic): -> after_hours |
  deterministic:expression:Outside working hours (latency: 0.6ms)
```

The `reasoning` field is the most useful debugging signal — when the agent makes a wrong transition, it almost always explains *why* it made that choice. See `references/debugging.md` for the symptom → fix table.

## Quality checklist before going live

- [ ] Every node has at least one exit edge, OR is an explicit terminal node.
- [ ] Every tool / API failure has a spoken fallback path.
- [ ] Static nodes don't contain dynamic facts unless safely templated.
- [ ] Compliance lines (disclosures, recording notice) can't be skipped by routing.
- [ ] Time-based expression edges only matter if `timezone` is set on the call.
- [ ] Event edges have a non-event fallback (timeout via `_node_turns` or `_silence_repeats`).
- [ ] Outcomes map to a disposition or `context_data` field for analytics.

## Going deeper

| File | What's in it |
|---|---|
| `references/edges-and-routing.md` | Expression operators, inline extraction, priority semantics. |
| `references/static-and-silence.md` | Pre-rendered audio, silence escalation patterns. |
| `references/event-injection.md` | REST endpoint, timing, concurrency, `properties` merging. |
| `references/debugging.md` | Routing logs, common misbehaviour, root causes. |
| `assets/full-example.json` | Annotated config with every feature wired together. |
| `scripts/create_graph_agent.py` | Creates the appointment-booking agent above via `POST /v2/agent`. |
| `scripts/inject_event.py` | Fires an event into a live call. |

## See also

- `create-agent` — top-level agent shape, `tools_config`, telephony/STT/TTS.
- `setup-tools` — defining `transfer_call`, custom HTTP tools.
- `create-knowledgebase` — generating the `vector_id` used by `rag_config`.
- `create-disposition` — pulling structured outcomes out of graph-agent calls.
- `../references/prompting-tips.md` — node-prompt patterns and multilingual.

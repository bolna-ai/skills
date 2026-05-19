---
name: setup-tools
description: "Add function tools to Bolna voice agents so they can take real-world action during a live call: transfer to a human, fetch/post data via any HTTP API, fetch and book Cal.com slots, look up current time, or capture DTMF keypad input. Uses the OpenAI function-calling schema with Bolna extensions (`key: \"custom_task\"`, `value` API config, `pre_call_message`). Use when the agent must do more than speak — escalate, retrieve, book, log, verify, or trigger a workflow."
license: MIT
compatibility: Requires internet access and a Bolna API key (BOLNA_API_KEY).
metadata:
  openclaw:
    requires:
      env:
        - BOLNA_API_KEY
    primaryEnv: BOLNA_API_KEY
---

# Bolna Function Tools

Tools turn a talking agent into a useful one. The LLM picks a tool based on `description`, collects parameters from the conversation, and Bolna fires the HTTP request — feeding the response back into the conversation.

## When to add a tool

| Goal | Tool |
|---|---|
| Hand the caller to a human | `transfer_call` (built-in) |
| Look up order / customer / account data | Custom HTTP `GET` |
| Create a ticket / lead / booking in CRM | Custom HTTP `POST` |
| Show calendar availability | `fetch_calendar_slots` (Cal.com) |
| Book a calendar slot | `book_calendar_slot` (Cal.com) |
| Get current time anywhere | Custom HTTP `GET` to WorldTimeAPI |
| Capture PIN / OTP / phone number on keypad | DTMF (`dtmf_enabled: true`) |

## Where tools live in the agent config

```
agent_config
  └── tasks[]
        └── tools_config
              └── api_tools
                    ├── tools[]          ← function schemas (OpenAI-style + Bolna extensions)
                    └── tools_params     ← per-tool API config (method, url, headers, param mapping)
```

Reference a tool from prompts with `@function_name` so the LLM knows when to use it. For graph agents, `function_call: "<tool_name>"` on a node forces the LLM's `tool_choice`.

## The schema in one minute

```json
{
  "name": "check_order_status",
  "description": "Use this function when the customer asks about their order status, delivery update, shipping progress, or tracking. The customer must provide their order ID.",
  "pre_call_message": "Let me check the status of your order.",
  "parameters": {
    "type": "object",
    "properties": {
      "order_id": {
        "type": "string",
        "description": "The customer's order ID. Usually starts with ORD- followed by numbers, e.g., ORD-78234."
      }
    },
    "required": ["order_id"]
  },
  "key": "custom_task",
  "value": {
    "method": "GET",
    "param": { "order_id": "%(order_id)s" },
    "url": "https://api.yourstore.com/orders",
    "api_token": "Bearer sk_live_abc123",
    "headers": {}
  }
}
```

Two halves:

- **Function definition** (`name`, `description`, `parameters`) — follows the [OpenAI function calling](https://platform.openai.com/docs/guides/function-calling) spec. The LLM uses this to decide *when* to call and *what* to extract.
- **Bolna extensions** (`pre_call_message`, `key`, `value`) — tells Bolna *how* to execute the API call.

> **`key` must be exactly `"custom_task"`.** Don't change it.

## The non-negotiable rules

1. **The description is everything.** The LLM reads it to decide whether to invoke the tool. Include synonyms ("status, shipping, delivery, tracking"), required preconditions ("only after the caller provides their order ID"), and exclusions ("not for billing questions — use `lookup_invoice` instead").
2. **Mark parameters `required` only if the call can't proceed without them.** The LLM will keep asking until required fields are filled — annoying when the data isn't strictly necessary.
3. **Always add `pre_call_message`** when the API takes more than ~500ms. "One moment please..." is much better than dead air.
4. **Match parameter names exactly** between `parameters.properties` and `value.param`. Case-sensitive.
5. **Use format specifiers** in `value.param`: `%(name)s` for string, `%(name)i` for int, `%(name)f` for float. Strings work for almost everything — only use `%i`/`%f` when the API needs a typed JSON value.
6. **Trust auto-injected context variables.** `{from_number}`, `{to_number}`, `{call_sid}`, `{agent_id}` and any `user_data` keys get substituted automatically — don't make the LLM ask the caller for data you already have.

## Quick examples

### Transfer to a human

The built-in `transfer_call` tool. Config differs slightly from custom functions — it's wired into Bolna's telephony layer:

```json
{
  "tools": [
    {
      "key": "transfer_call",
      "name": "transfer_to_sales",
      "description": "Transfer when the caller asks about pricing, demos, or purchasing, or explicitly asks to speak to sales.",
      "parameters": {
        "type": "object",
        "required": ["call_sid"],
        "properties": {
          "call_sid": { "type": "string", "description": "Unique call id" }
        }
      },
      "pre_call_message": "Sure, transferring you to sales — please hold a moment."
    }
  ],
  "tools_params": {
    "transfer_to_sales": {
      "url": null,
      "param": {
        "call_sid": "%(call_sid)s",
        "call_transfer_number": "+919876543210"
      },
      "method": "POST",
      "headers": {}
    }
  }
}
```

Add a separate tool per destination (`transfer_to_sales`, `transfer_to_support`, `transfer_to_billing`) — gives the LLM a sharper choice than one tool with a "which team" parameter.

### Cal.com — check availability, then book

Two tools, used in sequence. The LLM is good at chaining them — first show options, then confirm, then book.

```json
{
  "tools": [
    {
      "key": "calendar_slot_availability",
      "name": "fetch_calendar_slots",
      "description": "Fetch open Cal.com slots after the caller asks about scheduling a meeting or demo. Use the caller's preferred date if provided; otherwise use the next 3 business days.",
      "pre_call_message": "Just a moment, let me check our availability.",
      "parameters": {
        "type": "object",
        "properties": {
          "preferred_date": {
            "type": "string",
            "description": "Preferred date in YYYY-MM-DD format. Optional."
          }
        }
      }
    },
    {
      "key": "calendar_book",
      "name": "book_calendar_slot",
      "description": "Book a Cal.com slot ONLY after the caller has confirmed a specific time. Collect their full name and email first.",
      "pre_call_message": "Booking that for you now.",
      "parameters": {
        "type": "object",
        "properties": {
          "slot": { "type": "string", "description": "ISO 8601 slot start time, e.g. 2026-05-22T14:00:00+05:30" },
          "name": { "type": "string", "description": "Caller's full name" },
          "email": { "type": "string", "description": "Caller's email for the calendar invite" }
        },
        "required": ["slot", "name", "email"]
      }
    }
  ]
}
```

Cal.com API key, event ID, and timezone are configured per-tool in the dashboard once. Bolna handles the HTTP calls automatically — you don't need to write `url`/`api_token` for built-in Cal.com tools.

### Custom HTTP POST — create a support ticket

```json
{
  "name": "create_support_ticket",
  "description": "Use when the customer reports a problem, complaint, issue, or bug. Create a ticket with category, summary, and priority. Phone number is auto-injected.",
  "pre_call_message": "I'm creating a support ticket for this right away.",
  "parameters": {
    "type": "object",
    "properties": {
      "caller_phone":    { "type": "string", "description": "Auto-injected from {from_number}" },
      "issue_category":  { "type": "string", "description": "billing, technical, account, shipping, or other" },
      "description":     { "type": "string", "description": "1-2 sentence summary of the issue" },
      "priority":        { "type": "string", "description": "low, medium, or high. Set high if the customer is upset or the issue is time-sensitive." }
    },
    "required": ["caller_phone", "issue_category", "description"]
  },
  "key": "custom_task",
  "value": {
    "method": "POST",
    "param": {
      "caller_phone":   "%(caller_phone)s",
      "issue_category": "%(issue_category)s",
      "description":    "%(description)s",
      "priority":       "%(priority)s"
    },
    "url": "https://api.yourhelpdesk.com/tickets",
    "api_token": "Bearer helpdesk_key_789",
    "headers": { "Content-Type": "application/json" }
  }
}
```

To skip asking the caller for their phone, add `{from_number}` to the agent prompt and the LLM auto-fills `caller_phone`.

## DTMF (keypad input)

For numeric input the caller would rather type than speak (OTP, account number, PIN). Enable on `task_config`:

```json
{ "task_config": { "dtmf_enabled": true } }
```

| Telephony | Supported? |
|---|---|
| Plivo | Yes |
| Twilio | Yes |
| Exotel / Vobiz / SIP BYOT | No |

In the prompt, tell the caller to press `#` after their digits and tell the agent what the input means:

```
When you need the caller's phone number, say:
"Please enter your phone number on your keypad and press the hash key when done."

When you receive a message starting with "dtmf_number:", the digits that follow are
what the caller pressed. Read them back to confirm and proceed.
```

What the agent receives:

```
dtmf_number: 9876543210
```

The agent treats this like any other turn — it can confirm, pass to a tool, or branch.

For IVR-style **menu routing** ("press 1 for sales, 2 for support"), use Bolna's IVR feature instead — it doesn't burn LLM tokens on every menu turn. DTMF here is for *content* (a phone number, an OTP), not navigation.

## Going deeper

| File | What's in it |
|---|---|
| `references/tool-schemas.md` | Full schema reference: every field, every type, format specifiers, auto-injection, common failure modes. |
| `references/transfer-call.md` | Multi-destination patterns, post-transfer handling, failure fallbacks. |
| `references/cal-com.md` | Fetch + book end-to-end with worked prompts and example transcripts. |
| `references/dtmf.md` | DTMF prompt patterns, telephony support, fallback to speech. |
| `references/world-time.md` | WorldTimeAPI custom tool — no auth, useful template. |

## Debugging

| Symptom | Likely cause | Fix |
|---|---|---|
| Tool never called | `description` too vague or doesn't match the caller's vocabulary | Rewrite with synonyms ("status, tracking, shipping, delivery") and explicit trigger phrases |
| Tool called too eagerly | `description` too broad, overlaps with other tools | Tighten the "only when…" preconditions |
| Tool payload missing fields | Param names mismatched between `properties` and `param` | Make them byte-identical, including case |
| API returns 4xx | Wrong URL / auth / headers | Test the request with `curl` first; verify `api_token` format includes `Bearer ` |
| Variable not substituted | Variable not in agent prompt | Add `{variable_name}` to the prompt so it's in scope |
| Agent stalls during API call | Slow backend with no `pre_call_message` | Add a friendly "one moment please" message |
| Tool returns success but agent ignores result | No instruction in prompt on what to do with the result | Add: "After calling X, summarise the result and ask if they want anything else." |

## See also

- `create-agent` — where `tools_config.api_tools` slots into the agent config.
- `bolna-graph-agents` — using tools with `function_call` on a node for graph flows.
- `../references/prompting-tips.md` — when to ask the caller vs use auto-injected variables.
- `get-executions` — inspect raw logs to see exactly what the tool received and returned.

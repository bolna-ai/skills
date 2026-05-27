# Cal.com Integration

Two built-in tools: **Check Calendar Slots** (fetch availability) and **Book Calendar Slots** (create the booking). Use both — first show options, then confirm, then book. Don't try to book without a prior availability check, or the LLM will guess slot times.

## Prerequisites

1. Cal.com account with API access enabled.
2. Cal.com API key from `https://app.cal.com/settings/developer/api-keys`.
3. At least one event type (15 min meeting, 30 min demo, etc.) on your Cal.com account.

## Dashboard setup (fastest path)

For both tools:

1. Open the agent's **Tools Tab**.
2. Click **Select functions** → pick **"Check slot availability (using Cal.com)"** and **"Book appointment (using Cal.com)"**.
3. Paste your Cal.com API key. Event types load once validated.
4. Pick the event type per tool.
5. Set the timezone — must match the event's timezone in Cal.com.
6. Write a description focused on *when* to trigger.
7. Add a `pre_call_message`.

Bolna handles the Cal.com HTTP calls for you — no `url`/`api_token` to manage.

## Schema shape (when scripting the agent config)

### Fetch slots

```json
{
  "key": "calendar_slot_availability",
  "name": "fetch_calendar_slots",
  "description": "Fetch open Cal.com slots when the caller asks to schedule a meeting, demo, or consultation. Use their preferred date if provided; otherwise the next 3 business days.",
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
}
```

### Book a slot

```json
{
  "key": "calendar_book",
  "name": "book_calendar_slot",
  "description": "Book a Cal.com slot ONLY after the caller confirms a specific time. Collect name and email first.",
  "pre_call_message": "Booking that for you now.",
  "parameters": {
    "type": "object",
    "properties": {
      "slot":  { "type": "string", "description": "ISO 8601 slot start time, e.g. 2026-05-22T14:00:00+05:30" },
      "name":  { "type": "string", "description": "Caller's full name" },
      "email": { "type": "string", "description": "Caller's email — for the calendar invite" }
    },
    "required": ["slot", "name", "email"]
  }
}
```

## Prompt instructions

Tools alone aren't enough — the agent needs procedural instructions in the system prompt:

```
APPOINTMENT FLOW:
1. When the caller wants to schedule, ask for their preferred day.
2. Call @fetch_calendar_slots with the preferred date.
3. Read back exactly 2-3 available slots (don't list more — voice doesn't scale).
4. Wait for the caller to pick one. Confirm the picked slot explicitly.
5. Before booking, collect: full name and email address.
6. Call @book_calendar_slot with slot, name, email.
7. Confirm the booking and the calendar invite they'll receive.
```

## Conversation example

```
Caller:  "Hi, I'd like to schedule a 30-minute demo."
Agent:   "Of course! What day works best for you?"
Caller:  "How about Thursday?"
Agent:   "Let me check our availability."   [fetch_calendar_slots(preferred_date="2026-05-22")]
Agent:   "On Thursday I have 10 AM, 2 PM, or 4:30 PM. Which works for you?"
Caller:  "Let's do 2 PM."
Agent:   "Great, 2 PM Thursday. To confirm — what's your full name?"
Caller:  "Priya Sharma."
Agent:   "And the best email for the calendar invite?"
Caller:  "priya@example.com."
Agent:   "Booking that now."   [book_calendar_slot(slot=..., name=..., email=...)]
Agent:   "All set! You're booked for Thursday at 2 PM. The invite is on its way."
```

## Best practices

| Do | Don't |
|---|---|
| Check slots first, then book | Skip availability and let the LLM guess a time |
| Read 2-3 slots aloud max | Read a list of 8 slots — callers tune out |
| Make the agent confirm the slot explicitly before booking | Book on the first time mentioned |
| Use matching Bolna and Cal.com timezones | Have the agent in IST and the event in PT |
| Collect name + email before booking | Book and then say "what was your email?" — Cal.com fails the booking |

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Times spoken back are wrong | Timezone mismatch | Align Bolna config and Cal.com event timezones |
| `fetch_calendar_slots` returns nothing | Event type is paused / no availability window configured | Check the event in Cal.com |
| Booking succeeds in Cal.com but agent says it failed | Slow Cal.com response, tool timed out | Add a longer `pre_call_message`, verify in `get-executions` raw logs |
| Caller never gets the invite | Email mistyped in voice | Add a confirmation step: "Let me read back the email — p-r-i-y-a..." |

## Multilingual

Pre-tool messages support multiple languages (configure via the **+ Add** button in the Cal.com config UI). Useful when the agent might be speaking Hindi or another language at the moment the tool fires.

## See also

- `setup-tools/references/tool-schemas.md` — for the underlying custom-function schema.
- `bolna-graph-agents` — for using Cal.com tools inside a graph-agent node.
- `prompt-writing` — for crafting the procedural appointment flow.

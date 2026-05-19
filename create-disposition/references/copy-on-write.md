# Copy-on-Write for Shared Dispositions

Dispositions can be linked to multiple agents. If you edit one of them via *Agent A*, you probably want the change to apply only to *Agent A* — not to silently mutate behaviour for every other agent that shares the disposition. Bolna handles this with copy-on-write semantics on scoped updates.

## The two update modes

### Scoped update (recommended)

You're updating a disposition *for a specific agent*. Pass `agent_id` in the request.

```bash
curl --request PUT "https://api.bolna.ai/dispositions/$DISPOSITION_ID" \
  --header "Authorization: Bearer $BOLNA_API_KEY" \
  --header "Content-Type: application/json" \
  --data '{
    "agent_id": "'$AGENT_ID'",
    "question": "Was the customer interested AND did they confirm a follow-up time?",
    "objective_options": [
      { "value": "interested_confirmed", "condition": "Confirmed a follow-up date and time" },
      { "value": "interested_no_date",   "condition": "Said yes but no confirmed time" },
      { "value": "not_interested",       "condition": "Declined" }
    ]
  }'
```

Two outcomes:

| Disposition state | Server behaviour | HTTP status |
|---|---|---|
| Exclusive to *this* agent (no other agent links to it) | Edits in place. ID unchanged. | `200 OK` |
| Shared with other agents | Creates a private copy for this agent, re-links the agent to the copy, leaves the original disposition untouched for everyone else. | `201 Created` |

The `201` response body contains the **new disposition ID**. If your application stores disposition IDs (CRM mapping, dashboards, reports), update your reference to the new ID.

### Unscoped update

No `agent_id` is passed. Edits affect the disposition itself everywhere it's linked.

- **Admins** can update any disposition.
- **Non-admins** can only update dispositions they own (`created_by` matches their user).

Use unscoped when you intentionally want the change to propagate to all linked agents.

## Worked walkthrough

### Setup

You have three agents, all linked to a shared `Call Outcome` disposition:

```
Disposition: Call Outcome (id = D1)
  linked to: Agent A, Agent B, Agent C
```

### Scoped edit for Agent A

```
PUT /dispositions/D1
{ "agent_id": "A", "question": "...new question..." }
```

Behaviour:

1. Server sees D1 is linked to A, B, and C → not exclusive to A.
2. Creates a copy: `Call Outcome (id = D2)` with the new question.
3. Unlinks Agent A from D1, links Agent A to D2.
4. Returns `201 Created` with the new disposition payload (id = D2).

Resulting graph:

```
Disposition: Call Outcome (id = D1, unchanged)
  linked to: Agent B, Agent C

Disposition: Call Outcome (id = D2, edited)
  linked to: Agent A
```

Agents B and C are unaffected — exactly what you want.

### Scoped edit for Agent A (already exclusive)

If you do a second edit for Agent A:

```
PUT /dispositions/D2
{ "agent_id": "A", "question": "...another change..." }
```

D2 is exclusive to A → edited in place → `200 OK`, id stays D2.

## Code pattern

Your update logic should handle both 200 and 201 responses:

```python
import os, requests

def update_disposition_scoped(disposition_id: str, agent_id: str, fields: dict) -> str:
    url = f"https://api.bolna.ai/dispositions/{disposition_id}"
    body = {"agent_id": agent_id, **fields}
    resp = requests.put(
        url,
        headers={"Authorization": f"Bearer {os.environ['BOLNA_API_KEY']}"},
        json=body,
        timeout=30,
    )
    resp.raise_for_status()

    if resp.status_code == 201:
        new_id = resp.json()["id"]
        # Persist the new ID locally so future updates target the right copy
        return new_id
    return disposition_id  # 200 — id unchanged
```

## When to *avoid* copy-on-write

If you maintain a small set of "canonical" dispositions across all agents (compliance, sentiment, NPS), edit them **unscoped**. Otherwise each agent ends up with its own divergent copy and the canonical version stops being a single source of truth.

| Goal | Update mode |
|---|---|
| Customise one agent without affecting others | Scoped |
| Roll out a fleet-wide policy change | Unscoped (admin) |
| Tweak language only your team's agent uses | Scoped |

## Deletion

```
DELETE /dispositions/{disposition_id}
```

- Regular users can only delete dispositions they own.
- Admins can delete any disposition.
- Historical execution data (`extracted_data` in past executions) is **not** affected — only future calls stop evaluating the disposition.

## Common confusions

- **`agent_ids` (array) vs `agent_id` (single scope)**: `agent_ids` in the disposition body lists everyone linked. `agent_id` in an update request body or query specifies the scope of *this* update.
- **`201` doesn't mean the original was edited.** It means a copy was created. The original is still there, still linked to all other agents.
- **`200` after a previous `201` is normal.** Once the agent owns its private copy, further scoped edits stay in place.
- **Deletion of a copy doesn't affect the original.** The copy is its own disposition with its own id.

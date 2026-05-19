# Caller Identification (`ingest_source_config`)

When a call arrives, Bolna can look the caller up in your data source and inject their details into the agent's prompt before the conversation starts. Three flavours; pick whichever fits your stack.

`ingest_source_config` lives on the **agent**, not on the inbound mapping. Configure it once per agent, then map any inbound number to that agent.

## Internal API

Best for teams with an existing CRM, customer database, or auth service. Fully dynamic — every call hits your endpoint.

### How it works

Bolna sends a **GET** request to your endpoint with these query params:

| Param | Notes |
|---|---|
| `contact_number` | E.164 caller phone, e.g. `+19876543210`. |
| `agent_id` | UUID of the agent answering. |
| `execution_id` | UUID for this specific call. |

Auth: **Bearer token** (one configured per agent).

Example:

```
GET https://api.your-domain.com/customers
    ?contact_number=%2B19876543210
    &agent_id=06f64cb2-...
    &execution_id=c4be1d0b-...
Authorization: Bearer your_internal_token
```

### Response shape

Return JSON. Every key becomes a prompt variable:

```json
{
  "first_name": "Priya",
  "last_name": "Sharma",
  "plan": "Enterprise",
  "last_contacted_at": "2026-05-12",
  "account_status": "active"
}
```

In the agent prompt:

```
You are speaking with {first_name} {last_name}, on the {plan} plan.
They were last contacted on {last_contacted_at}.
```

If the caller isn't found:

- Return `404` or an empty JSON object `{}`.
- If `disallow_unknown_numbers: true` is set on the agent, Bolna rejects the call. Otherwise the prompt gets `NULL`-substituted variables and the agent should be written to handle the missing-data case gracefully.

### Endpoint requirements

- **GET** method only (no POST).
- HTTPS (HTTP fine for local dev, not production).
- Latency < 1 second — Bolna doesn't wait long before falling back to no data.
- Returns 200 with JSON, or 404 / empty for unknown callers.
- Bearer token auth (no API key headers, no OAuth flow).

### Worked example handler (FastAPI)

```python
from fastapi import FastAPI, HTTPException, Header

app = FastAPI()
TOKEN = "your_internal_token"

@app.get("/customers")
def lookup(
    contact_number: str,
    agent_id: str,
    execution_id: str,
    authorization: str = Header(...),
):
    if authorization != f"Bearer {TOKEN}":
        raise HTTPException(403, "Forbidden")
    customer = my_crm.find_by_phone(contact_number)
    if not customer:
        raise HTTPException(404, "Not found")
    return {
        "first_name": customer.first_name,
        "last_name":  customer.last_name,
        "plan":       customer.plan,
        "last_contacted_at": customer.last_contacted_at.isoformat(),
    }
```

## CSV upload

Best for small teams, low volume, or fixed prospect lists.

Upload a CSV via the dashboard with a `contact_number` column. All other columns become prompt variables.

```csv
contact_number,first_name,last_name,plan
+11231237890,Bruce,Wayne,Enterprise
+91012345678,Bruce,Lee,Pro
+44999999007,James,Bond,Starter
```

Pros: zero code, fast.
Cons: static. You re-upload whenever data changes.

## Google Sheet

Real-time sync without writing an endpoint.

1. Create a sheet with a `contact_number` column (with country code).
2. Make it **publicly accessible** ("Anyone with the link can view").
3. Paste the URL into Bolna's caller-identification config.

```
contact_number  | first_name | last_name | plan
+11231237890    | Bruce      | Wayne     | Enterprise
+91012345678    | Bruce      | Lee       | Pro
```

Bolna fetches the latest sheet contents on every inbound call.

> Public Google Sheets are visible to anyone with the URL. Don't put sensitive PII (account numbers, health records) in a public sheet — use the API source instead.

## Which to pick

| Choose | If |
|---|---|
| **Internal API** | CRM is the source of truth and you need real-time data |
| **CSV** | Fixed list, < 10k contacts, occasional updates |
| **Google Sheet** | Ops team manages the list in a sheet anyway, no engineering |

## Combining with spam controls

Once `ingest_source_config` is set, you can layer:

- `disallow_unknown_numbers: true` — reject anyone not in the source.
- `whitelist_phone_numbers: [...]` — always allow specific numbers regardless.
- `inbound_limit: N` — per-number daily cap.

```json
{
  "task_config": {
    "disallow_unknown_numbers": true,
    "whitelist_phone_numbers": ["+919876543210"],
    "inbound_limit": 3
  }
}
```

This combo gives you a closed-loop inbound system: only known customers get through, plus a hardcoded list of internal numbers (your team's mobiles for testing), capped at 3 calls per number per day.

## Debugging

| Symptom | Likely cause |
|---|---|
| `recipient_data` empty in prompt | API timeout, wrong path, auth header missing, contact_number format mismatch |
| Variables render as `NULL` in prompt | Source returned `{}` or `404`; agent fell through to no-data branch |
| Every caller rejected | `disallow_unknown_numbers: true` but source isn't returning matches |
| API endpoint hit but caller's data missing | Caller's phone number normalised differently than your DB stores it — match on E.164, not local format |
| CSV upload "succeeded" but agent still says "Hello, customer" | Re-save the agent after upload; the variable wiring is read at save time |

For unauth'd debugging: log incoming requests at your endpoint and look for the exact `contact_number` Bolna passes. Make sure your lookup handles `+`-prefixed E.164 (Bolna always sends `+`).

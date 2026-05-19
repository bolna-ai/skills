# IVR Configuration Deep-Dive

IVR (Interactive Voice Response) lets callers navigate menus or enter data on their keypad before reaching the Voice AI agent. **Plivo only** as of now.

## Where it goes

Inside the `ivr_config` block on `POST /inbound/setup`:

```json
{
  "agent_id": "...",
  "phone_number_id": "...",
  "ivr_config": {
    "enabled": true,
    "voice": "Polly.Aditi",
    "welcome_message": "Welcome to Acme.",
    "steps": [ ... ]
  }
}
```

## Top-level fields

| Field | Type | Default | Notes |
|---|---|---|---|
| `enabled` | bool | `false` | Master switch. Send `{"enabled": false}` to disable IVR without removing the mapping. |
| `voice` | string | `Polly.Joanna` | Polly voice for IVR prompts. Switch to `Polly.Aditi` for Hindi/Indian English, `Polly.Matthew` for US male, `Polly.Amy` for UK female, `Polly.Raveena` for Indian English (alt). |
| `welcome_message` | string | — | Spoken once when the call connects, before any step. |
| `timeout` | int (sec) | `5` | How long to wait for caller input on a step. |
| `max_retries` | int | `2` | Retries on invalid input per step. |
| `invalid_input_message` | string | `"Invalid input. Please try again."` | On wrong key press. |
| `no_input_message` | string | `"No input received. Goodbye."` | On timeout. |
| `steps[]` | array | required | Ordered IVR steps. |
| `default_agent_id` | string | — | Fallback agent when no option-level `agent_id` is set. |

## Step types

### `menu` — present options, route on digit

```json
{
  "step_id": "department",
  "type": "menu",
  "prompt": "Press 1 for Sales. Press 2 for Support. Press 3 for Billing.",
  "field_name": "department",
  "options": [
    { "digit": "1", "label": "Sales",   "agent_id": "sales-agent-uuid" },
    { "digit": "2", "label": "Support", "agent_id": "support-agent-uuid" },
    { "digit": "3", "label": "Billing", "agent_id": "billing-agent-uuid" }
  ]
}
```

| Option field | Required | Notes |
|---|---|---|
| `digit` | Yes | The keypad key: `"1"`, `"2"`, ..., `"#"`, `"*"`. |
| `label` | Yes | Stored in `recipient_data[<field_name>]`. |
| `agent_id` | No | Route to a specific agent when this option is picked. |
| `context_label` | No | Extra context passed to the agent. Stored as `recipient_data[<field_name>_context]`. |

### `collect` — capture multi-digit input

```json
{
  "step_id": "account",
  "type": "collect",
  "prompt": "Enter your 6-digit account number.",
  "field_name": "account_number",
  "num_digits": 6,
  "next_step": "pin_step"
}
```

| Field | Notes |
|---|---|
| `num_digits` | Exact length required. |
| `min_digits` / `max_digits` | If `num_digits` isn't set, use these for variable-length input. |
| `finish_on_key` | Default `#`. Pressing this terminates collection early. |

## Step navigation

| Field | Behaviour |
|---|---|
| `next_step` | Linear: go to this step after current finishes. |
| `conditional_next` | Branch by digit: `{"1": "menu_en", "2": "menu_hi"}`. |
| Neither | End of IVR → route to the selected `agent_id` (or `default_agent_id`). |

`conditional_next` is what gives IVR its tree structure. Combine with `next_step` for sequential collection:

```
language menu
  ├── digit 1 → menu_en
  └── digit 2 → menu_hi

menu_en
  ├── digit 1 → sales-agent (English)
  └── digit 2 → support-agent (English)

menu_hi
  ├── digit 1 → sales-agent (Hindi)
  └── digit 2 → support-agent (Hindi)
```

## What the agent sees afterwards

All `field_name` keys from IVR steps land in `recipient_data`:

```json
{
  "department": "Sales",
  "department_context": "sales_inquiry",
  "account_number": "123456",
  "language": "Hindi",
  "ivr_completed_at": "2026-05-19T10:30:00Z"
}
```

Reference in agent prompts:

```
Customer selected {department}. Account number: {account_number}.
Speak in {language}.
```

## Patterns

### Department routing (one menu)

```json
{
  "ivr_config": {
    "enabled": true,
    "voice": "Polly.Aditi",
    "welcome_message": "Welcome to Acme Corp.",
    "steps": [
      {
        "step_id": "department",
        "type": "menu",
        "prompt": "Press 1 for Sales. Press 2 for Support. Press 3 for Billing.",
        "field_name": "department",
        "options": [
          { "digit": "1", "label": "Sales",   "agent_id": "sales-agent-uuid" },
          { "digit": "2", "label": "Support", "agent_id": "support-agent-uuid" },
          { "digit": "3", "label": "Billing", "agent_id": "billing-agent-uuid" }
        ]
      }
    ]
  }
}
```

### Language + department (branching)

See `assets/ivr_multilingual.json`.

### Account + PIN verification (chained collect)

See `assets/ivr_account_verification.json`.

## Limitations

- **Plivo only.** Twilio, Vobiz, Exotel, SIP trunk numbers can't use IVR via Bolna. Route those through DTMF inside the agent instead (`setup-tools/references/dtmf.md`).
- **No "*" or "#" as a route**. The IVR routes on numeric digits only; `*` and `#` are commonly used for `finish_on_key` in `collect` steps.
- **No nested submenus deeper than ~3 levels**. Callers drop off after 2 menu prompts in practice.

## Voices

| Voice | Language |
|---|---|
| `Polly.Aditi` | Hindi + Indian English |
| `Polly.Raveena` | Indian English |
| `Polly.Joanna` | US English (Female) |
| `Polly.Matthew` | US English (Male) |
| `Polly.Amy` | British English (Female) |

The IVR voice is independent of the agent's TTS voice — IVR is rendered via AWS Polly through the telephony layer, the agent uses whatever TTS provider you've configured.

## Disabling IVR

```bash
curl -X POST https://api.bolna.ai/inbound/setup \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "your-agent-id",
    "phone_number_id": "your-phone-number-id",
    "ivr_config": { "enabled": false }
  }'
```

The phone number stays mapped to the agent; the IVR menu just stops appearing.

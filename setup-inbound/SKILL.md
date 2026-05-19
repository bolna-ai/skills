---
name: setup-inbound
description: "Wire a Bolna voice agent to answer inbound calls on a specific phone number. Covers the `POST /inbound/setup` mapping, IVR menus and digit-collect steps (Plivo-only), caller identification via `ingest_source_config` (Internal API / CSV / Google Sheet), inbound spam controls (`inbound_limit`, `whitelist_phone_numbers`, `disallow_unknown_numbers`), and auto-switch multilingual system messages (hangup, user-online check, tool wait). Use when building a support line, front-desk agent, IVR router, or multi-agent department setup."
license: MIT
compatibility: Requires internet access and a Bolna API key (BOLNA_API_KEY).
metadata:
  openclaw:
    requires:
      env:
        - BOLNA_API_KEY
    primaryEnv: BOLNA_API_KEY
---

# Bolna Inbound Calls

Inbound = map a phone number to an agent so calls to that number are answered automatically. Optionally layer IVR menus, caller identification, spam controls, and multilingual switching on top.

## Two endpoints — that's it

| Endpoint | Purpose |
|---|---|
| `POST /inbound/setup` | Map a phone number to an agent (with optional IVR config) |
| `POST /inbound/unlink` | Unmap |

Both: `Authorization: Bearer $BOLNA_API_KEY`, `Content-Type: application/json`.

## Where `phone_number_id` comes from

| Number source | How to get the ID |
|---|---|
| Bolna-hosted (purchased on dashboard) | `GET /phone-numbers/all` — see `manage-phone-numbers` |
| Connected provider (your Twilio, Plivo, Vobiz, Exotel) | Returned when you list phone numbers after connecting the provider |
| Your own SIP trunk (BYOT) | Returned from `POST /sip-trunks/trunks/{id}/numbers` — see `setup-sip-trunk` |

Whatever the source, the mapping flow is identical.

## Basic mapping

```bash
curl -X POST https://api.bolna.ai/inbound/setup \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
    "phone_number_id": "123e4567-e89b-12d3-a456-426614174000"
  }'
```

Response:

```json
{
  "url": "https://api.bolna.ai/inbound_call?agent_id=...&user_id=...",
  "phone_number": "+19876543210",
  "id": "3c90c3cc0d444b5088888dd25736052a"
}
```

That's the whole basic setup. Now any call to `+19876543210` is answered by the agent.

**One number, one agent.** Re-mapping a number to a different agent silently unmaps the previous link. To detach without re-mapping, use `/inbound/unlink`.

## IVR (menu routing)

For "press 1 for sales, 2 for support" or pre-call data collection. **Plivo only.**

```bash
curl -X POST https://api.bolna.ai/inbound/setup \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d @assets/ivr_department_routing.json
```

The asset file:

```json
{
  "agent_id": "default-agent-uuid",
  "phone_number_id": "phone-number-uuid",
  "ivr_config": {
    "enabled": true,
    "voice": "Polly.Aditi",
    "welcome_message": "Welcome to Acme Corp.",
    "timeout": 5,
    "max_retries": 2,
    "default_agent_id": "default-agent-uuid",
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

### Step types

| Type | Purpose |
|---|---|
| `menu` | Present options, route based on digit pressed. |
| `collect` | Capture a multi-digit input (account number, PIN). |

### Top-level IVR fields

| Field | Default | Notes |
|---|---|---|
| `enabled` | `false` | Master toggle. |
| `voice` | `Polly.Joanna` | Polly voice for the IVR prompts. `Polly.Aditi` for Hindi-English. |
| `welcome_message` | — | Played once on connect, before the first step. |
| `timeout` | `5` | Seconds to wait for caller input on a step. |
| `max_retries` | `2` | Retries on invalid input per step. |
| `invalid_input_message` | `"Invalid input. Please try again."` | Played on wrong key. |
| `no_input_message` | `"No input received. Goodbye."` | Played on timeout. |
| `steps[]` | required | IVR flow. |
| `default_agent_id` | — | Fallback agent when no option-level `agent_id` is set. |

### Step navigation

| Field | Behaviour |
|---|---|
| `next_step` | Linear: go to this step after current. |
| `conditional_next` | Branch by digit: `{"1": "menu_en", "2": "menu_hi"}`. |
| Neither | End of IVR. Route to selected `agent_id` or `default_agent_id`. |

### Multi-language IVR with branching

```json
{
  "step_id": "language",
  "type": "menu",
  "prompt": "For English press 1. Hindi ke liye 2 dabayein.",
  "field_name": "language",
  "options": [
    { "digit": "1", "label": "English" },
    { "digit": "2", "label": "Hindi" }
  ],
  "conditional_next": { "1": "menu_en", "2": "menu_hi" }
}
```

See `assets/ivr_multilingual.json` for the full multilingual department-routing flow.

### What the agent sees

After IVR completes, the collected fields are available as `recipient_data`:

```json
{
  "department": "Sales",
  "account_number": "123456",
  "language": "English",
  "ivr_completed_at": "2026-05-19T10:30:00Z"
}
```

Use them in agent prompts: `"Customer selected {department}. Account number: {account_number}."`

### Disable IVR

```bash
curl -X POST https://api.bolna.ai/inbound/setup \
  ... \
  -d '{ "agent_id": "...", "phone_number_id": "...", "ivr_config": { "enabled": false } }'
```

For full IVR reference (menu + collect step examples, conditional branching), see `references/ivr-config.md`.

## Caller identification (`ingest_source_config`)

Pre-fill the agent's prompt variables based on who's calling. Configured on the **agent**, not on `/inbound/setup`. Three flavours:

| Source | Best for |
|---|---|
| **Internal API** | Teams with an existing CRM / customer database. Real-time, fully dynamic. |
| **CSV upload** | Small teams, low-volume, no-code. Static — re-upload to update. |
| **Google Sheet** | Real-time sync without coding. Sheet must be publicly accessible. |

### Internal API source

Bolna does a `GET` request to your endpoint with:

```
GET https://your-api.example.com/customers
    ?contact_number=+19876543210
    &agent_id=<agent_uuid>
    &execution_id=<execution_uuid>
```

Auth: Bearer token (configured per agent).

Your response JSON is merged into `recipient_data`. Use it in prompts:

```
You are speaking with {first_name} {last_name}. They are on the {plan} plan,
last contacted on {last_contacted_at}.
```

### CSV / Google Sheet source

Both need a `contact_number` column (with country code). All other columns become prompt variables.

```csv
contact_number,first_name,last_name,plan,last_contacted_at
+19876543210,Priya,Sharma,Enterprise,2026-05-12
+918765432109,Rahul,Verma,Pro,2026-05-14
```

For full setup on each source, see `references/caller-identification.md`.

## Spam and abuse controls

These live on the **agent's** `task_config`, not on the inbound mapping itself.

| Field | Notes |
|---|---|
| `inbound_limit` | Max calls per recipient phone number. `-1` = unlimited. Useful to prevent a single number from running up costs. |
| `whitelist_phone_numbers[]` | E.164 numbers that always bypass any limits / unknown-caller rules. |
| `disallow_unknown_numbers` | Boolean. When `true`, reject callers not present in the agent's `ingest_source_config` lookup. **Requires `ingest_source_config` to be set.** |

```json
{
  "task_config": {
    "inbound_limit": 3,
    "whitelist_phone_numbers": ["+919876543210", "+19876543210"],
    "disallow_unknown_numbers": true
  }
}
```

> If `disallow_unknown_numbers: true` and `ingest_source_config` is not configured, every inbound call will be rejected. Always configure caller identification first.

## Multilingual auto-switching

Bolna can auto-detect the caller's language after ~3 conversation turns and switch system messages (hangup, user-online check, tool wait) to that language. Configure language variants in the agent:

```json
{
  "check_user_online_message": {
    "en": "Hey, are you still there?",
    "hi": "क्या आप अभी भी वहाँ हैं?",
    "ta": "வணக்கம், நீங்கள் இன்னும் இணைப்பில் இருக்கிறீர்களா?"
  },
  "call_hangup_message": {
    "en": "Thank you for calling. Goodbye!",
    "hi": "कॉल करने के लिए धन्यवाद। अलविदा!"
  }
}
```

Fallback order: detected language → `en` → first available. **Always configure `en` as a safety net.** See `references/auto-switch-messages.md`.

## Unlink

```bash
curl -X POST https://api.bolna.ai/inbound/unlink \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "phone_number_id": "123e4567-e89b-12d3-a456-426614174000" }'
```

The number remains owned (in your provider / SIP trunk / Bolna inventory). Only the agent link is removed.

## Going deeper

| File | Contents |
|---|---|
| `references/ivr-config.md` | All step types, navigation, voices, advanced patterns. |
| `references/caller-identification.md` | API, CSV, Google Sheet — setup walkthroughs and prompt-variable wiring. |
| `references/auto-switch-messages.md` | Multilingual message bundles, fallback order, supported codes. |
| `assets/ivr_department_routing.json` | Plain department-routing IVR. |
| `assets/ivr_multilingual.json` | Language selection → department menu, with separate agents per language. |
| `assets/ivr_account_verification.json` | Two-step `collect` flow (account + PIN) before agent. |
| `scripts/setup_inbound.py` | Wraps `POST /inbound/setup` with flags for plain and IVR setups. |

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Call rings but isn't answered | `phone_number_id` not yet mapped | Re-run `POST /inbound/setup`; verify with `GET /phone-numbers/all` |
| IVR returns `400` | Using IVR on non-Plivo number | IVR is Plivo-only; route via Plivo or skip IVR |
| `recipient_data` empty in prompt | `ingest_source_config` not set, or contact_number didn't match | Verify the source has the calling number; check Bolna logs for the lookup HTTP status |
| All callers rejected | `disallow_unknown_numbers: true` without `ingest_source_config` | Add the source first, or set `disallow_unknown_numbers: false` |
| Auto-switch hangup plays in wrong language | Detection needed 3 turns, call was shorter | Configure `en` fallback; expect the first turn or two to still be primary language |
| Agent picks up but audio quality is bad on inbound SIP | `ulaw` codec mismatch | Bolna sets `ulaw` on SIP-routed inbound; verify your trunk allows `ulaw` |

## See also

- `manage-phone-numbers` — buying or listing Bolna numbers (where `phone_number_id` comes from).
- `setup-sip-trunk` — wiring BYOT numbers into Bolna.
- `create-agent` — `task_config` (spam controls) and `ingest_source_config` live in the agent body.
- `setup-tools/references/dtmf.md` — keypad input *inside* a call (different from IVR menu routing).
- `../references/india-compliance.md` — DLT / 140 / 160-series rules if you're using regulated Indian numbers.

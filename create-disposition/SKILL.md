---
name: create-disposition
description: "Create, bulk-create, list, update, test, and delete Bolna dispositions for post-call structured extraction. Use when the user wants typed outcomes (lead_qualified, appointment_time, sentiment, churn_risk, consent_captured) pulled from every transcript and exposed in `extracted_data` on executions and webhook payloads. Covers Free Text vs Pre-defined answer types, validation (timestamp, numeric, boolean, email, regex), confidence scoring, copy-on-write semantics for shared dispositions, and the per-agent test endpoint."
license: MIT
compatibility: Requires internet access and a Bolna API key (BOLNA_API_KEY).
metadata:
  openclaw:
    requires:
      env:
        - BOLNA_API_KEY
    primaryEnv: BOLNA_API_KEY
---

# Bolna Dispositions (Post-Call Extractions)

Dispositions turn raw transcripts into structured data after every call. Each disposition asks one question; results land in `extracted_data` on the execution payload and in the webhook delivery.

## Hierarchy

```
Agent
└── Extractions (feature)
    └── Category  (e.g. "Lead Quality")
        └── Disposition  (e.g. "Call Outcome")
```

**Category** groups results visually. **Disposition** is the unit — one question, one answer set.

## When to add a disposition

| Use case | Field name | Answer type |
|---|---|---|
| Call outcome | `Call Outcome` | Pre-defined: `interested` / `not_interested` / `follow_up` / `wrong_number` |
| Lead qualification (BANT) | `Budget`, `Authority`, `Need`, `Timeline` | Mixed — free text + Yes/No |
| Appointment booked | `Appointment Date`, `Appointment Time` | Free text with `timestamp` / `text` validation |
| Sentiment | `Customer Sentiment` | Pre-defined: `positive` / `neutral` / `negative` |
| Agent handover required | `Handover Needed` | Pre-defined: `Yes` / `No` |
| Compliance | `Disclosure Read`, `Consent Captured` | Pre-defined: `Yes` / `No` |
| Contact info captured | `Email`, `Alt Phone` | Free text with `email` / `regex` validation |
| Open-ended summary | `Main Concern`, `Reason for Cancellation` | Free text |

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET    /dispositions/` | List all dispositions in the account (optionally scoped to an agent) |
| `GET    /dispositions/{id}` | Get a single disposition |
| `POST   /dispositions/` | Create one disposition, optionally linking to agents |
| `POST   /dispositions/bulk` | Create N dispositions for an agent atomically |
| `PUT    /dispositions/{id}` | Update a disposition (copy-on-write aware) |
| `DELETE /dispositions/{id}` | Delete a disposition |
| `POST   /v2/agent/{agent_id}/dispositions/test` | Test all of an agent's dispositions against a transcript |

Auth: `Authorization: Bearer $BOLNA_API_KEY`. JSON body for all POST/PUT.

## Disposition object

```json
{
  "name": "Call Outcome",
  "question": "What was the outcome of the call?",
  "system_prompt": "You are analyzing a sales call transcript.",
  "category": "Lead Quality",
  "model": "gpt-4.1-mini",

  "is_subjective": true,
  "is_objective": true,

  "subjective_type": "text",
  "subjective_type_config": null,

  "objective_options": [
    { "value": "interested",     "condition": "Customer expressed genuine interest and agreed to a next step" },
    { "value": "not_interested", "condition": "Customer declined all proposals" },
    { "value": "follow_up",      "condition": "Customer asked to be contacted later" }
  ],

  "agent_ids": ["3c90c3cc-0d44-4b50-8888-8dd25736052a"]
}
```

| Field | Type | Notes |
|---|---|---|
| `name` | string | Display name in `extracted_data`. |
| `question` | string | The prompt the LLM evaluates against the transcript. Be specific. |
| `system_prompt` | string \| null | Optional system context for the evaluation LLM. |
| `category` | string | Groups outputs. Default `"General"`. |
| `model` | string | Default `gpt-4.1-mini`. Use a stronger model for high-stakes extractions. |
| `is_subjective` | bool | Enables `subjective` free-text response. |
| `is_objective` | bool | Enables `objective` pre-defined selection. |
| `subjective_type` | string | Free-text constraint. See below. |
| `subjective_type_config` | object | Required when `subjective_type == "regex"`. |
| `objective_options` | array | Required when `is_objective` is true. |
| `agent_ids` | array | Agents this disposition is linked to. |

At least one of `is_subjective` or `is_objective` must be `true`.

## Free-text validation types

| `subjective_type` | What it validates | Example value | Notes |
|---|---|---|---|
| `text` | Anything | `"Customer was happy with the demo"` | Default. No validation. |
| `timestamp` | ISO 8601 | `"2026-04-08T14:30:00"` | Parsed and validated. |
| `numeric` | Int or decimal | `"42"`, `"3.14"` | |
| `boolean` | Exactly `true` or `false` | `"true"` | |
| `email` | Valid RFC email | `"user@example.com"` | |
| `regex` | Matches `subjective_type_config.pattern` | `"1234567890"` | Add `pattern` + optional `description` in `subjective_type_config`. |

When validation fails, the original LLM response is preserved in `subjective` and `validation.is_valid` is `false`. No data is lost — the consumer decides whether to use it.

Example with regex (10-digit phone):

```json
{
  "subjective_type": "regex",
  "subjective_type_config": {
    "pattern": "^\\d{10}$",
    "description": "10-digit phone number"
  }
}
```

## Objective options

```json
{
  "value": "interested",
  "condition": "Customer expressed genuine interest and agreed to a next step",
  "sub_options": []
}
```

`sub_options` is recursive and supports hierarchical classifications (e.g. `interested → enterprise / pro / starter`).

## Output format on executions

```json
{
  "execution_id": "abc123",
  "status": "completed",
  "transcript": "...",
  "extracted_data": {
    "Lead Quality": {
      "Call Outcome": {
        "subjective": "Customer expressed strong interest and asked about enterprise pricing.",
        "objective": "interested",
        "confidence": 0.92,
        "confidence_label": "High",
        "reasoning_subjective": "Customer asked about enterprise pricing and requested a demo.",
        "reasoning_objective": "Customer explicitly expressed interest and agreed to a next step.",
        "validation": null
      }
    },
    "Contact Info": {
      "Customer Email": {
        "subjective": "user@example.com",
        "objective": null,
        "confidence": 0.95,
        "confidence_label": "High",
        "reasoning_subjective": "Customer clearly provided their email address during the call.",
        "reasoning_objective": null,
        "validation": { "is_valid": true, "expected_type": "email" }
      }
    }
  }
}
```

| Field | Notes |
|---|---|
| `subjective` | Free-text response. `""` when nothing found, `null` when `is_subjective` is false. |
| `objective` | Selected pre-defined value, or `null`. |
| `confidence` | `0.0` – `1.0`. |
| `confidence_label` | `"High"` (≥0.8), `"Medium"` (≥0.5), `"Low"` (<0.5). |
| `reasoning_subjective` / `reasoning_objective` | LLM's explanation per answer type. Useful for audit + debugging. |
| `validation` | Present only when `subjective_type` is typed (not plain `text`). |

Same payload arrives via webhook. See `../references/execution-payload.md`.

## Create one disposition

```bash
curl --request POST https://api.bolna.ai/dispositions/ \
  --header "Authorization: Bearer $BOLNA_API_KEY" \
  --header "Content-Type: application/json" \
  --data @- <<'JSON'
{
  "name": "Call Outcome",
  "question": "What was the outcome of the call?",
  "category": "Lead Quality",
  "is_subjective": true,
  "is_objective": true,
  "subjective_type": "text",
  "objective_options": [
    { "value": "interested",     "condition": "Customer expressed genuine interest and agreed to a next step" },
    { "value": "not_interested", "condition": "Customer declined all proposals" },
    { "value": "follow_up",      "condition": "Customer asked to be contacted later" }
  ],
  "agent_ids": ["3c90c3cc-0d44-4b50-8888-8dd25736052a"]
}
JSON
```

Returns the full disposition object with `id`. Save it if you intend to update later.

## Bulk create (recommended for new agents)

Add a full analytics suite atomically — either all succeed or none do:

```bash
curl --request POST https://api.bolna.ai/dispositions/bulk \
  --header "Authorization: Bearer $BOLNA_API_KEY" \
  --header "Content-Type: application/json" \
  --data @assets/sample_bulk_dispositions.json
```

The asset file is a complete sales-call analytics pack: Call Outcome, Customer Sentiment, Budget mentioned, Decision Maker, Handover Needed, Customer Email.

## Test before going live

Run all of an agent's dispositions against a transcript and inspect what comes out:

```bash
curl --request POST "https://api.bolna.ai/v2/agent/$AGENT_ID/dispositions/test" \
  --header "Authorization: Bearer $BOLNA_API_KEY" \
  --header "Content-Type: application/json" \
  --data '{
    "transcript": "Agent: Hi, how can I help? Customer: I am interested in your enterprise plan. Agent: Great — what email should I send the proposal to? Customer: priya at example dot com.",
    "call_date": "2026-05-19T10:00:00Z"
  }'
```

Response is the same shape as a real execution's `extracted_data`. Iterate on dispositions until results match what you'd want from production calls.

## Updates and the copy-on-write rule

**Scoped update** (pass `agent_id` in the body or URL):

| Disposition state | Behaviour | Status |
|---|---|---|
| Exclusive to this agent | Edited in place | `200 OK` (id unchanged) |
| Shared with other agents | New private copy created, agent re-linked to copy | `201 Created` (**new id**) |

If you store disposition IDs in your own database, update the stored ID when you see `201`. The old ID still exists — it just no longer belongs to your scoped agent.

**Unscoped update** (no `agent_id`):

- Admins: edits any disposition in place.
- Non-admins: only edits dispositions they own.

## Authorization quirks

- Regular users can `DELETE` only dispositions they created (`created_by` matches their user ID).
- Admins can delete any disposition.
- Historical executions that already contain a disposition's output are unaffected by edits or deletion — only future calls change.

## Going deeper

| File | Contents |
|---|---|
| `references/answer-types.md` | Free Text vs Pre-defined, validation patterns, when to use each. |
| `references/copy-on-write.md` | Worked walkthrough of the 200 vs 201 update flow, with code. |
| `assets/sample_bulk_dispositions.json` | Drop-in sales-call analytics pack — 6 dispositions, two categories. |
| `assets/sample_transcripts.json` | Three transcripts (sales, support, appointment) for testing. |
| `scripts/create_disposition.py` | Wraps `POST /dispositions/` with flags. |
| `scripts/bulk_create_dispositions.py` | Wraps `POST /dispositions/bulk` from a JSON file. |
| `scripts/test_dispositions.py` | Wraps `POST /v2/agent/{id}/dispositions/test` for sample transcripts. |

## Legacy: `gpt_assistants.custom_questions`

Older agents (and some agents migrated from the v1 dashboard) carry their post-call extraction logic inline on the agent itself, **not** as separate disposition objects. You'll see this when `GET /v2/agent/{id}` returns:

```jsonc
{
  "dispositions": null,
  "gpt_assistants": [
    {
      "assistant_id": "asst_f4sCpG4zASXIls0FMl7PkMMt",
      "custom_questions": "1. interested:\n[- What to Extract: User interest in becoming an expert\n- Expected Response: Yes or No]\n\n2. reason_not_interested:\n[- What to Extract: Reason stated by the user...\n- Expected Response: Short reason]\n\n3. full_name:\n..."
    }
  ]
}
```

| Aspect | Legacy `gpt_assistants` | Modern `dispositions` |
|---|---|---|
| Where it lives | Inline on the agent, single free-text string | Separate disposition objects linked via `agent_ids` |
| Format | Numbered list, free-text "what to extract" + "expected response" hint | Structured: `name`, `question`, `objective_options[]`, `subjective_type` |
| Validation | None — the LLM returns whatever it interprets | Typed (`timestamp`, `email`, `regex`, etc.) with `validation.is_valid` flag |
| Confidence | No | Yes — `confidence` + `confidence_label` |
| Reusable across agents | No — copied per agent | Yes — one disposition can link to N agents |
| Where the result lands | Same `extracted_data` field on the execution | Same `extracted_data` field on the execution |

**Both systems coexist.** If `dispositions` is set, it runs. If `dispositions` is null but `gpt_assistants[0].custom_questions` has content, that runs instead. The output structure on the execution is the same shape either way.

**Migration:** when you ask the user to "add dispositions" to a legacy agent, you typically:

1. Parse the existing `custom_questions` string — one numbered item per intended disposition.
2. Convert each item into a structured disposition (`POST /dispositions/`).
3. Optionally clear `gpt_assistants` once the new dispositions are linked, so it's unambiguous which system is producing the output.

You don't need to migrate to use modern features — but you can't get confidence scores, typed validation, or shared dispositions without it.

## Common gotchas

- **Vague questions yield low confidence.** "How was the call?" → noisy. "Did the customer agree to a follow-up meeting? If yes, on what date?" → clear.
- **`objective_options.condition` is the LLM's selection rubric.** Write it as if instructing a human reviewer.
- **Don't pile many concepts into one disposition.** Split "lead quality and next step" into two dispositions — outcome + action.
- **Pick the right answer type.** Categorical = `is_objective`. Open-ended = `is_subjective`. Both = both flags true (lots of dispositions benefit from both).
- **Confidence ≥ 0.8 is generally trustworthy.** Below 0.5 → review manually. Build CRM routing around `confidence_label`, not raw transcript heuristics.
- **`agent_ids` is the linkage**. A disposition without `agent_ids` exists but doesn't run on any agent. Bulk-create is the easiest way to ensure every new disposition is linked.

## See also

- `get-executions` — fetching `extracted_data` after calls.
- `setup-webhook` — receiving extractions in real time.
- `create-agent` — top-level agent config (Extractions is a feature of the Analytics tab).
- `../references/execution-payload.md` — shape that contains `extracted_data`.

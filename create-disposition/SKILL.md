---
name: create-disposition
description: "Create, bulk-create, list, update, test, and delete Bolna dispositions for post-call classification and extraction. Use when the user wants structured call outcomes, lead qualification, appointment fields, sentiment, CRM fields, or analytics extracted from transcripts."
license: MIT
compatibility: "Requires internet access and BOLNA_API_KEY."
---

# Create Bolna Dispositions

## Purpose

Dispositions are post-call LLM classifiers. They evaluate transcripts after calls and write structured results into `extracted_data` on executions and webhook payloads.

Use dispositions for:

- Call outcome: interested, not interested, callback, wrong number.
- Lead quality: hot, warm, cold, disqualified.
- Appointment data: date, time, location, reschedule reason.
- Escalation: human handover needed, complaint, refund request.
- Compliance: consent captured, disclosure read, do-not-call request.

## Endpoints

- List: `GET https://api.bolna.ai/dispositions/`
- Get: `GET https://api.bolna.ai/dispositions/{disposition_id}`
- Create: `POST https://api.bolna.ai/dispositions/`
- Bulk create: `POST https://api.bolna.ai/dispositions/bulk`
- Update: `PUT https://api.bolna.ai/dispositions/{disposition_id}`
- Delete: `DELETE https://api.bolna.ai/dispositions/{disposition_id}`
- Test agent dispositions: `POST https://api.bolna.ai/v2/agent/{agent_id}/dispositions/test`

Use `Authorization: Bearer $BOLNA_API_KEY` and `Content-Type: application/json`.

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
    {
      "value": "interested",
      "condition": "Customer expressed genuine interest and agreed to a next step"
    },
    {
      "value": "not_interested",
      "condition": "Customer declined all proposals"
    },
    {
      "value": "follow_up",
      "condition": "Customer asked to be contacted later"
    }
  ],
  "agent_ids": ["3c90c3cc-0d44-4b50-8888-8dd25736052a"]
}
```

## Field rules

- `question`: precise question answered from the transcript.
- `category`: groups output in `extracted_data`.
- `is_subjective`: free-text answer.
- `is_objective`: selects from `objective_options`.
- `subjective_type`: `text`, `timestamp`, `numeric`, `boolean`, `email`, or `regex`.
- `objective_options`: required when `is_objective` is true. Each option needs `value` and `condition`; nested `sub_options` are allowed.
- `agent_ids`: link the disposition to agents.

## Bulk create

Use bulk creation when adding a full analytics set to an agent. It is atomic, so a malformed disposition should fail the group rather than leave a partial analytics setup.

## Test before production

```bash
curl --request POST \
  --url "https://api.bolna.ai/v2/agent/$AGENT_ID/dispositions/test" \
  --header "Authorization: Bearer $BOLNA_API_KEY" \
  --header "Content-Type: application/json" \
  --data '{
    "transcript": "Agent: Hi. Customer: I am interested in your enterprise plan.",
    "call_date": "2026-05-19T10:00:00Z"
  }'
```

Expected output is grouped by category and disposition name:

```json
{
  "extracted_data": {
    "Lead Quality": {
      "Call Outcome": {
        "subjective": "Customer expressed interest in enterprise pricing.",
        "objective": "interested"
      }
    }
  }
}
```

## Copy-on-write warning

Shared dispositions can be copied when updated through an agent scope. Before editing, check whether the user wants a shared template changed for all agents or a private agent-specific version.

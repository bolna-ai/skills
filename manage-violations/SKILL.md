---
name: manage-violations
description: "List Bolna call violations (paginated, status-filtered), inspect violation details, and submit evidence files (screenshots, documents, compliance proofs) for review. Bolna flags calls that may breach content policy, regulatory rules (DNC, TRAI calling hours, DLT mismatches), or fraud heuristics. Use when monitoring compliance, resolving account warnings, building an ops workflow around violation review, or attaching evidence to dispute a flag."
license: MIT
compatibility: Requires internet, a Bolna API key (BOLNA_API_KEY), and appropriate account permissions for the violations endpoints.
metadata:
  openclaw:
    requires:
      env:
        - BOLNA_API_KEY
    primaryEnv: BOLNA_API_KEY
---

# Bolna Violations

Violations are flags Bolna raises on calls that may breach content policy, regulatory rules, or fraud heuristics. Each violation has a status (open / under-review / resolved / rejected) and can have evidence attached. Use the API to monitor and respond to flags.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/violations/list` | List violations (paginated, status-filtered) |
| `POST` | `/violations/submit` | Submit evidence file + comment for a violation |

Auth: `Authorization: Bearer $BOLNA_API_KEY`.

## Violation object

```json
{
  "id": "vio_01HQXYZ123",
  "agent_id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
  "execution_id": "exec_abc123",
  "status": "open",
  "violation_type": "calling_hours",
  "description": "Call placed at 22:45 IST to +91XXXXXXXXXX — outside TRAI calling hours.",
  "evidence_required": true,
  "created_at": "2026-05-18T22:45:00Z",
  "due_by": "2026-05-25T22:45:00Z"
}
```

| Field | Notes |
|---|---|
| `status` | `open`, `under_review`, `resolved`, `rejected`. |
| `violation_type` | Bolna's category, e.g. `calling_hours`, `dnc_breach`, `content_policy`, `dlt_mismatch`, `consent_missing`, `fraud_signal`. |
| `evidence_required` | Some flags auto-resolve; others need you to submit evidence. |
| `due_by` | Deadline for evidence submission before the violation auto-escalates. |

## Common violation types

| Type | Trigger | Typical evidence |
|---|---|---|
| `calling_hours` | Outbound call outside the allowed window | Customer consent record showing waiver, or proof of corrected `calling_guardrails` |
| `dnc_breach` | Called a number on the do-not-call registry | DNC scrub log showing the number was clean at call time |
| `content_policy` | Agent prompt flagged for disallowed content | Updated prompt screenshot + explanation |
| `dlt_mismatch` | India 140/160 use without DLT approval | DLT approval certificate / Header URN |
| `consent_missing` | No recorded consent for the call | Opt-in record (form submission, signed contract) |
| `fraud_signal` | Unusual call pattern (mass dial, spoofing heuristic) | Business explanation + sample CRM records |

## List violations

```bash
# All open violations, page 1
curl "https://api.bolna.ai/violations/list?status=open&page_number=1&page_size=20" \
  -H "Authorization: Bearer $BOLNA_API_KEY"

# Everything for a specific agent
curl "https://api.bolna.ai/violations/list?agent_id=$AGENT_ID" \
  -H "Authorization: Bearer $BOLNA_API_KEY"
```

Response envelope follows the standard pagination shape (`total`, `has_more`, `data`). Loop until `has_more == false`.

## Submit evidence

Multipart POST with a file and optional comment.

```bash
curl -X POST https://api.bolna.ai/violations/submit \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -F 'violation_id=vio_01HQXYZ123' \
  -F 'file=@/path/to/evidence.pdf' \
  -F 'comment=Customer signed our consent form on 2026-05-10 — attached.'
```

| Form field | Required | Notes |
|---|---|---|
| `violation_id` | Yes | The `id` from `/violations/list`. |
| `file` | Usually yes | PDF, image, or doc with the evidence. |
| `comment` | Optional | Short explanation visible to Bolna's compliance review. |

Response confirms acceptance; status moves to `under_review`.

## Operational workflow

1. **Daily/weekly poll** of `GET /violations/list?status=open` — surface new flags.
2. **Triage** by `violation_type` — different teams own different categories (legal vs ops vs eng).
3. **Pull related executions** for context: `GET /executions/{execution_id}` + raw logs.
4. **Collect evidence** in your own systems (CRM exports, consent forms, prompt screenshots).
5. **Submit** via `POST /violations/submit` before `due_by`.
6. **Wait** for Bolna review to move status to `resolved` or `rejected`.
7. **Track** patterns — if the same `violation_type` recurs, fix the underlying agent / process.

## What to fix when you see each type

| Type | Likely fix |
|---|---|
| `calling_hours` | Set `calling_guardrails.call_start_hour` / `call_end_hour` correctly (recipient's TZ, not yours). |
| `dnc_breach` | Scrub against DNC registry before adding to batch CSV. |
| `content_policy` | Rewrite agent prompt removing prohibited content. Re-save to re-validate. |
| `dlt_mismatch` | Complete DLT / Header / Template registration (`../references/india-compliance.md`). |
| `consent_missing` | Capture explicit opt-in before placing calls; store the record. |
| `fraud_signal` | Reach out to support proactively — Bolna will want context on the legitimate use case. |

## Privacy and evidence handling

- **Evidence may contain PII** (customer signatures, IDs). Treat the upload as sensitive.
- **Don't commit evidence files to git** or paste contents into chat logs. Keep them in your own secure store and only upload via the API.
- **Audit log on your side**: record `violation_id`, evidence filename hash, submitter, and timestamp locally for compliance.
- **No fabrication.** Submit only real, dated evidence — false claims escalate the violation.

## Going deeper

| File | Contents |
|---|---|
| `scripts/list_violations.py` | Wraps `GET /violations/list` with status / agent / pagination. |
| `scripts/submit_violation_evidence.py` | Wraps `POST /violations/submit` with a multipart file upload. |

## See also

- `get-executions` — pull the offending call's transcript and raw logs for context before submitting.
- `../references/india-compliance.md` — DLT prerequisites that prevent `dlt_mismatch` flags.
- `create-agent` — `calling_guardrails` to prevent `calling_hours` flags.
- `setup-inbound` — `whitelist_phone_numbers` to prevent inbound spam flags.

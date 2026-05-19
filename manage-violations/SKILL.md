---
name: manage-violations
description: "List Bolna call violations, filter by status with pagination, and submit evidence files for violation review. Use when monitoring compliance, resolving account warnings, attaching screenshots or documents, or building an operations workflow around violations."
license: MIT
compatibility: "Requires BOLNA_API_KEY and appropriate account permissions."
---

# Manage Bolna Violations

## Endpoints

- List violations: `GET https://api.bolna.ai/violations/list`
- Submit evidence: `POST https://api.bolna.ai/violations/submit`

Use `Authorization: Bearer $BOLNA_API_KEY`.

## List workflow

1. Fetch violations with pagination.
2. Filter by status when the API supports it.
3. Group by account, agent, phone number, status, and age.
4. Escalate unresolved or repeated violations.
5. Keep evidence files out of git and private chat logs unless the user explicitly asks to store them.

## Submit workflow

Use submit when the user has evidence for a violation, such as a screenshot, document, or compliance proof. Confirm:

- Violation ID.
- Evidence file path.
- Whether the file contains sensitive personal data.
- Desired status or comment if supported by the API.

## Operational guidance

- Treat this as compliance-sensitive work.
- Do not fabricate evidence.
- Keep a local audit trail of what was submitted and when.
- If the violation is unclear, retrieve the relevant executions with `get-executions` and inspect raw logs before submitting.

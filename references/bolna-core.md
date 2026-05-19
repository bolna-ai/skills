# Bolna Core Reference

Cross-cutting facts every Bolna API call depends on — base URL, auth, headers, pagination, rate limits, phone-number format, and timezone rules.

## Base URL

```
https://api.bolna.ai
```

The older `api.bolna.dev` host is deprecated. Do not use it for new work.

## Authentication

Every request needs:

```
Authorization: Bearer $BOLNA_API_KEY
```

- Generate keys at `https://platform.bolna.ai` → **Developers** → **Create a new API Key**.
- The key is displayed once. Save it immediately. If lost, delete and regenerate.
- Sub-account keys are prefixed `sa-`. Code that needs to distinguish account vs sub-account can branch on the prefix.

## Standard headers

```
Authorization: Bearer $BOLNA_API_KEY
Content-Type: application/json     # for JSON POST/PATCH/PUT
Accept: application/json
```

For CSV uploads (`POST /batches`, `POST /knowledgebase`) use `multipart/form-data` — don't set `Content-Type` manually, let the HTTP client set the boundary.

## Pagination

List endpoints accept:

| Query param | Default | Max |
|---|---|---|
| `page_number` | `1` | — |
| `page_size` | `20` | `50` |

Response envelope:

```json
{
  "total": 38,
  "page": 2,
  "page_size": 5,
  "has_more": true,
  "data": [ ... ]
}
```

Loop until `has_more == false`. Don't try to compute pages from `total` — use the flag.

## Rate limits

Limits apply per **organization** (if you belong to one) or per **user**.

| Endpoint | Limit |
|---|---|
| `GET /v2/agent/{agent_id}` | 500/min |
| `GET /v2/agent/{agent_id}/executions` | 500/min |
| `POST /call` | 500/min |
| Everything else | 1000/min |

On `429 Too Many Requests`: back off with exponential delay. Spread bursts. Prefer **webhooks over polling** for execution updates.

## Phone numbers

Always **E.164**: `+91XXXXXXXXXX`, `+1XXXXXXXXXX`. Bare digits and national formats are rejected with `422` or `400`. Most "why doesn't this call go through" bugs trace back to a number missing `+` or country code.

## Webhook source IP

Bolna delivers webhooks from this single IP — whitelist it on your firewall:

```
13.203.39.153
```

Webhook payload shape = `GET /executions/{execution_id}` response. See `execution-payload.md`.

## Time and timezone

- All datetime fields use ISO 8601 with a **timezone offset**, e.g. `2026-05-19T18:30:00+05:30`.
- `scheduled_at` without offset is rejected or silently runs in UTC. Always include the offset.
- Graph-agent time variables (`recipient_data.current_hour`, etc.) populate **only when `timezone` is set on the call**. Without it, time-based expression edges never fire.
- Calling guardrails (`call_start_hour` / `call_end_hour`) are evaluated in the recipient's local timezone, not your account's.

## Common status codes

| Code | Meaning | First thing to check |
|---|---|---|
| `200` / `201` | Success | — |
| `202` | Accepted (event injection, batch schedule) | — |
| `400` | Malformed request | JSON body, field types |
| `401` | Missing or wrong `Authorization` header | `echo $BOLNA_API_KEY` |
| `403` | Key valid but not authorised for this resource | Sub-account scope, resource ownership |
| `404` | Resource missing | UUIDs, deleted entities, active vs ended calls |
| `422` | Validation failed | E.164 format, required fields, owned `from_phone_number` |
| `429` | Rate limited | Back off, slow down, use webhooks |
| `5xx` | Bolna-side error | Retry with backoff; if persistent, report to support |

## Dynamic variables

Bolna prompts and welcome messages substitute `{variable_name}` tokens at call time.

- **User variables**: defined by you. Values come from `user_data` on `POST /call`, CSV columns during batch calling, or graph-agent `context_data`.
- **System variables** (auto-filled): `agent_id`, `execution_id`, `call_sid`, `from_number`, `to_number`, `current_date`, `current_time`, `timezone`.

For inbound calls, `from_number` is the caller and `to_number` is your agent. For outbound calls it's reversed.

## OpenAPI spec

Pinned in `references/openapi.yml` (mirror of `https://www.bolna.ai/docs/api-reference/openapi.yml`). Treat the YAML as the canonical schema if a SKILL.md and the spec disagree.

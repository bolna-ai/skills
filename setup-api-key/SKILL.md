---
name: setup-api-key
description: "Generate, store, and verify a Bolna API key for BOLNA_API_KEY. Use when starting a Bolna project, configuring authentication, seeing 401 or 403 errors, or checking wallet and concurrency with the user API."
license: MIT
compatibility: Requires internet access. This skill helps you generate and verify BOLNA_API_KEY itself.
metadata:
  openclaw:
    requires:
      env:
        - BOLNA_API_KEY
    primaryEnv: BOLNA_API_KEY
---

# Setup Bolna API Key

## Core facts

- Base URL: `https://api.bolna.ai`
- Auth header: `Authorization: Bearer $BOLNA_API_KEY`
- Smoke test endpoint: `GET /user/me`
- API keys are created in the Bolna dashboard under Developers.
- The key is shown only once. If it is lost, delete it and generate a new one.
- Sub-account keys start with `sa-`.

## Workflow

1. Ask whether the user already has a Bolna API key.
2. If not, guide them to `https://platform.bolna.ai`, open Developers, and create a key.
3. Store it locally as an environment variable, never inside committed files.
4. Verify it with `GET /user/me`.
5. If verification fails, distinguish missing env var, invalid key, expired/deleted key, and insufficient account access.

## Shell setup

```bash
export BOLNA_API_KEY="paste-key-here"
```

For a project-local `.env`:

```bash
BOLNA_API_KEY=paste-key-here
```

Make sure `.env` is in `.gitignore`.

## cURL smoke test

```bash
curl --request GET \
  --url https://api.bolna.ai/user/me \
  --header "Authorization: Bearer $BOLNA_API_KEY"
```

Expected shape:

```json
{
  "id": "user-uuid",
  "name": "Account name",
  "email": "user@example.com",
  "wallet": 42.42,
  "concurrency": {
    "max": 10,
    "current": 0
  }
}
```

## Troubleshooting

- `401`: missing, malformed, deleted, or wrong API key.
- `403`: key exists but the account or sub-account cannot access the requested resource.
- `429`: rate limited; retry with exponential backoff.
- Empty `$BOLNA_API_KEY`: tell the user to export it in the shell session that will run scripts.

## Script

Run the included smoke test:

```bash
python3 setup-api-key/scripts/verify_key.py
```

## See also

- `../references/bolna-core.md` — base URL, headers, pagination, rate limits in one place.
- `manage-subaccounts` — the `sa-` prefix and the difference between parent vs sub-account keys.

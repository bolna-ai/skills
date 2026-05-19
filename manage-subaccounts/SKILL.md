---
name: manage-subaccounts
description: "Create, list, patch, delete, and inspect usage for Bolna enterprise sub-accounts. Sub-accounts provide isolated workspaces with auto-provisioned API keys (prefixed `sa-`), per-tenant agents/calls/phone-numbers/batches, and per-sub-account usage reporting for billing. Use for agencies, multi-tenant platforms, departments, regions, or regulated data boundaries. **Enterprise feature** — requires org admin access."
license: MIT
compatibility: Requires internet, a Bolna API key (BOLNA_API_KEY) with organization-admin scope, and Bolna enterprise tier for sub-account endpoints.
metadata:
  openclaw:
    requires:
      env:
        - BOLNA_API_KEY
    primaryEnv: BOLNA_API_KEY
---

# Bolna Sub-Accounts

Enterprise feature: split a parent organisation into isolated sub-account workspaces. Each sub-account gets its own auto-provisioned API key (prefixed `sa-`), its own agents, phone numbers, batches, executions, and a separate usage stream that rolls up to the parent for billing.

> **Enterprise only.** If `POST /sub-accounts/create` returns 403, the account isn't on the enterprise tier. Contact `enterprise@bolna.ai`.

## When to use

| Reason | Example |
|---|---|
| Multi-tenancy (agency / reseller) | One Bolna org per agency; one sub-account per client. |
| Department isolation | Sales / Support / Marketing share an org but want separate workspaces. |
| Region / compliance boundaries | EU customer data lives in an EU-tagged sub-account. |
| Environments | Dev / Staging / Prod sub-accounts under one billing umbrella. |

## What sub-accounts give you

- **Isolated data**: agents, calls, phone numbers, batches, executions don't bleed across sub-accounts.
- **Auto-provisioned API key**: created at the same time as the sub-account, prefixed `sa-`.
- **Per-sub-account usage**: separate `/usage` endpoint for billing reconciliation.
- **Centralised billing**: all sub-account spend rolls into the parent wallet.
- **Parent-only control**: a sub-account cannot create or destroy its own sub-accounts or modify other sub-accounts.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/sub-accounts/create` | Create a new sub-account |
| `GET` | `/sub-accounts/all` | List all sub-accounts |
| `PATCH` | `/sub-accounts/{sub_account_id}` | Update name / metadata |
| `DELETE` | `/sub-accounts/{sub_account_id}` | Delete (cascades to all sub-account data) |
| `GET` | `/sub-accounts/{sub_account_id}/usage` | Usage for one sub-account |
| `GET` | `/sub-accounts/all/usage` | Usage rollup across all sub-accounts |

Auth: parent-account `Authorization: Bearer $BOLNA_API_KEY` (an admin key on the parent org).

## Create

```bash
curl -X POST https://api.bolna.ai/sub-accounts/create \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Client - Customer A",
    "description": "Customer A workspace under Acme agency",
    "metadata": {
      "customer_id": "cust_abc123",
      "region": "in",
      "environment": "production"
    }
  }'
```

Response includes:

```json
{
  "id": "subacct_01HQXYZ123",
  "name": "Acme Client - Customer A",
  "api_key": "sa-bna_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "created_at": "2026-05-19T10:00:00Z"
}
```

**The `api_key` is shown only once.** Save it immediately. Sub-accounts cannot regenerate their own keys — only the parent can.

## Use the sub-account key

The sub-account API key works exactly like a top-level key, but only operates on the sub-account's resources:

```bash
export SA_KEY="sa-bna_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Creates an agent inside the sub-account
curl -X POST https://api.bolna.ai/v2/agent \
  -H "Authorization: Bearer $SA_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "agent_config": {...}, "agent_prompts": {...} }'
```

Any code that distinguishes parent vs sub-account behaviour can key on the `sa-` prefix.

## List sub-accounts

```bash
curl https://api.bolna.ai/sub-accounts/all \
  -H "Authorization: Bearer $BOLNA_API_KEY"
```

Paginated. Use `page_number` / `page_size` query params (see `../references/bolna-core.md`).

## Inspect usage

Per sub-account:

```bash
curl "https://api.bolna.ai/sub-accounts/$SUB_ACCOUNT_ID/usage" \
  -H "Authorization: Bearer $BOLNA_API_KEY"
```

Across all sub-accounts:

```bash
curl https://api.bolna.ai/sub-accounts/all/usage \
  -H "Authorization: Bearer $BOLNA_API_KEY"
```

Usage payloads typically include call minutes, executions count, phone-number rentals, and cost — useful for billing reconciliation. Pull weekly or daily and store in your own data warehouse.

## Patch

```bash
curl -X PATCH "https://api.bolna.ai/sub-accounts/$SUB_ACCOUNT_ID" \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "name": "Acme Client - Customer A (Renamed)" }'
```

The API key isn't regenerated on patch. To rotate, delete and recreate the sub-account.

## Delete — be careful

```bash
curl -X DELETE "https://api.bolna.ai/sub-accounts/$SUB_ACCOUNT_ID" \
  -H "Authorization: Bearer $BOLNA_API_KEY"
```

Deletion cascades:

- All agents in the sub-account.
- All batches, executions, recordings.
- All phone numbers owned by the sub-account (releases the DIDs; you lose them).
- All configurations and the `sa-` API key.

**Always confirm with the user** before deletion. Offer to back up:

- Agent configs: `GET /v2/agent/{id}` for each agent.
- Execution data: paginate `GET /v2/agent/{id}/executions`.
- Disposition definitions: `GET /dispositions/?agent_id=...`.

For audit-required organisations, archive these to your own storage before issuing the `DELETE`.

## Common patterns

### Per-customer workspaces (agency model)

```python
def onboard_new_client(client_name, client_id):
    sub = create_sub_account(name=f"Client - {client_name}", metadata={"client_id": client_id})
    store_in_db(client_id=client_id, sub_account_id=sub["id"], api_key=sub["api_key"])
    bootstrap_agents_for_client(sub["api_key"])
```

### Environment isolation

Create three sub-accounts: `acme-dev`, `acme-staging`, `acme-production`. Use the matching `sa-` key from each environment. Logs, calls, and phone numbers stay tagged correctly without manual filtering.

### Tenant billing reconciliation

Cron job pulls `GET /sub-accounts/all/usage` weekly, joins per-sub-account usage with your `clients` table, generates invoices.

## Quirks

- **Sub-accounts can't create their own sub-accounts.** Only the parent org admin can.
- **`sa-` keys can't access other sub-accounts.** Strict isolation.
- **Wallet is parent-level.** Sub-accounts don't have separate wallets — top up the parent.
- **Concurrency may be shared or per-sub-account** depending on tier; check `GET /sub-accounts/{id}/usage` for limit info.
- **Phone numbers bought via a sub-account belong to that sub-account.** Released on sub-account delete.

## Going deeper

| File | Contents |
|---|---|
| `scripts/create_sub_account.py` | Wraps `POST /sub-accounts/create` with name/metadata flags. |
| `scripts/list_sub_accounts.py` | Wraps `GET /sub-accounts/all` with pagination. |
| `scripts/sub_account_usage.py` | Wraps `GET /sub-accounts/{id}/usage` and the all-usage rollup. |

## See also

- `setup-api-key` — keys and the `sa-` prefix distinction.
- `../references/bolna-core.md` — auth, pagination.
- Bolna Enterprise: `https://www.bolna.ai/meet` for tier upgrades.

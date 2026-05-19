---
name: manage-subaccounts
description: "Create, list, patch, delete, and inspect usage for Bolna enterprise sub-accounts with isolated data, automatically provisioned API keys, concurrency limits, and centralized billing. Use for agencies, multi-tenant platforms, departments, or enterprise workspaces."
license: MIT
compatibility: "Requires organization admin access and BOLNA_API_KEY."
---

# Manage Bolna Sub-Accounts

## When to use

Use sub-accounts when one organization needs isolated Bolna workspaces for customers, departments, test environments, regions, or regulated data boundaries.

## Core facts

- Sub-accounts provide data isolation under a parent organization.
- Sub-accounts cannot generate their own API keys.
- When a sub-account is created, Bolna automatically provisions an associated API key.
- Sub-account API keys can start with `sa-`.
- Usage and billing can be inspected per sub-account or across all sub-accounts.

## Endpoints

- Create: `POST https://api.bolna.ai/sub-account`
- List: `GET https://api.bolna.ai/sub-accounts`
- Patch: `PATCH https://api.bolna.ai/sub-account/{sub_account_id}`
- Delete: `DELETE https://api.bolna.ai/sub-account/{sub_account_id}`
- Usage: `GET https://api.bolna.ai/sub-account/{sub_account_id}/usage`
- All usage: `GET https://api.bolna.ai/sub-accounts/usage`

Use `Authorization: Bearer $BOLNA_API_KEY`. Creation and patch requests use JSON.

## Workflow

1. Confirm the user has organization admin rights.
2. Decide the sub-account boundary: customer, department, region, environment, or team.
3. Set a clear name and concurrency limit if the API supports it for the account tier.
4. Store the returned sub-account API key securely.
5. Use the sub-account key for that tenant's agents, calls, phone numbers, and batches.
6. Monitor usage regularly from the parent account.

## Delete warning

Deleting a sub-account can delete its related agents, batches, executions, and configuration. Always confirm tenant, ID, and backup needs before deletion.

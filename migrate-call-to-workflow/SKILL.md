---
name: migrate-call-to-workflow
description: "Move an existing Bolna /call integration onto a Bolna workflow and rewrite the code that calls it. Use when a codebase places calls with POST https://api.bolna.ai/call and the user wants to switch to workflows, or wants retries, re-dials, routing on a variable, scheduled calls or multi-call follow-ups handled by Bolna instead of their own code."
license: MIT
compatibility: Requires internet access and a Bolna API key (BOLNA_API_KEY). Works over the REST API; the Bolna MCP server's workflow tools are an equivalent path.
metadata:
  openclaw:
    requires:
      env:
        - BOLNA_API_KEY
    primaryEnv: BOLNA_API_KEY
---

# Migrate a /call Integration to a Workflow

The end state:

- The code calls `POST /workflows/{workflow_id}/run` instead of `POST /call` for the migrated flow.
- Retry, re-dial, scheduling and agent-choosing logic moves out of the code and into the workflow.
- The existing call webhook handler keeps working unchanged.

## Rules

- Publishing and running act on the live account, and a run places a real, billed call. Ask the user before each one.
- The first test run dials a number the user owns, never a customer's.
- Do not edit or create Bolna agents unless the user asks. This skill only creates the workflow.
- Keep the old `/call` path behind a flag until the user confirms the workflow works in production.

## Step 1: Inventory the integration

Read the code and change nothing yet. For every place that calls `/call`, record:

| What | Why it matters |
|---|---|
| `agent_id` values, and how the code picks one | One agent node per agent. Picking by a variable becomes start-node cases |
| Every `user_data` key | Each becomes a declared start field and a mapped agent variable |
| `from_phone_number`: constant, per call, or absent | A constant goes on the agent node. Per call is not supported yet |
| `scheduled_at` | Becomes a `time` node |
| `retry_config`, or re-dial logic in the code (cron, queue, sleep loop) | Becomes cases on `call.status` plus a `retry` node. Record the statuses, intervals and attempt count |
| `agent_data` (voice_id, language) or `bypass_call_guardrails` | Not supported by workflows yet. Stop and tell the user this flow can't move as-is |
| How results are read: the agent's webhook, or polling `GET /executions/{id}` | Decides what changes in Step 7 |
| What is stored from the `/call` response | The run endpoint returns a workflow execution id instead of a call id |

Show the inventory to the user as a table and confirm it before building.

## Step 2: Read the agents

```bash
curl -s "https://api.bolna.ai/v2/agent/$AGENT_ID" -H "Authorization: Bearer $BOLNA_API_KEY"
```

Every `{placeholder}` in the welcome message and prompts must be mapped on the agent node. An agent node passes the call only the variables mapped on it, never the whole contact row. Validation in Step 4 warns `unmapped_agent_variable` for any it finds missing.

To confirm the keys sent today, read `context_details.recipient_data` on two or three recent calls from `GET https://api.bolna.ai/v2/agent/$AGENT_ID/executions`.

## Step 3: Map /call onto workflow pieces

| /call | Workflow |
|---|---|
| `agent_id` | Agent node `config.agent_id` |
| `recipient_phone_number` | `mobile_number` in the run body. The agent node dials `entry.mobile_number` by default |
| `user_data.<key>` | A start field `{"name": "<key>", "type": "string"}` in `config.fields`, plus `config.variables.<key> = {"value": {"var": "entry.<key>"}}` on every agent node that needs it |
| Constant `from_phone_number` | Agent node `config.from_number` |
| `retry_config` or code re-dials | Agent node cases on `call.status` routing to a `retry` node whose `attempts` are the intervals |
| `retry_on_voicemail: true` | Include `"voicemail"` in the statuses that route to the retry node |
| `scheduled_at` | A start field `scheduled_at` of type `timestamp`, and a `time` node with `"at": {"var": "entry.scheduled_at"}` before the agent node |
| Picking the agent by a variable | Start-node cases on `entry.<variable>`, one agent node per agent |

Declare a `user_data` key whose value is an object or array as `"type": "json"`: a `string` field rejects it, and the run returns `422`. The agent receives a `json` value as a JSON string.

Status names differ: `/call` uses `no-answer`, while the workflow's `call.status` uses `no_answer`. All `call.status` values are `completed`, `busy`, `no_answer`, `failed`, `voicemail`, `cancelled`, `rejected`, `timeout` and `error`.

Limits: 100 declared start fields, 200 nodes, 25 cases per node, 10 retry attempts. Field names match `^[a-zA-Z_][a-zA-Z0-9_-]{0,63}$`. `reference_id`, `mobile_number`, `name` and `email` are built-in fields and need no declaring. If the integration sends more than 100 `user_data` keys, stop and tell the user.

`assets/example-definition.json` is a complete definition that passes publish validation. It routes on a start field to one of two agents, and retries each on unanswered calls. Replace the agent ids, fields and values with the inventory's.

Shape rules that trip people up:

- The root needs `entry_node_id`, `on_no_match` and `nodes`.
- The start node routes with `cases`, never `to`. A node that doesn't branch uses one case, `{"when": {"always": true}, "then": {"to": "<next>"}}`.
- Only `time` nodes take `to`. `end` nodes take neither.
- Route every outcome to an `end` node, including the root `on_no_match`. Each end node's `label` becomes the execution's `termination_reason`, and its `outcome` is `success`, `failure` or `neutral`.

Every node type's config, defaults and bounds: `GET https://api.bolna.ai/workflow-node-types`.

## Step 4: Build and validate

```bash
H=(-H "Authorization: Bearer $BOLNA_API_KEY" -H "Content-Type: application/json")

# Create, then read the draft's current revision
WORKFLOW_ID=$(curl -s -X POST https://api.bolna.ai/workflows "${H[@]}" -d '{"name": "Screening calls"}' | jq -r .id)
REV=$(curl -s "https://api.bolna.ai/workflows/$WORKFLOW_ID/draft" "${H[@]}" | jq .revision)

# Save the definition, then validate
jq -n --argjson rev "$REV" --slurpfile def definition.json '{expected_revision: $rev, definition: $def[0]}' \
  | curl -s -X PUT "https://api.bolna.ai/workflows/$WORKFLOW_ID/draft" "${H[@]}" -d @-
curl -s -X POST "https://api.bolna.ai/workflows/$WORKFLOW_ID/validate" "${H[@]}"
```

Fix every error and every `unmapped_agent_variable` warning, save again with the new `revision`, and validate until clean. A `409` on save means the revision moved: read the draft again.

Show the user the routes in plain words: who gets called, with which agent, when it retries, and how it ends. Publish only after they agree:

```bash
curl -s -X POST "https://api.bolna.ai/workflows/$WORKFLOW_ID/publish" "${H[@]}"
```

With the Bolna MCP server connected, the same steps are `create_workflow`, `get_workflow_draft`, `save_workflow_draft`, `validate_workflow` and `publish_workflow`.

## Step 5: Test on the user's own number

Ask first, then run once per branch:

```bash
curl -s -X POST "https://api.bolna.ai/workflows/$WORKFLOW_ID/run" "${H[@]}" -d '{
  "reference_id": "migration-test-1",
  "mobile_number": "+91XXXXXXXXXX",
  "custom_fields": {"candidate_name": "Test", "job_role": "Analyst", "call_type": "screening"}
}'
curl -s "https://api.bolna.ai/workflow-executions/$EXECUTION_ID" "${H[@]}"
```

The execution's trail lists every node the contact passed through. The agent node's outputs carry `call.execution_id`. `GET https://api.bolna.ai/executions/{that id}` shows the call itself: check that its `recipient_data` holds every key the user's webhook handler reads today.

## Step 6: Rewrite the code

Keep `user_data` as it is and send it as `custom_fields`:

```python
# before
requests.post("https://api.bolna.ai/call", headers=headers, json={
    "agent_id": AGENT_ID,
    "recipient_phone_number": phone,
    "user_data": user_data,
})

# after
requests.post(f"https://api.bolna.ai/workflows/{WORKFLOW_ID}/run", headers=headers, json={
    "reference_id": run_reference,
    "mobile_number": phone,
    "custom_fields": user_data,
})
```

```javascript
// before
await fetch("https://api.bolna.ai/call", { method: "POST", headers, body: JSON.stringify({
  agent_id: AGENT_ID, recipient_phone_number: phone, user_data: userData,
}) });

// after
await fetch(`https://api.bolna.ai/workflows/${WORKFLOW_ID}/run`, { method: "POST", headers, body: JSON.stringify({
  reference_id: runReference, mobile_number: phone, custom_fields: userData,
}) });
```

- Put `WORKFLOW_ID` in config, next to where the agent id lives today.
- `reference_id` identifies one run. Sending the same value again returns `409 duplicate_run` with the existing `execution_id`, which makes retrying the HTTP request safe. Contacting the same person again for a separate reason needs a new value, for example `<order_id>-<purpose>`. Always set it: when omitted, it is derived from the row's content, so two identical requests collide.
- If `user_data` contains `name` or `email`, those are built-in fields and go at the top level, not under `custom_fields`.
- A `422 unknown_field` means a key isn't declared on the start node. Declare and map it, or stop sending it.
- The `201` response is `{"execution_id", "campaign_id", "workflow_version", "status"}`. Store this `execution_id` where the call's id was stored.
- Turn off the code's own re-dial and scheduling logic for this flow, behind the same flag as the new call path.

## Step 7: Results and webhooks

- **Call webhook:** the agent's webhook fires for every call the workflow places, with the same payload as before. A retried contact now produces one webhook per attempt, each with its own execution id. Handlers that read `recipient_data` keep working as long as every key they read is mapped on the agent node.
- **Execution webhook (optional):** one POST per contact when the workflow finishes, with `execution_id`, `reference_id`, `status`, `outcome`, `termination_reason` and the full `trail`. Turn it on with `PATCH https://api.bolna.ai/workflows/$WORKFLOW_ID` and body `{"settings": {"webhook": {"url": "https://..."}}}`, then send a sample with `POST https://api.bolna.ai/workflows/$WORKFLOW_ID/webhook:test`. Join on `reference_id`.
- **Polling:** replace `GET /executions/{execution_id}` with `GET /workflow-executions/{execution_id}`. For a call's transcript or recording, read `call.execution_id` from the agent node in the trail, then `GET /executions/{that id}`.

## Checklist before switching production traffic

- Every `user_data` key the prompts or the webhook handler use is declared and mapped, and validation shows no `unmapped_agent_variable`.
- Every branch has been tested on the user's own number.
- The `reference_id` scheme is decided and unique per run.
- The code's own re-dial and scheduling logic is off for this flow.
- The old `/call` path is still there behind a flag, for rollback.

## See also

- `make-call`: the `/call` fields this skill maps from.
- `setup-webhook`: the per-call webhook the workflow keeps firing.
- `bolna-graph-agents`: when routing belongs inside the call rather than before it.
- Workflow docs: https://www.bolna.ai/docs/workflows/introduction

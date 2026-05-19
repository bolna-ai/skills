---
name: manage-agents
description: "List, fetch, patch, fully update, delete, and stop queued calls for Bolna v2 voice agents. Use when the user wants to inspect agent configuration, change prompts or voices, back up an agent, decommission an agent, or cancel all queued calls for one agent."
license: MIT
compatibility: Requires internet access and a Bolna API key (BOLNA_API_KEY).
metadata:
  openclaw:
    requires:
      env:
        - BOLNA_API_KEY
    primaryEnv: BOLNA_API_KEY
---

# Manage Bolna Agents

## Endpoints

- List agents: `GET https://api.bolna.ai/v2/agent/all`
- Get agent: `GET https://api.bolna.ai/v2/agent/{agent_id}`
- Full update: `PUT https://api.bolna.ai/v2/agent/{agent_id}`
- Patch update: `PATCH https://api.bolna.ai/v2/agent/{agent_id}`
- Delete agent: `DELETE https://api.bolna.ai/v2/agent/{agent_id}`
- Stop queued calls for one agent: `POST https://api.bolna.ai/v2/agent/{agent_id}/stop`

Always send `Authorization: Bearer $BOLNA_API_KEY`. Send `Content-Type: application/json` for `PUT` and `PATCH`.

## Workflow

1. Use list or get before changing an agent.
2. Prefer `PATCH` for small changes to prompt, welcome message, webhook URL, synthesizer, inbound source config, or SIP telephony provider.
3. Use `PUT` only when you have the full desired agent document. A partial `PUT` can drop existing nested configuration.
4. Save a copy of the existing config before destructive changes.
5. Use stop before deleting when queued calls should not run.
6. Delete only after confirming the user understands this cleans up the agent and related operational data.

## List agents

```bash
curl --request GET \
  --url https://api.bolna.ai/v2/agent/all \
  --header "Authorization: Bearer $BOLNA_API_KEY"
```

## Patch prompt or welcome message

```bash
curl --request PATCH \
  --url "https://api.bolna.ai/v2/agent/$AGENT_ID" \
  --header "Authorization: Bearer $BOLNA_API_KEY" \
  --header "Content-Type: application/json" \
  --data '{
    "agent_config": {
      "agent_name": "Support Agent",
      "agent_welcome_message": "Hi {customer_name}, this is Tara from Acme."
    },
    "agent_prompts": {
      "task_1": {
        "system_prompt": "You are a concise support agent. Ask one question at a time."
      }
    }
  }'
```

## Patch SIP telephony provider

```bash
curl --request PATCH \
  --url "https://api.bolna.ai/v2/agent/$AGENT_ID" \
  --header "Authorization: Bearer $BOLNA_API_KEY" \
  --header "Content-Type: application/json" \
  --data '{"agent_config":{"telephony_provider":"sip-trunk"}}'
```

After this, map a SIP trunk phone number with `setup-inbound` for inbound calls, or use a trunk DID as the outbound caller ID.

## Stop queued calls

```bash
curl --request POST \
  --url "https://api.bolna.ai/v2/agent/$AGENT_ID/stop" \
  --header "Authorization: Bearer $BOLNA_API_KEY"
```

This stops queued calls for the agent. It is different from stopping one call or one batch.

## Delete agent

```bash
curl --request DELETE \
  --url "https://api.bolna.ai/v2/agent/$AGENT_ID" \
  --header "Authorization: Bearer $BOLNA_API_KEY"
```

## PUT vs PATCH

| When | Use |
|---|---|
| Renaming, swapping voice, updating webhook URL, changing the system prompt, toggling `task_config` flags | `PATCH` |
| Wholesale replacement of `agent_config` from a backed-up document | `PUT` |

`PUT` requires the **full** `agent_config` body — anything you omit is dropped. Common bug: PUT-ing a partial body loses `tools_config.api_tools` or `ingest_source_config`. Prefer `PATCH` when you only know a subset of fields.

## See also

- `create-agent` — initial creation; same shape `PUT` expects.
- `make-call` — `POST /v2/agent/{id}/stop` cancels queued calls for one agent without deleting it.
- `bolna-graph-agents` — for editing `llm_agent.nodes` and edge structures.
- `../references/bolna-core.md` — auth, headers, pagination defaults.

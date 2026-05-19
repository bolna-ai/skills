---
name: setup-webhook
description: "Configure Bolna webhooks for real-time call status and execution updates, validate webhook URLs, receive payloads, reconcile execution IDs, and build a local receiver. Use for CRM sync, dashboards, post-call automation, Make, Zapier, n8n, or custom backend integrations."
license: MIT
---

# Setup Bolna Webhooks

## What Bolna sends

Bolna sends HTTP POST requests to the configured webhook URL as call status and execution data changes. Treat the webhook payload as the execution object; use `get-executions` for the same execution ID to reconcile missed or duplicate delivery.

## Where to configure

- Dashboard: agent Analytics tab, "Push all execution data to webhook".
- API: set `agent_config.webhook_url` when creating or patching an agent.

## API patch

```bash
curl --request PATCH \
  --url "https://api.bolna.ai/v2/agent/$AGENT_ID" \
  --header "Authorization: Bearer $BOLNA_API_KEY" \
  --header "Content-Type: application/json" \
  --data '{
    "agent_config": {
      "webhook_url": "https://example.com/bolna/webhook"
    }
  }'
```

## Receiver requirements

- Public HTTPS URL in production.
- Accept POST JSON.
- Respond quickly with 2xx.
- Store by `execution_id` or `id` idempotently.
- Verify the payload shape before triggering irreversible downstream actions.
- If firewalling, check current Bolna docs for webhook source IPs before allow-listing.

## Local test receiver

```bash
python3 setup-webhook/scripts/webhook_receiver.py --port 8080
```

Expose with a tunnel such as ngrok or Cloudflare Tunnel, then configure the public HTTPS URL in Bolna.

## Minimal payload handling pattern

1. Parse JSON.
2. Extract execution ID, status, agent ID, phone numbers, transcript, recording URL, and extracted data.
3. Upsert into your database by execution ID.
4. Trigger automation only after relevant terminal statuses, usually `completed`, `failed`, `no-answer`, `busy`, or `error`.
5. If payload is incomplete, call `GET /executions/{execution_id}`.

## Common automations

- Send summary and recording to CRM.
- Update lead status from extracted data.
- Create a support ticket after failed handoff.
- Send WhatsApp, SMS, or email through Make, Zapier, n8n, or custom code.
- Build live dashboard cards from `queued`, `ringing`, `in-progress`, and `completed`.

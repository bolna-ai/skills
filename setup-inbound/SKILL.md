---
name: setup-inbound
description: "Configure Bolna inbound calling by mapping an agent to a phone number, unlinking inbound routing, setting caller matching, IVR options, spam limits, whitelists, and unknown caller behavior. Use for support lines, front desk agents, IVR, and SIP trunk inbound numbers."
license: MIT
---

# Setup Bolna Inbound Calls

## Endpoints

- Set inbound agent: `POST https://api.bolna.ai/inbound/setup`
- Unlink inbound agent: `POST https://api.bolna.ai/inbound/unlink`

Use `Authorization: Bearer $BOLNA_API_KEY` and `Content-Type: application/json`.

## Basic mapping

```bash
curl --request POST \
  --url https://api.bolna.ai/inbound/setup \
  --header "Authorization: Bearer $BOLNA_API_KEY" \
  --header "Content-Type: application/json" \
  --data '{
    "agent_id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
    "phone_number_id": "123e4567-e89b-12d3-a456-426614174000"
  }'
```

`phone_number_id` comes from Bolna phone number APIs, bought numbers, or SIP trunk number mapping.

## IVR configuration

Bolna supports IVR-style inbound setup. Include `allow_multiple` and `ivr_config` only when the user needs department routing, language selection, or menu-based routing.

```json
{
  "agent_id": "agent-uuid",
  "phone_number_id": "phone-number-id",
  "allow_multiple": true,
  "ivr_config": {
    "enabled": true,
    "voice": "Polly.Aditi",
    "welcome_message": "Welcome to Acme.",
    "timeout": 7,
    "max_retries": 2
  }
}
```

## Caller matching

Configure caller matching on the agent through `ingest_source_config`:

- API: Bolna calls your endpoint with `contact_number`, `agent_id`, and `execution_id`; your API returns JSON variables.
- CSV: file must include `contact_number`.
- Google Sheet: sheet must be public and include `contact_number`.

Returned fields can be used in prompts as dynamic variables.

## Spam prevention

Use these agent task settings:

- `inbound_limit`: max calls per phone number. `-1` means unlimited.
- `whitelist_phone_numbers`: always-allow list.
- `disallow_unknown_numbers`: reject callers not found in the configured data source.

If `disallow_unknown_numbers` is true, make sure caller matching is configured first.

## Unlink

```bash
curl --request POST \
  --url https://api.bolna.ai/inbound/unlink \
  --header "Authorization: Bearer $BOLNA_API_KEY" \
  --header "Content-Type: application/json" \
  --data '{
    "phone_number_id": "123e4567-e89b-12d3-a456-426614174000"
  }'
```

After unlinking, the number remains owned but no longer routes to that agent.

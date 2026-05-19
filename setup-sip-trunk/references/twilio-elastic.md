# Twilio Elastic SIP Trunk — End-to-End

Step-by-step setup for connecting Twilio Elastic SIP to Bolna. Use this when you already have (or want to set up) a Twilio Elastic SIP trunk and want Bolna agents to handle calls on it.

## Prerequisites

- Twilio account with Elastic SIP Trunking enabled.
- At least one Twilio number assigned to the trunk.
- Bolna account with SIP trunking access (enterprise beta).

## On Twilio

### 1. Create the trunk

Twilio Console → **Elastic SIP Trunking** → **Trunks** → **Create new SIP Trunk**.

- **Friendly name**: e.g. `Bolna Production`.
- **Domain name**: Twilio assigns one, e.g. `your-trunk.pstn.twilio.com`. **Save this** — it's the gateway address.

### 2. Auth — Credential List (recommended)

Twilio Console → **Elastic SIP Trunking** → **Authentication** → **Credential Lists** → **+**.

- Create credentials: pick a unique `username` and a strong `password`.
- Save them.

Back in the trunk: **Termination** → **Credential Lists** → attach your new list.

### 3. Termination URI

In **Termination** → **Termination URI**, note the URI Twilio expects calls to arrive at. This is the address **you** put on the carrier-side; Bolna will INVITE this from its IP.

### 4. Origination — point Twilio to Bolna

**Origination** → **Origination URIs** → add:

| If your Bolna trunk transport is | Use |
|---|---|
| UDP | `sip:sip.bolna.ai:5060` |
| TCP | `sip:sip.bolna.ai:5060` |
| TLS | `sip:sip.bolna.ai:5061;transport=tls` |

Set priority `10`, weight `10`. Save.

### 5. Whitelist Bolna's IP

**IP Access Control Lists** → create new list → add `13.200.45.61/32`.

In your trunk's **Termination** tab, attach that ACL so Bolna's INVITE is allowed.

### 6. Attach phone numbers

**Numbers** → add the Twilio numbers you want to use on this trunk.

## On Bolna

### Create the trunk

```bash
curl -X POST https://api.bolna.ai/sip-trunks/trunks \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Twilio Production",
    "provider": "twilio",
    "auth_type": "userpass",
    "auth_username": "<credential-list-username>",
    "auth_password": "<credential-list-password>",
    "gateways": [
      { "gateway_address": "your-trunk.pstn.twilio.com", "port": 5060, "priority": 1 }
    ],
    "transport": "transport-udp",
    "allow": "ulaw,alaw",
    "disallow": "all",
    "inbound_enabled": true,
    "outbound_leading_plus_enabled": true
  }'
```

Capture the returned trunk `id`.

### Register DIDs

```bash
curl -X POST "https://api.bolna.ai/sip-trunks/trunks/$TRUNK_ID/numbers" \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "phone_number": "+15551234567", "name": "Sales Line" }'
```

Save each `phone_number_id`.

### Wire to agents

**For inbound**:

```bash
curl -X POST https://api.bolna.ai/inbound/setup \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "agent_id": "'$AGENT_ID'", "phone_number_id": "'$PHONE_NUMBER_ID'" }'
```

**For outbound** — patch the agent's telephony provider once:

```bash
curl -X PATCH "https://api.bolna.ai/v2/agent/$AGENT_ID" \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"agent_config":{"telephony_provider":"sip-trunk"}}'
```

Then call:

```bash
curl -X POST https://api.bolna.ai/call \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "'$AGENT_ID'",
    "recipient_phone_number": "+19876543210",
    "from_phone_number": "+15551234567"
  }'
```

## TLS + SDES (encrypted media) on Twilio

Twilio supports TLS termination and SDES SRTP. If you want encrypted media:

1. Twilio trunk → **Termination** → enable **Secure** (TLS) → port `5061`.
2. **Encrypted Media** → enable.
3. On Bolna, change the trunk:

```bash
curl -X PATCH "https://api.bolna.ai/sip-trunks/trunks/$TRUNK_ID" \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "transport": "transport-tls",
    "media_encryption": "sdes",
    "gateways": [
      { "gateway_address": "your-trunk.pstn.twilio.com", "port": 5061, "priority": 1 }
    ]
  }'
```

4. Update Twilio's origination URI to `sip:sip.bolna.ai:5061;transport=tls`.

If you can't get media to flow afterwards, flip `media_encryption_optimistic: true` and test — it'll fall back to plain RTP while you debug.

## Common Twilio-specific issues

| Issue | Cause | Fix |
|---|---|---|
| `403 Forbidden` on INVITE from Bolna | Credential List not attached, or IP ACL missing | Verify both on the Termination tab |
| Inbound call hits Twilio but doesn't reach Bolna | Origination URI not set, or trunk's Origination tab disabled | Check Origination → URIs |
| Audio one-way (inbound caller can't be heard) | NAT / SRTP mismatch | Confirm `rtp_symmetric: true`; check Twilio's Secure Media toggle |
| Calls drop after exactly 30s | OPTIONS pings disabled or carrier requires keep-alive | `qualify_frequency: 60` (default) on Bolna's side |
| Long Twilio call IDs cause INVITE to be too big | UDP fragmentation | `transport: "transport-tcp"` |
| `from_number` not recognised | Twilio number isn't on the trunk's Numbers tab | Add it on Twilio first, then on Bolna |

---
name: setup-sip-trunk
description: "Bring your own SIP trunk to Bolna (BYOT) for AI voice agents. Create a trunk with gateways, IP-based or user/password auth, UDP/TCP/TLS transport, optional SDES (SRTP) media encryption, add DID numbers, and wire them to agents for inbound or outbound calls. Use with Twilio Elastic SIP, Plivo Zentrunk, Telnyx, Vonage, Zadarma, DIDWW, or any standards-compliant trunk. Covers IP whitelisting (`13.200.45.61`), origination URI setup, and the classic SRTP-mismatch / UDP-fragmentation / TLS-without-SDES diagnostic flow."
license: MIT
compatibility: Requires internet, a Bolna API key (BOLNA_API_KEY), and Bolna SIP-trunking beta access (contact enterprise@bolna.ai).
metadata:
  openclaw:
    requires:
      env:
        - BOLNA_API_KEY
    primaryEnv: BOLNA_API_KEY
---

# Bolna SIP Trunk (BYOT)

Use any standards-compliant SIP trunk — Twilio Elastic SIP, Plivo Zentrunk, Telnyx, Vonage, Zadarma, DIDWW, or your own carrier — for both inbound and outbound calls handled by a Bolna agent.

> **Beta.** SIP trunking requires enterprise access. Contact `enterprise@bolna.ai` if API calls return access errors before changing code.

## Why use BYOT

| Reason | Detail |
|---|---|
| Keep your existing carrier relationships | No porting, no parallel billing. |
| Negotiated rates | Bolna doesn't markup your minutes. |
| Number portability | Use the numbers you already own. |
| Compliance / regional carriers | Required when local regulation mandates a specific carrier. |

## High-level flow

```
1. Provider portal:    Whitelist 13.200.45.61, set origination URI to sip.bolna.ai
2. POST /sip-trunks/trunks                       → create trunk in Bolna
3. POST /sip-trunks/trunks/{id}/numbers          → register your DIDs on the trunk
4. PATCH /v2/agent/{id} telephony_provider=sip-trunk   (for outbound)
5. POST /inbound/setup                           → link DID ↔ agent (for inbound)
6. POST /call with from_phone_number = your DID  → outbound dial
```

## Step 0 — On your SIP provider's portal

### Whitelist Bolna's IP

```
13.200.45.61
```

Add this to your provider's allowed IPs / ACL / trusted-IP list. Without it Bolna's outbound INVITE and RTP packets get dropped.

For `ip-based` auth, this is also the IP your trunk identifies Bolna by.

### Set the origination URI (for inbound)

| Trunk transport | Origination URI |
|---|---|
| UDP or TCP | `sip:sip.bolna.ai:5060` |
| TLS | `sip:sip.bolna.ai:5061;transport=tls` |

If your provider only accepts an IP, use `sip:13.200.45.61:5060` for UDP/TCP. **TLS inbound requires the hostname** so the carrier can validate Bolna's TLS cert.

Set this either per DID or on the trunk as a whole — depends on your provider.

### Codecs

G.711 **ulaw** by default. Allow at least `ulaw` (and ideally `alaw` too). Avoid G.729 and other compressed codecs.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/sip-trunks/trunks` | Create a trunk |
| `GET` | `/sip-trunks/trunks` | List trunks |
| `GET` | `/sip-trunks/trunks/{trunk_id}` | Get one trunk |
| `PATCH` | `/sip-trunks/trunks/{trunk_id}` | Update a trunk |
| `DELETE` | `/sip-trunks/trunks/{trunk_id}` | Delete a trunk |
| `POST` | `/sip-trunks/trunks/{trunk_id}/numbers` | Add a DID |
| `GET` | `/sip-trunks/trunks/{trunk_id}/numbers` | List DIDs |
| `DELETE` | `/sip-trunks/trunks/{trunk_id}/numbers/{phone_number_id}` | Remove a DID |
| `POST` | `/inbound/setup` | Map a DID's `phone_number_id` to an agent |
| `POST` | `/inbound/unlink` | Unmap |

All paths are under `https://api.bolna.ai`. Auth: `Authorization: Bearer $BOLNA_API_KEY`.

## Worked example: Twilio Elastic SIP (userpass)

```bash
curl -X POST https://api.bolna.ai/sip-trunks/trunks \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Twilio Production",
    "provider": "twilio",
    "description": "Main Twilio Elastic SIP trunk",
    "auth_type": "userpass",
    "auth_username": "<your-sip-username>",
    "auth_password": "<your-sip-password>",
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

Response includes the trunk `id`. **Save it.**

## Worked example: Plivo Zentrunk (ip-based)

```bash
curl -X POST https://api.bolna.ai/sip-trunks/trunks \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Plivo Zentrunk",
    "provider": "plivo",
    "auth_type": "ip-based",
    "gateways": [
      { "gateway_address": "21467306465797919.zt.plivo.com", "port": 5060, "priority": 1 }
    ],
    "ip_identifiers": [
      { "ip_address": "15.207.90.192/31" },
      { "ip_address": "204.89.151.128/27" },
      { "ip_address": "13.52.9.0/25" }
    ],
    "transport": "transport-udp",
    "inbound_enabled": true
  }'
```

`ip_identifiers` are the carrier's egress IPs. Plivo, Telnyx, and others publish these.

## Worked example: TLS + SDES (encrypted media)

For carriers that support encrypted signaling and media:

```bash
curl -X POST https://api.bolna.ai/sip-trunks/trunks \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Twilio Production (encrypted)",
    "provider": "twilio",
    "auth_type": "userpass",
    "auth_username": "<u>",
    "auth_password": "<p>",
    "gateways": [
      { "gateway_address": "your-trunk.pstn.twilio.com", "port": 5061, "priority": 1 }
    ],
    "transport": "transport-tls",
    "media_encryption": "sdes",
    "media_encryption_optimistic": false,
    "inbound_enabled": true
  }'
```

| Knob | What it does |
|---|---|
| `transport: "transport-tls"` | Encrypted SIP signaling. Port `5061`. |
| `media_encryption: "sdes"` | SRTP with keys exchanged in SDP. **Requires TLS transport.** |
| `media_encryption_optimistic: true` | Fallback to plain RTP if carrier doesn't offer crypto. Useful for testing. |

Your carrier must have SDES/SRTP enabled on its end too — if not, the SIP call sets up but media never establishes (silent call).

## Add DID numbers to the trunk

```bash
curl -X POST "https://api.bolna.ai/sip-trunks/trunks/$TRUNK_ID/numbers" \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "919876543210",
    "name": "Mumbai Support Line"
  }'
```

Response contains a `phone_number_id` — this is the ID you use for inbound mapping. **Save it.** Bolna stores the number string verbatim; inbound matching is `+`-tolerant on lookup but be consistent.

## Outbound calls from your trunk

Patch the agent so Bolna routes via your trunk:

```bash
curl -X PATCH "https://api.bolna.ai/v2/agent/$AGENT_ID" \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"agent_config":{"telephony_provider":"sip-trunk"}}'
```

Then place the call as normal — `from_phone_number` must be a DID registered on your trunk:

```bash
curl -X POST https://api.bolna.ai/call \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "'$AGENT_ID'",
    "recipient_phone_number": "+918800001234",
    "from_phone_number": "+919876543210"
  }'
```

## Inbound calls to your trunk

After registering the DID, map it to an agent:

```bash
curl -X POST https://api.bolna.ai/inbound/setup \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "'$AGENT_ID'",
    "phone_number_id": "'$PHONE_NUMBER_ID'"
  }'
```

Bolna automatically sets the agent's audio format to `ulaw` to match Asterisk's requirements for SIP-routed calls.

**One number, one agent.** Re-mapping a DID to a new agent automatically unmaps it from the previous one. To detach without re-mapping, use `POST /inbound/unlink` with the same body.

## Create-trunk field reference

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `name` | string | Yes | — | Unique per account. |
| `provider` | string | Yes | — | `twilio`, `plivo`, `telnyx`, `vonage`, `custom`, etc. |
| `description` | string | No | `null` | Internal. |
| `auth_type` | string | Yes | — | `userpass` or `ip-based`. |
| `auth_username` / `auth_password` | string | Conditional | — | Required when `auth_type == "userpass"`. |
| `gateways[]` | array | Yes | — | One or more `{gateway_address, port, priority}`. |
| `ip_identifiers[]` | array | Conditional | `[]` | Required when `auth_type == "ip-based"`. List of `{ip_address}`. |
| `allow` | string | No | `"ulaw,alaw"` | CSV codecs. Always include `ulaw`. |
| `disallow` | string | No | `"all"` | CSV codecs. |
| `transport` | enum | No | `"transport-udp"` | `transport-udp`, `transport-tcp`, `transport-tls`. |
| `media_encryption` | enum | No | `"no"` | `no` or `sdes`. **`sdes` requires `transport-tls`.** |
| `media_encryption_optimistic` | bool | No | `false` | Falls back to clear RTP if carrier doesn't offer crypto. |
| `inbound_enabled` | bool | No | `false` | Turn on for incoming calls. |
| `outbound_leading_plus_enabled` | bool | No | `true` | Prepend `+` on outbound dials. Some carriers reject `+`. |
| `direct_media` | bool | No | `false` | Keep `false`. |
| `rtp_symmetric` | bool | No | `true` | Required for NAT. |
| `force_rport` | bool | No | `true` | Required for NAT. |
| `qualify_frequency` | int | No | `60` | SIP OPTIONS ping seconds; `0` disables. |
| `phone_numbers[]` | array | No | `[]` | Optional initial DIDs at create time. |

## Troubleshooting

### Inbound call connects but one-way / no audio

Most common cause: **SRTP mismatch** between Bolna and carrier.

- Carrier has SRTP disabled but `media_encryption: "sdes"` on Bolna → set `media_encryption: "no"`, or align the carrier.
- Quick test: `media_encryption_optimistic: true` falls back to clear RTP.
- Skip encryption entirely until call setup works: `transport-udp` + `media_encryption: "no"`.

### `422 media_encryption='sdes' requires transport='transport-tls'`

SDES keys travel inside SDP and need encrypted signaling. Either:

- Switch `transport` to `transport-tls` (and `port: 5061` on gateways), or
- Set `media_encryption: "no"`.

### Outbound INVITE rings forever / silently fails on one carrier

UDP fragmentation. The carrier puts big headers on the INVITE (long `Diversion`, multiple `Route`, `P-Asserted-Identity`) and the UDP packet exceeds MTU.

Fix: `transport: "transport-tcp"`. You don't need TLS — TCP alone avoids the fragmentation.

### No inbound calls arrive at all

Walk these in order:

1. Origination URI on the carrier set to `sip:sip.bolna.ai:5060` (or `:5061;transport=tls`)?
2. DID added to the trunk via `POST /sip-trunks/trunks/{id}/numbers`?
3. `inbound_enabled: true` on the trunk?
4. DID mapped to an agent via `POST /inbound/setup`?
5. Bolna IP `13.200.45.61` whitelisted on the carrier?
6. INVITE's `Request-URI` or `To` header matches your stored number format (with/without `+`)?

### `from_phone_number` rejected on outbound

- `from_phone_number` must be a DID registered on the trunk (`/sip-trunks/trunks/{id}/numbers`).
- Agent's `telephony_provider` must be patched to `sip-trunk`.
- `is_active: true` on the trunk.
- Some carriers reject leading `+` on dialed numbers — flip `outbound_leading_plus_enabled` to match.

### Authentication fails on `userpass`

Re-check the SIP creds in your carrier's portal — they're separate from your account creds. Twilio Elastic SIP uses a "Credential List" specifically for SIP REGISTER auth.

## Safety

Deleting a trunk removes its gateways, IP identifiers, and number mappings in cascade. Active inbound and outbound stops working immediately. Always confirm with the user before `DELETE /sip-trunks/trunks/{id}`.

## Going deeper

| File | Contents |
|---|---|
| `references/twilio-elastic.md` | End-to-end Twilio Elastic SIP setup with the exact carrier-side screens. |
| `references/plivo-zentrunk.md` | Plivo Zentrunk setup including ip_identifiers. |
| `scripts/create_sip_trunk.py` | Wraps `POST /sip-trunks/trunks`. |
| `scripts/add_trunk_number.py` | Wraps `POST /sip-trunks/trunks/{id}/numbers`. |
| `scripts/diagnose_trunk.py` | Reads back the trunk + numbers + active mappings for triage. |

## See also

- `setup-inbound` — DID-to-agent mapping (covers Bolna-hosted and SIP-trunk DIDs the same way).
- `make-call` — outbound API; works identically once `telephony_provider` is `sip-trunk`.
- `manage-phone-numbers` — Bolna-hosted DIDs (alternative to BYOT).
- `../references/india-compliance.md` — DLT requirements still apply to your numbers, even on your own trunk.

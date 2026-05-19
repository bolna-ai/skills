# Plivo Zentrunk — End-to-End

Plivo Zentrunk uses **IP-based authentication** by default (no SIP REGISTER username/password). The pattern is: Bolna IP whitelisted in Zentrunk, Plivo's egress IPs registered on Bolna's trunk.

## Prerequisites

- Plivo account with Zentrunk enabled.
- At least one Plivo number ready to map.
- Bolna account with SIP trunking access (enterprise beta).

## On Plivo (Zentrunk console)

### 1. Create an outbound trunk

Plivo → **Zentrunk** → **Outbound Trunks** → **Add**.

- **Friendly name**: e.g. `Bolna Outbound`.
- **Authentication**: IP.
- **Allowed IPs**: add `13.200.45.61`.

Save. Plivo gives you a **trunk URI**, typically of the form `<digits>.zt.plivo.com`. Save it.

### 2. Create an inbound trunk

Plivo → **Zentrunk** → **Inbound Trunks** → **Add**.

- **Friendly name**: e.g. `Bolna Inbound`.
- **Primary URI**: `sip:sip.bolna.ai:5060` (UDP/TCP) or `sip:sip.bolna.ai:5061;transport=tls` (TLS).

Save.

### 3. Attach phone numbers

For each Plivo number you want on this trunk:

Plivo → **Numbers** → click a number → set **Application Type** to **Zentrunk inbound** and pick the inbound trunk you just created.

### 4. Note Plivo's egress IP ranges

Plivo's docs list egress IP ranges for each region. They look like:

```
15.207.90.192/31
204.89.151.128/27
13.52.9.0/25
```

Check Plivo's current list at the time of setup — they update occasionally.

## On Bolna

### Create the trunk

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
    "allow": "ulaw,alaw",
    "disallow": "all",
    "inbound_enabled": true,
    "outbound_leading_plus_enabled": true
  }'
```

Update `ip_identifiers` to match the regions you're using.

### Register DIDs

```bash
curl -X POST "https://api.bolna.ai/sip-trunks/trunks/$TRUNK_ID/numbers" \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "phone_number": "+919876543210", "name": "Mumbai Sales" }'
```

### Wire to agents

Inbound mapping + agent outbound patching are identical to the Twilio flow — see `setup-sip-trunk/references/twilio-elastic.md` or `setup-sip-trunk/SKILL.md`.

## Plivo-specific notes

- **Number format**: Plivo Zentrunk typically uses numbers **without** leading `+`. Set `outbound_leading_plus_enabled: false` if outbound dials fail with "invalid number" on Plivo.
- **India 160-series numbers**: provisioned via Plivo. Plivo Zentrunk + Bolna is the standard path for transactional / service calls in India. See `../../references/india-compliance.md` for the DLT process.
- **Ambient noise** (`task_config.ambient_noise_track`): supported on Plivo for the *hosted* telephony path, but if you're routing via your own Zentrunk it depends on the call path — test in a lower environment first.
- **Voicemail detection**: works on Plivo-hosted calls. Behaviour with Zentrunk + Bolna is the same as IP carriers — test in staging.

## Common Plivo-specific issues

| Issue | Cause | Fix |
|---|---|---|
| `403` from Bolna on inbound | Bolna IP not in Plivo's allowed IPs for the outbound trunk | Re-check Plivo Zentrunk → Outbound Trunk → Allowed IPs includes `13.200.45.61` |
| INVITE arrives at Bolna with wrong number format | Plivo sometimes strips `+` | Phone number lookup is `+`-tolerant on Bolna; if it still fails, normalise on the registration step |
| Some Plivo egress IPs miss our `ip_identifiers` | Plivo expanded their egress ranges | Refresh `ip_identifiers` from Plivo's current docs and `PATCH` the trunk |
| Long calls drop after exactly 60s | Plivo OPTIONS ping interval mismatch | Keep `qualify_frequency: 60` on Bolna; if Plivo's keep-alive is more aggressive, tighten further |
| Outbound rejected: `invalid from` | Number registered with leading `+` on Bolna but Plivo expects no `+` | Set `outbound_leading_plus_enabled: false` |

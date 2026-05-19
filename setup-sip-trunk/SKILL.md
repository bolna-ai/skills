---
name: setup-sip-trunk
description: "Create and manage Bolna SIP trunks for bring-your-own-telephony, including gateways, IP identifiers, inbound and outbound enablement, trunk phone numbers, agent mapping, and troubleshooting Twilio or Plivo SIP routing. Use for BYOT and enterprise telephony."
license: MIT
compatibility: "Requires SIP trunk access and BOLNA_API_KEY."
---

# Setup Bolna SIP Trunk

## Important status

Bolna SIP trunking is documented as beta and may require enterprise access. If API calls return access errors, tell the user to contact Bolna or their account owner before changing code.

## Endpoints

- Create trunk: `POST https://api.bolna.ai/sip-trunks/trunks`
- List trunks: `GET https://api.bolna.ai/sip-trunks/trunks`
- Get trunk: `GET https://api.bolna.ai/sip-trunks/trunks/{trunk_id}`
- Patch trunk: `PATCH https://api.bolna.ai/sip-trunks/trunks/{trunk_id}`
- Delete trunk: `DELETE https://api.bolna.ai/sip-trunks/trunks/{trunk_id}`
- Add trunk number: `POST https://api.bolna.ai/sip-trunks/trunks/{trunk_id}/numbers`
- List trunk numbers: `GET https://api.bolna.ai/sip-trunks/trunks/{trunk_id}/numbers`
- Remove trunk number: `DELETE https://api.bolna.ai/sip-trunks/trunks/{trunk_id}/numbers/{phone_number_id}`

## BYOT flow

1. Create the trunk in the telephony provider, usually Twilio Elastic SIP Trunking or Plivo Zentrunk.
2. Configure provider origination to Bolna's SIP endpoint shown in Bolna docs, commonly `sip:13.200.45.61:5060`.
3. Create the trunk in Bolna with gateway and IP identifier settings.
4. Add DID phone numbers to the Bolna trunk.
5. For inbound, map each trunk phone number to an agent with `setup-inbound`.
6. For outbound, use that number as `from_phone_number` in `make-call` after the agent telephony provider is set appropriately.

## Agent setup

Patch the agent when switching it to SIP trunk telephony:

```bash
curl --request PATCH \
  --url "https://api.bolna.ai/v2/agent/$AGENT_ID" \
  --header "Authorization: Bearer $BOLNA_API_KEY" \
  --header "Content-Type: application/json" \
  --data '{"agent_config":{"telephony_provider":"sip-trunk"}}'
```

Inbound SIP calls may require `ulaw` audio format; Bolna can update mapping automatically for trunk-routed numbers.

## Troubleshooting

- No inbound calls arrive: check provider origination URI, trunk inbound enabled flag, and whether the DID was added to the trunk.
- Call rejected: check DID format, trunk registration, agent mapping, and account beta access.
- No audio: disable SRTP if unsupported, check codec allow-list, and enable symmetric RTP where required.
- Outbound fails: confirm the trunk supports outbound, the DID is on the trunk, and `from_phone_number` matches a registered number.

## Safety

Deleting a trunk can remove associated gateways, IP identifiers, and number mappings. Confirm before deletion.

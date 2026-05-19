---
name: manage-phone-numbers
description: "Search, buy, list, and delete Bolna-hosted phone numbers (DIDs). Covers US (Twilio) and India (Plivo, Vobiz) regions; pattern / region filtering; `$5/month` flat pricing; the buy → inbound-setup wiring; and India regulated 140/160-series compliance prerequisites. Use when the user wants to purchase a dedicated outbound caller ID, set up an inbound line, inspect their DID inventory, or understand which Indian region/provider to pick. For SIP-trunk DIDs (BYOT), use `setup-sip-trunk` instead."
license: MIT
compatibility: Requires internet access and a Bolna API key (BOLNA_API_KEY).
metadata:
  openclaw:
    requires:
      env:
        - BOLNA_API_KEY
    primaryEnv: BOLNA_API_KEY
---

# Bolna Phone Numbers

Buy, list, and manage dedicated DIDs through Bolna. US numbers come from Twilio; Indian numbers from Plivo (Karnataka, Maharashtra) or Vobiz (Karnataka, Gujarat, NCR). Flat `$5/month` rental per number, billed from the wallet.

For numbers you bring on your own SIP trunk (Twilio Elastic, Plivo Zentrunk, Telnyx, etc.), see `setup-sip-trunk`.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/phone-numbers/all` | List all numbers in your account |
| `GET` | `/phone-numbers/search` | Search available numbers to buy (filter by country, pattern, region) |
| `POST` | `/phone-numbers/buy` | Purchase a number |
| `DELETE` | `/phone-numbers/{phone_number_id}` | Delete (stops inbound routing + monthly rent) |

Auth: `Authorization: Bearer $BOLNA_API_KEY`.

## What you can do with a Bolna-hosted number

| Action | How |
|---|---|
| Outbound caller ID | Pass the number as `from_phone_number` to `POST /call` (see `make-call`). |
| Inbound agent routing | Map to an agent via `POST /inbound/setup` (see `setup-inbound`). |
| Batch outbound | Pass as one of the `from_phone_numbers` to `POST /batches` (see `create-batch`). |

## List your numbers

```bash
curl https://api.bolna.ai/phone-numbers/all \
  -H "Authorization: Bearer $BOLNA_API_KEY"
```

Important fields on each response item:

| Field | What it means |
|---|---|
| `id` | Phone-number UUID. Use this for `setup-inbound` and `DELETE`. |
| `phone_number` | E.164 number. |
| `agent_id` | UUID of the inbound agent if mapped, else `null`. |
| `price` | Monthly rental. `$5.0` for Bolna-hosted. |
| `telephony_provider` | `twilio` / `plivo` / `vobiz`. |
| `rented` | `true` if rented via Bolna; `false` for BYOT / connected provider. |
| `created_at` / `renewal_at` | Lifecycle dates. |

## Search before buying

```bash
# US numbers in the 718 area code
curl "https://api.bolna.ai/phone-numbers/search?country=US&pattern=718" \
  -H "Authorization: Bearer $BOLNA_API_KEY"

# India - Plivo - Karnataka (80)
curl "https://api.bolna.ai/phone-numbers/search?country=IN&provider=plivo&region=80" \
  -H "Authorization: Bearer $BOLNA_API_KEY"

# India - Vobiz - NCR (11)
curl "https://api.bolna.ai/phone-numbers/search?country=IN&provider=vobiz&region=11" \
  -H "Authorization: Bearer $BOLNA_API_KEY"
```

### Region codes

| Country | Provider | Region | Code |
|---|---|---|---|
| India | Plivo | Karnataka | `80` |
| India | Plivo | Maharashtra | `22` |
| India | Vobiz | Karnataka | `80` |
| India | Vobiz | Gujarat | `79` |
| India | Vobiz | NCR (Delhi) | `11` |

US numbers don't have a region filter — use `pattern` (area code prefix) instead.

## Buy

```bash
curl -X POST https://api.bolna.ai/phone-numbers/buy \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "country": "US",
    "phone_number": "+17182718146",
    "provider": "twilio"
  }'
```

For India:

```bash
curl -X POST https://api.bolna.ai/phone-numbers/buy \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "country": "IN",
    "phone_number": "+918012345678",
    "provider": "plivo"
  }'
```

Response includes the new `id` — save it for inbound mapping.

## After purchase — wire to an inbound agent

```bash
curl -X POST https://api.bolna.ai/inbound/setup \
  -H "Authorization: Bearer $BOLNA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "'$AGENT_ID'",
    "phone_number_id": "'$PHONE_NUMBER_ID'"
  }'
```

(Full detail in `setup-inbound/SKILL.md`.)

## Pricing

- **$5/month per number**, charged to your wallet on `renewal_at`.
- **Call charges are separate** — per-minute telephony costs (Twilio/Plivo/Vobiz) plus Bolna's platform fee.
- The wallet runs the show — if it's low, `POST /call` will land in `balance-low`. Check with `GET /user/me`.

## India: 140 / 160-series numbers

These are **not** ordinary numbers. Selling commercial calls in India requires:

| Series | Use case | Compliance |
|---|---|---|
| 140-series | Promotional / telemarketing | DLT registration via TATA Teleservices portal, KYC, ₹5,900 payment, PE ID, TM ID |
| 160-series | Transactional / service (BFSI, alerts) | DLT + Header registration (RBI/SEBI cert) + Template registration |

Plan **2-4 weeks** to go live. Full process in `../references/india-compliance.md`.

You **cannot** buy 140/160 numbers through `/phone-numbers/buy` without completing compliance first — the carrier rejects the allocation. Surface this prerequisite up front when a user asks for Indian regulated numbers.

## Delete

```bash
curl -X DELETE "https://api.bolna.ai/phone-numbers/$PHONE_NUMBER_ID" \
  -H "Authorization: Bearer $BOLNA_API_KEY"
```

Deletion:
- Stops inbound routing immediately (if mapped).
- Stops the $5/month rent at next renewal.
- Cannot be undone — you'd need to buy a new number.

Always confirm with the user before deleting, especially if the number is mapped to an active inbound agent (`agent_id` non-null in the list response).

## Bolna-hosted vs your own provider

| Approach | Pros | Cons |
|---|---|---|
| **Bolna-hosted DID** | Instant setup; one bill; supports inbound and outbound | Limited country/region selection |
| **Your own provider** (Twilio / Plivo / Vobiz / Exotel) | Use existing numbers, negotiated rates | Need to connect provider, manage two billing surfaces |
| **SIP Trunk (BYOT)** | Reuse trunks, regulated numbers from any carrier | Beta; needs ops setup |

For each, the `setup-inbound` flow is the same once a `phone_number_id` exists.

## Going deeper

| File | Contents |
|---|---|
| `scripts/search_numbers.py` | Wraps `GET /phone-numbers/search` with country/region/pattern flags. |
| `scripts/buy_number.py` | Wraps `POST /phone-numbers/buy`. |
| `scripts/list_numbers.py` | Wraps `GET /phone-numbers/all`. |
| `../references/india-compliance.md` | Full DLT process for 140 / 160-series. |

## See also

- `setup-inbound` — map a purchased number to an agent.
- `make-call` — use a number as `from_phone_number` for outbound.
- `setup-sip-trunk` — for BYOT trunks (different lifecycle, separate endpoints).
- `add-provider` — to connect your own Twilio/Plivo/Vobiz/Exotel and use their numbers.

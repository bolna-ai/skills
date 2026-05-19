---
name: manage-phone-numbers
description: "Search, buy, list, and delete Bolna phone numbers for outbound caller ID and inbound agent routing. Use when the user needs a dedicated DID, wants to inspect phone number inventory, connect numbers to agents, or handle India 140 and 160 series compliance."
license: MIT
---

# Manage Bolna Phone Numbers

## Endpoints

- List numbers: `GET https://api.bolna.ai/phone-numbers/all`
- Search numbers: `GET https://api.bolna.ai/phone-numbers/search`
- Buy number: `POST https://api.bolna.ai/phone-numbers/buy`
- Delete number: `DELETE https://api.bolna.ai/phone-numbers/{phone_number_id}`

Use `Authorization: Bearer $BOLNA_API_KEY`.

## List numbers

```bash
curl --request GET \
  --url https://api.bolna.ai/phone-numbers/all \
  --header "Authorization: Bearer $BOLNA_API_KEY"
```

Important fields:

- `id`: phone number ID for inbound mapping.
- `phone_number`: E.164 number.
- `agent_id`: associated inbound agent, if any.
- `price`: monthly rental price.
- `telephony_provider`: common values include `twilio`, `plivo`, and `vonage`.
- `rented`: whether it was bought through Bolna.

## Search before buying

Use search filters such as country, region, locality, or pattern where supported by the API. Show price to the user before buying.

```bash
curl --request GET \
  --url "https://api.bolna.ai/phone-numbers/search?country=US" \
  --header "Authorization: Bearer $BOLNA_API_KEY"
```

## Buy

```bash
curl --request POST \
  --url https://api.bolna.ai/phone-numbers/buy \
  --header "Authorization: Bearer $BOLNA_API_KEY" \
  --header "Content-Type: application/json" \
  --data '{
    "country": "US",
    "phone_number": "+19876543210",
    "provider": "twilio"
  }'
```

## Connect to an inbound agent

After purchase, use `setup-inbound` with the returned phone number `id`:

```json
{
  "agent_id": "agent-uuid",
  "phone_number_id": "phone-number-id"
}
```

## India compliance

For India regulated 140 and 160 series numbers, do not treat purchase as a normal instant DID flow. The user may need DLT registration, KYC, CIN, GST, and Bolna compliance review before provisioning. Point them to Bolna's phone number compliance docs before attempting purchase.

## Deletion

Deleting a number can stop inbound routing and billing for that number. Confirm before calling the delete endpoint.

```bash
curl --request DELETE \
  --url "https://api.bolna.ai/phone-numbers/$PHONE_NUMBER_ID" \
  --header "Authorization: Bearer $BOLNA_API_KEY"
```

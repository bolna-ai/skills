---
name: create-batch
description: "Create, schedule, monitor, stop, and delete Bolna batch calling campaigns using CSV recipients and per-recipient dynamic variables. Use for bulk outreach, surveys, collections, reminders, sales, support callbacks, and campaign execution."
license: MIT
---

# Create Bolna Batch Campaigns

## Endpoints

- Create batch: `POST https://api.bolna.ai/batches`
- Schedule batch: `POST https://api.bolna.ai/batches/{batch_id}/schedule`
- Stop batch: `POST https://api.bolna.ai/batches/{batch_id}/stop`
- Get batch: `GET https://api.bolna.ai/batches/{batch_id}`
- List batches for agent: `GET https://api.bolna.ai/batches/{agent_id}/all`
- List batch executions: `GET https://api.bolna.ai/batches/{batch_id}/executions`
- Delete batch: `DELETE https://api.bolna.ai/batches/{batch_id}`

## CSV format

The CSV must include recipient phone numbers and any variables referenced by the agent prompt.

```csv
contact_number,customer_name,plan
+919876543210,Amitesh,Pro
+918765432109,Riya,Starter
```

If the agent prompt says `{customer_name}` or `{plan}`, the CSV needs matching columns.
Use `contact_number` for the recipient number header. Bolna validates that column and passes the other columns through as custom variables.

## Create batch

Use multipart form upload.

```bash
curl --location https://api.bolna.ai/batches \
  --header "Authorization: Bearer $BOLNA_API_KEY" \
  --form 'agent_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"' \
  --form 'file=@"/path/to/recipients.csv"' \
  --form 'from_phone_numbers="+919876543210"' \
  --form 'from_phone_numbers="+919876543211"'
```

Optional retry config is a JSON string:

```bash
--form 'retry_config={"enabled":true,"max_retries":2,"retry_intervals_minutes":[15,30]}'
```

Expected response:

```json
{
  "batch_id": "3c90c3cc0d444b5088888dd25736052a",
  "state": "created"
}
```

## Schedule batch

```bash
curl --location "https://api.bolna.ai/batches/$BATCH_ID/schedule" \
  --header "Authorization: Bearer $BOLNA_API_KEY" \
  --form 'scheduled_at="2026-05-19T18:30:00+05:30"' \
  --form 'bypass_call_guardrails=false'
```

Always include timezone in `scheduled_at`.

## Monitor

```bash
curl --request GET \
  --url "https://api.bolna.ai/batches/$BATCH_ID" \
  --header "Authorization: Bearer $BOLNA_API_KEY"
```

Use execution counts and statuses to track completion. For per-call transcript, cost, recording, and extracted data, list batch executions.

## Stop and delete

Stopping a batch halts its remaining queued work. Deleting a batch removes it from batch management. Confirm the user's intent before either operation.

## Asset

Use `assets/sample_recipients.csv` as a starter template.

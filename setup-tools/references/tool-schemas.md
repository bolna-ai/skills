# Bolna Tool Schema Examples

## Custom HTTP lookup

Use this when the caller provides an account identifier and the agent needs backend context.

```json
{
  "name": "lookup_customer",
  "description": "Call this only after the caller provides a phone number or customer ID and asks about their account.",
  "parameters": {
    "type": "object",
    "properties": {
      "customer_id": {
        "type": "string",
        "description": "Customer ID or phone number supplied by the caller."
      }
    },
    "required": ["customer_id"]
  }
}
```

Tool params should point to your backend:

```json
{
  "method": "GET",
  "url": "https://api.example.com/customers",
  "headers": {
    "Authorization": "Bearer YOUR_BACKEND_TOKEN"
  },
  "query": {
    "customer_id": "%(customer_id)s"
  }
}
```

## Transfer call

Use when the caller asks for a human, escalation conditions are met, or the workflow requires a handoff.

```json
{
  "name": "transfer_to_human",
  "description": "Transfer the call when the caller explicitly asks for a human or the issue requires manual escalation.",
  "parameters": {
    "type": "object",
    "properties": {
      "reason": {
        "type": "string",
        "description": "Brief reason for handoff."
      }
    },
    "required": ["reason"]
  }
}
```

## Cal.com slot fetch

```json
{
  "name": "fetch_available_slots",
  "description": "Fetch available appointment slots after the caller gives a preferred date or time window.",
  "parameters": {
    "type": "object",
    "properties": {
      "date": {
        "type": "string",
        "description": "Preferred date in YYYY-MM-DD format."
      },
      "timezone": {
        "type": "string",
        "description": "Caller timezone, for example Asia/Kolkata."
      }
    },
    "required": ["date", "timezone"]
  }
}
```

## Cal.com booking

```json
{
  "name": "book_appointment",
  "description": "Book an appointment only after the caller confirms a specific slot.",
  "parameters": {
    "type": "object",
    "properties": {
      "slot": {"type": "string"},
      "name": {"type": "string"},
      "phone_number": {"type": "string"},
      "notes": {"type": "string"}
    },
    "required": ["slot", "name", "phone_number"]
  }
}
```

## Prompt instruction pattern

Add tool policy to the system prompt:

```text
If the caller asks to schedule, first gather date, time preference, name, and phone number.
Call fetch_available_slots once you have a date.
Read two available slots aloud.
Call book_appointment only after the caller confirms one slot.
After booking, summarize the confirmed time and end politely.
```

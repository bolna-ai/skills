# Tool Schema Reference

Full reference for the custom-function schema used in `api_tools.tools[]`. Bolna follows the [OpenAI function-calling spec](https://platform.openai.com/docs/guides/function-calling) plus its own extensions (`key`, `value`, `pre_call_message`) that tell Bolna how to actually execute the API call.

## Complete schema

```json
{
  "name": "function_name",
  "description": "Detailed description of when to call this function",
  "pre_call_message": "What agent says while the API is being called",
  "parameters": {
    "type": "object",
    "properties": {
      "param_name": { "type": "string", "description": "What this parameter represents" }
    },
    "required": ["param_name"]
  },
  "key": "custom_task",
  "value": {
    "method": "GET",
    "param": { "param_name": "%(param_name)s" },
    "url": "https://your-api.com/endpoint",
    "api_token": "Bearer your_token",
    "headers": {}
  }
}
```

| Field | Required | Notes |
|---|---|---|
| `name` | Yes | Unique identifier. `snake_case`. The LLM sees this as the tool name. |
| `description` | Yes | When to call the tool. The single most important field for triggering accuracy. |
| `parameters` | Yes | JSON Schema. Defines what the LLM collects. |
| `parameters.required` | Yes (array, can be empty) | Fields the LLM must collect before invoking. |
| `pre_call_message` | No | Spoken while the API runs. Add it whenever the call takes >500ms. |
| `key` | **Yes** | Must be `"custom_task"`. Identifies this as a Bolna custom function. |
| `value` | Yes | Bolna's API execution config (see below). |

## `value` (API execution config)

| Field | Required | Notes |
|---|---|---|
| `method` | Yes | `GET`, `POST`, `PUT`, `PATCH`, `DELETE`. |
| `url` | Yes | Endpoint URL. Supports `%(name)s` interpolation in path. |
| `param` | Yes | Maps LLM-collected parameters to the request. For `GET`: query string. For `POST`/`PUT`/`PATCH`: JSON body. |
| `api_token` | No | Value of the `Authorization` header, e.g. `Bearer XXX`. Bolna sends it as-is. |
| `headers` | No | Additional headers as key-value pairs. |

## Parameter data types

| `type` | Use for | Examples |
|---|---|---|
| `string` | Text, names, IDs, phones, dates | `"John Doe"`, `"ORD-12345"`, `"2026-05-22"` |
| `integer` | Whole numbers | `5`, `100`, `-10` |
| `number` | Decimals | `29.99`, `3.14` |
| `boolean` | Flags | `true`, `false` |

Prefer `string` for fields the API can parse loosely (dates, phones). Use typed numbers only when the API actually needs a JSON number.

## Format specifiers in `param`

Bolna substitutes parameters into `value.param` and `value.url` using Python-style format specifiers:

| Data type | Specifier | Example |
|---|---|---|
| String | `%(name)s` | `"customer_id": "%(customer_id)s"` |
| Integer | `%(name)i` | `"quantity": "%(quantity)i"` |
| Float | `%(name)f` | `"price": "%(price)f"` |

For `GET`, the values become query parameters. For `POST`/`PUT`/`PATCH`, they become a JSON body.

URL interpolation works the same way: `"url": "http://worldtimeapi.org/api/timezone/%(timezone)s"`.

## Required vs optional

| In `required` array? | LLM behaviour |
|---|---|
| Yes | Keeps asking until the user provides a value |
| No | Includes if mentioned, skips otherwise |

Don't over-require. If the API has a sensible default (e.g. priority = `medium`), drop the field from `required` so the LLM doesn't grill the caller for it.

## Auto-injected variables

Anything in `{braces}` in your **agent prompt** is in scope for tool parameters. If a tool parameter has the same name as a prompt variable, Bolna fills it automatically — the LLM does not ask.

| Variable | Source |
|---|---|
| `{agent_id}` | Bolna system |
| `{execution_id}` | Bolna system |
| `{call_sid}` | Telephony provider (Twilio, Plivo, etc.) |
| `{from_number}` | Caller (inbound) / agent (outbound) |
| `{to_number}` | Agent (inbound) / recipient (outbound) |
| `{current_date}`, `{current_time}`, `{timezone}` | Bolna system, timezone-aware |
| `{customer_name}`, `{order_id}`, ... | User variables from `user_data` or CSV row |

**Pattern**: put `{from_number}` in the agent prompt → set a tool parameter named `caller_phone` (mapped from `from_number`) → LLM auto-fills. Caller never has to repeat their phone number.

## Common failure modes

### Tool never triggers

The description doesn't match the caller's vocabulary. Add synonyms:

```diff
- "Use to check order status."
+ "Use when the caller asks about their order status, shipping, delivery,
+  tracking, ETA, or where their package is. Caller must provide an order ID."
```

### Tool triggers when it shouldn't

The description is too broad or overlaps with another tool. Add exclusions:

```diff
- "Use for any order-related question."
+ "Use ONLY for status/tracking. For refunds use `start_refund`. For
+  cancellations use `cancel_order`."
```

### Parameters arrive empty

Name mismatch between `parameters.properties` and `value.param`. Names are case-sensitive and must match exactly:

```diff
  "properties": { "orderId": ... }
  "param":      { "order_id": "%(order_id)s" }   ← won't match
```

### `415 Unsupported Media Type`

`POST` request missing `Content-Type: application/json`. Add it to `headers`:

```json
"headers": { "Content-Type": "application/json" }
```

### Auth keeps failing

`api_token` is the **header value**, not just the token. Include `Bearer `:

```json
"api_token": "Bearer sk_live_abc123"
```

### `%(name)s` shows up literally in the request

Parameter wasn't filled at runtime. Either the LLM didn't collect it (check it's in the conversation), or the name didn't match `properties`. Inspect `get-executions` raw logs to see the exact substituted payload.

## Two more worked examples

### GET with multiple parameters

```json
{
  "name": "get_account_balance",
  "description": "Use when the customer asks about their account balance, available credit, or account summary. Requires account ID and registered phone for verification.",
  "pre_call_message": "Let me pull up your account details.",
  "parameters": {
    "type": "object",
    "properties": {
      "account_id": { "type": "string", "description": "Customer's account ID, starts with ACC-" },
      "phone":      { "type": "string", "description": "Registered phone for verification" }
    },
    "required": ["account_id", "phone"]
  },
  "key": "custom_task",
  "value": {
    "method": "GET",
    "param": {
      "account_id": "%(account_id)s",
      "phone":      "%(phone)s"
    },
    "url": "https://api.yourbank.com/accounts/balance",
    "api_token": "Bearer fin_api_key_001",
    "headers": { "X-Request-Source": "voice-agent" }
  }
}
```

### POST with JSON body

```json
{
  "name": "book_appointment",
  "description": "Use when the caller wants to book or schedule an appointment. Collect name, preferred date (YYYY-MM-DD), time, and reason.",
  "pre_call_message": "I'm booking that appointment for you now.",
  "parameters": {
    "type": "object",
    "properties": {
      "patient_name":   { "type": "string", "description": "Full patient name" },
      "preferred_date": { "type": "string", "description": "Date in YYYY-MM-DD" },
      "preferred_time": { "type": "string", "description": "Time, e.g. 10:30 AM" },
      "reason":         { "type": "string", "description": "Brief reason. Optional." }
    },
    "required": ["patient_name", "preferred_date", "preferred_time"]
  },
  "key": "custom_task",
  "value": {
    "method": "POST",
    "param": {
      "patient_name":   "%(patient_name)s",
      "preferred_date": "%(preferred_date)s",
      "preferred_time": "%(preferred_time)s",
      "reason":         "%(reason)s"
    },
    "url": "https://api.yourclinic.com/v1/appointments",
    "api_token": "Bearer clinic_token_xyz",
    "headers": { "Content-Type": "application/json" }
  }
}
```

## Building tools from a `curl`

Bolna's dashboard has a **Generate from cURL** option — paste a working `curl` command and it auto-populates `name`, `description`, `method`, `url`, headers. Review the generated schema carefully:

- Rename to clear `snake_case`.
- Rewrite the description for *triggering* (when to call) not *function* (what it does).
- Trim parameters to those the caller would actually provide.
- Add `pre_call_message`.

Treat the output as a starting point, not the final schema.

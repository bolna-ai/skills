# World Time — Zero-Auth Custom Tool

A complete working example of a custom HTTP tool that needs no authentication. Useful as a template (URL-path interpolation, no `api_token`, optional parameters) and useful in practice (caller-aware time-zone answers).

Powered by [WorldTimeAPI](http://worldtimeapi.org).

## The schema

```json
{
  "name": "get_current_datetime",
  "description": "Fetches the current date and time for a specific timezone. Use when the caller asks for the time, especially if they mention a city, country, or region.",
  "pre_call_message": "Just a moment, I'm getting the local time for you.",
  "parameters": {
    "type": "object",
    "properties": {
      "timezone": {
        "type": "string",
        "description": "Timezone in 'Area/Location' format like 'America/New_York' or 'Europe/London'. If the caller doesn't specify a location, default to 'Etc/UTC'."
      }
    }
  },
  "key": "custom_task",
  "value": {
    "method": "GET",
    "param": {},
    "url": "http://worldtimeapi.org/api/timezone/%(timezone)s",
    "api_token": null,
    "headers": {}
  }
}
```

## What this demonstrates

| Feature | How |
|---|---|
| **Path interpolation** | `url` contains `%(timezone)s`. Bolna substitutes the parameter into the URL itself, not the query string. |
| **Empty `param`** | The query payload is `{}` because the value goes into the path. |
| **No auth** | `api_token: null` and `headers: {}` — Bolna sends no Authorization header. |
| **Optional parameter with default in description** | `timezone` is not in `required`. The description tells the LLM to default to `Etc/UTC`. |

## Conversation example

```
Caller: "Hey, what time is it in Tokyo right now?"
Agent:  "Just a moment, I'm getting the local time for you."
        [get_current_datetime(timezone="Asia/Tokyo")]
Agent:  "It's currently 11:42 PM on Tuesday in Tokyo. Anything else?"
```

## Adapting this template to your own no-auth API

Many internal services use path parameters and no auth (behind a VPN or internal-only):

```json
"url": "https://internal.example.com/users/%(user_id)s/orders/latest"
```

Pair with a different field interpolated into the query:

```json
"value": {
  "method": "GET",
  "param": { "fields": "%(fields)s" },
  "url": "https://internal.example.com/users/%(user_id)s/orders/latest",
  "api_token": null,
  "headers": {}
}
```

Bolna will resolve both: `%(user_id)s` in the URL path, `%(fields)s` in the query string.

## Timezone format

WorldTimeAPI uses the [tz database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) format: `Area/Location`. Examples:

- `America/New_York`
- `America/Los_Angeles`
- `Europe/London`
- `Asia/Kolkata`
- `Asia/Tokyo`
- `Australia/Sydney`
- `Etc/UTC`

Full list at `http://worldtimeapi.org/timezones`.

## Caveats

- WorldTimeAPI is a free public service — no SLA. Don't rely on it for billing-grade timestamps.
- Bolna already exposes `{current_date}`, `{current_time}`, and `{timezone}` as auto-injected variables. If you only need the *caller's* timezone (not a third location), use those instead — they're zero-latency and zero-cost.
- Reach for this tool when the caller asks about times in a *different* place from where they are. ("It's 3pm here, but what time is it in London?")

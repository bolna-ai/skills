# Call Statuses

Every Bolna execution carries a `status` field. The webhook fires each time the status changes; `GET /executions/{id}` returns the latest.

## Lifecycle

```
scheduled → queued → initiated → ringing → in-progress → call-disconnected → completed
                                      ↘ no-answer / busy
```

`completed` is the **terminal** status — it fires after recordings, transcripts, and extractions have finished post-processing (~2-3 minutes after disconnect). Don't treat `call-disconnected` as terminal; extracted data won't be available yet.

## Successful path

| Status | Meaning |
|---|---|
| `scheduled` | Waiting for `scheduled_at` to elapse. |
| `queued` | Bolna accepted the call and queued it. |
| `rescheduled` | Outside calling guardrails — auto-rescheduled to the next allowed window. |
| `initiated` | Call leaving Bolna's servers. |
| `ringing` | Ringing at destination. |
| `in-progress` | Answered, conversation active. |
| `call-disconnected` | Audio path ended. Post-processing still running. |
| `completed` | All post-processing finished. Recording URL, transcript, extractions available. |

## Unanswered

| Status | Meaning |
|---|---|
| `busy` | Callee was busy. |
| `no-answer` | Rang but not picked up. |
| `balance-low` | Account wallet too low to initiate. |

## Failed

| Status | Meaning |
|---|---|
| `canceled` | Cancelled via `POST /call/{id}/stop` or manually. |
| `failed` | Couldn't connect. Check `error_message`. |
| `stopped` | Telephony provider didn't respond or call was force-stopped. |
| `error` | Internal error while placing the call. `error_message` has the detail. |

## Programmatic patterns

**Wait for terminal status (poll):**

```python
TERMINAL = {"completed", "canceled", "failed", "stopped", "error", "balance-low",
            "busy", "no-answer"}

while True:
    ex = get_execution(execution_id)
    if ex["status"] in TERMINAL:
        return ex
    time.sleep(5)
```

Prefer the webhook over polling — `POST /call` returns immediately, and the webhook fires on every status transition. Polling burns rate-limit budget.

**Retry-eligible failures:**

```python
RETRY_STATUSES = {"no-answer", "busy", "failed", "error"}
```

This matches `retry_config.retry_on_statuses` defaults on `POST /call`. Add `voicemail` if `retry_on_voicemail: true`.

**Successful-conversation filter** (for analytics):

```python
def was_real_conversation(ex):
    return ex["status"] == "completed" and ex["conversation_duration"] >= 5
```

A `completed` status with zero conversation duration usually means the call was answered, the agent spoke, and the callee hung up immediately. Filter on duration to exclude those from conversion analytics.

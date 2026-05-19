# Hangup Codes

Every terminated call records three fields on `telephony_data` and `transfer_call_data`:

| Field | What it tells you |
|---|---|
| `hangup_by` | Who/what initiated the disconnect (`Caller`, `Callee`, `Carrier`, `Error`, `API Request`, `Plivo`, `Unknown`). |
| `hangup_code` | Numeric code from the telecom provider. |
| `hangup_reason` | Human-readable reason. |

Code `4000` is ambiguous on its own — it appears under `API Request`, `Caller`, and `Callee`. Always combine `hangup_code` with `hangup_by` *and* `call_type` (`inbound` vs `outbound`) to interpret correctly.

## Provider codes by `hangup_by`

| `hangup_by` | Codes |
|---|---|
| `API Request` | `4000`, `4020` |
| `Callee` (outbound calls) | `3020`, `4000` |
| `Caller` (inbound calls) | `4000` |
| `Carrier` | `2000`, `3000`, `3010`, `3020`, `3040`, `3050`, `3070` |
| `Error` | `3080`, `3090`, `3110`, `5010`, `5020`, `7011`, `8011` |
| `Plivo` | `1010`, `4010`, `5020`, `6000`, `6010`, `6020` |
| `Unknown` | `0` |

## Bolna-side hangup reasons

Bolna emits these when the agent itself terminated the call:

| Reason | What triggered it |
|---|---|
| `inactivity_timeout` | `task_config.hangup_after_silence` exceeded. |
| `llm_prompted_hangup` | Agent decided to hang up based on the prompt (e.g. "if user says bye, hang up"). |

## Carrier-side hangup reasons

These come from the telephony provider:

| Reason | Meaning |
|---|---|
| `Call recipient was busy` | Busy signal. |
| `Call unanswered` | Rang through to timeout. |
| `Call recipient number invalid` | Invalid / unreachable / unallocated. |
| `Call recipient hung up` | Callee disconnected. |
| `Carrier declined` | Carrier refused to route. |
| `Call recipient rejected` | Callee actively rejected. |
| `failed` | Could not initiate. |
| `Carrier ended because call limit exceeded` | Duration limit hit. |
| `Bolna Error` | Internal Bolna issue. |
| `Carrier unable to receive media` | RTP / media gateway problem. |
| `Network Congestion From Carrier` | Network congestion. |
| `End of inputs from Bolna` | Conversation finished normally (no explicit goodbye prompt). |
| `Carrier unable to reach bolna` | Carrier-side connectivity to Bolna. |
| `Carrier ended call because MPC duration limit exceeded` | Multi-party-call duration limit. |
| `Telephony Internal Error` | Telephony stack error. |
| `Carrier Internal Error` | Carrier-internal error. |
| `Call completed` | Normal completion. |
| `Call canceled` | Cancelled. |
| `Call ended` | Normal termination. |
| `Call timed out` | Exceeded timeout. |
| `Unknown` | Unknown. |

## Patterns to watch

- **Regional carrier issues**: a cluster of `3010` or `3050` from one region (e.g. India Tier-2 cities) usually means a local routing/coverage problem with that provider. Contact support and consider provider failover.
- **`Carrier unable to receive media`** spiking: investigate audio codec mismatch or NAT/firewall on your SIP trunk if BYOT.
- **`End of inputs from Bolna`**: not an error — the conversation finished but the prompt didn't explicitly hang up. Add a goodbye line if you want a cleaner reason on records.
- **`llm_prompted_hangup` on healthy conversations**: prompt is hanging up too aggressively. Loosen the hangup condition.

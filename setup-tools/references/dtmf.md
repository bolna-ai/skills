# DTMF (Keypad Input)

DTMF lets callers type digits on their phone keypad and have the agent respond to them like spoken input. Useful when typing is faster, safer, or more accurate than speech.

## When to use it

| Good fit | Better alternative |
|---|---|
| 4-6 digit OTP / PIN | — |
| Account or order number lookup (long digit strings) | — |
| Phone number capture (avoids STT errors on digits) | — |
| Sensitive input (caller doesn't want to say it aloud) | — |
| Yes/no confirmation ("press 1 to confirm, 2 to cancel") | — |
| Menu navigation ("press 1 for sales, 2 for support") | Use Bolna's **IVR** feature — no LLM cost per turn |

## Telephony support

| Provider | DTMF |
|---|---|
| Plivo | Yes |
| Twilio | Yes |
| Exotel | Not supported |
| Vobiz | Not supported |
| SIP Trunk (BYOT) | Not supported |

## Enabling DTMF

### Dashboard

Agent → Call Tab → toggle **Keypad Input (DTMF)** on.

### API

Set `dtmf_enabled: true` on the conversation task's `task_config`:

```json
{
  "tasks": [
    {
      "task_config": {
        "dtmf_enabled": true,
        "hangup_after_silence": 10,
        "call_terminate": 600
      }
    }
  ]
}
```

## How it works

1. The agent asks the caller to enter digits, terminated by `#`.
2. The caller presses keys.
3. Bolna accumulates digits until `#` is pressed.
4. Bolna delivers the digits to the LLM as a synthetic user turn: `dtmf_number: <digits>` (the `#` itself is not included).
5. The agent responds based on what it sees.

## Prompt template

```
PHONE NUMBER CAPTURE:
When you need the caller's phone number, say exactly:
"Please enter your phone number on your keypad and press the hash key when you're done."

INPUT HANDLING:
When you receive a message starting with "dtmf_number:", the digits that follow are
what the caller pressed.

- Read the number back digit-by-digit to confirm.
- If correct, proceed to the next step.
- If they say it's wrong, ask them to enter again.

EXAMPLE INPUT FROM CALLER:
dtmf_number: 9876543210

EXAMPLE AGENT REPLY:
"I got 9-8-7-6-5-4-3-2-1-0. Is that correct?"
```

## Mixed speech + DTMF

DTMF doesn't replace speech — both work simultaneously. The caller can speak freely between digit entries. Useful patterns:

- "Could you tell me what you're calling about, and once we're done you can enter your callback number on the keypad."
- "I need your 6-digit OTP. You can either say it or type it on your keypad followed by the hash key — whichever's easier."

## Confirmation flow

```
Agent: "Press 1 to confirm, or 2 to cancel."
Caller: [presses 1]
Bolna delivers: dtmf_number: 1
Agent: "Confirmed. Booking your appointment now."
```

Note the agent gets `dtmf_number: 1` even for a single digit — the caller still has to press `#` to terminate. If that feels unnatural for single-digit choices, instruct callers explicitly: *"...followed by the hash key."*

## Combining with custom tools

DTMF output is just another user turn from the LLM's perspective. Use it as input to a custom tool:

```
Agent: "Please enter your 8-digit account number and press hash."
Caller: [enters 12345678 + #]
Bolna delivers: dtmf_number: 12345678
Agent calls lookup_account(account_id="12345678")
```

The LLM does the substitution automatically — there's no special syntax needed.

## Limitations and gotchas

- **Single-digit input still needs `#`** — design your prompt around that or expect callers to time out.
- **No silent-DTMF event** — there's no separate notification when DTMF arrives vs spoken input; both look like text user turns.
- **Don't combine DTMF and IVR** for the same role. Use IVR for menu routing, DTMF for content (numbers).
- **Telephony provider matters** — Exotel, Vobiz, and SIP-BYOT customers can't use DTMF as of now. Plan a speech fallback if your provider mix changes.

## See also

- `setup-inbound` — for IVR menu setups (different feature, no LLM per turn).
- `setup-tools/references/tool-schemas.md` — for piping DTMF input into a custom API tool.
- `prompt-writing` — for the procedural prompt language that makes DTMF feel natural.

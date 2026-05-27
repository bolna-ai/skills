# task_config — Every Field

The `task_config` block on a conversation task controls latency, interruption, voicemail, silence handling, inbound limits, and noise suppression. Most defaults are sensible. Change a field when you have a specific reason — random tuning makes calls feel worse, not better.

## Latency and turn-taking

| Field | Default | Use case |
|---|---|---|
| `incremental_delay` | `400` (ms) | Delay before the agent commits to speaking. **Lower** for faster turn-taking (risk: agent interrupts itself on partial transcripts). **Higher** for noisy lines. |
| `number_of_words_for_interruption` | `2` | How many user words trigger the agent to stop talking. **1** = very responsive. **4-5** = "let the user finish a sentence." |
| `interruption_backoff_period` | `0` (ms) | Cooldown after the agent is interrupted before it tries to speak again. Bump to `100-200` if the agent keeps interrupting itself. |
| `optimize_latency` | `true` | Latency-optimized routing across providers. Leave `true` unless you have a specific reason. |

## Silence and presence

| Field | Default | Use case |
|---|---|---|
| `hangup_after_silence` | `10` (sec) | User silence before the call hangs up. **Lower** for IVR-style flows. **Higher** for thoughtful audiences (BFSI, healthcare, elderly callers). |
| `check_if_user_online` | `false` | Toggle the "Are you still there?" probe. |
| `check_user_online_message` | string or dict | What to say when the probe fires. Accepts a dict keyed by language code for multilingual. |
| `trigger_user_online_message_after` | `10` (sec) | Silence before the probe fires (must be `< hangup_after_silence`). |

## Hangup behavior

| Field | Default | Use case |
|---|---|---|
| `call_terminate` | `300` (sec, 5 min) | Hard cap on total call duration. Raise for long support / coaching calls. |
| `hangup_after_LLMCall` | `false` | If `true`, call ends right after the agent's first response. **Only** for one-shot announcements (SMS-OTP-style verification reads, broadcast messages). |
| `call_hangup_message` | string or dict | Final line the agent reads before disconnecting. Dict form keyed by language for multilingual. |
| `call_cancellation_prompt` | string | Secondary LLM prompt evaluated on the transcript to decide if the call should end. Used in long, complex flows where simple silence/duration rules aren't enough. |
| `auto_reschedule` | `false` | Auto-reschedule on no-answer / busy according to the agent's retry policy. |
| `welcome_message_delay` | `0` (sec) | Wait this long after the call connects before the agent speaks. Useful when the carrier injects a beep or "this call is recorded" message. |

## Voicemail detection

| Field | Default | Use case |
|---|---|---|
| `voicemail` | `false` | Master switch for voicemail detection. |
| `voicemail_check_interval` | `7.0` (sec) | How often to re-evaluate whether you're talking to a machine. |
| `voicemail_detection_time` | `2.5` (sec) | Minimum audio before the first voicemail check fires. |
| `voicemail_detection_duration` | `30.0` (sec) | Max time to wait before giving up on detection. |
| `voicemail_min_transcript_length` | `7` (chars) | Minimum transcript length before the LLM is asked "is this voicemail?" |
| `discard_pre_welcome_utterance` | `false` | Drop any caller audio captured before the welcome message finishes playing. Set `true` if callers tend to say "hello?" before the agent starts. |

## Language detection (multilingual)

| Field | Default | Use case |
|---|---|---|
| `language_detection_turns` | `null` | Number of user turns to listen to before locking in the conversation language. `null` uses `active_language` from `multilingual_config`. |

## Inbound access control

| Field | Default | Use case |
|---|---|---|
| `inbound_limit` | `-1` | Concurrent inbound caller cap per number. `-1` = unlimited. |
| `whitelist_phone_numbers` | `null` | Array of E.164 numbers always allowed in (even when other rules would block). |
| `disallow_unknown_numbers` | `false` | If `true`, reject inbound callers not matched by `ingest_source_config` (caller-data lookup). |

## Backchanneling and fillers

| Field | Default | Use case |
|---|---|---|
| `backchanneling` | `false` | Inject "mhm" / "okay" while the user is talking. Good for support calls. Weird in IVR-style flows. |
| `backchanneling_message_gap` | `5` (sec) | Minimum gap between backchannels. |
| `backchanneling_start_delay` | `5` (sec) | Wait this long into the user's turn before the first backchannel. |
| `use_fillers` | `false` | Inject "umm", "okay so..." in agent responses to sound more human. |

## Ambient and noise

| Field | Default | Use case |
|---|---|---|
| `ambient_noise` | `false` | Mix a background loop under the agent (e.g., office hum, call-center bustle). Makes the call feel real, not studio-clean. |
| `ambient_noise_track` | `null` | Which loop to play. Provider-specific. |
| `noise_cancellation_level` | `null` | 0-100. How aggressively to suppress background noise on the **inbound** audio. Higher for street/market callers. |

## Other

| Field | Default | Use case |
|---|---|---|
| `dtmf_enabled` | `false` | Accept DTMF keypad input mid-call. Only supported on Plivo and Twilio. |

## Worked example — production India outbound

```jsonc
"task_config": {
  "call_terminate": 600,
  "hangup_after_silence": 20,
  "hangup_after_LLMCall": false,
  "incremental_delay": 350,
  "number_of_words_for_interruption": 2,
  "interruption_backoff_period": 0,
  "check_if_user_online": true,
  "check_user_online_message": {
    "en": "Hey, are you still there?",
    "hi": "क्या आप अभी भी कॉल पर हैं?"
  },
  "trigger_user_online_message_after": 12,
  "noise_cancellation_level": 70,
  "voicemail": false,
  "auto_reschedule": true,
  "optimize_latency": true,
  "welcome_message_delay": 0,
  "discard_pre_welcome_utterance": false,
  "use_fillers": false,
  "backchanneling": false,
  "ambient_noise": false,
  "inbound_limit": -1
}
```

Notable choices for this production agent:
- `call_terminate: 600` — longer than default 300s because outbound consultative calls run 5-8 minutes.
- `hangup_after_silence: 20` — Indian callers (especially women in domestic settings) often pause to think.
- `number_of_words_for_interruption: 2` — quick to interrupt, since this is conversational, not a monologue.
- `noise_cancellation_level: 70` — moderate; callers are often in markets, kitchens, or near children.
- `check_user_online_message` as dict — multilingual probe so the language matches.
- `optimize_latency: true` + `incremental_delay: 350` — fast turn-taking with a small buffer.

## See also

- `../SKILL.md` — main agent creation guide.
- `../../debug-bolna-calls/SKILL.md` — symptom-to-fix table that maps user-visible complaints to these fields.
- `../../debug-bolna-calls/references/latency-metrics.md` — what each latency knob actually controls.

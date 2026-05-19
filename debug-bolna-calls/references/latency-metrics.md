# Latency Metrics

Every execution returns a `latency_data` object on `GET /executions/{execution_id}`. Use it to pinpoint which pipeline component is slow.

## Top-level

```json
{
  "latency_data": {
    "stream_id": 129.56,
    "time_to_first_audio": 130.84,
    "region": "in",
    "transcriber": { ... },
    "llm": { ... },
    "synthesizer": { ... }
  }
}
```

| Field | Notes |
|---|---|
| `stream_id` | Time (ms) to establish the audio stream connection. High = network / telephony provider issue. |
| `time_to_first_audio` | Time (ms) from call start to first byte of agent audio. **The headline number for perceived responsiveness.** |
| `region` | Geographic region (`in`, `us`, etc.). Use this when comparing latency across customers in different geos. |

## Transcriber

```json
{
  "transcriber": {
    "time_to_connect": 226,
    "turns": [
      {
        "turn": 1,
        "turn_latency": [
          { "sequence_id": 1, "audio_to_text_latency": 20.12, "text": "hello who is there" },
          { "sequence_id": 2, "audio_to_text_latency": 19.96, "text": "hello who is this" }
        ]
      }
    ]
  }
}
```

| Field | Meaning |
|---|---|
| `time_to_connect` | Initial connection to the transcriber service (Deepgram / Sarvam / etc.). |
| `turn` | Sequential user-turn number (starts at 1). |
| `sequence_id` | Within a turn, transcribers emit partial then final results — each is a sequence. |
| `audio_to_text_latency` | Time (ms) for each partial transcription. The **final sequence** is the one the LLM sees. |
| `text` | The transcribed text for that sequence. |

**Thresholds:**

| Component | Healthy | Concerning | Action |
|---|---|---|---|
| `audio_to_text_latency` | <50ms | >100ms | Switch transcriber / improve audio / move to a closer region |
| `time_to_connect` | <300ms | >1000ms | Retry; if persistent, escalate to provider |

## LLM

```json
{
  "llm": {
    "time_to_connect": null,
    "turns": [
      { "turn": 1, "time_to_first_token": 1633.04, "time_to_last_token": 1691.53 },
      { "turn": 2, "time_to_first_token":  737.80, "time_to_last_token":  777.49 }
    ]
  }
}
```

| Field | Meaning |
|---|---|
| `time_to_connect` | Often `null` — OpenAI / Azure don't need a separate connect step. |
| `time_to_first_token` | Time (ms) until the **first token** of the response. **Critical for streaming.** TTS starts as soon as tokens arrive. |
| `time_to_last_token` | Total generation time. Higher just means the response was longer. |

**Thresholds:**

| Component | Healthy | Concerning | Action |
|---|---|---|---|
| `time_to_first_token` | <500ms | >1000ms | Lighter model / shorter prompt / different provider / Azure regional cluster |
| Gap between `first_token` and `last_token` | proportional to length | abnormally large | Switch to streaming-first provider |

**Why TTFT matters more than total**: with streaming, the TTS starts speaking when the first token arrives. The caller perceives latency = TTFT + TTS first-byte, not total LLM time.

## Synthesizer (TTS)

```json
{
  "synthesizer": {
    "time_to_connect": 271,
    "turns": [
      { "turn": 1, "time_to_first_token": 599, "time_to_last_token": 800 },
      { "turn": 2, "time_to_first_token": 317, "time_to_last_token": 518 }
    ]
  }
}
```

| Field | Meaning |
|---|---|
| `time_to_connect` | Initial connection to the TTS service. |
| `time_to_first_token` | Time to first audio chunk. **Perceptual latency** for the caller. |
| `time_to_last_token` | Complete audio generation. |

**Thresholds:**

| Component | Healthy | Concerning | Action |
|---|---|---|---|
| `time_to_first_token` | <300ms | >500ms | Lighter voice; switch provider; reduce TTS buffer size |
| `time_to_connect` | <300ms | >1000ms | Provider issue; first-call cold start is normal |

## Reading the data — worked example

User reports "the agent takes a long time to start talking."

Pull the execution and look at the **first turn**:

```
latency_data.time_to_first_audio = 1932ms

latency_data.transcriber.turns[0].turn_latency[<final>].audio_to_text_latency = 32ms
latency_data.llm.turns[0].time_to_first_token = 1422ms     ← here
latency_data.synthesizer.turns[0].time_to_first_token = 287ms
```

The LLM is the bottleneck (1.4s of the 1.9s). Action: try `gpt-4.1-mini` on Azure (lower regional latency), or switch the LLM provider.

If instead it had been:

```
latency_data.transcriber.audio_to_text_latency = 150ms
latency_data.llm.time_to_first_token = 380ms
latency_data.synthesizer.time_to_first_token = 720ms
```

→ TTS is slow. Switch to ElevenLabs `eleven_turbo_v2_5` (or Cartesia for English) — lower buffer/streaming-first.

## First-turn vs subsequent turns

Cold starts: `time_to_connect` only happens on turn 1. Subsequent turns reuse the established connection — so turn-1 latency is usually 200-400ms higher than turn-2. Don't optimise turn-1 unless steady-state is also bad.

## Tuning knobs on the agent side

Even with fast providers, the agent has its own latency budget:

| Knob | Default | What it controls |
|---|---|---|
| `task_config.incremental_delay` | `400ms` | Buffer before the agent commits to speaking. Lower = faster, but risk of interrupting yourself on partials. |
| `transcriber.endpointing` | `250ms` (Deepgram), `700ms` (others) | How long the STT waits in silence before finalising the user's turn. Higher = more thoughtful pauses tolerated. |
| `synthesizer.buffer_size` | `220-250` | TTS chunk size. Lower = faster first audio, higher CPU. |
| `synthesizer.stream` | `true` | Always keep on for live calls. |
| `llm.max_tokens` | `150-200` | Cap response length. Less to generate = lower `time_to_last_token`. Doesn't affect TTFT. |

## When the math doesn't add up

Sometimes `time_to_first_audio` is bigger than `transcriber + llm + synthesizer`. The gap is the audio path: encoding, telephony jitter buffer, codec conversion (especially `ulaw` → wav → ulaw on SIP). Anything in the 100-300ms range is normal.

## See also

- `references/raw-logs.md` — pairing latency data with the actual prompts and responses.
- `setup-sip-trunk/SKILL.md` — telephony-side latency causes.
- `../../references/providers-matrix.md` — latency rules-of-thumb per provider.

---
name: create-agent
description: "Create a Bolna Voice AI agent with the current v2 API, including system prompt, welcome message, LLM, voice, transcriber, telephony input and output, latency tuning, guardrails, knowledge bases, and function tools. Use when the user wants to build, deploy, or clone a Bolna voice agent."
license: MIT
compatibility: Requires internet access and a Bolna API key (BOLNA_API_KEY).
metadata:
  openclaw:
    requires:
      env:
        - BOLNA_API_KEY
    primaryEnv: BOLNA_API_KEY
---

# Create Bolna Agent

## Use the current API

- Endpoint: `POST https://api.bolna.ai/v2/agent`
- Auth: `Authorization: Bearer $BOLNA_API_KEY`
- Body root: `agent_config` and `agent_prompts`
- Response: `agent_id` and `status: created`
- Do not use deprecated `/agent` v1 endpoints for new agents.

## Minimum creation flow

1. Confirm the user has `BOLNA_API_KEY` set.
2. Gather: agent name, use case, language, welcome message, system prompt, LLM provider/model, voice/TTS provider, transcriber/STT provider, telephony provider, webhook URL if needed.
3. Build one `conversation` task unless the user explicitly asks for extraction, summarization, or advanced flows.
4. Put dynamic variables in prompts with braces, for example `{customer_name}`.
5. Add matching values later through `user_data` when making calls.
6. Include conservative call controls: silence hangup, interruption words, max duration, voicemail behavior, inbound limits.
7. POST the payload, then save the returned `agent_id`.

## Request shape

```json
{
  "agent_config": {
    "agent_name": "Support Agent",
    "agent_welcome_message": "Hi {customer_name}, this is Tara from Acme.",
    "webhook_url": null,
    "agent_type": "other",
    "tasks": [
      {
        "task_type": "conversation",
        "tools_config": {
          "llm_agent": {},
          "synthesizer": {},
          "transcriber": {},
          "input": {},
          "output": {},
          "api_tools": null
        },
        "toolchain": {
          "execution": "parallel",
          "pipelines": [["transcriber", "llm", "synthesizer"]]
        },
        "task_config": {}
      }
    ],
    "ingest_source_config": null,
    "calling_guardrails": {
      "call_start_hour": 9,
      "call_end_hour": 18
    }
  },
  "agent_prompts": {
    "task_1": {
      "system_prompt": "You are a concise, helpful voice agent..."
    }
  }
}
```

## Required task blocks

- `llm_agent`: use `simple_llm_agent` for normal prompting or `knowledgebase_agent` when attaching RAG. Use `agent_flow_type: streaming` for live calls.
- `synthesizer`: TTS provider, voice, model, streaming, buffer size, audio format.
- `transcriber`: STT provider, model, language, streaming, sampling rate, encoding, endpointing.
- `input` and `output`: telephony provider and audio format.
- `toolchain`: usually one pipeline: `transcriber -> llm -> synthesizer`.
- `task_config`: human conversation controls such as silence timeout, interruption threshold, backchanneling, voicemail, call max duration, whitelist, and unknown caller behavior.

## Knowledge bases

1. Create or list knowledge bases with the `create-knowledgebase` skill.
2. Wait until status is `processed`.
3. Use the returned `vector_id` in the agent LLM vector store config.
4. Use a knowledgebase agent only when the voice agent must answer from documents, FAQs, URLs, policies, or product docs.

## Function tools

Use `setup-tools` when the agent must transfer calls, call external HTTP APIs, fetch or book calendar slots, or write to CRM systems. Keep function schemas narrow, with clear descriptions and JSON parameters.

## Details to read before complex agents

Read `references/agent-config-fields.md` for full field guidance, provider choices, dynamic variables, RAG wiring, and gotchas.

## Script

```bash
python3 create-agent/scripts/create_minimal_agent.py \
  --name "Demo Support Agent" \
  --welcome "Hi {customer_name}, how can I help?" \
  --prompt "You are a helpful support agent. Keep answers brief."
```

## Hindi / Indian-language agent

For an agent serving Indian callers in Hindi:

```json
{
  "agent_config": {
    "agent_name": "Hindi Support Agent",
    "agent_welcome_message": "नमस्ते {customer_name}, मैं Acme से तारा बोल रही हूँ।",
    "tasks": [{
      "task_type": "conversation",
      "tools_config": {
        "llm_agent": {
          "agent_type": "simple_llm_agent",
          "agent_flow_type": "streaming",
          "llm_config": {
            "provider": "openai", "family": "openai", "model": "gpt-4.1-mini",
            "max_tokens": 200, "temperature": 0.2
          }
        },
        "synthesizer": {
          "provider": "sarvam",
          "provider_config": { "voice": "meera", "model": "bulbul-v2" },
          "stream": true, "audio_format": "wav"
        },
        "transcriber": {
          "provider": "deepgram", "model": "nova-3",
          "language": "multi-hi", "stream": true,
          "encoding": "linear16", "sampling_rate": 16000, "endpointing": 700
        },
        "input":  { "provider": "plivo", "format": "wav" },
        "output": { "provider": "plivo", "format": "wav" }
      },
      "toolchain": { "execution": "parallel", "pipelines": [["transcriber","llm","synthesizer"]] }
    }]
  },
  "agent_prompts": { "task_1": { "system_prompt": "आप तारा हैं, Acme की Voice AI सहायक। एक बार में 2 से अधिक वाक्य न बोलें। ग्राहक की भाषा में जवाब दें।" } }
}
```

Key choices:
- **Deepgram `multi-hi`** STT handles Hindi-English code-switching (Hinglish) cleanly.
- **Sarvam** TTS for native Hindi pronunciation.
- **Plivo** telephony for Indian 160-series numbers (160 = transactional). Use Vobiz for 140-series promotional.
- **Native Devanagari** in the system prompt — never phonetic English.
- `endpointing: 700` accommodates the longer pauses common in Hindi calls.

See `../write-bolna-prompts/references/multilingual.md` for the full multilingual playbook.

## Knowledge-base agent (RAG)

When the agent must answer from documents (FAQs, policies, product docs):

```json
{
  "tools_config": {
    "llm_agent": {
      "agent_type": "knowledgebase_agent",
      "agent_flow_type": "streaming",
      "llm_config": { "provider": "openai", "model": "gpt-4o", "max_tokens": 200, "temperature": 0.3 },
      "vector_store": {
        "provider": "lancedb",
        "provider_config": {
          "vector_ids": ["<rag_id_1>", "<rag_id_2>"],
          "similarity_top_k": 8
        }
      }
    }
  }
}
```

- Create the knowledge base first via `create-knowledgebase` and wait for `status == "processed"`.
- Use `vector_ids[]` (array) to attach **multiple** knowledge bases to one agent.
- `gpt-4o` is recommended for KB agents — better at synthesising across retrieved chunks than `gpt-4.1-mini`.

## Semantic routes (FAQ short-circuits)

For high-volume FAQs and policy refusals, `llm_agent.routes` short-circuits common questions with a pre-defined answer — zero LLM cost, near-zero latency:

```json
{
  "llm_agent": {
    "agent_type": "simple_llm_agent",
    "agent_flow_type": "streaming",
    "llm_config": { "provider": "openai", "model": "gpt-4.1-mini", "max_tokens": 200 },
    "routes": [
      {
        "name": "refund_policy",
        "utterances": ["what's your refund policy", "can I get a refund", "how do returns work"],
        "response": "We offer full refunds within 30 days of purchase. I can email you the policy document — want that?",
        "similarity_threshold": 0.85
      },
      {
        "name": "business_hours",
        "utterances": ["what are your hours", "when are you open", "operating hours"],
        "response": "We're open 9 AM to 7 PM IST, Monday through Saturday.",
        "similarity_threshold": 0.85
      }
    ]
  }
}
```

Routes fire **before** the LLM runs. Use for FAQs, hard refusals (pricing, competitor questions), and stable policy answers. Don't use for anything that needs to be dynamic per caller.

## See also

- `references/agent-config-fields.md` — full field reference.
- `make-call` — how to actually dial after creation.
- `bolna-graph-agents` — switch from a single prompt to a node-based flow.
- `setup-tools` — add `transfer_call`, custom HTTP, Cal.com booking.
- `create-knowledgebase` — generate the `vector_id` used by knowledgebase agents.
- `../references/providers-matrix.md` — picking LLM × STT × TTS × telephony combos.
- `../write-bolna-prompts` — how to write the `system_prompt`.

---
name: create-agent
description: "Create a Bolna Voice AI agent with the current v2 API, including system prompt, welcome message, LLM, voice, transcriber, telephony input and output, latency tuning, guardrails, knowledge bases, and function tools. Use when the user wants to build, deploy, or clone a Bolna voice agent."
license: MIT
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

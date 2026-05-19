---
name: create-knowledgebase
description: "Create, list, inspect, and delete Bolna knowledge bases from PDF files or URLs, including multilingual retrieval settings, chunking, overlap, similarity top k, processing status, rag_id and vector_id usage. Use when a voice agent needs RAG over FAQs, policies, product docs, or web pages."
license: MIT
compatibility: Requires internet access and a Bolna API key (BOLNA_API_KEY).
metadata:
  openclaw:
    requires:
      env:
        - BOLNA_API_KEY
    primaryEnv: BOLNA_API_KEY
---

# Create Bolna Knowledgebase

## Endpoints

- Create: `POST https://api.bolna.ai/knowledgebase`
- Get: `GET https://api.bolna.ai/knowledgebase/{rag_id}`
- List: `GET https://api.bolna.ai/knowledgebase/all`
- Delete: `DELETE https://api.bolna.ai/knowledgebase/{rag_id}`

Use `Authorization: Bearer $BOLNA_API_KEY`.

## Create from PDF

```bash
curl --request POST \
  --url https://api.bolna.ai/knowledgebase \
  --header "Authorization: Bearer $BOLNA_API_KEY" \
  --form 'file=@"/path/to/file.pdf"' \
  --form 'chunk_size=512' \
  --form 'similarity_top_k=15' \
  --form 'overlapping=128' \
  --form 'language_support=multilingual'
```

PDF max size is documented as 20 MB. Use `language_support=multilingual` for non-English documents or cross-lingual retrieval.

## Create from URL

```bash
curl --request POST \
  --url https://api.bolna.ai/knowledgebase \
  --header "Authorization: Bearer $BOLNA_API_KEY" \
  --form 'url=https://example.com/docs' \
  --form 'chunk_size=512' \
  --form 'similarity_top_k=15' \
  --form 'overlapping=128'
```

## Response fields

- `rag_id`: knowledgebase ID used for get/delete operations.
- `file_name`: PDF name or URL source name.
- `status`: `processing`, `processed`, or `error`.
- `source_type`: `pdf` or `url`.
- `language_support`: `multilingual` or null.

List responses include `vector_id`, which is what an agent uses for RAG wiring.

## Poll until processed

```bash
curl --request GET \
  --url "https://api.bolna.ai/knowledgebase/$RAG_ID" \
  --header "Authorization: Bearer $BOLNA_API_KEY"
```

Do not attach a knowledgebase to an agent until it is `processed`.

## Wire into an agent

When creating or updating an agent, configure the LLM as a knowledgebase agent and include the processed vector IDs in the vector store provider config. Use `create-agent` for the full agent shape.

## Delete

```bash
curl --request DELETE \
  --url "https://api.bolna.ai/knowledgebase/$RAG_ID" \
  --header "Authorization: Bearer $BOLNA_API_KEY"
```

Confirm deletion first; agents using the vector may stop answering from that source.

## Wire into a Bolna agent

In the agent config, use `agent_type: "knowledgebase_agent"` and attach the `vector_id` (one or more):

```json
{
  "llm_agent": {
    "agent_type": "knowledgebase_agent",
    "agent_flow_type": "streaming",
    "llm_config": { "provider": "openai", "model": "gpt-4o", "max_tokens": 200, "temperature": 0.3 },
    "vector_store": {
      "provider": "lancedb",
      "provider_config": {
        "vector_ids": ["<vector_id_1>", "<vector_id_2>"],
        "similarity_top_k": 8
      }
    }
  }
}
```

For graph agents, attach per-node via `rag_config` on individual nodes — see `bolna-graph-agents/references/edges-and-routing.md` and the example in `bolna-graph-agents/assets/full-example.json`.

## Script

```bash
python3 create-knowledgebase/scripts/create_knowledgebase.py \
  --file /path/to/manual.pdf \
  --multilingual
```

## Tuning

| Knob | Default | Effect |
|---|---|---|
| `chunk_size` | `512` | Larger chunks = more context per retrieval, less precise matching. |
| `overlapping` | `128` | Overlap between chunks. Higher prevents missing answers that straddle boundaries. |
| `similarity_top_k` | `15` | How many chunks to retrieve. Lower for tight answers, higher for broader synthesis. |
| `language_support` | `null` | Set to `multilingual` for non-English docs or cross-lingual retrieval. |

## See also

- `create-agent` — `knowledgebase_agent` example with vector wiring.
- `bolna-graph-agents` — per-node RAG via `rag_config`.
- `../references/prompting-tips.md` — anti-hallucination guidance when answering from retrieved chunks.

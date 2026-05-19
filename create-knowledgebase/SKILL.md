---
name: create-knowledgebase
description: "Create, list, inspect, and delete Bolna knowledge bases from PDF files or URLs, including multilingual retrieval settings, chunking, overlap, similarity top k, processing status, rag_id and vector_id usage. Use when a voice agent needs RAG over FAQs, policies, product docs, or web pages."
license: MIT
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

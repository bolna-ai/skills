# Bolna Skills

Agent skills for building and operating Bolna Voice AI agents. The folders in this repo follow the Agent Skills layout used by `npx skills add`: each skill is a self-contained directory with a `SKILL.md` file and optional scripts, references, or assets.

## Local Install

From this machine, install all skills into a compatible agent with:

```bash
npx skills add "/Users/amitesh/Projects/Bolna-Skills "
```

Install one skill:

```bash
npx skills add "/Users/amitesh/Projects/Bolna-Skills " --skill create-agent
```

When this repo is later pushed to GitHub, the command becomes:

```bash
npx skills add YourOrg/bolna-skills
npx skills add YourOrg/bolna-skills --skill make-call
```

No npm package publish is needed. `npx skills` is the installer; this repo is the install source.

## Skills

| Skill | Use it for |
| --- | --- |
| `setup-api-key` | Generate, store, and verify `BOLNA_API_KEY`. |
| `create-agent` | Create a Bolna v2 voice agent with prompts, LLM, voice, transcriber, telephony, guardrails, and optional RAG or tools. |
| `manage-agents` | List, fetch, patch, fully update, delete, and stop queued calls for agents. |
| `make-call` | Start, schedule, personalize, retry, and stop outbound calls. |
| `setup-inbound` | Attach or unlink an agent from an inbound phone number and configure caller matching. |
| `manage-phone-numbers` | Search, buy, list, and delete Bolna phone numbers. |
| `create-batch` | Upload CSV campaign recipients, schedule batches, monitor batch status, and stop/delete batches. |
| `get-executions` | Fetch execution details, raw logs, transcripts, recordings, costs, statuses, and paginated call history. |
| `setup-webhook` | Configure webhook delivery and build a receiver for call status and execution payloads. |
| `create-knowledgebase` | Ingest PDFs or URLs as Bolna knowledge bases and wire vector IDs into agents. |
| `setup-tools` | Add function tools, transfer calls, custom HTTP APIs, and Cal.com booking patterns. |
| `add-provider` | Register and manage third-party telephony, LLM, TTS, and STT providers. |

## Bolna API Defaults

- Base URL: `https://api.bolna.ai`
- Auth header: `Authorization: Bearer $BOLNA_API_KEY`
- API key smoke test: `GET /user/me`
- Current agent API: `/v2/agent`
- Deprecated agent v1 API: `/agent`; do not use it for new skills.
- Docs index: `https://www.bolna.ai/docs/llms.txt`
- OpenAPI spec: `https://www.bolna.ai/docs/api-reference/openapi.yml`

## Validate Locally

```bash
python3 scripts/validate_skills.py
```

This checks folder names, required frontmatter, description length, and accidental deprecated agent v1 usage.

## Git

This repo is intended to stay local until you decide to publish it. Do normal local tracking:

```bash
git status
git log --oneline
```

## License

MIT

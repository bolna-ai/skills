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

Install for a specific agent when supported by the installer:

```bash
npx skills add "/Users/amitesh/Projects/Bolna-Skills " -a codex
npx skills add "/Users/amitesh/Projects/Bolna-Skills " -a claude-code
npx skills add "/Users/amitesh/Projects/Bolna-Skills " -a cursor
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
| `create-disposition` | Create, update, test, and delete post-call extraction and classification templates. |
| `setup-sip-trunk` | Create and manage BYOT SIP trunks, gateways, and trunk phone numbers. |
| `manage-subaccounts` | Create, update, delete, list, and inspect enterprise sub-accounts and usage. |
| `manage-violations` | List call violations and submit evidence files for review. |
| `bolna-graph-agents` | Design node-based graph agents, routing edges, static nodes, and event injection. |
| `write-bolna-prompts` | Write production voice prompts, multilingual prompts, hangup rules, and context variables. |
| `debug-bolna-calls` | Diagnose latency, interruptions, silence, webhook, transcript, and provider issues. |

## Bolna API Defaults

- Base URL: `https://api.bolna.ai`
- Auth header: `Authorization: Bearer $BOLNA_API_KEY`
- API key smoke test: `GET /user/me`
- Current agent API: `/v2/agent`
- Deprecated agent v1 API: `/agent`; do not use it for new skills.
- Docs index: `https://www.bolna.ai/docs/llms.txt`
- OpenAPI spec: `https://www.bolna.ai/docs/api-reference/openapi.yml`

## Reference Repo Patterns Applied

- ElevenLabs pattern: each skill folder is self-contained, with quick starts and optional references/scripts.
- Vapi pattern: workflow-specific skills, explicit install commands, and clear API-key setup.
- Firecrawl pattern: separate operational skills from build/debug/workflow skills so agents load only what they need.
- Bolna-specific decision: no first-party Bolna MCP is assumed. `.mcp.example.json` is optional and points at a third-party Composio router only when the user deliberately configures it.

## Validate Locally

```bash
python3 scripts/validate_skills.py
python3 evals/run_all.py
```

The validator checks folder names, required frontmatter, description length, and accidental deprecated agent v1 usage. The eval script checks trigger coverage and a few repo-specific invariants.

## Git

This repo is intended to stay local until you decide to publish it. Do normal local tracking:

```bash
git status
git log --oneline
```

## License

MIT

# Bolna Skills

Official Agent Skills for [Bolna Voice AI](https://bolna.ai). Teach your AI coding assistant — Claude Code, Cursor, Codex, or any tool that supports the Agent Skills format — to build, deploy, and operate production voice agents in one command.

## Install

```bash
npx skills add bolna-ai/skills
```

For a specific tool:

```bash
npx skills add bolna-ai/skills -a claude-code
npx skills add bolna-ai/skills -a cursor
npx skills add bolna-ai/skills -a codex
```

Just one skill:

```bash
npx skills add bolna-ai/skills --skill create-agent
```

## Setup

Get your API key from the [Bolna Dashboard → Developers](https://platform.bolna.ai) and export it:

```bash
export BOLNA_API_KEY="..."
```

That's it. Your AI assistant now knows how to use Bolna.

## What you can do

Once installed, ask your AI assistant things like:

- *"Create a Hindi voice agent for appointment booking using Plivo and Sarvam."*
- *"Place a test call to +91… and pass `customer_name: Priya` as user_data."*
- *"Upload `leads.csv` as a Bolna batch campaign and monitor it until done."*
- *"My Bolna call has a long silence before each response — debug it."*
- *"Build a graph agent for payment confirmation with real-time event injection."*
- *"Add post-call dispositions for lead quality and customer sentiment to my agent."*
- *"Set up an inbound IVR that routes sales / support / billing to three different agents."*
- *"Bring my Twilio Elastic SIP trunk to Bolna for outbound calling on my own numbers."*

The right skill loads automatically based on what you ask.

## Skills

### Build agents

| Skill | What it does |
|---|---|
| `setup-api-key` | Generate, store, and verify your `BOLNA_API_KEY`. |
| `add-provider` | Bring your own OpenAI, Anthropic, Azure, ElevenLabs, Cartesia, Sarvam, Deepgram, Twilio, Plivo, Vobiz, or Exotel credentials. |
| `create-agent` | Create a voice agent end-to-end: LLM + voice + transcriber + telephony, with knowledge bases, function tools, and semantic routes. |
| `manage-agents` | List, update, delete, or stop queued calls for an agent. |
| `write-bolna-prompts` | Write production voice prompts. Includes vertical templates (sales, support, appointment, BFSI reminder, recruitment) and a full multilingual native-script guide. |

### Make calls

| Skill | What it does |
|---|---|
| `make-call` | Place a single outbound call — immediate or scheduled, with dynamic variables, voice overrides, and auto-retry. |
| `create-batch` | Run CSV-driven outbound campaigns at scale. Schedule, monitor, stop. |
| `setup-inbound` | Wire phone numbers to agents. Includes IVR menus, caller identification, and multilingual auto-switching. |
| `manage-phone-numbers` | Search and buy US (Twilio) or India (Plivo, Vobiz) numbers. |
| `setup-sip-trunk` | Bring your own SIP trunk — Twilio Elastic, Plivo Zentrunk, Telnyx, Vonage, and any standards-compliant carrier. |

### Monitor and improve

| Skill | What it does |
|---|---|
| `get-executions` | Pull transcripts, recordings, costs, hangup codes, and raw logs from any call. |
| `setup-webhook` | Stream call updates to your backend in real time for CRM sync and dashboards. |
| `create-disposition` | Extract structured data from every transcript: lead quality, appointment times, sentiment, consent captured. |
| `manage-violations` | List compliance flags and submit evidence files for review. |
| `debug-bolna-calls` | Symptom-to-fix runbook for slow responses, robot voice, interruptions, missed webhooks, SIP no-audio, batch failures, and more. |

### Advanced

| Skill | What it does |
|---|---|
| `bolna-graph-agents` | Build deterministic, node-based call flows with LLM, expression, and event-driven transitions. Push real-time events into live calls. |
| `setup-tools` | Give agents function-calling tools: live transfer, Cal.com booking, any HTTP API, and DTMF keypad input. |
| `create-knowledgebase` | Add RAG over PDFs or URLs, including multilingual document support. |
| `manage-subaccounts` | Multi-tenant workspaces for agencies and enterprise teams (auto-provisioned API keys). |

## Resources

- [Bolna docs](https://docs.bolna.ai)
- [Dashboard](https://platform.bolna.ai)
- [API reference](https://docs.bolna.ai/api-reference/introduction)
- Issues and questions → [github.com/bolna-ai/skills/issues](https://github.com/bolna-ai/skills/issues)

## License

MIT

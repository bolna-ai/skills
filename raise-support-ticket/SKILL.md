---
name: raise-support-ticket
description: "Raise, track and reply to Bolna support tickets from your AI assistant: contact Bolna support, report a bug, escalate a problem, complain about a failed call, ask the Bolna team for help, or request a feature. Diagnoses the issue first, checks for an existing open ticket, drafts a ticket with agent and execution ids, waits for the user to confirm, then files it with the Bolna MCP support tools (raise_support_ticket, list_support_tickets, get_support_ticket, reply_support_ticket)."
license: MIT
compatibility: Requires the Bolna MCP server (https://mcp.bolna.ai/api/mcp) connected with a Bolna API key. Ticket tools are currently enabled for Bolna staff accounts only.
metadata:
  openclaw:
    requires:
      env:
        - BOLNA_API_KEY
    primaryEnv: BOLNA_API_KEY
---

# Raise a Bolna support ticket

Most "contact support" requests can be answered without a ticket. File one only when the problem needs the Bolna team, and make the ticket good enough that nobody has to ask for the basics again.

## 1. Try to solve it first

| The user says | Do this first |
|---|---|
| A call failed, sounded wrong, hung up early, had silences | Follow the `debug-bolna-calls` skill with the `execution_id`. |
| "How do I…" | Search the docs with the MCP `search_docs` tool and answer. |
| Billing, wallet, balance | Look up the account with `get_user_info`. |
| Something is broken for every call, or the dashboard/API is down | Go straight to step 2 with priority 0 or 1. |

If that fixes it, stop. Offer a ticket only when the fix needs Bolna (a platform bug, a provider outage, an account change you can't make, or a feature that doesn't exist).

## 2. Check for an open ticket

Call `list_support_tickets`. If an open or in-progress ticket covers the same problem, show it and offer `reply_support_ticket` with the new details instead of filing a duplicate. `get_support_ticket` shows the support team's replies.

## 3. Draft the ticket

| Field | What goes in it |
|---|---|
| `title` | One line, the symptom plus where: "Hindi agent hangs up after 5 seconds on Plivo inbound". |
| `description` | What happened, what was expected, what you already checked, and the ids: `agent_id`, `execution_id`, `batch_id`, approximate time with timezone. |
| `category` | `bug_report`, `question`, `feature_request` or `ux_issue`. |
| `priority` | 0 urgent (live calls down), 1 high (one agent or campaign blocked), 2 normal (default), 3 low. |

Never put API keys, provider credentials, passwords or full customer phone numbers in a ticket. Mask numbers, for example `+91 98XXX XXX10`.

## 4. Confirm, then file

Show the user the exact title, category, priority and description. File it with `raise_support_ticket` only after they confirm in their next message. Then give them the ticket id and say they can ask for its status at any time.

## If the ticket tools aren't available

The tools need the Bolna MCP server and, for now, a Bolna staff account (a `403` means tickets aren't enabled for this account). Otherwise, hand the user the drafted ticket and point them to the support chat on [docs.bolna.ai](https://docs.bolna.ai) or [Getting help](https://docs.bolna.ai/getting-help).

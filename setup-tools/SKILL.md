---
name: setup-tools
description: "Add Bolna function tools to voice agents, including transfer calls, custom HTTP API calls, Cal.com slot lookup and booking, OpenAI-style JSON schemas, tool parameters, and DTMF or IVR style actions. Use when a Bolna agent must take real-world actions during a live call."
license: MIT
---

# Setup Bolna Function Tools

## When to add tools

Use tools when the agent must do more than speak:

- Transfer a call to a human or queue.
- Fetch customer, order, payment, shipment, or ticket data.
- Create records in CRM or support systems.
- Check and book calendar slots.
- Trigger a workflow in Make, Zapier, n8n, or a custom backend.
- Capture DTMF-style keypad choices or route IVR flows.

## Tool placement

Function tools live under the conversation task's `tools_config.api_tools` block. Keep schemas narrow and explicit. Overbroad tools cause accidental calls and poor voice UX.

## Design rules

1. Use clear tool names, for example `lookup_customer`, `book_slot`, or `transfer_to_sales`.
2. Make the `description` say exactly when the model should call it.
3. Use JSON Schema parameters compatible with OpenAI function calling.
4. Add a short pre-call phrase when the user will hear a pause.
5. Keep secrets in provider config, environment, or backend; do not hard-code them in prompts.
6. Test with raw logs from `get-executions`.

## Common tool categories

- Transfer call: hand off to a phone number, SIP destination, or queue.
- Custom HTTP: `GET`, `POST`, `PATCH`, or `DELETE` to your own API.
- Cal.com availability: fetch available slots.
- Cal.com booking: book the selected slot with caller details.

## Reference examples

Read `references/tool-schemas.md` for worked examples.

## Debugging

- Tool never called: improve the tool description and system prompt trigger language.
- Tool called too often: tighten description and require explicit user intent.
- Tool payload wrong: simplify parameter schema and add examples in the system prompt.
- Tool timeout: make backend faster or use a pre-call message.
- Bad post-tool response: tell the agent exactly how to summarize tool results.

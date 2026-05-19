---
name: bolna-graph-agents
description: "Design Bolna graph agents with nodes, edges, expression routing, static low-latency responses, silence repeat behavior, real-time event injection, and deterministic multi-step call flows. Use when a single prompt is too fragile for a structured voice workflow."
license: MIT
compatibility: "Requires Bolna graph-agent access and current Bolna docs."
---

# Bolna Graph Agents

## When to use graph agents

Use a graph agent when the call flow has strict steps, branching, compliance checkpoints, deterministic greetings, or external events. Use normal prompt agents for flexible conversations where a single system prompt is enough.

Good fits:

- Appointment booking with date, slot, confirmation, and fallback branches.
- Lead qualification with disqualification branches.
- Collections or compliance calls with mandatory disclosures.
- IVR-like menu flows with LLM fallback.
- High-volume flows where static nodes reduce latency and LLM cost.

## Core concepts

- Nodes: conversation states.
- Edges: transitions between nodes.
- Expression routing: rules using built-in variables and extracted values.
- Static nodes: pre-cached messages that can play very quickly without an LLM round trip.
- Silence repeat: replay or escalate after user silence.
- Event injection: external REST events can transition the graph or trigger proactive speech.

## Design workflow

1. Write the desired call flow as states and transitions before writing JSON.
2. Mark which nodes need LLM reasoning and which can be static.
3. Define required variables and where they are collected.
4. Define terminal states: completed, transferred, voicemail, no consent, do-not-call, failed.
5. Add fallback edges for silence, confusion, invalid input, and tool failure.
6. Test with transcripts and real calls before using batches.

## Quality checks

- Every node has an exit condition.
- Every tool or API failure has a spoken fallback.
- Static nodes do not include dynamic facts unless templated safely.
- Required compliance statements cannot be skipped by routing.
- External event injection is authenticated and idempotent.
- Graph outcomes map to dispositions or execution fields for analytics.

## Debugging

Use Bolna graph-agent routing logs to inspect what the routing LLM saw, which expression matched, and why the next node was chosen. If routing is unstable, simplify edge conditions before changing the prompt.

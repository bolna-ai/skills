# Text block → MCP tool param mapping

The Bolna UI shows Category / Name / Extraction Prompt / Answer Type as separate fields. The `create_disposition`, `bulk_create_dispositions`, and `test_dispositions` MCP tools take a flatter object. This is the exact translation — use it verbatim when constructing tool calls, don't improvise field names.

## Single disposition object

```json
{
  "agent_id": "<required only at push-live time>",
  "name": "call_outcome",
  "category": "Call_Outcome",
  "question": "<the full EXTRACTION PROMPT text, all 7 skeleton parts>",
  "system_prompt": "<optional — see note below>",
  "model": "gpt-4.1-mini",
  "is_subjective": false,
  "is_objective": true,
  "subjective_type": "text",
  "subjective_type_config": { "pattern": "...", "description": "..." },
  "objective_options": [
    { "value": "Interested", "condition": "Yield this value if ..." },
    { "value": "Not_Interested", "condition": "...",
      "sub_options": [
        { "value": "Price_High", "condition": "..." }
      ]
    }
  ]
}
```

## Field-by-field

| Text block field | Tool param | Notes |
|---|---|---|
| `CATEGORY:` | `category` | String, defaults to `"General"` server-side if omitted — always set it explicitly, it's how Bolna's dashboard groups results. |
| `NAME:` | `name` | snake_case. This is also the key under `extracted_data[category][...]` — keep it stable once live; renaming looks like a new field downstream. |
| `EXTRACTION PROMPT:` | `question` | **Required.** The entire skeleton (role, scope, classification, definitions, guardrails, tie-breakers, default) goes here as one string. This is literally what the extraction LLM reads alongside the transcript — nothing else is passed in, so it must be fully self-contained. |
| — | `system_prompt` | Optional, separate from `question`. Only use this when several dispositions on the *same agent* need shared framing (e.g. "You are analyzing a debt-collection call; the customer is the debtor, not the agent's employer.") that would otherwise be duplicated verbatim in every `question`. Default: leave unset. Do not split the 7-part skeleton across `question`/`system_prompt` — the skeleton is one coherent unit and belongs entirely in `question`. |
| `ANSWER TYPE: Free Text` | `is_subjective: true` | |
| `EXPECTED FORMAT:` | `subjective_type` | `Text`→`"text"` (default), `Timestamp`→`"timestamp"`, `Numeric`→`"numeric"`, `Boolean`→`"boolean"`, `Email`→`"email"`, `Custom Regex`→`"regex"` + populate `subjective_type_config.pattern` (required when type is `regex`) and optionally `.description`. Never invent a regex pattern the user didn't ask for — default to `"text"` when a strict format wasn't actually specified, even if the PDF/brief says "Custom Regex / Text" loosely. |
| `ANSWER TYPE: Pre-defined` | `is_objective: true` | |
| `POSSIBLE ANSWERS:` list | `objective_options[]` | Each entry: `{ "value": "...", "condition": "..." }`. `value` = the Answer Value, `condition` = the Condition prompt. |
| `└─` nested entries | parent's `objective_options[i].sub_options[]` | Same `{value, condition}` shape, recursively (`sub_options` can itself contain `sub_options`, though 2 layers covers nearly every real case). Evaluated only when the parent value is selected — this is exactly the Layer 1 / Layer 2 pattern from nested pre-defined dispositions. |
| `ANSWER TYPE: Both` | `is_subjective: true` AND `is_objective: true` | Both come back in the same `extracted_data` entry (`subjective` + `objective` keys) from one API call. |
| (rarely surfaced in the brief) | `model` | Defaults to `"gpt-4.1-mini"`. Only override for a deliberately higher-stakes extraction (e.g. compliance/consent capture) where the user asks for more rigor — don't default to a stronger model unasked, it changes cost. |

Schema constraint to respect: **at least one of `is_subjective` / `is_objective` must be `true`.** If you produced a block with only Pre-defined, `is_subjective` stays `false` and `subjective_type` is simply unused (leave it at default, don't worry about it).

## Bulk vs. single

- One extraction for one agent → `create_disposition` (takes `agent_id` + the object above, flattened as top-level params, not nested under a key).
- Several extractions for one agent → `bulk_create_dispositions`: `{ "agent_id": "...", "dispositions": [ {..}, {..} ] }`. **Atomic** — if any one object fails validation (e.g. `is_objective: true` with empty `objective_options`), none are created. Mentally run the self-check from SKILL.md on every item before calling, especially when pushing a whole category from the ed-tech asset pack — a single malformed nested `sub_options` entry blocks the other 12.

## Testing before going live

`test_dispositions` takes `agent_id` + `transcript` (+ optional `call_date`) and runs *every disposition already linked to that agent* — not just the ones you just added. It returns the same `extracted_data` shape a real execution would. Use it right after `create_disposition`/`bulk_create_dispositions` when the user gives you a sample transcript, to catch:
- a condition that fires on the wrong behavior (overlap you missed in the self-check)
- a Free Text field that returns non-empty when it should be empty (missing "if not mentioned, return empty string" rule)
- low `confidence` (< 0.5) on a value that should be obvious — usually means the `question` isn't scoped enough (skeleton step 2)

## What this skill does NOT need to touch

`update_disposition`'s copy-on-write behavior (edit-in-place vs. new id when shared across agents), `delete_disposition`'s authorization rules, and the legacy `gpt_assistants.custom_questions` migration path are `create-disposition`'s territory — read that skill's SKILL.md directly if the user's question is about API mechanics rather than what to write in `question`/`condition`.

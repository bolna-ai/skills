# Disposition Answer Types

Each disposition can produce a **Free Text** answer (`is_subjective`), a **Pre-defined** value (`is_objective`), or both. Pick based on what consumes the data downstream.

## Free Text (`is_subjective: true`)

The LLM writes a custom answer based on transcript context.

**Use for:**

- Open-ended summaries ("describe the customer's main concern").
- Captured values that vary per call (email, name, address, alt phone).
- Reasons / explanations ("why did they cancel").

**Don't use for:**

- Categorical fields where you want clean CRM values (`hot`/`warm`/`cold`).
- Strict yes/no questions.

### Subjective types

| `subjective_type` | Validates | Example | Notes |
|---|---|---|---|
| `text` (default) | Anything | `"Customer wants pricing for enterprise plan"` | No validation. |
| `timestamp` | ISO 8601 | `"2026-04-08T14:30:00"` | Parsed and validated. |
| `numeric` | Number | `"42"`, `"3.14"` | |
| `boolean` | `true` / `false` | `"true"` | Use this OR pre-defined Yes/No — not both. |
| `email` | Valid RFC email | `"user@example.com"` | |
| `regex` | Matches `subjective_type_config.pattern` | `"+919876543210"` | Pattern is mandatory. |

Validation failures don't drop the value — the original response stays in `subjective` and `validation.is_valid` is `false`.

### Regex pattern example

```json
{
  "subjective_type": "regex",
  "subjective_type_config": {
    "pattern": "^\\+\\d{10,15}$",
    "description": "E.164 phone number"
  }
}
```

```json
{
  "subjective": "+919876543210",
  "validation": { "is_valid": true, "expected_type": "regex" }
}
```

## Pre-defined (`is_objective: true`)

The LLM picks one value from a list you control. Clean for CRMs.

```json
{
  "is_objective": true,
  "objective_options": [
    { "value": "hot",          "condition": "Customer is ready to buy, has budget, has authority, and timeline within 30 days" },
    { "value": "warm",         "condition": "Customer is interested but missing budget, authority, or timeline" },
    { "value": "cold",         "condition": "Customer has limited interest but might revisit later" },
    { "value": "disqualified", "condition": "Customer is not a fit, no budget, no need, or wrong company" }
  ]
}
```

| Field | Notes |
|---|---|
| `value` | What gets written to `extracted_data.objective`. Use snake_case if it'll be machine-read; Yes/No / hot / warm if it'll be human-read. |
| `condition` | The LLM's selection rubric. Write it like instructions for a human reviewer. |
| `sub_options` | Optional recursive options for hierarchical classifications. |

### Sub-options for hierarchical classification

```json
{
  "value": "interested",
  "condition": "Customer expressed intent to buy",
  "sub_options": [
    { "value": "enterprise", "condition": "Mentioned enterprise pricing, seats > 50, custom contract, SSO/SAML, or VPC deployment" },
    { "value": "pro",        "condition": "Mentioned mid-size teams (10-50 seats) or standard paid tier" },
    { "value": "starter",    "condition": "Mentioned small team, individual use, or free tier" }
  ]
}
```

The LLM picks both the top level and a sub-option when conditions match.

## Both at the same time

A disposition can produce both a free text summary AND a categorical value:

```json
{
  "name": "Call Outcome",
  "question": "What was the outcome of the call? Also summarise the customer's reasoning in one sentence.",
  "is_subjective": true,
  "is_objective": true,
  "subjective_type": "text",
  "objective_options": [
    { "value": "interested",     "condition": "Customer agreed to a next step or scheduled a follow-up" },
    { "value": "not_interested", "condition": "Customer declined all proposals" },
    { "value": "follow_up",      "condition": "Customer asked to be contacted later, no specific date" }
  ]
}
```

Output:

```json
{
  "Call Outcome": {
    "subjective": "Customer wants to discuss with their CTO and reconnect next week.",
    "objective": "follow_up",
    "confidence": 0.88,
    "confidence_label": "High"
  }
}
```

The categorical value drives routing; the free text gives a reviewer the gist without reading the full transcript.

## When to split

If a question feels like it has too many possible answers, split it:

- ❌ "What's the lead score and what's the reason?"  (one disposition)
- ✅ "Lead Score" (Pre-defined: hot/warm/cold) + "Reason for Lead Score" (Free text)

Smaller, focused dispositions give higher confidence scores.

## Empty vs null

| Value | Means |
|---|---|
| `""` (empty string) | LLM found no info to summarise. |
| `"null"` (string) | Extraction wasn't applicable. |
| `null` (JSON null) | Field not configured (e.g. `objective` when `is_objective: false`), or no condition matched. |

Treat these as distinct in your downstream code. `null` for `objective` could mean "we asked but no option matched" — different from "we didn't ask."

## Picking the model

Most dispositions run fine on `gpt-4.1-mini`. Bump to a stronger model when:

- The question requires multi-step reasoning across the transcript.
- Multiple categorical conditions overlap and require careful disambiguation.
- The output drives high-stakes downstream actions (legal, financial, healthcare).

```json
{ "model": "gpt-4o" }
```

Cost increases ~5×. Test with `dispositions/test` before flipping for high-volume agents.

# Extraction Patterns & Anti-Patterns Library

Reference material for `bolna-extraction-designer`. Read the relevant section when designing; synthesize into the specific extraction, don't quote back to the user.

## Archetype 1: Binary Intent / Agreement

Use when the signal is fundamentally yes/no. Examples: `checkout_link_agreement`, `purchase_intent`, `interested_in_job`, `compared_to_another_platform`.

Pre-defined, 3 values: affirmative / negative / third-bucket (mandatory — `Undecided`/`Maybe`/`Unclear`/`NA`). Often paired with conditional Free Text (Sub-pattern A) so "Yes" captures more detail.

```
You are an assistant scanning the transcript to determine whether [the customer did X].
Use the full conversation for context, but base the decision only on [the customer's own statements / responses to the agent's questions about X].
Classify as Yes, No, or [third bucket].
Return Yes if the customer clearly [behavioral signals].
Return No if the customer clearly [opposite signals].
Return [third bucket] if the customer is vague, silent, unclear, hesitant, asks a question without clearly agreeing, or the call ends before a clear answer.
Use the customer's most recent clear intent if they change their mind.
Do not infer agreement from politeness or general interest alone.
```

## Archetype 2: Sentiment Classifier

Pre-defined, 3-5 values across the emotional spectrum. Include a Busy/Distracted bucket if relevant — distinct from Negative. Focus on *dominant* sentiment by call end, not intermediate fluctuation.

```
You are an assistant scanning the transcript to classify the [customer's] overall sentiment toward [the call/agent/product/opportunity].
Use the full conversation for context and focus on tone, cooperation, objections, and final stance.
Classify as Positive, Neutral, Negative, or Busy.
Use the most recent and dominant sentiment by the end of the call.
```

## Archetype 3: Call Outcome / Disposition

3-6 values, one per closing branch the call could realistically reach. Include a `Follow_Up_Required`-equivalent for incomplete/ambiguous calls.

```
You are an assistant scanning through the transcript and determining the final outcome of the [call type].
Analyze the entire conversation for context and base the decision only on responses related to [key signals — list them].
Classify the result using the [customer's] final clear intent.
[per-value definitions]
If the transcript is too short, incomplete, or ambiguous, return [Follow_Up_Required].
```

## Archetype 4: Objection Categorizer (Nested Pre-defined)

Parent Yes (objection raised) / No, with 4-8 categorized objection types nested under Yes. Always include `No_Particular_Reason` under Yes for ambiguous cases. Maps to `sub_options` (see `field-mapping.md`).

```
You are an assistant scanning the transcript to determine whether the customer raised an objection about [topic], and if yes, classify it.
Use the full conversation for context, but base the decision only on the customer's own statements.
Use the top-level value No only when no clear objection is raised.
Use Yes when an objection, concern, hesitation, complaint, resistance, or reason for not [acting] is raised; select the best-matching category under it.
Do not treat normal information questions as objections unless they show hesitation, resistance, doubt, or complaint.
If multiple objections appear, choose the most specific or most recent.
Do not hallucinate an objection the customer didn't clearly raise.
```

## Archetype 5: Structured-Format Extraction

Free Text with a strict output shape (date/time/ID). The prompt does the heavy lifting: strict format spec + normalization rules + empty-output rule. Usually the longest prompt type.

```
You are an assistant scanning the transcript to extract the [data point].
Use the full conversation for context, but extract a [value] only from the user's response to an explicit [question topic] question.
Return exactly one of: [FORMAT] / empty string.
Rules:
- Return empty if the assistant never asked the [question topic].
- Return empty if the user only greeted, answered availability, or continued the current call without addressing the question.
- [If applicable] If the user agrees but gives no [value], apply a default using a reference timestamp variable.
[format-specific normalization rules, e.g. "morning: 11:00", "today/aaj/आज: use call date"]
Never return a past value. Output only the value or empty string.
```

## Archetype 6: Subjective + Objective Dual Output

Both `is_subjective` and `is_objective` true. Free Text = one-sentence factual reasoning; Pre-defined = verdict. The prompt has explicit "For the subjective answer" / "For the objective answer" sections — don't let them blur together.

```
You are an assistant scanning the transcript to determine [a verdict].
Analyze the entire conversation for context and base the decision only on responses related to [signals]. Do not use the assistant's questions or offers as evidence by themselves.
For the subjective answer, write one short factual sentence explaining why [the verdict applies]. If incomplete, mention what's missing.
For the objective answer, choose Yes if [...], No if [...].
If the verdict is not clearly established, do not force a positive result — the reasoning should say what's missing or unclear.
```

## Archetype 7: Free-Text Data Capture

Free Text only, no classification. Clear inclusion/exclusion criteria and an explicit empty-output rule. Often paired with a sibling binary extraction (`compared_to_another_platform`: Yes/No + `compared_platforms`: the actual names).

```
You are an assistant scanning the transcript to extract [the data point].
Use the full conversation for context, but extract only [scope: actual questions / clear requests / explicit mentions].
Do not include [exclusions — agent's questions, hypotheticals]. Do not invent data.
If multiple [items], list each separately. If the customer doesn't [do X], leave empty.
Output only the data. No explanation.
```

## Archetype 8: Synthesis / Meta-Extraction

One extraction combining evidence from multiple conversational topics into a single verdict (e.g. `call_outcome` = interest + location + relocation + vehicle + documents). Pre-defined, 3-6 values; the prompt explicitly lists all the constituent signals up front, then each value's condition references the combined pattern.

## Archetype 9: Priority-Rule Classifier

Use when several conditions could legitimately match and you need deterministic precedence rather than "most recent"/"most specific." Explicit If/Else-if/Else block in the prompt; one value is always reached (usually ending in a catch-all like `NA`).

```
Choose only one final result from: [Value1, Value2, Value3, Value4].
Interpret meaning, not exact wording. Consider close variants and natural phrasing: [list per value].
Priority rules:
If [highest-priority condition], return [Value A].
Else if [next condition], return [Value B].
Else if [next condition], return [Value C].
Else return [Value D].
```

Worked examples in the ed-tech catalog: `contact_validity_status` (Wrong_Number > Do_Not_Contact > Valid_Contact > Not_Specified) and `call_outcome` (an 11-value, 11-rule priority chain — the most elaborate priority-rule classifier in that pack).

---

## Anti-patterns

**1. Thin one-liner.** `"Determine if the customer is interested. Return Yes or No."` has no scope, no third bucket, no tie-breaker, no guardrail — the LLM over-fits to politeness and over-classifies Yes. Always run the full 7-part skeleton, even for something that feels obviously binary.

**2. Overlapping conditions.** If `Not_Interested`'s condition is "not interested in continuing" and `Busy`'s condition is "not available to talk," both could fire on "I'm busy right now, not interested at the moment." Fix: make the conditions describe mutually exclusive behavior — declined-the-offer vs. willing-but-unavailable, not two framings of the same utterance.

**3. Missing the couldn't-determine bucket.** A conditional-branch question (e.g. relocation, asked only after a No on location) with only Yes/No forces every call where the question was never reached into a wrong answer. Add `NA`/`Not_Asked`.

**4. Conflating distinct states.** "Already purchased elsewhere" lumped into `Not_Interested` destroys a differently-actionable signal (converted-elsewhere lead vs. rejected lead). Split them.

**5. Referencing the agent prompt or flow sections.** The extraction LLM receives only `question` (+ `system_prompt`) and the transcript — never the agent prompt, never section numbers. "Section 4 Branch A" means nothing to it. Describe the observable behavior instead ("agrees to receive the checkout link and gives clear consent to proceed").

**6. Inconsistent value naming.** Mixing `Yes`, `Disqualified - Location`, `Do_Not_Contact`, `no answer` in one list breaks every downstream parser/dashboard filter. Pick one convention, hold it for the whole `objective_options` list.

**7. Hallucinating specifics.** If the brief says "lead qualification call" without naming a city, product, or company, don't invent "Bengaluru delivery rider" — write it generic and note the assumption, or ask (thin-brief path only).

**8. Forgetting multilingual handling.** For mixed-language deployments, `Return Yes if the customer says "yes"` underperforms. Spell out: "Interpret meaning, not exact wording. Consider close variants: haan, ji haan, theek hai, le lo, order kar do, yes, sure, okay."

**9. Splitting the skeleton across `question` and `system_prompt`.** The 7-part skeleton is one coherent unit; don't move guardrails or tie-breakers into `system_prompt` just because it "feels like setup" — `system_prompt` is for framing shared across multiple dispositions on the same agent, not a place to hide skeleton parts.

---

## Design judgment notes (for building a whole pack, not just one extraction)

**Resume-this-conversation vs. book-a-new-one are different extractions, always.** A callback ("I'm busy, call me back later to finish *this* conversation") and a next-step engagement ("sure, have someone call me about pricing") look similar in a brief but drive different downstream actions — a callback re-dials the same agent/context, a next-step engagement often routes to a different person or team entirely. Keep them as two separate dispositions even when a user asks for "one scheduling extraction."

**Separate what the contact *is* from where the lead *stands*.** Profile/identity fields (name, qualification, preferences, anything that describes who the person is) answer a different question than funnel fields (qualification status, sentiment, outcome, anything that describes where they are in the process). When a brief conflates the two ("track whether they're qualified and what their background is in one field"), split it — a single extraction trying to do both jobs produces noisy, hard-to-report-on values.

**Nested dispositions earn their keep only when the sub-category is conditional on the top-level answer.** If "the issue type" only makes sense after "Facing_Issue," or "which assistance type" only makes sense after "wants financial help," that's a real Layer 1/Layer 2 split (see Archetype 4). If the two facts are independent of each other, they're two flat extractions, not one nested one — don't nest just because two related questions exist.

**When multiple values could legitimately match, decide priority order once, in the prompt — not at read time.** This is Archetype 9. The recurring real-world case: an operational blocker (wrong number, do-not-contact, never connected) should always outrank a sales-funnel outcome (interested, qualified, converted), because a lead that can't be re-contacted isn't actionable regardless of how interested they sounded.

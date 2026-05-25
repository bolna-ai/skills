# Transcript Diagnosis and Fix Workflow

When the user pastes a Bolna call transcript and asks for improvements (sometimes together with the current prompt, sometimes just the transcript), follow this workflow.

## Step 1: Read the whole transcript before judging

A single bad turn often traces back to an earlier setup failure. Read the full transcript end to end. Note which language the agent and caller spoke, where the agent acted out of role, and where the flow felt unnatural.

## Step 2: Identify successes and failures separately

Make two private lists:

- **What the agent did right** — useful for not over-patching things that are already working.
- **What the agent did wrong** — the actual fix surface.

Failures usually fall into one of these patterns:

| Symptom in transcript | Section/subsection at fault |
|---|---|
| Agent quoted a fee, date, or detail that isn't in the prompt | `# Guardrails`, or Section 8 (Context) is missing the data |
| Agent restarted a section after handling an FAQ | `# Conversation Structure and Flow` — flow recovery rule unclear |
| Agent stacked acknowledgements ("Okay, alright, sure, so...") | `# Conversational Naturalization` was modified or removed — restore verbatim |
| Agent read a phone number with country code or as a single chunk | Phone number capture instruction missing the digit-by-digit / three-group rule |
| Agent read out raw digits like "5000 rupees" | `# Numeric Expression Rules` missing, or numbers in Context JSON stored as numerals |
| Agent pronounced an acronym as a word ("SBI" as "sibby") | `# Pronunciation and Script Normalisation` was paraphrased — restore verbatim |
| Agent kept asking the same question after vague caller responses | `# Ambiguous Response Handling` subsection missing |
| Agent agreed to commitments outside the company's policy | `# Guardrails` missing the relevant restriction |
| Agent used exclamation marks or sounded performative | Tone subsection drifting, or static module modified |
| Agent jumped to closing without trying objection handling | `# Objection Handling` subsection missing or threshold for graceful exit too low |
| Agent looped on the wrong branch | Branch routing instruction unclear — rewrite the routing prose as explicit Section/Question/Branch pointers |
| Agent switched language when caller didn't ask for it | `# Language` switching rule missing or contradictory |
| Agent failed to capture a value (name, number, email) | Capture module missing — paste from `reusable-modules.md` |
| Agent disclosed it is an AI | `# Identity` lacks the explicit non-disclosure clause, or `# Guardrails` missing it |
| Agent asked the caller to repeat themselves multiple times | Speech style needs a "repeat back once, then accept" rule, or `# Ambiguous Response Handling` missing |

## Step 3: Map each failure to the smallest fix

For every failure, decide whether the fix is:

- **A patched subsection** — when one Section 1 subsection or one Question's instruction needs tightening. Output just the patched block(s).
- **A new subsection** — when the original prompt lacked a guardrail, edge case, or ambiguity rule entirely. Output the new subsection in the correct slot.
- **A full prompt rewrite** — when failures span multiple sections or the original prompt structure doesn't match the mandatory format. Output the full prompt.

Lean toward the smallest fix. A patched paragraph is easier for the user to apply than a full rewrite, and it preserves the parts that were working.

## Step 4: Write the fix in the exact format defined by the skill

All format rules from `SKILL.md` apply to the fix output:

- Hindi or Hinglish lines first, English second.
- Devanagari for Hindi script, Roman for naturally English loanwords.
- Instructions as continuous paragraph prose, passive voice, in English.
- Routing as explicit Section/Question/Branch references.
- No forbidden symbols in spoken text.
- Numbers in words.
- Variables in the right notation: `{preloaded}` vs `[context]`.

If the original prompt used a slightly different style (for example, `Instruction:` vs `Instructions:`), match the original prompt's style in the patch — consistency within a single prompt matters more than matching the skill's default.

## Step 5: Always include a short change-note

After the patched content, write a brief note (three to six sentences, prose, no bullets) explaining:

1. What the transcript revealed went wrong.
2. Which section/subsection you changed and why.
3. What behaviour the fix is expected to produce on the next call.

Keep the note plain and useful. The reader is the person debugging the bot, not a stakeholder needing a status update.

## Worked diagnosis example

> **Transcript excerpt:**
> Agent: "Hi, this is Rahul calling from Bolna. Aapka loan ka payment due hai. Aap toh paisa de denge na?"
> Caller: "Kaun bol raha hai? Kis baare mein call hai?"
> Agent: "Sir, payment ka issue hai. Late fee bhi lag raha hai."
> Caller: "Mujhe samajh nahi aaya..."
> Agent: "Okay, alright, sir, payment urgent hai!"
>
> **Diagnosis:**
> - The agent skipped identity verification — never confirmed whether the caller is the named customer. Trace: opening line in Section 2 is too thin.
> - The agent stacked two acknowledgements ("Okay, alright"). Trace: Conversational Naturalization module was paraphrased or removed.
> - The agent used an exclamation mark in delivery and the prompt allowed it. Trace: Guardrails missing the no-exclamation rule, or Tone drifted.
> - The agent did not handle the caller's confusion ("Mujhe samajh nahi aaya") with a paraphrase — it doubled down on the same demand. Trace: Ambiguous Response Handling subsection missing.
> - The agent's purpose statement was abrupt ("Aap toh paisa de denge na?") rather than respectful. Trace: Tone subsection too aggressive for a collections call.
>
> **Fix:** rewrite Section 2 to verify identity and state purpose courteously; restore Conversational Naturalization verbatim from `static-modules.md`; add `# Ambiguous Response Handling` to Section 1; tighten `# Guardrails` to forbid exclamation marks and demanding language.

The output to the user would then be the patched Section 2 block, the restored Conversational Naturalization module, the new Ambiguous Response Handling subsection, and a tightened Guardrails paragraph — followed by the short change-note.

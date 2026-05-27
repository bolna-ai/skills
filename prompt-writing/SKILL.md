---
name: bolna-voice-prompt
description: Author production-grade prompts for Bolna outbound and inbound voice agents (Hindi/English/Hinglish), and diagnose-and-fix existing prompts from call transcripts. Use this skill whenever the user describes a calling-bot or voice-agent use case (e.g. lead qualification, recruitment screening, appointment booking, onboarding calls, renewal/collection calls, NPS, surveys), pastes a Bolna or voice-agent transcript and asks for improvements, asks for an Indian-language calling script, or mentions Bolna, GPT-4.1 mini voice agents, IVR scripts, telecaller bots, or similar — even if they do not name "Bolna" explicitly. This skill produces output in a very specific structure (numbered sections, Hindi-first/English-second scripted lines, paragraph-prose instructions, YAML FAQs, JSON context blocks) and that structure is non-negotiable, so always consult this skill before drafting any voice-agent prompt.
---

# Bolna Voice Prompt Engineering

This skill produces production-ready prompts for Bolna voice agents running on GPT-4.1 mini. The format is rigid by design — GPT-4.1 mini executes these prompts at call-time, and any drift in structure, variable notation, or language ordering degrades reliability. Treat the rules in this file as load-bearing.

## What this skill covers

Two workflows, both triggered by the user:

1. **New prompt from a use-case description.** The user describes a calling scenario (recruitment screening, appointment booking, NPS, renewal, lead qualification, etc.) and any preloaded variables they have. Output: a full prompt following the exact structure below.
2. **Fixing an existing prompt from a transcript.** The user pastes a call transcript (sometimes alongside the current prompt) and points at problems. Output: either the patched section(s) or a full updated prompt, with a short change-note. See `references/transcript-workflow.md` for the diagnostic approach.

If agent gender, primary language, or the primary call goal is unclear from the user's brief, ask one focused clarifying question before drafting. If those three are clear, draft the whole prompt straight away — don't pepper the user with questions for things you can reasonably infer (call direction, role title, branch coverage).

## Before drafting: always load the static modules

Two subsections in Section 1 — `# Conversational Naturalization (Acknowledgements & Flow Softening)` and `# Pronunciation and Script Normalisation` — must be copied verbatim into every prompt. Read `references/static-modules.md` and paste the contents into the new prompt. Do not paraphrase, summarise, shorten, or "improve" these modules. They are tuned and changes break agent behaviour.

## The mandatory section structure

Every prompt is organised in this exact order. Section numbers are not optional. Section 1 always uses the named subsections below; flow sections (3 onward) are named after what they do.

### SECTION 1: IDENTITY AND DEMEANOUR

Section 1 acts globally — it governs everything that follows. Both `SECTION 1: IDENTITY AND DEMEANOUR` and `SECTION 1: DEMEANOUR AND IDENTITY` appear in production and are both acceptable; pick one and hold it for the whole prompt. `SECTION 1: Demeanour & Identity` (mixed case with `&`) is also valid — `&` is permitted in section and subsection titles (see "Special formatting" below).

Use these subsections, introduced with `#`. The canonical order is below, but production prompts occasionally swap Tone/Goal or insert Context/Environment between Identity and Tone — that's fine as long as each subsection still has one clear job:

- `# Identity` — opens with a fixed bracketed-label header line and then a descriptive paragraph. The header line takes one of two forms, both seen in production:
  - `You are [Agent_name: Shivani], [Gender: Female]`
  - `[Agent_name: Juhi], [Gender: Female]`
  The brackets here are a labelled-metadata convention, **not** context variables — do not try to populate them from any captured value. The paragraph that follows names the agent's role, the company being represented, and an identity statement that must hold across the whole call (including the non-disclosure-of-AI clause).
- `# Tone` — three to four lines describing how the agent should sound. Align with the client's brand. Reach for words like professional, warm, calm, confident, respectful.
- `# Goal` — the single primary call objective, stated in action terms. If different scenarios have different goals (e.g. confirming an interview vs rescheduling it), name each goal explicitly.
- `# Guardrails` — strict behavioural boundaries: what the agent must do, must never do, must avoid. Include client-specific restrictions (e.g. "never quote pricing not present in Section 8") and fixed rules (no exclamation marks, no monologuing).
- `# Language` — primary language, secondary languages, the language to open the call in, and the switching rule (typically: match whichever language the caller speaks; if the caller switches mid-call, the agent switches accordingly).
- `# Conversation Structure and Flow` — how the call progresses end to end, mandatory vs optional steps, how the agent returns to the main flow after handling an FAQ or side query, and how it must not restart earlier sections.
- `# Handling Customer Queries` — how the agent listens before responding, keeps answers aligned with the current section's objective, paraphrases politely when clarification is needed instead of repeating verbatim, and defers out-of-scope questions to a senior teammate. The noun in this header (and throughout Section 1) tracks the caller role: `# Handling Partner Queries` for Porter, `# Handling Employee Queries` for Zepto/CureFoods recruitment, `# Handling Candidate Queries` for OEG, `# Handling Learner Queries` for upGrad. Pick one caller noun for the whole prompt and use it consistently.

Then the two **static modules** (copy verbatim from `references/static-modules.md`):

- `# Conversational Naturalization (Acknowledgements & Flow Softening)`
- `# Pronunciation and Script Normalisation`

After the static modules, add any extra Section 1 subsections the use case requires. Optional subsections that appear in production:

- `# Context` — short paragraph describing the call situation (used in recruitment-style prompts like Whizzy, Zepto, CureFoods).
- `# Environment` — short paragraph describing the caller's likely environment (used in Whizzy, Announcements).
- `# Ambiguous Response Handling`, `# Speech Style`, `# Eligibility Criteria`, `# Edge Cases`, `# Discount Logic`, `# Objection Handling`, `# Upsell Triggers`, `# Numeric Expression Rules`, `# For Hindi Conversation` (a Schoolini pattern for tone-shaping the Hindi delivery). Whatever the use case needs.

### SECTION 2: CONVERSATION STARTER

The opening line, written in all required languages in fixed order (Hindi/Hinglish first, English second, any third language third), followed by its instruction block. This section always exists.

### SECTION 3 ONWARDS: USE-CASE FLOW SECTIONS

Numbered sequentially and named after what they do — `SECTION 3: INTENT DETECTION`, `SECTION 4: BASIC DETAILS COLLECTION`, `SECTION 5: ELIGIBILITY CHECK`, `SECTION 6: APPOINTMENT BOOKING`, and so on. These contain the actual questions, branches, and routing.

### SECTION X: CLOSING

Always the second-last section. Multiple branches — `BRANCH A: Successful Close`, `BRANCH B: Not Interested`, `BRANCH C: Rescheduling`, `BRANCH D: Wrong Number`, etc. — each named for the outcome it handles.

### SECTION X: CONTEXT (when needed)

A structured JSON knowledge base for pricing, product catalogues, location data, policy facts. Only include if the flow needs to look something up. Format described in `references/section-templates.md`.

### SECTION X: FAQ (always last)

Strict YAML. Format in `references/section-templates.md`.

For the section templates with the exact opening/question/closing/branch format, see `references/section-templates.md`.

## Variable notation — never mix

There are exactly two variable types, and mixing them breaks the call.

- **Preloaded variables**: known before the call, passed from CRM/backend/API. Curly braces with underscores: `{full_name}`, `{contact_number}`, `{appointment_date}`. No spaces inside the braces.
- **Context variables**: captured during the call from caller responses, or used to raise an internal flag. Square brackets with underscores: `[name]`, `[contact_number]`, `[preferred_time]`, `[wants_callback]`. No spaces inside the brackets.

**Only use preloaded variables the user has explicitly listed.** Do not invent extra ones. If the use case needs a piece of data the user did not list, capture it as a context variable inside the conversation.

A common pattern: assign a context variable from a preloaded one at the top of a question, e.g. `You have the values [name] = {referee_name}.` This lets the prompt reference `[name]` cleanly downstream while making the source explicit.

## Scripted-text format

Every scripted line — opening, question, closing, fixed responses — exists in both languages, in fixed order. Hindi (or Hinglish) **always first**, English **always second**, any third language third. This order never reverses.

```
Opening (Hindi): [Devanagari script]
Opening (English): [English text]
```
```
Question 1 (Hindi): [Devanagari script]
Question 1 (English): [English text]
```
```
Closing (Hindi): [Devanagari script]
Closing (English): [English text]
```

If the use case is explicitly Hinglish (mixed Hindi-English, written largely in Devanagari with embedded Roman words), the label is `(Hinglish)` instead of `(Hindi)` and it still goes first.

### Devanagari rules inside Hindi lines

- Hindi lines are written in Devanagari script.
- English loanwords commonly used in Indian conversation stay in Roman script even inside a Hindi line: `app`, `WhatsApp`, `form`, `session`, `login`, `OTP`, `link`, `email`, `call`, `number`, `register`, `confirm`, `please`, `thank you`, `okay`, `sorry`. Do not transliterate these.
- Acronyms are spelt out letter-by-letter in Devanagari phonetic form when spoken in a Hindi sentence — `SSC` → `एस एस सी`, `UPI` → `यू पी आई`, `EMI` → `ई एम आई`. (The `# Pronunciation and Script Normalisation` module handles the broader rule globally.)

### Numbers in scripted text

All numbers in scripted lines and FAQ answers are written in worded form, in the surrounding language. "Five thousand rupees", not "5000 rupees". "Thirty percent", not "30 percent". "Six months", not "6 months". This applies to fees, durations, percentages, ages, distances, salary figures, exam scores — everything spoken. Numbers inside variable names or technical references (e.g. `Section 4 Question 3`) stay numeric.

Phone numbers and identifier digit sequences are spoken digit-by-digit and follow the rules in `references/reusable-modules.md`.

## Instruction writing rules

Every scripted line is followed by an instruction block. Instructions are **continuous paragraph prose** — no bullets, no numbered lists, no dashes, no pointers of any kind inside an instruction paragraph.

Each instruction starts with `Instruction:` (or `Instructions:` — both appear in reference prompts, pick one and stay consistent within a single prompt). It covers:

- The objective of the line (why this question exists).
- The expected caller behaviour and how to interpret it.
- Edge cases (vague replies, declines, requests for clarification, language mismatches).
- The exact routing logic, written as prose: *"If the caller responds affirmatively, move to Section 4, Question 2. If the caller declines, move to Section 7, Branch B. If the caller asks an out-of-scope question, briefly defer to the senior counsellor and return to Section 4, Question 1."*

Instructions are written in **passive voice** and are invisible to the caller — never let an instruction reference itself ("as the instruction says" is forbidden). Instructions are also written entirely in English, even inside a Hindi-heavy prompt. Only the spoken Hindi lines themselves are in Devanagari.

### Standard closing instruction

Use this verbatim for most closing branches unless the scenario demands custom routing. This is the exact wording used across ADDA, Porter, OEG, upGrad, CureFoods, LPU, and Schoolini production prompts:

> Instructions: Make sure that you are speaking the closing as it is. This closing statement is designed to professionally conclude the conversation, ensuring a respectful and neutral closure. The AI should deliver the closing message warmly and clearly, avoiding abruptness or over-promising about outcomes. Maintain a courteous tone throughout. No follow-up or probing is necessary here; the goal is to end the interaction smoothly and on a positive note. No additional follow-ups or questions are required at this point.

For Hindi-only or empathetic closes (e.g. Porter's empathetic variant for health/family issues), keep the opening line "Make sure that you are speaking the closing as it is." and then add the situation-specific note in front of the rest of the standard wording.

## Branching and numbering

- Linear questions in a section are numbered sequentially: Question 1, Question 2, Question 3.
- When a branch opens **after** a question, the first question inside the branch **continues** the previous numbering. (If Question 3 ends a linear stretch and Branch A starts, Branch A begins at Question 4.)
- When multiple branches sit at the **same** decision point (parallel branches off the same question), the first question number is the **same** in each branch, because they originate from the same point.
- Branch labels: `BRANCH A: [SHORT DESCRIPTION]`, `BRANCH B: [SHORT DESCRIPTION]`, etc. The all-caps form is the dominant style (ADDA, Porter, OEG, upGrad, Schoolini, LPU); `Branch A: Title Case Description` also appears (CureFoods) and is acceptable — be consistent within a single prompt. In closing sections, the description names the outcome (Successful Close, Not Interested, Rescheduling, Wrong Number, Relative Answered, Out-of-Service Area). Deeply nested branches use dotted suffixes: `BRANCH A.1`, `BRANCH A.2` (ADDA pattern, used sparingly).

## Content generation rules blocks

When the agent must handle a situation contextually rather than from a pre-scripted line, open the subsection with a bracketed rules block:

```
[
Content generation rules:
- Rule one
- Rule two
- Rule three
]
```

This is the **only** place dashes and bullet-style formatting are acceptable in the prompt body, alongside the static Conversational Naturalization module which already uses dashes internally. Every Edge Cases, Objection Handling, Upsell Triggers, and Discount Logic subsection must open with one of these blocks.

For edge cases, follow the rules block with each case spelled out as: a clear Trigger, a Response in both languages, and an Instruction paragraph for routing.

For objection handling, keep responses to three sentences maximum, conversational, in both languages, with one pivot maximum per objection. Two consecutive declines from the caller must trigger a graceful close — encode that explicitly.

For upsell, define the trigger condition and the upsell response in both languages. Maximum one upsell per call.

For discount logic, write the step-by-step rules **inside** the content generation rules block (not as bullets in the main body).

## FAQ section (YAML)

Always present, always last, always YAML. Open with a content generation rules block:

```
[
Content generation rules:
- This section includes answers to common questions callers may ask during the conversation.
- Always keep the answers to the point, clear, and aligned with the tone defined in Section 1.
- After answering an FAQ, the agent must smoothly return to the exact point in the conversation flow where the interaction was paused.
- If the caller asks something not listed here, the agent must not generate a speculative answer and should politely defer to the sales or support team.
]
```

Then list entries:

```
- id: 1
  question:
    en: "[English question only]"
  keywords:
    - "keyword one"
    - "keyword two"
    - "keyword three"
  answer:
    en: "[English answer]"
    hi: "[Hindi answer in Devanagari]"
```

Questions are written in **English only**. Answers are in both languages. Maximum six keywords per FAQ. Keywords can mix Hindi and English terms.

For the context JSON format and worked YAML examples, see `references/section-templates.md`.

## Special formatting and spoken-line rules

These hold across every spoken line and instruction in the prompt:

- **Forbidden symbols inside scripted spoken text and instruction paragraphs**: `!`, `/`, `@`, `%`, `#`, `&`, `$`. These symbols **are** permitted in section and subsection titles where they're idiomatic — `# Conversational Naturalization (Acknowledgements & Flow Softening)`, `SECTION 1: Demeanour & Identity`, `SECTION 9: FAQ's`, `# Handling Customer Queries` — because the heading marker isn't spoken at runtime. The ban applies to any line the TTS will read aloud (Opening, Question, Closing, Response, FAQ answer) and to instruction paragraphs (where these symbols can be misread as routing or formatting cues). The `#` symbol is allowed as a heading marker for Section 1 subsections.
- **No `-` or `—` inside spoken dialogue lines.** Dashes are permitted only inside content generation rules blocks and inside the static Conversational Naturalization module (which uses them internally — that's fine, you're copying it verbatim).
- **No exclamation marks in spoken lines.** Ever. The Conversational Naturalization module also forbids them — this is a TTS pacing concern, not a stylistic one.
- **All numbers in scripted messages and FAQ answers are written as words**, in the correct surrounding language. See "Numbers in scripted text" above.
- **One acknowledgement per agent turn, never stacked.** Use contextual replies — apologising, thanking, probing — based on the caller's last message, not a fixed prefix.
- **Agent gender stays consistent across every single line.** If the agent is female, Hindi verb forms and self-references stay in feminine form throughout (हूँ, करूँगी, बताऊँगी). The caller's gender is tracked from conversational signals and adjusted mid-call.
- **No monologuing.** The agent checks in with the caller every two to three sentences.
- **No tables.** Use FAQs or YAML/JSON sets instead.
- **Instructions, guardrails, and all meta-prompting content are in English.** Only the spoken Hindi lines themselves use Devanagari. Never write an instruction or a guardrail in Hindi.

## Consistency rules

- Don't repeat the goal or instructions across subsections. Each subsection has one job.
- Don't introduce contradictions between subsections. Tone, language, and identity must hold from Section 1 through to the closing.
- Once a conversation language is established, it doesn't change unless the caller explicitly asks for the other language.

## Underlying model

The runtime LLM is GPT-4.1 mini. The structure, verbosity, and naming conventions in this skill are calibrated for that model. Resist the urge to introduce markdown decoration, fancier formatting, headers with emojis, or paraphrased rewrites of reference patterns. Match the reference style exactly — section naming, instruction phrasing, spoken-line construction, branching notation. Boring and consistent beats clever.

## Workflow when given a use-case description

1. Read the brief. Confirm agent gender, primary language, and the primary call goal. Ask one focused clarifying question only if any of those three is genuinely unclear.
2. Load `references/static-modules.md` and `references/section-templates.md`. Skim `references/reusable-modules.md` if the use case involves capturing name, phone, email, or numeric inputs. Skim `references/reusable-flows.md` if the use case involves scheduling a callback at a specific date/time or producing a scored evaluation outcome.
3. Draft Section 1: start with the bracketed Identity header (`You are [Agent_name: NAME], [Gender: Female/Male]`), then the Identity paragraph, then the remaining subsections. Paste the two static modules verbatim. Add any extra Section 1 subsections the use case needs (Context, Environment, Eligibility Criteria, Edge Cases, etc.).
4. Write Section 2 (Conversation Starter).
5. Map the call flow into named, numbered sections from Section 3 onward.
6. Write the Closing section with all relevant branches (always at minimum: Successful Close, Not Interested, Wrong Number; add Rescheduling, Relative Answered, Language Mismatch as the use case requires).
7. Add Context (JSON, flat YAML, or markdown-headed sections — see section-templates.md) only if the flow needs lookup data. If you include a Context section, also include the "Answering User Questions" section that opens with a content-generation-rules block explaining how the agent uses Section X (Context) and Section Y (FAQ) — this is a separate section from Context itself.
8. Write FAQ (YAML), always.

The prompt ends at the FAQ. There is no "Variables Reference" or trailing metadata block — none of the production prompts have one. Preloaded variables are introduced inline where they first appear and don't need a glossary.

When in doubt about a section template or a closing branch's wording, open `references/section-templates.md` rather than improvising.

## Workflow when given a transcript

Read `references/transcript-workflow.md`. The short version:

1. Identify where the agent succeeded and where it failed.
2. Map each failure to a section in the prompt it stems from — usually a missing guardrail, a weak branch, an unclear routing instruction, an objection not pre-empted, or a tone drift.
3. Produce either the patched section(s) or the full updated prompt, in the same format defined above.
4. End with a short note (a few sentences) explaining what changed and why.

## Reference files

- `references/static-modules.md` — the two mandatory Section 1 modules to paste verbatim.
- `references/section-templates.md` — full templates and worked examples for every section type, including the Section 1 subsection patterns (with the bracketed Identity header), Section 2 starters, Closing branches, Context format variants (JSON, flat YAML, markdown-headed), and FAQ YAML variants.
- `references/reusable-modules.md` — name, phone-number, email, and numeric-expression collection patterns drawn from production prompts.
- `references/reusable-flows.md` — the date/time callback scheduling block (used identically across CureFoods, upGrad, Porter), the scored-interview evaluation pattern (CureFoods), and the "Answering User Questions" gateway pattern (ADDA, Porter).
- `references/transcript-workflow.md` — how to diagnose a transcript and map failures back to prompt sections.
- `references/multilingual.md` — authoring prompts for `multilingual_config` agents (one agent, multiple language entries each with its own STT/TTS and full Section 1..N prompt).

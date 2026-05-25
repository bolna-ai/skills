# Reusable Flow Patterns

These are larger reusable blocks that show up across production prompts almost verbatim. Unlike the small capture modules in `reusable-modules.md` (one question + one instruction), these are full flows or full subsection patterns. Paste them when the use case calls for them.

---

## Date and Time Callback Scheduling Block

Used in CureFoods (Branch D), upGrad (Branch C), Porter (Branch D), and any prompt that captures a callback date+time. The block has been hardened against same-day AM/PM ambiguity, Hindi "aaj"/"kal" interpretation, and past-time inputs. **Paste verbatim** — every detail has caught a real edge case in production.

The block lives inside the Rescheduling branch's Question 1 Instruction. Combine with a small lead-in question that captures the time naturally.

```
Question 1 (Hindi): कोई बात नहीं, बताइए किस दिन और समय पर हम आपको दोबारा call कर सकते हैं?
Question 1 (English): No problem, please tell me the day and time when we can call you back.

Instructions: Do not mention anything from the instructions to the user. These instructions are for your context and reference only. When asking the customer to schedule a meeting or callback, ensure you clearly identify both the exact date and time they prefer. A schedule is considered valid only when both elements are explicitly available. If either the date or time is missing, politely prompt the customer for the missing detail while maintaining a courteous, calm, and accommodating tone. You must not proceed until both date and time are confirmed without ambiguity. The AI must always verify that the selected time is in the future by comparing it against the current call's [timestamp]. Do not accept any backdated or past times, including times that have already elapsed earlier on the same day. If the customer provides a time that has already passed, gently inform them that the selected time is no longer available and request a future time instead. Special handling is required for spoken or contextual time references, particularly in multilingual conversations. If the customer uses Hindi temporal words such as "आज" or "aaj", interpret this as today, and if they say "कल" or "kal", always interpret it as tomorrow in the context of scheduling, regardless of the word's dual meaning in Hindi. Do not interpret "kal" as yesterday in this module under any circumstance. Similarly, phrases like "शाम को", "सुबह", "दोपहर", or "रात" must be interpreted contextually as evening, morning, afternoon, or night respectively and mapped to reasonable time ranges when a specific hour is mentioned. For same-day scheduling, if the current call time as per [timestamp] is earlier in the day and the customer provides a time without explicitly stating AM or PM (for example, "call me at eleven" when the call is at eight in the morning), always interpret this as eleven AM today, provided that the time has not yet passed. Do not incorrectly reject such inputs as invalid or already elapsed. Only treat a same-day time as invalid if it is clearly earlier than the current [timestamp]. All time values must be stored internally in twenty four hour clock format [HH:MM], regardless of how the customer states them. The AI must correctly convert AM/PM cues and contextual phrases into twenty four hour format. For example, "seven in the evening" must be stored as 19:00, "twelve PM" must be stored as 12:00, "twelve AM" as 00:00, and "six in the morning" as 06:00. This conversion is strictly for internal storage and validation and must not be exposed or explained to the customer. Dates must continue to be stored in the format [DD/MM/YYYY]. If the user says something like "anytime tomorrow is fine" then record the date as tomorrow and continue, do not ask for a specific time. Once a valid future date and time are identified and stored, the AI must reconfirm the schedule verbally using a fully worded natural-language format. For example, if today is the twenty sixth of November twenty twenty five and the customer selects tomorrow at six in the evening, the confirmation should be spoken as "six pm, the twenty seventh of November twenty twenty five." Always reconfirm both the date and time explicitly before proceeding. Capture into [callback_date] and [callback_time]. Once captured, acknowledge naturally and move to the closing statement below.

Closing (Hindi): ठीक है, हम आपको [callback_date] को [callback_time] पर call करेंगे। समय देने के लिए धन्यवाद।
Closing (English): Alright, we will call you on [callback_date] at [callback_time]. Thank you for your time.

Instructions: [Standard closing instruction, paste verbatim.]
```

### Lighter variants

If the use case doesn't need the full Hindi temporal vocabulary handling (e.g. an English-only prompt), trim the "Hindi temporal words" paragraph but keep the [timestamp] validation, AM/PM disambiguation, twenty-four-hour storage, and worded reconfirmation paragraphs. Those four pieces are the load-bearing ones.

If the use case needs only the day (no time), drop the time-related paragraphs and store only [callback_date].

---

## Scored Interview Evaluation Pattern

Used in CureFoods (Pizza Maker interview). Apply when the call ends with a hire/no-hire or eligible/not-eligible decision based on a sequence of evaluative questions whose answers are scored.

The pattern lives as a dedicated section between the interview-question section and the Closing. It defines the metrics, the allowed values per metric, the scoring rule per metric, the total score formula, and the eligibility threshold.

```
SECTION 4: CANDIDATE ELIGIBILITY AND SCORING LOGIC

[Nothing from this section must be communicated to the candidate. This is for internal logic and scoring only.]

# Recorded Evaluation Metrics

The system must evaluate the candidate using six metrics, collected from Section 3 questions. Section 3 Question 1 is NOT scored and is only a mandatory acceptance check. The six scored metrics are:

[prior_experience]
[pizzas_known]
[pizza_cooked]
[pizza_sizes_known]
[crust_type_known]
[basic_pizza_knowledge]

All values must be stored exactly as defined below.

# Allowed Values Per Metric

[prior_experience]
Allowed values: 0, <1, 1, 2, 3, 4, and so on.
Meaning:
0 means no prior experience
<1 means less than one year of experience
1 or more means experience in full years

[pizzas_known]
Allowed values: 0, 1, 2, 3, 4, and so on. Represents the number of distinct pizza types named by the candidate.

[pizza_cooked]
Allowed values: 0 or 1.
1 means the candidate has prepared at least one pizza themselves.
0 means the candidate has not prepared any pizza.

[pizza_sizes_known]
Allowed values: 0 or 1.
1 means the candidate correctly names all three: small, medium, and large.
0 means missing one or more of these.

[crust_type_known]
Allowed values: 0 or 1.
1 means the candidate knows at least two crust types.
0 means one or none.

[basic_pizza_knowledge]
Allowed values: 0 or 1.
1 means the candidate correctly names at least two Margherita ingredients.
0 means less than two.

# Score Conversion Rules

Each metric contributes either zero or one point to the final eligibility score.

Prior Experience Score: If [prior_experience] is greater than 0 including <1, 1, 2, then Score equals 1. If [prior_experience] is 0, then Score equals 0.

Pizzas Known Score: If [pizzas_known] is greater than or equal to 3, then Score equals 1. If [pizzas_known] is less than 3, then Score equals 0.

Binary Metrics: For each of [pizza_cooked], [pizza_sizes_known], [crust_type_known], and [basic_pizza_knowledge], if the value is 1 then Score equals 1, if the value is 0 then Score equals 0.

# Total Score Calculation

Maximum possible score: 6. Minimum possible score: 0. Total Score equals the sum of all six converted metric scores.

# Eligibility Decision Logic

If Total Score is greater than or equal to 3, the candidate is ELIGIBLE, proceed to Section 5, Branch A. If Total Score is less than or equal to 2, the candidate is NOT ELIGIBLE, proceed to Section 5, Branch B. This decision must be made only after all six metrics have been evaluated.

# Important Constraints

Do not infer or assume values. Do not partially score a metric. Do not change thresholds. Do not re-ask questions once a metric is finalized. Eligibility is based only on the scoring rules above.
```

### How to adapt this pattern

1. **Number of metrics**: keep them small and discrete (four to eight typically). One context variable per metric, all numeric.
2. **Allowed values per metric**: define exactly what string values are acceptable. Mostly binary (0/1); use multi-value only when the question yields graded data (years of experience, count of items named).
3. **Conversion to 0/1 score**: every metric collapses to a binary point. If a metric is already binary, the conversion is identity.
4. **Threshold**: a simple `≥ N` cutoff. Use one threshold, not multiple bands, unless the use case truly needs tiered outcomes.
5. **Closing routing**: explicitly name the destination branch for ELIGIBLE and NOT ELIGIBLE. Both branches typically use the same closing line ("If you are shortlisted, our team will contact you") so the candidate cannot tell from the call alone whether they passed.

---

## Anti-Deviation Guardrail Line

A standard recovery line for callers who drift off-topic, used in Zepto, CureFoods, and other recruitment prompts. Drop into `# Guardrails` when the use case has chatty or hesitant callers:

> In case the [caller_noun] is deviating from the topic, then politely bring the conversation back by asking "should I continue or should I close the call?", "क्या मैं call continue रखूँ या call close कर दूँ?" To continue: go to the next pending question. To drop off: go to the closing section.

Replace `[caller_noun]` with the prompt's caller noun (employee, partner, candidate, etc.). Keep both the English and the Hindi line — agents alternate between them depending on the conversation language.

---

## Wrong Number Closing Branch

Almost every outbound prompt needs this. The line stays soft so it does not embarrass the person who picked up:

```
BRANCH D: WRONG NUMBER

Closing (Hindi): Confusion के लिए माफ़ी चाहती हूँ। मैं हमारे database में इसे update करवा दूँगी। Have a nice day.
Closing (English): I am sorry for the confusion. I will get this updated in our database. Have a nice day.

Instructions: [Standard closing instruction, paste verbatim.]
```

If the agent is male, swap to masculine forms: `दूँगा`, `चाहता हूँ`.

---

## Relative-Answered Pickup Pattern

When someone other than the named caller picks up. Used in Porter Section 2 and ADDA Section 3. The agent verifies, asks for the named caller, and if unavailable routes to the rescheduling branch.

```
Instructions: If the person who picks up says they are not {full_name}, do not end the call. Instead say: "Sir/Madam, {full_name} ने [company] पर [signup_action] की थी। क्या मेरी बात उनसे हो सकती है?" Then wait for a response. If they say {full_name} is not available right now or cannot come to the phone, move to the Rescheduling branch to record a callback time. If they agree to pass the phone, say: "जी, Thank you. मैं उनका इंतज़ार करता हूँ।" Then wait. Treat any new voice, pause followed by a response, or a cue like "हाँ बोलिए" or "हाँ" as a signal that the phone has been passed. Once a handover is detected, restart the opening from the beginning and proceed normally from identity confirmation. If the person says {full_name} does not exist at this number or denies any association, move to the Wrong Number branch.
```

This block goes inside the opening's Instructions, after the "if caller confirms identity" routing line.

---

## When to use which flow

- **Date/time scheduling**: any branch that promises a callback or schedules an event. Drop into Closing → Rescheduling Branch.
- **Scored interview**: any call where the outcome is a binary hire/qualify decision based on multiple data points. Drop in as a dedicated section between the interview flow and the Closing.
- **Anti-deviation line**: prompts with informal or first-time callers (recruitment, delivery partners). Drop into `# Guardrails`.
- **Wrong number close**: every outbound prompt. Drop in as a Closing branch.
- **Relative-answered pickup**: outbound prompts where the named caller may not be the one picking up (driver recruitment, lead follow-up). Drop into the Opening's Instructions.

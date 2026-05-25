# Reusable Capture Modules

Four patterns that recur across nearly every Bolna prompt: capturing a name, a phone number, an email, and any spoken numeric expression. These have been tuned against real call transcripts. Use them wherever the flow needs to capture one of these fields, and adapt the surrounding language to the use case.

---

## Name capture

Use when the prompt has a `{full_name}` preloaded and needs to confirm it, or when the flow needs to capture a name from scratch.

### Confirming a preloaded name

```
Question X (Hindi): क्या आपका पूरा नाम [name] है?
Question X (English): Is your full name [name]?

Instruction: You have the value [name] = {full_name}. If the conversation language is Hindi, generate [name] in Devanagari using the Pronunciation and Script Normalisation module. The objective of this question is to confirm the caller's full name for the record. If the caller indicates affirmation, move to Section [X], Question [X+1]. If the caller indicates the name is incorrect or wants to update it, allow them to state the full name without interruption and capture it into [name]. Repeat the corrected name back to confirm accuracy, character by character only if the spelling is ambiguous. If the caller gives a vague or unclear response such as "ji", "madam", "kya bola", or "phirse", repeat the [name] once again to confirm rather than asking them to restate it. Do not ask the caller to spell their name unless they explicitly indicate the captured name is incorrect. Once confirmed, proceed to Section [X], Question [X+1].
```

### Capturing a new name from scratch

```
Question X (Hindi): क्या आप अपना पूरा नाम बता सकते हैं?
Question X (English): Could you please share your full name?

Instruction: The objective is to capture the caller's full name. Allow the caller to finish speaking without interruption. Capture the response into [name]. Always confirm the captured name by reading it back once. If spelling is ambiguous (uncommon names, Roman-script input), confirm character by character using clear phonetic cues, for example "Sandeep, that is S, A, N, D, E, E, P, correct?" If the caller corrects only part of the name, repeat back only the corrected portion and treat already-confirmed parts as final. If the caller declines to share their name, acknowledge politely and record [name] = "NIL". Names should always be recorded in the Roman alphabet regardless of spoken language. Once captured or marked NIL, proceed to Section [X], Question [X+1].
```

### Hindi name pronunciation rule

Inside Hindi lines, Indian names spelled in Roman script in the preloaded variable must be rendered in Devanagari for TTS accuracy. The `# Pronunciation and Script Normalisation` module already covers this globally, so the flow instruction can simply say: "If the conversation language is Hindi, generate [name] in Devanagari." Non-Indian names stay in Roman.

---

## Phone number capture

Use when the prompt has a `{contact_number}` preloaded and needs to confirm it, or when the flow needs to capture a new one.

### Confirming a preloaded phone number

```
Question X (Hindi): क्या आपका phone number यही है, [contact_number]?
Question X (English): Is this your phone number, [contact_number]?

Instruction: You have the caller's contact number as [contact_number] = {contact_number}.
- If [contact_number] starts with +91, strip the +91 prefix. Example: +918680937292 becomes "8680937292". Never read or include the country code +91.
- If [contact_number] starts with 91 and the total length is twelve digits, strip the leading 91. Example: 918680937292 becomes "8680937292".
- After cleaning, [contact_number] must be exactly ten digits.

The objective of this question is to confirm the ten-digit number accurately. Always read the entire ten-digit number digit by digit, slowly. If the conversation language is English, read each digit in English: nine, eight, seven, six, and so on. If the conversation language is Hindi, read each digit in Hindi: नौ, आठ, सात, छह. When restating for confirmation, break the number into three groups for natural pacing: first three digits, short pause, next three digits, short pause, last four digits. For example, 8495774510 is read as "eight four nine, five seven seven, four five one zero".

If the caller gives a vague response like "ji", "madam", "kya bola", or "phirse", repeat the [contact_number] once again to them rather than asking them to restate. If the caller indicates the number is correct, proceed to Section [X], Question [X+1]. If the caller indicates the number is incorrect or wants to update it, move to the new-number capture below.
```

### Capturing a new phone number

```
Question X (Hindi): ठीक है, please अपना सही phone number बताइए।
Question X (English): Alright, please share your correct phone number.

Instruction: The objective is to capture a new ten-digit phone number. Do not interrupt the caller; wait for them to finish. Interpret verbal inputs naturally: "double two" as 22, "triple zero" as 000, "double seven" as 77. Do not announce or explain this interpretation to the caller. If the caller gives the number in parts or with hesitation, capture all digits and combine into a single ten-digit string. Always confirm by reading the captured number back digit by digit in three-group format described in the previous question. If the caller corrects only part of the number, identify the corrected portion by pattern matching, repeat only that portion back, and update [contact_number] accordingly. For example, if the original was 8495764510 and the caller says "it is seven seven four five one zero", restate as "five seven seven, four five one zero, correct?" and update the value to 8495774510. If the caller declines to share a number, record [contact_number] = "NIL" and proceed to Section [X], Question [X+1]. Once confirmed or marked NIL, proceed to Section [X], Question [X+1].
```

### Common Hindi numeral edge cases

If the caller speaks the number as a combined word (e.g. "उन्यासी तैंतालीस तिहत्तर, छप्पन इकसठ"), politely ask them to repeat digit by digit and read back in single-digit Hindi: "आठ, नौ, चार, तीन..." rather than the combined form.

Hindi number reference for commonly-confused tens (include this in instructions when prompts handle prices or large numbers in Hindi):

- 71-79: इकहत्तर, बहत्तर, तिहत्तर, चौहत्तर, पचहत्तर, छिहत्तर, सतहत्तर, अठहत्तर, उनासी
- 41-49: इकतालीस, बयालीस, तैंतालीस, चौवालीस, पैंतालीस, छियालीस, सैंतालीस, अड़तालीस, उनचास
- 51-59: इक्यावन, बावन, तिरपन, चौवन, पचपन, छप्पन, सत्तावन, अट्ठावन, उनसठ
- 61-69: इकसठ, बासठ, तिरसठ, चौंसठ, पैंसठ, छियासठ, सड़सठ, अड़सठ, उनहत्तर
- 81-89: इक्यासी, बयासी, तिरासी, चौरासी, पचासी, छियासी, सत्तासी, अट्ठासी, नवासी
- 91-99: इक्यानवे, बानवे, तिरानवे, चौरानवे, पचानवे, छियानवे, सत्तानवे, अट्ठानवे, निन्यानवे

72 is बहत्तर (not चौहत्तर) and 74 is चौहत्तर (not बहत्तर) — these two are the most commonly confused.

---

## Email capture

```
Question X (Hindi): क्या आप अपना email ID share कर सकते हैं?
Question X (English): Could you please share your email ID?

Instruction: The objective is to capture the caller's email ID accurately. Common email domains may be pronounced as words: gmail.com as "जीमेल dot कॉम" (phonetic: jeemael.com), yahoo.com as "याहू dot कॉम" (phonetic: yaahoo.com), outlook.com as "आउटलुक dot कॉम". Interpret verbal inputs as follows: "at", "at the rate", "at sign" all mean @; "dot", "dot com", "dot co dot in" mean .com or .co.in; "underscore" or "under score" means _; "dash" or "hyphen" means -. Do not reconfirm this interpretation logic with the caller.

If the caller speaks the email in English like "rahul dot sharma at gmail dot com", repeat it back as "r, a, h, u, l, dot, s, h, a, r, m, a, at, gmail, dot, com". If the caller gives the email in Hindi, repeat it back in Hindi letter names one by one. If the caller gives a grouped or unclear form like "rahulsharma at gmail", politely ask them to repeat the local part one character at a time and confirm character by character.

Do not interrupt while the caller is speaking the email; let them finish through "dot com". Do not rush, do not skip characters, do not guess, do not auto-correct, and do not use symbols or punctuation in your spoken confirmation. Always read "at" as at, "dot" as dot, "underscore" as underscore, and "dash" as dash. If the caller declines to share an email, acknowledge politely and record [email] = "NIL". Once captured or marked NIL, proceed to Section [X], Question [X+1].
```

---

## Numeric expression rules

Add this as a `# Numeric Expression Rules` subsection in Section 1 whenever the prompt handles fees, dates, prices, durations, or any other significant numeric content.

```
# Numeric Expression Rules

All numbers in spoken lines and FAQ answers are expressed in worded form, in the conversation language. Raw digits are never spoken.

For digit sequences such as phone numbers, OTPs, account numbers, and codes, each digit is pronounced separately. Example: 997 is spoken as "nine nine seven", not "nine hundred ninety seven".

For values, fees, prices, and durations, the number is spoken as a full natural figure. Example: 1875 is spoken as "one thousand eight hundred and seventy five". 176875 rupees is spoken as "one lakh seventy six thousand eight hundred and seventy five rupees".

For percentages, the word "percent" replaces the symbol. Example: 15% is spoken as "fifteen percent".

For currency, "Rs" or "INR" is spoken as "rupees" and "USD" as "US dollars". The currency word follows the number.

For placement packages or salary figures expressed in LPA, the phrase "Lakhs per Year" is used. Example: 41 LPA is spoken as "forty one lakhs per year".

For units like km, kg, hours, minutes, days, months, the number is spoken as a full figure followed by the unit word, never digit by digit. Example: 6810 km is spoken as "six thousand eight hundred and ten kilometres", not "six eight one zero kilometres".

For dates, the format is day-month order, not month-day. The day uses ordinal form in English ("first July", "twenty third August"). Years use paired pronunciation in English ("twenty twenty six", not "two thousand twenty six").

For prices in Hindi conversations, the entire price including the rupee word is spoken in Hindi. Example: 72,430 rupees is spoken as "बहत्तर हज़ार चार सौ तीस रुपये", not as raw digits or English number words. Do not use the rupee symbol in any output.
```

---

## When to bundle which module

- **Name capture**: always, if a preloaded name is verified or a new name is captured.
- **Phone number capture**: always, if the prompt verifies a preloaded number or captures a new one. Almost every prompt uses this.
- **Email capture**: only if the flow specifically asks for an email.
- **Numeric expression rules**: any prompt that quotes a fee, a price, a date, a percentage, a duration in months/days, or a placement figure. Most prompts will need this — paste it into Section 1 as a dedicated subsection.

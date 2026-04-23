# Variable 1 / Variable 2 Guardrails

Clay AI variables fail in one predictable way: they hallucinate. The model
reads a LinkedIn description that is vague or in another language, gets
creative, and inserts a noun phrase that does not match the source. Across
5,000 leads, even a 2% hallucination rate means 100 weird emails hitting
inboxes.

The fix is simple: **every Variable prompt must end with an approved
list**. The model picks from the list or returns a safe fallback. Nothing
else.

This single guardrail is the difference between a campaign that scales and
a campaign that embarrasses the client.

## The standard Variable prompt shape

```
[One-line instruction describing what you want.]
Rules:
- Pick ONLY from this approved list:
  [comma-separated safe phrases, between 8 and 20 items]
- If no clean match: return "[safe fallback phrase]"
- [formatting rules: lowercase, no em-dashes, no extra text, etc.]
Input: {{input_field}}
Output: (the phrase only, nothing else)
```

Every part of this shape is load-bearing. Do not drop a line.

## Load-bearing elements explained

1. **`Pick ONLY from this approved list`**, the word ONLY is doing the
   work. Without it, the model treats the list as "suggestions" and adds
   new phrases.
2. **The list must be 8 to 20 items.** Fewer and you get "UAE mid-market
   group" in 60% of outputs (boring). More and the model starts matching
   loosely (hallucinating).
3. **Safe fallback**, a generic phrase that reads fine in any context.
   The fallback is what protects you when the input is garbage or empty.
4. **`(the phrase only, nothing else)`**, forces the model to drop its
   instinct to explain. Without this, you get "The best match here would
   be 'property management firm'" instead of "property management firm".
5. **`Input: {{input_field}}`** as the last line, the model reads
   top-to-bottom. Put the input at the end so the rules stay in working
   memory when it emits.

## Two-variable rule: visual contrast

If Variable 1 is a short noun phrase (2 to 4 words), Variable 2 should be
a list of items, a percentage, a currency figure, or a short verb phrase.
Two variables of the same shape make the email feel templated.

**Good pairing**
- Variable 1 = "property management firm" (2 to 4 words, noun phrase)
- Variable 2 = "back-office leasing, tenant calls and invoicing" (list)

**Bad pairing (both are noun phrases of the same shape)**
- Variable 1 = "property management firm"
- Variable 2 = "real estate operator"

**Bad pairing (too similar in meaning)**
- Variable 1 = "the retail operator"
- Variable 2 = "the retail group"

## Worked example 1: Connect Resources Variable 1

Task: generate a persona-fit company-type phrase that fits after the
words "one similar". Must work across ~4,500 UAE companies in mixed
industries.

```
Read the company's LinkedIn description and return ONE short phrase (2 to 4 words) that describes what type of company this is. The phrase fits after the words "one similar".
Rules:
- Pick ONLY from this approved list:
  property management firm, real estate group, retail operator, F&B group, hospitality group, construction firm, logistics operator, professional services firm, facilities management company, insurance broker, healthcare group, education group
- If no clean match: return "UAE mid-market group"
- No adjectives. Lowercase unless proper noun. No em-dashes.
Input: {{linkedin_description}}
Output: (the phrase only, nothing else)
```

Why this works:
- 12 approved phrases cover 85%+ of the target industry list.
- The fallback "UAE mid-market group" reads cleanly in the email
  ("one similar UAE mid-market group is saving...").
- The formatting rules (lowercase, no adjectives) prevent the model from
  drifting to "one similar exclusive hospitality group" or similar
  embellishments.

## Worked example 2: Connect Resources Variable 2

Task: generate 2 to 3 outsourceable function names that fit after the
word "usually in".

```
Read the company's LinkedIn description and return 2 or 3 function names that could be outsourced. The phrase fits after "usually in".
Rules:
- Pick ONLY from this approved list:
  admin, back-office operations, back-office leasing, tenant calls, customer service, data entry, collections, accounts receivable, dispatch coordination, reservations handling, scheduling support, invoicing support, documentation processing, HR operations support, payroll support, IT helpdesk, first-line support
- Return 2 or 3 items only, comma-separated, with "and" before the last one.
- If no clean match: return "admin, back-office operations and data entry"
- Lowercase. No em-dashes. No extra commentary.
Input: {{linkedin_description}}
Output: (the phrase only, nothing else)
```

Why this works:
- The approved list maps cleanly to the 6 target industries in CR
  (real estate, retail, F&B, logistics, hospitality, professional
  services).
- Forcing "2 or 3 items, comma-separated, with 'and' before the last one"
  makes the output grammatically correct inside the email.
- The fallback is grammatically identical to a real list so it never
  breaks the sentence.

## How to design the approved list for a new campaign

Follow this recipe.

1. **Look at the Company Table industry filter.** The approved list for
   Variable 1 should map 1 to 1 with the industries you are targeting.
   If the filter is "Real Estate, Retail, F&B, Construction,
   Hospitality", the Variable 1 list should have a noun phrase for each.
2. **Look at the Offer in `library_data`.** If the offer is
   "outsourcing", Variable 2 is departments. If the offer is "automate
   X", Variable 2 is manual processes. The offer dictates what kind of
   list Variable 2 is.
3. **Read 10 to 15 real LinkedIn descriptions** from a quick sample of
   the target list. Notice how the company describes itself. Your
   approved list should use those self-descriptions, not marketing
   clichés.
4. **Keep items short.** 2 to 4 words max. Long phrases read as stilted
   when pasted into a sentence.
5. **Test in the final sentence mentally.** Drop every approved phrase
   into the actual email sentence. If one of them reads weird, remove
   it from the list.

## Fallback design rule

The fallback must read fine in the final sentence. A safe test: the
fallback sentence should be grammatically correct even if every other
Variable in the email is a fallback.

**Bad fallback**
- Variable 1 fallback: "various types of companies" → "One similar
  various types of companies is saving..." (broken grammar)

**Good fallback**
- Variable 1 fallback: "UAE mid-market group" → "One similar UAE
  mid-market group is saving..." (clean)

## When to skip Variables entirely

- **Small curated lists (under 100 leads)**. Personalize manually via
  First Name + Company Name + a hand-written observation. AI Variables
  are overkill and add noise.
- **Very homogeneous audiences** where one noun phrase fits all. Just
  hard-code the phrase into the body.
- **Email 2 and Email 3** in sequences. Keep Variables in Email 1 where
  they do the most work. Follow-up emails read cleaner with fewer AI
  variables.

## Debugging a Variable that drifts

Symptom: you see hallucinations in the Clay preview.

Check, in order:
1. Did the prompt end with the input field and output format? If not,
   fix the order.
2. Is the approved list too long (more than 25 items)? The model starts
   matching loosely. Trim.
3. Is the approved list too narrow for the audience? Add 1 to 2 items
   that cover the edge cases you are seeing.
4. Is the input field `{{linkedin_description}}` empty for the leads
   that drift? That is the fallback's job. Check the fallback reads
   cleanly in-sentence.
5. Last resort: add an explicit rule `If the company is in [sector X],
   always return "[specific phrase]"`. Only do this if one sector
   consistently drifts.

## Variable naming in Clay vs. Instantly

- In Clay, you can name the AI column anything, `similar_company_phrase`,
  `outsourceable_departments`, `persona_consequence`. The descriptive
  name helps Jose keep his head straight when building.
- In Instantly, those columns import as `{{Variable 1}}` and
  `{{Variable 2}}` (the first and second AI variables on the lead
  record). The body spintax **must** use `{{Variable 1}}` and
  `{{Variable 2}}`, not the descriptive names, or Instantly will render
  them as literal text.

Always check: the order in which Clay exports the Variable columns into
Instantly determines which one is "1" and which is "2". If the mapping is
flipped, swap the references in the body.

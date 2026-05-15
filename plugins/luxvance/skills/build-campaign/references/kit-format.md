# Output Kit Format

This is the exact shape Jose expects when you hand him the production kit. Same shape gets pasted into Marko's Notion task. Zero divergence between the kit and the task body.

Keep the section order. Keep the code fences around pasteable blocks. Keep the prose blocks short and readable.

## Why the format is rigid

Three reasons:

1. Jose scans top to bottom in the same order every time. Speed matters.
2. The same body goes into the Notion task with no rearrangement.
3. Marko and Ana paste each block into a known destination tool: blocks 4-7 into Clay, blocks 8-9 into Instantly. A consistent shape saves ~60 seconds per campaign and keeps the team aligned.

## The 9 blocks, in order

```
1. Campaign name
2. Campaign brief             (≤60 words, one paragraph, prose)
3. Rendered email             (Subject + body, plain markdown)
4. Clay — Company filter      (Sculpture prompt, code fence)
5. Clay — People filter       (Sculpture prompt, code fence)
6. Clay — Variable 1 prompt   (code fence)
7. Clay — Variable 2 prompt   (code fence)
8. Instantly — Subject spintax (code fence)
9. Instantly — Body spintax    (code fence)
```

Close with a one-liner inviting Jose to tune. No postamble.

## What is intentionally omitted

These appeared in older versions and are now out of the kit:

- **Hypothesis** (Bet / Why / Evidence). Lives upstream in `campaign-intelligence`. The build skill receives a locked hypothesis as input, does not re-emit it.
- **Client request** sub-block. Same reason.
- **Who we send to** prose. The Sculpture filters in blocks 4 and 5 express this.
- **Ideal client avatar** with billionaire riff. Used internally to write better copy and pick realistic Variable sample values for the rendered email. Never appears in the output.
- **Template overlay name** ("Josh Whitfield Permission-Based", "Problem-Offer Matrix" etc). Internal scaffolding. Surfacing it adds zero value to a Luxvance operator and reads as academic jargon.
- **Sequence spacing** as a standalone block. Email labels carry the spacing. Default is Step 1 only.
- **"Why this angle"**, **"Heads-up flags"**, **"Next step" instructions**. Cut.
- **"From:" line** in the rendered email. Subject and body only.

## Section-by-section detail

### Block 1. Campaign name

A single inline-code line with the Luxvance naming convention.

```
## Campaign name

`Luxvance - [Region] - [Persona] - [Trigger] - W[ISO week]`
```

Example: `Luxvance - NAM - Sales Leaders 11-200 - New in Role - W18`

Use ASCII hyphens, not en-dashes. Match the convention of existing campaign names in Instantly.

### Block 2. Campaign brief

One paragraph. **60 words max.** Prose. No bullets. Names persona + region + trigger + the "why now" in plain language.

The brief is the only context the team gets in the kit. It should let Marko or Ana understand what they are building and why in one breath. If it takes more than 60 words, you do not understand the campaign well enough to ship.

Shape:

```
## Campaign brief

[One paragraph, ≤60 words.]
```

Example:

> NAM-based B2B mid-market companies whose Sales leader was promoted or hired in the last 90 days. Newly-in-role VPs and Directors of Sales feel the pipeline pressure on day one and have not yet picked a lead-gen partner. The "prospecting tax" math gives them a peer-voice opener that sidesteps the AI-built-it-internally objection.

### Block 3. Rendered email

Subject + body, plain markdown, **not in a code fence**. Reads like an email.

Use realistic sample values:
- `{{firstName}}` → the avatar's invented first name (Brendan, Olivia, etc).
- `{{companyName}}` → the avatar's invented company name.
- `{{title}}` → the avatar's title (VP of Sales, Head of Sales, etc).
- `{{Variable 1}}` → a value from the Variable 1 approved list that matches the avatar's industry.
- `{{Variable 2}}` → a value from the Variable 2 approved list that matches the avatar's industry.
- `{{accountSignature}}` → render as a typical signature: name, role, company line.

The avatar exists internally to make the render concrete. **Do not name the avatar in the kit.** Do not include a "billionaire riff" line, a job-title line, or any biographical context. The render is the only place the avatar surfaces.

Shape:

```
## Rendered email

**Subject:** [rendered subject]

> Hi [firstName],
>
> [rendered body with one variant picked for each RANDOM block]
>
> [signature]
>
> [PS]
>
> [opt-out]
```

If the campaign runs a multi-email sequence, add `### Email 2` and `### Email 3` sub-sections below Email 1 with their own renders. Email 2 and Email 3 subjects threaded:

> **Subject:** (threaded, leave blank in Instantly so it replies to the Email 1 thread)

Default is **Email 1 only**. Multi-email only when Jose explicitly asks.

### Block 4. Clay — Company filter (Sculpture)

A Sculpture prompt that returns `KEEP` or `REJECT: <reason>`. Code fence.

**Keep it lean.** 3 KEEP rules + 2 REJECT rules is the target ceiling. Filters must operate on data Clay reliably exposes (LinkedIn company description, country, employee count, industry, website text). Avoid filters that depend on slow or expensive enrichment fields.

Shape:

```
## Clay — Company filter

(Sculpture prompt, paste into Clay's Company Table Sculpture)

\`\`\`
ROLE
You are filtering companies for a Luxvance outbound campaign targeting [region]-based [segment]...

INPUT
{{linkedin_company_description}}, {{company_country}}, {{company_employee_count}}, {{company_industry}}, {{company_website_text}}

KEEP THE COMPANY IF ALL OF THESE ARE TRUE
1. ...
2. ...
3. ...

REJECT THE COMPANY IF ANY OF THESE ARE TRUE
1. ...
2. ...

OUTPUT
Return only one of:
- "KEEP"
- "REJECT: <one short reason>"
\`\`\`
```

### Block 5. Clay — People filter (Sculpture)

Same shape as block 4, for the People Table. Filters on title, country, and (if cheap to compute) seniority signals.

**Tenure filters** ("less than 3 months in role") should be applied at audience-build stage in Apollo or Sales Navigator before Sculpture runs, not in the Sculpture itself. Sculpture is fast yes/no on data already loaded.

### Block 6. Clay — Variable 1 prompt

Code fence. Single-prompt Claygent, no web search, reads only `{{linkedin_company_description}}`. Output 2-8 words. Approved list + safe fallback.

Shape:

```
## Clay — Variable 1 prompt

(Renders as `{{Variable 1}}` in the body.)

\`\`\`
ROLE
You are writing a 2-to-8 word descriptor of [what Variable 1 represents].

INPUT
{{linkedin_company_description}}

RULES
- Read the LinkedIn company description ONLY. Do not search the web.
- Output 2 to 8 words. Lowercase. No trailing punctuation. No em-dashes.
- Pick from this approved list when possible (preferred matches first):
  [comma-separated list of 15-30 safe phrases, all in the same shape]
- If no clean match, infer the closest 2-to-8 word phrase using the same shape.
- If you genuinely cannot tell, return: "[safe fallback]"

OUTPUT
The phrase only. No quotes. No explanation. No trailing period.
Input: {{linkedin_company_description}}
Output:
\`\`\`
```

### Block 7. Clay — Variable 2 prompt

Same shape as block 6, for `{{Variable 2}}`.

### Block 8. Instantly — Subject spintax

One line, single `{{RANDOM|...}}` block, 4-6 variants. Variants differ on hook angle (curiosity / number / person / trigger / risk), not word choice. Code fence.

Shape:

```
## Instantly — Subject spintax

\`\`\`
{{RANDOM|variant 1|variant 2|variant 3|variant 4|variant 5|variant 6}}
\`\`\`
```

### Block 9. Instantly — Body spintax

The full Email 1 body wrapped in a code fence. Spintax on every swappable phrase. Includes greeting, hook, position, lead magnet, CTA, signature placeholder, PS, and opt-out.

Shape:

```
## Instantly — Body spintax

\`\`\`
[full body spintax]
\`\`\`
```

If multi-email is requested, add `### Email 2 body` and `### Email 3 body` sub-sections, each in its own code fence.

For Email 3, add this note above the code fence: "Forbidden in Email 3: last chance, final, removing you, bumping, checking in."

## Multi-option delivery (Phase 4 Path B)

Before Jose picks an option, render three mini-versions. Each mini includes only:
- A short rationale (one line, plain English, no template overlay name)
- Rendered Email 1 (Subject + body, plain markdown)
- Email 1 body spintax (code fence)

Hold back blocks 1, 2, 4, 5, 6, 7, 8 until Jose picks.

Shape:

```
# [Campaign working title], three options

## Option A

**Why this:** [one line, plain English]

**Subject:** [rendered subject]

[rendered body]

**Email 1 body spintax**

\`\`\`
[full body spintax]
\`\`\`

## Option B
(same shape)

## Option C
(same shape)

## Your pick

Tell me A, B, C, or "blend A and C". I produce the full kit from there.
```

## Shape notes

- Always wrap Sculpture prompts, Variable prompts, and spintax in triple-backtick code fences. Curly braces and pipes break if not fenced.
- The rendered email (block 3) is **not** in a code fence. Plain markdown so it reads like an email.
- Email labels are plain: "Email 1", "Email 2", "Email 3". No "(day 0)", "(day +3)", "(day +6)" suffixes.
- Email 2 and Email 3 subjects are always "(threaded, leave blank in Instantly so it replies to the Email 1 thread)" in the rendered section. Their paste-ready bodies still appear, but no separate Subject spintax — Instantly threads automatically.
- Do not narrate, do not add postamble. A one-line invitation to tune is the right sign-off.

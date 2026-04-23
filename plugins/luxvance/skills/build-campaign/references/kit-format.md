# Output Kit Format

This is the exact shape Jose expects when you hand him the production kit.
Keep the section order. Keep the code fences around pasteable blocks. Keep
the prose blocks short and readable.

## The two halves

The kit is two halves.

The **top half** is the **context summary**: the campaign title, the
hypothesis, who we send to, the ideal client avatar, the campaign name,
and the rendered emails. This is what Jose reads first and shares with
the team. Prose and headings, no code fences in this half.

The **bottom half** is the **paste-ready assembly**: Instantly spintax
and Clay Sculpture prompts. This is what he literally copies into the
tools. Everything in this half is wrapped in triple-backtick code fences
so curly braces and pipes survive the copy.

Order is non-negotiable. The flow is designed so Jose can scan top to
bottom, understand the bet, see a realistic example, and then execute.

## Section checklist

The kit always has these sections, in this order. Do not add, do not
remove, do not reorder.

1. Campaign title (H1) with template overlay subtitle (bold)
2. Hypothesis (H2)
   - Client request (H3, sub-block)
3. Who we send to (H2)
   - Companies (H3, sub-block)
   - People (H3, sub-block)
4. Ideal client avatar (H2)
5. Campaign name (H2)
6. What [avatar firstName] sees (H2)
   - Email 1 (H3) — Subject + rendered body
   - Email 2 (H3) — Subject note + rendered body
   - Email 3 (H3) — Subject note + rendered body, if applicable
7. Paste-ready for Instantly (H2)
   - Subject line (H3) — code fence with spintax
   - Email 1 body (H3) — code fence with spintax
   - Email 2 body (H3) — code fence with spintax
   - Email 3 body (H3) — code fence with spintax, if applicable
8. Paste-ready for Clay (H2)
   - Company Table Sculpture prompt (H3) — code fence
   - People Table Sculpture prompt (H3) — code fence
   - Variable 1 prompt (H3) — code fence
   - Variable 2 prompt (H3) — code fence

Close with a one-liner inviting Jose to tune the shape or the copy. No
long postamble.

## What is intentionally omitted

These sections used to exist and are now deliberately out of the kit:

- **Sequence spacing** as a standalone block. The Email 1 / 2 / 3 labels
  carry the sequence. Day offsets live in the skill's Sequence Spacing
  Defaults section, not in the output. Do not label emails with
  "(day 0)", "(day +3)", etc.
- **Why this angle** rationale. The Hypothesis block carries the
  reasoning in a tighter, more honest form.
- **Heads-up flags**. If a flag matters, bake it into the Hypothesis or
  the Client Request text. Otherwise drop it.
- **Next step** or copy-paste instructions. Jose knows the flow.
- **"From:" line** in the rendered email. Subject and body only.

## Section-by-section detail

### 1. Campaign title and template overlay

Top of the output. H1 with the campaign's working title (short, readable,
not the Luxvance naming convention, that comes later in section 5).
Below it, a bold line with the template overlay.

Example:

```
# CR Emiratisation Hook, CEO UAE, Apr 2026
**Template: Josh Whitfield Permission-Based**
```

### 2. Hypothesis

Three sentences in a blockquote. Bet, Why, Evidence. Each labelled.

Shape:

```
## Hypothesis

> Bet: [one sentence, the bet we are placing].
> Why: [one sentence, the mechanism that makes the bet reasonable].
> Evidence: [one sentence, prior runs / library facts / market facts
> supporting the bet. If first-time test, say so honestly].
```

#### 2b. Client request (sub-block)

H3 under Hypothesis. One paragraph in a blockquote. Who asked, when,
why. Fireflies quote if you have one clean. If no Fireflies anchor,
name the origin honestly (for example "Jose's campaign-intelligence
brief dated [date]"). **Never invent a quote.**

### 3. Who we send to

Two sub-blocks.

**Companies** (H3): two to four sentences. Country, headcount band,
industries, exclusions. Prose, no bullets.

**People** (H3): two to three sentences. Job titles, seniority floor,
exclusions. Note de-dupe against related campaigns if relevant.

### 4. Ideal client avatar

A blockquote with the fictitious lead. Always a phonetic riff on a
famous billionaire. Always an invented job title at an invented company,
both industry-relevant. See "Billionaire avatar convention" below for
the canonical name list.

Shape:

```
## Ideal client avatar

> **[Funny billionaire riff], [job title] of [invented company]**
> [Location]. [headcount / venues / scale context].
> [One sentence on what they care about day to day].
> [One sentence on how they read email and how they decide].
```

### 5. Campaign name

A single code-inline line with the Luxvance naming convention.

```
## Campaign name

`[CLIENT] - [Angle] - [Persona] [Geo] - [Month Year]`
```

### 6. What [avatar firstName] sees

Rendered emails. Use the avatar's firstName and companyName literally.
For Variable 1 and Variable 2 slots, pick realistic sample values from
each approved list that match the avatar's industry (for a hospitality
avatar, "hospitality group" and "front-of-house hiring", not generic
placeholders).

No code fences in this section. Plain markdown so it reads like an
email.

Email labels are **"Email 1"**, **"Email 2"**, **"Email 3"** — plain, no
day-offset suffix. The skill's Sequence Spacing Defaults section
controls the actual day offsets in Instantly.

Email 2 and Email 3 subject lines are threaded (reply to Email 1's
thread). Mark them like this:

> **Subject:** (threaded, leave blank in Instantly so it replies to the Email 1 thread)

Shape:

```
## What [avatar firstName] sees

### Email 1

**Subject:** [rendered subject]

[rendered body with one variant picked for each RANDOM block]

### Email 2

**Subject:** (threaded, leave blank in Instantly so it replies to the Email 1 thread)

[rendered body]

### Email 3

**Subject:** (threaded, leave blank in Instantly)

[rendered body]
```

### 7. Paste-ready for Instantly

Everything in triple-backtick code fences. Subject is one line, a single
RANDOM block with 4 to 6 variants (Email 1 only; Email 2 and 3 thread,
no subject). Body spintax for each email is a full block with
`{{firstName}}`, `{{companyName}}`, `{{Variable 1}}`, `{{Variable 2}}`,
`{{accountSignature}}`, and RANDOM blocks everywhere swappable.

For Email 3, add this note above the code fence:
"Forbidden in Email 3: last chance, final, removing you, bumping,
checking in."

Email labels here are also plain: "Email 1 body", "Email 2 body",
"Email 3 body". No day suffix.

### 8. Paste-ready for Clay

Four code fences in this order: Company Table Sculpture prompt, People
Table Sculpture prompt, Variable 1 prompt (with approved list and
fallback), Variable 2 prompt (with approved list and fallback). Label
each Variable with "renders as {{Variable 1}}" / "renders as
{{Variable 2}}" as a note above the code fence.

## Billionaire avatar convention

The avatar name is always a phonetic riff on a famous billionaire. The
convention keeps the examples memorable, funny, and clearly fictional so
no reader confuses the avatar with a real prospect.

Canonical name list (pick the riff that best fits the industry of the
ideal target):

The naming pattern is: keep the real first name intact, tweak the
surname into something cute, pet-name, or punny. Examples:

- **Tim Cookie** (Tim Cook) → tech, hardware, consumer electronics
- **Elon Huskie** (Elon Musk) → tech, automotive, industrial
- **Bernard Arnie** (Bernard Arnault) → hospitality, luxury, retail
- **Jeff Bezie** (Jeff Bezos) → e-commerce, logistics, cloud
- **Warren Buffy** (Warren Buffett) → insurance, finance, holdings
- **Bill Gatesy** (Bill Gates) → software, enterprise, consulting
- **Howard Schultzy** (Howard Schultz) → F&B, hospitality, retail
- **Ray Krocky** (Ray Kroc) → F&B, franchise, retail
- **Richard Bransy** (Richard Branson) → hospitality, travel, airlines
- **Larry Pagey** (Larry Page) → tech, data, search
- **Sergey Brinnie** (Sergey Brin) → tech, search, research
- **Mukesh Ambi** (Mukesh Ambani) → telecom, energy, conglomerate
- **Carlos Slimmy** (Carlos Slim) → telecom, holdings, real estate
- **Gautam Adie** (Gautam Adani) → infrastructure, logistics, energy
- **Mark Zuckie** (Mark Zuckerberg) → social, advertising, tech

If no clean fit, default to **Elon Huskie** or **Tim Cookie** and
adjust the invented company name to match the target industry. Feel
free to invent fresh ones that follow the same pattern (real first
name + cute last name) if the industry needs a better-fitting riff.

Invented company name rule: short, two or three words, fictional,
industry-relevant, usually riffing on the avatar's cute surname.
Example patterns:
- "Arnie Hospitality Group"
- "Bezie Logistics"
- "Gatesy Partners"
- "Krocky F&B Holdings"
- "Buffy Property Holdings"

Job title rule: the target persona exactly. If the campaign targets
CEOs, the avatar is a CEO. If the campaign targets CFOs, the avatar is
a CFO. Do not drift the title for drama.

## Multi-option delivery (Phase 4 Path B)

Before Jose picks an option, render three mini-versions. Each mini
includes only: overlay name, one-line rationale, rendered Email 1
(Subject + body), and the Email 1 body spintax. Do not produce
Hypothesis, Client Request, Who We Send To, Avatar, Campaign Name, Clay
assets, or Email 2 / 3 until the pick is locked.

Shape:

```
# [Campaign Working Title], three options

## Option A: [Overlay name]

**Why this:** [one line]

**What [avatar firstName] sees**

**Subject:** [rendered subject]

[rendered body]

**Email 1 body spintax**

    [full body spintax in a code fence]

## Option B: [Overlay name]
(same shape)

## Option C: [Overlay name]
(same shape)

## Your pick

Tell me A, B, C, or "blend A and C". I produce the full kit from there.
```

## Shape notes

- Always put Instantly spintax and Clay prompts inside triple-backtick
  code fences. Instantly and Clay eat curly braces and pipes if they
  are not fenced.
- The rendered email (in "What [avatar firstName] sees") is **not** in a
  code fence. It is plain markdown so it reads like an email.
- Never output Paste-ready sections without code fences.
- Email labels are always plain: "Email 1", "Email 2", "Email 3". No
  "(day 0)", no "(day +3)", no "(day +6)".
- Email 2 and Email 3 subjects in the rendered section are always
  "(threaded, leave blank in Instantly so it replies to the Email 1
  thread)". Email 2 and Email 3 do not have their own subject line in
  the paste-ready section.
- Do not narrate or add "Next step" instructions at the bottom. A
  one-liner inviting Jose to tune is the right sign-off.

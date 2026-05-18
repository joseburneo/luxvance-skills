---
name: spam-word-checker
description: >
  Always-on spam and deliverability guardrail for every piece of cold-email copy Luxvance ships.
  Scans subject lines, openers, body, follow-ups, CTAs, opt-out lines, and company names against
  a banned-word/phrase list and a phishing-pattern list, then proposes safe replacements.
  Triggers on "check this for spam", "spam word check", "deliverability review", "QA this copy",
  "flag banned words", "check subject line", "is this safe to send", "scan for spam triggers".
  Spanish triggers: "revisa esto por spam", "limpia este copy", "qa de esta secuencia",
  "es seguro mandar esto". Also auto-triggers as a background rule whenever build-campaign or
  personalized-copywriting is active — every piece of outbound copy gets screened.
version: 0.1.0
---

# Spam Word Checker

Always-on guardrail. Every subject line, opener, body line, follow-up, CTA, opt-out, and company-name reference Luxvance produces gets scanned against the rules below. If the rule fires, the offending word is replaced or the line is rewritten before the copy ships.

This skill is small by design. Most other Luxvance copywriting skills invoke it automatically.

## When to use

- Inside `build-campaign` (auto-trigger on the rendered email + every spintax block)
- Inside `personalized-copywriting` (auto-trigger on every per-lead variable + situation/value/cta line)
- When Jose pastes copy and asks "is this safe to send"
- Before any `launch-instantly-campaign` upload (final QA gate)
- When a campaign's positive-reply-scoring report shows elevated `negative_hostile` or `unsubscribe` rate (run this on the copy retroactively)

## When NOT to use

- On non-cold-email content (internal docs, client invoices, contracts) — the banned-word list is calibrated for Gmail/Outlook spam filters, not general writing.
- On the spintax mechanics (`{{RANDOM|a|b|c}}`) — those are markers, not body content.

## Relationship with sibling skills

| Skill | Relationship |
|---|---|
| `build-campaign` | Auto-triggers this skill on block 3 (rendered email) + block 9 (body spintax) before output. |
| `personalized-copywriting` | Auto-triggers this skill on every batch of rendered emails during the QA loop. |
| `launch-instantly-campaign` | Re-runs this skill as a final gate on the `variants.yaml` body before creating the DRAFT. |
| `campaign-intelligence` | Reads scoring data this skill never touches. No interaction. |
| `cold-email-weekly-rhythm` | Wednesday positive-reply sweep references this when hostile/unsub rates spike. |

## Banned single words

Treat each as banned standalone OR inside a compound. Punctuation, hyphens, or splits do not make a banned token safe (`cash-cycle` still contains `cash`).

```
get, bank, credit, access, open, compare, problem, now, billing, deal,
finance, financial, claims, insurance, mortgage, soon, new, performance,
freedom, home, sales, medical, urgent, life, marketing, investment,
diagnostics, friend, cash, invoice, extra, purchase
```

Edge case: if a banned word is part of a real company name in the copy (e.g. `Access Brand Communications`, `Buckeye Insurance`, `Calcon Mutual Mortgage`), apply the company-name handling rule (below) instead of deleting the reference.

## Banned short phrases

```
off chance, one time, all good, following up here, last note from me here,
great fit, bumping this once, just following up once, circle back,
one more quick follow-up, keep this open, compare notes, compare notes live,
appreciate the reply
```

### Banned "follow up" boilerplate (Luxvance voice rule)

Every variant of "following up" is banned — it reads as templated and is the single most reliable tell that a sequence is automated. Banned across all clients, all steps:

```
just a short follow up on my last note
a quick follow up on my note from earlier
following up on my message from earlier this week
just following up
I'm following up on
following up to see if
wanted to follow up
quick follow up
short follow up
follow up on my note
follow up on my email
```

**Safe replacements** (natural reference-to-prior-email phrasing, especially as Step 2 openers):

- "Did you have the chance to see my email below?"
- "Did you get the opportunity to see my email below?"
- "Have you seen my email below?"
- "Have you had a moment to look at my note below?"

### Banned link-bridge phrases in Email 1 (Luxvance deliverability rule)

Email 1 of a sequence has zero links AND zero references to a link coming later. The following phrases (or anything semantically equivalent) trigger an automatic rewrite of Email 1:

```
I'll share the menu in a separate note
I'll follow up with the link
I'll send the link in a separate note
the link is coming
more details to come
I'll send more info in a moment
I'll share more in a follow-up
let me send you the link after this
```

The copy should read as if no link was ever part of the plan. If a link belongs in the campaign, it goes in Email 2+, and Email 1 must not reference its existence.

See [`docs/BUILD_A_CAMPAIGN.md`](../../docs/BUILD_A_CAMPAIGN.md#rule-2--zero-links-in-email-1-and-never-mention-ill-send-the-link) for the full rule.

## High-risk promotional / pressure wording

The full list lives in `references/banned-phrases.md`. Categories covered:

- Money / discount hype: `50% off`, `100% guaranteed`, `100% free`, `best deal`, `cash bonus`, `earn cash`, `extra income`, `risk-free`, `save big`, `pure profit`, etc.
- Time-pressure: `act now`, `limited time`, `expires today`, `hurry up`, `last chance`, `while supplies last`, `this won't last`, etc.
- CTAs that scream promo: `apply now`, `buy today`, `call now`, `click here`, `order today`, `get started now`, `sign up free`, etc.
- Hype adjectives: `amazing`, `fantastic`, `incredible`, `unbelievable`, `unbeatable`, `wonderful`.

## Phishing-style / security-warning language

Banned because these trip spam filters trained on phishing:

```
access your account, account update, activate now, change password,
click to verify, confirm your details, confidential information,
data breach, download now, final notice, important update,
immediate action required, install now, last warning, log in now,
new login detected, password reset, payment details needed,
phishing alert, security breach, security update, update account,
verify identity, warning message
```

## Irrelevant blacklisted categories (never appear in B2B cold copy)

```
adult content, betting/gambling, weight loss, miracle cure, prescription drugs,
medical breakthrough, "100% natural" claims, casino, lottery, jackpot, slots,
diet pill, fat burner, no prescription needed, secret formula, xxx
```

Full list in `references/banned-phrases.md`.

## Formatting and style bans

- No em-dashes (`—`). Use commas, periods, or colons. This is also enforced by Luxvance brand-guidelines.
- No ALL CAPS in body text.
- No multiple exclamation marks (`!!`, `!!!`).
- **Greeting rules (Luxvance voice):**
  - **Avoid "Hi" entirely** for UAE / medical / executive audiences. Banned at first contact for these contexts: `Hi {{firstName}}`, `Hi Dr.`, `Hi Doctor`, `Hi there`.
  - **Avoid "Hey" everywhere** (too casual for any Luxvance audience).
  - **For UAE / medical / executive:** use `Dear Dr. {{firstName}}`, `Hello Dr. {{firstName}}`, `Hello Doctor`, `Good day Dr. {{firstName}}`. Formal address matches the cultural register.
  - **For NAM / EMEA non-medical B2B:** `Hello {{firstName}}` is OK. Plain `{{firstName}},` (no prefix) is also OK.
  - **Never open with flattery** (no "I've been following your work", "huge fan", etc.).
- No third-person self-references like `[Company] offers...` / `[Company] helps...`. Cold email is first-person.
- No fake urgency, misleading subject lines, excessive links, or promotional formatting.

## Unsubscribe / closeout line rules

Never write a closeout line that promises to stop following up based on silence. Luxvance DOES follow up — that is the whole point of sequences. Silence-based promises misrepresent actual behavior and trip subscriber-trust filters.

**Banned (silence = we stop):**

- `I will take silence as a no`
- `read no reply as a pass`
- `assume no response means no interest`
- `If I don't hear back, I will leave it there / let this one go / leave you alone`
- `I am happy to stay out of the way` (when context implies silence triggers stop)
- Any construction where the user doing nothing = we stop sending.

**Allowed (explicit user action = we stop):**

- `A reply of 'no' / 'not for us' / 'pass' is enough and I'll step out of your inbox`
- `Just say the word and I'll stop`
- `A one-word reply works fine if you'd rather I stopped`
- `Feel free to ignore this` (permission, no promise)
- `Happy to try back later when timing makes more sense` (defers, doesn't stop)
- `If this isn't the right angle, tell me what is` (invites pivot)
- `If I misjudged the fit, I'd rather know than guess` (asks for clarification)

Rule of thumb: **the user has to do something explicit for the sequence to stop**. Silence keeps the cadence running.

## Safe replacement patterns

When a banned word fires, prefer a substitution from the table below. If nothing in the table fits, rewrite the line so the operational meaning is explicit (no fuzzy hype).

| Banned / Risky | Safe Replacement |
|---|---|
| `free consultation` | `open to a short conversation` |
| `special offer` | `what we are seeing in the market` |
| `act now` | `if relevant, happy to send details` |
| `guaranteed results` | `this may be relevant depending on your situation` |
| `click here` | `let me know and I can send it over` |
| `limited time` | `not sure if this is timely for you` |
| `increase revenue` | precise business outcome (e.g. `help support liquidity`) |
| `save money` | precise business outcome (e.g. `reduce processing cost per file`) |
| `get more customers` | `bring qualified meetings on calendar` |
| `unlock` | rewrite — Luxvance brand-guidelines bans this verb |
| `leverage` | rewrite — Luxvance brand-guidelines bans this verb |
| `synergy` | rewrite — Luxvance brand-guidelines bans this verb |

More replacements in `references/safe-replacements.md`.

## Company-name handling

If a banned word appears inside a real company name used in copy (`Access Brand Communications`, `Coming Soon New York`, `Buckeye Insurance`, `Calcon Mutual Mortgage`):

1. Do not drop the company reference entirely. The personalization signal is too valuable.
2. Rewrite the displayed company name so the banned token is removed from standalone form.
3. Priority: remove the token if the remaining name still reads clearly. Only abbreviate or compress when needed.

Examples:

- `Access Brand Communications` → `AB Communications`
- `Calcon Mutual Mortgage` → `Calcon Mutual`
- `Buckeye Insurance` → `Buckeye`
- `Coming Soon New York` → `Coming NY`
- `Mortgage Builder Software` → `MB Software`

## Rewriting logic

- Rewrite hype into plain, observational language.
- Replace pressure with permission.
- Replace promotional wording with specific business language.
- If a line sounds like an ad, coupon, scam, or phishing message, rewrite it.
- If a "bump" sounds filler-heavy or vague, replace with a direct next-step question or clear closeout line.
- If a value line uses fuzzy words (`tight`, `fit`, `access`, `problem`), rewrite so the operational meaning is explicit.
- If a reply acknowledgement sounds low-status, remove it and go straight to the next useful question.
- If a sentence sounds AI-polished, simplify until it reads like a person speaking plainly.

## How to run the scan

When invoked, scan the input text in this order:

1. **Banned single words** — substring match (case-insensitive) including inside compounds. Flag every hit with line number.
2. **Banned short phrases** — exact substring match. Flag every hit.
3. **High-risk promotional / phishing / irrelevant** — exact substring match. Flag every hit.
4. **Formatting violations** — em-dashes, ALL CAPS runs, multiple exclamation marks, greeting prefix before first name.
5. **Unsubscribe / closeout rule** — pattern-match for "silence = we stop" constructions.
6. **Company-name banned tokens** — detect company names that contain banned tokens. Propose rewrite.

For each flag, return:

```
LINE [N] — [original text]
  FLAG: [category] — "[token or phrase]"
  FIX: [proposed rewrite]
```

If zero flags fire, return: `Spam check: clean. Safe to ship.`

## Final QA checklist

Before approving any copy:

- [ ] Scan subject line for spam-trigger wording
- [ ] Scan body for banned or high-risk wording
- [ ] Rewrite any hype-heavy or pressure-heavy line into plain language
- [ ] Remove fake urgency
- [ ] Confirm email sounds like a credible real person, not a promotion
- [ ] Confirm unsubscribe line is action-conditional (not silence-conditional)
- [ ] Confirm no em-dashes, no ALL CAPS body, no greeting prefix before first name

## Auto-trigger behavior

When this skill is invoked as a background guardrail from another skill (build-campaign or personalized-copywriting), it should:

1. Not narrate intermediate steps.
2. Only surface output if a flag fires.
3. If the calling skill rendered a sample email, scan the rendered version (not the spintax wrapper, since spintax markers themselves are not part of the message a recipient sees).
4. If the calling skill produced multiple variants (A/B/C), scan each independently.

## Language

Default to the language of Jose's most recent message for the report. The banned-word lists themselves are English (Luxvance leads are English-speaking). When Jose is writing Spanish-language copy for a Spanish-language client (rare today), the equivalent Spanish banned-word list lives in `references/banned-phrases-es.md` (to be built when first Spanish campaign launches).

## Learned patterns

<!-- self-improvement entries get appended here when Jose adopts a new banned word or pattern on the fly -->

When the list grows past ~10 entries, promote the durable ones into the main body of this SKILL.md.

## References

- `references/banned-phrases.md` — full lists (high-risk, phishing, irrelevant categories)
- `references/safe-replacements.md` — extended substitution table

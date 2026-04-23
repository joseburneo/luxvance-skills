# Template Library

Five overlays, plus the Custom path. Every overlay is a **structural and
psychological recipe**, not a pre-written email. You render a fresh email
every time based on the client's Library data and the angle Jose chose.

## How to pick an overlay

Do not toss a coin. Use this simple decision tree.

1. **Does Jose have an email or draft in his head?**
   → Custom (most of the time).

2. **Is the audience C-level, Founder, or MD at a large company?**
   → **Josh Whitfield Permission-Based**. The permission-to-reject PS is
   the unlock for saturated inboxes.

3. **Is the market under a real, dated event in the last 30 days (new
   regulation, cost relief, regulatory deadline, tariff, ruling)?**
   → **Tension-Led**. Use the event as the opening hook. Dies in quiet
   markets, so skip it if there is no real event.

4. **Is the offer a cost / efficiency / displacement play with a clear
   quantified delta (AED 300K saved, 20% cost cut, 2-week turnaround)?**
   → **Problem-Offer Matrix**. Connect Resources Apr 2026 is the canonical
   example (see `connect-resources.md`).

5. **Is the persona problem-aware but solution-unaware? Does the offer need
   a diagnostic moment before the pitch can land?**
   → **NEPQ**. Opens with a question, not a pitch.

6. **Is the audience a busy operator, a second-touch campaign, or an
   audience with low tolerance for long emails?**
   → **Instantly 5-Line**. Five lines, one idea each.

If two overlays tie, pick the one you have more reference material for in
the chat. Do not mix overlays inside a single email or inside a single
3-step sequence. Mixing is what makes copy feel inconsistent.

---

## Overlay 1: Josh Whitfield Permission-Based

**Core psychology**
Saturated senior inboxes. The trick is to make rejection free and explicit.
The PS in Email 1 reads: "a quick reply of [leave me alone | not interested
| not cool | whatever] and I promise not to send another email for life."
This inverts the pressure. They can close the loop in one word. Paradox:
giving permission to reject dramatically raises reply rate.

**Email 1 shape**
- Opening line: dense fact about their world, not about you.
- Body: 4 to 7 lines that pack the Offer, the Outcome, the Proof (one
  named Credibility Asset with a number), and the CTA.
- CTA: one low-friction ask (reply with one word, one scan, one signal).
- Signature line: `Enterprise Partners: X | Y | Z | W` as passive social
  proof. The named partners go on the signature line, not inside the email
  body, so the body stays focused.
- PS: explicit permission-to-reject, spintaxed.

**Email 2 shape (day +3)**
- Context drop, not a bump. Offer a new angle or a new piece of proof.
- Never say "bumping" or "following up".
- Keep it tight. 4 to 6 lines.

**Email 3 shape (day +6)**
- Gratitude breakup. Zero urgency. Zero implied threat.
- Forbidden words: `last chance`, `final`, `removing you`, `bumping`,
  `checking in`.
- Shape: "Thanks for considering. I am stepping back. If [future trigger]
  happens, the door is open. Best, [name]"

**When Josh Whitfield wins**
- C-suite at 200 to 5,000 headcount firms.
- Mature industries where everyone is getting 50 cold emails a week.
- Buyers who are emotionally allergic to pressure tactics.

**When Josh Whitfield loses**
- Operators or individual contributors, the permission framing reads as
  overly polite.
- Offers without at least one hard Credibility Asset with a number. The
  dense Email 1 needs proof to survive.

**PS spintax library**
```
P.S. {{RANDOM|A quick reply of "not interested" and I close the loop for life.|If this is not the right moment, one word back and I step away.|Reply "no" and I promise not to send another email, ever.}}
```

**Signature social-proof line**
```
Enterprise Partners: {{client_partner_1}} | {{client_partner_2}} | {{client_partner_3}} | {{client_partner_4}}
```

---

## Overlay 2: Instantly 5-Line Pattern

**Core psychology**
Busy people reply to emails they can read in six seconds. Strip the email
to five lines. One idea per line. No throat-clearing. No preambles.

**Shape**
```
Line 1: {{RANDOM|Hi|Hello}} {{firstName}},
Line 2: [fact about their world or a hard observation, one sentence]
Line 3: [one-sentence offer with a specific number or specific delta]
Line 4: [micro-CTA, one word or one question]
Line 5: {{RANDOM|Best|Thanks|Cheers}}, {{accountSignature}}
```

Optional P.S. with social proof, spintaxed. No more than one P.S.

**When it wins**
- Second-touch campaigns after a long Email 1 did not land.
- C-suite at smaller firms (under 100 people) where the buyer wears many
  hats and does not have time for dense emails.
- Operators who prefer Slack over email.

**When it loses**
- Offers that need context to feel credible. Five lines is too few to
  establish trust for a new category or a new proof story.

**Variables in 5-Line**
Usually only one Variable fits cleanly. Use `{{Variable 1}}` for the
persona-fit noun phrase on Line 2. Skip `{{Variable 2}}` unless you can
fit it into Line 3 without padding.

---

## Overlay 3: NEPQ

**Core psychology**
Borrowed from Jeremy Miner's NEPQ framework: problem-aware buyers resist
pitches but engage with precise diagnostic questions. The email leads with
a question that reframes their current state, then lets them fill in the
gap.

**Shape**
```
Line 1: {{RANDOM|Hi|Hello}} {{firstName}},
Line 2-3: [observation about a pattern in their segment, neutral tone]
Line 4 (the question): [a question that exposes the gap between their
current state and a better state]
Line 5-6: [short framing, "we work with [client type] on [outcome]"]
Line 7: [micro-CTA, reply with one word, one signal, or one context]
Line 8: {{RANDOM|Best|Thanks}}, {{accountSignature}}
```

**The question rule**
The question must be uncomfortable but not hostile. Example:
"How are you currently handling [specific problem] in [specific context]?"
vs. the wrong version "Are you having problems with [problem]?"
The first asks about the mechanism, the second asks for a yes/no. Always
ask about the mechanism.

**When it wins**
- Problem-aware / solution-unaware personas. They feel the pain but have
  not shopped for a fix.
- Consultative offers where the right next step is a conversation, not a
  demo.

**When it loses**
- Offers with hard quantified deltas ("save AED 300K"), those want
  Problem-Offer Matrix, not NEPQ. NEPQ softens the number.

**Variables in NEPQ**
`{{Variable 1}}` = the specific problem name (persona-fit).
`{{Variable 2}}` = the specific context or department where the problem
shows up.

---

## Overlay 4: Problem-Offer Matrix

**Core psychology**
Hard pain statement + specific outcome with a number + concrete
displacement offer. No soft edges, no hedging. The email is a piece of
technical sales mail dressed up as a note.

**Shape**
```
Line 1: {{RANDOM|Hi|Hello|Dear}} {{firstName}},
Para 1 (pain + market fact): 2 to 3 sentences anchoring the pain in a
  concrete number or a concrete regulatory fact. Must include one persona-
  fit Variable (the department, the function, the asset class).
Para 2 (offer + proof): 2 to 3 sentences describing the offer with a
  quantified outcome ("AED 300 to 400K a year") and the mechanism ("from
  Jordan or South Africa under our UAE sponsorship"). Include one
  Credibility Asset by name.
Para 3 (CTA): 1 to 2 sentences. Micro-CTA. "Reply with one [thing] and I
  send [specific asset]."
Closing: {{RANDOM|Best|Thanks|Regards|All the best|Cheers}},
{{accountSignature}}
P.S. (social proof): one line naming 3 recognizable logos from
  Credibility Assets.
P.P.S. (opt-out): one line giving them a clean exit, spintaxed.
```

**When it wins**
- Cost pressure, efficiency, displacement plays. Connect Resources is the
  canonical example.
- UAE, Saudi, and GCC markets where specificity and numbers beat charm.
- Senior Finance and Operations buyers.

**When it loses**
- Soft, brand-led, category-building offers. Matrix is too sharp for
  those.
- Very small audiences (under 500 leads) where personalization beats
  structure.

**Variables in Problem-Offer Matrix**
`{{Variable 1}}` = similar company phrase (for the proof point, "one
similar [company type] is saving...").
`{{Variable 2}}` = outsourceable / cuttable / optimizable department
phrase (2 to 3 items, comma-separated with "and").

**Canonical example: Connect Resources Apr 2026**
See `connect-resources.md` for the full kit. Use it as the tonal and
structural benchmark for new Problem-Offer Matrix campaigns.

---

## Overlay 5: Tension-Led

**Core psychology**
The market just shook. A new regulation dropped. A tariff changed. A
competitor raised. You open the email with the tension itself and thread
the offer as the resolution. The tension is the hook. No tension, no
overlay.

**Shape**
```
Line 1: {{RANDOM|Hi|Hello}} {{firstName}},
Para 1 (the tension, dated): "On [date], [event happened]. Most [persona]
  in [geo] are now [second-order effect]."
Para 2 (the implication for them): "For a company like {{companyName}}
  that means [specific implication tied to persona / industry]."
Para 3 (the resolution): "We help [persona] [specific outcome] by
  [mechanism]. [Credibility Asset]."
CTA: 1 line. "Reply and I send [asset] within 24 hours."
Closing + sig.
P.S. social proof. P.P.S. opt-out.
```

**When it wins**
- A real, dated, verifiable macro event in the last 30 days. Not a rumor,
  not a think-piece, not a trend.
- Industries where senior buyers track regulation closely (finance,
  healthcare, compliance, telecom, energy).

**When it loses**
- Quiet markets. There is no tension to lead with, so the email reads as
  manufactured drama.
- Personas who are insulated from macro events (individual contributors,
  hyper-tactical operators).

**How to source the tension**
Use the Phase 1 macro-context pull. If nothing credible, fall back to
Problem-Offer Matrix. Never invent a tension.

**Variables in Tension-Led**
`{{Variable 1}}` = persona-fit consequence of the tension ("frozen hires",
"tightened margins", "blocked renewals").
`{{Variable 2}}` = the mechanism description or the specific segment hint
the leads can associate with.

---

## The Custom path

Jose gives you an email, a draft, or a two-sentence idea. Your job is to
**preserve his intent** and **apply the Luxvance production structure**.

**Steps**

1. Parse his input. Identify: the pain / observation, the offer, the
   proof, the CTA. Note which is missing.
2. Pick the **closest matching overlay** silently (usually Problem-Offer
   Matrix or Instantly 5-Line). You do not announce the overlay unless
   Jose asks, he gave you his own direction.
3. Rewrite into the structure, filling missing pieces from `library_data`
   and from conversation context. Example: if the draft has no proof,
   pull the best-fitting Credibility Asset from the Library.
4. Apply voice guardrails. No em-dashes. CEFR B1-B2. Mirror length.
5. Spintax everything swappable.
6. Add Variables 1 and 2 (unless the draft is for a small curated list
   and Jose opted out).
7. Add subject line spintax (4 to 6 variants, hook-different).
8. Add PS social proof and P.P.S. opt-out if they fit.
9. Output the full kit in `kit-format.md`.

**Golden rule for Custom**: never swap Jose's hook for a "better" hook. If
he wrote "cost scan" do not turn it into "cost audit". If he wrote "from
Jordan" do not turn it into "from anywhere". He chose those words on
purpose.

**Flag but do not change** if the draft has:
- A buzzword the brand bans ("synergies", "leverage", "empower",
  "revolutionary").
- An em-dash.
- A claim that is not supported by any Credibility Asset in `library_data`.

Call these out at the end in a short "heads up" block after the kit. Jose
decides.

---

## What happens after Jose picks

If Path B (templates), Jose replies with "A", "B", "C", or "blend A and
C". You produce the full kit for that pick.

If Path A (custom), you already produced the kit in one shot.

Either way, the kit format is the same (see `kit-format.md`).

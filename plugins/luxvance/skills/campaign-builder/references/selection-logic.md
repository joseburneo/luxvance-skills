# Campaign Builder — Selection Logic Reference

Detailed gating, scoring, and selection logic used by the `campaign-builder` skill when picking Angle / Structure / Tone / Hook for each hypothesis.

---

## STEP 1 — UNIT OF SELECTION

The builder operates on a Campaign Unit:
**Offer × Segment × Persona × Use Case**

Everything else layers on top. Never mix offers inside one hypothesis. Hypothesis A and B can share the same Offer but must differ in Angle, Hook, or ideally both.

---

## STEP 2 — GATING RULES (Hard Eliminations)

Before scoring, eliminate bad fits. These are binary filters.

### A. Proof Gate
If no Credibility Assets match the selected Segment AND Persona:
- Downrank Social Proof angle heavily.
- Downrank Competitive framing if no comparative advantage is documented.

### B. Sophistication Gate
Sophistication level of the Segment:
- **Unaware** → disallow Problem Offer · downrank Social Proof.
- **Problem-Aware** → most angles allowed · avoid heavy competitive framing.
- **Solution-Aware** → allow Problem Offer, The Gift, Poke the Bear.
- **Vendor-Comparing** → up-rank Social Proof · up-rank Competitive angles.

### C. Persona Seniority Gate
- **C-suite** → up-rank The Minimal · downrank bullet-heavy structures.
- **Manager / Director** → downrank The Minimal · allow Full Structure and Three Ideas.
- **Mixed seniority** → default to The Question or Full Structure.

### D. Entry Offer Gate
If the Offer has no Entry Offer defined:
- Downrank The Gift angle.
- Prefer Problem Offer or Poke the Bear.

### E. Positioning Constraint Gate (Brand Guardrails)
If the client's Brand Guardrails prohibit:
- Guarantees → remove any hook relying on "guaranteed outcome".
- Direct competitor mentions → remove Competitive angles.
- Free audits → remove The Gift variants that offer unpaid deliverables.

---

## STEP 3 — FIT SCORING MODEL (0–5 per dimension)

For each viable Angle, score across 5 dimensions:

### 1. Offer Clarity (0–5)
How specific and measurable are the Problem → Outcome pairs in the Library?
- 5 = "Reduce localization turnaround from 6 weeks to 48 hours"
- 1 = "Save time"

### 2. Proof Strength (0–5)
How many Credibility Assets match both the Segment AND the Persona, and how strong are their key metrics?

### 3. Urgency Strength (0–5)
From the Use Case's "Why Urgent" field. Hard deadlines, cost escalation, and competitor movement score high. Ambiguous urgency scores 0–1.

### 4. Sophistication Match (0–5)
Does the Angle align with the Segment's sophistication level? (See gating B.)

### 5. Persona Alignment (0–5)
Does the Structure fit the Persona's seniority and communication style?

**Total possible: 25.**
Rank angles by total. Top angle = Hypothesis A. Second-ranked (or an intentional contrast) = Hypothesis B.

---

## STEP 4 — STRUCTURE SELECTION LOGIC

Based on Angle + Persona:

| Angle | Default Structure |
|---|---|
| The Minimal | One-Liner |
| The Gift | Full Structure or Three Ideas |
| Social Proof | Three Ideas |
| Poke the Bear | Full Structure or The Question |
| Problem Offer | Full Structure |

Structure is suggested, not fixed. Override if the Persona's communication style demands it.

---

## STEP 5 — TONE SELECTION LOGIC

Based on Persona + Sophistication:

| Combination | Tone |
|---|---|
| C-suite + Vendor-comparing | Assertive |
| Mid-level + Problem-aware | Conversational |
| Risk-averse Segment | Humble |

Tone is a secondary layer. If unsure, default to Conversational for most B2B cold outreach.

---

## STEP 6 — HOOK SELECTION

Selection logic based on the Use Case's urgency driver:

| Urgency Signal | Hook |
|---|---|
| Deadline | Compliance |
| Cost escalation | Cost |
| Competitor movement | Status |
| Revenue leakage | Opportunity |
| Slow processes | Speed |
| Exposure / risk | Risk |

If the Use Case has no clear urgency driver, the Selector must flag it — weak urgency produces weak campaigns. Either strengthen the Use Case in the Library or pick a different Campaign Unit.

---

## STEP 7 — LEARNING MODE

When a recent `campaign-intelligence` brief is available, weight its findings HIGHER than theory.

### Adjustments:

- **Reply rate high, positive rate low** → problem-clarity issue → adjust Angle toward more specific pain.
- **Reply rate low overall** → Hook mismatch or deliverability. Check Hook against Use Case urgency first.
- **Positive rate strong** → scale the same Angle, test a new Hook in hypothesis B.
- **Repeated objections in past campaigns** → adjust Persona or Segment selection.
- **"Ideal Campaign Profile" in campaign-intelligence** → use its geography + title + company size to override Library defaults if there's conflict.

**The campaign-intelligence brief is the strongest signal in the room. Don't override it without an explicit reason.**

---

## A / B DIFFERENTIATION RULES

Hypotheses A and B must differ on at least ONE of:

- Different Angle (preferred)
- Different Hook psychology
- Different Structure + Tone combination

Cosmetic differences (same angle, different subject line) are not A/B tests — they're variant tests. Save those for Ana Maria's optimization phase, not for hypothesis generation.

---

## OUTPUT STRUCTURE

Each hypothesis always includes:

- Campaign Unit (Offer × Segment × Persona × Use Case)
- Strategic picks (Angle / Structure / Tone / Hook)
- Fit score (X/25 with per-dimension breakdown)
- Gates passed (list)
- Why this should work (3 bullets)

Then the **Delta** section compares A vs B and states the primary contrast + why it's a real test.

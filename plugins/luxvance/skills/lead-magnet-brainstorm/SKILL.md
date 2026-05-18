---
name: lead-magnet-brainstorm
description: >
  Helps Jose find a free lead magnet to offer in cold emails when the standard
  Luxvance "book a discovery call" feels weak or the client's reply rate is low
  due to a generic ask. Scores 10 archetypes against the client's offer, picks
  top 2-3, and writes them to the client profile so build-campaign can use them.
  Triggers on "what should I give away for [client]", "lead magnet ideas",
  "qué puedo regalar en este email", "hook ideas for [client]", "free offer
  brainstorm", "needs a hook", "ideas de lead magnet para [cliente]".
version: 0.1.0
---

# Lead Magnet Brainstorm

Cold emails with a concrete free offer outperform "book a call" asks by 3-10x. This skill helps Jose pick an offer the client can actually deliver.

A good lead magnet is:

1. **Cheap to deliver at scale** (ideally automated)
2. **Genuinely valuable to the prospect** (they would pay for it, or it saves them obvious time/money)
3. **Demonstrates the client's competence** (so buying becomes the natural next step)

## When to use

- During `campaign-intelligence` when the locked hypothesis needs a CTA stronger than "book a discovery call"
- When the client's reply rate is below 1% and the diagnosis is "weak ask" (not deliverability)
- When onboarding a new Luxvance client and the offer is fuzzy
- Before running `build-campaign` if no lead magnet is defined yet

## When NOT to use

- The client already has a proven lead magnet that converts (e.g. CapQuest's PE/equity assessment) — don't rebuild
- The client's product/service has a free trial that effectively IS the magnet (skip, use the trial)
- For internal Luxvance outbound (Jose's own agency lead gen) — Jose's offer is already locked (`discovery call`)

## Relationship with sibling skills

| Skill | Relationship |
|---|---|
| `campaign-intelligence` | The analyst locks the hypothesis and CTA direction. If the CTA needs strengthening, this skill runs as a sub-step. |
| `build-campaign` | Reads the chosen lead magnet from the client profile when writing the rendered email. |
| `make-a-task` (Notion) | Sometimes the magnet requires a Marko/Ana workflow (e.g. running an audit template). The chosen magnet becomes a Notion task. |

## Inputs

- Client name (resolves to `profiles/<client-slug>/`)
- Optional: Jose's notes on what the client can/cannot give away
- Optional: client's current CTA + reason it's weak

## Outputs

Two files:

1. `profiles/<client-slug>/lead-magnets.md` — full brainstorm with scores per archetype + top 2-3 picks
2. Update `profiles/<client-slug>/client-profile.yaml` with `offer.lead_magnet` field populated

## Flow

### Phase 1: 4 intake questions

Ask one at a time. Do not batch.

1. **What does the client sell, in one sentence?** Pre-fill from `library_data` in Supabase if available.
2. **What is the #1 problem their best customer had BEFORE buying?** (This is the north star. The magnet should ease this problem.)
3. **What could the client do for a prospect in under 30 minutes that they would pay $100 for?** Push back on "nothing" — there is always something. SEO agency → audit a page. Copywriter → rewrite a subject line. Recruiter → review one job spec. Consultant → review one process.
4. **Any legal / regulatory restrictions on what they can promise or give?** (Financial advice, medical claims, securities — know before proposing.)

### Phase 2: Score the 10 archetypes

For each archetype, score 1-5 on four criteria:

| Criterion | What it measures |
|---|---|
| Cheap to deliver | 1 = expensive, 5 = automated. AI-rendered counts as automated. |
| Genuinely valuable | 1 = no, 5 = they would pay $100+ |
| Demonstrates competence | 1 = no signal, 5 = strong signal |
| Unique vs competitors | 1 = everyone does it, 5 = only this client could |

Total ≥15/20 = worth proposing. Below 15 = skip or rework.

#### The 10 archetypes

| # | Name | What it is | Delivery | Best for |
|---|---|---|---|---|
| A | Free audit / diagnostic | "Free 5-min audit of your [thing]" | Manual or AI quick check; 1-page report back | Agencies, consultants, dev shops |
| B | Data / research piece | "Report on [their industry] — [metric or trend]" | Create once, reuse infinitely | High-volume campaigns, B2B SaaS |
| C | Competitive intel | "What your top 3 competitors are doing that you're not" | AI-powered LinkedIn / web scrape | Mid-market sales, marketing, recruiting |
| D | Template / checklist | "The exact [template/checklist/playbook] we use for [outcome]" | Google Doc, Notion, or PDF link | Agencies, consultants, ops |
| E | Intro / connection | "I can intro you to [specific person]" | Warm intro from network | High-ACV sales, recruiting. **Do not fake this.** |
| F | Quick-win work | "I'll do [small scoped piece of work] free as a sample" | 30-60 min of real work | Service businesses, agencies |
| G | Specific-to-them analysis | "I noticed [specific thing about their company] — here's what I think" | 2-3 sentences of real observation, no deliverable | High-ACV sales where thoughtful observation IS the magnet |
| H | Free tool / account | "Free account on [your product] with [specific scope removed]" | Actual product access | SaaS companies with self-serve onboarding |
| I | 15-min working session | "15-min screen share where I [specific thing] for you" | 15 min of real time | High-ACV, later-stage buyers |
| J | Benchmark / comparison | "How your [metric] compares to [peer group]" | Pre-built benchmark data | Industries with public/scrapable metrics (SEO, hiring, web traffic) |

Per-archetype scoring template:

```
Archetype A — Free audit / diagnostic
  Cheap to deliver:       X/5  [rationale]
  Genuinely valuable:     X/5  [rationale]
  Demonstrates competence: X/5  [rationale]
  Unique vs competitors:  X/5  [rationale]
  Total:                  X/20
```

### Phase 3: Output 5-10 concrete ideas

For each archetype that scored 15+, write:

```
**[Magnet name]**
What it is: <one sentence>
What the client needs to deliver it: <tools, data, time>
Example CTA for the cold email:
  "Reply Y and I'll send you [the thing]. Takes you 30 seconds, no call needed."
Rubric score: X/20
Why it might work for [client]: <one line>
Why it might not: <one line — the risk>
```

### Phase 4: Recommend the top 2-3

Pick based on:

- **Delivery friction** — favor low-friction (automated, pre-built, AI-rendered)
- **Match to their ICP's actual pain** — answer to intake question 2 anchors this
- **Novelty** — if every competitor does free audits, pick something else

Surface the top 2-3 with one-line reasoning each. Ask Jose to lock one.

### Phase 5: Save

Save the full brainstorm to `profiles/<client-slug>/lead-magnets.md`.

Update `profiles/<client-slug>/client-profile.yaml`:

```yaml
offer:
  lead_magnet: <chosen archetype name>
  lead_magnet_details: <one sentence on what gets delivered>
  lead_magnet_cta_example: <example reply-hook CTA>
  alternates:
    - <second pick — one line>
    - <third pick — one line>
```

The alternates list survives so future campaigns for this client can rotate the magnet without re-brainstorming.

## Common mistakes (worth flagging during the brainstorm)

- **Proposing magnets the client cannot actually deliver.** Always confirm delivery capacity. "Free audit" from someone who has never done one = disaster.
- **Asking for a meeting as the magnet.** A meeting is an ASK, not a magnet. The magnet is what gets given BEFORE the meeting.
- **Magnets that require too much from the prospect.** "Fill out this 20-field intake form" = dead. Maximum ask: reply with 1-2 data points.
- **Gated PDFs behind forms.** For cold email, NEVER gate the magnet. Send it inline or as a direct link.
- **"Free consultation."** Generic and uninspiring. Replace with something specific — "15 min where I [specific action] for you".
- **Single-magnet thinking.** Different leads respond to different magnets. The `alternates` list in the profile lets future campaigns rotate.

## Luxvance-specific archetype suggestions (per existing clients)

Pre-loaded suggestions based on what each client sells. The skill should surface these as starting hypotheses, not as final picks.

| Client | Most likely archetype | Specific magnet idea |
|---|---|---|
| CapQuest | C (competitive intel) or J (benchmark) | "How your industry's PE/VC equity grants compare to peers" |
| Connect Resources | A (free audit) | "Free 5-min compliance audit on your UAE labor setup" |
| Kcal | F (quick-win work) | "I'll send you a sample week of corporate meal plan for your size" |
| GFV | B (data piece) | "What top food brands paid per kg last quarter" |
| Remly | A (free audit) | "Free property-listing audit for [property]" |
| Luxvance (own) | G (specific-to-them analysis) | "I'll send you 3 cold email subject line ideas tailored to your ICP" |
| CAMB.AI | H (free tool) | "We will spin you up an account with [scoped feature] free for 14 days" |

Treat these as priors. Re-evaluate via the 4 intake questions each time.

## Important rules

- **One sentence definitions only.** A magnet that needs 3 paragraphs to explain is too complicated to be a hook.
- **Confirm delivery feasibility.** Never propose a magnet without confirming the client can deliver it within 24h of a reply.
- **Save alternates.** The future campaign for the same client should rotate, not repeat.
- **Skip flattery.** "We help amazing companies like yours" is not a magnet, it's filler.

## Language

Default to the language of Jose's most recent message. Magnet name examples in the table stay in English (cold-email convention).

## Learned patterns

<!-- self-improvement entries get appended here when Jose adopts a new archetype or scoring rule on the fly -->

When the list grows past ~10 entries, promote the durable ones into the main body of this SKILL.md.

## Related files

- `campaign-intelligence/SKILL.md` — produces the hypothesis this skill strengthens
- `build-campaign/SKILL.md` — reads the chosen magnet
- `references/archetype-examples.md` — extended worked examples per archetype (to be built as Jose locks magnets)

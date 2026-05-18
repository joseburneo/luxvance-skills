---
name: experiment-design
description: >
  Framework for running single-variable cold-email experiments at Luxvance.
  Forces every test to isolate ONE variable (list, copy, offer, subject, opener,
  CTA, cadence, sequence length) so the learning is interpretable. Defines the
  three experiment types (list-only / copy-only / combined), the sample-size
  table by baseline and expected lift, the 1% rule baseline check, and the
  success-criteria template. Output: an experiment YAML saved per campaign.
  Triggers on "plan an experiment", "design an A/B", "set up the test for
  [client]", "compare X vs Y", "what should we test next", "disena un
  experimento", "planifica el A/B", "que probamos despues".
version: 0.1.0
---

# Experiment Design

If Luxvance changes the list, the copy, and the offer at the same time, we learn nothing. This skill forces one variable per experiment so the learning is interpretable.

## Why this exists

Most cold-email operators run "throw-everything" experiments. Campaign 1 gets a new list, new copy, new offer. It performs better. Victory declared. But nobody can tell whether the list, the copy, or the offer drove the lift.

Then campaign 2 changes all three again. Regression. Nobody knows why.

This skill is the antidote: every experiment has a one-sentence hypothesis, isolates one variable, sets success criteria before launch, measures at day 21, and weights the learning by confidence.

The 2026-05-17 session set up a Clay-built campaign vs Claude-Code-built campaign in Instantly with no formal framework. That test gets documented retroactively as Luxvance's first formal experiment.

## When to use

- Before any new campaign that is intended to test a hypothesis (not just ship copy)
- When `campaign-intelligence` produces a new hypothesis that needs validation
- When `cold-email-weekly-rhythm` Friday retrospective shows a campaign in the "middling" zone (near baseline)
- When Jose has an idea ("what if we used Heads of Revenue instead of VP Sales?") and wants to test it

## When NOT to use

- Luxvance has never shipped a campaign for this client → ship the baseline first, then experiment
- Sample size will be under 500 per arm → too noisy
- Multiple variables MUST change at once (rebrand, new product launch) → label it `combined` and treat as hypothesis-generation, not conclusion

## Relationship with sibling skills

| Skill | Relationship |
|---|---|
| `campaign-intelligence` | Produces the hypothesis this skill turns into an experiment plan. |
| `build-campaign` | Builds the copy for each arm. The variant gets the test treatment, the control gets the baseline. |
| `launch-instantly-campaign` | Creates the two campaigns (control + variant) as DRAFTs. |
| `positive-reply-scoring` | Measures the outcome at day 21. |
| `cold-email-weekly-rhythm` | Friday retrospective and quarterly review both reference experiment results from here. |
| `list-quality-scorecard` | Both arms' lists must score B or above; otherwise the experiment is invalid. |

## The three experiment types

### A. List-only experiment

- **What varies:** the list (targeting criteria — title, industry, geography, size, trigger)
- **What stays fixed:** copy, offer, sending infrastructure, sequence timing
- **What you learn:** whether this segment fits Luxvance's offer better than the baseline
- **Confidence on learnings:** HIGH on targeting, LOW on copy

### B. Copy-only experiment

- **What varies:** the copy (subject, body, sequence, A/B/C variants)
- **What stays fixed:** list, offer, sending infrastructure
- **What you learn:** whether this copy resonates with this audience
- **Confidence on learnings:** HIGH on copy, LOW on targeting

### C. Combined experiment (use sparingly)

- **What varies:** list AND copy (and sometimes offer)
- **What stays fixed:** only infrastructure
- **When to use:** launching a whole new campaign for a new ICP — nothing is comparable
- **Confidence on learnings:** MEDIUM on everything. Use as hypothesis-generation, not conclusion. If a combined experiment wins, the next step is a list-only or copy-only follow-up to isolate which piece drove the lift.

## Flow

### Step 1: Name the hypothesis (one sentence)

Every experiment opens with a one-sentence hypothesis Jose can defend in writing:

> "Targeting Heads of Revenue at 50-200 person UK B2B SaaS will produce a higher positive_reply_rate than our current VP Sales baseline, because Heads of Revenue own the metric the lead magnet improves."

Or:

> "Leading the subject with a competitor reference (`'how Vodafone does X'`) will produce a higher positive_reply_rate than our current benefit-focused subject, because UK SaaS buyers respond to social proof from named peers."

If the hypothesis cannot be written in one sentence, the experiment is not ready. Push back to `campaign-intelligence` to refine.

### Step 2: Identify the single variable

Write the variable explicitly with the constants:

```
Variable: Target seniority
Change: "VP Sales" → "Head of Revenue"

Constants:
- Industry filter: B2B SaaS (unchanged)
- Headcount: 50-200 (unchanged)
- Geography: UK (unchanged)
- Copy: unchanged (same 1-step sequence, same V1/V2 prompts)
- Offer: unchanged (same lead magnet)
- Sending infrastructure: same 20 domains, 40 inboxes (split evenly)
- Send schedule: unchanged (M-F 8-17 UK timezone, throttle 10 min, max 30/day/inbox)
```

If ANY constant is actually changing, stop. Either lock it down or reclassify as a `combined` experiment with appropriate confidence weighting.

### Step 3: Baseline sanity check — the 1% rule

Before designing any experiment, confirm the baseline campaign is healthy: **positive_reply_rate or overall reply rate ≥1% after 200+ sends**. If the baseline is below 1% after 200 sends, the problem is not the experiment — it is the underlying infrastructure or copy.

Running an experiment on a broken baseline is wasted volume: both arms will be bad and Luxvance learns nothing about the variable being tested.

If the 1% rule fails, run `deliverability-audit` first. Fix the infrastructure or copy. Then come back and run the experiment.

### Step 4: Calculate minimum sample size

Sample size scales with the size of the effect being tested. Rough rules for cold email:

| Current baseline | Expected lift | Minimum sends per arm |
|---|---|---|
| 1% positive | 2x (1% → 2%) | ~500 |
| 1% positive | 1.5x (1% → 1.5%) | ~2,000 |
| 1% positive | 1.2x (1% → 1.2%) | ~10,000 |
| 2% positive | 2x (2% → 4%) | ~250 |
| 2% positive | 1.5x (2% → 3%) | ~1,000 |

Rule of thumb: **if the test has fewer than 500 sends per arm, you cannot tell signal from noise.**

Luxvance default for most experiments: 2,000 sends per arm.

### Step 5: Define success criteria up front

Write the criteria BEFORE launching. This prevents post-hoc rationalization.

```
Success      = variant positive_reply_rate ≥ <X>% (baseline is <Y>%)
Failure      = variant positive_reply_rate ≤ <Z>%
Inconclusive = between Z and X
Required sample: at least <N> sends per arm
Measurement date: day 21 after both campaigns are launched
```

Use the sample-size table to pick N. Set X at a meaningful lift over baseline (typically +50% or more — anything smaller will be noisy at this sample size).

### Step 6: Launch both arms simultaneously

Same day, same infrastructure split, same schedule. If the control sends Monday and the variant sends Thursday, day-of-week effects bias the test.

Use `launch-instantly-campaign` to create both DRAFTs at the same time. Jose attaches inboxes evenly (e.g. 20 inboxes total, 10 to each campaign). Both DRAFTs launched at the same time on the same day.

### Step 7: Measure at day 21

Wait until the full sequence has finished for ALL leads + the reply grace period. Measuring earlier biases the comparison toward the first email's reply rate.

Use `positive-reply-scoring` on each arm with the same cutoff date.

Primary metric: positive_reply_rate.
Secondary metrics (report but don't optimize for):

- Overall reply rate (sanity check)
- Bounce rate (sanity check — if one arm bounces 2x more, the LIST is bad in that arm, not the variable being tested)
- Unsubscribe rate
- Hostile rate

### Step 8: Weight the learning by confidence

```
Experiment: <name>
Type: list-only | copy-only | combined
Variable: <what changed>

Result: <winner name> at <X>% vs <baseline>%
Confidence: HIGH | MEDIUM | LOW

Learnings (by confidence):
  HIGH confidence:
    - <thing you can trust>
  MEDIUM confidence:
    - <thing that looks good but needs replication>
  LOW confidence:
    - <thing you are speculating about>
```

HIGH only if:
- Experiment type isolated the variable (list-only OR copy-only), AND
- Sample size met the minimum from the table.

### Step 9: Decide what to do with the result

- **Winner with ≥20% lift, HIGH confidence:** adopt as new baseline. Document in the experiment log. Move to next experiment.
- **Winner with 10-20% lift, HIGH confidence:** run a replication experiment with fresh leads. If it wins again, adopt.
- **Winner with <10% lift:** inconclusive. Run bigger next time or move on.
- **Loser:** document WHY you think it lost. The loss is also a learning — feed it back into `campaign-intelligence` as a negative result.
- **Combined experiment winner:** do NOT adopt as a new baseline. Split into single-variable follow-ups to figure out which piece actually drove the lift.

## What NOT to experiment on (at first)

If Luxvance is just launching a brand-new client, don't run experiments yet. Ship the baseline campaign, let it run 21 days, get the baseline number, THEN start experimenting.

Priority order of experiments (once a baseline exists):

1. **List** — biggest impact. Bad list kills any copy.
2. **Offer / lead magnet** — second biggest. "Book a call" vs a real magnet.
3. **Subject line** — cheap to test, drives open rate.
4. **Opener / first line** — after subject, the biggest lever.
5. **CTA** — how the email ends.
6. **Sequence cadence** — day 3 vs day 2 follow-up.
7. **Sequence length** — 1-step vs 2-step vs 3-step.

Do not jump to step 6 when step 1 is broken.

## Output: experiment plan file

At the end of planning, write to:

```
profiles/<client-slug>/experiments/YYYY-MM-DD-<name>.yaml
```

Schema:

```yaml
experiment:
  name: <short name>
  hypothesis: <one sentence>
  type: list-only | copy-only | combined
  variable: <what changes>
  constants: <list of what stays fixed>

success_criteria:
  positive_reply_rate_target: <float>
  baseline: <float>
  minimum_sends_per_arm: <int>
  measurement_date: <YYYY-MM-DD>

arms:
  control:
    instantly_campaign_id: <set at launch>
    description: <what is in the control>
  variant:
    instantly_campaign_id: <set at launch>
    description: <what is in the variant>

results:
  control_positive_reply_rate: null
  variant_positive_reply_rate: null
  winner: null
  confidence: null
  decision: null
```

After day 21, `positive-reply-scoring` populates the `results:` section, and `cold-email-weekly-rhythm` Friday retrospective references it.

## The 2026-05-17 retroactive case

Document the Clay-vs-Claude-Code campaign as the first formal Luxvance experiment:

```yaml
experiment:
  name: clay-vs-claude-code-uk-sales-leaders
  hypothesis: |
    A Claude-Code-built campaign (2,566 leads, locally personalized) will produce
    a positive_reply_rate at least as good as the Clay-built campaign (1,491 leads,
    Clay AI personalized), because the local Sonnet personalization preserves the
    same V1+V2 framework while Luxvance owns the cost structure.
  type: combined
  variable: list size and personalization engine simultaneously
  constants:
    - Copy template (same 1-step, same Subject + body)
    - Schedule (same M-F 8-17 UK, throttle, max/day)
    - Sending infrastructure (Luxvance UK inboxes)
    - Sequence: 1 step
  confidence: MEDIUM (because TWO variables change: list size + personalization source)

success_criteria:
  positive_reply_rate_target: not yet baselined for this segment
  baseline: TBD (Clay-built campaign serves as baseline)
  minimum_sends_per_arm: 1,491 (control) / 2,566 (variant) — fixed by what was sent
  measurement_date: 2026-06-07 (21 days after both went live)

arms:
  control:
    instantly_campaign_id: 9be79365-b273-41c0-8192-ba3f6189f7de
    description: Clay-built, 1,491 leads
  variant:
    instantly_campaign_id: 9987af18-4275-4d9b-b5b2-d3deed227899
    description: Claude-Code-built, 2,566 leads

results:
  control_positive_reply_rate: null
  variant_positive_reply_rate: null
  winner: null
  confidence: null
  decision: null
```

Save this to `profiles/luxvance/experiments/2026-05-17-clay-vs-claude-code-uk-sales-leaders.yaml` so the Friday retrospective on 2026-06-07 references it.

## Common mistakes

- **A/B testing inside one campaign.** Instantly's A/B variant feature mixes the data — fine for small copy tweaks, terrible for hypothesis testing. Use TWO campaigns for real isolation.
- **"I will test 3 things at once."** You learn nothing.
- **Calling it early.** Wait 21 days minimum. Cold-email replies trickle in over weeks.
- **Changing infrastructure mid-test.** If one arm uses new domains and one uses old, deliverability skews everything.
- **Ignoring bounce rate.** If variant bounce rate is 2x control, the LIST is bad — not the copy. Disqualify the test.
- **Picking a winner with <500 sends per arm.** Pure noise.

## Important rules

- One sentence hypothesis. If you can't write it, the experiment isn't ready.
- One variable. If multiple change, classify as `combined` and weight confidence DOWN.
- 1% rule baseline check. No broken-baseline experiments.
- Sample size from the table. No eyeballing.
- Success criteria before launch. No post-hoc rationalization.
- Day-21 measurement. No early calls.
- Same cutoff date for both arms.
- Confidence-weighted learnings. No false certainty.

## What to do next

**Plan locked.** Hand the experiment YAML to `build-campaign` to produce copy for each arm (control may already exist — only build the variant). Then `launch-instantly-campaign` for both as DRAFTs.

**Day 21:** `positive-reply-scoring` on each arm. Update the `results:` block. Decide per the Step 9 logic.

**Friday after measurement:** the Friday task in `cold-email-weekly-rhythm` references this experiment. Quarterly review aggregates all experiments.

## Language

Default to the language of Jose's most recent message for prose. The YAML schema fields stay in English.

## Learned patterns

<!-- self-improvement entries get appended here when Jose adopts a new variable category, threshold, or experiment type on the fly -->

When the list grows past ~10 entries, promote the durable ones into the main body of this SKILL.md.

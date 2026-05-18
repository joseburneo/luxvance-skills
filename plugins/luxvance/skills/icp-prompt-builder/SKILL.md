---
name: icp-prompt-builder
description: >
  Interactive loop that builds and tunes an AI prompt for evaluating whether a
  company or person fits a Luxvance client's ICP. Runs after any list-building
  skill (lead-sourcing Apollo, competitor-engagers, google-maps-list-builder)
  to qualify rows before paying for downstream enrichment + sending. Iterates
  batches of 10 with Jose's feedback, stops when 2 consecutive rounds have
  zero corrections, saves the final prompt for reuse. Uses Claude Code Task
  subagents — no external API key. Triggers on "qualify this list", "build an
  ICP filter for [client]", "tune the ICP prompt", "filter the engager list",
  "califica esta lista", "filtra los leads de [cliente]".
version: 0.1.0
---

# ICP Prompt Builder

Before Luxvance pays to verify 5,000 emails, tune a qualification prompt on 10-50 of them. This skill walks through the iterative loop.

## Why this exists

The list-builder skills (`lead-sourcing` Apollo, `competitor-engagers`, `google-maps-list-builder`, future `disco-like`, future `blitz-list-builder`) return ROWS, but they don't know whether those rows match the client's ICP. If a list-builder returns 5,000 companies and 60% are wrong fits, Luxvance wastes money:

- Verification: ~$1.60 per 1,000 rows (deliverability waterfall)
- Personalization: free in Sonnet quota, but burns it
- Instantly send: per-workspace subscription, not per-lead, but bad sends hurt reputation

The fix: build an AI qualification prompt BEFORE scaling. Pull 10 rows, have the prompt score them, compare to Jose's judgment, refine, repeat. Once the prompt agrees with Jose 2 rounds in a row with zero corrections, lock it in and apply at scale.

## When to use

- After `lead-sourcing` (especially `competitor-engagers` and `google-maps-list-builder`, where noise is 30-50%)
- After `disco-like` or `blitz-list-builder` when those providers exist
- When `enrich-and-verify-leads` is about to run on a freshly-sourced list
- When `list-quality-scorecard` reports a low ICP-fit dimension score and Jose wants to filter

## When NOT to use

- Less than 100 rows total — just eyeball them
- The list is already proven (used in 2+ prior campaigns with good positive_reply_rate) — reuse the prior tuned prompt
- Pure title-first Apollo searches with tight `seniorityIncludes` + `personTitleIncludes` — Apollo's filters already do this work

## Relationship with sibling skills

| Skill | Relationship |
|---|---|
| `lead-sourcing` | Source of the rows this skill qualifies |
| `competitor-engagers`, `google-maps-list-builder` | Required next step after their output (their READMEs say "always run icp-prompt-builder") |
| `enrich-and-verify-leads` | Runs AFTER qualification; only qualified rows pay for verification |
| `list-quality-scorecard` | Dimension 7 (ICP fit) can use the tuned prompt as a scorer |
| `personalized-copywriting` | The tuned prompt is reusable; same client = same ICP rules apply on the next campaign |

## Always uses Task subagents (no API key)

This skill runs entirely inside Claude Code via the `Agent` tool. No Anthropic SDK calls, no OpenAI calls — Claude Code does the scoring itself.

- **No extra API spend.** Uses Jose's Claude Code plan.
- **No key management.** Works out of the box.
- **Parallel scoring.** For 20-100 evaluations, 2-3 Task subagents batch 10-20 rows each.

At very large scale (5,000+ rows per batch), the TUNED prompt can be exported and run through the Anthropic API directly for speed. But TUNING always happens inside Claude Code with Jose in the loop.

## The loop (8 steps)

### Step 1 — Gather ICP context

Pull from `profiles/<client-slug>/client-profile.yaml` if it exists. If not, ask Jose:

- Client name / domain
- Who IS a good customer? What makes them a good fit? (named examples preferred)
- Who is NOT a good customer? What disqualifies them?
- Any specific signals? (B2B only, revenue range, tech stack, hiring status, recent fundraise, etc.)
- Any HARD disqualifiers? (competitor domains, existing customer domains, certain industries/geographies)

Save answers to the profile if it didn't exist.

### Step 2 — Select 10 test rows

Pull 10 rows from the list-builder output:

- Mix likely-good and likely-bad fits (do not auto-pick the first 10 — that biases the tuning)
- Variety in industry, size, location
- Each row needs at minimum: `domain` / `company_name` / `industry` / `headcount` / `description` (companies) OR `name` / `job_title` / `company` / `linkedin_url` (people)
- Richer fields make scoring better

### Step 3 — Build the initial qualification prompt

Template (varies for companies vs people):

```
You are an ICP evaluator for <CLIENT_NAME>.

## Target ICP
<ICP description from profile or Jose's input>

## Qualification criteria (MUST be true)
- <criterion 1>
- <criterion 2>
- ...

## Disqualification criteria (ANY match = disqualify)
- <disqualifier 1>
- <disqualifier 2>
- ...

## Input
You will receive a row with these fields:
- <list the fields available>

## Output
For each row, return JSON:
{
  "qualified": true | false,
  "confidence": 0.0-1.0,
  "reason": "one-sentence explanation"
}
```

### Step 4 — Run the prompt on the 10 rows

Via the `Agent` tool (`subagent_type: general-purpose`). One subagent that reads the prompt + 10 rows, returns 10 JSON scores. Write the result to `/tmp/icp-batch-N.json`.

### Step 5 — Present results to Jose

Format as a table:

```
Row                       | Qualified | Conf | Reason
--------------------------|-----------|------|----------------------------------------
acme-corp.com             | YES       | 0.92 | B2B SaaS, 200 employees, target industry
random-nonprofit.org      | NO        | 0.95 | Nonprofit, not a business customer
edge-case-company.com     | YES       | 0.55 | Could fit but revenue model unclear
...
```

Surface the per-row confidence so Jose can focus on edge cases first.

### Step 6 — Collect feedback

Ask specifically:

- Which evaluations are wrong? ("acme-corp should be NO because they're a competitor")
- Which are right but for the wrong reason?
- Any patterns the prompt missed?
- Any new disqualifiers to add?

If Jose gives zero corrections, log this round as "approved".

### Step 7 — Refine the prompt (or move on)

If Jose gave corrections:

- Add/remove qualification criteria
- Tighten/loosen disqualifiers
- Add specific examples of edge cases ("companies like X are NOT a fit because Y")
- Adjust confidence thresholds if everything is coming back at 0.5

Show the UPDATED full prompt back to Jose. Then go back to Step 4 with a NEW batch of 10 rows.

### Step 8 — Stop condition + save

The loop ends when **2 consecutive rounds have zero corrections from Jose**. When that happens:

1. Save the final tuned prompt to `profiles/<client-slug>/icp-prompt.txt`.
2. Append metadata to `client-profile.yaml`:

```yaml
icp_qualification_prompt:
  path: profiles/<client-slug>/icp-prompt.txt
  tuned_at: <YYYY-MM-DD>
  rounds_to_convergence: <N>
  final_batch_size: 10
  type: company | person
```

3. Print a one-liner for next steps:

```
Prompt locked. To apply to the full N-row list, run:
  /icp-prompt-builder --apply --prompt-file=profiles/<slug>/icp-prompt.txt \
    --input=path/to/list.csv --out=qualified.csv
```

(The `--apply` flag launches 3-5 parallel subagents that score the full list in batches.)

## Approval-loop rules (important)

- **Never auto-approve.** Even if the prompt looks right, require Jose to explicitly say "approved" or give zero corrections for 2 consecutive rounds.
- **Reset counter on any correction.** One correction resets the streak to 0.
- **Do not skip the batches.** Running 30 rows all at once feels faster but masks errors. 10 at a time is the right batch size — small enough to eyeball.
- **Show the full prompt each round.** After each refinement, display the current full prompt back to Jose so they see what changed.
- **Always use Task subagents** for the scoring inside each round. Never call external APIs.

## Using the tuned prompt at scale

Once saved, the prompt is applied to the full list via `--apply` mode. Options:

**Option A (free, slow):** 3-5 parallel Task subagents in batches of 50-100 rows per agent. Good for under 5,000 total.

**Option B (paid, fast):** export prompt + rows to the Anthropic API with parallelism. Good for 5,000-50,000. Costs ~$0.0002 per row at Sonnet rates.

Default is Option A to keep everything inside Claude Code.

## Per-Luxvance-client seed prompts

For each existing client, the skill should auto-populate the initial qualification prompt from `library_data` in Supabase if available, then iterate from there. Saves Jose from typing ICP context for clients already in the database.

| Client | library_data field | Likely prompt focus |
|---|---|---|
| CapQuest | Personas, Use Cases | "Mid-market companies with PE/VC equity allocation decisions" |
| Connect Resources | Personas, Segments | "UAE/GCC businesses needing labor compliance + payroll setup" |
| Kcal | Segments, Use Cases | "Dubai businesses serving meals to 20+ people daily" |
| GFV | Personas | "Food procurement / supply leads at mid-market food service" |
| Remly | Personas, Segments | "Property managers or real estate owners listing units in Dubai" |
| Luxvance (own) | Personas | "B2B service businesses doing $100k+ ARR needing outbound" |

These are STARTING hypotheses, not final prompts. The loop refines them.

## Recommended flow

1. Run a list-building skill (`lead-sourcing`, `competitor-engagers`, `google-maps-list-builder`)
2. Pull a sample of 50-100 rows
3. Run THIS skill → tune qualification prompt (3-5 rounds typical)
4. Apply tuned prompt to the full list → keep only `qualified: true` with `confidence >= 0.6`
5. Pass qualified subset to `enrich-and-verify-leads`
6. Then `list-quality-scorecard` → `personalized-copywriting` → `launch-instantly-campaign`

## Data points the prompt can use

From most list-builder outputs:

- `domain`, `company_name`, `industry`, `headcount`, `description`, `linkedin_url`

Additional fields (if enrichment has run):

- Business Type (B2B / B2C / B2B2C)
- Annual Revenue range
- Scale Scope (Enterprise / Mid-Market / SMB)
- Sub-industry (more specific than primary industry)
- Tech stack
- Recent signals (funding, hiring, news)

From `competitor-engagers` specifically:

- `engaged_with_competitor`, `engagement_type`, `total_engagements` — these are warmth signals; tune the prompt to score them in

From `google-maps-list-builder` specifically:

- `rating`, `review_count`, `recent_review_snippet`, `hours` — these encode quality + service-level signals

Tell the AI about the fields available in the prompt preamble.

## Common mistakes

- **Building the prompt too tight on round 1.** Start broad, narrow with feedback. Tight initial prompt = many false negatives on round 2.
- **Not including negative examples.** "Companies like Netflix are NOT a fit because they're B2C" is more powerful than generic "must be B2B".
- **Using only "qualified: true/false" without confidence.** Always ask for confidence — 0.5-0.7 borderline cases are where you learn the most.
- **Scoring 50 at once "to save time".** Defeats the point of the loop.
- **Not saving the prompt.** The point of tuning is reuse. If you don't save, you re-tune next time.

## Tier Classifier overlap (Luxvance Campaign Factory)

`code/agency-os/08_Campaign_Factory/tier_classifier.py` (351 lines) exists as backend Python and may overlap with this skill. Before deploying this skill in production, audit `tier_classifier.py` for:

- Does it classify per-company or per-person?
- What categories does it produce (Enterprise / Mid-Market / SMB? Custom buckets?)
- Is it deterministic (rules) or LLM-based?
- Does it write to Supabase?

If `tier_classifier.py` already implements something close, this skill should call it instead of duplicating. Mark as a follow-up task before the next big campaign launch.

## Important rules

- **Task subagents only.** Never call OpenAI or Anthropic API directly for scoring.
- **10 rows per batch.** Larger batches mask errors.
- **2 consecutive zero-correction rounds = stop.** Not "2 rounds total".
- **Save the prompt.** The reuse on the next campaign is the whole point.
- **Surface confidence per row.** Edge cases (0.5-0.7) are the most useful for tuning.

## Language

Default to the language of Jose's most recent message for prompts and review tables. The qualification prompt itself stays in English (the LLM scoring is more reliable in English, and the data fields are usually in English).

## Learned patterns

<!-- self-improvement entries get appended here when Jose adopts a new ICP heuristic on the fly -->

When the list grows past ~10 entries, promote the durable ones into the main body of this SKILL.md.

## Related files

- `competitor-engagers/SKILL.md` — its output requires this skill
- `google-maps-list-builder/SKILL.md` — its output requires this skill
- `lead-sourcing/SKILL.md` — its output benefits from this skill on edge cases
- `enrich-and-verify-leads/SKILL.md` — runs AFTER this skill filters the list
- `code/agency-os/08_Campaign_Factory/tier_classifier.py` — possible overlap; audit before scaling

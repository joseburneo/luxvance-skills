---
name: list-quality-scorecard
description: >
  Pre-upload quality grader for a Luxvance leads CSV. Scores the list across 8 dimensions
  (email verification coverage, dup emails, dup domains, title relevance, bad-title detection,
  catch-all density, ICP fit, name quality) and produces a letter grade A+ to F with action
  items. Run between enrich-and-verify-leads and personalized-copywriting (or between
  personalized-copywriting and launch-instantly-campaign) as the final pre-send sanity gate.
  Triggers on "grade this list", "score the list", "is this list ready to send",
  "list quality check", "scorecard". Spanish: "califica esta lista", "revisa la calidad
  de la lista", "esta lista esta lista para enviar".
version: 0.1.0
---

# List Quality Scorecard

A list of 5,000 leads is not the same as a good list of 5,000 leads. This skill grades the list across 8 dimensions BEFORE the campaign uploads, catching the failure modes Luxvance has paid for in the past: unverified emails that bounce, lists that drift from ICP, catch-all density that kills sender reputation.

## When to use

- After `enrich-and-verify-leads` (the verifier produces a deliverable subset; this skill grades that subset for shape, not just deliverability)
- After `personalized-copywriting` if the QA pass dropped a meaningful chunk (>5%)
- Before any `launch-instantly-campaign` upload (final sanity gate)
- When a campaign's bounce rate spikes (run retroactively on the original list to see if shape was the cause)

## When NOT to use

- Lists under 100 rows — sample too small for reliable stats.
- Static lists that have already been scored once and are being reused in the next 30 days.

## Relationship with sibling skills

| Skill | Relationship |
|---|---|
| `enrich-and-verify-leads` | Produces the input. The scorecard checks the verified subset, not the raw scrape. |
| `personalized-copywriting` | Optional input. If personalization has already run, the scorecard can also check the enriched CSV. |
| `launch-instantly-campaign` | Consumes the scorecard's grade as a precondition. C-grade or below blocks the upload. |
| `deliverability-incident-response` | If a campaign's bounce rate spikes, run this retroactively to confirm or rule out list shape as the cause. |
| `cold-email-weekly-rhythm` | Friday retrospective references the scorecard grade per campaign. |

## Inputs

A CSV with at least these columns:

- `email` (required)
- `first_name`, `last_name` (required)
- `job_title` OR `title` (required for dimensions 4 and 5)
- `company` OR `company_name` (required for dimension 3)
- `company_domain` (optional — derived from email if missing)
- `industry` (optional — used for dimension 7)
- `company_employee_count` (optional — used for dimension 7)
- `email_status`, `email_verified_at`, `email_verified_by` (optional — used for dimension 1)

Optional second input: the locked hypothesis or `library_data` ICP from `campaign-intelligence` / `build-campaign`. Without it, dimension 7 (ICP fit) is skipped and the overall grade is weighted on the remaining 7 dimensions.

## The 8 dimensions

### 1. Email verification coverage (CRITICAL — weighted 2x)

- **What:** percent of emails with `email_status = 'deliverable'` AND `email_verified_at` within the last 60 days.
- **Rule:** 100% required. Cold sending on an unverified or stale-verified list burns inbox reputation.
- **Score:** 100 if all verified within 60 days. 50 if 80-99%. 0 if below 80%.

### 2. Duplicate email rate

- **What:** percent of duplicate emails in the list (same address appearing more than once).
- **Rule:** under 1% acceptable, above 5% is a problem (suggests bad merge or scrape).
- **Score:** 100 at 0%, drops linearly to 0 at 10%.

### 3. Duplicate domain rate

- **What:** max number of leads from any single domain. Also reports avg leads-per-domain.
- **Rule:** 1-2 leads per domain ideal. 5+ suggests the list is over-indexing one company (often Apollo's behavior with very-large-company seeds).
- **Score:** 100 if avg under 2 per domain. 60 if avg 2-5. 30 if avg above 5.

### 4. Title relevance

- **What:** percent of `job_title` values that match the ICP's job-title list (exact OR documented synonym).
- **Rule:** if the campaign targets "VP Sales" but 40% of the list is "Sales Manager", you have drift.
- **Score:** 100 if 80%+ match. 50 if 40-80%. 0 if below 40%.
- **Skip if:** the ICP hypothesis has no specific titles.

### 5. Bad-title detection

- **What:** percent of titles matching known-bad patterns.
- **Bad patterns:** `intern`, `assistant`, `coordinator`, `student`, `part-time`, `retired`, `freelance`, `self-employed`, non-English titles when the campaign targets UK/US.
- **Rule:** under 2% is normal. Above 10% means the source filter is too loose (typically `roleMatchMode: "any"` was used in Apollo, see `lead-sourcing` rules).
- **Score:** 100 if under 2%. Drops sharply: 50 at 5%, 0 at 10%.

### 6. Catch-all domain density

- **What:** percent of emails on catch-all addresses (`info@`, `contact@`, `hello@`, `team@`, `office@`, `admin@`, `support@`, `sales@`, `marketing@`).
- **Rule:** under 5% acceptable for B2B outbound. Catch-all addresses respond at half the rate of named addresses and trigger spam filters more often.
- **Score:** 100 if under 5%. 50 at 5-15%. 0 if above 15%.

### 7. ICP fit (CRITICAL — weighted 2x)

- **What:** percent of leads matching the locked hypothesis filters on industry + headcount + geography.
- **Requires:** the campaign's hypothesis or `library_data` ICP filters.
- **Rule:** 80%+ match. 100 if exact.
- **Score:** 100 if 80%+. 50 if 60-80%. 0 if below 60%.
- **Skip if:** no hypothesis provided.

### 8. Name quality

- **What:** percent of rows with both `first_name` AND `last_name` populated AND looking human.
- **Checks:** not all-caps, not all-lowercase placeholders (`admin`, `info`), not email-as-name (`john.smith@`), not empty.
- **Rule:** 95%+ acceptable.
- **Score:** 100 if 95%+. Drops linearly to 0 at 70%.

## Letter grade

Weighted average across the 8 dimensions. Dimensions 1 and 7 weighted 2x.

| Avg score | Grade | Action |
|---|---|---|
| 90-100 | A+ / A | Ship it. |
| 80-89 | B | Minor fixes (top 1-3 issues from the report). Ship after. |
| 70-79 | C | Fix top 3-5 issues first. Then re-grade. |
| 60-69 | D | Serious cleanup. Re-run lead-sourcing with tighter filters. |
| below 60 | F | Don't send. Rebuild the list. |

`launch-instantly-campaign` SHOULD refuse to upload C or below by default.

## Output

A markdown scorecard like:

```
=== List Quality Scorecard ===

File: enriched_leads.csv (2,566 rows)
ICP source: locked hypothesis from build-campaign (CapQuest Q3 hypothesis)
Grade: B (84/100)

Dimensions:
1. Email verification:    100/100  (100% verified within 60 days)
2. Duplicate emails:       95/100  (1.1% duplicates — trim before send)
3. Duplicate domains:      78/100  (avg 2.4 per domain — some over-concentration)
4. Title relevance:        82/100  (85% titles match "Director+/Head of Sales")
5. Bad-title detection:    92/100  (3% Coordinators slipped in — filter)
6. Catch-all density:      80/100  (8% catch-all — consider dropping)
7. ICP fit:                88/100  (88% match declared industry + headcount filter)
8. Name quality:           97/100  (good)

Top 5 issues to fix:
1. 28 emails are duplicates (1.1%) — deduplicate before upload
2. 205 leads are on catch-all addresses (8.0%) — drop or move to a separate
   campaign with lower volume
3. 77 Coordinators in the list — filter by seniority before re-running
4. 188 leads cluster on 14 domains (>5 each) — cap at 3 per domain
5. 308 leads outside declared industry filter (12%) — filter by industry

Pre-send checklist:
[ ] Deduplicate by email
[ ] Drop catch-all if over 5% (reduces bounce + improves reply rate)
[ ] Filter out bad titles
[ ] Cap per-domain concentration at 3
[ ] Re-run enrich-and-verify-leads if list shrunk over 10%

Recommendation: APPLY THE 5 FIXES, then re-grade. Expected new grade: A.
```

## Scoring algorithm (deterministic)

For each dimension, compute the raw percentage from the data, then map to the score curve (above). Final grade = weighted average where dimensions 1 and 7 count 2x.

When dimension 7 is skipped (no ICP source), use the weighted average of the remaining 7 dimensions with dimension 1 still weighted 2x.

## How this skill runs

1. Read the input CSV.
2. Validate required columns. If any required column is missing, abort with a clear error.
3. Compute the 8 dimensions in order (skip 4 and 7 if their preconditions fail).
4. Produce the markdown scorecard.
5. If a hypothesis input is provided, save the report to `profiles/<client-slug>/campaigns/<campaign-slug>/scorecard-<YYYY-MM-DD>.md`.
6. Output the grade + top 5 issues to the conversation.

## Output paths

```
profiles/
  <client-slug>/
    campaigns/
      <campaign-slug>/
        scorecard-YYYY-MM-DD.md
```

If `profiles/<client-slug>/` does not exist yet, create it. If `<campaign-slug>` is not provided, use `unknown-campaign`.

## Important rules

- Never block on optional dimensions. If `industry` or `company_employee_count` is missing, skip dimension 7 — report it in the output but don't crash.
- Always weight dimensions 1 and 7 at 2x. They are the make-or-break dimensions.
- Always report 5 fixes max. Reporting 20 fixes is paralysis. The top 5 capture 80% of the impact.
- Never modify the input CSV. This skill grades, it does not mutate.
- The 60-day verification freshness rule (`docs/LEAD_ENRICHMENT_PIPELINE.md`) is enforced inside dimension 1. Stale verifications drop the score even if `email_status='deliverable'`.

## Common failure modes (from real Luxvance lists)

- **Apollo `roleMatchMode: "any"` (instead of "all")** — pulls Coordinators / Assistants. Dimension 5 catches this.
- **Apollo missing both country filters** — pulls people in wrong country at right-country companies. Dimension 7 catches this if `country` is in the ICP, otherwise check manually.
- **Pattern-match Apollo emails** — Apollo's "verified" tag is only 28% reliable (see `docs/LEAD_ENRICHMENT_PIPELINE.md`). Dimension 1 catches these if `email_verified_by = apollo` rather than `million_verifier` or `bounceban`.
- **Catch-all-heavy industries** — UK accounting firms, German insurance brokers, some EU SMBs. Dimension 6 flags this so Jose can decide to drop or run a low-volume separate campaign.
- **Over-concentrated domains** — when Apollo finds a 500-person company that matches the filter loosely, it returns 30+ contacts from that one company. Dimension 3 catches this.

## What to do next

**Grade A or B (≥80):** proceed to `personalized-copywriting` (if not done) or `launch-instantly-campaign`.

**Grade C (70-79):** apply the top 3 fixes (usually deduplicate + drop catch-all + filter bad titles). Re-grade. Should land at A or B.

**Grade D or F (below 70):** the underlying list is broken. Re-run `lead-sourcing` with tighter filters. Common fixes:
- Apollo `roleMatchMode: "all"`
- Both country filters
- Tighter `personTitleIncludes` keyword list
- Stricter `seniorityIncludes`

After re-sourcing, run `enrich-and-verify-leads` again, then this skill again.

## Language

Default to the language of Jose's most recent message for the scorecard report. Internal field names stay in English (CSV columns, dimension labels).

## Learned patterns

<!-- self-improvement entries get appended here when Jose adopts a new dimension or threshold on the fly -->

When the list grows past ~10 entries, promote the durable ones into the main body of this SKILL.md.

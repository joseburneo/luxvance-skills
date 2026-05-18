---
name: competitor-engagers
description: >
  Finds people actively engaging with Luxvance clients' competitor LinkedIn
  posts — the highest-intent prospects for cold outreach. Given a target domain,
  discovers ~20 competitors via LLM, scrapes each competitor's company and
  employee posts (90-day lookback), collects every commenter and reactor,
  deduplicates, and outputs a raw_leads.csv ready for icp-prompt-builder
  qualification and then enrich-and-verify-leads. Triggers on "find competitor
  engagers for [client]", "scrape competitor LinkedIn for [client]", "who is
  engaging with [competitor]", "build a list from competitor engagement",
  "encuentra engagers de [cliente]", "consigue leads de los competidores",
  "scrape LinkedIn de la competencia".
version: 0.1.0
---

# Competitor Engagers

Finds people commenting on or reacting to competitor LinkedIn content. They are already in the buying conversation — the highest-intent prospects available without paid intent data.

## When to use

- The client has 3-5 clearly identifiable competitors with active LinkedIn presence (most Luxvance clients qualify: CapQuest, Connect Resources, Remly, GFV).
- A trigger-based campaign is wanted (the trigger is "engaged with competitor in last 90 days").
- The standard Apollo title-first ICP search is producing low reply rates and Jose wants a higher-intent angle.
- A client specifically asks for "warm" cold prospects.

## When NOT to use

- The client has no clear competitors (e.g. CAMB.AI is in a thin market). Use `lead-sourcing` Apollo path instead.
- Sample target is under 100 leads. The skill takes 30-120 minutes; below 100 prospects it is not worth the wall clock.
- The client's competitors do not post on LinkedIn. Some industries (legal, financial advisory) have quiet competitors.

## Relationship with sibling skills

| Skill | Relationship |
|---|---|
| `lead-sourcing` | This skill is a 4th provider behind `--provider competitor-engagers`. Its output matches the `raw_leads.csv` schema. |
| `icp-prompt-builder` | **Required next step.** Engager lists are 30-50% non-ICP (fans, peers, recruiters, students). Qualify before enriching downstream. |
| `enrich-and-verify-leads` | Runs after icp-prompt-builder has filtered. |
| `campaign-intelligence` | The locked hypothesis defines the competitor set. |
| `personalized-copywriting` | The personalization can reference the specific competitor and post the lead engaged with. |

## Inputs

- **Target domain** — the LUXVANCE CLIENT's domain (e.g. `capquest.com`), not the competitor's. The skill discovers competitors itself.
- **Optional:**
  - Number of competitors to discover (default 20)
  - Posts per competitor (default 30)
  - Specific competitor LinkedIn URLs to include (overrides or augments LLM discovery)
  - Lookback window (default 90 days)

## Outputs

`raw_leads.csv` matching the `lead-sourcing` output schema:

| Column | Source | Notes |
|---|---|---|
| `email` | empty (Apollo / Icypeas fills in next stage) | Engagement data does not include email; downstream enrichment finds it. |
| `first_name`, `last_name` | LinkedIn profile | Capitalized. |
| `company` | LinkedIn profile (current company) | Raw, not normalized. |
| `job_title` | LinkedIn profile | Raw. |
| `industry` | LinkedIn company tag | |
| `website` | LinkedIn company website | |
| `linkedin_url` | profile URL | The signal that brought them into the list. |
| `city`, `country` | LinkedIn profile | |
| **`engaged_with_competitor`** | LinkedIn engagement source | Competitor's company name (e.g. "Cognism"). |
| **`engaged_with_post_url`** | LinkedIn engagement source | URL of the post they engaged with. |
| **`engagement_type`** | LinkedIn engagement source | `comment` or `react`. |
| **`engagement_date`** | LinkedIn engagement source | ISO date. |
| **`total_engagements`** | Aggregated across run | How many competitor posts they engaged with in the window. Higher = warmer. |
| **`source`** | constant | `competitor_engagers` |

The last 6 columns are unique to this provider and survive into `personalized-copywriting` for use in V1/V2 prompts ("noticed you engaged with [competitor]'s post about X").

## How it works

```
Target domain (Luxvance client)
        │
        ▼
[Phase 1] Discover competitors via LLM (default 20)
        │   (Jose can add or override specific competitor LinkedIn URLs)
        ▼
[Phase 2] For each competitor company:
   ├─ Fetch company LinkedIn posts (default 30, 90-day window)
   └─ Fetch employee posts (up to 200 employees, default 30 posts each)
        │
        ▼
[Phase 3] For each post:
   ├─ Collect every commenter (full profile data)
   └─ Collect every reactor (full profile data)
        │
        ▼
[Phase 4] Dedupe by LinkedIn URL across all posts
        │
        ▼
[Phase 5] Drop noise:
   ├─ People employed at the Luxvance client itself
   ├─ People employed at any of the competitors discovered
   ├─ Profiles missing core fields (name, current company)
        │
        ▼
[Phase 6] Aggregate per person:
   ├─ total_engagements (count across all posts)
   ├─ engaged_with_competitor (highest-engagement competitor)
   └─ engaged_with_post_url (most-recent post)
        │
        ▼
[Phase 7] Sort by total_engagements DESC, output raw_leads.csv
```

## Phase 1: Discover competitors

Two paths:

**Path A — LLM-discovered (default):**

1. Scrape the Luxvance client's website homepage + about + customers pages.
2. Prompt Claude with the site context + "list 20 direct competitors with LinkedIn company URLs".
3. Validate each LinkedIn URL is reachable.
4. Surface the list to Jose with a one-line rationale per competitor.

**Path B — Jose-provided:**

1. Jose passes `--extra-competitor=<linkedin-url>` repeatedly (or pastes a list).
2. Skill skips LLM discovery, uses the Jose list directly.
3. Useful when Jose knows the specific competitors better than the LLM does.

**Hybrid:** LLM discovers, Jose adds 2-3 more, run uses the merged list.

Save the final competitor list to `profiles/<client-slug>/competitor-engagers/<YYYY-MM-DD>-competitors.json` for reuse.

## Phase 2: Fetch competitor posts

Use a LinkedIn data provider. Two API options Luxvance can register for:

**Option A: RapidAPI's "Realtime LinkedIn Bulk Data" API** (what GEX uses)
- Endpoint cluster: company posts, employee list, employee posts, post commenters, post reactors.
- Need `RAPIDAPI_KEY` env var (not in `master.env` yet — see registration in "APIs to register" below).
- Cost: ~$0.001 per API call. A full run (20 competitors × 200 employees × 30 posts) hits ~120k calls = $120. **Expensive.**

**Option B: Apify LinkedIn scrapers**
- Several actors exist (`apify/linkedin-companies-scraper`, `apify/linkedin-people-scraper`).
- Cost: ~$2-5 per 1,000 LinkedIn profiles scraped. For a 20-competitor run, roughly $50-100.
- Already have `APIFY_API_TOKEN` in master.env. **Preferred.**

The skill defaults to Apify. Surface cost estimate before triggering.

## Phase 3-5: Collect, dedupe, drop noise

Standard processing. Drop list:

- Anyone whose current company is the Luxvance client.
- Anyone whose current company is one of the competitors discovered (peer noise).
- Profiles with missing name or company.
- Profiles whose title contains: `intern`, `student`, `recruiter` (the recruiter exclusion is debatable — Jose may want to KEEP recruiters for some campaigns; surface as a choice).

## Phase 6: Aggregate per person

For each person, compute:

- `total_engagements` — sum across all posts they touched
- `engaged_with_competitor` — competitor whose posts they engaged with most
- `engaged_with_post_url` — most recent post they engaged with (for the personalization line)
- `engagement_type` — most common type (comment > react if both)
- `engagement_date` — most recent date

Higher `total_engagements` = warmer lead. Sort DESC. Surface top 10 to Jose at the end.

## Phase 7: Output

Write `raw_leads.csv` to `profiles/<client-slug>/competitor-engagers/<YYYY-MM-DD>/raw_leads.csv`.

Surface summary:

```
Done.

Discovered: 20 competitors
Posts fetched: 612 (across companies + employees)
Engagements collected: 8,247
Unique people: 1,403
After noise drop: 1,184

Top 10 most active engagers:
1. Sarah Chen, VP RevOps at TechCo — 12 engagements with Cognism + Apollo
2. ...

Output: profiles/<client>/competitor-engagers/<date>/raw_leads.csv

Next step: run icp-prompt-builder on a 50-row sample BEFORE paying for email
enrichment. Engager lists are typically 30-50% non-ICP.
```

## APIs to register

If `RAPIDAPI_KEY` not in `master.env` and Jose wants the RapidAPI path:

1. Sign up at https://rapidapi.com
2. Subscribe to "Realtime LinkedIn Bulk Data" by `apibuilderz` (or equivalent — verify endpoint coverage)
3. Add `RAPIDAPI_KEY=<key>` to `credentials/master.env`

Apify path uses existing `APIFY_API_TOKEN`. No new registration needed.

## Important rules

- **Discover competitors before scraping.** Never default to a hardcoded competitor list — each Luxvance client has different ones.
- **90-day lookback by default.** Older engagements are stale signals. Override only when a campaign needs a specific older event.
- **Always run `icp-prompt-builder` next** on a 50-row sample. Skipping this step burns money on enrichment of non-ICP rows (LinkedIn fans, peers, recruiters, students).
- **Cost-gate before run.** Surface "this will cost ~$X via Apify, ~Y wall clock minutes". Wait for Jose's go.
- **Resumable.** Save a checkpoint `profiles/<client>/competitor-engagers/<date>/checkpoint.json` after each phase. If the run crashes after Phase 4, resume from Phase 5 without re-paying for Phase 2 LinkedIn fetches.

## Failure modes

| Failure | Recovery |
|---|---|
| LLM-discovered competitors are wrong (not actually competitors) | Jose corrects via `--extra-competitor=` overrides, re-run Phase 1 |
| LinkedIn provider rate-limits | Switch to alternative provider, OR slow down + retry |
| Less than 50 unique engagers found | The competitors are quiet on LinkedIn. Use a different acquisition channel (back to Apollo). |
| Over 50% noise in the output | Run `icp-prompt-builder` to filter. Do NOT widen the noise drop list — let the AI qualifier handle it. |

## Cost expectations

| Run size | API cost | Wall clock |
|---|---|---|
| 5 competitors × 100 employees × 20 posts | ~$15 | 15-30 min |
| 20 competitors × 200 employees × 30 posts (default) | ~$50-100 | 30-120 min |
| 50 competitors × 200 employees × 30 posts (max scale) | ~$300+ | 4-6 hours |

Default is reasonable for most Luxvance clients. Larger runs only when ROI is proven.

## Language

Default to the language of Jose's most recent message for prompts and summary. Competitor-discovery LLM prompt stays in English.

## Learned patterns

<!-- self-improvement entries get appended here when Jose adopts a new heuristic on the fly -->

When the list grows past ~10 entries, promote the durable ones into the main body of this SKILL.md.

## Related files

- `lead-sourcing/SKILL.md` — this skill is a 4th provider behind `--provider competitor-engagers`
- `icp-prompt-builder/SKILL.md` — required next step
- `enrich-and-verify-leads/SKILL.md` — runs after icp-prompt-builder filters the list

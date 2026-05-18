---
name: lead-sourcing
description: >
  Scrapes raw leads matching an ICP filter spec from a chosen provider
  (Apify Apollo by default, Icypeas or Prospeo for email-finder workflows)
  and writes a raw_leads.csv that enrich-and-verify-leads can consume directly.
  Bakes in the filter conventions Jose locked during the 2026-05-17 session
  (roleMatchMode all, BOTH person+company country filters, Director+ seniority
  set, 33-industry exclude list, resume via resetProgress). Triggers on
  "scrape leads for [client]", "saca leads de [ICP]", "corre el Apollo scraper",
  "consigue 5k leads UK Director+", "lead sourcing for [campaign]", "find emails
  for these LinkedIn URLs", "Icypeas / Prospeo lookup", or any ask to go from
  an ICP spec to a raw_leads.csv ready for verification.
version: 0.1.0
---

# Lead Sourcing

Takes an ICP filter spec and produces a `raw_leads.csv` matching the input schema of `enrich-and-verify-leads`. Three providers behind a `--provider` flag.

## When to use

- A new campaign needs fresh leads (not from the master DB).
- An ICP changed and the existing 456k master rows do not cover the new shape.
- A curated LinkedIn list needs emails (Icypeas / Prospeo path).
- Topping up a campaign that ran out of qualified leads.

## When NOT to use

- Pulling existing leads from the master DB — that is a direct SQL query against `nbwbauomozeokflntcwa`, no scraping needed.
- Targeting individual leads — just look them up manually.
- Verification — that is `enrich-and-verify-leads`. This skill assumes the next step is verification.

## Relationship with sibling skills

| Skill | Purpose | When it runs |
|---|---|---|
| `campaign-intelligence` | Decides what ICP to target. | Before this skill. |
| `build-campaign` | Builds the kit, including Sculpture filters that describe the ICP in natural English. | Often runs in parallel with this skill, or before it. The Sculpture brief from build-campaign is a great input to the ICP spec here. |
| **`lead-sourcing`** | **Scrapes raw leads matching the ICP and writes `raw_leads.csv`.** | **Between build-campaign and enrich-and-verify-leads.** |
| `enrich-and-verify-leads` | Verifies the raw emails and applies the 60-day rule. | Immediately after this skill. |

## Providers

### Provider 1: `apify-apollo` (default)

The Apify actor `pipelinelabs/lead-scraper-apollo-zoominfo-lusha-ppe`. Most flexible filters. Pay per result (~$1 per 1,000 leads). Best for net-new ICP scrapes.

Use this provider when:

- Starting from filters (industry, seniority, geography, employee count), not from a name list.
- Volume target is 1,000-50,000 raw leads.
- The ICP is well-defined enough to express as Apollo filters.

### Provider 2: `icypeas`

Email finder. Input: LinkedIn profile URLs OR name + company pairs. Output: best-guess work emails.

Use this provider when:

- Jose has a curated list from Sales Navigator, ZoomInfo, or a CSV someone shared.
- The names + companies are known; only the emails need to be found.
- Volume target is 100-5,000 leads (Icypeas is per-lookup priced).

### Provider 3: `prospeo`

Alternative email finder. Similar input/output to Icypeas. Worth running in parallel with Icypeas when the input list is large and a hit-rate comparison matters.

Use this provider when:

- Same use case as Icypeas but Jose wants a second opinion or Icypeas is rate-limited.

## How to pick a provider

Default to `apify-apollo` unless Jose has a curated list. If he says "I have a list of 800 LinkedIn URLs" or "I have a CSV with names and companies", use `icypeas`. If Icypeas hits a rate limit or returns under 60% match, fall back to `prospeo`.

Ask only when ambiguous.

## Output

**`raw_leads.csv`** — input format for `enrich-and-verify-leads`.

Required columns:

| Column | Source | Notes |
|---|---|---|
| `email` | provider | May be a `pattern_match` guess (Apollo / Icypeas / Prospeo all do this when no verified email exists). Re-verified downstream. |
| `first_name` | provider | Capitalized. |
| `last_name` | provider | Capitalized. |
| `company` | provider | Raw, NOT normalized (that is stage 5's job). |
| `job_title` | provider | Raw. |
| `industry` | provider | Provider's industry taxonomy (Apollo's, in most cases). |
| `website` | provider | Domain, with or without protocol. |
| `linkedin_url` | provider | Profile URL. |
| `city`, `country` | provider | Location. |

Optional columns retained for downstream context (not used by the verifier but useful for filtering):

| Column | Source | Notes |
|---|---|---|
| `company_employee_count` | provider | Estimated headcount, Apollo's count. |
| `company_industry_apollo` | provider | Apollo's industry tag. |
| `seniority` | provider | Apollo's seniority bucket. |
| `email_source` | provider tag | `apollo_verified` / `apollo_pattern_match` / `icypeas` / `prospeo`. Used by the verifier to weight the verification cost. |

Columns to discard before saving:

- `phone`, `mobile`, `direct_phone` — Instantly does not accept phone. Drop early to avoid PII leakage downstream.
- Any provider-specific tracking ID columns (e.g. Apollo's `id`, Icypeas's `lookup_id`) — internal scratch.

Default output path: `raw_leads.csv` in the current working directory, or a path Jose specifies. Ask before overwriting an existing file.

## How it works

### Path 1: `apify-apollo` (default)

```
ICP spec (industry, seniority, geography, employee count, persona keywords)
        │
        ▼
[Phase 1] Build the Apify input JSON from the defaults + Jose's overrides
        │
        ▼
[Phase 2] Confirm cost estimate ($1 per 1,000 results) before triggering
        │
        ▼
[Phase 3] Trigger the Apify actor run (asynchronous)
        │
        ▼
[Phase 4] Poll the run until COMPLETED (typical: 5-30 minutes for 5-25k leads)
        │
        ▼
[Phase 5] Download the dataset, map provider columns to raw_leads.csv schema
        │
        ▼
[Phase 6] Save raw_leads.csv, surface stats (count, seniority breakdown, country split)
```

### Path 2: `icypeas` or `prospeo`

```
Input list (LinkedIn URLs or name+company pairs)
        │
        ▼
[Phase 1] Validate input rows, dedupe by (name, company) or LinkedIn URL
        │
        ▼
[Phase 2] Confirm cost estimate (per-lookup price) before triggering
        │
        ▼
[Phase 3] POST batches to the provider's API (20 workers max)
        │
        ▼
[Phase 4] Collect responses, drop rows with no email found
        │
        ▼
[Phase 5] Map provider response to raw_leads.csv schema (fill `email_source` tag)
        │
        ▼
[Phase 6] Save raw_leads.csv, surface hit rate
```

---

## Apify Apollo path — detailed

### Phase 1: Build the Apify input JSON

Start from the default template in `references/apify-apollo-defaults.json`. Override fields based on Jose's ICP spec.

**Highest-impact fields (always confirm these):**

| Field | What it does | Default |
|---|---|---|
| `companyLocationCountryIncludes` | Country list for the company. | `["United Kingdom"]` (varies per campaign) |
| `personLocationCountryIncludes` | Country list for the person. MUST be set in addition to company country — otherwise you get people in the wrong country at right-country companies. | Same as company. |
| `seniorityIncludes` | Seniority brackets. | `["c_suite", "vp", "director", "owner", "partner"]` (Director+, no manager) |
| `functionIncludes` | Job function brackets. | `["sales", "business_development", "marketing"]` (catches Growth / Demand Gen / Revenue too) |
| `personTitleIncludes` | Keyword filter on title. | Broad keyword list — see defaults file. Helps narrow precisely. |
| `companyEmployeeMin` / `companyEmployeeMax` | Headcount band. | `10` / `100` (typical for $5k+ ACV). |
| `companyIndustryExcludes` | 33-industry B2C / regulated / low-LTV exclude list. | See defaults file. |
| `hasEmail` | Only return rows with an Apollo email (verified or pattern_match). | `true` |
| `roleMatchMode` | How the seniority + title filters combine. | `"all"` — REQUIRED. `"any"` lets entry-level slip past the seniority filter. |
| `totalResults` | Cap. | Ask Jose. Default 25,000 for a campaign-scale scrape. |
| `resetProgress` | Reuse prior runs' state. | `false` — resumes from where prior runs left off, avoids re-paying for dupes. |

**Critical Apollo-specific quirks (from 2026-05-17 session):**

1. **No `head` seniority bucket.** Apollo merges "Head of X" titles into the `director` bucket automatically. Including `director` captures Heads with ~99% accuracy.
2. **`manager` EXCLUDED for Director+ targeting.** Including `manager` pulls "Account Manager" / "Sales Manager" individual contributors. Director+ campaigns target deciders, not ICs.
3. **`roleMatchMode: "any"` is the trap.** Default behavior, but lets entry-level "Outbound Sales" slip past the seniority filter. Always `"all"`.
4. **`hasPhone: false`.** We do not use phone. Including this field forces Apollo to filter on it, narrowing the pool unnecessarily.
5. **Industry excludes drive yield more than ICP keywords.** A clean exclude list keeps the result set high-quality. The 33-industry default covers B2C, regulated, low-LTV.

### Phase 2: Cost estimate

Apify charges per result. The pricing structure on `pipelinelabs/lead-scraper-apollo-zoominfo-lusha-ppe` is roughly $1 per 1,000 results delivered.

Estimate:

> Target 5,000 leads at ~$1 per 1,000 = ~$5. Actual cost is metered on results, not requests, so failed lookups do not bill.

Wait for Jose's "go" before triggering the actor.

### Phase 3: Trigger the actor

Use the Apify MCP tool `mcp__Apify_MCP_server__call-actor` with:

- `actorId`: `pipelinelabs/lead-scraper-apollo-zoominfo-lusha-ppe`
- `input`: the JSON built in Phase 1
- `runOptions`: defaults (timeout 3 hours, build `latest`)

The call returns a run ID. Save it.

### Phase 4: Poll until COMPLETED

Use `mcp__Apify_MCP_server__get-actor-run` with the run ID. Status field cycles through `READY` → `RUNNING` → `SUCCEEDED` / `FAILED`.

Typical wall clock:

- 1,000 leads: ~2-3 minutes
- 10,000 leads: ~10-15 minutes
- 25,000 leads: ~25-35 minutes

Poll every 60 seconds. If status is `FAILED`, fetch the run log via `mcp__Apify_MCP_server__get-actor-run` and surface the error to Jose.

### Phase 5: Download and map

Once the run is `SUCCEEDED`, fetch the dataset via `mcp__Apify_MCP_server__get-actor-output`. The dataset is a JSON array.

Map provider fields to the `raw_leads.csv` schema:

| Apollo field | raw_leads.csv column |
|---|---|
| `email` | `email` |
| `firstName` | `first_name` |
| `lastName` | `last_name` |
| `organization.name` | `company` |
| `title` | `job_title` |
| `organization.industry` | `industry` |
| `organization.websiteUrl` | `website` |
| `linkedinUrl` | `linkedin_url` |
| `city` | `city` |
| `country` | `country` |
| `organization.estimatedNumEmployees` | `company_employee_count` |
| `organization.industry` | `company_industry_apollo` |
| `seniority` | `seniority` |
| `emailStatus` (Apollo's tag) | `email_source` (mapped: `verified` → `apollo_verified`, `pattern_match` → `apollo_pattern_match`) |

Drop:

- Any row missing `email`.
- Any row whose `seniority` is `entry`, `intern`, or `senior` (catches Apollo regressions on `roleMatchMode`).
- Any row whose `organization.estimatedNumEmployees` falls outside the requested band by more than 50% (Apollo sometimes returns out-of-band rows).
- Phone columns.

### Phase 6: Save and report

Write the CSV. Report to Jose:

```
Done. raw_leads.csv at /path/to/file.

Total scraped: 26,237 rows
After filter (Director+, employee band, country): 8,370 rows
Top countries: UK 6,201 / IE 1,109 / MT 412 / Other 648
Top seniorities: Director 4,891 / VP 1,920 / C-Suite 1,033 / Owner+Partner 526
Apollo "verified" emails: 4,231 (51%) — re-verify all of them; only 28% are real per session data
Apollo "pattern_match" emails: 4,139 (49%) — re-verify, expect ~10% deliverable

Cost: $26.24 (~$3.14 per 1,000 sendable leads after verify, assuming 12% yield)

Next step: run enrich-and-verify-leads on this file.
```

---

## Icypeas / Prospeo path — detailed

### Phase 1: Validate input

Inputs come in two shapes:

1. **LinkedIn URL list:** one URL per row. Validate each is a valid LinkedIn profile URL.
2. **Name + company list:** at least `first_name`, `last_name`, `company` per row. `company_domain` is optional but improves hit rate.

Dedupe on the input shape (LinkedIn URL OR `(name + company)` tuple).

### Phase 2: Cost estimate

Icypeas: ~$0.03 per lookup. Prospeo: ~$0.02 per lookup. Both have monthly subscription tiers — check current usage via the provider dashboard before running.

Estimate:

> 800 LinkedIn URLs via Icypeas = ~$24. ~70% expected hit rate = ~560 emails.

Wait for Jose's "go".

### Phase 3: POST to provider

Both APIs accept a single email-lookup request per call. Batch via 20 workers.

**Icypeas:**

- Endpoint: `https://app.icypeas.com/api/email-search` (consult the up-to-date docs in `references/icypeas-howto.md`)
- Auth: `Authorization: Bearer {ICYPEAS_API_KEY}` + signature with `ICYPEAS_API_SECRET`
- Body: `{"firstname": "...", "lastname": "...", "domainOrCompany": "..."}` (varies per endpoint)

**Prospeo:**

- Endpoint: `https://api.prospeo.io/email-finder` (consult `references/prospeo-howto.md`)
- Auth: `X-KEY: {PROSPEO_API_KEY}` (if available — check master.env)
- Body: `{"first_name": "...", "last_name": "...", "company": "..."}`

Read keys with the Python `with open()` pattern documented in [SESSION_HANDOFF_2026-05-17.md](../../../docs/SESSION_HANDOFF_2026-05-17.md).

### Phase 4: Collect and filter

For each response:

- Email found and confidence is high → keep.
- Email found and confidence is medium → keep but tag `email_source` with `_low_confidence` suffix.
- Email not found → drop.

### Phase 5: Map to schema

Fill `email_source`:

- Icypeas verified email → `icypeas_verified`
- Icypeas pattern guess → `icypeas_pattern_match`
- Prospeo verified email → `prospeo_verified`
- Prospeo pattern guess → `prospeo_pattern_match`

### Phase 6: Save and report

```
Done. raw_leads.csv at /path/to/file.

Input rows: 800
Hit: 562 (70%)
  - icypeas_verified: 412
  - icypeas_pattern_match: 150
Miss: 238

Cost: $24.00

Next step: run enrich-and-verify-leads on this file.
```

---

## Important rules

- **Use `roleMatchMode: "all"` on every Apify Apollo run.** No exceptions.
- **Filter country on BOTH person AND company.** Skipping `personLocationCountryIncludes` is the most common pollution source.
- **`resetProgress: false`** on every Apify run unless Jose says "start fresh". Resuming avoids paying for duplicates.
- **Apollo's "verified" tag is unreliable** — only ~28% are actually deliverable per the 2026-05-17 measurement. Always pass the output to `enrich-and-verify-leads` next.
- **Drop phone columns** before saving. PII leak prevention.
- **Never run more than 4 concurrent Apify or Icypeas / Prospeo workers** without Jose's explicit OK. Provider rate limits silently degrade results.
- **Read API keys with `with open()`**, not `grep` or `os.environ`. Master.env is gitignored and `grep`/`ugrep` is blocked.

## Failure modes and recovery

| Failure | Symptom | Recovery |
|---|---|---|
| Apify actor timeout | Run status `RUNNING` past 3 hours | Cancel run, lower `totalResults`, retry. |
| Apify rate limit | 429 on subsequent calls | Wait 60s, retry. Reduce concurrency. |
| Apollo returns out-of-band sizes | Headcount filter ignored | Add post-filter in Phase 5. |
| Apollo returns out-of-country leads | Country filter ignored | Confirm BOTH country filters set. Add post-filter in Phase 5. |
| Icypeas / Prospeo low hit rate | <40% emails found | Try the other provider in parallel. Validate input quality (LinkedIn URLs valid? Company names clean?). |
| Provider API key missing | 401 / 403 | Add to `credentials/master.env`. Confirm with Jose before retry. |

## Language

Default to the language of Jose's most recent message for user-facing prompts (cost estimate, summary report). Filter values and API payloads stay in English because the providers operate in English data.

## Learned patterns

<!-- self-improvement entries get appended here when Jose adopts a new pattern on the fly -->

When the list grows past ~10 entries, consolidate the durable ones into the main body of this SKILL.md (under the relevant section) and prune the entries below. Patterns that get used three or more times are no longer "learned" — they are documented behavior.

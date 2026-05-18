# Lead Enrichment Pipeline

Reference doc for how Luxvance scrapes, verifies, stores, and pushes B2B leads from raw Apollo data to a deliverable-only campaign-ready list.

**Owner:** Jose
**Last updated:** 2026-05-17
**Replaces:** Clay (~$300/mo saved)

---

## What this pipeline does

```
┌────────┐    ┌────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Apify  │───▶│ Master │───▶│ Million  │───▶│ BounceBan│───▶│ Instantly│
│ Apollo │    │ DB     │    │ Verifier │    │ (catch-  │    │ campaign │
│ scrape │    │ upsert │    │ (waterfall│    │  all only)│    │  push    │
└────────┘    └────────┘    └──────────┘    └──────────┘    └──────────┘
```

Goal: end up with a CSV of **deliverable-only** leads ready to push to Instantly without poisoning inbox reputation.

---

## Stage-by-stage

### Stage 1: Apify (lead sourcing)

- **Actor:** `pipelinelabs/lead-scraper-apollo-zoominfo-lusha-ppe`
- **Cost:** $1 per 1,000 leads (pay per result, not per attempt)
- **Filters that matter:**
  - `companyLocationCountryIncludes` + `personLocationCountryIncludes` — both, otherwise you get people in the wrong country at right-country companies
  - `seniorityIncludes`: `["c_suite", "vp", "director", "owner", "partner"]` — Apollo merges "Head of X" into `director` (~99% accuracy in our tests)
  - `functionIncludes`: `["sales", "business_development", "marketing"]` — marketing catches Growth/Demand Gen leaders
  - `personTitleIncludes`: broad keywords (`sales`, `growth`, `business development`, `revenue`, `demand generation`, `chief`, `partnerships`, etc.)
  - `roleMatchMode: "all"` — REQUIRED. Default `any` lets entry-level "Outbound Sales" slip through with seniority=entry.
  - `companyEmployeeMin/Max`: depends on client LTV. 10-100 typical for $5k+ ACV.
  - `companyIndustryExcludes`: 33-industry list (B2C, regulated, low-LTV). See `enrich-and-verify-leads/SKILL.md` for full list.
  - `hasEmail: true`

### Stage 2: Master DB upsert (Supabase)

**Project:** `Luxvance Contact Database` (`nbwbauomozeokflntcwa`, region `eu-west-1`)

**Schema (table `contacts`):**

| Column | Type | Purpose |
|---|---|---|
| `id` | bigint PK | Internal ID |
| `email` | text UNIQUE | Dedup key — UPSERT on this |
| `first_name`, `last_name`, `phone` | text | Person identity |
| `company`, `job_title`, `industry`, `website`, `linkedin_url` | text | Company + role |
| `city`, `country` | text | Location |
| `email_status` | text | `deliverable` / `catch_all` / `bad` / `unknown` / `pattern_match` / `pattern_generated` / `unavailable` |
| `email_verified_at` | timestamptz | When we last verified this email (NULL = never) |
| `email_verified_by` | text | `apollo` / `million_verifier` / `bounceban` |
| `is_sendable` | boolean GENERATED | TRUE iff `email_status = 'deliverable'`. Auto-updates. |

**Insert pattern:** UPSERT on `email` via the edge function `bulk-upsert-contacts`. Existing rows merge — new data fills gaps but never overwrites better data with worse data (uses `COALESCE`).

**Why an edge function and not direct REST:** The `contacts` table has RLS enabled. Edge function runs with `service_role` context, bypasses RLS cleanly without exposing service_role key to clients.

### Stage 3: Million Verifier (primary verification)

**Endpoint:** `https://api.millionverifier.com/api/v3/?api={KEY}&email={EMAIL}&timeout=10`

**Auth:** API key in query string

**⚠️ CRITICAL:** Must set `User-Agent: curl/7.88.1` header. Default Python `urllib` user-agent gets 403 Forbidden after small bursts.

**Rate limit:** Stay at ≤20 concurrent requests. We hit ~170/sec briefly which got throttled later.

**Results mapping:**

| MV `result` | Our `email_status` | `is_sendable` |
|---|---|---|
| `ok` | `deliverable` | TRUE |
| `catch_all` | `catch_all` | FALSE → goes to BounceBan |
| `invalid` | `bad` | FALSE |
| `disposable` | `disposable` | FALSE |
| `unknown` | `unknown` | FALSE |
| `error` | (don't write; leave as-is) | n/a |

**Cost:** ~$0.0006 per check.

### Stage 4: BounceBan (catch-all resolver)

**Endpoint:** `https://api.bounceban.com/v1/verify/single?email={EMAIL}`

**Auth:** `Authorization: Bearer {KEY}` header OR `?api_key={KEY}` query param. NOT `X-API-KEY` (returns 401).

**Why only on catch_all:** BounceBan is more expensive per check and specialized for catch-all servers. Million Verifier handles the rest faster + cheaper.

**Results mapping:**

| BB `result` | Our `email_status` | `is_sendable` |
|---|---|---|
| `deliverable` | `deliverable` | TRUE |
| `undeliverable` | `bad` | FALSE |
| `risky` | `catch_all` | FALSE (still risky after BB — don't send) |
| `unknown` | `unknown` | FALSE |

**Cost:** ~$0.005 per check.

### Stage 5: Campaign push (Instantly)

- Use the `contacts_for_send` VIEW: only deliverable + verified within 60 days
- Apply 30-day re-contact rule per client (TODO: needs `contact_sends` table — not built yet)
- Push to Instantly via per-client MCP (`mcp__instantly-{client}__*`) or REST API with `INSTANTLY_API_KEY_{CLIENT}` from `master.env`

---

## Conventions

### 60-day verification freshness rule

**Rule:** A lead is considered "campaign-ready" only if `email_verified_at > now() - interval '60 days'`. Older verifications must be re-run before pushing to Instantly.

**Rationale:** Email deliverability decays. People leave companies, domains expire, mailservers change. 60 days balances:
- Cost (re-verifying 1,400 sendable leads = ~$1)
- Risk (sending to dead emails kills inbox reputation)

**Implementation:** `contacts_for_send` VIEW filters this automatically. `contacts_needing_reverification` VIEW shows leads that need refresh before use.

### Lazy verification

**Do NOT** bulk re-verify legacy contacts upfront. The master DB has 456k+ contacts from older imports — verifying them all would cost ~$275.

**Instead:** Verify only when a lead is being pulled into a campaign. The `enrich-and-verify-leads` skill handles this automatically:

```
1. Query master DB for ICP candidates
2. For each candidate, check email_verified_at:
   - Fresh (<60d) + sendable → include
   - Fresh (<60d) + not sendable → discard
   - Stale (>60d or NULL) → run MV + BB → then include/discard
3. Push final deliverable list to Instantly
```

**Result:** Pay verification cost only on leads we actually use. Typical campaign of 5,000 candidates = ~$3-5 verification cost.

### Apollo "deliverable" is unreliable

Empirical finding from 2026-05-17 (n=3,975): When Apollo claims `deliverable`, Million Verifier disagrees **72% of the time**:

| MV verdict on Apollo "deliverable" | Count | % |
|---|---|---|
| `invalid` (bad) | 1,829 | 46.0% |
| `ok` (true deliverable) | 1,120 | 28.2% |
| `catch_all` | 654 | 16.5% |
| `unknown` | 372 | 9.4% |

**Conclusion:** Always run Million Verifier even on Apollo-tagged "deliverable". Never push directly from Apollo to Instantly.

### Yield expectations

From a typical Apollo scrape with our filters, expect:

- ~5-15% become MV-verified deliverable
- BounceBan recovers ~40% of MV catch_all → another 3-5%
- **Total yield: 8-20% of raw scrape becomes sendable**

Plan campaign volume accordingly. To get 5k sendable leads, scrape 30-50k raw.

---

## Costs reference (per 1,000 leads)

| Stage | Cost per 1,000 | Notes |
|---|---|---|
| Apify (Apollo scraper) | $1.00 | Pay per result |
| Million Verifier | $0.60 | $0.0006/check |
| BounceBan | ~$5.00 | $0.005/check; only on catch_all (~10-20% of MV-checked) |
| Supabase (storage) | $0.00 | Within plan limits |
| Instantly | varies | Per-client subscription, not per-lead |

**Real example (2026-05-17 session):**
- 26,237 leads scraped (3 Apify runs)
- 8,370 made it past Director+/Head + companyDescription filter
- Million Verifier ran on all 8,370 → 1,120 deliverable + 654 catch_all + 1,829 bad + 4,767 unknown
- BounceBan ran on 654 catch_all → +270 deliverable rescued
- **Final: 1,390 sendable leads**
- **Total cost: $34**
- **Cost per sendable lead: $0.024**

---

## Common pitfalls

1. **Don't trust `roleMatchMode: "any"`** — lets entry-level reps slip past your seniority filter. Always use `"all"`.

2. **Don't forget User-Agent on MV** — silently returns 403 for default Python UA, looks like API failure.

3. **Don't upsert MV "error" results to the DB** — they aren't real verification verdicts. Just retry or skip.

4. **Don't push pattern_match emails to Instantly** — Apollo's pattern guess is wrong 70%+ of the time per our data.

5. **Don't bulk re-verify legacy contacts** — wasteful. Use lazy verification per campaign.

6. **Don't share service_role key with clients** — only the publishable/anon key is safe to embed in code. Edge functions handle the privileged work.

---

## Open evaluations (TODO)

### Alternative verification suppliers

We currently use **MillionVerifier ($0.0006/check) + BounceBan ($0.005/check)**. Before next big scrape, evaluate alternatives on cost + accuracy:

| Candidate | Pricing (approx) | Worth testing? |
|---|---|---|
| Reoon | $0.0005/check, claims 99% catch-all resolution | YES — could replace BounceBan |
| Bouncer | $0.005/check, includes catch-all in single pass | YES — could replace whole MV+BB |
| Emailable | $0.007/check | Probably not — more expensive |
| ZeroBounce | $0.008/check | Probably not |
| NeverBounce | $0.008/check | Probably not |

**Method:** take 200 emails of known verdict (50 deliverable, 50 catch_all, 50 bad, 50 unknown from our current data) and run them through each. Compare verdicts + cost. Pick winner.

### Diminishing returns on second pass

Session 2026-05-17 finding: running a SECOND pass of MV + BB on the gray zone of an 8,370-batch:
- Recovered +1,249 more deliverable (+89%)
- Cost: $10.56 extra ($0.0085 per recovered lead)
- Was actually 3x cheaper per lead than pass 1, BUT only valuable if you'll use the extra volume

**Rule of thumb:** default to single-pass. Only run the gray-zone second pass when a specific campaign needs more volume than the first pass gives.

## Related files

- **Skill (executable):** `.claude/skills/enrich-and-verify-leads/SKILL.md`
- **Credentials:** `credentials/master.env`
- **Edge functions:** `bulk-upsert-contacts`, `get-emails-by-status` (both in Supabase project `nbwbauomozeokflntcwa`)
- **Views:** `contacts_for_send`, `contacts_needing_reverification`

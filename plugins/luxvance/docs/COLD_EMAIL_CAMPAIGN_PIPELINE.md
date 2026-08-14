# Cold Email Campaign Pipeline

> **⚠️ SUPERSEDED 2026-05-31.** The standalone Contact DB project (`nbwbauomozeokflntcwa`) was deleted in the Supabase consolidation. The master now lives in Agency OS `core.contacts` (`sgaeggmkmipcoikzqwpy`). For the current flow see [`docs/sops/lead-flow-supabase.md`](../sops/lead-flow-supabase.md). Sections below referencing the old project / `bulk-upsert-contacts` edge function are historical.

Umbrella reference for how Luxvance ships a cold email campaign end-to-end without Clay, from past-performance analysis to a DRAFT campaign sitting in Instantly. Six skills, four data files, one orchestrator (planned).

**Owner:** Jose
**Last updated:** 2026-05-17
**Replaces:** Clay (~$300/mo saved per client at typical volume)

---

## The pipeline at a glance

```
┌──────────────────────┐
│ campaign-intelligence│  Analyst. Reads past campaign + reply data, iterates with
│                      │  Jose, locks a hypothesis + client-request statement.
└──────────┬───────────┘
           │  hypothesis.md (locked) + client_request.md
           ▼
┌──────────────────────┐
│ build-campaign       │  Production engineer. Ships the 10-block kit:
│                      │  campaign name, brief, rendered email, Clay prompts,
│                      │  Instantly spintax, and variants.yaml.
└──────────┬───────────┘
           │  variants.yaml + Notion task for Marko/Ana (if manual path)
           ▼
┌──────────────────────┐
│ lead-sourcing        │  Scraper. Apify Apollo (default) / Icypeas / Prospeo.
│ (NEW, TODO)          │  Pulls raw leads matching ICP filters.
└──────────┬───────────┘
           │  raw_leads.csv
           ▼
┌──────────────────────┐
│ enrich-and-verify-   │  Waterfall verifier. Upserts to Supabase master,
│ leads                │  runs Million Verifier → BounceBan, applies the
│                      │  60-day freshness rule.
└──────────┬───────────┘
           │  verified.csv (deliverable-only)
           ▼
┌──────────────────────┐
│ personalized-        │  Per-lead copy generator. Sonnet/Opus subagents
│ copywriting          │  produce variable_1, variable_2 (and optional
│ (NEW, TODO)          │  situation/value/cta lines). Iterative QA loop.
└──────────┬───────────┘
           │  enriched_leads.csv
           ▼
┌──────────────────────┐
│ launch-instantly-    │  Deployer. Consumes variants.yaml + enriched_leads.csv,
│ campaign             │  creates DRAFT in Instantly via MCP, attaches inboxes
│                      │  by tag, schedules. Stops at DRAFT for Jose to start.
└──────────────────────┘
```

The pipeline is deliberately decoupled. Each skill consumes a well-defined file from the previous stage and emits a well-defined file for the next one. That lets Jose re-run any stage in isolation, hand a stage off to a teammate, or replace a stage's implementation (e.g. swap Apify for Icypeas) without touching the rest.

A future orchestrator skill — working name `build-cold-email-campaign` — will chain all six. For now, each runs on its own.

---

## Skill index

**Create-side pipeline (6 skills + orchestrator):**

| # | Skill | Status | Path |
|---|---|---|---|
| 1 | `campaign-intelligence` | Exists | `.claude/skills/campaign-intelligence/SKILL.md` |
| 2 | `build-campaign` | Exists (v3 with GEX frameworks, sequence config, self-improve) | `.claude/skills/build-campaign/SKILL.md` |
| 3 | `lead-sourcing` | Exists | `.claude/skills/lead-sourcing/SKILL.md` |
| 4 | `enrich-and-verify-leads` | Exists | `.claude/skills/enrich-and-verify-leads/SKILL.md` |
| 4.5 | `list-quality-scorecard` | Exists (2026-05-18) | `.claude/skills/list-quality-scorecard/SKILL.md` |
| 5 | `personalized-copywriting` | Exists (v2 with saved prompt reuse) | `.claude/skills/personalized-copywriting/SKILL.md` |
| 6 | `launch-instantly-campaign` | Exists | `.claude/skills/launch-instantly-campaign/SKILL.md` |
| ★ | `build-cold-email-campaign` (orchestrator) | Exists (2026-05-18) | `.claude/skills/build-cold-email-campaign/SKILL.md` |

**Optimize-side layer (5 skills, new 2026-05-18):**

| # | Skill | Status | Path |
|---|---|---|---|
| O1 | `cold-email-weekly-rhythm` | Exists | `.claude/skills/cold-email-weekly-rhythm/SKILL.md` |
| O2 | `positive-reply-scoring` | Exists | `.claude/skills/positive-reply-scoring/SKILL.md` |
| O3 | `experiment-design` | Exists | `.claude/skills/experiment-design/SKILL.md` |
| O4 | `deliverability-audit` | Exists | `.claude/skills/deliverability-audit/SKILL.md` |
| O5 | `deliverability-incident-response` | Exists | `.claude/skills/deliverability-incident-response/SKILL.md` |

**Always-on guardrail:**

| # | Skill | Status | Path |
|---|---|---|---|
| G1 | `spam-word-checker` | Exists (auto-triggers inside build-campaign + personalized-copywriting) | `.claude/skills/spam-word-checker/SKILL.md` |

**Strategy + intake (new 2026-05-18, second sprint):**

| # | Skill | Status | Path |
|---|---|---|---|
| S1 | `campaign-strategy` | Exists (2026-05-18) — 15-25 forward-looking idea generator | `.claude/skills/campaign-strategy/SKILL.md` |
| S2 | `lead-magnet-brainstorm` | Exists | `.claude/skills/lead-magnet-brainstorm/SKILL.md` |
| S3 | `icp-prompt-builder` | Exists | `.claude/skills/icp-prompt-builder/SKILL.md` |

**Acquisition channels (new 2026-05-18, complements lead-sourcing):**

| # | Skill | Status | Path |
|---|---|---|---|
| C1 | `competitor-engagers` | Exists | `.claude/skills/competitor-engagers/SKILL.md` |
| C2 | `google-maps-list-builder` | Exists | `.claude/skills/google-maps-list-builder/SKILL.md` |

**Infrastructure operations (new 2026-05-18, wraps existing Render crons):**

| # | Skill | Status | Path |
|---|---|---|---|
| I1 | `instantly-inbox-manager` | Exists (wraps `ramp_agent.py` + `inbox_placement.py`) | `.claude/skills/instantly-inbox-manager/SKILL.md` |
| I2 | `domain-name-generator` | Exists (Phase A — name + availability check) | `.claude/skills/domain-name-generator/SKILL.md` |
| I3 | `domain-provision-zapmail` | Deferred (Phase B — purchase + provision) | TBD |

See [INBOX_AND_DOMAIN_INFRASTRUCTURE_AUDIT.md](INBOX_AND_DOMAIN_INFRASTRUCTURE_AUDIT.md) for the full audit of what existing Luxvance code already covers vs the gaps these skills close.

Sub-docs:

- [LEAD_ENRICHMENT_PIPELINE.md](LEAD_ENRICHMENT_PIPELINE.md) — deep-dive on the verification stage (skill #4). Schema of the `contacts` table, MV/BB API details, common pitfalls. Read this before touching the master DB or verification waterfall.
- [SYSTEM_MANUAL.md](SYSTEM_MANUAL.md) — broader Luxvance system manual (Render services, Notion sync, etc.).
- [RENDER_SERVICES.md](RENDER_SERVICES.md) — Render cron and worker reference.

---

## Stage 1 — `campaign-intelligence`

**Role:** Analyst.

**Input:** A client name. Implicit: full history of past campaigns + replies for that client (Supabase project `sgaeggmkmipcoikzqwpy`).

**Output:** A locked hypothesis + client-request statement. Free-form text in the conversation; Jose copy-pastes it into `build-campaign`'s opening prompt.

**Closes when:** Jose says the hypothesis is locked. The skill is deliberately iterative — pushes back, refines, vetoes. It does not execute, does not create assets, does not modify data.

**Reads from:** `clients`, `campaigns`, `lead_replies`, `campaign_daily_snapshots` tables in Supabase `sgaeggmkmipcoikzqwpy`.

**Does not produce a file.** The handoff to the next skill is a paragraph or two of locked direction. That is intentional — the human-readable hypothesis is what `build-campaign` needs, not structured JSON.

---

## Stage 2 — `build-campaign`

**Role:** Production engineer.

**Input:** Locked hypothesis (from stage 1) + client request statement.

**Output:** 10-block kit. Blocks 1-9 are paste-ready text for Clay and Instantly (used when the campaign goes through Marko or Ana manually). Block 10 is `variants.yaml`, the machine-readable mirror that `launch-instantly-campaign` consumes.

**Block 10 schema:** See `.claude/skills/launch-instantly-campaign/references/variants-schema.yaml`. Covers campaign name, schedule (timezone, days, hours, throttle), sender account selection by Instantly tag, sequences with A/B/C variants.

**Pending edits (queued for Phase 1B):**

1. Sequence config questions at close (1/2/3 steps? days between?), baked into `variants.yaml`.
2. Self-improving prompt: "Today we did X different from the documented pattern. Add to the skill?" auto-edits its own SKILL.md.
3. More Phase 1 gathering questions: region/currency, preferred proof asset, recent market trigger or objection.

---

## Stage 3 — `lead-sourcing` (TODO)

**Role:** Scraper.

**Input:** ICP filter spec (industries, seniorities, company size, country, etc.). Provider flag.

**Output:** `raw_leads.csv` with columns:

| Column | Source | Notes |
|---|---|---|
| `email` | Apollo / Icypeas / Prospeo | Required. May be Apollo's `pattern_match` guess (must be re-verified downstream). |
| `first_name` | Provider | Capitalized. |
| `last_name` | Provider | Capitalized. |
| `company` | Provider | Raw company name as scraped. NOT normalized (that's stage 5's job). |
| `job_title` | Provider | Raw title. |
| `industry` | Provider | Apollo industry taxonomy. |
| `website` | Provider | Domain. |
| `linkedin_url` | Provider | Profile URL. |
| `city`, `country` | Provider | Location. |
| `phone` | Provider (optional) | Discarded before stage 6 — Instantly does not accept phone. |

**Providers behind `--provider` flag:**

- `apify-apollo` (default) — actor `pipelinelabs/lead-scraper-apollo-zoominfo-lusha-ppe`. Most flexible filters. ~$1/1k leads.
- `icypeas` — email finder. Input: LinkedIn URLs or name+company pairs. Output: emails.
- `prospeo` — alternative email finder.

**Critical filters (Apify Apollo):** documented in `LEAD_ENRICHMENT_PIPELINE.md` and in the Apollo input template archived in `SESSION_HANDOFF_2026-05-17.md`. Highlights:

- `roleMatchMode: "all"` is REQUIRED (default `"any"` lets entry-level slip past seniority filter).
- Filter on BOTH `companyLocationCountryIncludes` AND `personLocationCountryIncludes`.
- For Director+ targeting use `["c_suite", "vp", "director", "owner", "partner"]` (Apollo merges Head → director). Exclude `manager`.
- `companyIndustryExcludes` is a 33-industry list (B2C, regulated, low-LTV).
- `resetProgress: false` to resume from prior runs without duplicating leads.

**Cost:** ~$1 per 1,000 raw leads (Apify, pay per result).

---

## Stage 4 — `enrich-and-verify-leads`

**Role:** Waterfall verifier.

**Input:** `raw_leads.csv` (from stage 3) OR an arbitrary email list.

**Output:** `verified.csv` — same schema as raw_leads.csv plus three verification columns:

| Column | Type | Values |
|---|---|---|
| `email_status` | text | `deliverable`, `catch_all`, `bad`, `unknown`, `disposable`, `pattern_match` |
| `email_verified_at` | timestamptz | When this verification ran |
| `email_verified_by` | text | `million_verifier`, `bounceban`, `apollo`, `manual` |

Plus `is_sendable` (boolean, generated): TRUE iff `email_status='deliverable'`.

**Default filter on output:** only rows where `is_sendable=true` and `email_verified_at > now() - interval '60 days'`. That is the SQL VIEW `contacts_for_send` in the master DB.

**Reads/writes:** Supabase project `nbwbauomozeokflntcwa`, table `contacts`. UPSERTs by `email`. Bypasses RLS via the edge function `bulk-upsert-contacts`.

**Waterfall:**

```
raw_leads.csv
   │
   ▼
1. UPSERT to contacts table (bulk-upsert-contacts edge function)
2. SELECT leads needing verification (NULL or > 60d)
3. Million Verifier (20 concurrent workers, User-Agent: curl/7.88.1 header)
       ok        → email_status='deliverable'
       catch_all → step 4
       invalid   → email_status='bad'
       unknown   → email_status='unknown'
4. BounceBan on catch_all only
       deliverable   → email_status='deliverable'
       undeliverable → email_status='bad'
       risky         → email_status='catch_all' (still risky, don't send)
5. UPSERT verification verdicts back to contacts
6. Export contacts_for_send VIEW → verified.csv
```

See [LEAD_ENRICHMENT_PIPELINE.md](LEAD_ENRICHMENT_PIPELINE.md) for the full reference: API endpoints, auth quirks (MV needs custom User-Agent, BB uses Bearer not X-API-KEY), rate limits, yield expectations (~8-20% of raw scrape becomes sendable), and the empirical finding that **Apollo's "deliverable" tag is only 28% real** — always re-verify.

**Cost:** ~$0.60 per 1,000 MV checks; ~$5 per 1,000 BB checks (only on the ~10-20% catch_all subset). Real total per 1,000 raw leads: ~$1.60.

---

## Stage 5 — `personalized-copywriting` (TODO)

**Role:** Per-lead copy generator. Replaces what Clay AI did with Claygents, but runs locally via Claude Code subagents on Jose's Max plan.

**Input:** `verified.csv` (from stage 4) + the rendered email template + variable prompts from `build-campaign` (blocks 6 and 7).

**Output:** `enriched_leads.csv` matching the schema in `.claude/skills/launch-instantly-campaign/references/leads-csv-schema.md`. Required columns:

| Column | Source | Notes |
|---|---|---|
| `email` | verified.csv | Recipient. |
| `first_name`, `last_name` | verified.csv | Capitalized. |
| `company_name` | normalized from `company` | Strip LTD/LIMITED/LLC/INC/PLC. Fix ALL CAPS → Title Case. Preserve intentional lowercase brands (iPhone, ThinkAnalytics, Black&Callow). |

Allowed optional columns:

| Column | Source | Purpose |
|---|---|---|
| `company_domain` | verified.csv `website` | Merge field `{{companyDomain}}`. |
| `title` | verified.csv `job_title` | Merge field `{{title}}`. Lowercase recommended. |
| `linkedin_url` | verified.csv | Merge field `{{linkedinUrl}}`. |
| `variable_1` | AI-generated | Prospect's own company segment. 2-8 words, lowercase, no trailing punctuation. |
| `variable_2` | AI-generated | Three named brands matching variable_1's size descriptor. |
| `situation_line`, `value_line`, `cta_line` | AI-generated (optional) | Full sentences if the template calls for them. |

**Iterative QA loop (Jose's specific request):**

1. Model choice prompt: Sonnet (default, Max plan quota) / Opus (max quality, more quota) / parallel test with OpenAI `gpt-4o-mini` for comparison.
2. Cost estimate up front: "Sonnet 2,623 leads ≈ X% of weekly Sonnet quota. Opus ≈ Y%. OpenAI ≈ $0.30."
3. Batch 1 of 10 leads → render full email (subject + body, all variables filled) → show to Jose. Jose says OK or asks to adjust prompt.
4. Batch 2 of 10 → render → show → feedback.
5. Batch 3 of 10 → render → show → final OK.
6. After 30 leads with OK: run full batch via parallel Sonnet subagents (3 batches in parallel typical).
7. QA pass: 3 more agents output keep / fix / drop per lead. Drop charities, gov, no-fit (typical drop rate 2-4%).

**Critical rules (lessons from 2026-05-17 session, must bake into the prompt):**

- Variable 1 must NEVER echo the lead's own role. If the lead is a Sales Director, V1 must NOT be "Sales Directors at X" — they would be talking about themselves.
- Variable 2 brand size must match V1 size descriptor. Mid-market V1 → mid-market brands. Enterprise V1 → enterprise brands.
- companyName normalization rules: strip LTD/LIMITED/LLC/INC/PLC; fix ALL CAPS to Title Case; preserve intentional lowercase brands.

**Few-shot examples** (Jose's patterns from existing 1,491 leads):

```
Lead: Business Director at Gleeson Recruitment (staffing)
  → V1: "General Managers at growing companies"
  → V2: "Jaguar Land Rover, Rolls-Royce, and John Lewis"

Lead: VP Sales EMEA at ThinkAnalytics (media analytics)
  → V1: "Heads of Revenue at enterprise companies"
  → V2: "Sky, ITV, and Channel 4"

Lead: Business Director at IDEX Consulting (insurance)
  → V1: "Chief People Officers at insurance carriers"
  → V2: "Aviva, AXA UK, and Zurich Insurance Group"

Lead: BD Director at IFS assyst (ITSM software)
  → V1: "CIOs at enterprise companies"
  → V2: "Tesco, Vodafone, and Unilever"

Lead: Sales Director at Black&Callow (legal/IPO services)
  → V1: "CEOs at enterprise companies"
  → V2: "Aviva, HSBC, and Legal & General"
```

**Cost:** Sonnet via Max plan subagents — effectively $0 out of pocket, ~5-10% of weekly Sonnet quota per 2,500 leads. OpenAI fallback ~$0.30 per 2,500 leads.

---

## Stage 6 — `launch-instantly-campaign`

**Role:** Deployer.

**Input:** `variants.yaml` (from stage 2) + `enriched_leads.csv` (from stage 5).

**Output:** A DRAFT campaign in Instantly via MCP (`mcp__instantly-{client}__*` tools). Always stops at DRAFT. Jose reviews and activates from the Instantly UI.

**What it does:**

1. Validates `leads.csv` columns against the allowlist (`references/leads-csv-schema.md`). Aborts on any disallowed column.
2. Creates the campaign with name from `variants.yaml`.
3. Attaches sending accounts by Instantly tag.
4. Builds the sequence with steps + A/B/C variants (spintax bodies + subjects).
5. Uploads leads in batches with custom variables.
6. Sets the schedule (timezone, days, hours, throttle, max new leads per inbox per day).
7. Confirms DRAFT state. Reports campaign ID + Instantly UI URL.

**What it does NOT do:**

- Does not write copy (that's stage 2).
- Does not verify emails (that's stage 4 — CSV must already be `is_sendable=true`).
- Does not activate the campaign (Jose hits Start manually after review).

**Allowed CSV columns:** see `.claude/skills/launch-instantly-campaign/references/leads-csv-schema.md`. Disallowed: phone, address, internal scoring fields, anything not on the allowlist. Hard fail on schema drift.

**Cost:** $0 per lead (Instantly is per-workspace subscription, not per-send).

---

## Data file contracts between stages

```
            ┌─────────────────────┐
hypothesis  │ (free-form text     │  stage 1 → stage 2
+ request   │  in conversation)   │  Jose pastes it in.
            └─────────────────────┘

            ┌─────────────────────┐
variants    │ variants.yaml       │  stage 2 → stage 6
.yaml       │ schema: launch-     │  (skips 3, 4, 5 — variants.yaml is
            │  instantly-campaign │  about copy + schedule, not leads)
            │  /references/       │
            └─────────────────────┘

            ┌─────────────────────┐
raw_leads   │ email, first_name,  │  stage 3 → stage 4
.csv        │ last_name, company, │
            │ job_title, industry,│
            │ website, linkedin,  │
            │ city, country       │
            └─────────────────────┘

            ┌─────────────────────┐
verified    │ raw_leads cols      │  stage 4 → stage 5
.csv        │ + email_status      │  (only is_sendable=true rows)
            │ + email_verified_at │
            │ + email_verified_by │
            └─────────────────────┘

            ┌─────────────────────┐
enriched_   │ email, first_name,  │  stage 5 → stage 6
leads.csv   │ last_name,          │
            │ company_name (norm),│
            │ company_domain,     │
            │ title, linkedin_url,│
            │ variable_1,         │
            │ variable_2,         │
            │ [situation/value/   │
            │  cta_line optional] │
            └─────────────────────┘
```

The transition from `verified.csv` to `enriched_leads.csv` involves both normalization (`company` → `company_name`) and column drops (drop `industry`, `city`, `country`, `phone` — Instantly does not accept them). Stage 5 owns both transformations.

---

## Cost reference (per 1,000 raw leads)

End-to-end cost from raw scrape to DRAFT in Instantly. Numbers from the 2026-05-17 session, normalized to per-1,000.

| Stage | Tool | Per 1,000 raw leads | Notes |
|---|---|---|---|
| 1 | `campaign-intelligence` (Sonnet) | ~$0 | Max plan quota, one-time per campaign (not per lead). |
| 2 | `build-campaign` (Sonnet) | ~$0 | Max plan quota, one-time per campaign. |
| 3 | `lead-sourcing` (Apify Apollo) | $1.00 | Pay per result. |
| 4 | `enrich-and-verify-leads` (MV + BB) | ~$1.60 | $0.60 MV all + $1 BB on catch_all subset. |
| 5 | `personalized-copywriting` (Sonnet) | ~$0 | Max plan quota. Only runs on verified subset (~10-20% of raw), so ~$0.05 worst case if OpenAI fallback used. |
| 6 | `launch-instantly-campaign` (MCP) | $0 | No per-lead cost. |
| | **Total per 1,000 raw leads** | **~$2.60** | Yields ~100-200 sendable leads after verification. |
| | **Total per 1,000 SENDABLE leads** | **~$17** | Assuming 15% yield. |

**Comparison:** Clay charges ~$300/month per client for the same workflow at typical Luxvance volume. Six clients = ~$1,800/month. Replacing Clay with this pipeline saves the agency that recurring cost, with the only fixed substitution being Claude Code (already paid via Max plan) and the Apify + MV + BB usage above.

---

## Reference example: the 2026-05-17 A/B test

This session shipped the first campaign built end-to-end through this pipeline (skipping stage 5 since stages 5 and 3 were not yet packaged as skills — stage 5 ran ad hoc via Sonnet subagents in `/tmp/`).

**Campaign:** `Luxvance - UK - Sales Leaders 10-100 - W20 - Claude Code` (id `9987af18-4275-4d9b-b5b2-d3deed227899`).

| Stage | Tool | Input | Output | Cost |
|---|---|---|---|---|
| 3 (lead-sourcing) | Apify Apollo, 3 runs | UK Director+/Head, 10-100 emp, B2B industries | 26,237 raw leads | $25.89 |
| (filter) | Manual SQL on raw scrape | companyDescription + seniority sanity check | 8,370 qualified | — |
| 4 (enrich-and-verify) | MV + BB, 2 passes | 8,370 emails | 2,639 deliverable (1,390 first pass + 1,249 recovered) | $18.91 |
| 5 (personalize) | 3 Sonnet subagents in parallel | 2,623 leads (after dedup vs older campaign) | 2,623 with V1 + V2 + normalized companyName | Max plan quota |
| (QA) | 3 more Sonnet subagents | 2,623 enriched | 53 drops + 671 fixes | Max plan quota |
| 6 (launch-instantly) | MCP | variants.yaml + 2,566 final leads | DRAFT in Instantly | $0 |

Total out-of-pocket: **~$44.80** for 2,566 sendable leads delivered to Instantly DRAFT, vs ~$300/mo for the equivalent Clay workflow.

**A/B test setup:**

| | Clay-built | Claude-Code-built |
|---|---|---|
| Campaign ID | `9be79365-b273-41c0-8192-ba3f6189f7de` | `9987af18-4275-4d9b-b5b2-d3deed227899` |
| Leads | 1,491 | 2,566 |
| Copy template | Same | Same |
| Schedule | Same | Same |
| Sequence | 1 step | 1 step |

Pure comparison on reply rate + opportunity rate once both are active.

---

## Conventions across the pipeline

### 60-day verification freshness rule

A lead is campaign-ready only if `email_verified_at > now() - interval '60 days'`. Older verifications must be re-run before stage 6. The `contacts_for_send` VIEW filters this automatically. See [LEAD_ENRICHMENT_PIPELINE.md](LEAD_ENRICHMENT_PIPELINE.md#60-day-verification-freshness-rule) for rationale.

### Lazy verification

Never bulk re-verify the 456k legacy contacts in the master DB upfront. Verify only when pulling candidates into a campaign. See [LEAD_ENRICHMENT_PIPELINE.md](LEAD_ENRICHMENT_PIPELINE.md#lazy-verification).

### Spanish-or-English

Every skill in the pipeline supports Spanish and English triggers and responses. Jose alternates fluidly between both. Match his language in the same conversation.

### Stop at DRAFT

Stage 6 always stops at DRAFT in Instantly. Activation is manual — Jose attaches sending inboxes by tag in the Instantly UI, then hits Start. This is intentional: it gives Jose one final review point before any email leaves a Luxvance inbox.

### Decoupled stages, file-based handoff

Every stage reads a file and writes a file (except stage 1, which produces conversational handoff text, and stages 1+2 which run inside Claude). Any stage can be re-run in isolation. Any stage can be handed off to a teammate.

### Schema is the contract

Stage 6 (`launch-instantly-campaign`) hard-fails on any column not in its allowlist. Stage 4 hard-fails if the master DB schema does not match expectations. This catches PII leaks (no phone, no address) and silent merge-field mismatches (no typo'd `compny_domain`) at the boundary, not in production.

---

## Open work

### Phase 1A — Write the umbrella doc ✅

You are reading it. Done 2026-05-17.

### Phase 1B — Edit `build-campaign` ✅

Done 2026-05-17. Added:

- Phase 2 calibration questions expanded from 1 to up to 4 (region, angle, proof asset, market trigger).
- Phase 7 sequence config question (1/2/3 steps + days between), asked before block 10.
- Phase 8 produces block 10 (`variants.yaml`) using the chosen sequence.
- Phase 9 self-improvement check + `## Learned patterns` section template at the bottom of the SKILL.md.

### Phase 2 — Build `personalized-copywriting` ✅

Done 2026-05-17. Includes:

- Iterative QA loop (10 → 10 → 10 → full batch).
- Model choice prompt (Sonnet / Opus / OpenAI fallback).
- Few-shot prompt with the V1/V2 examples in `references/subagent-prompt.md`.
- Company name normalization rules in `references/company-name-normalization.md`.
- Output matches `launch-instantly-campaign/references/leads-csv-schema.md`.

### Phase 3 — Build `lead-sourcing` ✅

Done 2026-05-17. Includes:

- Three providers behind a `--provider` flag (apify-apollo default, icypeas, prospeo).
- Apollo input template baked into `references/apify-apollo-defaults.json` (UK Director+ baseline, 33-industry excludes, `roleMatchMode: "all"`).
- `references/icypeas-howto.md` and `references/prospeo-howto.md` for the email-finder paths.
- Output matches the `raw_leads.csv` schema above.

### Phase 4 — Build `build-cold-email-campaign` orchestrator (deferred)

Chains all six. Reads a single high-level prompt ("build a UK Director+ campaign for Luxvance, 2k sendable leads, mid-market manufacturers"), runs each stage in order, prompts Jose at each handoff.

### Phase 5 — Self-improvement on remaining skills (deferred)

Apply the `build-campaign` "learned patterns" auto-edit pattern to `enrich-and-verify-leads` and `launch-instantly-campaign`. (`personalized-copywriting` and `lead-sourcing` already include the `## Learned patterns` template — they just need to start being used.) Each skill learns from its own runs.

---

## Critical lessons (don't relearn the hard way)

Captured here for quick scan. Full context lives in [LEAD_ENRICHMENT_PIPELINE.md](LEAD_ENRICHMENT_PIPELINE.md) and [SESSION_HANDOFF_2026-05-17.md](SESSION_HANDOFF_2026-05-17.md).

1. **Apollo's "deliverable" is 28% real.** Always re-verify via MV. Source: n=3,975 in the 2026-05-17 session.
2. **MV and Instantly APIs block default Python urllib UA.** Set `User-Agent: curl/7.88.1` on every urllib request.
3. **MV rate limit:** ~20 concurrent workers max. Bursts above ~150 req/sec trigger silent throttle (403 for a while).
4. **BounceBan auth:** `Authorization: Bearer <key>` or `?api_key=` query. NOT `X-API-KEY` (401).
5. **60-day freshness rule.** Use `contacts_for_send` VIEW. Never push leads with `email_verified_at` older than 60 days.
6. **Lazy verification.** Never bulk re-verify legacy contacts. ~$275 wasted.
7. **Don't overwrite on MV `error`.** When MV returns HTTP error (not a verdict), skip the row. Don't overwrite the existing email_status.
8. **MCP `instantly__list_leads` is workspace-scoped.** Use raw REST `https://api.instantly.ai/api/v2/leads/list` with POST body for reliable campaign-scoped listing.
9. **Instantly has a global blocklist per workspace.** Unsubscribes from any campaign block future uploads (400 "Lead is in blocklist"). This is intentional — don't bypass.
10. **MCP `execute_sql` result limit:** ~25K tokens. For large pulls, use `string_agg` to compact, or deploy an edge function.
11. **Apollo `roleMatchMode: "all"` is required.** Default `"any"` lets entry-level slip past seniority filter.
12. **Filter country on BOTH company AND person.** Otherwise you get people in the wrong country at right-country companies.
13. **Variable 1 must never echo the lead's own role.** If they are a Sales Director, V1 cannot be "Sales Directors at X".
14. **V2 brand size must match V1 size descriptor.** Mid-market V1 → mid-market brands. Enterprise V1 → enterprise brands.
15. **Stop at DRAFT.** Stage 6 never activates. Jose reviews in the Instantly UI first.

---

## Related files

- **This doc:** `docs/COLD_EMAIL_CAMPAIGN_PIPELINE.md`
- **Verification deep-dive:** `docs/LEAD_ENRICHMENT_PIPELINE.md`
- **System manual:** `docs/SYSTEM_MANUAL.md`
- **Render services:** `docs/RENDER_SERVICES.md`
- **Session handoff (2026-05-17):** `docs/SESSION_HANDOFF_2026-05-17.md`
- **Credentials:** `credentials/master.env` (gitignored, local-only)
- **Supabase project (Agency OS, for stage 1):** `sgaeggmkmipcoikzqwpy`
- **Supabase project (Contact DB, for stage 4):** `nbwbauomozeokflntcwa`

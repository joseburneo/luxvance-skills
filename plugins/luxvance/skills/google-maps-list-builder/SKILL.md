---
name: google-maps-list-builder
description: >
  Scrapes Google Maps for local businesses by category + location, outputs a
  raw_leads.csv ready for icp-prompt-builder qualification and then
  enrich-and-verify-leads. Primary use case at Luxvance: Kcal (food delivery
  targeting gyms, fitness studios, corporate cafeterias, hotels) and any
  future SMB campaign for any client. Triggers on "scrape google maps for
  [category] in [location]", "find local [businesses] in [city]", "build a
  list of [restaurants/gyms/clinics] in [zip]", "consigue locales de [tipo]
  en [ciudad]", "scrapea Google Maps para Kcal".
version: 0.1.0
---

# Google Maps List Builder

Scrapes Google Maps for local businesses. Returns COMPANIES (name, domain, phone, address, ratings, reviews) — does NOT return PEOPLE. Chain with `lead-sourcing` Apollo or a domain-first owner-finder downstream to get decision-makers.

## When to use

- A Luxvance SMB client needs a local list (Kcal is the obvious one — gyms, fitness studios, corporate cafeterias, hotels in Dubai)
- A campaign needs business-context personalization (recent reviews, rating signals, opening hours)
- Apollo's coverage is thin for the vertical (Apollo undercovers true SMBs)

## When NOT to use

- The target list is medium-or-larger B2B (use Apollo via `lead-sourcing`)
- The target list is over 5,000 companies and the scope is national/multi-state (RapidAPI Maps cost scales linearly; for very large pulls evaluate scraping or a different provider)
- The target needs SPECIFIC PEOPLE in the company — Maps returns companies only

## Relationship with sibling skills

| Skill | Relationship |
|---|---|
| `lead-sourcing` | This skill is a 5th provider behind `--provider google-maps`. Its output matches the `raw_leads.csv` schema but with company-only rows (no person columns) — downstream skills chain to find people. |
| `icp-prompt-builder` | **Required next step.** Maps will return 10k pizzerías per state. Filter before enriching. |
| `lead-sourcing` (Apollo or owner-finder) | Runs after this skill to find decision-makers per domain. |
| `enrich-and-verify-leads` | Runs after people are found. |
| `personalized-copywriting` | Can reference Maps-specific signals (recent reviews, rating, hours) in V1/V2 prompts. |

## Inputs

- **Category** (required) — e.g. "gym", "pizza restaurant", "dental clinic", "boutique hotel"
- **Location** (required) — zip code, city, state, country, OR lat/lng coords with radius
- **Max results** (optional, default 500) — Maps will pay-per-call, so cap explicitly

## Outputs

`raw_leads.csv` with company-only columns (filled person columns come from downstream chaining):

| Column | Source | Notes |
|---|---|---|
| `email` | empty | downstream (owner-finder) fills |
| `first_name`, `last_name` | empty | downstream fills |
| `company` | Maps `business_name` | Raw name |
| `job_title` | empty | downstream fills |
| `industry` | Maps `category` | e.g. "Italian restaurant" |
| `website` | Maps `website_url` | domain, no protocol |
| `linkedin_url` | empty | usually thin for SMBs |
| `city`, `country` | Maps `address_components` | |
| **`phone`** | Maps `phone_number` | **NOT pushed to Instantly** (PII), but available for Whatsapp/SMS workflows |
| **`address`** | Maps `address` | full street |
| **`rating`** | Maps `rating` | 1-5 |
| **`review_count`** | Maps `user_ratings_total` | |
| **`recent_review_snippet`** | Maps recent reviews | one-line; optional, costs extra calls |
| **`hours`** | Maps `opening_hours` | structured weekly |
| **`source`** | constant | `google_maps` |

The last 5 columns survive into `personalized-copywriting` for context-rich V1/V2 prompts ("noticed your shop on Sheikh Zayed Road has 247 reviews averaging 4.7 stars").

## How it works

```
Category + Location
        │
        ▼
[Phase 1] Resolve location to lat/lng + radius (if zip/city/state given)
        │
        ▼
[Phase 2] Cost estimate — surface "expecting ~N results, ~$X via RapidAPI"
        │
        ▼
[Phase 3] Paginate through Maps Data API
   ├─ Pull batch (20-100 results per call)
   ├─ Throttle to provider rate limit (bottleneck library, ~10 req/sec)
   └─ Stop at max_results
        │
        ▼
[Phase 4] Enrich (optional, costs extra calls):
   ├─ Recent reviews per business (1-3 most recent review snippets)
   └─ Detailed hours per business
        │
        ▼
[Phase 5] Drop noise:
   ├─ Businesses with no website (cold email needs a domain)
   ├─ Chain franchises (when Jose wants only independents)
   ├─ Businesses with rating below threshold (Kcal usually wants 4.0+)
        │
        ▼
[Phase 6] Output raw_leads.csv + summary
```

## Phase 1: Resolve location

Maps Data API accepts:

- ZIP code (US only) — most precise for US local
- City + State + Country
- Lat/Lng with radius (in km)

For Luxvance use:

- **Dubai/UAE SMBs:** use coordinates + radius. Example: Sheikh Zayed Road area `25.2048,55.2708` + 5km radius.
- **UK SMBs:** use postcode area (e.g. "EC1") + radius.
- **EU SMBs:** city + country.

The skill should handle "Dubai" / "Madrid" / "London" as friendly inputs and resolve internally.

## Phase 2: Cost estimate

RapidAPI Maps Data pricing (verify current rates):

- ~$0.0005 per result
- 500 results = ~$0.25
- 5,000 results = ~$2.50

Cheap. Surface anyway so Jose confirms before triggering.

## Phase 3: Paginate

Maps Data API returns up to 20 results per call. Paginate via offset OR `next_page_token` (provider-specific).

Throttle: 10 req/sec by default. The bottleneck library (already in Luxvance's stack — used by other Render crons) handles this cleanly.

## Phase 4: Optional enrichment

Two enrichments worth running, especially for personalization:

**Recent review snippet** (1 extra call per business): pulls the 3 most recent reviews, picks the most recent non-trivial one (avoid 1-word reviews like "Great!"). Costs roughly 5x the base scrape. Worth it when:

- Personalization needs a specific signal ("I saw the recent review about delivery time")
- Sample size is below ~500 (otherwise cost compounds)

**Detailed hours** (1 extra call per business): pulls the weekly opening hours. Worth it when the campaign targets businesses with specific hours profiles (e.g. "open Sundays" or "24/7").

Default: enrichment OFF. Surface as a question before Phase 3.

## Phase 5: Drop noise

- No website / domain → drop (cold email needs a domain)
- Permanently closed → drop (Maps tags these)
- Chain franchise duplicates → de-dupe by parent brand if Jose wants only independents (e.g. one McDonald's row per region, not per location)
- Rating below threshold → optional drop (Kcal might want only 4.0+ to ensure quality establishments)

Surface drop count and reasons.

## Phase 6: Output

Write `raw_leads.csv` to `profiles/<client-slug>/google-maps/<YYYY-MM-DD>/raw_leads.csv`.

Surface summary:

```
Done.

Category: gym
Location: Dubai, UAE (25.2048,55.2708 + 10km radius)
Results scraped: 847
After noise drop:
  - No website: 312 dropped
  - Permanently closed: 14 dropped
  - Rating below 4.0: 78 dropped
Final: 443 rows

Cost: $0.42

Top 10 by review count:
1. Body Time Fitness Center — 4.8 rating, 1,892 reviews, bodytime.ae
2. ...

Output: profiles/kcal/google-maps/2026-05-18/raw_leads.csv

Next step: icp-prompt-builder on a 50-row sample to filter chain vs independent
(and any other Kcal-specific ICP rules). Then `lead-sourcing --provider blitz`
(once we build that provider) OR Apollo by domain to find the decision-makers
at each business.
```

## Owner-finding downstream

This skill returns COMPANIES. To run cold email, Luxvance needs PEOPLE. Three paths to chain:

**Path 1 — Apollo domain lookup (already supported):**

Feed `raw_leads.csv` to `lead-sourcing --provider apify-apollo` with `companyDomainMatchMode: "strict"` + a list of domains. Apollo finds employees at those specific domains. Cleanest path.

**Path 2 — Icypeas / Prospeo by domain:**

If Apollo coverage is thin, use Icypeas's domain-search endpoint. Already supported in `lead-sourcing`.

**Path 3 — Blitz (future, when we build the provider):**

Blitz specializes in SMB owner-finding (restaurants, clinics, salons, contractors). Best for Kcal's use case. Build when `lead-sourcing` adds the Blitz provider.

## APIs to register

If `RAPIDAPI_KEY` not in `master.env`:

1. Sign up at https://rapidapi.com
2. Subscribe to `maps-data` by `alexanderxbx` (or equivalent — GEX's choice; verify endpoint coverage)
3. Add `RAPIDAPI_KEY=<key>` to `credentials/master.env`

If already registered (e.g. for `competitor-engagers`), reuse the same key.

## Important rules

- **No people data from Maps.** Always chain with an owner-finder downstream.
- **Always run `icp-prompt-builder` after.** "Pizza restaurants in California" returns 10k+ rows; most won't be Kcal-fit (no chains, no franchises, rating threshold).
- **Drop phone column before pushing to Instantly.** PII rule.
- **Rate-limit handling.** Maps Data API will return 429s on burst. The bottleneck library throttles by default.
- **Cost-gate at 5,000+ results.** Below 5k is dirt-cheap; above is worth confirming.

## Failure modes

| Failure | Recovery |
|---|---|
| Maps returns very few results despite broad query | Location resolution failed; double-check lat/lng or expand radius |
| Most results have no website | The vertical is too small / unfit for cold email (try a different category) |
| RapidAPI 429 | Throttle is too aggressive; reduce concurrency to 5 |
| 90%+ chains in the output | Need to filter by review count + name pattern; surface to Jose for review |

## Language

Default to the language of Jose's most recent message for prompts and summary. Maps API queries stay in English (the provider's data is keyed in English).

## Learned patterns

<!-- self-improvement entries get appended here when Jose adopts a new category or filter rule on the fly -->

When the list grows past ~10 entries, promote the durable ones into the main body of this SKILL.md.

## Related files

- `lead-sourcing/SKILL.md` — this skill is a 5th provider; output schema matches
- `icp-prompt-builder/SKILL.md` — required next step
- `enrich-and-verify-leads/SKILL.md` — runs after people are found via downstream chaining

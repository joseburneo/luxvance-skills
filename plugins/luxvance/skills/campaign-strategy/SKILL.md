---
name: campaign-strategy
description: >
  Generates 15-25 forward-looking cold-email campaign ideas for a Luxvance
  client, informed by (1) the locked hypothesis from campaign-intelligence,
  (2) the client's library_data in Supabase, and (3) deep website + case-study
  research. Each idea has targeting level (broad/focused/niche), list filters,
  AI personalization strategy, value proposition (save time / make money /
  save money / mitigate risk), and a campaign overview ready for build-campaign.
  Always includes the 3 proven required campaigns: Creative Ideas, New Hire,
  and Lookalike. Triggers on "generate campaign ideas for [client]",
  "what campaigns should we run for [client]", "campaign strategy",
  "brainstorm campaigns", "ideas de campaña para [cliente]",
  "qué campañas probamos en [cliente]".
version: 0.1.0
---

# Campaign Strategy

Generates **15-25 specific campaign ideas** for a Luxvance client, informed by what already works (from `campaign-intelligence`) and what the market shows (from website + case-study research). Each idea is ready to hand off to `build-campaign` as a single picked direction.

This skill sits between **`campaign-intelligence`** (analyst, locks broad hypothesis) and **`build-campaign`** (production engineer, ships the 10-block kit). It bridges them: takes the broad hypothesis and explodes it into 15-25 specific, executable ideas.

## When to use

- After `campaign-intelligence` has locked a hypothesis, before `build-campaign` builds anything
- When onboarding a new client and there's no historical data yet (skip the intelligence step, use the locked client-request from intake instead)
- When a quarterly review surfaces a need for fresh angles for an existing client
- When the team needs a backlog of campaign ideas to test across the quarter (one per week or biweekly)

## When NOT to use

- For a one-shot campaign that's already locked end-to-end (jump directly to `build-campaign`)
- When Jose has already picked the specific campaign idea (no need to generate 25 options)
- For continuing an experiment iteration (use `experiment-design` instead)

## Relationship with sibling skills

| Skill | Relationship |
|---|---|
| `campaign-intelligence` | Provides the locked hypothesis + client request that frames this skill's output. Read its handoff first. |
| **`campaign-strategy`** (this) | **Generates 15-25 ideas within the hypothesis frame. Jose picks one.** |
| `build-campaign` | Receives the picked idea as input. Produces the 10-block kit. |
| `lead-sourcing` | Each idea's "list filters" map to Apollo / Icypeas / Prospeo / Google Maps / Competitor Engagers inputs downstream. |
| `lead-magnet-brainstorm` | If an idea needs a stronger CTA than "book a call", invoke this skill alongside to pick the magnet. |
| `experiment-design` | For each idea Jose picks to test against the baseline, formalize as an experiment here. |

## Inputs

Required:

- **Client name** (resolves to `library_data` in Supabase + `profiles/<client-slug>/`)
- **Full `campaign-intelligence` output** — not just the one-line locked hypothesis, but the complete analysis: segment performance, angle performance, decline signals, persona insights from the last 60 days of Supabase data. This is what tells you what IS WORKING right now and what stopped working. Without it the ideas are uninformed.

Strongly recommended (the skill is much weaker without these):

- **Recent Fireflies client calls** (last 60-90 days) — captures the client's verbalized direction shifts, market objections they're hearing, offer/product changes, persona pivots. The data tells you what *worked*; Fireflies tells you what the client *wants next*. Access via `mcp__...fireflies_search` + `fireflies_get_summary` / `fireflies_get_transcript`. See "Fireflies client-call analysis" section below.
- **Client website URL** (the skill scrapes it for case studies + value prop signals)
- **Existing `client-profile.yaml`** (per `profiles/<client-slug>/client-profile.yaml`) if it exists from prior runs

Optional:

- **`lead-magnets.md`** from `lead-magnet-brainstorm` — shapes the front-end offer per idea
- **Past campaign scoring history** from `positive-reply-scoring` at `profiles/<client>/scores/*.json` — identifies which angles have already been tested and at what positive_reply_rate

## Outputs

Two files:

1. **`profiles/<client-slug>/campaigns/<campaign-slug>/ideas.md`** — the full 15-25 idea brief (table + per-idea detail)
2. **Conversational pick** — Jose says "use idea #X" and the skill writes a one-line handoff to `build-campaign`

## Core philosophy

Every campaign has two levers:

1. **The list** — who we reach out to (broad → niche)
2. **The message** — what value proposition we lead with

Deeper, more focused lists let messaging reference the filter criteria directly. Broad lists need AI personalization to feel relevant.

**Value proposition categories.** Every B2B offer ladders to one of:

- **Save time** (efficiency, automation, fewer steps)
- **Make money** (more revenue, more deals, growth)
- **Save money** (lower cost, better ROI, consolidation)
- **Mitigate risk** (compliance, security, avoid mistakes)

Rotate these across campaigns. If the client's last winner was a "make money" angle, test a "save time" or "save money" angle next.

**Targeting levels.** Pick a mix:

- **Broad** — widest audience within the locked hypothesis. Needs strong AI personalization.
- **Focused** — one extra filter on top of broad (e.g., new hires, recent fundraise, specific tech installed).
- **Niche** — multiple filters stacked. Small but highly relevant list (50-500 prospects).

## Flow

### Phase 1: Load context

Pull in parallel from ALL of these sources. Skip any that aren't available and surface what's missing so Jose can decide whether to proceed with partial input.

1. **Full `campaign-intelligence` output** (NOT just the locked hypothesis):
   - The 4 analysis blocks from the last 60 days (segment performance, angle performance, decline signals, persona insights)
   - The locked hypothesis + client-request statement
   - Source: the most recent `campaign-intelligence` conversation OR `profiles/<client>/campaigns/<slug>/intelligence.md` if persisted
   - If campaign-intelligence has NOT been run for this client in the last 14 days, prompt Jose to run it first. Stale intelligence = ideas based on outdated patterns.

2. **`clients.library_data` jsonb** from Supabase project `sgaeggmkmipcoikzqwpy` (Offers, Personas, Segments, Use Cases, Credibility Assets, Brand Guardrails). Access via **`mcp__e722c133-ad03-40d9-bcc4-684a7fd1ebe0__execute_sql`** with that `project_id`. This is the static client knowledge — what they sell, who they sell to, what they will not say.

3. **Recent Fireflies client calls** (last 60-90 days) — see "Fireflies client-call analysis" section below for the detailed extraction protocol.

4. **Past campaign scoring history** from `positive-reply-scoring` at `profiles/<client>/scores/*.json`. Identifies which campaigns have already been tested and their `positive_reply_rate`. Lets you AVOID proposing ideas that have already lost.

5. **Client website** (scrape homepage + about + customers/case-studies + features + pricing).

6. **Existing `client-profile.yaml`** if any.

### Phase 2: Website + case-study deep research

Following GEX's proven protocol:

1. **Homepage** — extract core value prop, primary target audience mentioned
2. **Navigation** — find Customers, Case Studies, Features, Pricing, About, Blog pages
3. **Case study deep dive** — for EVERY customer case study:
   - Company name + industry + size
   - Specific metrics / results achieved
   - The problem they solved
   - Their quote / testimonial if any
4. **Pattern identification** — what industries appear most? What sizes? What roles bought? What common pains?
5. **ICP challenge** — does the case study pattern align with the locked hypothesis? If the locked hypothesis says "UK SaaS 50-200 emp" but case studies are mostly Manufacturing 500+, surface the divergence. Either Jose corrects the hypothesis or accepts a Lookalike-driven targeting.

### Phase 2.5: Fireflies client-call analysis (CRITICAL)

This is one of the highest-leverage inputs. The data tells you what *worked historically*; Fireflies tells you what the client *wants next*. Without this, ideas miss recent pivots in the client's direction.

**Definition of "client calls":** recurring internal sessions between Luxvance and the paying client (weekly check-ins, strategy reviews, kickoff calls, mid-campaign retros). NOT discovery calls with prospects (those are out of scope; the `book-discovery-call` skill manages them separately).

**Step 1: Search**

```
mcp__7e300d4c-0d67-4cba-b6c6-de59cf01be2d__fireflies_search
  query: "<client_name>"
  date_range: last 90 days
```

Surface a list of matching meetings (title + date + duration).

**Step 2: Filter**

Keep meetings that look like internal client check-ins. Titles usually contain: `weekly`, `sync`, `review`, `kickoff`, `strategy`, `check-in`, `<client> ↔ Luxvance`, `<client> + Luxvance`.

Drop:
- Discovery calls with prospects of the client (those have prospect names in title, not client name)
- Internal-only Luxvance calls (no client representative present)
- Demos, sales calls, onboarding-prospect calls

If unsure, surface the title list to Jose and ask which to include. Default: include the 3-5 most recent that match the filter.

**Step 3: Extract per call**

For each retained meeting, fetch summary via `fireflies_get_summary` (faster than full transcript). For high-signal calls, follow up with `fireflies_get_transcript` for verbatim quotes.

Extract:

| Signal type | What to capture | How it feeds the ideas |
|---|---|---|
| **New direction signals** | "We want to start targeting [X]", "Let's shift away from [Y]", "Can we try [Z]" | High weight on the next round of ideas — the client is explicitly asking |
| **Pain points the client emphasizes** | "Our customers keep complaining about [X]", "We're losing deals because of [Y]" | Becomes the angle for a value-prop-led campaign |
| **Objections from the client's own market** | "Prospects keep saying [X] when we pitch [Y]" | The campaign copy must address this objection upfront |
| **Win signals** | "We just closed [X], they were a great fit because [Y]" | The win profile becomes a Lookalike anchor |
| **Offer / product changes** | "We launched [X] last month", "Pricing changed", "New service tier" | New ideas built around the new offer |
| **Persona shifts** | "We want to start going up-market", "Mid-market is dead for us" | Adjusts the locked hypothesis if the data agrees; flag tension if not |

**Step 4: Cross-reference with `campaign-intelligence`**

Both signals matter, but they can conflict:

| Fireflies says | Data says | Action |
|---|---|---|
| "Let's target enterprise" | Mid-market has the best positive_reply_rate | Surface the tension. Propose BOTH a "enterprise pilot" niche idea AND continuing the mid-market winner. Let Jose decide. |
| "Stop running the Aviva-lookalike, it's tired" | Lookalike still at 1.8% positive_reply_rate | Trust the client — they hear what the data can't measure (e.g. brand reputation issues with the angle). Drop the Lookalike from this round of ideas. |
| Silent on a topic | Data shows a clear pattern | Run with the data — Fireflies didn't contradict. |
| Says X is critical | No data on X yet | Propose X as a new experiment with explicit "no baseline yet" caveat. |

**Step 5: Quote in the brief (when relevant)**

In the campaign overview for any idea informed by a Fireflies call, quote the specific moment:

```
Campaign 7 — "Compliance-led for new UK SaaS hires"

Per the 2026-05-12 weekly call with [CapQuest CEO name], they want to
test a compliance-led angle on new finance hires at UK SaaS companies
("we've been winning these deals lately, but our cold outbound hasn't
caught up to that signal"). This idea operationalizes that signal.
```

**Never invent a Fireflies quote.** If the call did not include the relevant signal, do not pretend it did. If the search returns no calls at all, surface that clearly:

```
Fireflies search returned 0 client calls for [client] in the last 90 days.
Proceeding without client-direction input. The ideas will be data-driven
only. Recommend scheduling a strategy review call before launching to
align direction.
```

### Phase 3: Generate 15-25 ideas

For each idea, produce:

```
| Campaign Name | Targeting | List Filters | AI Strategy | Value Prop | Campaign Overview |
```

**Each idea draws from up to FOUR signal sources** (more = stronger idea):

1. **Campaign-intelligence patterns** — the segment/angle/persona insights from the 60-day analysis
2. **Fireflies client direction** — what the client explicitly asked for in recent calls
3. **Case-study patterns** — what types of companies bought the client's service historically
4. **Triggers from the market** — funding events, hiring signals, regulation changes, product launches

The strongest ideas hit 3-4 signals at once. The weakest hit only 1. Aim for at least 60% of the 15-25 ideas to draw from 2+ signals.

**Required 3 ideas (always include):**

1. **Creative Ideas Campaign**
   - Targeting: Broad (within hypothesis)
   - AI Strategy: Analyze each prospect's website → generate 3 specific use cases for the client's offer
   - Value Prop: any (varies by industry)
   - Why it works: shows research, provides immediate value, demonstrates capability

2. **New Hire Campaign**
   - Targeting: Focused (people who started role in last 90 days)
   - AI Strategy: Pull start date, previous company, detect what they inherited
   - Value Prop: usually "save time" (new leaders want quick wins)
   - Why it works: new hires actively seek tools, open to outreach

3. **Lookalike Campaign**
   - Targeting: Niche (companies similar to client's best case studies)
   - AI Strategy: Reference the specific case study: "we helped [X] who's similar to you..."
   - Value Prop: usually "make money" (mirror the case study's outcome)
   - Why it works: if it worked for similar, it should work for them

**Creative stretch ideas (8-15 more):**

Push beyond obvious. Techniques:

- **Quantify the pain** — count team members in a role, estimate time waste, name-drop employees
- **Detect unusual job titles** that signal perfect fit
- **Combine multiple signals** — "New VP Sales + hiring SDRs + uses Salesforce + posted about scaling outbound"
- **Tenure-based messaging** — years in business or role tenure changes the angle
- **Recent triggers** — fundraise, hiring, news, product launch
- **Industry-specific signals** — Google reviews for SMBs, web traffic decline for SaaS, hiring posts for ops
- **Inverted signals** (only when reliably detectable) — "has VP Sales but NO GTM Engineer"
- **No-AI campaigns** (at least 1) — short, tight targeting, strong static value prop. No personalization. Often outperforms AI-heavy at scale.

### Phase 4: Required No-AI campaign (always include)

At least one campaign that uses **zero AI personalization**. Short, snappy, relies on tight targeting + a strong static value prop.

Format:
- Campaign name
- Why it works without AI (the targeting is so tight that personalization is unnecessary)
- Core message structure (subject + body skeleton, no per-lead variables)

### Phase 5: Front-end offer suggestions

If the client's core CTA is "book a call" and the locked hypothesis is in a higher-friction segment (enterprise, regulated industries, sceptical buyers), suggest 1-3 softer front-end offers that convert cold traffic before the main pitch:

- Free audit / assessment (uses `lead-magnet-brainstorm` archetype A)
- Industry report / benchmark data (archetype B)
- Template / playbook (archetype D)
- Specific-to-them analysis (archetype G)

Reference `lead-magnet-brainstorm` for the full archetype set.

### Phase 6: Output the brief

Save to `profiles/<client-slug>/campaigns/<campaign-slug>/ideas.md`. Surface to Jose with the table first, then per-idea detail below.

### Phase 7: Pick one and hand off

Wait for Jose's pick ("idea #7" or "the lookalike one"). Then write:

```
## Picked: <idea name>

**Targeting:** <broad/focused/niche>
**List filters:** <from the row>
**AI strategy:** <from the row>
**Value prop:** <from the row>
**Campaign overview:** <from the row>

## Handoff

Ready to invoke `build-campaign`. The build skill receives this picked idea
as its locked direction and produces the 10-block kit.
```

After this output, the skill is done. Jose invokes `build-campaign` (or the orchestrator handles it).

## Luxvance-specific seed patterns per existing client

Pre-loaded starting hypotheses for the 6 active clients. These are NOT final ideas — they're priors that should be refined by Phase 2 research.

| Client | Likely required + 2 stretch ideas |
|---|---|
| **CapQuest** | Required: Lookalike (PE-backed mid-market UK), New Hire (newly-in-role CFO/Head of Finance), Creative Ideas. Stretch: "Recent fundraise + equity dilution math", "Operators who just IPO'd". |
| **Connect Resources** | Required + UAE compliance audit angle, hiring-velocity-detected (companies posting many ops roles in UAE). |
| **Kcal** | Required + Google Maps SMB targeting (gyms, fitness studios, corporate cafeterias in Dubai), "Recent corporate hire >100 employees" trigger. |
| **GFV** | Required + Wholesale food buyers, "Recent menu changes" trigger via web scrape. |
| **Remly** | Required + Property managers with units listed >60 days, "Owner of multiple properties" via title detection. |
| **Luxvance** (own) | Required + B2B services agencies, "Companies hiring SDRs but no outbound infra" (combined signal). |

These priors should be in `references/client-seed-ideas.md` (to be populated as Jose runs the skill per client).

## Data sources the AI strategies can use

From most lead-sourcing outputs:

- LinkedIn profile + activity (recent posts, engagement, tenure)
- Company website content (homepage, product pages, blog)
- Job postings + hiring patterns
- Tech stack (BuiltWith, Wappalyzer)
- Funding + fundraise signals
- News mentions, press releases
- Podcast appearances, speaking engagements
- Industry association memberships
- For local SMBs: Google reviews, business hours, ratings

**Data sources to AVOID:**

- G2 / Capterra / Trustpilot reviews (platforms block scraping)
- Private revenue figures, internal metrics
- Free-tier or existing-user data (that's nurture/PLG, not cold outbound — flag if suggested)

## Quality checklist (before saving the brief)

- [ ] **Campaign-intelligence ran in the last 14 days** (if not, run it first — stale intelligence = bad ideas)
- [ ] **Fireflies client-call search completed** (last 90 days) — even if zero results, surface that
- [ ] At least 15-20 ideas (more if they're strong)
- [ ] At least 60% of ideas draw from 2+ signal sources (intel + Fireflies + case studies + market triggers)
- [ ] Ordered from broadest to most niche
- [ ] **Creative Ideas campaign included** (required)
- [ ] **New Hire campaign included** (required)
- [ ] **Lookalike campaign included** (required, with specific case-study reference)
- [ ] At least 2-3 creative stretch ideas (not obvious ones)
- [ ] At least 1 No-AI campaign (static, tight targeting)
- [ ] Each AI strategy uses publicly-available data only
- [ ] Each value prop tied to: save time / make money / save money / mitigate risk
- [ ] Front-end offer suggestions included (if relevant)
- [ ] At least one "Golden ICP" idea (what a rep would send after 10 min of manual research)
- [ ] Case-study analysis completed (if the locked hypothesis can be challenged by the pattern, surface it)
- [ ] Fireflies-vs-data tensions surfaced (don't silently override either)
- [ ] When quoting Fireflies, the exact meeting date + speaker is named

## Output format

Section-by-section detail:

```markdown
## Campaign Strategy for <Client Name>

**Locked hypothesis:** <one sentence from campaign-intelligence>
**Locked client request:** <one paragraph from campaign-intelligence>
**Target persona summary:** <from library_data + research>

---

### Customer Discovery Analysis

**Case Studies Reviewed:**
| Company | Industry | Size | Key Metric | Problem Solved |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

**Patterns Identified:**
- Industries: <list>
- Sizes: <range>
- Roles: <titles>
- Common pains: <list>

**Targeting recommendation:** <if research suggests broader/different ICP than locked hypothesis, note it>

**Best Lookalike anchors:** <3-5 case-study companies that anchor the Lookalike campaign>

---

### Campaign Ideas (15-25)

| # | Campaign Name | Targeting | List Filters | AI Strategy | Value Prop | Overview |
|---|---|---|---|---|---|---|
| 1 | Creative Ideas (required) | Broad | - | Per-prospect use case from website | varies | ... |
| 2 | New Hire (required) | Focused | Started <90d | Pull start date + prior co | save time | ... |
| 3 | Lookalike (required) | Niche | Companies like [case study X, Y, Z] | Reference case study | make money | ... |
| 4-25 | ... | ... | ... | ... | ... | ... |

### No-AI Campaign

**<Name>**
- Why it works: <one sentence>
- Core message: <subject + body skeleton>

### Front-end Offer Suggestions

1. <Offer name>: <description, why it fits>
2. ...
```

## Important rules

- **Never invent case-study customers** that aren't on the client's actual website. If the scrape returns no case studies, surface that and skip the Lookalike anchor (use industry archetypes instead).
- **Never invent Fireflies quotes.** If the call did not contain the signal, do not pretend it did. If the search returned zero calls, surface that and proceed without that input.
- **Never silently override Fireflies vs data.** When they conflict, surface the tension and let Jose decide. The most expensive mistake is "the data said target A, the client wanted B, we built for A, the client cancelled."
- **Never recommend AI strategies that need private data** (revenue, internal metrics, gated reviews). Stick to publicly-scrapable.
- **Never recommend campaigns that need a free trial when the client doesn't sell SaaS.** Match the offer mechanic to the client's actual delivery capacity.
- **Always include the required 3** (Creative Ideas, New Hire, Lookalike). They are proven.
- **Always include ≥1 No-AI campaign.** AI personalization is not always a win; static + tight targeting often outperforms.
- **Always tie value props to the 4 categories** (save time / make money / save money / mitigate risk). Vague value props ("better outcomes") are not actionable.
- **Always rotate value props across the 15-25 ideas.** If 20 of 25 are "make money" angles, the brief is unbalanced.
- **Always cross-reference Fireflies with `campaign-intelligence`** before finalizing. Both feed the ideas; neither overrides the other silently.

## Language

Default to the language of Jose's most recent message for the brief. Campaign names + AI strategy descriptions stay in English (these get used by `build-campaign` and `lead-sourcing` downstream which operate in English data).

## Learned patterns

<!-- self-improvement entries get appended here when Jose adopts a new idea archetype or AI strategy on the fly -->

When the list grows past ~10 entries, promote the durable ones into the main body of this SKILL.md.

## Related files + external sources

- `campaign-intelligence/SKILL.md` — produces the full 60-day analysis + locked hypothesis this skill explodes into ideas
- `build-campaign/SKILL.md` — receives the picked idea
- `lead-magnet-brainstorm/SKILL.md` — provides front-end offer archetypes referenced in Phase 5
- `lead-sourcing/SKILL.md` — executes the list filters per idea
- `experiment-design/SKILL.md` — formalizes each idea as an experiment when testing against baseline
- `references/client-seed-ideas.md` — per-client priors (populated as Jose runs the skill)
- **Fireflies (external):** accessed via `mcp__7e300d4c-0d67-4cba-b6c6-de59cf01be2d__fireflies_search`, `fireflies_get_summary`, `fireflies_get_transcript`. The client-call source of truth for what the client wants next.
- **Supabase `sgaeggmkmipcoikzqwpy` (Agency OS):** `clients.library_data`, `campaigns`, `lead_replies`, `campaign_daily_snapshots` — the historical pattern source of truth.

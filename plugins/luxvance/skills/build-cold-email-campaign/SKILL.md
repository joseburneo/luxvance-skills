---
name: build-cold-email-campaign
description: >
  End-to-end orchestrator for shipping a Luxvance cold-email campaign. Chains the
  6 pipeline skills in order: campaign-intelligence → build-campaign → lead-sourcing
  → enrich-and-verify-leads → list-quality-scorecard → personalized-copywriting →
  launch-instantly-campaign. Pauses at each handoff for Jose's review, saves
  experiment state per campaign, and ends with a DRAFT in Instantly ready for
  Jose to activate. Triggers on "build a campaign for [client]", "ship a campaign",
  "run the full pipeline", "orchestrate a campaign", "construye una campana para
  [cliente]", "lanza una campana completa", "corre el pipeline para [cliente]".
version: 0.1.0
---

# Build Cold Email Campaign (Orchestrator)

The single entry point for shipping a Luxvance campaign end-to-end. Wraps the 6 pipeline skills + the new optimize-side skills into one guided flow.

This is the Luxvance equivalent of GEX's `auto-research-public`, adapted to the Luxvance 6-skill pipeline and Instantly stack.

## When to use

- A new campaign hypothesis is locked and Jose wants to ship the full flow without remembering which skill to invoke when
- Onboarding Marko or Ana — they invoke this skill instead of memorizing the 6 individual skills
- A repeat campaign for an existing client where the V1/V2 prompt is already tuned (orchestrator detects the saved prompt and skips re-tuning)

## When NOT to use

- For an experiment ARM where one specific stage is being modified (e.g. just testing a new list against an existing copy). In that case, invoke the specific skill directly.
- For ongoing optimization work (Wednesday reply sweep, Monday audit). Use `cold-email-weekly-rhythm` directly.

## Inputs

- **Client name** (required) — one of the 6 active Luxvance clients OR a new client
- **Locked hypothesis** (optional but recommended) — from a prior `campaign-intelligence` run. If absent, the orchestrator invokes `campaign-intelligence` first.
- **Campaign name** (optional) — defaults to the Luxvance naming convention from `build-campaign`

## Outputs

When the orchestrator completes, Jose has:

1. A locked hypothesis + client-request statement (from `campaign-intelligence`)
2. A 10-block kit (from `build-campaign`)
3. A `raw_leads.csv` (from `lead-sourcing`)
4. A `verified.csv` with deliverable-only leads (from `enrich-and-verify-leads`)
5. A list quality scorecard (from `list-quality-scorecard`)
6. An `enriched_leads.csv` with V1/V2 + normalized company names (from `personalized-copywriting`)
7. A DRAFT campaign in Instantly (from `launch-instantly-campaign`)
8. A populated experiment YAML at `profiles/<client-slug>/experiments/<YYYY-MM-DD>-<campaign-slug>.yaml`

Total wall-clock: 60-90 minutes (vs 3-5 hours invoking skills one by one).

## The 9 phases

```
Phase 1: Resolve client + load saved state
Phase 2: campaign-intelligence  → locked hypothesis + client request
        (skipped if already provided, or if client has no prior data)
Phase 3: campaign-strategy      → 15-25 specific ideas; Jose picks one
        (skipped if Jose passes a specific one-line direction directly)
Phase 4: build-campaign         → 10-block kit + sequence config
        ▼ spam-word-checker auto-triggers
Phase 5: lead-sourcing          → raw_leads.csv
Phase 6: enrich-and-verify-leads → verified.csv
Phase 7: list-quality-scorecard → grade A/B/C/D/F + action items
        ▼ if C or below, loop back to Phase 5 or 6 with fixes
Phase 8: personalized-copywriting → enriched_leads.csv
        (uses saved prompt if present)
Phase 9: launch-instantly-campaign → DRAFT in Instantly
        ▼ save experiment YAML
```

Each phase pauses at its handoff. Jose reviews and confirms before the next phase runs.

## Relationship with sibling skills

| Skill | Role in this orchestrator |
|---|---|
| `campaign-intelligence` | Phase 2 — produces the locked hypothesis (skipped if already provided) |
| `campaign-strategy` | Phase 3 — generates 15-25 ideas, Jose picks one (skipped if Jose has a specific direction) |
| `build-campaign` | Phase 4 — produces the 10-block kit + variants.yaml |
| `spam-word-checker` | Auto-trigger inside Phase 4 + Phase 8 |
| `lead-sourcing` | Phase 5 — produces raw_leads.csv |
| `enrich-and-verify-leads` | Phase 6 — produces verified.csv |
| `list-quality-scorecard` | Phase 7 — gates the upload |
| `personalized-copywriting` | Phase 8 — produces enriched_leads.csv |
| `launch-instantly-campaign` | Phase 9 — produces DRAFT in Instantly |
| `experiment-design` | This orchestrator writes the experiment YAML at the end. Used when this campaign is an experiment arm. |
| `cold-email-weekly-rhythm` | This orchestrator hands off to weekly-rhythm after Phase 8 (the next Monday audit will pick up the new campaign). |

## Phase 1: Resolve client + load saved state

1. Confirm the client (from the user's invocation OR by asking).
2. Resolve the `client-slug` (lowercase, dashes — e.g. "Global Food Ventures" → `gfv`).
3. Check `profiles/<client-slug>/`:
   - If exists, list what is in it: `client-profile.yaml`, prior `experiments/*.yaml`, `personalization-prompt.txt`, prior `audits/*.md`, prior `scores/*.json`.
   - If does not exist, create the directory.
4. Surface to Jose: "Found prior state for [client]: N campaigns, last shipped <date>, tuned personalization prompt from <date>. Continue?"

## Phase 2: campaign-intelligence

Skip this phase if the user already passed a locked hypothesis.

Otherwise:

1. Invoke `campaign-intelligence` for the client.
2. The skill iterates with Jose until the hypothesis is locked.
3. Save the hypothesis text to `profiles/<client-slug>/campaigns/<campaign-slug>/hypothesis.md`.

Surface the locked hypothesis at the end of this phase. Confirm with Jose before moving to Phase 3.

## Phase 3: campaign-strategy

Skip this phase if Jose passed a specific one-line direction (no need to generate 25 options when he already picked).

Otherwise:

1. Invoke `campaign-strategy` with the locked hypothesis from Phase 2 as input.
2. The skill scrapes the client's website, analyzes case studies, generates 15-25 specific ideas (Creative Ideas + New Hire + Lookalike always included, plus creative stretch + at least 1 No-AI).
3. Surface the ideas table to Jose.
4. Wait for Jose's pick ("idea #7" or "the lookalike one").
5. Save the picked idea to `profiles/<client-slug>/campaigns/<campaign-slug>/picked-idea.md`.
6. Save the full ideas brief to `profiles/<client-slug>/campaigns/<campaign-slug>/ideas.md`.

Confirm the picked idea before Phase 4.

## Phase 4: build-campaign

1. Invoke `build-campaign` with the picked idea (from Phase 3) as input.
2. The skill runs its Phase 1-9 flow (silent gathering → calibration questions → bifurcation → render → blocks 1-9 → sequence config → block 10 → self-improvement).
3. `spam-word-checker` auto-triggers on block 3 + block 9.
4. Save the 10-block kit to `profiles/<client-slug>/campaigns/<campaign-slug>/kit.md` and the `variants.yaml` to `profiles/<client-slug>/campaigns/<campaign-slug>/variants.yaml`.

Surface blocks 1-9 to Jose. Confirm before Phase 5.

## Phase 5: lead-sourcing

1. Read the locked hypothesis to derive the ICP filter spec (industries, seniorities, geography, headcount).
2. Pick the provider:
   - **Apify Apollo** (default) — for net-new ICP scrapes.
   - **Icypeas / Prospeo** — if Jose provided a curated list of LinkedIn URLs or name+company pairs.
3. Surface the Apollo input JSON (built from the defaults in `lead-sourcing/references/apify-apollo-defaults.json`, overridden per hypothesis).
4. Confirm cost estimate ($1/1k leads) before triggering.
5. Run the scrape.
6. Save `raw_leads.csv` to `profiles/<client-slug>/campaigns/<campaign-slug>/raw_leads.csv`.

Surface count + top-3 country/seniority breakdown. Confirm before Phase 6.

## Phase 6: enrich-and-verify-leads

1. Pass `raw_leads.csv` to `enrich-and-verify-leads`.
2. The skill runs the MV → BB waterfall, applies the 60-day freshness rule, and upserts to the master Supabase contacts table.
3. Output: `verified.csv` with only `is_sendable=true` rows.
4. Save to `profiles/<client-slug>/campaigns/<campaign-slug>/verified.csv`.

Surface verification stats (MV verdicts, BB recovery, final yield). Confirm before Phase 7.

## Phase 7: list-quality-scorecard

1. Pass `verified.csv` to `list-quality-scorecard`.
2. The skill grades the list across 8 dimensions (verification, dup email, dup domain, title relevance, bad-title detection, catch-all density, ICP fit, name quality).
3. Surface the letter grade + top 5 fixes.

**Gate logic:**

- Grade **A or B** → proceed to Phase 8.
- Grade **C** → apply the top 3 fixes (deduplicate, drop catch-all, filter bad titles), re-grade, then proceed.
- Grade **D or F** → loop back to Phase 5 with tighter filters. Do NOT proceed.

Save the scorecard to `profiles/<client-slug>/campaigns/<campaign-slug>/scorecard.md`.

## Phase 8: personalized-copywriting

1. Pass `verified.csv` + V1/V2 prompts (from `build-campaign` blocks 6 + 7) to `personalized-copywriting`.
2. **Check for saved prompt:** if `profiles/<client-slug>/personalization-prompt.txt` exists, ask Jose:
   - Use saved prompt (default) → skip Phase 4 of `personalized-copywriting`, go directly to full-batch generation
   - Re-tune from scratch → run the full 10-10-10 QA loop, save the new prompt at the end
3. Run the full-batch generation + QA pass.
4. Output: `enriched_leads.csv` matching `launch-instantly-campaign/references/leads-csv-schema.md`.
5. Save to `profiles/<client-slug>/campaigns/<campaign-slug>/enriched_leads.csv`.

Surface drop count + top 3 fix reasons. Confirm before Phase 9.

## Phase 9: launch-instantly-campaign

1. Pass `variants.yaml` (from Phase 4) + `enriched_leads.csv` (from Phase 8) to `launch-instantly-campaign`.
2. The skill creates the campaign in Instantly via MCP, attaches inboxes by tag, uploads leads, sets schedule.
3. Stops at DRAFT.
4. Save the Instantly campaign ID + URL to the experiment YAML.

Surface the campaign URL. Confirm:

> Campaign is in DRAFT. Review in Instantly UI: <url>
>
> When ready, attach sending inboxes (tag: active) and hit Start. Once active, the campaign will be tracked by `cold-email-weekly-rhythm` automatically — Monday audit + Wednesday reply sweep.

## Save experiment YAML (final step)

Write `profiles/<client-slug>/experiments/<YYYY-MM-DD>-<campaign-slug>.yaml`:

```yaml
experiment:
  name: <campaign-slug>
  client: <client>
  hypothesis: <text from Phase 2>
  type: combined  # by default for a new campaign; promote to list-only or copy-only if Jose was running a specific test
  variable: <what we are betting on this campaign>
  constants:
    - rest of the parameters

success_criteria:
  positive_reply_rate_target: <float — default 1.5x prior best for this client>
  baseline: <prior best for this client>
  minimum_sends_per_arm: <count from Phase 7>
  measurement_date: <launch date + 21 days>

arms:
  variant:
    instantly_campaign_id: <from Phase 8>
    description: <campaign-slug + brief>

results:
  control_positive_reply_rate: null
  variant_positive_reply_rate: null
  winner: null
  confidence: null
  decision: null

artifacts:
  hypothesis: profiles/<client-slug>/campaigns/<campaign-slug>/hypothesis.md
  kit: profiles/<client-slug>/campaigns/<campaign-slug>/kit.md
  raw_leads: profiles/<client-slug>/campaigns/<campaign-slug>/raw_leads.csv
  verified: profiles/<client-slug>/campaigns/<campaign-slug>/verified.csv
  scorecard: profiles/<client-slug>/campaigns/<campaign-slug>/scorecard.md
  enriched_leads: profiles/<client-slug>/campaigns/<campaign-slug>/enriched_leads.csv
  variants: profiles/<client-slug>/campaigns/<campaign-slug>/variants.yaml
```

This YAML becomes the source of truth for `cold-email-weekly-rhythm` Friday retrospective (at day 21) and the quarterly review.

## Important rules

- **Pause at every handoff.** Never auto-confirm. Jose's review is the safety mechanism.
- **Save artifacts after every phase.** If the session crashes, Jose can resume from the last completed phase by reading the saved files.
- **Single client per invocation.** Do not try to batch across clients.
- **Block at scorecard C-grade or below.** Phase 6 gates Phase 7. Bad lists do not pass through.
- **Stop at DRAFT.** The orchestrator never activates the campaign in Instantly. Jose hits Start manually.
- **Detect saved personalization prompt.** Phase 7 should detect and offer reuse without prompting Jose to navigate to the file.

## Cost estimate (per campaign)

For a typical Luxvance campaign at 2,500 sendable leads (15% yield from a ~17k raw scrape):

| Phase | Tool | Cost |
|---|---|---|
| 2 | campaign-intelligence (Sonnet) | $0 (Max plan) |
| 3 | build-campaign (Sonnet) | $0 (Max plan) |
| 4 | lead-sourcing (Apify Apollo, ~17k leads) | ~$17 |
| 5 | enrich-and-verify-leads (MV + BB) | ~$27 |
| 6 | list-quality-scorecard | $0 |
| 7 | personalized-copywriting (Sonnet subagents) | $0 (Max plan, ~5-10% weekly quota) |
| 8 | launch-instantly-campaign (MCP) | $0 |
| **Total** | | **~$44 per campaign** |

vs Clay's ~$300/month per client. Break-even at ~7 campaigns per month per client, but the real win is the velocity gain (60-90 min vs 3-5 hours).

## Failure modes and recovery

| Failure | Recovery |
|---|---|
| campaign-intelligence cannot find prior data for the client | Ask Jose for a one-line hypothesis manually, skip Phase 2 |
| Apollo returns under 5,000 leads | Widen filters (looser industry, broader country) and re-run Phase 4 |
| Verification yield is under 5% | List is too cold or too pattern-match-heavy. Re-source with stricter Apollo filters. |
| Scorecard grade D or F | Loop back to Phase 4 or 5. Do NOT push C-grade lists. |
| Personalization QA loop never converges | The hypothesis is too vague. Loop back to Phase 2 to refine. |
| Instantly upload fails (workspace tag missing, inbox count zero) | Surface the error, manually fix in Instantly UI, retry Phase 8 |

## Language

Default to the language of Jose's most recent message for orchestrator-level prompts and summaries. The phase skills handle their own language defaults inside.

## Learned patterns

<!-- self-improvement entries get appended here when Jose adopts a new orchestration step or override on the fly -->

When the list grows past ~10 entries, promote the durable ones into the main body of this SKILL.md.

## Related files

- `docs/COLD_EMAIL_CAMPAIGN_PIPELINE.md` — the pipeline doc this skill orchestrates
- All 6 pipeline skills + the 7 optimize-side skills referenced above

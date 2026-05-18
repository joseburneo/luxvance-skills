---
name: cold-email-weekly-rhythm
description: >
  Operational playbook for running Luxvance's cold email continuously. Prescribes
  what runs on Monday / Wednesday / Friday / biweekly / monthly / quarterly across
  all active client campaigns. Pure schedule — no automation. The difference between
  shipping campaigns and compounding an agency is consistency. Jose's calendar is
  the system. Triggers on "weekly rhythm", "what should I be doing this week",
  "ops cadence", "what is on the cold email calendar", "ritmo semanal",
  "que toca hoy", "operativa semanal de cold email".
version: 0.1.0
---

# Cold Email Weekly Rhythm

Having 14 skills doesn't help if Luxvance does not run them on a schedule. This is the schedule.

This is a pure playbook. No scripts, no automatic reminders. Jose puts the rhythm on his own calendar (Step 1 below) and runs the prescribed skill at the prescribed time. That is the entire system.

## Why this exists

The 2026-05-17 session shipped two campaigns into Instantly and then left them running with no formal review cadence. Without this skill, every Luxvance campaign sits in Instantly accumulating data nobody analyzes. Replies pile up unscored. Bounces creep up unnoticed. Domains burn one week at a time.

This skill is the schedule that turns Luxvance from "ship campaigns" into "compounding agency": every Monday catches infrastructure problems, every Wednesday catches positive replies before they go cold, every Friday closes the loop on what worked.

## Efficiency note (CLI vs MCP)

This skill's cadence runs across **all 6 client workspaces** every Monday and Wednesday. That's 6 × ~50 inboxes × multiple metrics = a fleet operation. The skills it invokes (`deliverability-audit`, `positive-reply-scoring`) should default to the **Instantly CLI** (`bcharleson/instantly-cli` via `npx`) for these fleet-wide pulls, not MCP. See [`docs/INSTANTLY_CLI_QUICKREF.md`](../../../docs/INSTANTLY_CLI_QUICKREF.md) for the per-workspace key wrapping pattern.

MCP stays useful for the ad-hoc "Jose pokes one inbox" moments during triage, not for the scheduled rhythm itself.

## When to use

- Once per Luxvance client, the first time Jose runs cold email for them
- Whenever Jose says "what should I be doing this week" or "what's on the cold email calendar"
- When onboarding Marko or Ana — this is the doc they get pointed at

## When NOT to use

- For a one-off campaign that ships and stops — the rhythm assumes continuous operation
- During the first 7 days of a campaign's life — too early for any of the cadence checks to produce signal

## Relationship with sibling skills

This skill orchestrates ALL the optimize-side Luxvance skills:

| Skill | When this skill calls it |
|---|---|
| `deliverability-audit` | Monday (every week) + 1st of each month |
| `positive-reply-scoring` | Wednesday (every week) + Friday for campaigns at day 21 |
| `experiment-design` | Friday (after retrospectives) + first Monday of each quarter |
| `deliverability-incident-response` | Whenever Monday audit flags an issue |
| `list-quality-scorecard` | Before each new campaign launch (not a calendar event, a precondition) |
| `spam-word-checker` | Auto-trigger inside copywriting (no calendar event) |
| `campaign-intelligence` | Quarterly review (first Monday of each quarter) |

## Step 1 (required before using this skill): put the rhythm on Jose's calendar

Open Google Calendar / Outlook / Apple Reminders / whatever Jose actually looks at every day. Create these as recurring events. Copy the titles and cadences exactly.

| Event title | Cadence | Duration | Owner |
|---|---|---|---|
| Luxvance: Monday deliverability audit | Every Monday, 09:00 GST | 15 min | Jose |
| Luxvance: Wednesday positive-reply sweep | Every Wednesday, 10:00 GST | 30-60 min | Jose |
| Luxvance: Friday campaign retrospectives | Every Friday, 15:00 GST | 20 min per campaign at day 21 | Jose |
| Luxvance: Inbox rotation | Every other Monday, 11:00 GST | 30 min | Jose / Marko |
| Luxvance: Monthly spam placement test | 1st of each month, 10:00 GST | 25 min active | Jose |
| Luxvance: Quarterly experiment review | First Monday of each quarter, 13:00 GST | 90 min | Jose |

**Do not skip Step 1.** The difference between an agency that ships and one that compounds is consistency. This skill has no built-in reminder — intentionally — because if it did and it broke, Luxvance's ops would silently fail. The calendar is the accountability system.

## Monday — Deliverability audit (15 min)

**Run:** `deliverability-audit --days=7` across all active Luxvance campaigns and inboxes.

**Review:**

- Fleet positive_reply_rate over last 7 days — must be ≥1% (the 1% rule)
- Flagged campaigns (`flag_low_reply = TRUE`)
- Flagged inboxes (`flag_high_bounce = TRUE`)
- Any inbox with reputation "bad" or warmup "blocked"
- DNS authentication issues (missing DKIM, SPF, DMARC)

**Action:**

- If any campaign failed the 1% rule, run `deliverability-incident-response` → triage decision tree
- If bounce rate spiked above 2%, pause the offending campaign immediately, then triage
- If a domain is missing DKIM/SPF/DMARC, fix at the registrar / Zapmail
- If everything clean, log the check in a weekly journal entry and close the tab

**Where to log:** `profiles/luxvance/journal/<YYYY-MM-DD>.md` with one line per active campaign.

## Wednesday — Positive-reply sweep (30-60 min depending on volume)

**Run:** `positive-reply-scoring` on every active Luxvance campaign that has accumulated ≥200 sends in the last 7 days.

**Review:**

- Every `positive_interested` and `positive_soft` reply — leads wanting to engage
- Every `positive_referral` reply — high-value handoff opportunities
- Every `negative_hostile` reply — investigate why

**Action:**

- **Respond to every `positive_interested` reply within 30 seconds of seeing it.** Do not batch these. A reply that feels like it took minutes converts 3x better than one that took hours.
- **For referrals:** reach out to the referred person within 24h, name the referrer in the opener.
- **For hostile:** apologize, remove from all lists, investigate why they were flagged for hostility (often signals bad targeting from `lead-sourcing`).

**Time management:** if Jose has more than 50 positive replies per week, this is the scale where a dedicated closer/AE makes sense. Hand off Wednesday morning so they can work the queue Wednesday afternoon.

## Friday — Campaign retrospectives (20 min per campaign at day 21)

**Identify campaigns hitting their 21-day mark this week.** 21 days is the minimum for positive_reply_rate to stabilize.

For each campaign at day 21:

1. Run `positive-reply-scoring --campaign-id=<id>`.
2. Compare to the client's baseline (or to the experiment's control arm if this is an experiment).
3. Decide:
   - **Winner (positive_reply_rate ≥ 2x baseline):** keep running. Consider scaling — clone to more inboxes via `launch-instantly-campaign`.
   - **Middling (near baseline):** plan the next iteration via `experiment-design`. Monday next week.
   - **Loser (under 50% of baseline):** kill it. Document why in the experiment log.

4. Log the result in `profiles/<client-slug>/experiments/<campaign-yyyy-mm-dd>.yaml`:
   - `positive_reply_rate`, overall reply rate, bounce rate
   - Decision (keep / iterate / kill) + reasoning
   - Hypothesis for next iteration (if iterating)

**Critical:** do not skip the log. The quarterly review reads from these files. Without history, no learning across campaigns.

## Every other Monday — Inbox rotation (30 min)

**Run:** pull inbox health from Instantly (per workspace — one query per client workspace).

For each client workspace (Luxvance, CapQuest, Kcal, Connect Resources, GFV, Remly):

```
mcp__instantly-<client>__accounts_list with status filters
```

**Review the output:**

- Any inboxes with reputation "bad" or warmup status flagged?
- Any inboxes with sending paused due to bounce or block events?
- Any inboxes with <5 sends/day despite being in active campaigns?

**Action:**

1. Identify inboxes failing the 1% rule (sent ≥200 in last 30 days, positive_reply_rate <1%) — flag for retirement.
2. Identify warmed-but-idle inboxes (currently insurance pool) that can rotate into active campaigns.
3. Promote insurance → active via Instantly UI (tagging) or MCP.
4. Retire failing inboxes: tag as "retired", disable warmup, remove from active campaigns.

**If insurance pool is getting thin (fewer than 5 inboxes available to rotate in for any client):** plan a new domain purchase cycle. Takes 2 weeks from purchase to sendable. Start early.

## 1st of the month — Spam placement test (25 min active)

**Run:** spam placement test via Instantly's seed-inbox feature OR via a third-party tool like GlockApps if Instantly's coverage is thin for the campaign's TAM.

For the highest-volume active campaign per client:

- Trigger test with ~100 senders
- Wait for completion (5-20 min)
- Pull placement breakdown (Inbox vs Promotions vs Spam) per provider (Gmail, Outlook, Yahoo)

**Review:**

- Overall inbox placement % — target ≥85%
- Spam filter triggers — which filters fired, which senders affected
- Per-provider breakdown — Gmail vs Outlook performance

**Action:**

- ≥90% inbox placement: great. Keep doing what is working.
- 80-90%: yellow. Look at the spam-filter detail. Start fixing the highest-frequency trigger next week.
- Below 80%: red. Pause the campaign, run `deliverability-incident-response`, fix before sending more.

## First Monday of each quarter — Experiment review (90 min)

Read all `experiments/*.yaml` from the last quarter across all clients. Identify patterns:

- Which campaigns had the highest positive_reply_rate?
- Which list sources produced the best leads (Apollo vs Icypeas vs Prospeo, by client)?
- Which copy angles resonated (Problem Sniffing / Billboard / AI Generic, by segment)?
- Which ICP archetypes converted best?

**Output:** a 1-page quarterly retrospective saved to `profiles/<client-slug>/retrospectives/<YYYY>-Q<N>.md`:

- Top 3 campaigns + what made them work (with positive_reply_rate numbers)
- Bottom 3 campaigns + what to avoid in next quarter
- 3-5 hypotheses for next quarter's experiments
- Any ICP adjustment for `library_data` in Supabase

Use the retrospective as input to design next quarter's experiments via `experiment-design`.

If a pattern is durable (same insight from 3+ campaigns), promote it into the relevant skill's `## Learned patterns` section so the next campaign for that client picks it up automatically.

## What to skip

Jose does NOT need to:

- Check Instantly every day. Wednesday sweep catches everything important.
- Obsess over daily reply-rate fluctuations. Wait for 7-day averages.
- Read every positive reply in real time. Set up notifications if immediacy matters, but the Wednesday sweep is the system.

Daily pokes at the cold-email stack are a procrastination pattern, not a performance pattern. Trust the schedule.

## Per-client variants

Some Luxvance clients need a tighter cadence:

- **CapQuest:** Wednesday sweep is daily for this client (they pay for the closer's time). Friday retrospective runs per campaign as it hits day 21.
- **GFV / Kcal (food / B2C-adjacent):** monthly spam placement test moves to biweekly. These verticals have noisier deliverability.
- **CAMB.AI:** quarterly review folds into the SOW deliverable. Surface to the client.

These exceptions live in `references/client-cadence-overrides.md`.

## What this skill produces

- A populated weekly journal at `profiles/luxvance/journal/<YYYY-MM-DD>.md` (Monday entries)
- Updated experiment YAMLs at `profiles/<client-slug>/experiments/*.yaml` (Friday entries)
- Quarterly retrospectives at `profiles/<client-slug>/retrospectives/<YYYY>-Q<N>.md`

## Important rules

- **Calendar is the accountability system.** This skill has no built-in cron. Jose owns the events.
- **Day-21 minimum before retrospective.** Earlier readings overweight the first email and miss positive_soft / positive_referral that arrive in week 3.
- **Same cutoff date when comparing two campaigns** (e.g. experiment arms).
- **Never skip the journal log on Monday.** The quarterly review depends on it.
- **Never call a campaign winner from <500 sends per arm.** Noise.

## What to do next

This skill IS the loop. The next action is the next calendar event.

**If Luxvance has not yet run any campaign:** skip this skill entirely. Come back after the first campaign hits the 7-day mark.

**If onboarding a new client:** set up the calendar events under that client's name (or shared calendar) before launching their first campaign.

## Language

Default to the language of Jose's most recent message for the report and prompts. Field names, skill names, and file paths stay in English.

## Learned patterns

<!-- self-improvement entries get appended here when Jose adopts a new cadence rule or override on the fly -->

When the list grows past ~10 entries, promote the durable ones into the main body of this SKILL.md.

## References

- `references/client-cadence-overrides.md` — per-client deviations from the default rhythm
- `docs/COLD_EMAIL_CAMPAIGN_PIPELINE.md` — overall pipeline doc
- `positive-reply-scoring/SKILL.md` — the metric the rhythm tracks
- `experiment-design/SKILL.md` — the framework the retrospective feeds
- `deliverability-audit/SKILL.md` — the Monday + monthly task
- `deliverability-incident-response/SKILL.md` — invoked when the audit flags issues

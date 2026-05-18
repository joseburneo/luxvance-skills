---
name: positive-reply-scoring
description: >
  Pulls replies from a Luxvance campaign (Instantly + Supabase lead_replies),
  classifies each into one of 11 labels (positive_interested, positive_soft,
  positive_referral, neutral_question, negative_notnow, negative_notfit,
  negative_hostile, unsubscribe, ooo, bounce, other), and reports the
  positive_reply_rate = positives / total_sent — the north-star metric for
  cold email. Triggers on "score the replies of [campaign]", "how is [campaign]
  doing", "positive reply rate", "is this campaign working", "puntua las
  replies de [campana]", "como va la campana de [cliente]", "tasa de respuesta
  positiva". Runs as the Wednesday task in cold-email-weekly-rhythm.
version: 0.1.0
---

# Positive Reply Scoring

**Reply rate tells you if people are paying attention. Positive reply rate tells you if they want what Luxvance is selling.** This skill computes the second.

## Why this exists

A Luxvance campaign can get 4% reply rate and still be a disaster. If 90% of those replies are "unsubscribe" and "not a fit", we are burning client inboxes for nothing — and the client's domain reputation pays the price.

The metric that matters:

```
positive_reply_rate = positive_replies / total_sent
```

Side-by-side example:

- Campaign A: 1% reply rate, 70% positive → 0.7% positive_reply_rate
- Campaign B: 5% reply rate, 10% positive → 0.5% positive_reply_rate
- **Campaign A wins.** Scale Campaign A, not Campaign B.

This is the only metric Luxvance uses to decide keep / iterate / kill on a campaign.

## When to use

- After a campaign has run 14+ days (otherwise sample is too small to trust)
- Weekly as the Wednesday task in `cold-email-weekly-rhythm`
- Before deciding to scale or kill a campaign
- When comparing two campaigns in an `experiment-design` (use the same cutoff date for both)
- When `campaign-intelligence` is locking a hypothesis and needs to see what worked recently

## When NOT to use

- Campaigns under 200 sends — positive_reply_rate is dominated by noise.
- Real-time reply triage — for that, log into Instantly directly. This skill is the weekly aggregate.

## Relationship with sibling skills

| Skill | Relationship |
|---|---|
| `campaign-intelligence` | Reads the per-campaign positive_reply_rate this skill produces. Uses it to lock the next hypothesis. |
| `experiment-design` | Uses positive_reply_rate as the success metric in every experiment arm. |
| `cold-email-weekly-rhythm` | Wednesday task. The weekly rhythm orchestrates when this skill runs. |
| `deliverability-incident-response` | If `negative_hostile` or `unsubscribe` rate spikes, that triggers a deliverability investigation. |
| `deliverability-audit` | Cross-checks: if positive_reply_rate is below the 1% baseline, run audit to rule out infrastructure. |

## Classification schema

Every reply is classified into exactly one bucket:

| Label | Meaning | Counts as positive? |
|---|---|---|
| `positive_interested` | "Yes, tell me more" or booked a meeting | ✅ |
| `positive_soft` | "Send more info" / "reach out in Q3" / specific info request | ✅ |
| `positive_referral` | "Not me, but talk to X" — referrals are high-value | ✅ |
| `neutral_question` | Clarifying question, no commitment yet | ❌ (optional half-credit) |
| `negative_notnow` | "Not right now, maybe later" | ❌ |
| `negative_notfit` | "Not a fit" / "we don't need this" | ❌ |
| `negative_hostile` | Angry, complaint, legal threat, spam report | ❌ (and tracked separately as a risk signal) |
| `unsubscribe` | Explicit opt-out | ❌ |
| `ooo` | Out-of-office auto-reply | ❌ (excluded from denominators) |
| `bounce` | Technical bounce | ❌ (excluded from denominators) |
| `other` | Can't tell with confidence ≥0.7 | ❌ |

```
positive_reply_rate = (positive_interested + positive_soft + positive_referral) / total_sent
```

## Data sources

Two sources, in order of preference:

### Source A: Luxvance Supabase `lead_replies` table (preferred)

Project: `sgaeggmkmipcoikzqwpy` (Agency OS). Tool: **`mcp__e722c133-ad03-40d9-bcc4-684a7fd1ebe0__execute_sql`** with `project_id: "sgaeggmkmipcoikzqwpy"`.

Schema: `campaign_id (FK)`, `client_id (FK)`, `campaign_name`, `reply_category` (currently free-form Luxvance text, NOT the 11-label schema above — this skill RE-classifies), `email`, `first_name`, `last_name`, `job_title`, `company_name`, `company_size`, `country`, `inbound_email`, `outbound_email`, `reply_date`.

The Render cron that ingests Instantly replies into this table runs daily. So all replies up to yesterday are available without hitting the Instantly API at all. This is the most token-efficient path: one SQL query returns everything.

### Source B: Instantly API direct (fallback)

When the Supabase ingest is stale or the campaign is new and not yet synced.

- **Small pull (under 200 replies):** MCP `mcp__instantly-<client>__email_list` with `campaign_id` filter. Single conversational call.
- **Large pull (200+ replies, or all replies across all campaigns of a workspace for the Wed sweep):** **CLI** `npx instantly-cli email list --campaign-id <id>` wrapped with the per-client `INSTANTLY_API_KEY`. The CLI returns JSON in one stream; MCP would chunk it into many tool calls. See [`docs/INSTANTLY_CLI_QUICKREF.md`](../../docs/INSTANTLY_CLI_QUICKREF.md).

Default for the Wednesday sweep across all active campaigns: CLI, looped across workspaces.

## Inputs

- Campaign identifier — Instantly campaign ID OR Luxvance campaign name OR "the latest CapQuest campaign"
- Optional: client identifier (if ambiguous)
- Optional: date range (defaults to "since campaign launched")

## Flow

### Phase 1: Resolve the campaign

1. If the user gave a campaign ID, use it.
2. If the user gave a campaign name, query `campaigns` table in Supabase `sgaeggmkmipcoikzqwpy` to resolve to ID.
3. If the user gave a client name only, list the last 3 campaigns for that client and ask which one.
4. Resolve the `instantly_campaign_id` from the `campaigns` row.

### Phase 2: Fetch the replies

Try Source A (Supabase `lead_replies`):

```sql
SELECT id, email, first_name, last_name, job_title, company_name,
       inbound_email, reply_date, sequence_step
FROM lead_replies
WHERE campaign_id = '<resolved campaign_id>'
  AND (reply_date >= <start_date> OR <start_date> IS NULL)
ORDER BY reply_date ASC;
```

If Source A is empty or stale (latest `reply_date` is more than 24h behind today and the campaign is active), fall back to Source B.

Source B: Instantly API direct via MCP. Pull all leads for the campaign with `has_reply = true`, then fetch each reply.

### Phase 3: Fetch total_sent

```sql
SELECT emails_sent
FROM campaigns
WHERE id = '<resolved campaign_id>';
```

If the campaign is in flight and `emails_sent` is stale, fall back to Instantly's `campaigns_get` MCP for the live count.

### Phase 4: Classify each reply

For each reply, classify into one of the 11 labels using this prompt (applied via the conversation, not via subagent — keeps the QA loop tight and inspectable):

```
Classify the reply below as one of:
- positive_interested, positive_soft, positive_referral
- neutral_question
- negative_notnow, negative_notfit, negative_hostile
- unsubscribe, ooo, bounce, other

Output: { "label": "...", "confidence": 0.0-1.0, "reason": "one line" }

Rules:
- OOO auto-replies ("out of office", "off until X") → ooo
- Bounce notifications (delivery failure, mailer-daemon, postmaster) → bounce
- "Unsubscribe", "remove me", "take me off your list", "STOP" → unsubscribe
- "Not interested", "not a fit", "we don't need this" → negative_notfit
- "Not right now", "circle back Q3", "ask me later" → negative_notnow
- "Try [other person]", "[name] handles this" → positive_referral
- "Tell me more", "send info", "what is it" (without commitment) → positive_soft
- "Yes book a call", "what times work", calendar links → positive_interested
- Insults, legal threats, spam complaints → negative_hostile
- If confidence below 0.7 → other

Reply body:
<reply text>
```

For larger campaigns (more than ~100 replies), fan out via `Agent` subagents (`subagent_type: general-purpose`), batches of 30 replies per agent, parallel.

### Phase 5: Aggregate

```
Campaign: <name> (id <id>)
Date range: <start> to <end>
Client: <client name>

Total sent:                <N>
Total replies:             <N> (<%>)
  ooo/bounce (excluded):   <N>
  Net replies:             <N>

Breakdown:
  positive_interested:    <N>
  positive_soft:          <N>
  positive_referral:      <N>
  neutral_question:       <N>
  negative_notnow:        <N>
  negative_notfit:        <N>
  negative_hostile:       <N>
  unsubscribe:            <N>
  other:                  <N>

Positive reply rate:     <%> (<N> positives / <N> sent)
Positive % of replies:   <%> (<N> positives / <N> net replies)
Negative hostile risk:    <%> (<N> hostile / <N> sent)
Unsub rate:              <%> (<N> unsubscribes / <N> sent)
```

### Phase 6: Benchmark

Luxvance benchmarks (per the agency's historical performance):

| Tier | Positive reply rate | Hostile rate | Unsub rate |
|---|---|---|---|
| Excellent | ≥2% | <0.2% | <1% |
| Good | ≥1% | <0.3% | <2% |
| Average | ≥0.5% | <0.5% | <3% |
| Risk | <0.5% | ≥0.5% | ≥3% |

Risk thresholds trigger a `deliverability-incident-response` recommendation in the report.

### Phase 7: Save to history

Append the result to Supabase `campaign_daily_snapshots` (if a row for today does not exist), OR write a flat file:

```
profiles/<client-slug>/scores/<campaign-id>-<YYYY-MM-DD>.json
```

JSON schema:

```json
{
  "campaign_id": "...",
  "campaign_name": "...",
  "client": "...",
  "date_range": { "start": "...", "end": "..." },
  "total_sent": 5284,
  "total_replies": 212,
  "net_replies": 178,
  "breakdown": {
    "positive_interested": 22,
    "positive_soft": 31,
    "positive_referral": 8,
    "neutral_question": 14,
    "negative_notnow": 28,
    "negative_notfit": 52,
    "negative_hostile": 3,
    "unsubscribe": 20,
    "ooo": 22,
    "bounce": 12,
    "other": 0
  },
  "positive_reply_rate": 0.0115,
  "hostile_rate": 0.00057,
  "unsub_rate": 0.00378,
  "tier": "good",
  "scored_at": "2026-05-18T10:00:00Z"
}
```

### Phase 8: Surface action items

At the end, list:

- **Top positive replies that need a human response** — the top 10 `positive_interested` leads with their reply body. Jose should respond within 30 seconds of seeing this.
- **Referrals to follow up** — every `positive_referral`. Add the referred contact to a new outreach list (with the referrer mentioned).
- **Hostile flags** — every `negative_hostile`. Read manually. Consider pausing the offending inbox.
- **Unsubscribes** — confirm they are globally suppressed in Instantly. The MCP `mcp__instantly-<client>__leads_list` with `unsubscribe = true` filter shows the suppression list.

## Important rules

- **Classify only the FIRST reply per lead.** If a lead replied, Jose replied, they replied again — only the first reply is the signal. Later messages are the conversation, not the scoring.
- **Exclude OOO + bounce from denominators.** They are not real replies. The aggregation does this automatically.
- **Wait 14+ days minimum.** Cold-email replies trickle in for weeks. Scoring at day 7 underweights positive_soft / positive_referral (those take time).
- **Under 500 sends, the positive_reply_rate is noisy.** Report it but flag the small sample.
- **Never overwrite Luxvance's existing `reply_category` field** in Supabase. That column is the team's own tagging. This skill writes to `campaign_daily_snapshots` or a flat file, not back into `lead_replies`.
- **For experiments, use the SAME cutoff date for both arms.** Otherwise the comparison is biased.

## Common failure modes

- **Replies were classified before the user finished the conversation.** Some leads send "yes" first and then "actually no" two days later. The first-reply-only rule is on purpose: it tells you whether the OPENING earned interest. The conversation outcome is a separate metric.
- **Auto-responder loops counted as bounces.** Some shared inboxes auto-respond to every cold email with a templated "we received your message". Tag these as `other`, not `negative_notfit` — they are non-signal.
- **Forwarded replies from an executive assistant.** Often signal `positive_referral` even when the language sounds dismissive. Read the full chain before tagging.

## What to do next

**If positive_reply_rate is below 1% after 200+ sends:** the 1% rule failed. Run `deliverability-audit` (are emails reaching inboxes?), then re-read the copy for vague CTAs, generic openers, em-dashes, banned words (re-run `spam-word-checker`).

**If positive_reply_rate is between 1% and 2%:** middling. Plan the next iteration via `experiment-design`. Test ONE variable.

**If positive_reply_rate is at or above 2%:** scale. Clone the campaign to more inboxes via `launch-instantly-campaign`. Document the learning in the experiment log.

**If hostile rate is above 0.3% OR unsub rate is above 2%:** deliverability risk. Pause the campaign. Run `deliverability-incident-response`.

## Language

Default to the language of Jose's most recent message for the report. Classification labels stay in English (they are stable enum values used by `experiment-design` and `campaign-intelligence`).

## Learned patterns

<!-- self-improvement entries get appended here when Jose adopts a new label or threshold on the fly -->

When the list grows past ~10 entries, promote the durable ones into the main body of this SKILL.md.

## Related files

- `docs/COLD_EMAIL_CAMPAIGN_PIPELINE.md` — overall pipeline doc
- `campaign-intelligence/SKILL.md` — the analyst skill that consumes the scores produced here
- `experiment-design/SKILL.md` — the experiment framework that uses positive_reply_rate as success metric

---
name: deliverability-audit
description: >
  Diagnostic audit for Luxvance's cold email infrastructure. Checks domain
  authentication (SPF / DKIM / DMARC) via dig, inbox health and reputation from
  Instantly per-workspace, bounce rate by inbox and domain, and per-campaign
  reply rate against the 1% rule. Optionally compares reply/bounce by inbox
  type (G Suite / Office365 / SMTP). Outputs a markdown report with action
  items. Use when reply rates drop, when bounces spike, when onboarding a new
  client workspace, or as the Monday + monthly task in cold-email-weekly-rhythm.
  Triggers on "audit deliverability", "check the inboxes", "is everything
  healthy", "domain auth check", "SPF DKIM DMARC", "1% rule check",
  "audita los inboxes", "revisa la deliverability", "como estan los dominios".
version: 0.1.0
---

# Deliverability Audit

If Luxvance's positive_reply_rate is dropping and Jose does not know why, start here. Most of the time the problem is deliverability — emails are not reaching inboxes. This skill tells you what is broken.

## When to use

- Reply rate dropped by more than 30% week-over-week → run the full audit
- Bounces spiked above 2% → run authentication + spam-placement checks
- Before scaling a campaign — make sure infrastructure is ready
- Monday morning as part of `cold-email-weekly-rhythm` (15 min check)
- 1st of each month — full audit with spam placement test (25 min)
- When taking over a client's Instantly workspace Luxvance did not set up

## When NOT to use

- Replies just trickled in for one day and Jose is being impatient — wait for 7-day averages
- A single inbox bounced one email — not an incident
- During the first 48h of a brand-new domain — too early for any signal

## Relationship with sibling skills

| Skill | Relationship |
|---|---|
| `cold-email-weekly-rhythm` | This skill is the Monday task and the 1st-of-month task. |
| `deliverability-incident-response` | When this skill flags an issue, that skill provides the triage decision tree. |
| `positive-reply-scoring` | This skill cross-checks with positive_reply_rate — if positive is low AND deliverability is bad, fix deliverability first. |
| `lead-sourcing` | If bounce rate is high (>3%) on a fresh campaign, the LIST may be the problem (Apollo pattern-match emails). |
| `enrich-and-verify-leads` | Audit cross-references — if bounce is high and the verifier ran recently, the verifier's freshness rule (60 days) may have been violated. |
| `launch-instantly-campaign` | Audit-flagged inboxes get removed from future campaign uploads. |

## What it checks

| Layer | What | How (efficient default) |
|---|---|---|
| DNS auth | SPF, DKIM, DMARC present on each sending domain | `dig` commands (local, read-only) |
| Inbox health | Warmup status, reputation, blocked accounts, connection failures | **CLI** `npx instantly-cli accounts list --json` per workspace (fleet read, bulk) |
| Volume health | Daily sent trending, capacity utilization | **CLI** `npx instantly-cli analytics daily-account --start <date>` (bulk read) |
| Send + reply rate per inbox | Sent count, reply count, reply rate over lookback period | **CLI** `npx instantly-cli analytics campaign-overview` + `analytics daily-account` |
| Bounce rate | Per-inbox and per-domain bounce rate over last 30 days | **CLI** `analytics campaign --id <id>` per campaign, batched |
| Spam placement (monthly only) | Real inbox-vs-spam test | **CLI** `npx instantly-cli inbox-placement create/get` (single ops, but CLI more scriptable than MCP for the cron) |
| Inbox type comparison | Reply / bounce per type (G Suite / Office365 / SMTP) | Aggregate the CLI output in shell + jq |

**Tool choice rationale.** This audit runs across **6 workspaces × 50-100 inboxes each = 300-600 inboxes**. Doing this via MCP = 300-600 tool calls = massive token cost. Doing it via CLI = 6 bash calls (one per workspace) that stream small JSON. **The CLI is the right default for this skill.** See [`docs/INSTANTLY_CLI_QUICKREF.md`](../../docs/INSTANTLY_CLI_QUICKREF.md) for the per-workspace key wrapping pattern.

When Jose asks an ad-hoc one-off question ("is sales@trygrowth.co blocked?"), use MCP. When the Monday audit fires across the whole fleet, use CLI.

## The 1% rule — core domain-health threshold

**A healthy Luxvance domain should have an overall reply rate of at least 1% after 200 emails sent.**

Below 1% after 200+ sends is a red flag — something is broken. The audit explicitly checks this and flags any domain or inbox that:

- Has sent ≥200 emails in the lookback window
- Has an overall reply rate <1%

Possible causes (the audit's root-cause suggestions try to pinpoint which):

1. **Emails landing in spam** — run the spam placement test (monthly).
2. **Domain reputation damaged** — check DMARC reports, reconsider domain age.
3. **Copy is broken** — manually review for vague CTAs, generic openers, em-dashes; re-run `spam-word-checker`.
4. **List is cold or wrong ICP** — check bounce rate; if >3%, the list is the problem (escalate to `list-quality-scorecard`).
5. **Inbox has not warmed enough** — check warmup status, give it more time.

Below 200 sends: too early to judge. The rule needs sample size.

## Inputs

- Instantly API access (per-workspace MCP). All 6 client workspaces are configured (Luxvance, CapQuest, Kcal, Connect Resources, GFV, Remly).
- Optional scope flags:
  - Client (which workspace to audit; defaults to ALL active workspaces)
  - Campaign ID (audit only one campaign's inboxes)
  - Domain (audit only one sending domain)
  - Inbox tag (e.g. `active`, `insurance`)

## Flow

### Step 1: Pull the inbox inventory (per workspace)

For each Luxvance client workspace:

```
mcp__instantly-<client>__accounts_list with limit=100
```

Output per inbox: `id, email, domain, warmup_status, reputation, max_warmup/day, sent_today, smtp_ok, imap_ok, is_blocked, tags`.

### Step 2: Check domain authentication

For each unique sending domain across the fleet, run:

```bash
dig TXT <domain> +short                         # SPF
dig TXT default._domainkey.<domain> +short      # DKIM (Zapmail uses "default")
dig TXT _dmarc.<domain> +short                  # DMARC
```

Record per domain:

- `spf_present` (true/false)
- `spf_strict` (uses `-all` or `~all`, not `+all`)
- `dkim_present` (true/false)
- `dmarc_present` (true/false)
- `dmarc_policy` (none / quarantine / reject)

### Step 3: Pull sent + reply + bounce metrics

For each active campaign per workspace, pull per-inbox analytics for the last 30 days via:

```
mcp__instantly-<client>__analytics_daily_account
mcp__instantly-<client>__analytics_campaign
```

Compute per inbox:

- `sent` (30-day count)
- `replies` (30-day count)
- `bounces` (30-day count)
- `reply_rate_pct = replies / sent * 100`
- `bounce_rate_pct = bounces / sent * 100`
- `flag_low_reply = TRUE if sent ≥200 AND reply_rate_pct < 1.0`
- `flag_high_bounce = TRUE if sent ≥50 AND bounce_rate_pct > 3.0`

### Step 4 (monthly only): Spam placement test

Run on the highest-volume active campaign per client.

Options:

- **Instantly seed inboxes** — built-in feature. Send to ~100 seed mailboxes, wait 5-20 min, pull placement breakdown.
- **GlockApps** (recommended for accuracy) — external service. Provides Inbox / Promotions / Spam breakdown per provider (Gmail / Outlook / Yahoo).

Record per campaign:

- Overall inbox placement percent
- Per-provider breakdown (Gmail, Outlook, Yahoo, Apple Mail)
- Spam filter triggers that fired (DKIM_INVALID, HTML_MESSAGE, LINK_REDIRECT, etc.)

### Step 5: Inbox type comparison

Group inboxes by `provider_code` (G Suite, Office365, SMTP via Zapmail / other). Aggregate `sent, replies, bounces, reply_rate, bounce_rate` per group.

Report:

```
Type          Inboxes   Sent      Replies   Bounces   Reply%    Bounce%
G Suite           12     3,120        42        12     1.35%      0.38%
Office365         24     6,440        65        28     1.01%      0.43%
SMTP              44    10,780        55        98     0.51%      0.91%
TOTAL             80    20,340       162       138     0.80%      0.68%
```

Surface anomalies: if SMTP reply rate is half of G Suite, investigate SMTP domains.

### Step 6: Synthesize the markdown report

```
# Deliverability Audit — <client> — <date>

## Summary

- N inboxes audited across M domains
- X inboxes blocked (Y%)
- Z domains missing DKIM
- W domains with DMARC policy=none (no enforcement)
- Fleet performance (last 30d):
    Sent:           N
    Replies:        N
    Reply rate:     X.X% (PASS — above 1% threshold) OR (FAIL)
    Bounces:        N
    Bounce rate:    X.X% (PASS — below 2%) OR (FAIL)
- N inboxes failed the 1% rule
- Spam placement (test run): X% inbox / Y% spam / Z% promo

## Critical issues (fix within 24h)

1. ...
2. ...

## Warnings (fix within 1 week)

- ...

## Action items (prioritized)

1. [HIGH] ...
2. [HIGH] ...
3. [MED] ...
4. [LOW] ...
```

### Step 7: Act on the action items

Feed action items into the right skill:

- Missing DKIM / SPF → manual fix at the registrar OR `deliverability-incident-response` for the playbook
- Blocked inboxes → pause + retire in Instantly UI (manual today)
- Campaign schedule issues → Instantly campaign schedule settings
- Bad copy flagged → re-run `spam-word-checker` on the campaign's body

## Interpreting the numbers

### Bounce rates

- **<1%** — Excellent. Healthy list.
- **1-2%** — Normal for cold. No action.
- **2-3%** — Yellow. Check list quality (`list-quality-scorecard`); emails may be stale.
- **>3%** — Red. Verify the list (`enrich-and-verify-leads`), consider pausing the campaign.
- **>5%** — Stop immediately. Domain reputation is being damaged.

### Spam placement

- **>90% inbox** — Great. Ship more.
- **80-90% inbox** — Acceptable.
- **70-80% inbox** — Yellow. Look at spam-filter detail to see what is triggering.
- **<70% inbox** — Red. Pause and fix auth + copy before sending more.

### DMARC policies

- **None** — Acceptable for first 2 weeks of a domain's life. After that, tighten.
- **Quarantine** — Recommended long-term. Emails failing auth land in spam.
- **Reject** — Strictest. Only use after 30+ days of clean `rua=` reports confirming all legitimate mail passes.

### Warmup reputation (Instantly scale)

- **Good** — inbox is healthy. Send normally.
- **Fair** — warming or coming back from a small issue. Keep warming, do not push volume.
- **Bad** — warmup peers are not seeing emails in their inboxes. Investigate or retire.

## Common root causes

- **SPF too lax** — `v=spf1 +all` whitelists everyone. Use `v=spf1 include:zapmail.com ~all` or whatever the provider documents.
- **DKIM missing** — new domain, selector not published. Zapmail publishes at `default._domainkey` by default.
- **DMARC alignment failure** — From-domain doesn't match SPF/DKIM domain. Usually a misconfigured reply-to or a third-party sender added to the chain.
- **Too many inboxes per domain** — Gmail flags domains with >3-5 inboxes as suspicious. Keep it at 2/domain.
- **Aggressive warmup ramp** — Jumping from 5 to 40/day in one week triggers warmup-network flags. Ramp over 2-4 weeks.
- **Shared sending IP with spam traffic** — Zapmail and similar providers use shared pools. If someone else on the IP spammed, Luxvance suffers. Wait for pool rotation (1-2 weeks).
- **Pattern-match Apollo emails** — Apollo's "verified" tag is only 28% reliable. If the list has many Apollo-only emails, bounce rate spikes. Fix at `enrich-and-verify-leads`.

## Important rules

- **`dig` is read-only.** No DNS changes from this skill — that is manual at the registrar.
- **Never auto-retire an inbox.** Flag it in the report; Jose decides whether to retire.
- **Per-workspace audits.** Each Luxvance client workspace is queried independently. Do not mix metrics across clients.
- **The 1% rule kicks in at 200 sends, not earlier.** Smaller samples are noise.
- **Spam placement test is monthly, not weekly.** It is expensive (seed credits, time) and the result does not change week-over-week unless something major happened.

## Output paths

```
profiles/<client-slug>/audits/<YYYY-MM-DD>-audit.md
profiles/<client-slug>/audits/<YYYY-MM-DD>-inboxes.csv
profiles/<client-slug>/audits/<YYYY-MM-DD>-domains.csv
profiles/<client-slug>/audits/<YYYY-MM-DD>-spam-test.json  (monthly only)
```

For the Monday cadence, save the report and notify Jose if any HIGH-priority action items fired.

## What to do next

**If any flag fired:** `deliverability-incident-response` → triage decision tree for whatever was flagged (low reply rate, high bounce, blocked inbox, etc).

**If all clean:** next Monday, run this again. This audit is the Monday task in `cold-email-weekly-rhythm`.

**If fixes were just applied:** wait 7 days before re-auditing. Reputation propagates slowly.

## Language

Default to the language of Jose's most recent message for the report. Technical field names (SPF, DKIM, DMARC, reputation buckets) stay in English.

## Learned patterns

<!-- self-improvement entries get appended here when Jose adopts a new threshold or check on the fly -->

When the list grows past ~10 entries, promote the durable ones into the main body of this SKILL.md.

## References

- `references/dns-records.md` — SPF / DKIM / DMARC record templates + interpretation guide
- `references/spam-filter-triggers.md` — common spam-filter trigger codes and fixes
- `references/instantly-api-endpoints.md` — Instantly MCP endpoints used in each step

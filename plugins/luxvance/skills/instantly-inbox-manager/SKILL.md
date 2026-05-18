---
name: instantly-inbox-manager
description: >
  Conversational interface for managing Luxvance Instantly inboxes across all
  client workspaces. WRAPS the existing Render crons (deliverability-ramp-agent
  daily ramp + inbox-placement-launch Mon/Thu) and ADDS active/insurance/retired
  tagging, the 1% rule retire detector, bulk signature setting, and ad-hoc
  operator queries. The ramp logic itself is owned by ramp_agent.py — this skill
  reads its data (Supabase email_accounts + Instantly MCP) and writes only on
  Jose's explicit ask. Triggers on "show unhealthy inboxes for [client]",
  "tag these inboxes as retired", "rotate insurance pool into [campaign]",
  "set signatures for [client]", "como estan los inboxes de [cliente]",
  "limpia los inboxes muertos", "mueve estos al pool de insurance".
version: 0.1.0
---

# Instantly Inbox Manager

Operator-level skill for managing Luxvance's Instantly inboxes. Wraps the existing automated infrastructure with a conversational interface so Jose (or Marko / Ana) can ask "what's unhealthy in CapQuest?" or "retire these 4 inboxes" without leaving the conversation.

**Critical:** the AUTOMATIC ramp logic lives in `code/agency-os/02_Deliverability_Ramp_Agent/ramp_agent.py` (Render cron, daily 6 AM Dubai). This skill does NOT duplicate that logic. It reads the same data the ramp agent maintains (Supabase `email_accounts`) and the same Instantly MCP endpoints, so the skill and the cron stay aligned.

## When to use

- Wednesday positive-reply sweep (`cold-email-weekly-rhythm`) surfaces unhealthy inboxes and Jose wants to act on them
- Onboarding new inboxes after a Zapmail provisioning round (need to set warmup + signature + tags)
- A client's positive_reply_rate dropped and the `deliverability-incident-response` decision tree pointed at inbox-level fixes
- Quarterly review identifies inboxes that have been below the 1% rule for multiple weeks
- Ad-hoc: "show me CapQuest's sending pool", "which Kcal inboxes haven't sent in 7 days"

## When NOT to use

- For automatic daily ramp adjustments — that's `ramp_agent.py`'s job, runs every morning
- For the biweekly inbox-placement test launch — that's `inbox_placement.py`'s job, runs Mon + Thu
- For creating BRAND NEW inboxes (domain provisioning) — that's `domain-name-generator` + future `domain-provision-zapmail`
- For a single inbox issue — just open Instantly UI and fix manually; this skill is for bulk operations

## Relationship with sibling skills + existing code

| Component | Type | Relationship |
|---|---|---|
| `ramp_agent.py` (Render cron) | Existing, daily | **Source of truth for daily_limit + warmup health.** This skill READS the data it maintains; never overrides except when Jose forces it. |
| `inbox_placement.py` (Render cron) | Existing, Mon+Thu | **Source of truth for placement test results.** This skill surfaces summary; the manual review happens in Instantly UI on Wednesday. |
| Supabase `email_accounts` table | Existing | Read by both the cron and this skill. Persists TRUE age across reconnects (`first_seen_at`). |
| `cold-email-weekly-rhythm` | Skill | Invokes this skill on Wednesday + biweekly Monday rotation tasks. |
| `deliverability-audit` | Skill | Surfaces inbox health flags; this skill is how Jose ACTS on them. |
| `deliverability-incident-response` | Skill | Triages incidents; some actions (retire inbox, change warmup config) execute via this skill. |
| `positive-reply-scoring` | Skill | Provides per-inbox reply rate data; this skill uses it for the 1% rule retire detection. |

## Inputs / queries supported

| Query | What it does |
|---|---|
| `show <client>` | Lists all inboxes for one client workspace: email, domain, age, warmup_score, daily_limit, sent_today, tags |
| `show unhealthy <client>` | Same but filtered to `warmup_score <= 95` OR `is_blocked` OR `flag_low_reply` |
| `show active <client>` | Active pool (currently in live campaigns) |
| `show insurance <client>` | Insurance pool (warmed but idle) |
| `show retired <client>` | Retired (excluded from ramp + campaigns) |
| `tag <email>... as <tag>` | Bulk tag inboxes. Tags: `active`, `insurance`, `retired`, `new` |
| `untag <email>... <tag>` | Remove a tag |
| `set warmup <email>... mode=<enable\|disable> warmup-per-day=N ramp=N` | Bulk warmup config |
| `set signature <client> [--template-file=path]` | Apply signature template to all inboxes for a client |
| `rotate insurance to active <client> count=N` | Promote N healthiest insurance inboxes to active. Disables warmup on promoted ones. |
| `retire failing <client>` | Apply 1% rule + warmup score check; flag candidates and ask Jose to confirm before retiring |
| `report <client>` | Generate the operator-friendly health report (same shape as ramp_agent email but on-demand) |

## How active vs insurance vs retired works (Luxvance convention)

Defined here for the first time (`ramp_agent.py` does NOT yet read tags — it ramps everyone). Going forward:

| Tag | Behavior | Use case |
|---|---|---|
| `active` | Default. Warmup OFF in ramp_agent. Daily limit follows the age curve (cap 30). Counted in inbox-placement tests. | Currently in live campaigns. |
| `insurance` | Warmup ON, lower volume (15/day, no ramp). Daily limit = 0 in ramp_agent (do not send for live campaigns). | Warm reserve. Ready to rotate in when active inboxes burn. |
| `retired` | Excluded from ramp_agent. Warmup OFF. Daily limit = 0. NOT counted in inbox-placement tests. | Bad reputation, failed 1% rule, or otherwise unfit. Kept in Instantly only so the email address is preserved for suppression lookups; should not send. |
| `new` | Newly provisioned, less than 14 days since Zapmail creation. Warmup ON at 40/day with default 5-ramp. Daily limit = 0 in ramp_agent (do not send during initial warmup). After 14 days, promote to `insurance` or `active`. | Fresh from Zapmail. |

**Transition diagram:**

```
new ──(14 days, healthy warmup_score)──► insurance ──(rotated in)──► active
                                              │                          │
                                              │                          │
                                              ▼                          ▼
                                          retired ◄──────────(failed 1% rule)────
```

**Action required for this convention to be enforced:** edit `ramp_agent.py` to read tags from Instantly and apply the rules above. This is a follow-up code change, not part of the skill itself. Until that edit lands, this skill works in "advisory" mode: it surfaces what tags say SHOULD happen, but ramp_agent still ramps everyone.

## The 1% rule retire detector

A logical addition on top of `ramp_agent.py`'s current health check (which uses `stat_warmup_score` only).

**Detection logic:**

For each inbox in the last 30 days:

- Pull `sent` count and `replies` count from Instantly analytics (via MCP `analytics_daily_account` or `analytics_campaign`)
- Compute `reply_rate = replies / sent`
- Flag if `sent >= 200 AND reply_rate < 1%`
- Cross-reference with `warmup_score` from `ramp_agent.py`'s sync
- If both flags are present (low reply + low warmup) → STRONG retire candidate
- If only reply is low (warmup is fine) → REVIEW candidate (could be copy issue, not inbox issue)
- If only warmup is low → already handled by `ramp_agent.py` (clamps daily_limit)

**Output:**

```
1% rule check — CapQuest workspace, last 30 days

STRONG retire candidates (low reply + low warmup):
  sales@capquest-trygrowth.co — sent 412, replied 2 (0.49%), warmup 72
  marketing@capquest-getq.co — sent 287, replied 1 (0.35%), warmup 81

REVIEW candidates (low reply, warmup OK — could be copy issue):
  growth@capquest-tryhq.co — sent 654, replied 4 (0.61%), warmup 96
  newbiz@capquest-myhub.co — sent 522, replied 2 (0.38%), warmup 98

(handled by ramp_agent.py, no action needed) Low warmup:
  ops@capquest-getlab.co — warmup 68 (already clamped to daily_limit=1)

Action: retire STRONG candidates? Run /spam-word-checker on the campaign copy
for REVIEW candidates first.
```

## Signature template (Luxvance default)

```
{from_name}
{title}
{company}
{address}
```

Renders to (example):

```
Sarah Chen
Director, Outbound
CapQuest
Office 1207, Marina Plaza, Dubai Marina, Dubai, UAE
```

Where:

- `{from_name}` — from the inbox's `from_name` field in Instantly (different per inbox, e.g. "Sarah Chen" or "Marco Diaz"), or fallback to a client-default first/last name
- `{title}` — from a client-default like "Director, Outbound" (configured per workspace)
- `{company}` — the client name
- `{address}` — physical address (required by CAN-SPAM / similar regulations)

Per-client defaults live in `references/client-signature-defaults.yaml` (to be created when each client is onboarded).

In Instantly campaign body, end with `%signature%` (or the equivalent Instantly merge tag) so the inbox's signature is injected. Body should be:

```
<body>

<PS opt-out>

%signature%
```

## Common workflows

### Onboarding new inboxes after Zapmail provisioning

```
1. tag <list of new emails> as new
2. set warmup <emails> mode=enable warmup-per-day=40 ramp=5
3. set signature <client>     (applies the client's default template to all `new` inboxes)
4. Wait 14 days for warmup
5. tag <emails> as insurance (move out of `new` to `insurance` pool)
6. set warmup <emails> mode=enable warmup-per-day=15 ramp=0
```

### Activating insurance inboxes into a live campaign

```
1. show insurance <client>           (list available)
2. rotate insurance to active <client> count=10   (promotes the 10 healthiest)
   - Promoted inboxes get `active` tag, warmup OFF
   - Demoted (none in this direction) stays insurance
3. Add the new active inboxes to the campaign in Instantly UI (skill can do this if the user passes campaign-id)
```

### Weekly Wednesday health check

```
1. report <client> (or "report all" for all 6 workspaces)
2. retire failing <client> — surfaces 1% rule candidates, asks Jose to confirm
3. show insurance <client> — if active pool got smaller after retire, rotate insurance in
```

### Replacing burned inboxes

```
1. retire failing <client>           (move bad ones to retired)
2. show insurance <client>           (see what's available)
3. If insurance pool < 5, kick off domain provisioning (future domain-provision-zapmail skill)
   Otherwise, rotate from insurance.
```

## Per-workspace MCP routing

Luxvance has 6 Instantly workspaces, each with its own MCP namespace:

- `mcp__instantly-luxvance__*`
- `mcp__instantly-capquest__*`
- `mcp__instantly-kcal__*`
- `mcp__instantly-connect-resources__*`
- `mcp__instantly-gfv__*`
- `mcp__instantly-remly__*`

When Jose asks "show CapQuest", the skill uses `mcp__instantly-capquest__accounts_list`. Each workspace is queried independently — never mix metrics across clients.

## What this skill writes (and what it doesn't)

**Writes:**

- Instantly account tags (via `accounts_update` MCP)
- Instantly warmup config (via `accounts_warmup_enable` / `accounts_warmup_disable` MCP) — only on Jose's explicit ask
- Instantly account signatures (via `accounts_update` MCP)
- Supabase `email_accounts` table: nothing (the ramp_agent owns writes here)

**Reads only:**

- Instantly account list (`accounts_list`)
- Instantly analytics (`analytics_daily_account`, `analytics_campaign`)
- Supabase `email_accounts` (TRUE age, warmup history, last_checked_at)

**Never:**

- Overrides `ramp_agent.py`'s daily_limit decisions (that's the cron's job)
- Modifies the Supabase `email_accounts` schema or rows
- Triggers an inbox-placement test (that's `inbox_placement.py`'s job, scheduled)

## Important rules

- **Read-mostly.** Default mode is reporting. Writes happen only when Jose explicitly asks.
- **Per-workspace.** Never mix metrics across clients. CapQuest's pool is independent of Kcal's.
- **Confirm before bulk writes.** "retire failing" surfaces candidates and waits for Jose's confirmation per email.
- **Tag conventions matter.** The `active`/`insurance`/`retired`/`new` rules are the Luxvance convention; the ramp agent should be edited to enforce them (follow-up code change).
- **Don't duplicate ramp logic.** If a daily_limit needs adjusting, `ramp_agent.py` does it. This skill only nudges via tags + warmup config.

## Follow-up code changes (track separately)

1. **Edit `ramp_agent.py`** to read Instantly tags and apply the active/insurance/retired/new behavior (not currently enforced).
2. **Add 1% rule check to `ramp_agent.py`** so it also flags inboxes by reply rate, not just warmup score. Currently the reply-rate check happens only when this skill runs.
3. **Extend Supabase `email_accounts`** schema with a `tag` column synced from Instantly, so historical tag transitions are queryable.

Document these in `docs/INBOX_AND_DOMAIN_INFRASTRUCTURE_AUDIT.md` as TODO items.

## Failure modes

| Failure | Recovery |
|---|---|
| MCP `accounts_update` returns 4xx | Confirm tag exists in Instantly UI (some operations require pre-existing tags). Create via UI, retry. |
| Bulk operation times out on >100 inboxes | Batch in groups of 20-50. Retry the failed batch. |
| Tag transitions inconsistent (Instantly shows different state than skill expects) | Run `show <client>` to refresh ground truth; ramp_agent's daily run will reconcile. |
| Signature template references missing variable | Fall back to a safe default ("`<from_name>`\n`<company>`") and warn. |

## Language

Default to the language of Jose's most recent message for the report. Tag values stay in English (`active`, `insurance`, `retired`, `new`).

## Learned patterns

<!-- self-improvement entries get appended here when Jose adopts a new tag, threshold, or workflow on the fly -->

When the list grows past ~10 entries, promote the durable ones into the main body of this SKILL.md.

## Related files

- `code/agency-os/02_Deliverability_Ramp_Agent/ramp_agent.py` — source of truth for daily ramp; follow-up edits needed (see above)
- `code/agency-os/04_Inbox_Placement_Monitor/inbox_placement.py` — placement testing cron
- `docs/INBOX_AND_DOMAIN_INFRASTRUCTURE_AUDIT.md` — full audit of what exists vs gaps
- `docs/RENDER_SERVICES.md` — Render cron inventory
- `cold-email-weekly-rhythm/SKILL.md` — schedules when this skill runs
- `deliverability-audit/SKILL.md` — flags the inboxes this skill acts on
- `deliverability-incident-response/SKILL.md` — triage that may call this skill to execute fixes

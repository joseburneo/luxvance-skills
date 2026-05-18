---
name: deliverability-incident-response
description: >
  Triage playbook for when Luxvance cold-email deliverability breaks. Decision
  trees for the five most common incident types: reply rate dropped sharply,
  bounce rate spiked (>3%), domain blacklisted, inbox blocked in warmup, Gmail
  marking as Promotional. Includes the 72-hour "total failure" checklist for
  when nothing is working and Jose does not know why. Pair with deliverability-audit
  for diagnosis. Triggers on "we are in spam", "bounces are spiking",
  "domain is blacklisted", "inbox is blocked", "reply rate dropped",
  "incident response", "what do I do", "se cayeron las replies",
  "estamos en spam", "que hago si bounce sube".
version: 0.1.0
---

# Deliverability Incident Response

Things break. When they do, Luxvance needs a playbook — not panic. This skill is the triage decision tree.

## When to use

- `deliverability-audit` flagged a HIGH-priority issue
- Reply rate dropped >30% week-over-week with no obvious explanation
- Bounce rate spiked above 2-3%
- An Instantly inbox showed as blocked or warmup-failed
- Gmail is sending Luxvance emails to Promotions
- An angry recipient sent a spam complaint or threatened legal action
- Nothing is working and Jose has no idea why → use the 72-hour checklist

## When NOT to use

- A single inbox bounced one email — not an incident
- Replies trickled in slowly for a day — wait for 7-day averages
- For the routine Monday audit — that is `deliverability-audit`, not this skill

## Relationship with sibling skills

| Skill | Relationship |
|---|---|
| `deliverability-audit` | Diagnostic precedes triage. Audit identifies the issue; this skill decides the fix. |
| `positive-reply-scoring` | Used to confirm recovery after fixes — reply rate must return to baseline. |
| `cold-email-weekly-rhythm` | Triggers this skill when the Monday audit fires a HIGH flag. |
| `spam-word-checker` | Re-run on the campaign's copy if the incident is copy-driven (Gmail Promotional, hostile replies). |
| `enrich-and-verify-leads` | Re-run if the incident is list-driven (high bounce rate). |
| `lead-sourcing` | Re-run with tighter filters if the LIST is broken. |
| `list-quality-scorecard` | Re-grade the list after applying fixes. |

## The five incident types

| Symptom | Most likely cause | First action | Fix time |
|---|---|---|---|
| Reply rate dropped sharply | Deliverability — emails landing in spam | Run spam placement test | 1-14 days |
| Bounce rate spiked >3% | Bad list OR domain reputation | Check bounce types | 1-3 days |
| Domain blacklisted | Shared IP bad actor OR domain flagged | Check blacklists, rotate if needed | 7-30 days |
| Inbox blocked in warmup | Warmup network flagged sending patterns | Pause, investigate, maybe replace | 1-7 days |
| Gmail marking as Promotional | Content triggers (links, images, HTML) | Simplify content | 1-3 days |

## Decision tree: "reply rate dropped"

### Step 1: Quantify the drop

```
Was this week's reply rate <50% of the last 4 weeks' average?
  Yes → real drop, continue triage
  No  → noise, wait another week
```

If drop is real, continue.

### Step 2: Campaign-specific or fleet-wide?

```
Are ALL campaigns dropping, or just one?
  All → fleet-level issue (infrastructure or copy pattern)
  One → campaign-specific (targeting, copy, list)
```

### Step 3: Fleet-wide drop — check in order

1. **Spam placement test** (`deliverability-audit` monthly task, run early).
   - If inbox placement <70% → real deliverability issue. Skip to Step 4.
   - If inbox placement >85% → deliverability is fine. Look at copy / targeting.

2. **Domain authentication** (`deliverability-audit` Step 2).
   - Missing DKIM on any domain → fix immediately at registrar.
   - DMARC `policy=reject` with alignment failures → temporarily lower to `quarantine`.

3. **Warmup status** (`deliverability-audit` Step 1).
   - Multiple inboxes blocked in warmup → warmup network flagged Luxvance.
   - Reputation dropped "good" → "fair" on many inboxes → slow down sending volume.

4. **Bounce rate** (`deliverability-audit` Step 3).
   - If bounce >3% → list quality degraded. Jump to "bounce rate spiked" decision tree.
   - If bounce <1% but reply rate low → emails landing in spam (Step 1 result).

### Step 4: Spam-placement problem — what to do

Time-ordered actions:

1. **Immediate (today):** pause the highest-volume campaign. Stop damage.
2. **Day 1:** run spam placement test on 2-3 sender subsets (different tags: active vs new vs insurance). Find which cohort is worst.
3. **Day 1:** check the spam-filter detail report — which filters are firing. Common: `DKIM_INVALID`, `HTML_MESSAGE`, `LINK_REDIRECT`, `URI_TLD_BAD`. Each has a specific fix:
   - `DKIM_INVALID` → verify DKIM records across all domains, re-publish if needed
   - `HTML_MESSAGE` → simplify email body (fewer fonts, no inline CSS, no tracking pixels)
   - `LINK_REDIRECT` → remove or reduce links in Email 1 (ideally 0 links)
   - `URI_TLD_BAD` → switch domain TLD if `.info` / `.xyz` / `.click` are in the sending pool
4. **Day 2:** apply fixes.
5. **Day 3-14:** slow down send volume. Cut daily send per inbox by 50% for a week. Reputation rebuilds slowly.
6. **Day 14:** re-run spam placement test. If back above 85%, resume normal volume.

## Decision tree: "bounce rate spiked"

### Step 1: What kind of bounces?

Instantly categorizes bounces as hard (invalid address, permanent) or soft (temporary).

```
bounce_rate > 3% AND mostly_hard_bounces
  → list quality problem; re-verify with MillionVerifier

bounce_rate > 3% AND mostly_soft_bounces (greylist, temp)
  → domain reputation problem; slow sending

bounce_rate > 5% either type
  → STOP the campaign immediately to prevent ISP suspension
```

### Step 2: If list problem

1. Export the remaining leads from the campaign via Instantly MCP.
2. Re-run `enrich-and-verify-leads` (MV + BB waterfall) on the export.
3. Only reuse emails with `email_status = 'deliverable'` AND `email_verified_at` within 60 days.
4. Discard the rest.
5. Re-grade with `list-quality-scorecard` before re-uploading.

### Step 3: If reputation problem

Slow way down. Cut daily volume per inbox by 50% for 2 weeks. Re-enable / re-tune warmup more aggressively on the affected inboxes.

## Decision tree: "domain blacklisted"

### Step 1: Confirm the blacklist

Check:

- Spamhaus, Barracuda, SURBL via `deliverability-audit` monthly spam test (returns blacklist detail).
- MX Toolbox (https://mxtoolbox.com/blacklists.aspx) for a second opinion.

### Step 2: What tier of blacklist?

- **Domain on Spamhaus DBL or SURBL** → serious. May need to replace the domain entirely.
- **Sending IP on a DNSBL** → usually the IP pool's fault (shared Zapmail IPs). Wait 1-2 weeks for pool rotation.
- **Minor list (Barracuda, SORBS)** → submit delisting request at their portal. Usually resolved in 3-7 days.

### Step 3: Replace vs repair

- **Domain <30 days old + blacklisted** → replace. Not worth the cleanup effort.
- **Domain >90 days old + blacklisted** → try repair. Stop sending for 7 days, submit delisting requests, slowly resume.
- **If replacing:** archive the old domain (do NOT delete in case it surfaces again), buy a new lookalike at the registrar, warm for 2 weeks before reusing.

## Decision tree: "inbox blocked in warmup"

### Step 1: Why is it blocked?

Instantly flags `warmup_status = blocked` for several reasons:

- Warmup emails looked like spam to the warmup network
- Too many warmup peers marked them as spam
- The inbox's ESP rate-limits

### Step 2: Triage

1. Check the blocked reason (if Instantly exposes it).
2. If warmup-network issue → the inbox reputation may be damaged.
   - Young inbox (<30 days) → retire, provision new.
   - Established inbox (>90 days, previously good) → disable warmup, wait 48h, re-enable with `total_warmup_per_day` lowered (try 15 instead of 40).
3. If ISP rate-limit → wait 48h, re-enable warmup.

### Step 3: Retire workflow

- Tag the inbox as `retired` in Instantly UI
- Disable warmup
- Remove from active campaigns
- Provision a replacement (manual today; future skill could automate via Dynadot + Zapmail)

## Decision tree: "Gmail marking as Promotional"

### Step 1: Test on a fresh Gmail account

Send Email 1 of the campaign to a fresh @gmail.com address (Jose's, not in the campaign). Where does it land?

- Primary → fine
- Promotions → this is the issue
- Spam → bigger deliverability problem (see "reply rate dropped" tree)

### Step 2: Promotional-tab triggers (and fixes)

- Multiple links in email → drop to 0-1 links in Email 1
- Images / inline images → remove them
- Heavy HTML styling → simplify, fewer tags
- Marketing-style phrases (`click here`, `act now`, `limited time`) → run `spam-word-checker` and rewrite
- Unsubscribe in header (`List-Unsubscribe`) → actually helps deliverability, but formatting must be correct
- Mass signature blocks with logos → simplify to text-only

### Step 3: A/B test

Create two versions — current and stripped-down. Send 50 leads each. Compare reply rate after 7 days. Use `experiment-design` to formalize.

## The 72-hour "total failure" checklist

If NOTHING is working and Jose does not know why:

1. **Pause all Luxvance campaigns.** Stop damage.
2. **Audit:** run `deliverability-audit` full suite across all client workspaces.
3. **Spam test:** run spam placement on 2 sender subsets (active vs insurance).
4. **Check SPF / DKIM / DMARC on every domain** — if ANY are missing, fix at the registrar before resuming.
5. **Check the sending platform's health dashboard** — Instantly's status page, Zapmail's status. If the platform is down, everyone on it suffers.
6. **Reduce volume 75%** for the restart.
7. **Use a known-good copy** — don't launch new copy during recovery.
8. **Watch reply rate daily** for 7 days post-restart via `positive-reply-scoring`.

## When to call in experts

- Luxvance has been in spam for >2 weeks despite fixes → infrastructure-level issue. Consider migrating sending platforms.
- Multiple domains permanently blacklisted → IP pool issue. Switch providers.
- A specific client's domain reputation never recovers after 4 weeks → retire the domain, replace.

## Important rules

- **Pause first, investigate second.** Continued sending while broken digs the hole deeper.
- **Reputation rebuilds slowly.** After applying fixes, wait 7 days before re-auditing. Faster re-audits read noise, not signal.
- **Never skip the experiment after a fix.** Document what changed and what recovered, so the same incident type next time is faster to triage.
- **One incident at a time.** If two fires are burning, pick the bigger one first. Bounces > spam-placement > Promotional tab.
- **Hostile complaints are red flags.** A single legal-threat reply is not "noise" — it can trigger ESP-level investigation. Pause the offending campaign, remove the offended contact, document.

## The 1% rule sanity check

After fixes are applied, give the recovery at least 200 sends at normal volume. If reply rate is still below 1% — there is a deeper issue. Start the playbook over.

## What to do next

**Re-run `deliverability-audit --days=7`** in 7 days to confirm recovery. Domain / inbox reputation rebuilds slowly.

Meanwhile: continue `cold-email-weekly-rhythm`, which catches new issues as they emerge.

**If the incident required replacing domains / inboxes:** wait 2 weeks for warmup on the replacements before expecting full recovery.

**Document the incident:** save a one-page incident report to `profiles/<client-slug>/incidents/<YYYY-MM-DD>-<incident>.md`. Quarterly review reads this to spot patterns.

## Language

Default to the language of Jose's most recent message for the report and triage prompts. Technical terms (SPF, DKIM, DMARC, DNSBL) stay in English.

## Learned patterns

<!-- self-improvement entries get appended here when Jose adopts a new incident type or fix on the fly -->

When the list grows past ~10 entries, promote the durable ones into the main body of this SKILL.md.

## References

- `references/incident-templates.md` — one-page incident report template
- `references/spam-filter-triggers.md` — common spam-filter codes (shared with deliverability-audit)
- `deliverability-audit/SKILL.md` — diagnostic suite this skill depends on
- `cold-email-weekly-rhythm/SKILL.md` — ops cadence that surfaces incidents

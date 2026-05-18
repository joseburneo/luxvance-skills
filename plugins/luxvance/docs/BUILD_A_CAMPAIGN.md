# Build a Campaign — Operational Handbook

The complete step-by-step the Luxvance team follows to create and launch a cold-email campaign. This is the doc Marko and Ana open before pressing Start. The skills do the heavy lifting; this doc is the human-readable checklist and the source of truth for the rules.

**Read this once. Bookmark it. Re-open before every launch.**

---

## TL;DR — The fastest path

```
1.  Invoke /build-cold-email-campaign in Claude Code
       (orchestrator chains the 9 phases below)
2.  Approve each handoff (intel, strategy pick, kit, leads, etc.)
3.  Open the Instantly URL printed at the end
4.  Confirm sender inboxes are tagged "Actively Sending"
5.  Hit Start in the Instantly UI
6.  cold-email-weekly-rhythm takes over from here
```

That's it. The rest of this doc explains what to expect at each phase, the hard rules, and the Instantly settings you'll touch.

---

## The 9 phases (what /build-cold-email-campaign runs)

| # | Phase | Skill invoked | What you see / approve |
|---|---|---|---|
| 1 | Resolve client + load state | (orchestrator) | "Found prior state for [client]: N campaigns, last shipped..." |
| 2 | Analyze historical data | `campaign-intelligence` | 60-day analysis + locked hypothesis (Bet / Why / Evidence) |
| 3 | Generate 15-25 ideas | `campaign-strategy` | Ideas table — you pick one |
| 4 | Build the kit | `build-campaign` | 10-block kit + variants.yaml (rendered email + Clay prompts + Instantly spintax) |
| 5 | Source the leads | `lead-sourcing` | raw_leads.csv (Apollo / Icypeas / Prospeo / engagers / Maps) |
| 6 | Verify deliverability | `enrich-and-verify-leads` | verified.csv (Million Verifier + BounceBan waterfall) |
| 7 | Grade the list | `list-quality-scorecard` | Letter grade A-F. Below C blocks the upload. |
| 8 | Personalize per lead | `personalized-copywriting` | enriched_leads.csv with V1 + V2 (uses saved prompt for repeat clients) |
| 9 | Push to Instantly DRAFT | `launch-instantly-campaign` | Campaign DRAFT URL — review, attach inboxes, Start manually |

Phases can be skipped:
- Skip Phase 2 if Jose gave a one-line hypothesis directly
- Skip Phase 3 if Jose already picked the specific campaign idea
- Skip Phase 5 if Jose provides a CSV directly

---

## Hard rules (every campaign, no exceptions)

These three rules apply to **every** campaign across **every** Luxvance client. They are not stylistic preferences — they protect deliverability and reply rates.

### Rule 1 — Minimum 3 days between sequence steps

Every step after Step 1 must wait **at least 3 days** from the previous step.

```
Step 1: day 0
Step 2: day +3 (minimum)
Step 3: day +6 (minimum)
```

Longer waits (5, 7, 10 days) are fine. Shorter (1 day, 2 days) are not.

**Why:** Tight cadences feel pushy in B2B and especially in healthcare / executive outreach where the recipient may only check non-priority mail a few times a week. Three days respects the prospect's inbox rhythm and keeps reply rates healthy.

**How `build-campaign` enforces this:** Phase 7 (sequence config question) defaults to day 0 / day +3 / day +6. If you override ("3 steps, 0/1/2"), the skill rejects it and asks for a cadence ≥ 3 days.

### Rule 2 — Zero links in Email 1, and never mention "I'll send the link"

Email 1 of any sequence contains **zero links**. No URLs, no hyperlinks, no tracked or untracked anchors. The copy reads as if no link was ever part of the plan.

**Forbidden phrases in Email 1:**
- "I'll share the menu in a separate note"
- "I'll follow up with the link"
- "More details to come"
- Any reference to a link coming later

**Step 2+ links:** include a link ONLY when there's a genuinely useful resource (menu page, calendar booking, case study, product page). If no relevant link exists, Step 2 is text-only and that's correct — often better than forcing one.

**Why:** Cold inboxes (Gmail, Outlook, GSuite) flag first-touch emails with links as a deliverability risk. The first email is the highest-stakes for inboxing, so it stays text-only. The reason is operational — irrelevant to the prospect — so we never expose it in the copy.

**How `build-campaign` enforces this:** Phase 6 + `spam-word-checker` auto-trigger together remove any URL from block 3 (rendered email) and block 9 (body spintax) when those represent Step 1. They also flag any "I'll send the link" bridge sentence for rewrite.

### Rule 3 — Voice: natural English + respectful greetings

#### 3a. Never use "follow up" boilerplate

These phrases are banned on every step:

- "Just a short follow up on my last note."
- "A quick follow up on my note from earlier."
- "Following up on my message from earlier this week."
- "Just following up."
- Any variant of "I'm following up on..."

**Use natural reference-to-prior-email phrasing instead** (especially as the Step 2 opener):

- "Did you have the chance to see my email below?"
- "Did you get the opportunity to see my email below?"
- "Have you seen my email below?"
- "Have you had a moment to look at my note below?"

These read like a real person, not a template.

#### 3b. Default to formal greetings (especially UAE / medical / executive)

For UAE prospects, doctors, and senior professionals, formality matters culturally.

**Use:**
- "Dear Dr. {{firstName}}"
- "Hello Dr. {{firstName}}"
- "Hello Doctor"
- "Good day Dr. {{firstName}}"

**Avoid "Hi"** — too casual for UAE / medical / executive contexts. Even "Hi Dr." reads under-dressed for the relationship at first contact.

For non-medical B2B prospects in NAM / EMEA, "Hello {{firstName}}" works. Reserve "Dear" for the most formal contexts (medical, legal, government).

**How `build-campaign` enforces this:** brand-guidelines + spam-word-checker block flattery openers and over-casual greetings. The audience tone in the locked hypothesis (formal / casual / peer-to-peer) gates the greeting choice.

---

## Instantly settings: every campaign needs these

When `launch-instantly-campaign` (Phase 9) creates the DRAFT, these settings get applied. You should know what each does before approving the launch.

### Sending account selection

**Tag convention:** `Actively Sending` (or `active` — confirm the exact tag name in your client's Instantly workspace before launch).

How the convention works:

| Tag | Behavior | When to apply |
|---|---|---|
| `Actively Sending` (= active) | Inboxes currently sending in live campaigns. Warmup OFF or minimal. | Default for any inbox attached to a DRAFT or running campaign. |
| `insurance` | Warmed but idle. Warmup ON at lower volume (15/day, no ramp). | Reserve pool. Rotate in when an active inbox burns. |
| `retired` | Excluded from ramp + new campaigns. Warmup OFF. | Inboxes that failed the 1% rule or are flagged. Kept for suppression lookups only. |
| `new` | Less than 14 days since Zapmail creation. Warmup ON at 40/day with 5-ramp. | After Zapmail provisioning. Promote to insurance after 14-day warmup. |

In the campaign's `variants.yaml`:

```yaml
inbox_selection:
  tag: "Actively Sending"   # or "active" — match your workspace's exact tag
  count: 20                  # how many active inboxes to attach
```

`launch-instantly-campaign` queries Instantly for inboxes matching the tag, sorts by least-recently-used (LRU by daily_sent_count ASC), and attaches the top N.

### Schedule

```yaml
schedule:
  timezone: "Europe/London"        # IANA timezone, match the prospect region
  days: [1, 2, 3, 4, 5]            # 1=Mon ... 7=Sun. Default M-F.
  start_hour: "08:00"              # local to the timezone
  end_hour: "17:00"
  min_time_btw_emails: 10          # minutes between consecutive sends from the same inbox
  max_leads_per_day: 30            # new leads started per inbox per day
```

**Region defaults:**
- NAM → `America/New_York`, M-F
- EMEA (UK / IE / continental) → `Europe/London` or `Europe/Brussels`, M-F
- GCC (UAE) → `Asia/Dubai`, **Sun-Thu** (`days: [7, 1, 2, 3, 4]`)
- LATAM → `America/Bogota`, M-F

**Throttle defaults:** 10 min between sends per inbox. Higher (15-30 min) for ramping new inboxes.

**Max leads/inbox/day:** 30 for fully warmed inboxes. 15 for newly active inboxes. Never above 40.

### Sequence

Default is **Step 1 only**. Multi-step only when explicitly chosen in Phase 7 (sequence config question).

```yaml
sequences:
  - step: 1
    delay_days: 0
    variants:
      - label: A
        subject: "..."
        body: "..."
      - label: B           # optional A/B/C
        subject: "..."
        body: "..."
  - step: 2                # optional — Phase 7 must approve
    delay_days: 3          # ≥3 (Rule 1)
    variants:
      - label: A
        subject: ""        # empty = threaded under Step 1
        body: "..."
  - step: 3                # optional
    delay_days: 3          # ≥3
    variants:
      - label: A
        subject: "..."     # fresh subject = new thread
        body: "..."
```

### Tracking + reply behavior

These should be set on every Luxvance campaign:

| Setting | Value | Why |
|---|---|---|
| Open tracking | OFF | Open tracking inserts a tracking pixel that some spam filters flag. Open rate is unreliable anyway — `positive-reply-scoring` is what we care about. |
| Click tracking | OFF | Same reason. Plus we don't put links in Email 1 (Rule 2). |
| Stop on reply | ON | Once a lead replies, halt the rest of the sequence. Manual reply triage takes over. |
| Stop on auto-reply | OFF | OOO replies should NOT stop the sequence; the lead is just out. |
| Unsubscribe footer | OFF | Luxvance's opt-out is in the body copy ("A reply of 'no' is enough and I'll step out of your inbox"). Instantly's default footer is too marketing-y. |

### Custom variables (CSV → Instantly mapping)

The `enriched_leads.csv` from `personalized-copywriting` (Phase 8) maps to Instantly merge fields:

| CSV column | Instantly merge | Notes |
|---|---|---|
| `email` | (recipient, not a merge) | Required |
| `first_name` | `{{firstName}}` | Required |
| `last_name` | `{{lastName}}` | Required |
| `company_name` | `{{companyName}}` | Required. Never use `{{company}}`. |
| `company_domain` | `{{companyDomain}}` | Optional |
| `title` | `{{title}}` | Optional |
| `linkedin_url` | `{{linkedinUrl}}` | Optional |
| `variable_1` | `{{Variable 1}}` | Per-lead AI variable |
| `variable_2` | `{{Variable 2}}` | Per-lead AI variable |
| `situation_line` | `{{situation_line}}` | Optional, AI-generated |
| `value_line` | `{{value_line}}` | Optional, AI-generated |
| `cta_line` | `{{cta_line}}` | Optional, AI-generated |

Disallowed columns (will fail the upload): `phone`, `mobile`, `address`, `street`, `city`, `state`, `zip`, `country`, `revenue`, `funding`, anything starting with `_`.

---

## Pre-launch checklist (do this before Start)

Open the Instantly DRAFT URL printed at the end of Phase 9. Verify:

- [ ] Campaign name matches the Luxvance convention: `Luxvance - <Region> - <Persona> - <Trigger> - W<ISO week>`
- [ ] Subject lines + body previews look clean, no broken spintax, no em-dashes
- [ ] **Rule 1 check:** sequence cadence is day 0 / day +3 / day +6 (or longer)
- [ ] **Rule 2 check:** Email 1 has zero links and no "I'll send the link" phrasing
- [ ] **Rule 3 check:** greetings are formal (Dear / Hello / Good day, not "Hi") for the audience tone; no "follow up" boilerplate in Step 2+
- [ ] Sender inboxes: tag is `Actively Sending` (or your workspace's equivalent), count matches expected (typically 20)
- [ ] Schedule: timezone matches prospect region, throttle reasonable (10 min between), max/day reasonable (≤30)
- [ ] Tracking: open OFF, click OFF, stop-on-reply ON
- [ ] Lead count: matches `enriched_leads.csv` row count exactly
- [ ] Spot-check 3 random leads' rendered emails: variables look right, no `{{}}` artifacts, no broken AI variable values

If all checked, hit Start. If anything is off, fix in Instantly UI OR re-run the relevant skill and re-upload.

---

## What happens after Start

`cold-email-weekly-rhythm` takes over. Put these on your calendar:

| Cadence | Task | Skill |
|---|---|---|
| Every Monday 9am Dubai | Deliverability audit | `deliverability-audit` |
| Every Wednesday 10am Dubai | Positive-reply sweep — respond to interested leads within 30 seconds | `positive-reply-scoring` |
| Every Friday 3pm Dubai | Campaign retrospectives (at day 21) | `positive-reply-scoring` + `experiment-design` |
| Every other Monday 11am | Inbox rotation (insurance → active, retire bad) | `instantly-inbox-manager` |
| 1st of each month | Spam placement test (or rely on the `inbox-placement-launch` Render cron Mon+Thu) | `deliverability-audit` |
| First Monday of each quarter | Experiment review + ICP adjustment | `experiment-design` |

Full playbook in [`cold-email-weekly-rhythm/SKILL.md`](.claude/skills/cold-email-weekly-rhythm/SKILL.md) (or via the plugin).

---

## When things break

| Symptom | Where to go |
|---|---|
| Reply rate dropped >30% week-over-week | `deliverability-incident-response` → reply-rate-drop tree |
| Bounce rate spiked above 3% | `deliverability-incident-response` → bounce tree |
| Domain on a blacklist | `deliverability-incident-response` → blacklist tree |
| Inbox blocked in warmup | `deliverability-incident-response` → warmup-block tree |
| Gmail marking as Promotional | `deliverability-incident-response` → Gmail tree |
| List quality scorecard returned C or below | Loop back to Phase 5 with tighter `lead-sourcing` filters; re-grade |
| Personalization QA loop never converges | The locked hypothesis is too vague — back to Phase 2 (`campaign-intelligence`) |

---

## Related docs + skills

- [`COLD_EMAIL_CAMPAIGN_PIPELINE.md`](COLD_EMAIL_CAMPAIGN_PIPELINE.md) — the full pipeline reference (all 26 skills indexed)
- [`LEAD_ENRICHMENT_PIPELINE.md`](LEAD_ENRICHMENT_PIPELINE.md) — deep-dive on Phase 6 verification stage
- [`INSTANTLY_CLI_QUICKREF.md`](INSTANTLY_CLI_QUICKREF.md) — when to use CLI vs MCP for Instantly operations
- [`INBOX_AND_DOMAIN_INFRASTRUCTURE_AUDIT.md`](INBOX_AND_DOMAIN_INFRASTRUCTURE_AUDIT.md) — what existing Luxvance code already covers (ramp agent, inbox placement crons)
- [`RENDER_SERVICES.md`](RENDER_SERVICES.md) — the 21 Render crons that run alongside the skills
- All 26 skills at `code/luxvance-skills/plugins/luxvance/skills/` (synced to GitHub for team install)

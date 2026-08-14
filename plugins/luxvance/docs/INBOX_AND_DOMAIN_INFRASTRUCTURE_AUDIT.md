# Inbox + Domain Infrastructure Audit

> Auditoría histórica (mayo 2026). La parte de skills está retirada; proceso vigente: `docs/CAMPAIGN_BUILDING.md`. La parte de infraestructura sigue siendo referencia útil.

**Date:** 2026-05-18
**Owner:** Jose
**Purpose:** Before building new inbox-manager and domain-setup skills inspired by Growth Engine X, audit what Luxvance already has in production code so we tropicalize cleanly instead of duplicating.

---

## TL;DR

Luxvance already runs **two production Render crons** that cover meaningful chunks of what GEX's `smartlead-inbox-manager` and `email-deliverability-audit` describe. We also have an entire `Campaign Factory` Python codebase that overlaps with `lead-sourcing`, `enrich-and-verify-leads`, and `personalized-copywriting`. New skills should **wrap and surface** what we have, not duplicate it.

For domain provisioning (Dynadot + Zapmail end-to-end automation), we have **none** of the buy-side or provisioning logic. We only have transactional notifications via Zapmail and a reporting CSV on existing Zapmail accounts. That whole layer is net-new build.

---

## What we already have

### 1. `deliverability-ramp-agent` (Render cron, runs daily 6 AM Dubai)

**Path:** `code/agency-os/02_Deliverability_Ramp_Agent/ramp_agent.py` (467 lines)
**Render service:** `crn-d6ear7sr85hc73d3ub4g`
**Schedule:** `0 2 * * *` UTC (daily)
**Status:** Live, in production

**What it does:**
- Pulls every Instantly account across every Luxvance workspace (Luxvance, CapQuest, Kcal, Connect Resources, GFV, Remly, plus any others connected)
- Tracks each account's **TRUE age** in Supabase table `email_accounts` (survives Instantly reconnections — important: when an inbox gets disconnected and reconnected, Instantly resets the `created_at` to today, which would crash a naive ramp)
- Ramps `daily_limit` per account:
  - Days 1-10: 0 (warmup only)
  - Day 11+: `(age - 10) * 2`, capped at 30
- **Health check:** if `stat_warmup_score <= 95`, the account is "sick" → clamps `daily_limit` to 1
- **Never ramps DOWN a healthy account** (preserves prior warmup when an account was already at a higher limit)
- Multi-threaded (20 workers)
- Sends an HTML email report with per-client breakdown (processed / scaled_up / sick / coasting / total_capacity)

**What it covers from GEX `smartlead-inbox-manager`:**
- ✅ Bulk warmup ramp (we do it daily, automated)
- ✅ Health-driven retire / clamp logic (sick → 1)
- ✅ Survival-of-reconnect behavior (Luxvance-specific, GEX doesn't have this)

**What's missing vs GEX:**
- ❌ Active vs Insurance tagging — Luxvance has no formal tag distinction
- ❌ Signature bulk-set — Luxvance does this manually in the Instantly UI
- ❌ 1% rule applied at inbox level (current health check only uses warmup score, not reply rate)
- ❌ Conversational operator interface — today only the email report exposes this data

---

### 2. `inbox-placement-launch` (Render cron, runs Mon + Thu 9 AM Dubai)

**Path:** `code/agency-os/04_Inbox_Placement_Monitor/inbox_placement.py` (352 lines)
**Render service:** `crn-d69c0m8gjchc73dh9re0`
**Schedule:** `0 5 * * 1,4` UTC (Monday and Thursday)
**Status:** Live, in production

**What it does:**
- For each Luxvance client workspace, launches **two Instantly inbox-placement tests** simultaneously:
  - **Test A (Safe):** generic template with spintax greetings/CTAs, no merge fields
  - **Test B (Campaign):** **real sent email from the best active campaign**, variables already rendered (uses Instantly's `/emails` endpoint, picks `ue_type=1` sent emails with a non-empty subject — this is clever)
- Requires minimum 6 active accounts per workspace to run
- Sends a summary HTML email to Jose + Anita
- Review of placement results is **manual** in the Instantly UI on Wednesday

**What it covers from GEX `email-deliverability-audit`:**
- ✅ Spam placement testing — and we do it BIWEEKLY, vs GEX's monthly. We're ahead.
- ✅ A/B test methodology (safe vs real campaign copy)

**What's missing vs GEX:**
- ❌ Automated parsing of placement results — the Wednesday review is manual
- ❌ Flagging by provider (Gmail vs Outlook vs Yahoo split)
- ❌ Automatic action triggers (e.g. "below 80% inbox → pause campaign")
- ❌ SPF / DKIM / DMARC `dig` checks

---

### 3. `agency-master-report` (Render cron, 8 AM + 5 PM Brussels)

**Path:** `code/agency-os/01_Agency_Master_Report/agency_report.py`
**Render service:** `crn-d6dvmq15pdvs73fjvu90`
**Schedule:** `0 6,15 * * *` UTC
**Status:** Live, in production

**Covers:** Daily KPIs + Slack digest. Surface-level overview of every active campaign across every client.

**Relationship to GEX:** complementary, not duplicated. The new `positive-reply-scoring` skill produces deeper per-campaign analysis that feeds back to this report's content.

---

### 4. `lead-reply-body-audit` (Render cron, daily 9 AM Dubai)

**Path:** `code/agency-os/domains/quality/lead_reply_body_audit.py`
**Render service:** `crn-d7tpi0beo5us738ckorg`
**Status:** Live, in production

**Covers:** data-quality guardrail on the reply ingest pipeline (catches Clay/Instantly extraction breakage within 24h).

**Relationship to GEX:** complementary. Luxvance-specific data hygiene.

---

### 5. Campaign Factory (Python module, `code/agency-os/08_Campaign_Factory/`)

**Size:** 14 Python files, ~3,900 lines total
**Status:** Exists; deployment status unclear (not in `render.yaml`, may run locally or via separate trigger)

**Key files:**

| File | Lines | What it does |
|---|---|---|
| `factory_orchestrator.py` | 287 | Stateful HITL orchestrator with `job_id` JSON state files |
| `apify_client.py` | 127 | Apify Apollo wrapper |
| `icypeas_client.py` | 316 | Icypeas wrapper |
| `lead_sourcer.py` | 324 | Lead sourcing orchestration |
| `verification_engine.py` | 430 | MV + BB verification waterfall |
| `enrichment_engine.py` | 419 | Lead enrichment |
| `personalization_engine.py` | 603 | Per-lead variable generation |
| `tier_classifier.py` | 351 | ICP classification |
| `supabase_cache.py` | 426 | Supabase-backed lookup cache for leads |
| `template_parser.py` | 225 | Campaign template parser |
| `zapmail_client.py` | 123 | **Transactional notification sender via Zapmail** (alerts on Instantly disconnections) |
| `zapmail_manager.py` | 162 | **Reporting CSV of existing Zapmail accounts** (active/disconnected/paused per domain + MRR) |

**Critical observation:** The Campaign Factory in Python already implements much of what `lead-sourcing`, `enrich-and-verify-leads`, and `personalized-copywriting` skills describe — but as backend code, not as Claude Code skills. The skills we built yesterday are the **conversational interface layer** that should call into this code where possible, OR the Python code should be retired in favor of the skill-only pipeline.

**Decision (to revisit):** keep both for now. The Python code runs unattended (good for scheduled jobs); the skills are for interactive operator work (good for ad-hoc campaigns). They don't conflict, but they share the same Supabase tables, so we need to make sure they don't double-write.

---

### 6. What we have for Zapmail / domain provisioning (almost nothing)

**Current state:**
- `zapmail_client.py` — sends transactional emails via Zapmail's send API (used for alerts when an Instantly account disconnects). Bearer auth, `/v1/send` endpoint. Read-only on the rest of the Zapmail platform.
- `zapmail_manager.py` — reports on existing Zapmail accounts and subscriptions. Pulls `/v2/onebox/connected-accounts` + `/v2/subscriptions`. Outputs a CSV with active/disconnected/paused counts per client domain + MRR. Read-only.

**What does NOT exist:**
- ❌ Dynadot integration of any kind (no API client, no env vars)
- ❌ Domain name generation (no brand+prefix+suffix combinator)
- ❌ Domain availability checking
- ❌ Domain purchase
- ❌ Nameserver switching
- ❌ Inbox provisioning via Zapmail's create-account endpoint
- ❌ End-to-end provisioning orchestrator
- ❌ Cost-gating before spending

Jose buys domains manually via the Dynadot / Cloudflare UI, then adds them to Zapmail manually, then creates inboxes manually. The whole buy-side flow is 100% manual today.

---

## What we'd need to add (gap analysis)

### Inbox manager — `instantly-inbox-manager` skill

**Approach:** WRAP what we have, ADD the gaps. Net-new build is small.

| Capability | Source |
|---|---|
| Ramp daily limits by age + health | **Existing** — `ramp_agent.py`, runs daily |
| Auto-ramp survives Instantly reconnects | **Existing** — `ramp_agent.py` + Supabase `email_accounts.first_seen_at` |
| Email report after ramp | **Existing** — `ramp_agent.py` |
| Inbox placement test (safe + campaign) | **Existing** — `inbox_placement.py`, Mon+Thu |
| Bulk warmup config (force values for a tagged subset) | **NEW** — skill calls Instantly MCP `accounts_warmup_enable/disable` |
| Bulk signature set | **NEW** — skill renders signature from `{from_name}, {title}, {company}, {address}` and calls Instantly MCP `accounts_update` per inbox |
| Active vs Insurance tagging | **NEW** — define convention, apply via Instantly MCP. Default convention: untagged = active (legacy behavior); tag `insurance` = warmup ON + daily_limit forced 0; tag `retired` = excluded from ramp_agent |
| 1% rule retire detection | **NEW** — skill queries Instantly analytics for sent + reply over 30 days per inbox; flags inboxes with sent ≥200 AND reply <1%; surfaces in the Wed sweep |
| Conversational operator interface | **NEW** — the skill itself, with Jose asking "show me unhealthy inboxes for CapQuest", "tag these 4 as retired", "rotate insurance pool into Luxvance UK" |

**Implementation note:** the skill should READ the data the existing crons already maintain (Supabase `email_accounts` + Instantly via MCP) and WRITE only when Jose explicitly asks. It should never duplicate the ramp logic — that lives in `ramp_agent.py` and is the source of truth.

**Effort estimate:** 3-4 hours to build. Most of it is conversational logic + Instantly MCP wrapping.

---

### Domain setup — `domain-setup-zapmail` skill

**Approach:** mostly net-new build (the buy-side is missing entirely).

| Capability | Source |
|---|---|
| Read existing Zapmail accounts + subscriptions | **Existing** — `zapmail_manager.py` |
| Notify on Instantly disconnect | **Existing** — `zapmail_client.py` |
| Generate short domain candidates (brand + prefixes + suffixes) | **NEW** — port GEX naming logic. 36 prefixes (go, try, get, my, hey, …) + 40 suffixes (hq, hub, pro, lab, …), max 40 chars SLD, banned substrings (mega, ultra, grp), awkward-substring screen |
| Check availability at Dynadot (batch up to 100) | **NEW** — Dynadot API client. Need `DYNADOT_API_KEY` env var (not in `master.env` yet) |
| Wallet balance check before purchase | **NEW** — Dynadot `command=account_info` |
| Purchase domains (one per call) | **NEW** — Dynadot `command=register&domain=X&duration=1` |
| Switch nameservers to Zapmail | **NEW** — Dynadot `command=set_ns` |
| Wait 15-20 min for DNS propagation | **NEW** — orchestrator delay logic |
| Connect domains on Zapmail | **NEW** — Zapmail v2 add-domain endpoint (not in current `zapmail_client.py`) |
| Wait 10-30 min for assignable status | **NEW** — orchestrator delay logic |
| Create inboxes on Zapmail (3-5 per domain) | **NEW** — Zapmail v2 create-inbox endpoint |
| Wait 4-6 hours for inbox provisioning | **NEW** — orchestrator delay (these waits make the skill best run in chunks, not one-shot) |
| Export inbox credentials to CSV for Instantly import | **NEW** — straightforward CSV write |
| Cost-gate before spending | **NEW** — surface "I'm about to buy N domains at ~$X each = $Y. Confirm?" before any purchase call |

**APIs to register / configure:**

1. **Dynadot API key** — get from `dynadot.com → Tools → API`. Whitelist the IP that runs the skill (or Render IPs if we deploy it). Add `DYNADOT_API_KEY` to `master.env`.
2. **Zapmail API key** — already in `master.env` as `ZAPMAIL_API_KEY` (used by `zapmail_manager.py`). Verify scopes include domain-add and inbox-create.
3. **Budget thresholds** — define max per-domain price ($3.50 for `.com`), max batch size (50 domains per session by default), confirm-before-execute gate.

**Effort estimate:** 5-6 hours to build properly. The orchestrator's wait logic is tricky (long sleeps don't play well with Claude Code sessions). Probably worth splitting into two skills:

- `domain-name-generator` — generate candidates, check availability, surface a CSV. Fast, no spending.
- `domain-provision-zapmail` — given a list of available domains, run the buy → nameserver → connect → inbox creation flow. Slow, spends money, needs to handle waits.

**Caveat:** the wait times (15-30 min DNS, 10-30 min Zapmail assignable, 4-6 hours inbox provisioning) mean this skill is best designed as **resumable** — checkpoint progress to a JSON file so Jose can stop and resume later without re-running expensive steps.

---

## Recommendations

### For `instantly-inbox-manager`

**Build now.** It's a thin conversational layer over existing infrastructure. The skill should:

1. Document the existing crons as the source of truth (don't duplicate).
2. Add the active/insurance/retired tagging convention.
3. Add the 1% rule retire-detector.
4. Provide conversational queries: "show me unhealthy CapQuest inboxes", "what's the active pool for Luxvance", "retire these 4 inboxes".
5. Reference the ramp report email — Jose already gets the data; the skill helps him ACT on it.

### For `domain-setup-zapmail`

**Build in two phases:**

1. **Phase A (build now):** `domain-name-generator` — port the GEX naming logic + Dynadot availability check. Costs nothing to run. Output: a CSV of available short brand domains with prices. Jose can review and decide whether to buy via the Dynadot UI manually, OR pass the list to Phase B.

2. **Phase B (build after Phase A is validated):** `domain-provision-zapmail` — the buy → nameserver → connect → inbox-create flow. Adds Dynadot API key requirement, real spending, and the resumable orchestrator pattern. Worth waiting until Phase A has produced 1-2 good domain lists Jose actually used.

**Why split:** Phase A is safe to ship today; Phase B needs more design work on the resumable / wait-time pattern + cost gating. Splitting also reduces the blast radius if either side has bugs.

---

## What to do with the existing Campaign Factory

**Open question for Jose:** the `08_Campaign_Factory/` Python module overlaps significantly with the new Claude Code skills (`lead-sourcing`, `enrich-and-verify-leads`, `personalized-copywriting`, `build-cold-email-campaign`).

Two paths forward:

1. **Keep both as parallel implementations.** Skills for interactive work, Python module for unattended/scheduled jobs. Risk: divergence over time, double-maintenance, confusing for new operators.
2. **Pick one as the source of truth and retire the other.** If the new skills cover everything the Python code does, retire the Python (keep the verification + enrichment + personalization engines as libraries the skills call, but drop the orchestrator). If the Python code is more battle-tested, then the skills should be thin wrappers around it.

**Decision deferred** — we should review the Campaign Factory more carefully (especially `personalization_engine.py` at 603 lines and `factory_orchestrator.py`) before deciding. Until then, the new skills and the Python code coexist without conflict because they read/write the same Supabase tables idempotently.

---

## Next concrete builds

Given the audit, the build queue is (in order):

1. `competitor-engagers` — net-new channel, no existing code to reconcile (~3h)
2. `google-maps-list-builder` — net-new channel (~3h)
3. `lead-magnet-brainstorm` — net-new framework (~1.5h)
4. `icp-prompt-builder` — net-new pattern, but the Tier Classifier in Campaign Factory may overlap; check before building (~2h)
5. `instantly-inbox-manager` — wraps existing ramp + inbox-placement crons + adds gaps (~3-4h)
6. `domain-name-generator` (Phase A) — port GEX naming + Dynadot availability check (~3h)
7. `domain-provision-zapmail` (Phase B) — deferred until Phase A proven

Total: ~16-19 hours of focused work for the full set.

---

## Related files

- `docs/RENDER_SERVICES.md` — live inventory of the 21 Render services
- `docs/COLD_EMAIL_CAMPAIGN_PIPELINE.md` — pipeline doc that now includes the optimize layer
- `code/agency-os/02_Deliverability_Ramp_Agent/ramp_agent.py` — ramp source of truth
- `code/agency-os/04_Inbox_Placement_Monitor/inbox_placement.py` — placement testing source of truth
- `code/agency-os/08_Campaign_Factory/` — overlapping Python module (open question)

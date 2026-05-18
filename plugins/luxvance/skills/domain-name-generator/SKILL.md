---
name: domain-name-generator
description: >
  Phase A of Luxvance's domain provisioning pipeline. Generates short
  brand-prefix/suffix domain candidates, screens them against banned substrings
  and awkward-word patterns, and outputs a CSV of available .com / .co domains
  with prices via Dynadot's search API. Stops before buying — Jose reviews the
  CSV and decides to buy via Dynadot UI (today) or via a future
  domain-provision-zapmail skill (when built). Triggers on "generate domain
  names for [client]", "find available domains for [brand]", "domain candidates
  para [marca]", "necesito dominios nuevos para [cliente]".
version: 0.1.0
---

# Domain Name Generator

Phase A of Luxvance's domain provisioning. Generates short brand-aligned domain candidates and checks availability at Dynadot. Output is a CSV of available domains with prices.

**This skill does NOT buy domains.** That is Phase B (`domain-provision-zapmail`), which we will build after Phase A has produced 1-2 good lists Jose actually uses.

## Why split into two phases

Domain provisioning has three risk classes:

1. **Phase A (this skill):** name generation + availability check. No money spent, no DNS changes. Cheap to run, safe to iterate.
2. **Phase B (future):** purchase + nameserver swap + Zapmail connect + inbox creation. Spends real money, makes real DNS changes, has long wait times (4-6 hours for inbox provisioning).
3. **Phase C (manual today):** Jose buys via Dynadot UI, switches nameservers manually, adds to Zapmail manually, creates inboxes manually.

Phase A is shipped today. Phase B is deferred until the audit has reviewed `code/agency-os/08_Campaign_Factory/zapmail_client.py` more carefully and Jose has approved the cost-gating UX. Phase C is what Jose does today.

## When to use

- A Luxvance client needs more sending domains (insurance pool below 5, ramp curve is saturated, scaling a winning campaign)
- Onboarding a new client and provisioning their first batch of sending domains
- Replacing burned domains (blacklisted, flagged by `deliverability-incident-response`)

## When NOT to use

- A specific domain is already in mind (just buy it manually)
- The client name does not lend itself to short prefix+suffix combinations (e.g. `Global Food Ventures` is too long even compressed to `gfv` produces awkward outputs — surface as an issue)
- Less than 5 domains needed (Dynadot UI is faster for one-offs)

## Relationship with sibling skills + existing code

| Component | Type | Relationship |
|---|---|---|
| `domain-provision-zapmail` | Future skill (Phase B) | Consumes this skill's CSV. Buys + provisions. |
| `instantly-inbox-manager` | Skill | Manages inboxes AFTER they've been provisioned through Phases A + B. |
| `code/agency-os/08_Campaign_Factory/zapmail_client.py` | Existing Python | Transactional alerts via Zapmail. NOT domain provisioning. |
| `code/agency-os/08_Campaign_Factory/zapmail_manager.py` | Existing Python | Reports on existing Zapmail accounts. NOT domain provisioning. |
| `deliverability-incident-response` | Skill | When a domain is burned, triggers a refresh cycle that includes this skill. |

## Inputs

- **Brand keyword** (required) — e.g. `capquest`, `kcal`, `luxvance`. The shorter, the better (under 10 chars ideal).
- **Tier** (optional, default 1+2) — which prefix/suffix tiers to use (Tier 1: prefix only, Tier 2: suffix only, Tier 3: prefix+suffix)
- **TLDs** (optional, default `[.com, .co]`) — list of TLDs to check
- **Max candidates** (optional, default 100) — cap on availability checks
- **Max price** (optional, default $3.50 for .com, $30 for .co) — drop expensive premium domains

## Outputs

A CSV at `profiles/<client-slug>/domains/<YYYY-MM-DD>-candidates.csv` with columns:

| Column | Notes |
|---|---|
| `domain` | full domain (sld + tld) |
| `sld` | second-level domain (`goacme` in `goacme.com`) |
| `tld` | TLD (`.com`, `.co`) |
| `tier` | 1 / 2 / 3 — which combination tier produced this |
| `prefix` | the prefix used (empty for Tier 2) |
| `suffix` | the suffix used (empty for Tier 1) |
| `available` | true / false |
| `price_usd` | from Dynadot search response |
| `under_max_price` | true / false — `available AND price <= max_price` |
| `length` | char count (shorter is better) |
| `recommendation` | `top_pick` / `acceptable` / `expensive` / `taken` |

Surface the `top_pick` rows first when reporting to Jose.

## Naming strategy

The strategy is borrowed from Growth Engine X's `zapmail-domain-setup-public` skill and validated by Luxvance practice.

### Tier 1 — Prefix + Brand (shortest, try first)

36 prefixes:

```
go, get, try, join, find, search, explore, reach, access, boost,
team, send, email, connect, launch, start, build, discover, meet,
use, hello, hey, my, the, top, best, run, open, live, grow,
with, via, one, all, new, pro
```

For brand `acme`: `goacme.com`, `tryacme.com`, `getacme.com`, `myacme.com`, etc.

### Tier 2 — Brand + Suffix

40 suffixes:

```
hq, hub, online, today, direct, teams, projects, outreach, works,
signal, scope, flow, edge, radar, desk, global, core, base, systems,
engine, link, next, source, circle, stack, zone, path, spot, wave,
grid, point, shift, field, net, way, pulse, vault, peak, sync, lab
```

For brand `acme`: `acmehq.com`, `acmehub.com`, `acmepro.com`, `acmeflow.com`, etc.

### Tier 3 — Prefix + Brand + Suffix (use only if 1+2 yield too few)

36 × 40 = 1,440 combinations. Use only when the brand keyword produces too few Tier 1+2 hits.

For `acme`: `goacmehq.com`, `tryacmehub.com`, `getacmepro.com`.

### Filters

- **Max SLD length:** 40 characters. Shorter is always better. Aim for under 20.
- **Banned substrings:** `mega`, `ultra`, `grp` (look spammy).
- **Awkward substring check:** screen for unintended words. Examples to catch:
  - `therapist` = `the` + `rapist`
  - any profanity (run against a blocklist)
  - any English slur
- **Deduplicate globally:** never propose the same domain that already exists in Luxvance's Zapmail (read from `zapmail_clients_report.csv` if present, else skip this check).

### TLD preference

- **`.com`** — primary choice (~$10-14 on Dynadot). Best inbox trust, cleanest pattern-match for recipients.
- **`.co`** — secondary (~$8-30 depending on name). Looks professional, often available when `.com` is taken.
- **Avoid:** `.info`, `.xyz`, `.click`, `.top`, `.buzz`, `.loan`. These hurt deliverability with recipients who pattern-match on TLD.

## Flow

```
Brand keyword + options
        │
        ▼
[Phase 1] Generate Tier 1 candidates (36 prefixes × 2 TLDs = 72)
[Phase 2] Generate Tier 2 candidates (40 suffixes × 2 TLDs = 80)
[Phase 3] Apply filters (length, banned, awkward, dedupe vs Zapmail)
        │
        ▼
[Phase 4] If candidate count < 20, fall back to Tier 3 (1,440 × 2 TLDs)
[Phase 5] Cap to `max_candidates` (default 100)
        │
        ▼
[Phase 6] Cost estimate — surface ~$0.05 per 100 lookups
[Phase 7] Confirm with Jose before triggering Dynadot search
        │
        ▼
[Phase 8] Batch check availability on Dynadot (100 per request, 1s pause)
[Phase 9] Filter by `available AND price <= max_price`
        │
        ▼
[Phase 10] Sort: top_pick first (Tier 1 + length + price), then acceptable
[Phase 11] Output CSV + summary report
```

## Phase 8 detail — Dynadot batch search

**Endpoint:** `GET https://api.dynadot.com/api3.json`
**Params:**

```
key=<DYNADOT_API_KEY>
command=search
show_price=1
currency=USD
domain0=<sld>.<tld>
domain1=<sld>.<tld>
...
domain99=<sld>.<tld>
```

Max 100 domains per request. Pause 1 second between batches to avoid rate limits.

Response shape:

```json
{
  "SearchResponse": {
    "SearchResults": [
      { "DomainName": "goacme.com", "Available": "yes", "Price": "12.99" },
      { "DomainName": "tryacme.com", "Available": "no" },
      ...
    ]
  }
}
```

## Phase 11 detail — summary

```
Brand: acme
Tiers run: 1, 2
Total candidates: 152
After filters (length, banned, awkward, dedupe): 138
Availability checked: 100 (capped)

Available + under max price ($3.50 .com / $30 .co):
  top_pick (Tier 1, short, .com, cheap): 8 candidates
  acceptable: 14 candidates
  expensive (above max price): 6 candidates
  taken: 72 candidates

Top 10 picks:
  1. goacme.com      — 7 chars, $2.99
  2. tryacme.com     — 8 chars, $3.49
  3. getacme.com     — 8 chars, $2.99
  4. acmehq.com      — 7 chars, $3.49
  5. ...

Output: profiles/<client>/domains/2026-05-18-candidates.csv

Next step: review the CSV, decide which to buy. Today: buy via Dynadot UI
manually. Future: pass to domain-provision-zapmail (Phase B) for end-to-end.
```

## APIs to register

`DYNADOT_API_KEY` is required and is NOT currently in `master.env`.

To register:

1. Log into https://www.dynadot.com
2. Go to **Tools → API**
3. Enable API access, copy the API key
4. **Whitelist the IP** that runs the skill (or the Render IPs if deployed there)
5. Add `DYNADOT_API_KEY=<key>` to `credentials/master.env`

Read pattern (sandbox-safe, per `docs/SESSION_HANDOFF_2026-05-17.md`):

```python
with open('/Users/joseburneo/Luxvance_OS/credentials/master.env') as f:
    for line in f:
        if line.startswith('DYNADOT_API_KEY='):
            v = line.split('=', 1)[1].strip()
```

## Important rules

- **No purchases in this skill.** Phase A is name generation + availability only. Anyone asking "buy these now" gets redirected to the future Phase B (or the Dynadot UI today).
- **Confirm cost before running.** Dynadot search is cheap (~$0.05 per 100), but surface anyway.
- **Always run the awkward-substring check.** Domains that contain unintended slurs or profanity ship to real client inboxes and create real damage.
- **Dedupe against `zapmail_clients_report.csv`** if present. Buying a domain Luxvance already owns wastes money.
- **Output only available + under-max-price as top picks.** Surface taken / expensive as separate sections for transparency, but don't recommend them.

## Failure modes

| Failure | Recovery |
|---|---|
| Dynadot API rate-limit (429) | Wait 60 seconds, reduce batch size to 50, retry. |
| Dynadot API key missing | Surface to Jose with the registration instructions above. Stop. |
| Less than 5 candidates pass all filters | Brand keyword is too unusual or too long. Suggest a shorter / cleaner brand alias. |
| All Tier 1+2 candidates taken | Fall back to Tier 3 (3-part combinations). Surface a warning that these are longer / less professional. |
| Awkward-substring check fires on a candidate that LOOKS clean | Add the false-positive substring to an allowlist for this client's brand. |

## What's needed to ship Phase B (`domain-provision-zapmail`)

When Jose decides to ship Phase B, the additional work needed:

1. Zapmail v2 endpoints for domain-add + inbox-create (not currently used by `zapmail_client.py`). Verify scopes on the existing `ZAPMAIL_API_KEY`.
2. Resumable orchestrator pattern — checkpoint to a JSON file so the skill can pause through 4-6h waits without losing state.
3. Cost gate UX — confirm-before-execute on the purchase step, with explicit "I am about to spend $N USD" line.
4. Dynadot `command=register` integration.
5. Dynadot `command=set_ns` integration (switch nameservers to Zapmail).
6. DNS propagation waits (15-20 min after nameserver switch).
7. Zapmail "assignable" status polling (10-30 min after domain-add).
8. Zapmail inbox-create with the Luxvance default signature template.
9. CSV export of inbox credentials for Instantly import.

Estimated build effort: 5-6 hours. Defer until Phase A is producing lists Jose actually uses.

## Language

Default to the language of Jose's most recent message for the report. Domain names, API queries, and Dynadot field names stay in English.

## Learned patterns

<!-- self-improvement entries get appended here when Jose adopts a new prefix, suffix, or filter on the fly -->

When the list grows past ~10 entries, promote the durable ones into the main body of this SKILL.md.

## Related files

- `docs/INBOX_AND_DOMAIN_INFRASTRUCTURE_AUDIT.md` — full audit of what exists vs gaps for domain provisioning
- `code/agency-os/08_Campaign_Factory/zapmail_client.py` — existing transactional notifier (NOT provisioning)
- `code/agency-os/08_Campaign_Factory/zapmail_manager.py` — existing reporting (NOT provisioning)
- `code/agency-os/08_Campaign_Factory/zapmail_clients_report.csv` — read for dedupe of already-owned domains
- Future `domain-provision-zapmail/SKILL.md` — Phase B, consumes this skill's CSV

---
name: enrich-and-verify-leads
description: >
  Verifies email deliverability for a list of leads using the MillionVerifier → BounceBan
  waterfall, upserts results to the Luxvance Contact Database (Supabase), and applies the
  60-day freshness rule. Triggers on "verifica estos leads", "verify these emails",
  "corre el waterfall sobre [csv]", "limpia los emails de [campaña]", "re-verifica los
  leads viejos", "enrich leads from [path]", "import [csv] to master DB and verify",
  or any request that takes raw email leads and needs them turned into a deliverable-only
  campaign-ready list.
version: 0.1.0
---

# Enrich and Verify Leads

Takes a CSV or list of email leads, upserts them into the Luxvance Contact Database master, runs the verification waterfall, and outputs a deliverable-only list ready for Instantly.

## When to use

- A new Apollo / Apify export needs to be imported + verified
- Before pushing leads to an Instantly campaign — must confirm freshness
- Re-verification of stale leads (>60 days since last check)
- Lazy verification: only verify leads that match a campaign's ICP, never bulk

## When NOT to use

- For non-Luxvance contact databases — this assumes the Supabase project `nbwbauomozeokflntcwa`
- For verifying a single email — just use `curl` against MillionVerifier directly
- For bulk re-verifying the entire master DB (456k contacts) — that's ~$275 and explicitly out of scope per [LEAD_ENRICHMENT_PIPELINE.md](../../docs/LEAD_ENRICHMENT_PIPELINE.md)

## How it works

The waterfall:

```
CSV/list of leads
       │
       ▼
1. UPSERT to contacts table  (bulk-upsert-contacts edge function)
       │
       ▼
2. SELECT leads needing verification:
       email_verified_at IS NULL
       OR email_verified_at < now() - interval '60 days'
       │
       ▼
3. Run Million Verifier on those emails (20 workers, User-Agent header)
       │   ├─ ok → email_status='deliverable', email_verified_by='million_verifier'
       │   ├─ catch_all → go to step 4
       │   ├─ invalid → email_status='bad'
       │   └─ unknown/error → email_status='unknown'
       │
       ▼
4. Run BounceBan on the catch_all subset (specialized for catch-all servers)
       │   ├─ deliverable → email_status='deliverable', email_verified_by='bounceban'
       │   ├─ undeliverable → email_status='bad'
       │   └─ risky/unknown → keep as catch_all / unknown
       │
       ▼
5. is_sendable column auto-flips to TRUE for newly-deliverable leads
       │
       ▼
6. Final deliverable list available via contacts_for_send VIEW
```

## Conventions (must follow)

1. **Set `User-Agent: curl/7.88.1` on Million Verifier requests.** Default Python urllib UA gets 403 Forbidden after small bursts.
2. **Stay at ≤20 concurrent requests** for MV. Bursts >150 req/sec trigger silent throttle.
3. **Never trust Apollo's "deliverable" tag.** Run MV anyway — 72% of Apollo-tagged deliverable fail MV in our tests.
4. **Apply 60-day rule.** Leads verified >60 days ago must be re-verified before push.
5. **Lazy verification only.** Never bulk-process the full DB; only candidates for an active campaign.

## Environment variables (from `credentials/master.env`)

| Variable | Use |
|---|---|
| `MILLIONVERIFIER_API_KEY` | Primary email verifier |
| `BOUNCEBAN_API_KEY` | Catch-all resolver |
| `SUPABASE_URL` | Agency OS project URL (https://sgaeggmkmipcoikzqwpy.supabase.co) |
| `SUPABASE_SERVICE_KEY` | Bypasses RLS to call the master-upsert RPC |

Migrated 2026-05-28 from the standalone Contact Database (`nbwbauomozeokflntcwa`).
All scripts now POST to the `upsert_master_contacts(jsonb)` RPC inside Agency OS
which writes to `core.contacts` after the canonical field transforms (industry
→ primary_industry, linkedin_url → linkedin_profile, verified_by mapped to
MV/BB or NULL).

## Workflow

### Scenario A: Fresh CSV from Apify scrape

```bash
# 1. Validate CSV has required columns (email at minimum)
python3 scripts/validate_csv.py /path/to/leads.csv

# 2. UPSERT to master DB (Agency OS core.contacts via RPC)
python3 scripts/bulk_upsert_to_supabase.py /path/to/leads.csv

# 3. Run waterfall on unverified or stale leads
python3 scripts/run_waterfall.py --source-batch "$(basename /path/to/leads.csv .csv)"

# 4. Export final deliverable list
python3 scripts/export_for_instantly.py \
  --batch-tag "$(basename /path/to/leads.csv .csv)" \
  --output /tmp/instantly_push.csv
```

### Scenario B: Re-verify stale leads for an upcoming campaign

```bash
# Pull candidates matching ICP from contacts_for_send (already filtered by 60d)
# If short, pull from contacts_needing_reverification, run waterfall, then include
python3 scripts/refresh_stale_for_icp.py \
  --country "United Kingdom" \
  --seniority "director,vp,c_suite,owner,partner" \
  --min-employees 10 --max-employees 100 \
  --target-count 5000 \
  --output /tmp/campaign_candidates.csv
```

## Scripts in this skill

| Script | Purpose |
|---|---|
| `scripts/bulk_upsert_to_supabase.py` | UPSERT a CSV of leads to `contacts` via edge function |
| `scripts/run_waterfall.py` | Run MV → BB waterfall on a set of emails (or on stale ones) |
| `scripts/run_million_verifier.py` | Standalone MV run (used by waterfall and refresh) |
| `scripts/run_bounceban.py` | Standalone BB run (used by waterfall on catch_all) |
| `scripts/refresh_stale_for_icp.py` | Lazy verify: pull ICP candidates, refresh stale ones, output deliverable CSV |
| `scripts/export_for_instantly.py` | Export `contacts_for_send` to Instantly-shaped CSV |

All scripts use `User-Agent: curl/7.88.1` for MV calls. All use the `upsert_master_contacts` RPC in Agency OS for writes (security_definer bypasses RLS safely).

## Cost estimates

- 1,000 unverified leads → ~$0.60 MV + ~$1.00 BB (if ~20% become catch_all) = **~$1.60 total**
- 5,000 candidates → **~$3-5 verification cost** (typical campaign)
- Never run on >50k at once unless explicitly approved

## Related

- **Reference doc:** [LEAD_ENRICHMENT_PIPELINE.md](../../docs/LEAD_ENRICHMENT_PIPELINE.md)
- **Sibling skill:** `cleanup-completed-campaigns` (frees Instantly slots after sending)
- **Credentials:** `credentials/master.env`

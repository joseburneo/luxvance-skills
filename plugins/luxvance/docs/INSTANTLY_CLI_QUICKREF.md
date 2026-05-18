# Instantly CLI Quick Reference

**CLI:** [`bcharleson/instantly-cli`](https://github.com/bcharleson/instantly-cli) — 156 commands across 31 API groups.
**Install:** Zero-install via `npx instantly-cli <command>` OR global install `npm install -g instantly-cli`.
**Auth:** Single env var `INSTANTLY_API_KEY`. For Luxvance's 6 workspaces, wrap each call with the right per-client key.

This doc is referenced by skills that touch Instantly. Read it once, then the skills point back here so we don't duplicate the patterns.

---

## When to use CLI vs MCP

| Scenario | Use | Why |
|---|---|---|
| Single conversational query ("which CapQuest inbox sent the most this week?") | **MCP** (`mcp__instantly-capquest__*`) | One call, returns small JSON, Claude reasons over it inline. Cheap. |
| Bulk read (analytics across 100+ inboxes, all campaigns fleet-wide) | **CLI** | One bash call returns everything. MCP would need N tool calls = N× the tokens. |
| Bulk write (tag 50 inboxes, set warmup config in batch, upload 1,000 leads) | **CLI** | The CLI's `bulk-add` etc. handle internal batching. MCP can't batch. |
| Operation that already has a Luxvance Render cron handling it | **NEITHER from skills** | Let the cron own it. The skill describes the data the cron produces, doesn't duplicate the work. |
| Exploring something Jose hasn't seen before | **MCP** | Conversational back-and-forth wins. |

**Rule of thumb:** if the operation touches more than 20 rows OR runs across multiple workspaces in one pass, use CLI. Otherwise MCP.

---

## Per-workspace key wrapping

Luxvance has 6 Instantly workspaces, each with its own API key in `credentials/master.env`:

```
INSTANTLY_API_KEY_LUXVANCE
INSTANTLY_API_KEY_CAPQUEST
INSTANTLY_API_KEY_KCAL
INSTANTLY_API_KEY_CONNECT_RESOURCE
INSTANTLY_API_KEY_GLOBAL_FOOD_VENTURES
INSTANTLY_API_KEY_REMLY
```

The CLI reads a single `INSTANTLY_API_KEY`. So wrap each call:

```bash
# Load from master.env
export INSTANTLY_API_KEY_CAPQUEST=$(grep '^INSTANTLY_API_KEY_CAPQUEST=' /Users/joseburneo/Luxvance_OS/credentials/master.env | cut -d= -f2)

# Run a CLI command against that workspace
INSTANTLY_API_KEY="$INSTANTLY_API_KEY_CAPQUEST" npx instantly-cli accounts list
```

Helper alias (add to your shell profile):

```bash
luxvance-instantly() {
  local client="$1"; shift
  local key_var="INSTANTLY_API_KEY_$(echo $client | tr '[:lower:]' '[:upper:]')"
  local key=$(grep "^${key_var}=" /Users/joseburneo/Luxvance_OS/credentials/master.env | cut -d= -f2)
  INSTANTLY_API_KEY="$key" npx instantly-cli "$@"
}

# Usage:
luxvance-instantly capquest campaigns list
luxvance-instantly kcal accounts list
```

---

## Top commands by use case

### Inbox management (used by `instantly-inbox-manager`)

```bash
# List all accounts across a workspace
npx instantly-cli accounts list

# Get one account's health
npx instantly-cli accounts get --email "sales@capquest-hq.co"

# Bulk enable warmup
npx instantly-cli accounts warmup-enable --account-ids "id1,id2,id3"

# Bulk disable warmup (for active inboxes)
npx instantly-cli accounts warmup-disable --account-ids "id1,id2,id3"

# Test inbox vitals (SMTP + IMAP connectivity)
npx instantly-cli accounts test-vitals --account-ids "id1,id2"

# Pause / resume an inbox
npx instantly-cli accounts pause --email "..."
npx instantly-cli accounts resume --email "..."

# Mark a flagged inbox as fixed (clears the flag, doesn't re-test)
npx instantly-cli accounts mark-fixed --email "..."

# Update tags, signature, daily limit, etc.
npx instantly-cli accounts update --email "..." --tags "active" --daily-limit 30
```

### Analytics + reporting (used by `positive-reply-scoring`, `deliverability-audit`)

```bash
# Campaign-level analytics (all campaigns)
npx instantly-cli analytics campaign-overview

# One campaign's detailed analytics
npx instantly-cli analytics campaign --id <campaign-id>

# Per-step analytics (open/reply/bounce by sequence step)
npx instantly-cli analytics campaign-steps --id <campaign-id>

# Daily breakdown for one campaign
npx instantly-cli analytics daily-campaign --id <campaign-id> --start 2026-04-01 --end 2026-05-18

# Daily breakdown for one account
npx instantly-cli analytics daily-account --email "..." --start 2026-04-01

# Warmup analytics (network performance)
npx instantly-cli analytics warmup --email "..."
```

### Leads management (used by `launch-instantly-campaign`)

```bash
# Bulk add up to 1,000 leads at a time
npx instantly-cli leads bulk-add --campaign-id <id> --leads-file leads.json

# List leads from a campaign
npx instantly-cli leads list --campaign-id <id>

# Find which campaign(s) contain a given email
npx instantly-cli campaigns search-by-contact --email "..."

# Move leads between campaigns
npx instantly-cli leads move --lead-ids "..." --to-campaign <id>

# Bulk delete
npx instantly-cli leads bulk-delete --lead-ids "..."
```

### Campaign management

```bash
# Create a campaign
npx instantly-cli campaigns create --name "..." --config-file campaign.json

# Activate / pause / delete
npx instantly-cli campaigns activate --id <id>
npx instantly-cli campaigns pause --id <id>
npx instantly-cli campaigns delete --id <id>

# Duplicate (great for cloning a winning campaign to more inboxes)
npx instantly-cli campaigns duplicate --id <id> --new-name "..."
```

### Inbox placement testing (used by `deliverability-audit`)

```bash
# Create a placement test
npx instantly-cli inbox-placement create --name "..." --senders "id1,id2"

# Get test results
npx instantly-cli inbox-placement get --test-id <id>

# Analytics aggregate
npx instantly-cli inbox-placement analytics-stats-by-test --test-id <id>
```

### Workspace + billing

```bash
# Credit balance
npx instantly-cli workspace credits

# Plan details
npx instantly-cli workspace billing plan-details

# Audit logs (who did what)
npx instantly-cli audit-logs list --start 2026-05-01
```

---

## Common patterns

### Pull all campaigns across all 6 workspaces (efficient fleet query)

```bash
for client in luxvance capquest kcal connect_resource global_food_ventures remly; do
  key_var="INSTANTLY_API_KEY_$(echo $client | tr '[:lower:]' '[:upper:]')"
  key=$(grep "^${key_var}=" /Users/joseburneo/Luxvance_OS/credentials/master.env | cut -d= -f2)
  echo "=== $client ==="
  INSTANTLY_API_KEY="$key" npx instantly-cli campaigns list --json | jq '.[] | {id, name, status}'
done
```

vs the MCP equivalent: 6 tool calls × N campaigns each = lots of context. The bash version: 1 stream of small JSON.

### Bulk inbox tag rotation

```bash
# Move 20 insurance inboxes to active in CapQuest workspace
INSTANTLY_API_KEY="$INSTANTLY_API_KEY_CAPQUEST" npx instantly-cli accounts update \
  --account-ids "id1,id2,...,id20" \
  --tags "active"

# Disable warmup on those same 20 inboxes
INSTANTLY_API_KEY="$INSTANTLY_API_KEY_CAPQUEST" npx instantly-cli accounts warmup-disable \
  --account-ids "id1,id2,...,id20"
```

### Bulk lead upload to a DRAFT campaign

```bash
INSTANTLY_API_KEY="$INSTANTLY_API_KEY_LUXVANCE" npx instantly-cli leads bulk-add \
  --campaign-id <campaign-id> \
  --leads-file enriched_leads.json
```

For lists over 1,000 leads, batch in chunks of 1,000 with a simple loop:

```bash
jq -c '.[]' enriched_leads.json | split -l 1000 - batch_
for f in batch_*; do
  jq -s '.' "$f" > "${f}.json"
  INSTANTLY_API_KEY="$INSTANTLY_API_KEY_LUXVANCE" npx instantly-cli leads bulk-add \
    --campaign-id <id> --leads-file "${f}.json"
  rm "$f" "${f}.json"
done
```

---

## What this CLI does NOT cover

These operations stay in MCP or other tools because no CLI command exists:

- Some webhook event introspection (use MCP `webhook_events_*` instead)
- Some workspace-group member operations (rare, MCP is fine)
- Anything outside Instantly (Supabase queries → use `mcp__execute_sql`, Notion → Notion MCP, etc.)

---

## Skills that reference this doc

- `instantly-inbox-manager` — bulk inbox operations
- `launch-instantly-campaign` — bulk lead upload + campaign create
- `deliverability-audit` — fleet-wide health queries
- `positive-reply-scoring` — bulk reply pull (when reply count > 200)
- `cold-email-weekly-rhythm` — schedules when each CLI command runs

---

## Discovery + maintenance

```bash
# See all commands available
npx instantly-cli --help

# See help for a specific command group
npx instantly-cli campaigns --help
npx instantly-cli accounts --help

# Version check (run this periodically — bcharleson ships updates often)
npm list -g instantly-cli 2>/dev/null || npx instantly-cli --version
```

When `bcharleson/instantly-cli` releases a new version with new commands, this doc may go stale. Re-check the [README](https://github.com/bcharleson/instantly-cli) quarterly.

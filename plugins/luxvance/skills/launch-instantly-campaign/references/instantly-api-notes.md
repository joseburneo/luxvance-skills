# Instantly API + MCP — operator notes

This file is the quick reference for the Instantly endpoints the deployer hits. Keep it updated as the MCP surface or Instantly's v2 API changes.

## Two ways to reach Instantly

1. **MCP tools (preferred for skill execution).** Wired into Claude Code for every Luxvance workspace. Namespace pattern: `mcp__instantly-<workspace>__<resource>_<action>`. Authentication, retries, and schema validation are handled by the MCP.
2. **Direct REST API (fallback).** `https://api.instantly.ai/api/v2/...` with `Authorization: Bearer <INSTANTLY_API_KEY>`. Use when running outside Claude Code or for very large bulk operations the MCP times out on.

The deployer uses MCP by default. The TS fallback script is not built yet; add it if MCP-only proves too slow for 10K+ lead uploads.

## Workspace MCPs available

| Workspace | MCP namespace |
|---|---|
| Luxvance (master) | `mcp__instantly-luxvance__` |
| CapQuest | `mcp__instantly-capquest__` |
| Connect Resources | `mcp__instantly-connect-resources__` |
| Global Food Ventures | `mcp__instantly-gfv__` |
| Kcal | `mcp__instantly-kcal__` |
| Remly | `mcp__instantly-remly__` |

The flow is identical for every workspace. Only the namespace prefix changes.

## Tool map by deployer phase

### Phase 4 — Create campaign shell

| Tool | Purpose |
|---|---|
| `campaigns_create` | POST a new campaign with at least a name. Returns campaign UUID. |

Minimum payload: `{ "name": "<campaign name>" }`. Some MCPs also accept the sequence and schedule inline; the deployer keeps them separate for cleaner error handling.

### Phase 5 — Configure sequence + variants

| Tool | Purpose |
|---|---|
| `campaigns_update` | PATCH the campaign with `sequences` array. Each sequence has `step`, `delay_days`, and `variants[]` with `label`, `subject`, `body`. |

The MCP accepts spintax `{a|b|c}` and merge fields `{{field}}` in `body` verbatim. Do NOT URL-encode or escape.

### Phase 6 — Attach sending accounts

| Tool | Purpose |
|---|---|
| `accounts_list` | Returns array of all sending accounts with status, tags, warmup, daily sent count. |
| `campaigns_update` | PATCH with `email_account_ids` array of UUIDs to attach. |

Inbox selection logic in the deployer (Phase 6):
1. List all accounts.
2. Filter where `tags` includes `<requested_tag>` AND account is not paused AND warmup is not stalled.
3. Sort ascending by `daily_sent_count` (LRU - least-recently-used first).
4. Take first N.

### Phase 7 — Set schedule

| Tool | Purpose |
|---|---|
| `campaigns_update` | PATCH with the schedule fields. |

Expected fields (Instantly v2 naming):
- `timezone` (string, IANA)
- `days_of_week` (array of integers 1-7, 1=Mon)
- `from_hour`, `to_hour` (`HH:MM` strings)
- `delay_between_emails_minutes` (integer)
- `max_new_leads_per_day` (integer, per inbox)
- `stop_on_reply` (boolean, always true)
- `track_opens` (boolean, always false)
- `track_clicks` (boolean, always false)

If the MCP rejects any of these field names, check the current schema with the Instantly developer docs and update both this file and the deployer's `SKILL.md`.

### Phase 8 — Upload leads

| Tool | Purpose |
|---|---|
| `leads_bulk_add` | POST array of lead objects to a campaign. Returns inserted IDs. |

Each lead object shape (CSV columns are snake_case; the deployer translates to Instantly's native field names before upload):

```json
{
  "email": "jane@acme.com",
  "firstName": "Jane",
  "lastName": "Smith",
  "companyName": "Acme Corp",
  "custom_variables": {
    "companyDomain": "acme.com",
    "title": "vp of sales",
    "linkedinUrl": "https://linkedin.com/in/jane",
    "Variable 1": "b2b software firm",
    "Variable 2": "founders at b2b software firms",
    "situation_line": "...",
    "value_line": "...",
    "cta_line": "..."
  }
}
```

The exact field names on the Instantly side (`firstName` vs `first_name`, `Variable 1` vs `variable_1`) matter because they must match the merge fields used in the campaign body. The deployer's mapping table is in `leads-csv-schema.md`. If Instantly's MCP renames any of these fields in a future version, update the mapping in both places.

Batch size: 100 leads per call. Retry once on transient failure (5xx, 429). On second failure, log the batch and continue; do not halt the entire upload.

### Phase 9 — Verify

| Tool | Purpose |
|---|---|
| `campaigns_get` | Returns the campaign object. Read back name, sequence count, lead count, status. |
| `campaigns_pause` | Safety net: pause the campaign if it somehow lands as active. |

The deployer NEVER calls `campaigns_activate`. That is a manual click in the Instantly UI, by design.

## Spintax syntax

Instantly: `{{RANDOM|option1|option2|option3}}`. Double curly braces, `RANDOM` keyword, pipe-separated options. This is NOT the same as Smartlead's `{a|b|c}` syntax. If the body uses Smartlead-style braces, Instantly renders the literal text including the braces and pipes (not what we want).

Merge fields: `{{fieldName}}` or `{{Field Name}}`. Double curly braces, mixed case allowed, spaces allowed inside the braces. Examples already live in Luxvance's Instantly workspaces:

- `{{firstName}}`, `{{lastName}}`, `{{companyName}}` (camelCase)
- `{{Variable 1}}`, `{{Variable 2}}` (capitalized with space, Clay-pattern variables)
- `{{accountSignature}}` (Instantly built-in, renders the sending inbox's signature)
- `{{situation_line}}`, `{{value_line}}`, `{{cta_line}}` (snake_case, new AI-generated fields)

The deployer translates CSV column names (always snake_case) to Instantly field names on upload. See `leads-csv-schema.md` for the full mapping. Both spintax and merge field syntax pass through MCP and API verbatim. Do not escape, encode, or normalize.

## Region-specific notes

Luxvance ships campaigns across NAM, EMEA, GCC, LATAM. Each region needs its own schedule timezone:

| Region | Timezone (IANA) | Typical hours |
|---|---|---|
| NAM | `America/New_York` (ET) or `America/Los_Angeles` (PT) | 08:00-17:00 |
| EMEA continental | `Europe/Brussels` or `Europe/Madrid` | 08:00-17:00 |
| EMEA UK/IE | `Europe/London` | 08:00-17:00 |
| GCC | `Asia/Dubai` | 09:00-17:00 (note Sun-Thu work week: `days: [7,1,2,3,4]`) |
| LATAM | `America/Bogota` or `America/Mexico_City` | 08:00-17:00 |

The deployer reads `schedule.timezone` and `schedule.days` from variants.yaml verbatim. The copywriter is responsible for setting the right region.

## Known gotchas

- **Workspace mismatch.** Calling `mcp__instantly-luxvance__campaigns_create` while Jose intended Kcal puts the campaign in the wrong workspace. The deployer reads the workspace from the campaign name's client prefix; if ambiguous, ask Jose once.
- **Tag must exist before launch.** If the requested tag has zero matching inboxes, the campaign has no senders and Instantly silently leaves it inert. The deployer aborts with a clear error in this case (Phase 6).
- **Lead deduplication.** Instantly deduplicates per campaign server-side, but does NOT deduplicate against other campaigns. If the same email is in two simultaneous campaigns, the prospect gets hit twice. Use the master Contact DB (`enrich-and-verify-leads`) to enforce cross-campaign dedup BEFORE upload.
- **Tracking pixels.** The deployer always sets `track_opens: false` and `track_clicks: false`. In 2026, tracking pixels hurt deliverability across Gmail and Outlook, and we do not need open data for the kinds of campaigns Luxvance ships. Do not override this.
- **Threading.** Step 2 onward with empty `subject` threads under Step 1. Step 3 typically starts a new thread (non-empty subject). Verify in the Instantly UI before hitting Start.

## When the API changes

Instantly ships breaking API changes occasionally. If a tool call returns an unexpected error:

1. Check the Instantly developer docs at `https://developer.instantly.ai/api/v2`.
2. Update this file with the new field names or payload shape.
3. Update the deployer's `SKILL.md` Phase descriptions to match.
4. If the MCP is out of date, file an issue or check for an updated version of the MCP server.

Do not work around API changes silently. Update the docs at the same time as the code.

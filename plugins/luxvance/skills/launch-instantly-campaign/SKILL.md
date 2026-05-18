---
name: launch-instantly-campaign
description: "Production deployer that takes a `variants.yaml` (from build-campaign) and a `leads.csv` and creates a DRAFT campaign directly in Instantly via the Luxvance MCP — no Clay, no manual paste. Builds the sequence with spintax bodies, attaches sending accounts by tag, uploads leads in batches with custom variables, sets the schedule, then stops at DRAFT so Jose reviews and hits Start in the Instantly UI. Triggers on 'launch the campaign in Instantly', 'sube esto a Instantly', 'ship it to Instantly', 'crea el draft', 'push to Instantly', 'arma la campaña en Instantly' and similar."
---

# Launch Instantly Campaign

## Role

You are the deployer. The strategic thinking is done upstream by `campaign-intelligence`. The copy and Clay/Instantly assets are produced by `build-campaign`. Your only job is to take the finished `variants.yaml` plus a verified `leads.csv` and create a DRAFT campaign in Instantly via the Luxvance MCP tools, without manual paste.

You are not a copywriter, not a strategist, not an analyst. You assemble the API calls and verify the result.

## Why this skill exists

The old Luxvance flow ended at `build-campaign` producing a paste-kit that Marko or Ana then keyed into Clay for filters + variables, then into Instantly for the copy. That introduces two costs we want to remove:

1. **Clay dependency.** Clay charges per row, the Sculpture step adds latency, and every campaign sits in Clay's queue. For trigger-based or fast-iteration campaigns we want Claude Code to be the one source of truth.
2. **Manual paste latency.** Even with a well-formatted kit, 5 to 10 minutes per campaign goes into copying blocks into the right tools. At 5 campaigns a week per client across 6 clients, that's hours of human time we can eliminate.

This skill is the first piece of the Clay-independent pipeline. Future siblings will replace Clay's filtering and enrichment too, but the deployer is the linchpin: nothing else matters if we still need a human to paste into Instantly.

This skill mirrors the Growth Engine X pattern (`/smartlead-campaign-upload-public`) but adapted to our stack:

| Growth Engine X | Luxvance |
|---|---|
| Smartlead | Instantly |
| `SMARTLEAD_API_KEY` env var, direct REST | `mcp__instantly-luxvance__*` MCP tools |
| `--leads`, `--variants` CLI flags | Claude reads files via Read, calls MCP step by step |
| TypeScript `upload.ts` script | Markdown skill + optional fallback script |

## Inputs

Two files, both produced upstream:

1. **`variants.yaml`** — produced by `build-campaign` (next iteration) or written by hand. Schema in `references/variants-schema.yaml`. Defines:
   - campaign name (Luxvance naming convention)
   - schedule (timezone, days, hours, throttle, max new leads per inbox per day)
   - sending account selection (Instantly tag plus count, LRU by daily sent volume)
   - sequences with steps and A/B/C variants (subject plus spintax body)

2. **`leads.csv`** — verified deliverable list. Schema in `references/leads-csv-schema.md`. Required columns: `email`, `first_name`, `last_name`, `company_name`. Allowed optional columns map to Instantly custom variables: `company_domain`, `title`, `linkedin_url`, `variable_1`, `variable_2`, `situation_line`, `value_line`, `cta_line`.

Any column not on the allowed list aborts the upload with a clear error. This is intentional: it prevents accidental PII leaks and silent merge-field mismatches.

## What this skill does NOT do

- Does **not** write copy. That is `build-campaign`.
- Does **not** verify emails. That is `enrich-and-verify-leads` (MillionVerifier plus BounceBan waterfall). The CSV is assumed to be already verified.
- Does **not** activate the campaign. Always stops at DRAFT. Jose hits Start manually in the Instantly UI after reviewing.
- Does **not** create or warm sending accounts. Those are provisioned in advance and tagged in Instantly.
- Does **not** modify Notion, Supabase, or Drive.

## Hard rule: DRAFT only, always

The skill must never call `mcp__instantly-luxvance__campaigns_activate` (or the CLI equivalent `npx instantly-cli campaigns activate`). Even if Jose explicitly asks "and start it" in the same message, refuse and explain: cold-email launches need a 30-second human review of subject lines, inbox count, lead count, and schedule before going live. The 30 seconds saved by auto-activating is not worth the risk of sending a malformed campaign to 5,000 prospects on the wrong inboxes.

If Jose insists, point him at the Instantly URL printed at the end. He hits Start in the UI in two clicks.

## Efficiency: CLI vs MCP

This skill picks the right tool per phase to minimize tokens:

| Phase | Tool | Why |
|---|---|---|
| Phase 1-3 (input validation, confirm shape) | local code, no API | Cheap |
| Phase 4 campaign create + sequence config | MCP `campaigns_create` | Single call, structured object |
| Phase 5 attach inboxes by tag | MCP `accounts_list` + filter | Small result, conversational decision (which to pick if too many) |
| Phase 6 **bulk lead upload** | **CLI `npx instantly-cli leads bulk-add`** | The CLI's bulk-add handles up to 1,000 leads per call. For 2,000+ leads, batching in CSV is way more efficient than N MCP calls. |
| Phase 7 schedule + settings | MCP `campaigns_update` | Single call |
| Phase 8 verify DRAFT state | MCP `campaigns_get` | Single read, conversational confirmation |

See [`docs/INSTANTLY_CLI_QUICKREF.md`](../../../docs/INSTANTLY_CLI_QUICKREF.md) for the exact CLI commands and the per-workspace `INSTANTLY_API_KEY` wrapping pattern.

Token impact of the CLI for Phase 6: a 2,566-lead campaign that would have been ~26 MCP calls (100 leads each) becomes 3 CLI calls (1,000 each). The MCP version sends 26× the request JSON through Claude's context; the CLI version sends 3.

## The flow

Run these phases in order. Do not skip validation phases even if the inputs "look obvious."

### Phase 1: Locate inputs

If Jose says "use the campaign from earlier" or similar, infer the file paths from the conversation context. The conventional layout is:

```
profiles/<client-slug>/campaigns/<campaign-slug>/variants.yaml
profiles/<client-slug>/campaigns/<campaign-slug>/leads.csv
```

If Jose gives an absolute path or a paste of YAML inline, use that. If you cannot find the files after one reasonable attempt, ask Jose where they live. One question, not three.

### Phase 2: Validate locally before any API call

Before touching Instantly, validate both files. Failing fast here saves Jose 60 seconds and a half-finished campaign in Instantly.

**variants.yaml checks:**

- Top-level `name`, `schedule`, `inbox_selection`, `sequences` all present
- `schedule.timezone` is a valid IANA string
- `schedule.days` is an array of integers 1 to 7
- `schedule.start_hour` and `schedule.end_hour` are `HH:MM` strings, end after start
- `inbox_selection.tag` is a non-empty string
- `inbox_selection.count` is a positive integer
- `sequences` is non-empty, each step has `step`, `delay_days`, and at least one variant
- Every variant has `label` (A, B, or C), `subject` (string, may be empty for threaded follow-ups), and non-empty `body`
- No em-dashes in any subject or body string. Replace `—` with ` - ` if found. Em-dashes are a Luxvance voice violation and Instantly does not normalize them.
- All spintax blocks `{{RANDOM|a|b|c}}` have at least 2 options. Single-option spintax is a copy-paste error. Note: Instantly's spintax syntax is `{{RANDOM|...}}`, not Smartlead's `{a|b|c}`. The `RANDOM` keyword inside double curly braces is required.
- All merge fields `{{field}}` reference either a required field (`{{firstName}}`, `{{lastName}}`, `{{companyName}}`, `{{accountSignature}}`) or a custom variable derived from an optional CSV column. The CSV column to Instantly merge field translation is documented in `references/leads-csv-schema.md`. Flag missing merges as a hard error before upload.

**leads.csv checks:**

- All four required columns present: `email`, `first_name`, `last_name`, `company_name`
- Any extra columns must be on the allowlist in `references/leads-csv-schema.md`. Reject unknown columns with a clear error pointing at the schema.
- Email column passes basic regex (`x@y.z`). Do not re-verify deliverability here.
- Zero duplicate emails inside the file. If duplicates exist, report the count and ask Jose whether to dedupe automatically (keep first occurrence) or stop.
- Lead count below 25,000. Above that, ask Jose to split into multiple campaigns. Instantly handles bigger campaigns but the deliverability math gets messy.

If any check fails, print the error, the offending row or field, and stop. Do not proceed.

### Phase 3: Confirm shape with Jose (one sentence)

Once validation passes, summarize what is about to happen in ONE sentence and ask one binary confirmation:

> About to create DRAFT campaign `Luxvance - NAM - Sales Leaders - New in Role - W18` in Instantly Luxvance workspace: 1 sequence step, 3 variants (A/B/C), 20 inboxes tagged `active`, schedule M-F 08:00-17:00 America/New_York with 30 new leads/inbox/day, 1,847 verified leads. Proceed?

If Jose says yes (or "go", "ship it", "dale"), proceed. Otherwise stop.

### Phase 4: Create the campaign shell

Call `mcp__instantly-luxvance__campaigns_create` with at minimum the campaign name from the YAML. Capture the returned `id` (Instantly's UUID). All subsequent calls reference this ID.

If the create call returns an error, abort. Do not retry blindly; show Jose the error and ask.

### Phase 5: Configure the sequence with variants

Call `mcp__instantly-luxvance__campaigns_update` on the new campaign ID. Construct the `sequences` payload to mirror the YAML:

- Each `step` in YAML becomes one sequence step
- `delay_days` from YAML maps to Instantly's step delay
- Each variant under that step becomes a variant in Instantly's A/B/C structure, with `subject` and `body` populated verbatim from YAML

Critical: the `body` field goes in exactly as-is, with spintax `{{RANDOM|a|b|c}}` and merge field `{{firstName}}` / `{{Variable 1}}` syntax intact. Both use double curly braces; the `RANDOM` keyword distinguishes spintax from a merge field. Do NOT escape, encode, or normalize the braces or the keyword.

If the YAML body uses `\n` for line breaks, convert to actual newlines before sending. Instantly stores `body` as plain text with embedded `\n` or `<br>` depending on the API version. Check `references/instantly-api-notes.md` for the current expected format and adjust if Instantly's API changed.

### Phase 6: Attach sending accounts by tag

This is the inbox selection logic, modeled on GEX's pattern.

1. Call `mcp__instantly-luxvance__accounts_list` to fetch all sending accounts.
2. Filter to accounts that:
   - Have the requested tag (`inbox_selection.tag` from YAML) attached
   - Are not paused
   - Are warmed (warmup status complete or in maintenance phase, not still ramping)
3. Sort ascending by daily sent count (LRU - least-recently-used inboxes go first). This balances send volume across the available pool.
4. Take the first N inboxes where N = `inbox_selection.count` from YAML.
5. If fewer than N healthy inboxes match the tag, attach all available and print a warning: `Only 14 inboxes matched tag=active (requested 20). Proceeding with what is available.`
6. If zero match, abort with a clear error pointing Jose at the Instantly accounts tab. Do not silently launch a campaign with no inboxes.
7. Call `mcp__instantly-luxvance__campaigns_update` (or the dedicated email accounts attachment endpoint if exposed by MCP) to attach the selected account IDs.

### Phase 7: Set the schedule

Call `mcp__instantly-luxvance__campaigns_update` with the schedule from YAML:

- `timezone`: pass through
- `days_of_week`: convert YAML's `[1,2,3,4,5]` (1=Mon) to whatever format the MCP expects, usually identical
- `from_hour` / `to_hour`: pass through as `HH:MM`
- `delay_between_emails_minutes`: from YAML's `min_time_btw_emails`
- `max_new_leads_per_day`: from YAML's `max_leads_per_day`
- `stop_on_reply`: always `true`. Cold email never overrides this.
- `track_opens` / `track_clicks`: always `false`. Tracking pixels and link tracking hurt deliverability in 2026 even for warm relationships, and we do not need open data for the kinds of campaigns Luxvance ships.

### Phase 8: Upload leads in batches

Read the CSV. For each batch of 100 leads:

1. Build a JSON array of lead objects. CSV columns are snake_case, but Instantly merge fields use Instantly's native naming (camelCase or spaced). The deployer translates between them. Required mapping:

   | CSV column | Instantly field | Merge syntax in body |
   |---|---|---|
   | `email` | `email` | (recipient address, not a merge) |
   | `first_name` | `firstName` | `{{firstName}}` |
   | `last_name` | `lastName` | `{{lastName}}` |
   | `company_name` | `companyName` | `{{companyName}}` |
   | `company_domain` | `companyDomain` | `{{companyDomain}}` |
   | `title` | `title` | `{{title}}` |
   | `linkedin_url` | `linkedinUrl` | `{{linkedinUrl}}` |
   | `variable_1` | `Variable 1` | `{{Variable 1}}` |
   | `variable_2` | `Variable 2` | `{{Variable 2}}` |
   | `situation_line` | `situation_line` | `{{situation_line}}` |
   | `value_line` | `value_line` | `{{value_line}}` |
   | `cta_line` | `cta_line` | `{{cta_line}}` |

   Why two naming conventions? Luxvance's Instantly workspace already uses camelCase for the standard fields (`firstName`, `companyName`) and `Variable 1`/`Variable 2` for the Clay-style pattern. The deployer keeps that exact naming on the Instantly side so existing campaigns and account signatures still work. CSVs use snake_case for clean parsing.

   Standard fields (`email`, `first_name`, `last_name`, `company_name`) go in the top-level lead object after translation. Everything else goes under `custom_variables` (or whatever Instantly's MCP names the per-lead variable bag) with the Instantly-side name as the key.

2. Call `mcp__instantly-luxvance__leads_bulk_add` (or the workspace-specific MCP) with the batch and the campaign ID.
3. If the call fails on a batch, retry once with exponential backoff. If it still fails, log which rows failed and continue. Do NOT halt the entire upload because one batch failed.
4. After all batches: print `Uploaded N of M leads. K failed.` If any failed, list the first 5 failure reasons.

100 leads per batch is the sweet spot. Larger batches risk MCP timeouts, smaller batches waste round trips.

### Phase 9: Verify and report

After the upload completes:

1. Call `mcp__instantly-luxvance__campaigns_get` on the new campaign ID. Read back: campaign name, sequence step count, variant count, account count, lead count, status.
2. Confirm `status` is `draft` (or whatever Instantly's draft enum is in v2). If somehow it landed as active, immediately call `mcp__instantly-luxvance__campaigns_pause` and report the anomaly to Jose.
3. Print the result block:

```
Campaign created in DRAFT.

  Name:     Luxvance - NAM - Sales Leaders - New in Role - W18
  ID:       <uuid>
  Steps:    1
  Variants: A, B, C
  Inboxes:  20 attached (tag=active, LRU)
  Leads:    1,847 uploaded
  Schedule: M-F 08:00-17:00 ET, 30/inbox/day
  Tracking: off (opens + clicks)
  Stop on reply: on

Review and Start:
  https://app.instantly.ai/app/campaigns/<uuid>
```

End with one line: `DRAFT only. Review subject/body/inbox/lead count, then hit Start in the Instantly UI when ready.` Nothing else.

## Workspace pick

The Luxvance MCP namespace is `mcp__instantly-luxvance__*`. For client-specific workspaces use:

- `mcp__instantly-capquest__*`
- `mcp__instantly-connect-resources__*`
- `mcp__instantly-gfv__*` (Global Food Ventures)
- `mcp__instantly-kcal__*`
- `mcp__instantly-remly__*`

Pick the workspace from the campaign name's client prefix or ask Jose if ambiguous. The flow is identical, only the MCP namespace changes.

## When this skill is invoked

Common triggers:

- "launch this in Instantly" / "ship to Instantly" / "create the draft" (after `build-campaign` finished)
- "sube esto a Instantly" / "crea el draft en Instantly" / "arma la campaña en Instantly"
- A file path to a `variants.yaml` plus mention of a leads list
- A clear handoff from `build-campaign` where the operator says "and launch it"

If Jose says "build and launch", chain `build-campaign` first, then this skill. Do not skip ahead.

## Errors that block the upload

These conditions stop the flow immediately, with a clear message:

| Condition | Message |
|---|---|
| `variants.yaml` missing required field | `variants.yaml missing required field: <field>. See references/variants-schema.yaml.` |
| `leads.csv` extra column | `leads.csv has unallowed column: <col>. Update references/leads-csv-schema.md and the allowlist if you need this field.` |
| Zero inboxes with the requested tag | `No healthy inboxes found with tag=<tag>. Tag at least 1 inbox in Instantly before launching.` |
| API auth failure | `Instantly MCP returned 401. Verify the workspace MCP is connected in Claude Code settings.` |
| Lead count > 25,000 | `1.847 leads OK; 27,000 is too large for one campaign. Split by region or persona and run twice.` |

For everything else, log the error and continue if it is recoverable (single batch failure on leads), abort if it is not (campaign create failure, sequence configure failure).

## Relationship with sibling skills

| Skill | Direction | Role |
|---|---|---|
| `campaign-intelligence` | Upstream | Locks hypothesis. Produces `client request` text. |
| `build-campaign` | Upstream | Writes copy. Produces 9-block kit AND `variants.yaml`. |
| `enrich-and-verify-leads` | Upstream | Produces verified `leads.csv` (deliverable only). |
| **`launch-instantly-campaign`** | **This skill** | **Takes the two artifacts, creates DRAFT in Instantly.** |
| `make-a-task` | Optional sibling | If Jose wants a record of the launch in Notion, run after this. |
| `cleanup-completed-campaigns` | Downstream | Runs weeks later to free inbox quota when campaign finishes. |

## Output format

Phase 9's result block is the only structured output. Everything else (validation errors, warnings) is plain prose. Match the language of Jose's most recent message.

No emojis. No postamble. No "next step" prose unless Jose explicitly asks.

## What is intentionally out of scope (for now)

- List building from Prospeo or other sources. The skill assumes `leads.csv` exists already, produced by Clay export (legacy), Prospeo (future sibling skill), or manual upload.
- Per-lead AI personalization at scale (situation_line, value_line per row). The skill consumes those columns if they exist, but does not generate them. That is a future sibling: `personalize-leads-with-subagents`, mirroring GEX's `/personalization-subagent-pattern`.
- Inbox provisioning and warmup. Done in Instantly directly.
- Email verification. Done by `enrich-and-verify-leads` upstream.

These will arrive as separate skills. The current skill is the foundation; everything else flows through it once we are off Clay.

## Files

- `references/variants-schema.yaml` — blank schema with field descriptions
- `references/leads-csv-schema.md` — required and allowed columns
- `references/instantly-api-notes.md` — MCP tool reference for the endpoints this skill hits

## Language

Default to the language of Jose's most recent message for prose responses. The campaign name, the variants.yaml content, and the leads.csv content stay in English because Instantly stores them in English regardless.

# leads.csv — required and allowed columns

The deployer (`launch-instantly-campaign`) accepts a CSV with these exact columns. Any column not listed below causes the upload to abort with a clear error, pointing at this file.

This strict allowlist is intentional. Three reasons:

1. **PII safety.** Stops accidental upload of addresses, phone numbers, DOBs, or anything else that does not belong inside Instantly's lead store.
2. **Merge-field integrity.** A misspelled column like `compny_domain` would silently fail to render in the email body. Catch it at upload time.
3. **Schema drift control.** If a copywriter starts using a new merge field, the operator must update this file and the skill at the same time. No untracked field expansion.

## Two naming conventions

CSV columns use **snake_case** (clean to parse, easier to write by hand). Instantly merge fields use a **mix of camelCase and spaced names** because that is the convention already established in Luxvance's Instantly workspaces (and pre-existing account signatures, automations, and campaigns reference those exact field names).

The deployer maps from CSV column to Instantly field on upload. Operators do not need to track both names; the SKILL.md does the translation.

## Required columns

| CSV column | Instantly field | Merge syntax in body | Notes |
|---|---|---|---|
| `email` | `email` | (recipient address, not a merge) | Must pass basic email regex. Deliverability is assumed (run `enrich-and-verify-leads` first). |
| `first_name` | `firstName` | `{{firstName}}` | Capitalized. Strip whitespace. |
| `last_name` | `lastName` | `{{lastName}}` | Capitalized. Strip whitespace. |
| `company_name` | `companyName` | `{{companyName}}` | Use the public company name, not the legal entity. NEVER use `{{company}}` in copy. |

## Allowed optional columns

| CSV column | Instantly field | Merge syntax in body | Source / purpose |
|---|---|---|---|
| `company_domain` | `companyDomain` | `{{companyDomain}}` | The prospect's website domain. Used in copy when referencing their site or for proof-line context. |
| `title` | `title` | `{{title}}` | Job title. Lowercase recommended for natural sentence flow. |
| `linkedin_url` | `linkedinUrl` | `{{linkedinUrl}}` | LinkedIn profile URL. Rarely used in body; useful for sales rep context in reply triage. |
| `variable_1` | `Variable 1` | `{{Variable 1}}` | The Clay-style Variable 1. Per `build-campaign` convention: prospect's own company segment. 2-8 words, lowercase, no trailing punctuation. Example: `b2b software firm`. |
| `variable_2` | `Variable 2` | `{{Variable 2}}` | Variable 2. Per `build-campaign` convention: the prospect's ideal buyer. 2-8 words. Example: `founders at b2b software firms`. |
| `situation_line` | `situation_line` | `{{situation_line}}` | AI-generated per-lead observation (1 sentence). What you noticed about their company that opens the email. Produced by future `personalize-leads-with-subagents` skill. |
| `value_line` | `value_line` | `{{value_line}}` | AI-generated per-lead value connection (1 sentence). |
| `cta_line` | `cta_line` | `{{cta_line}}` | AI-generated per-lead soft CTA (1 sentence). |

## Disallowed columns

These columns are explicitly rejected. If a list-builder emits them, strip them before uploading:

- `phone`, `mobile`, `phone_number` — phone numbers do not belong in Instantly. If the campaign needs SMS, that runs through a different tool.
- `address`, `street`, `city`, `state`, `zip`, `country` — geographic data is encoded in the campaign targeting (the list filter), not per lead.
- `revenue`, `funding`, `industry_revenue` — internal scoring fields, not for sending.
- Any column starting with `_` (underscore) — convention for internal scratch fields.
- Any column not in the required or allowed lists above.

## Header row example

Minimal:

```csv
email,first_name,last_name,company_name
```

With Clay-style variables (build-campaign convention):

```csv
email,first_name,last_name,company_name,company_domain,title,variable_1,variable_2
```

With AI personalization (future state, after `personalize-leads-with-subagents` lands):

```csv
email,first_name,last_name,company_name,company_domain,title,situation_line,value_line,cta_line
```

## Pre-upload checklist

Before handing the CSV to `launch-instantly-campaign`, confirm:

- [ ] All emails verified (run `enrich-and-verify-leads`, expect ≥98% deliverable)
- [ ] Zero internal duplicates (same email appearing twice)
- [ ] No row missing a required column
- [ ] No row with empty `email`
- [ ] All optional columns named exactly as listed above
- [ ] No PII column slipped in (phone, address, etc.)
- [ ] Total row count below 25,000

If any check fails, fix the CSV and re-run. The deployer aborts on any of these.

## Adding a new field

If a copywriter wants to use a new merge field like `{{recent_post_topic}}`, do this in one PR:

1. Add the column row to the "Allowed optional columns" table above.
2. Add the column name to the `ALLOWED_COLS` set in the deployer's validation logic (currently inline in `SKILL.md`; will move to a script when one exists).
3. Document the source: where does the value come from? Manual research? AI subagent? Clay enrichment?
4. Ship the change BEFORE writing copy that uses the new field. Reverse order causes silent merge failures.

The deployer never accepts ad-hoc columns. The schema is the contract.

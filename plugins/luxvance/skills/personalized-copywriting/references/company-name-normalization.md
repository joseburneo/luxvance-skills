# Company Name Normalization

Rules applied by the subagent during `personalized-copywriting`. Mirrors what Clay's "Clean Company Name" step does, but runs locally.

The goal: a `company_name` field that reads naturally inside the email body. `"Hi {{firstName}}, saw {{companyName}} is ..."` should not produce `"Hi Sarah, saw JAGUAR LAND ROVER LTD is ..."` or `"Hi Sarah, saw Acme Inc., is ..."`.

## Rule 1: Strip legal suffixes

Case-insensitive match. Match at the end of the string, optionally preceded by a comma.

| Suffix | Strip? | Example |
|---|---|---|
| `LTD` | Yes | `Acme Ltd` → `Acme` |
| `LIMITED` | Yes | `Acme Limited` → `Acme` |
| `LLC` | Yes | `Acme LLC` → `Acme` |
| `INC` / `INC.` | Yes | `Acme Inc.` → `Acme` |
| `PLC` | Yes | `Acme PLC` → `Acme` |
| `CORP` / `CORP.` | Yes | `Acme Corp.` → `Acme` |
| `GMBH` | Yes | `Acme GmbH` → `Acme` |
| `SA` / `S.A.` | Yes | `Acme S.A.` → `Acme` |
| `BV` / `B.V.` | Yes | `Acme B.V.` → `Acme` |
| `AG` | Yes | `Siemens AG` → `Siemens` |
| `OY` / `OYJ` | Yes | `Nokia Oyj` → `Nokia` |

Strip the comma before the suffix too: `Acme, Inc.` → `Acme`.

Do NOT strip:
- The word "Group" — that is usually part of the brand (`Bain Capital Group` stays).
- The word "Company" — same reason (`The Walt Disney Company` stays).
- "Holdings" / "Industries" — brand-identifying suffix (`Berkshire Hathaway Industries` stays).

## Rule 2: ALL CAPS → Title Case

If the entire company name (after suffix strip) is uppercase, convert to Title Case.

Examples:

| Input | Output |
|---|---|
| `JAGUAR LAND ROVER` | `Jaguar Land Rover` |
| `BLACK & CALLOW` | `Black & Callow` |
| `KPMG` | `KPMG` (preserved — see Rule 3) |
| `IBM` | `IBM` (preserved — see Rule 3) |

## Rule 3: Preserve intentional case

A company name is intentionally cased and must be preserved as-is if any of these are true:

1. **Acronym (3 letters or fewer, all uppercase):** `IBM`, `KPMG` (4 letters but commonly capitalized), `BBC`, `KFC`, `PwC` (mixed but identifiable).
2. **Mid-word uppercase letter:** `iPhone`, `ThinkAnalytics`, `PayPal`, `eBay`, `iRobot`, `LinkedIn`, `YouTube`.
3. **Mid-word ampersand with no spaces:** `Black&Callow`, `S&P` (note: `S&P Global` is the correct expansion — but if the source has `S&P`, preserve).
4. **Lowercase first word followed by capitalized word:** `IFS assyst`, `dbt Labs`, `npm Inc`.
5. **Brand has a registered trademark / stylized casing the team recognizes:** `Adobe`, `Apple`, `Google` — Title Case is fine for these.

When in doubt, preserve the original casing.

## Rule 4: Strip noise characters

- Trailing punctuation: `Acme,` → `Acme`. `Acme.` → `Acme`.
- Surrounding quotes: `"Acme"` → `Acme`. `'Acme'` → `Acme`.
- Double spaces: `Acme  Group` → `Acme Group`.
- Trailing whitespace.

## Rule 5: Empty or null fallback

If the `company` field is empty, null, or after normalization becomes empty, fall back to the email domain.

Process:

1. Take the part of the email after `@`.
2. Drop the TLD (e.g. `.com`, `.co.uk`, `.io`).
3. Capitalize the remainder.

Examples:

| Email | Empty company → fallback |
|---|---|
| `sarah@acme.com` | `Acme` |
| `john@acme-corp.co.uk` | `Acme-Corp` |
| `jose@luxvance.com` | `Luxvance` |

If the domain is a public ESP (gmail, outlook, yahoo, hotmail, icloud, etc.), do NOT use it as a fallback. Mark the row's `company_name` as empty and let the QA pass drop it.

## Rule 6: Strip parentheticals

Often Apollo includes a parenthetical region marker:

| Input | Output |
|---|---|
| `Acme (UK)` | `Acme` |
| `Acme Corp. (formerly Beta)` | `Acme` |
| `Acme Group (US)` | `Acme Group` |

Strip everything from `(` to the matching `)` and any trailing whitespace.

## Rule 7: DBA handling

If the name contains "DBA" or "d/b/a" (doing business as), keep the DBA name, drop the legal name.

Example: `Smith Holdings DBA Smith & Sons` → `Smith & Sons`.

## Edge cases worth handling

- **Multiple suffixes:** `Acme Inc. LLC` → `Acme`. Strip iteratively.
- **Suffix mid-word:** `Limited Brands` (the company, not a legal suffix). Detect by: if "Limited" is followed by another word that is not at the start of a suffix, preserve.
- **Lowercase brands with periods:** `dbt Labs.` → `dbt Labs`. Trailing period strip but preserve internal lowercase.
- **Brand has the word "Group" as the FIRST word:** `Group Three Holdings` — preserve as a real brand name.
- **Comma-separated DBA:** `Acme, doing business as Beta` → `Beta`. Same logic as DBA.

## Test fixtures

Use these to sanity-check the subagent's normalization output during the QA loop.

| Raw company | Expected company_name |
|---|---|
| `JAGUAR LAND ROVER LTD` | `Jaguar Land Rover` |
| `Acme Inc.` | `Acme` |
| `Acme, Inc.` | `Acme` |
| `iPhone Repair Shop Ltd` | `iPhone Repair Shop` |
| `Black&Callow Limited` | `Black&Callow` |
| `IFS assyst PLC` | `IFS assyst` |
| `KPMG LLP` | `KPMG` |
| `Acme (UK) Ltd` | `Acme` |
| (empty), email `john@acme.com` | `Acme` |
| (empty), email `john@gmail.com` | (empty, drop) |

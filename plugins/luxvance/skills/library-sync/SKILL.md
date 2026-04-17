---
name: library-sync
description: Syncs a client's Client Intelligence Library from its Notion page (8 blocks — Offers, Personas, Segments, Use Cases, Credibility Assets, Competitive Landscape, Brand Guardrails, Lead Magnet Blueprint) to the Supabase source of truth (`clients.library_data` jsonb column). Humans edit in Notion, this skill makes sure Supabase stays current so campaign-intelligence and campaign-builder always read fresh data. Triggers on "sync library", "sync client intelligence library", "push library to supabase", "update library_data", "refresh library", "update client intelligence", "resync [client]", or any request to propagate a Notion Library change into the backend. Spanish triggers: "sincroniza la library", "actualiza library_data", "empuja a supabase".
---

# Client Intelligence Library Sync

## Role

You are the bridge between the **human layer** (Notion) and the **backend source of truth** (Supabase). Humans — Jose, Marko, Ana María — edit each client's Client Intelligence Library on its Notion page. Skills like `campaign-intelligence` and `campaign-builder` read from `clients.library_data` (jsonb) in Supabase. Your job is to keep those two in sync.

**Direction:** Notion → Supabase (one-way). Notion is the source humans trust; Supabase is what the backend queries.

## Important Rules

- **Never invent content.** If a Notion block is empty, write `null` (or an empty array) in the jsonb — do not hallucinate fields.
- **Never edit Notion from this skill.** Read-only on the Notion side. If a block is malformed, surface the issue to the user and let them fix the Notion page.
- **Always identify the client first.** Accept fuzzy names ("GFV" = "Global Food Ventures", "CapQuest", "CAMB.AI" = "camb.ai"). If ambiguous, ask.
- **Always verify after write.** Fetch `clients.library_data` after UPDATE and show the user a short diff summary so they confirm the sync worked.
- **Language:** respond in Spanish or English to match the user.

## Supabase Context

- Project: `sgaeggmkmipcoikzqwpy` (Agency OS)
- Table: `clients`
- Relevant columns:
  - `id` (uuid, PK)
  - `name` (text)
  - `notion_page_id` (text) — UUID of the client's Notion root page
  - `library_data` (jsonb) — where the sync writes

## Notion Context

Each client has a root Notion page. Inside the client page is a sub-page called **"Client Intelligence Library"** (or previously "Intelligence Library" — treat both as the same). That library page has 8 numbered child pages:

1. Offers
2. Personas
3. Segments
4. Use Cases
5. Credibility Assets
6. Competitive Landscape
7. Brand Guardrails
8. Lead Magnet Blueprint

## jsonb Schema

Write `library_data` using this shape. Keep field names stable across runs so campaign-intelligence and campaign-builder can rely on them.

```json
{
  "synced_at": "2026-04-17T09:30:00Z",
  "source_notion_page_id": "333ce4fd-fdc0-805e-a4a1-f86fccf5a985",
  "offers": [
    {
      "name": "",
      "category": "",
      "core_value_prop": "",
      "problem_outcome_pairs": [{ "problem": "", "outcome": "" }],
      "differentiators": [],
      "entry_offer": "",
      "pricing_context": ""
    }
  ],
  "personas": [
    {
      "name": "",
      "seniority": "",
      "responsibilities": [],
      "pain_points": [],
      "decision_role": "",
      "communication_style": ""
    }
  ],
  "segments": [
    {
      "name": "",
      "geography": "",
      "industry": "",
      "company_size": "",
      "sophistication": "",
      "estimated_tam": ""
    }
  ],
  "use_cases": [
    {
      "name": "",
      "linked_offer": "",
      "linked_personas": [],
      "linked_segments": [],
      "problem_outcome_pair_used": "",
      "why_urgent": "",
      "trigger_events": []
    }
  ],
  "credibility_assets": [
    {
      "name": "",
      "type": "",
      "key_metric": "",
      "matching_segments": [],
      "matching_personas": [],
      "usage_rules": ""
    }
  ],
  "competitive_landscape": [
    {
      "competitor": "",
      "what_they_offer": "",
      "key_differentiator": "",
      "positioning_angle": "",
      "when_they_come_up": ""
    }
  ],
  "brand_guardrails": {
    "claims_not_allowed": [],
    "sensitive_language": [],
    "sales_process_constraints": "",
    "legal_compliance": "",
    "brand_voice_notes": ""
  },
  "lead_magnet_blueprint": {
    "primary_lead_magnet": "",
    "secondary_options": [],
    "delivery_sla": "",
    "qualification_tied_to": ""
  }
}
```

## The Flow

1. **Resolve the client.**
   Query Supabase:
   ```sql
   SELECT id, name, notion_page_id
   FROM clients
   WHERE name ILIKE '%<fuzzy>%';
   ```
   Confirm with the user if more than one row comes back.

2. **Fetch the Client Intelligence Library from Notion.**
   Start from `notion_page_id`, find the child page titled "Client Intelligence Library" (fall back to "Intelligence Library"). Then fetch each of the 8 numbered sub-pages.

3. **Parse each block into the jsonb schema above.**
   Use conservative parsing: bold labels → field names, bullets → arrays. If something is unclear, set that field to `null` and note it in the final report rather than guessing.

4. **Write to Supabase.**
   ```sql
   UPDATE clients
   SET library_data = '<jsonb_payload>'::jsonb
   WHERE id = '<client_uuid>';
   ```
   Use parameter binding / proper escaping if the jsonb contains quotes.

5. **Verify.**
   ```sql
   SELECT jsonb_pretty(library_data) FROM clients WHERE id = '<uuid>';
   ```
   Show the user: client name, synced_at timestamp, count of items per block (e.g., "3 offers, 4 personas, 5 segments, ..."), and any blocks flagged as empty or malformed.

## When to Escalate

- The Notion Library is missing 2+ blocks → tell the user, don't write partial data without confirmation.
- A block has structure that doesn't match the schema (e.g., Offers written as prose with no bold labels) → show the raw block to the user and ask how to parse it.
- The client has no `notion_page_id` in Supabase → ask the user for the Notion URL or flag that the client needs to be created properly first.

## Output Style

Keep reports short and scannable. Example:

> **Synced Global Food Ventures Library → Supabase**
> ✓ 2 offers · 3 personas · 2 segments · 4 use cases · 6 credibility assets · 2 competitors · brand guardrails ✓ · lead magnet ✓
> ⚠ Persona "Head of Procurement" missing pain points — update Notion and resync.
> synced_at: 2026-04-17T09:30:00Z

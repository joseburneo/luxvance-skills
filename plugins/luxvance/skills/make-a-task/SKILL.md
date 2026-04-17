---
name: make-a-task
description: Create a task in the Luxvance Notion Tasks database for Marko, Ana María, or Jose, linked to a client. Use this skill whenever the user says "make a task", "create a task", "new task", "add a task", or describes an action item for a specific person on a specific client in their Notion workspace. Trigger even if the user doesn't say the word "Notion" — any time Jose assigns work to his team (Marko, Ana María, himself) for a client (Global Food Ventures, Kcal Lunch, CapQuest, Connect Resources, Luxvance, Remly, Insurance Market, Qureos, etc.), this skill applies. Also trigger on Spanish phrasings like "haz una tarea", "crea una tarea", "añade una tarea".
---

# Make a Task (Luxvance / Notion)

Jose runs Luxvance and uses a single Notion Tasks database to drive all client work for his team (Marko, Ana María, himself). This skill turns a short natural-language instruction into a properly-linked Notion task in seconds.

The goal is **speed**: one sentence in, task created, link out. Don't over-explain or ask extra questions when the request is already clear.

## When this skill triggers

Use this skill whenever the user asks to make, create, add, or note down a task — especially when the request involves one of the teammates and/or a client. Typical phrasings:

- "Make a task for Marko on Global Food Ventures: ..."
- "Create a task for Ana María on Kcal Lunch: ..."
- "Add a task for me: review X for CapQuest"
- "Note down a task — Marko should ... for Connect Resources"
- "Haz una tarea para Ana en Kcal sobre ..."

If the user gives you a block of context (e.g., "Georges requested...") and ends with something that sounds like an assignment, treat it as a task request and use this skill.

## Fixed data you already know

These IDs are stable in the Luxvance Notion workspace — don't re-look them up. Use them directly in the `notion-create-pages` call.

**Tasks data source** (the parent for the new page):
`aa426b13-e339-4ebf-a2b7-65af80b27264`

**Clients data source** (for looking up the client relation):
`eea9f2a2-7089-4a74-af21-50b8458c865e`

**Team member user IDs** (pass inside the `Owner` property, which is a JSON array of user URIs):

| Name (and common variants) | User ID |
|---|---|
| Marko / Marco / Mark | `user://1a4d872b-594c-81b2-8059-0002e186ad1d` |
| Ana María / Ana Maria / Ana / Anita | `user://1fcd872b-594c-8121-a28c-0002b354640c` |
| Jose / José / "me" / "myself" / "I" | `user://22c47f6c-029d-404f-b36d-312a40b080d0` |

Jose sometimes says "Marco" when he means "Marko" — always map that to Marko. Both spellings refer to the same person.

Multiple owners are allowed — if the user says "for Marko and me", include both user URIs in the array.

## Task properties

The Tasks data source has these properties (use exactly these names):

- **To-Do** (title) — a concise one-line description of the work. Prefer an imperative verb ("Check", "Draft", "Run", "Review").
- **Owner** (person) — JSON array of one or more user URIs, e.g. `["user://..."]`.
- **Client** (relation) — JSON array of one page URL relating to the Clients data source, e.g. `["https://www.notion.so/<client-page-id>"]`.
- **Complete** (status) — default to `"Preparing"` unless the user specifies otherwise. Valid values: `Preparing`, `Working`, `Done`.
- **Due** (date) — only set if the user mentions a due date. Use the expanded property `date:Due:start` with an ISO-8601 date string (`YYYY-MM-DD`).

## The flow

1. **Parse the request.** Pull out:
   - Owner(s) — from "for [name]" / "me" / names mentioned after the verb
   - Client — from "on [client]" / "for [client]" / context
   - Title — a concise imperative version of the ask (not the full context)
   - Extra context — any "who requested it", "why", "goal", "scope" the user gave
   - Due date — if mentioned ("by Friday", "next Tuesday", "end of month")

2. **Resolve the client.** Call `notion-search` scoped to the Clients data source:
   ```
   notion-search(query="<client name>", data_source_url="collection://eea9f2a2-7089-4a74-af21-50b8458c865e")
   ```
   Take the top result when it's a clear match. If there's no obvious match, ask which client rather than guessing.

3. **Fill any missing required fields.** If owner or client wasn't specified, ask — don't invent. Prefer a quick multi-choice question via `AskUserQuestion` so the user can pick fast.

4. **Create the page.** Call `notion-create-pages` with:
   ```
   parent: { type: "data_source_id", data_source_id: "aa426b13-e339-4ebf-a2b7-65af80b27264" }
   pages: [{
     properties: {
       "To-Do": "<concise title>",
       "Owner": "[\"user://<owner-id>\"]",
       "Client": "[\"<client-page-url>\"]",
       "Complete": "Preparing"
       // optional: "date:Due:start": "2026-04-20"
     },
     content: "<body in the format below, if there's useful context>"
   }]
   ```

5. **Reply with the link.** Short response: one sentence confirming what you did, then a clickable link to the task. Don't re-paste the full body — the user can click through. Use Notion URL format: `https://www.notion.so/<page-id-without-dashes>`.

## Body format (use when there's meaningful context)

When the user provides background (who requested it, why, what success looks like), structure the body like this — it mirrors how Jose thinks about work:

```
**Requested by:** <name, if specified>

**Ask:** <one-sentence statement of what to do>

**Goal:** <what success looks like — why this matters>

**Scope:**
- <bullet>
- <bullet>
```

If the request is a one-liner ("make a task for Marko on Luxvance: renew the domain next Tuesday"), **skip the structured body** — the title alone is enough, and forcing structure where there isn't any wastes everyone's time.

## Examples

### Example 1 — rich context

User says:
> "Make a task for Marko on Global Food Ventures: Georges requested to do, for two weeks, a single email per lead — new leads and a single email — to measure the amount of replies compared to outreach doing follow-ups."

Extracted:
- **Title:** `GFV — 2-week test: single email per lead (no follow-ups) to measure reply rate`
- **Owner:** Marko
- **Client:** Global Food Ventures (search, pick top result)
- **Status:** Preparing
- **Body:** structured (Requested by: Georges / Ask / Goal / Scope)

### Example 2 — one-liner

User says:
> "Make a task for me on CapQuest: check the results from the Ramp agent execution"

Extracted:
- **Title:** `Check Ramp agent execution results`
- **Owner:** Jose
- **Client:** CapQuest
- **Status:** Preparing
- **Body:** empty

### Example 3 — with a due date

User says:
> "Task for Ana María on Kcal Lunch by next Friday: finalize the C-suite meal plan copy"

Extracted:
- **Title:** `Finalize C-suite meal plan copy`
- **Owner:** Ana María
- **Client:** Kcal Lunch
- **Due:** next Friday (resolve to ISO date)
- **Status:** Preparing

### Example 4 — ambiguous, needs a question

User says:
> "Make a task for Ana"

→ No client, no description. Ask via `AskUserQuestion`:
- Which client?
- What should Ana do?

## Keep it fast

Jose values speed above all. After creating the task, reply with a short confirmation and the link — no long summary of what you wrote in the body. If everything went smoothly, two sentences is plenty.

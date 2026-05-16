---
name: cleanup-completed-campaigns
description: >
  Frees Instantly contact-quota by removing no-reply leads from campaigns that are
  completed, paused, or ≥98% finished at the lead level. Always preserves leads who replied.
  Triggers on "limpia las campañas de [cliente]", "clean up [client] campaigns",
  "borra los leads sin respuesta de [cliente]", "free Instantly quota for [client]",
  "limpia leads no-respondedores", "cleanup instantly [client]", or any request to
  delete stale leads from finished/paused Instantly campaigns to free contact slots.
version: 0.1.0
---

# Cleanup Completed Campaigns

Wraps the bundled `scripts/cleanup_completed_campaigns.py` (sibling to this SKILL.md) to free Instantly's contact-quota by removing leads who never replied from campaigns that are effectively done.

## When to use

User wants to free slots in an Instantly workspace and is fine deleting non-responders from campaigns that have already finished sending or have been parked. Active campaigns that are still sending are skipped unless ≥98% of their leads have already finished the sequence.

**Never** delete leads who replied (`email_reply_count > 0`). The script enforces this; do not propose workarounds.

## Supported clients

Resolved from `credentials/master.env`: `luxvance, kcal, connect-resources, capquest, gfv, remly`. See [[project-active-clients]].

## How to run

Always **dry-run first**, show the user the per-campaign counts, then ask for explicit confirmation before re-running with `--execute`.

```bash
# Step 1 — dry-run (default)
python3 .claude/skills/cleanup-completed-campaigns/scripts/cleanup_completed_campaigns.py --client <name>

# Step 2 — execute only after user says "sí, borra"
python3 .claude/skills/cleanup-completed-campaigns/scripts/cleanup_completed_campaigns.py --client <name> --execute
```

Flags:
- `--threshold 0.98` (default) — minimum ratio of lead-status=3 for active/draft campaigns to qualify
- `--batch-size 1000` (default) — initial `--limit` per bulk-delete call; the script adapts down if the server processes fewer

## Output to expect

- Per-campaign classification line with ✓ (eligible) or · (skip) and reason
- Per-campaign tally: `total / delete / keep`
- Grand total at the end

On `--execute`, watch for `"cap detected: server processed N/M — adapting"` — this is the script learning the real API cap for bulk-delete that run. Report the discovered cap back to the user; it informs future runs.

## Safety rails

1. **Never run `--execute` without explicit user approval** after showing the dry-run report. Phrasing like "sí, avanza", "ejecuta", "borra" is required. A user simply saying "limpia X" should produce a dry-run, not a delete.
2. **Confirm the client name** before running if ambiguous. Match the spoken client to one in the supported list.
3. **Replied leads are preserved** automatically by the script — do not bypass this filter.
4. **Quota implications:** explain that deletions are permanent in Instantly and the freed slots will be immediately reusable for new lead uploads.

## After execution

- Summarize: `<N> deleted, <M> repliers preserved across <K> campaigns`.
- If the run discovered an API cap different from 50 (the cap observed 2026-05-16), mention it so the user knows the script will go faster next time.
- The contact-quota in Instantly will reflect the freed slots immediately.

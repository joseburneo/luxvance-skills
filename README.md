# Luxvance Skills

Cowork plugin marketplace for the Luxvance team. 26 skills + 5 operational docs to run the end-to-end cold email service.

## First-time install (one time per machine)

```
/plugin marketplace add joseburneo/luxvance-skills
/plugin install luxvance@joseburneo-luxvance-skills
```

The marketplace name is `joseburneo-luxvance-skills` (owner-repo slug with a hyphen). The plugin inside it is named `luxvance`, so the install target is `luxvance@joseburneo-luxvance-skills`.

## Update to the latest version

```
/plugin marketplace update joseburneo-luxvance-skills
/plugin update luxvance@joseburneo-luxvance-skills
```

No uninstall required. No restart required.

## Verify the installed version

Run `/plugin` and open the **Installed** tab. Version number is shown next to `luxvance`. Current version: **v0.5.3**.

## Optional: auto-update on session start

Run `/plugin`, go to the **Marketplaces** tab, select `joseburneo-luxvance-skills`, toggle **Enable auto-update**.

---

## Start here

**Open `plugins/luxvance/docs/BUILD_A_CAMPAIGN.md` first.** That doc is the operational handbook — the steps every Luxvance team member follows to create, launch, and optimize a campaign. Hard rules (3-day cadence, no link in Email 1, voice rules), Instantly settings (Actively Sending tag convention, schedule defaults per region, tracking config), pre-launch checklist, and post-launch cadence.

## The 26 skills, organized

| Group | Skills |
|---|---|
| 🎯 Orchestrator (the entry point) | `build-cold-email-campaign` |
| Strategy + intake | `campaign-intelligence`, `campaign-strategy`, `lead-magnet-brainstorm`, `icp-prompt-builder` |
| Acquisition channels | `lead-sourcing`, `competitor-engagers`, `google-maps-list-builder` |
| Build → Launch pipeline | `build-campaign`, `enrich-and-verify-leads`, `list-quality-scorecard`, `personalized-copywriting`, `launch-instantly-campaign` |
| Post-launch optimization | `cold-email-weekly-rhythm`, `positive-reply-scoring`, `experiment-design`, `deliverability-audit`, `deliverability-incident-response` |
| Infrastructure ops | `instantly-inbox-manager`, `domain-name-generator` |
| Always-on guardrail | `spam-word-checker` (auto-triggered) |
| General agency ops | `book-discovery-call`, `brand-guidelines`, `make-a-task`, `make-invoice` |
| Maintenance | `cleanup-completed-campaigns` |

## How to use a skill

In any Claude Code session after install, type a natural-language phrase that matches a skill's trigger. Examples:

- `build a campaign for CapQuest` → fires the orchestrator
- `analyze last 60 days for Kcal` → fires campaign-intelligence
- `score the replies of campaign X` → fires positive-reply-scoring
- `qualify this list against the CapQuest ICP` → fires icp-prompt-builder

The skill takes over and guides the rest of the conversation. No special syntax — just describe what you want.

## Docs included in this plugin

All under `plugins/luxvance/docs/`:

| Doc | What it covers |
|---|---|
| `BUILD_A_CAMPAIGN.md` | **Start here.** Step-by-step handbook for launching a campaign. Hard rules + all Instantly settings. |
| `COLD_EMAIL_CAMPAIGN_PIPELINE.md` | Umbrella pipeline doc — all 26 skills indexed, data flow diagrams, cost references |
| `INSTANTLY_CLI_QUICKREF.md` | When to use Instantly CLI (bulk) vs MCP (conversational). Per-workspace key wrapping. Top commands. |
| `LEAD_ENRICHMENT_PIPELINE.md` | Deep dive on the email verification stage (MillionVerifier + BounceBan waterfall, 60-day freshness rule) |
| `INBOX_AND_DOMAIN_INFRASTRUCTURE_AUDIT.md` | What's already running in the Luxvance backend (Render crons, Campaign Factory) vs what the skills layer on top |

## Daily / weekly cadence (after installing)

The plugin includes `cold-email-weekly-rhythm` which orchestrates the operational schedule. Put these on your calendar:

- **Monday 9:00 AM Dubai** — Deliverability audit
- **Wednesday 10:00 AM Dubai** — Positive-reply sweep (respond to interested leads within 30 seconds)
- **Friday 3:00 PM Dubai** — Campaign retrospectives at day 21
- **Every other Monday 11:00 AM** — Inbox rotation
- **1st of each month 10:00 AM** — Spam placement test review
- **First Monday of each quarter 1:00 PM** — Experiment review

Full schedule + actions in the `cold-email-weekly-rhythm` skill (just invoke it).

## Reporting issues

If a skill behaves unexpectedly, gives a wrong answer, or you find a gap, message Jose with:
- The exact phrase you typed
- What the skill did
- What you expected
- Which campaign / client you were working on

The skills self-improve — Jose's feedback gets baked into the skill so it doesn't happen again.

---

*Precision Leads. Engineered by Intelligence.*

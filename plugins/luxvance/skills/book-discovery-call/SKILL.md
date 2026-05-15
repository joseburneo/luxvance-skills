---
name: book-discovery-call
description: Books a Google Calendar discovery call with the right Luxvance conventions. Use whenever Jose says "book a discovery call", "book a call with [prospect]", "book a meeting with [prospect]", "schedule the discovery", "schedule a discovery call", "set up a discovery call", "send the meeting invite", or sends a screenshot or email and asks for a meeting to be booked. Spanish triggers "agenda la llamada", "agenda una reunión con", "agendar la discovery", "manda la invitación", "agéndalo". The skill's only job is to create the calendar event with the correct title, color, duration, Meet link, and notification level. It does not draft replies, search the inbox, or chase the prospect.
---

# Book Discovery Call (Luxvance)

Jose books discovery calls with prospects. Each booking has to follow the same conventions every time, so his color-based reminder automation fires and his calendar stays scannable.

This skill is the booking action only. The conversation that leads to a confirmed time happens elsewhere (Instantly inbox, LinkedIn DM, screenshot Jose sends, referral, etc.). By the time the skill is invoked, a time is already agreed.

## When this skill triggers

- "Book a discovery call with [name]"
- "Book a call with [prospect] on [date] at [time]"
- "Schedule a 45-minute discovery with [name]"
- "Send the meeting invite for [name]"
- "Set up a discovery call with [prospect] for [date]"
- Jose pastes or screenshots a confirmation and says "book it"
- Spanish: "agenda la llamada con [prospecto]", "agéndalo para [fecha]", "manda la invitación"

If Jose is asking for time options, slots, or "find a free slot", that is a different need (use `suggest_time` directly, do not invoke this skill).

## Required inputs

| Input | How to source it if missing |
|---|---|
| Prospect email | Required. If missing, ask Jose. Do not guess. |
| Date | Required. If Jose says "next Tuesday" resolve from today and confirm in the response. |
| Start time | Required. Default time zone is Jose's primary, Europe/Brussels. If the prospect is in another time zone and Jose specifies "10 AM ET", convert to Europe/Brussels in the ISO timestamp. |

## Optional inputs (with defaults)

| Input | Default |
|---|---|
| Duration | **30 minutes.** If Jose says "15", "20", "45", "60", "1 hour", "an hour and a half", parse and use that exact length. |
| Prospect name | If missing, derive from the local part of the email (`otto.hughes@dnv.com` → `Otto Hughes`). Capitalize cleanly. |
| Company name | If missing, derive from the email domain stripped of TLD and uppercased if it is an acronym, otherwise title-cased (`dnv.com` → `DNV`, `getflex.com` → `Flex`, `connectresources.ae` → `Connect Resources`). |
| Description | Use the default block below unless Jose passes one. |

## Fixed parameters (never change these)

These are non-negotiable. Always set them on every booking.

| Parameter | Value |
|---|---|
| `colorId` | `"3"` (Grape). Required for Jose's reminder automation to fire. |
| `addGoogleMeetUrl` | `true` |
| `notificationLevel` | `"ALL"` |
| `timeZone` | `"Europe/Brussels"` (unless Jose explicitly requests another) |
| `attendeeEmails` | The prospect email (and any other emails Jose names) |

## Title pattern

```
<Company> × Luxvance · Discovery (<Name>)
```

Use the multiplication sign `×` (U+00D7), not the letter `x`. Use the middle dot `·` (U+00B7), not a hyphen, dash, or em-dash.

Examples:
- `DNV × Luxvance · Discovery (Otto Hughes)`
- `Flex × Luxvance · Discovery (Jennette Sanchez)`
- `CapQuest × Luxvance · Discovery (Marco Banfi)`
- `Connect Resources × Luxvance · Discovery (Liam Doherty)`

If a prospect has only one name, use it alone. If a company is two words, keep it as is (e.g. `Connect Resources`, `Insurance Market`).

## Default description block

```
Discovery call between Jose Burneo (Luxvance) and <Name> (<Company>).

Agenda:
- Current outbound motion and what is working
- Where Luxvance can compound results
- What a pilot would look like

Jose Burneo
Luxvance
Precision Leads. Engineered by Intelligence.
```

If Jose passes a custom description (e.g. "this is a follow-up after the first call, mention the May 13 agenda"), use his version instead. Do not merge.

## The booking call

Use this exact tool: `mcp__4f0edc16-9516-4fb5-bf61-a38814d228ee__create_event`

```
create_event(
  summary: "<Company> × Luxvance · Discovery (<Name>)",
  startTime: "<ISO 8601 start>",
  endTime: "<start + duration in ISO 8601>",
  timeZone: "Europe/Brussels",
  attendeeEmails: ["<prospect_email>"],
  colorId: "3",
  addGoogleMeetUrl: true,
  notificationLevel: "ALL",
  description: "<default block or Jose's custom version>"
)
```

## After booking

Confirm in one short line. Do not summarize the agenda back. Jose already knows.

Format:
```
Booked: <day, date> at <HH:MM CEST/CET> with <Name> (<Company>). Invite sent to <email>. Meet: <url>.
```

Example:
```
Booked: Wednesday 13 May at 14:00 CEST with Otto Hughes (DNV). Invite sent to otto.hughes@dnv.com. Meet: https://meet.google.com/rxn-eyqo-iwt.
```

If Jose asked for a different duration than the default, mention it in the same line so he can spot a misparse fast: `... at 14:00 CEST (45 min) with Otto Hughes (DNV) ...`.

## Conflict and sanity checks

Before creating the event, do a quick conflict check on Jose's primary calendar:

```
list_events(startTime: "<start - 5 min>", endTime: "<end + 5 min>", pageSize: 5)
```

If anything overlaps, surface it to Jose in one line and wait for him to decide:

```
Heads up: that slot overlaps with "Team standup" (14:00 to 14:30). Book anyway, or pick another time?
```

Do not book through a conflict without his confirmation.

## Edge cases

- **Multiple attendees.** If Jose says "include Marko" or "add anita@luxvance.com", append them to `attendeeEmails`. The title still uses the prospect company and prospect name.
- **External co-attendee from prospect side.** Same. Add their email. Title stays one prospect, the primary one.
- **Reschedule, not new booking.** If Jose says "move the DNV call to Friday at 15:00", do not invoke this skill. Use `update_event` directly with `startTime` and `endTime`. Keep `colorId` and the rest unchanged.
- **All-day or block event.** Not supported. This skill is for prospect calls only.
- **No prospect email.** Stop. Ask Jose for the email. Do not book a placeholder.

## Voice for any text the skill produces

The confirmation line, the conflict prompt, and any description text you generate must follow `luxvance:brand-guidelines`:

- No em-dashes.
- CEFR B1 to B2 English (or Spanish if Jose is writing in Spanish).
- Short sentences.
- No buzzwords, no flattery, no emojis.
- One-line confirmation. No agenda recap.

## What this skill does not do

- It does not search the Instantly inbox.
- It does not draft replies to leads.
- It does not propose times. If Jose has not picked a time, ask him for one.
- It does not update HubSpot or Notion. If Jose wants the prospect logged elsewhere, that is a separate skill or a separate ask.

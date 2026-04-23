---
name: instantly-reply-copilot
description: Jose's human-in-the-loop copilot for the Instantly inbox. Finds every received email that hasn't been replied to (not just unread), ranks by interest signal, drafts replies in Jose's voice for his approval, sends them through Instantly, and books discovery calls on Google Calendar when a lead is ready. Use whenever Jose says "check my inbox", "who needs a reply", "what's in instantly", "triage the inbox", "last emails we haven't replied to", "what replies came in", "reply to [lead]", "book a call with [prospect]", "run the reply copilot", or any request to process outbound reply traffic. Also trigger on Spanish phrasings like "revisa mi bandeja", "qué correos hay que responder", "tríanos lo pendiente", "agenda una llamada con [prospecto]". Distinct from the autonomous AI auto-reply agent already running in Instantly — this one drafts, Jose approves, then it sends.
---

# Instantly Reply Copilot (Luxvance)

Jose runs Luxvance's outbound campaigns through Instantly. Every day, a handful of prospects reply to the campaigns. Some are hot (want a call), some are warm (want more info), some are objections, some are noise (OOO, wrong person). The job of this skill is to turn that inbox into a short, ranked action list and help Jose close the loop fast: draft a reply in his voice, send it, and book the call on his calendar when it's time.

The goal is **speed with judgment**. Jose is the CEO and his time is the scarce resource. Show him the signal, hide the noise, and let him approve each outbound reply before it actually sends.

## When this skill triggers

Any time Jose wants to look at what's happened in Instantly since the last triage, or take action on a specific lead. Typical phrasings:

- "Check my inbox"
- "What's new in Instantly?"
- "Who needs a reply today?"
- "Show me the last emails we haven't replied to"
- "Triage the inbox"
- "Draft a reply to the Flex one"
- "Book a call with Sushil"
- Spanish: "revisa el buzón", "qué hay pendiente de responder", "agenda la llamada con [X]"

If Jose references a lead by first name or company without specifying inbox tools, still treat it as this skill's domain if there's clearly an open thread in Instantly.

## Fixed tooling (don't guess at tool names)

All Instantly and Calendar work goes through these exact tools. Use them directly.

**Instantly (Jose's outbound mailboxes):**

| Purpose | Tool |
|---|---|
| List emails with filters + pagination | `mcp__2ae8d3dd-75a0-4b60-9e64-32a2101fe934__list_emails` |
| Full body of one email | `mcp__2ae8d3dd-75a0-4b60-9e64-32a2101fe934__get_email` |
| All emails in a thread | `list_emails` with `search: "thread:<thread_id>"` |
| Send the reply | `mcp__2ae8d3dd-75a0-4b60-9e64-32a2101fe934__reply_to_email` |
| Mark thread read when done | `mcp__2ae8d3dd-75a0-4b60-9e64-32a2101fe934__mark_thread_as_read` |

The shorter `mcp__instantly__*` namespace points at the same server but its schema is missing fields. Always use the `mcp__2ae8d3dd-...` namespace above.

**Google Calendar (Jose's calendar):**

| Purpose | Tool |
|---|---|
| Find free 30-min slots | `mcp__4f0edc16-9516-4fb5-bf61-a38814d228ee__suggest_time` |
| Create the call + send invite | `mcp__4f0edc16-9516-4fb5-bf61-a38814d228ee__create_event` |
| Sanity-check conflicts | `mcp__4f0edc16-9516-4fb5-bf61-a38814d228ee__list_events` |

**Fallback booking link (always include in reply alongside proposed times):**
`https://www.luxvance.com/book-a-call`

## Field glossary (Instantly)

These fields come back from `list_emails` and are easy to misread. Keep this glossary close.

| Field | Meaning |
|---|---|
| `ue_type` | `1` = campaign-sent by us, `2` = received from prospect, `3` = manual reply OR auto-reply agent. **If `from_address_email` matches `eaccount` (or any of Jose's mailboxes), a `ue_type==3` email is OUR reply — count the thread as replied.** |
| `is_unread` | `1` = unread in inbox, `0` = already read |
| `i_status` | Interest status set by Instantly. `1` = interested, `2` = meeting booked, `3` = not interested, `-1` = out of office. `null` = not classified yet |
| `thread_id` | Groups messages in one conversation. Use it to find out if we already replied |
| `eaccount` | The sender account we used. Must be passed back to `reply_to_email` |
| `campaign_id` | Which campaign the lead came from |
| `from_address_email` | The prospect's email |
| `timestamp_email` | ISO timestamp of the email |

## The flow

### Step 1 — Pull all unreplied threads (not just unread)

Team members sometimes open an email and forget to reply. "Unread" is not a reliable signal for "unreplied". Do it properly:

1. Call `list_emails` with `email_type: "received"` and a reasonable window (`limit: 100`, sorted by most recent). Paginate with `starting_after` if `next_starting_after` comes back, up to roughly 3 pages (300 received emails is far more than one daily triage will ever have).
2. Build a set of unique `thread_id` values from the received emails.
3. For each `thread_id`, check only the **latest** message in that thread:
   ```
   list_emails(search: "thread:<thread_id>", limit: 1, sort_order: "desc", preview_only: true)
   ```
   `preview_only: true` keeps the response around 1.5 KB per thread instead of pulling the full bodies — the difference between the triage finishing in seconds vs. blowing through the context window on big inboxes.
4. Classify the thread:
   - Latest is `ue_type == 2` (received) AND the sender domain is the prospect's: **UNREPLIED**.
   - Latest is `ue_type == 1`: already replied, skip.
   - Latest is `ue_type == 3` AND `from_address_email` matches `eaccount` or one of Jose's own mailbox domains (`luxvance.com`, `luxvanceconsults.com`, `luxacqpartners.com`, `lvleadgen.com`, `luxaiengine.com`, `gtmluxvpartners.com`, `connectluxvgrowth.com`, etc.): **REPLIED** (that's either Jose replying from his personal mailbox, or the AI auto-reply agent — both count as handled).
   - Latest is `ue_type == 2` but the preview matches an OOO / auto-reply pattern ("out of the office", "mailer-daemon", "do not reply"): **NOISE**, skip.

Do the thread-check calls in parallel (batch the tool calls in the same turn). Stay under ~12 parallel calls — Instantly returns `429 Too Many Requests` around 15. If a batch fails, wait ~8 seconds and retry just the ones that failed.

### Step 2 — Rank by interest signal

For each unreplied thread, read the latest received email's `content_preview` plus a quick `get_email` if the preview is ambiguous. Tag into one of four buckets.

| Bucket | Signal |
|---|---|
| **Hot** | Asks for a call, for times, for pricing, for a deck, or says "yes, interested". `i_status == 1` is a hint but not decisive — read the words |
| **Warm** | Friendly reply with a question, or asks for more info to decide |
| **Objection** | "Not now", "no budget", "we already have a vendor", "wrong person" — still worth a short reply, often a referral ask |
| **Noise** | Out-of-office auto-replies (`i_status == -1`), bounces, unsubscribe confirmations, one-word "thanks". Skip these in the ranked list but mention the count |

Present the list to Jose in this order: Hot first, then Warm, then Objection. Each item as one line:

```
1. [Hot] Jennette Sanchez (Flex) — "I would be interested in a call. Can you send calendar..." — joseburneo@gtmluxvpartners.com
```

Include enough context that Jose can pick one without opening the email.

### Step 3 — Draft a reply in Jose's voice

When Jose picks a thread (or says "draft replies to the hot ones"), produce a draft that:

- Follows `luxvance:brand-guidelines` voice rules: no em dashes, CEFR B1–B2 English, mirror reply length, no buzzwords, no flattery, no emojis in client-facing copy.
- Matches the Jose Roberto writing voice memory (polite, human, no marketing lingo).
- Mirrors the prospect's **language** (if they wrote in Spanish, reply in Spanish).
- Mirrors the prospect's **length** (one-sentence reply gets a one-sentence reply).
- Signs off with a simple `Jose` (not "Best regards, Jose Burneo, CEO of Luxvance" — that's agency-bro energy).

Reference material Jose and Luxvance can point to when it helps: case studies on `luxvance.com`, pricing on `luxvance.com`, booking link `https://www.luxvance.com/book-a-call`.

Show the draft to Jose **inline** alongside the incoming message. Use a compact format:

```
— Incoming (Jennette @ Flex) —
"Hi Jose, I would be interested in a call. Can you send calendar..."

— Draft —
Hi Jennette,

Happy to. I open 30 minutes on my calendar. Here are three slots that work for me (all in your local time):

- Monday 20, 10:00 AM
- Monday 20, 2:30 PM
- Tuesday 21, 11:00 AM

If none of these fit, you can also pick a time here: https://www.luxvance.com/book-a-call

Jose
```

Wait for Jose to approve or edit before step 4. Never auto-send.

### Step 4 — Send via Instantly

Once Jose approves, call `reply_to_email` with:

- `reply_to_uuid`: the email UUID of the incoming message (from `list_emails.items[].id`).
- `eaccount`: the **same** `eaccount` that received the message. Do not switch sender accounts mid-thread — it breaks deliverability and looks strange to the lead.
- `subject`: reuse the incoming subject (with `Re:` already present) or craft a new one only if Jose edits it.
- `body`: **use `html`, not `text`.** Instantly collapses all `\n` newlines in plain-text bodies into a single run-on paragraph, which ruins any reply that uses a list, line breaks, or spacing (tested and confirmed). Build the HTML with `<p>` for paragraphs, `<br>` for single line breaks, and `<ul><li>` for lists.

Example body payload for a reply with time slots:

```
body: {
  html: "<p>Hi Jennette,</p><p>Happy to. A few options next week (Dubai time, GST):</p><ul><li>Mon 20 Apr, 2:30 PM</li><li>Mon 20 Apr, 3:30 PM</li><li>Tue 21 Apr, 2:30 PM</li></ul><p>If none of those fit, grab any slot here: <a href=\"https://www.luxvance.com/book-a-call\">https://www.luxvance.com/book-a-call</a></p><p>Jose</p>"
}
```

**Known limitation — no CC field.** `reply_to_email` does not expose `cc` or `bcc` parameters. If Jose wants a copy on `jburneo@luxvance.com` or any other address, there is no way to add it through Instantly from this skill. Two workarounds, ask Jose which he prefers:

- Send without CC (simplest — Jose can still see the sent message inside Instantly's UI).
- After sending, use the Gmail MCP to forward the sent HTML body to Jose's personal address as a log copy.

After the reply sends, call `mark_thread_as_read` with the thread UUID to clear the inbox counter.

### Step 5 — Book the call (only for hot leads who want one)

If Jose's draft proposes times, make them real, not imaginary.

1. Call `suggest_time` with:
   - `attendeeEmails: ["primary"]` (Jose's own primary calendar — no need to include the prospect yet, they haven't confirmed a time).
   - `startTime` = now, `endTime` = 5 working days ahead.
   - `durationMinutes: 30`.
   - `timeZone`: Jose's local TZ (default to the one `list_calendars` reports on the primary calendar).
   - `preferences: { startHour: "09:00", endHour: "18:00", excludeWeekends: true }`.
2. Pick 2–3 slots at different times of day (avoid three back-to-back options — spread them across morning / afternoon and across days).
3. Include them in the draft from step 3.

When the prospect picks a time (usually in their next reply), confirm and **create the event**:

```
create_event(
  summary: "Luxvance × <Company> — Discovery call",
  startTime: "<prospect's chosen start in ISO>",
  endTime: "<start + 30 min in ISO>",
  timeZone: "<Jose's primary TZ>",
  attendeeEmails: ["<prospect email>"],
  addGoogleMeetUrl: true,
  notificationLevel: "ALL",
  description: "Discovery call between Jose Burneo (Luxvance) and <Name> (<Company>). Agenda: current outbound motion, what's working, where AI-driven lead gen can compound results."
)
```

`notificationLevel: "ALL"` makes Google Calendar email the prospect an invite that blocks their calendar. That's the behavior Jose wants: block their time, send the meet link, done.

Then send a **short confirmation reply** through `reply_to_email` summarizing: "Booked for [time]. Invite with Meet link is in your inbox. Talk soon, Jose."

### Step 6 — Close the loop

After sending any reply (with or without a booking), always:

1. `mark_thread_as_read` on the thread.
2. Tell Jose one sentence: what you sent, to whom, and — if booked — the time.

## Voice rules (the short version)

These are the parts of the Luxvance brand voice that matter most for replies. For anything unclear, fall back to `luxvance:brand-guidelines`.

- **No em dashes.** Ever. Use a comma, a period, parentheses, or a colon.
- **CEFR B1–B2.** Simple words. Short sentences.
- **Mirror length.** 1 sentence in, 1 sentence out. 3 paragraphs in, up to 2 out.
- **Same language** as the prospect wrote in.
- **No flattery** opener. Don't say "love what you're building". Get to the point.
- **No buzzwords.** Avoid "synergy", "leverage", "unlock", "seamless", "streamline", "at scale".
- **Signature:** just `Jose`. Skip titles and taglines in replies.
- **One clear ask per email.** Either propose a call, or share info, or ask a single question. Not all three.

## What to do if the user asks for replies in bulk

Sometimes Jose will say "draft replies to all the hot ones". Fine. Draft each one **separately** and show them as a numbered list. Do not auto-send any of them. Jose approves each one (or says "send 1 and 3, skip 2"), and only then do you call `reply_to_email`.

If there are more than 5 hot leads in one triage, check in with Jose: "I see 7 hot replies. Want me to draft all of them, or start with the top 3 and you pick up from there?" Mirrors his preferred cadence and avoids a wall of drafts.

## Examples

### Example 1 — hot lead with a call request

Incoming:
> "Hi Jose, I would be interested in a call. Can you send calendar availability?"

Drafted reply:
```
Hi Jennette,

Happy to. I have 30 minutes open on my side. Here are three options in your local time:

- Mon Apr 20, 10:00 AM
- Mon Apr 20, 2:30 PM
- Tue Apr 21, 11:00 AM

If none of those fit, you can pick a time here: https://www.luxvance.com/book-a-call

Jose
```

After Jose approves and the prospect picks Mon 10:00 AM, create the event with `attendeeEmails: ["jennette.sanchez@getflex.com"]`, send the short confirmation reply, and mark the thread read.

### Example 2 — warm lead asking for more info

Incoming:
> "Thanks for reaching out Jose. Sure, can you kindly share more details on the service?"

Drafted reply (mirrors length, one clear next step):
```
Hi Marianela,

Sure. In one line, we run outbound for B2B teams with full AI-driven personalization — lead research, copy, sending, and reply handling, all priced as one service. More detail and case studies here: https://www.luxvance.com/

If it helps, I can share a 2-minute overview on a quick call. Here's my calendar: https://www.luxvance.com/book-a-call

Jose
```

### Example 3 — objection (not now)

Incoming:
> "Appreciate the note but we're not looking at new vendors this quarter."

Drafted reply (short, respectful, leaves door open — no pressure):
```
Understood, thanks for the quick reply. I'll circle back next quarter if that works. In the meantime if anything changes on your side, you know where to find me.

Jose
```

### Example 4 — out of office (noise)

Skip. Mention in the summary: "1 OOO auto-reply from X — ignored."

## Keep it fast

Jose values speed. Triage reports should be bullet-tight. Drafts should be 3–6 lines unless the prospect wrote more. Don't add trailing summaries after sending — a one-line confirmation is enough.

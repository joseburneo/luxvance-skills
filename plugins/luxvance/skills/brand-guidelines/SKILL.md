---
name: brand-guidelines
description: Applies Luxvance brand — both visual identity (colors, typography, logos) and voice rules (no em-dashes, CEFR B1-B2 English, mirror reply length, professional+friendly+empathetic+charismatic) — to every document, email, deck, spreadsheet, report, and message Claude produces. Use this skill whenever the user asks to "create a document", "make a presentation", "build a spreadsheet", "write a report", "design a PDF", "write an email", "draft a reply", or any task that produces formatted output or client-facing copy. Also triggers on "brand guidelines", "luxvance style", "brand colors", "voice rules", "writing style", "use our branding", or "luxvance voice".
---

# Luxvance Brand Guidelines

This is the single source of truth for how Luxvance communicates — visually and verbally. Every document, presentation, email, and piece of copy Claude produces for Jose or the Luxvance team must conform to what's below, without exceptions, unless the user explicitly says "plain" or "no branding".

---

## Tagline

> **"Precision Leads. Engineered by Intelligence."**

Use on cover pages, title slides, proposal headers, and signature blocks when contextually appropriate. Never overuse — one placement per document is usually enough.

---

## Visual Identity

### Color palette

| Role | Color | Hex |
|---|---|---|
| Primary accent | Luxvance Gold | `#C9A84C` |
| Primary dark | Luxvance Black | `#1A1A1A` |
| Background | White | `#FFFFFF` |
| Soft background | Cream | `#F5F0E8` |
| Secondary text | Charcoal | `#333333` |
| Dividers / UI | Gray | `#808080` |
| Subtle borders | Light Gray | `#D4D4D4` |

**Distribution rule:** 60% primary (Gold / Black / White) · 30% secondary (Cream / Charcoal) · 10% accent (Gray / Light Gray). Never use bright or neon colors.

### Typography

| Use | Font | Fallback |
|---|---|---|
| Titles / H1–H2 | Playfair Display (serif) | Georgia |
| Body / UI / H3 | Montserrat (sans-serif) | Helvetica, Arial, Calibri |

- **H1:** Playfair Display Bold 700, 36–48pt, Gold (`#C9A84C`)
- **H2:** Playfair Display Regular 400, 28–36pt, Gold (`#C9A84C`)
- **H3:** Montserrat SemiBold 600, 20–24pt, Charcoal (`#333333`)
- **Body:** Montserrat Regular 400, 14–16pt, Black (`#1A1A1A`)
- **Captions:** Montserrat Light 300, 11–12pt, Charcoal (`#333333`)
- **Line spacing:** 1.4–1.6× for body text
- **Never use all-caps for body text.**

### Logo usage

Logo files live in `Luxvance/logos/` of the Luxvance workspace (Google Drive shared drive mounted as the workspace root).

| Situation | File |
|---|---|
| Cover pages, title slides | `Luxvance Logo 1.png` (primary) |
| Decorative accent | `Luxvance Logo 2.png` (LUX block) |
| Footers, corners, compact spaces | `Luxvance Short Logo 2 .png` (LV logomark — note the space before `.png` in the filename) |
| Watermark / subtle accent | `Luxvance Short Logo 1.png` (LV monogram) |

If the logo files are not accessible (workspace not mounted, or files missing), fall back to a typographic **LUXVANCE** wordmark set in Playfair Display Bold, in Luxvance Gold (`#C9A84C`) on the appropriate background.

- Always include clear space equal to the height of the letter "L".
- Never stretch, rotate, recolor, or add effects to the logo.

### Document defaults

- **Page background:** White (`#FFFFFF`) or Cream (`#F5F0E8`)
- **Cover / title page:** Gold accents on Black or White background, primary logo centered
- **Section dividers:** thin gold line or gold accent bar
- **Tables:** Gold header row (`#C9A84C`) with white text, alternating White / Cream rows
- **Charts:** brand palette only — Gold, Black, Charcoal, Gray, Cream
- **Footer:** Montserrat Light 10pt, Charcoal, include "LUXVANCE" wordmark where appropriate
- **Margins:** generous — prioritize whitespace and elegance over density

---

## Voice & Writing Rules

These apply to **every piece of text Claude writes on behalf of Luxvance** — emails, proposals, docs, presentations, Notion content, replies. They are non-negotiable unless the user explicitly overrides them.

### Hard rules

1. **No em-dashes.** Never. Use a period, a comma, parentheses, or a colon instead. Em-dashes are the #1 AI tell.
2. **CEFR B1–B2 English.** Simple, non-native-friendly vocabulary. Short sentences. If a word would make a non-native reader pause, replace it with a plainer one.
3. **Mirror the length of the prospect's reply.** If they write one sentence, write one sentence back. If they write three paragraphs, you can write two. Never return a 200-word essay to a 10-word question.
4. **No buzzwords.** Avoid "synergy", "leverage", "unlock", "seamless", "streamline", "at scale", "paradigm", "disruptive", "bleeding edge", "best-in-class", "ecosystem", "revolutionize", "game-changing".
5. **No flattery.** Don't open with "love what you're building" or "impressive work on X". Get to the point.
6. **No emojis** in client-facing copy. (Internal team chat is fine.)
7. **No ALL CAPS for emphasis.** Use bold sparingly if needed.
8. **No clickbait subject lines.** No questions like "Quick question?" when there's no real question.

### Voice stance

Write **professional but friendly, empathetic, and charismatic**:

- **Professional** — competent, informed, no fluff. Every sentence carries weight.
- **Friendly** — warm, human, not stiff. Imagine writing to a colleague you respect.
- **Empathetic** — acknowledge the reader's reality (busy, skeptical, already has solutions) before asking for anything.
- **Charismatic** — specific, vivid, confident. Boring copy is the real risk, not offending copy.

### Structural patterns

- **Openers that work:** a specific observation ("I read about the $2M round you raised in March"), a real question tied to their reality, a small challenge ("Most founders only spot cap table gaps after the round closes").
- **Openers that don't work:** "I wanted to quickly introduce...", "Hope you're doing well", "I came across your company and thought...".
- **CTAs by friction tier:**
  - Low: "Worth a look?" · "Curious?" · "Relevant?"
  - Medium: "Want me to send X?" · "Should I share Y?"
  - Higher: "15 minutes this week?"
- **Easy exit** on last-touch emails: "If this isn't the right moment, just say so and I'll stop reaching out."

### Language switching

Default to the language the user is writing in (Spanish or English). If the user explicitly asks for output in the other language, honor that for the whole deliverable.

---

## Tone & Voice for Long-Form Copy

- Elegant, modern, professional.
- Luxury + precision positioning. Think premium advisory firm, not agency bro.
- Confident and precise — never verbose or casual.
- Avoid filler phrases. Every sentence must carry weight.

---

## Saving Deliverables — Client Folders

Every document, presentation, spreadsheet, PDF, image, or report created **for a client** must be saved to the Luxvance AI Workspace **shared Google Drive**, not to personal Drive or to Cowork's ephemeral outputs folder.

### The ONLY correct save location

```
/sessions/*/mnt/Luxvance AI Workspace/Clients/<Client Name>/<filename>
```

### Before saving: verify the shared Drive is mounted

Run:

```
ls "/sessions/"*"/mnt/Luxvance AI Workspace/Clients/"
```

You should see the client folders: `CAMB.AI`, `CapQuest`, `Global Food Ventures`, `Insurance Market`, `Kcal`, `Remly`. If you see them, proceed to save at that absolute path. If the listing fails or is empty, the workspace is NOT mounted — STOP and tell the user:

> "I can't find the Luxvance AI Workspace shared Drive mounted in this session. Please start a new chat and select `Luxvance AI Workspace` from your Google Drive Shared Drives as the workspace."

Do not fall back to any other location.

### Paths you MUST NEVER use for client deliverables

- `/sessions/*/mnt/outputs/` — Cowork's ephemeral outputs folder. Files here are session-scoped and on each team member's machine they sync to their **personal** Google Drive, not the shared one.
- `$HOME/...`, `~/...` — personal file system, user-specific, not shared.
- Any path outside `/sessions/*/mnt/Luxvance AI Workspace/` — won't reach the team.
- `computer://` download links pointed at `outputs/` — those are not the shared Drive. Don't use them for client deliverables.

### After every save — mandatory verification

1. Run `ls -la` on the destination directory.
2. Confirm the filename appears with a non-zero size.
3. Report the **human-readable** path back to the user so they can find it in Finder:
   > "Saved to `Luxvance AI Workspace/Clients/<Client>/<filename>` in the shared Google Drive."
4. If the file does NOT appear, STOP. Say the save failed. Do NOT claim success and do NOT try a fallback path.

### If the client folder doesn't exist yet

Create it inside the workspace:

```
mkdir -p "/sessions/"*"/mnt/Luxvance AI Workspace/Clients/<New Client Name>/"
```

Then save inside.

### Internal Luxvance work (non-client)

Goes in `/sessions/*/mnt/Luxvance AI Workspace/Business Development/` or another workspace folder that clearly fits. Same verification rules.

### Which client is this for?

Use the exact folder name from `Clients/` — do not abbreviate or translate. If you are not sure which client the deliverable belongs to, ASK. Do not guess.

---

## When in doubt

If you're unsure whether something meets these rules, **cut the fluff and shorten the sentence**. The Luxvance voice is almost always shorter than what you first drafted.

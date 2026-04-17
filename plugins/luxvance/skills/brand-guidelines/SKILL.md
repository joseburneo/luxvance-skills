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

Logo files live in `04_Brand_and_Assets/logos/` of the Luxvance workspace:

| Situation | File |
|---|---|
| Cover pages, title slides | `Luxvance Logo 1.png` (primary) |
| Decorative accent | `Luxvance Logo 2.png` (LUX block) |
| Footers, corners, compact spaces | `Luxvance Short Logo 2.png` (LV logomark) |
| Watermark / subtle accent | `Luxvance Short Logo 1.png` (LV monogram) |

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

## When in doubt

If you're unsure whether something meets these rules, **cut the fluff and shorten the sentence**. The Luxvance voice is almost always shorter than what you first drafted.

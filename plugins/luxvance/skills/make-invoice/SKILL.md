---
name: make-invoice
description: Generate a branded Luxvance invoice PDF for a specific client (CapQuest, Camb.ai, Kcal World, Global Culinary Ventures / GFV, or any client in clients.json), save it to the Luxvance AI Workspace Finance folder, and draft a Gmail to the client recipients. Use this skill whenever Jose says "make the invoice", "create the invoice", "monthly invoice for X", "send the May invoice", "ship this month's invoice", "ship this month's invoices", or "re-issue invoice INV-X". Spanish triggers "haz la factura", "crea la factura", "factura del mes para X", "envía la factura de mayo". Always uses brand-guidelines visual rules and saves to the shared Drive (never to /tmp or personal Drive).
---

# Make Invoice (Luxvance)

Jose runs Luxvance and bills a small roster of clients monthly. This skill turns a one-line ask ("make this month's invoice for CapQuest") into a branded PDF saved in the right Finance folder, plus a Gmail draft to the right recipients.

## What this skill ALWAYS does

- Renders the PDF with Luxvance brand: Logo 1 in the header, Short Logo 2 in the footer, Gold #C9A84C, Playfair-style serif headings, Helvetica/Montserrat body, gold horizontal rule, gold "PAY NOW" button when applicable. **Defer all visual questions to the `brand-guidelines` skill.**
- Saves the PDF to the user's "Luxvance AI Workspace" Google Drive shared drive at:
  ```
  🏦 Finance/Business Income invoices/{YYYY}/{N. Mon YYYY}/{INV-NUMBER} - {Client display name} - {Mon DD, YYYY}.pdf
  ```
- Drafts a Gmail to the client recipients after the PDF is ready (see "Drafting the Gmail" below).

## What this skill NEVER does

- Save to `/tmp` or to Jose's personal Drive. Always the shared Drive path above.
- Hardcode client data into the script. The script reads `data/clients.json` for the roster.
- Skip the visual-verification step. After rendering, read the PDF and confirm it looks right.

## Step-by-step flow

### 1. Identify the client

If the user names the client (CapQuest, Camb.ai, Kcal, GFV, etc.), match it. The roster includes case-insensitive aliases under `clients.json["aliases"]` ("kcal" → "kcal-world", "global food ventures" → "gfv", etc.).

If ambiguous or no client is named, ask: "Which client is this for?"

### 2. Load client config

Read `data/clients.json` (sibling of this `SKILL.md`, under `Skills/make-invoice/data/clients.json`) and look up the client by key.

If the chosen client has a `default_amount_note` (e.g. Kcal World during the reduced-retainer review), surface it to Jose and confirm the amount before proceeding.

If `recipients.to` contains the literal `"TBD"` (currently GFV), ask Jose for the recipient email(s) before drafting the Gmail.

### 3. Determine dates and invoice number

- **Issue date**: today, unless Jose specified otherwise. Format as `Month DD, YYYY` (e.g. `May 31, 2026`) for the PDF, and as `YYYY-MM-DD` for the file path.
- **Due date**: derive from the client's `due_date_rule`:
  - `1st of next month` → first day of the month after the issue date.
  - `15th of next month` → the 15th of the month after the issue date.
- **Invoice number**:
  - **New invoice**: `INV-YYYY-MMDD` based on the issue date (e.g. `INV-2026-0531`).
  - **Re-issue**: keep the original sequential number (e.g. `INV-000322`). Jose will name it explicitly.
- **Service period** (used in the line-item description):
  - `billing_model: in advance` (everyone except GFV) → period is the month *containing* the issue date or the *next* full month, depending on Jose's intent. Default: the month *containing* the issue date. Confirm with Jose if the issue date is near a month boundary.
  - `billing_model: in arrears` (GFV) → period is the month *just ended* before the issue date.

### 4. Compute the math

- `subtotal_services` = the client's `default_amount` (or whatever Jose specified).
- `credit_note` = present only when Jose explicitly asks for one (label, amount, explanatory subtext).
- `net_subtotal` = `subtotal_services - credit_note`.
- `vat_rate`: UAE clients = `0.05`, KSA clients = `0.0`. Read from `clients.json["clients"][key]["vat_treatment"]`.
- `vat_amount` = `round(net_subtotal * vat_rate, 2)`.
- `total` = `net_subtotal + vat_amount`.

### 5. Build the invoice config JSON

Write a JSON file (e.g. to `/tmp/lux-invoice-staging/<INV-NUMBER>.json`) that the script will consume. Schema:

```json
{
  "invoice_number": "INV-2026-0531",
  "issue_date": "May 31, 2026",
  "due_date": "June 1, 2026",
  "currency": "AED",
  "vat_rate": 0.05,
  "vat_label": "VAT (5%)",
  "from": { ... },
  "client": {
    "legal_name": "CapQuest Software Limited",
    "trn": "104885885400001",
    "trn_label": "TRN",
    "registration": null,
    "country_label": "United Arab Emirates",
    "contact_name": "Antoine Bruna",
    "contact_email": "antoine@capquest.io"
  },
  "items": [
    {
      "description_html": "<b>...</b><br/><font size=\"8\">...</font>",
      "qty": 1,
      "unit_price": 9181.00,
      "amount": 9181.00,
      "is_credit_note": false
    }
  ],
  "bank": { ... },
  "notes": "...",
  "stripe": { "enabled": false },
  "zatca": { "enabled": false },
  "logo_header_path": "/Users/joseburneo/Library/CloudStorage/GoogleDrive-jose@luxvance.com/Shared drives/Luxvance AI Workspace/🎨 Brand/Luxvance Logo 1.png",
  "logo_footer_path": "/Users/joseburneo/Library/CloudStorage/GoogleDrive-jose@luxvance.com/Shared drives/Luxvance AI Workspace/🎨 Brand/Luxvance Short Logo 2 .png",
  "output_path": "/full/path/to/Finance/folder/<INV-NUMBER> - <Client display> - <Mon DD, YYYY>.pdf"
}
```

Pull `from`, `bank`, and base client fields from `data/clients.json`. Override `vat_label` to `"VAT (0% - Export of Services)"` for KSA clients.

For GFV (or any client with `include_stripe_link: true`), set `stripe.enabled: true` and use the client's `stripe_url`.

For KSA clients, set `zatca.enabled: true` and provide `seller_name`, `vat_no`, and `date_iso` (use the issue date with `T10:00:00`). The script renders a `[QR placeholder]` box; real ZATCA QR generation is out of scope for v1.

### 6. Render the PDF

```bash
python3 "<plugin>/skills/make-invoice/scripts/generate_invoice.py" \
    --config /tmp/lux-invoice-staging/<INV-NUMBER>.json
```

The script writes the PDF to `output_path` from the config. Verify the file exists and the size is non-trivial (>50 KB for a single-page invoice).

### 7. Visual verification

Read the rendered PDF back and confirm:
- The header logo, "INVOICE" title, and meta block are aligned.
- BILL TO shows the right client name, TRN/Unified No, country.
- The line-item description, qty, unit price, and amount match.
- The Total Due number is correct.
- For KSA: ZATCA QR + PAY NOW blocks render side-by-side, VAT line reads "VAT (0% - Export of Services)".
- The LV mark + footer text are at the bottom.

If anything looks wrong, fix the config and re-render. Do not ship a broken PDF.

### 8. Drafting the Gmail

After the PDF is saved, draft a Gmail to the client's `recipients.to` (and `recipients.cc` if any). Use the manual-client-email HTML wrapper:

```html
<div style="font-family: Verdana, Geneva, sans-serif;">
  <p style="margin: 0 0 14px 0;">Hi {{first_name}},</p>
  <p style="margin: 0 0 14px 0;">Please find attached our invoice {{INV-NUMBER}} for {{service period}}, due on {{due date}}.</p>
  <p style="margin: 0 0 14px 0;">Bank details and (where applicable) the Stripe pay-now link are on the invoice itself. Let me know if anything needs adjusting.</p>
  <p style="margin: 0 0 14px 0;">Thank you.</p>
  <p style="margin: 0 0 14px 0;">Jose</p>
</div>
```

Rules:
- Use **Verdana** as the font family.
- Do **not** declare a font-size (let the client pick).
- Each paragraph uses `margin: 0 0 14px 0;` — no other margin styles.
- Subject line: `Luxvance Invoice {{INV-NUMBER}} — {{Client display name}} — {{Month YYYY}}` (use an em-dash here is fine in subject lines, but per brand-guidelines do not use em-dashes inside the body copy). Actually, follow brand-guidelines strictly: no em-dashes anywhere. Use a comma or hyphen in the subject too.
- Attach the rendered PDF.
- Save as a draft. Do not send. Jose reviews and sends manually.

### 9. Report back

Reply to Jose with:
- The full saved PDF path (so it is clickable in Finder).
- The total amount and currency.
- The Gmail draft status ("Draft saved to: To = …, CC = …, with the PDF attached").
- Any caveat (e.g. "GFV recipients were TBD in the roster, used the address you provided").

## Global rules

| Rule | Value |
|---|---|
| Numbering, new | `INV-YYYY-MMDD` from the issue date |
| Numbering, re-issue | keep the original sequential number |
| Default issue date | today |
| Default due date | 1st of next month, except GFV (15th of next month) |
| Billing model | in advance, except GFV (in arrears) |
| Currency | AED for everyone (no multi-currency yet) |
| VAT — UAE | 5% |
| VAT — KSA | 0% (export of services) |
| Bank block | Wio AED details, always present |
| Stripe block | only when `include_stripe_link: true` (today: GFV only) |
| ZATCA QR block | only for KSA clients (placeholder for v1) |
| Save path | shared Drive Finance folder, see top of this file |
| Header logo | `🎨 Brand/Luxvance Logo 1.png` |
| Footer logo | `🎨 Brand/Luxvance Short Logo 2 .png` (note the space before `.png`) |

## Where things live

```
🛠️ Skills/make-invoice/
├── SKILL.md            ← this file
├── scripts/
│   └── generate_invoice.py    ← parameterized renderer
└── data/
    └── clients.json    ← roster + from / bank shared blocks
```

The plugin source-of-truth lives in the Luxvance AI Workspace shared Drive at `🛠️ Skills/`. The build script (`scripts/build-plugin.sh` in the agency-os-workspace repo) packages this skill into the published plugin at `joseburneo/luxvance-skills`. To ship a new version, use the `ship-plugin-release` skill.

## Running outside Jose's Mac (Cowork, headless agents)

The default `logo_header_path` and `logo_footer_path` assume Google Drive File Stream is mounted at `/Users/joseburneo/Library/CloudStorage/GoogleDrive-jose@luxvance.com/`. When the skill runs in an environment where that mount is not present (Cowork sandbox, CI), the renderer will fail because the logo files cannot be read.

In those environments, before running `generate_invoice.py`:

1. Download the official logos from Drive into a local working directory:
   - `Luxvance Logo 1.png` (file ID `1hp28HkMcI8GUo6Z5E4NENy7qrhhEF147`) → `<workdir>/logo_header.png`
   - `Luxvance Short Logo 2 .png` (file ID `1WnqSsZ_w9Tgup2OeWAAvV0uRzkynRbga`) → `<workdir>/logo_footer.png`

   If the Drive MCP returns the content too large to inline, the response is still cached on disk (look for `tool-results/mcp-*-download_file_content-*.txt`) and you can `jq -r '.content' <cached> | base64 -d > <workdir>/logo.png`.

2. Override the two `logo_*_path` fields en el config JSON to point at the local copies before invoking the renderer.

Never recreate the logos with PIL or text fallbacks. Always use the official PNGs.

## Language

Default to Jose's language (Spanish or English). Per `brand-guidelines`, no em-dashes anywhere in the email body or notes field. Keep the invoice itself bilingual-neutral (numbers, dates, names) — only the line-item description and notes vary by language, and Jose works in English with these clients today.

#!/usr/bin/env python3
"""
generate_invoice.py — Parameterized Luxvance invoice renderer.

Takes a JSON config and writes a branded A4 PDF that matches the canonical
template (header logo + tagline, gold rule, FROM / BILL TO, gold-header line
items table, totals with gold rule above Total Due, optional Stripe and ZATCA
blocks side-by-side, bank details, notes, LV footer mark).

Usage:
    python3 generate_invoice.py --config invoice.json
    python3 generate_invoice.py --config invoice.json --output /path/out.pdf

Config schema — see Skills/make-invoice/SKILL.md for the full reference.
The skill writes the config; the script just renders it.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from PIL import Image as PILImage

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

GOLD = colors.HexColor("#C9A84C")
BLACK = colors.HexColor("#1A1A1A")
CHARCOAL = colors.HexColor("#333333")
LIGHT_GRAY = colors.HexColor("#D4D4D4")
CREAM = colors.HexColor("#F5F0E8")


def require_logo(path: str, label: str) -> str:
    """Hard-fail if a logo PNG is missing or empty. No silent fallbacks."""
    if not path:
        raise FileNotFoundError(f"{label} logo path is empty in config")
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"{label} logo not found at: {path}")
    if p.stat().st_size == 0:
        raise FileNotFoundError(f"{label} logo file is empty: {path}")
    return str(p)


def aspect_ratio(path: str) -> float:
    """Return height / width of an image, read from the file (no hardcoded ratios)."""
    with PILImage.open(path) as im:
        w, h = im.size
    if w == 0:
        raise ValueError(f"Image has zero width: {path}")
    return h / w


def fmt(amount: float, currency: str) -> str:
    return f"{currency} {amount:,.2f}"


def build_styles():
    base = getSampleStyleSheet()
    return {
        "body": ParagraphStyle("body", parent=base["Normal"],
            fontName="Helvetica", fontSize=9, textColor=BLACK, leading=12),
        "body_bold": ParagraphStyle("body_bold", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=9, textColor=BLACK, leading=12),
        "meta_label": ParagraphStyle("meta_label", parent=base["Normal"],
            fontName="Helvetica", fontSize=9, textColor=BLACK, alignment=TA_RIGHT),
        "invoice_title": ParagraphStyle("invoice_title", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=28, textColor=GOLD, alignment=TA_RIGHT),
        "total_label": ParagraphStyle("total_label", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=12, textColor=GOLD, alignment=TA_LEFT),
        "total_val": ParagraphStyle("total_val", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=12, textColor=GOLD, alignment=TA_RIGHT),
        "tagline": ParagraphStyle("tagline", parent=base["Normal"],
            fontName="Helvetica-Oblique", fontSize=8, textColor=CHARCOAL),
        "section": ParagraphStyle("section", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=9, textColor=GOLD, spaceAfter=4),
        "pay_now": ParagraphStyle("pay_now", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=14, textColor=colors.white,
            alignment=TA_CENTER, leading=18),
        "pay_url": ParagraphStyle("pay_url", parent=base["Normal"],
            fontName="Helvetica-Oblique", fontSize=8, textColor=CHARCOAL,
            alignment=TA_CENTER, leading=10),
        "zatca_kv": ParagraphStyle("zatca_kv", parent=base["Normal"],
            fontName="Helvetica", fontSize=8, textColor=BLACK, leading=11),
    }


def header_block(cfg, S):
    logo_path = require_logo(cfg["logo_header_path"], "header")
    logo_w = 68 * mm
    logo = Image(logo_path, width=logo_w, height=logo_w * aspect_ratio(logo_path))

    invoice_meta = [
        [Paragraph("<b>INVOICE</b>", S["invoice_title"])],
        [Paragraph(f"Invoice No: <b>{cfg['invoice_number']}</b>", S["meta_label"])],
        [Paragraph(f"Date: {cfg['issue_date']}", S["meta_label"])],
        [Paragraph(f"Due: {cfg['due_date']}", S["meta_label"])],
    ]
    meta_t = Table(invoice_meta, colWidths=[80 * mm],
                   rowHeights=[14 * mm, 5 * mm, 5 * mm, 5 * mm])
    meta_t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    logo_t = Table(
        [
            [logo],
            [Spacer(1, 2)],
            [Paragraph("<i>Precision Leads. Engineered by Intelligence.</i>", S["tagline"])],
        ],
        colWidths=[80 * mm],
    )
    logo_t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    row = Table([[logo_t, meta_t]], colWidths=[90 * mm, 84 * mm])
    row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return row


def parties_block(cfg, S):
    f = cfg["from"]
    from_lines = [
        Paragraph("FROM", S["section"]),
        Paragraph(f["legal_name"], S["body"]),
    ]
    for line in f["address_lines"]:
        from_lines.append(Paragraph(line, S["body"]))
    from_lines.append(Spacer(1, 6))
    from_lines.append(Paragraph(f"Phone: {f['phone']}", S["body"]))
    from_lines.append(Paragraph(f"Web: {f['web']}", S["body"]))
    from_lines.append(Paragraph(f"TRN: {f['trn']}", S["body"]))

    c = cfg["client"]
    to_lines = [
        Paragraph("BILL TO", S["section"]),
        Paragraph(c["legal_name"], S["body_bold"]),
    ]
    if c.get("trn"):
        label = c.get("trn_label") or "TRN"
        to_lines.append(Paragraph(f"{label}: {c['trn']}", S["body"]))
    if c.get("registration"):
        to_lines.append(Paragraph(c["registration"], S["body"]))
    if c.get("contact_name"):
        to_lines.append(Paragraph(f"Contact: {c['contact_name']}", S["body"]))
    if c.get("contact_email"):
        to_lines.append(Paragraph(f"Email: {c['contact_email']}", S["body"]))
    to_lines.append(Paragraph(c["country_label"], S["body"]))

    party = Table([[from_lines, to_lines]], colWidths=[87 * mm, 87 * mm])
    party.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return party


def items_block(cfg, S):
    currency = cfg["currency"]

    header_style = ParagraphStyle("h", fontName="Helvetica-Bold",
                                  fontSize=9, textColor=colors.white)
    header_center = ParagraphStyle("h", fontName="Helvetica-Bold",
                                   fontSize=9, textColor=colors.white,
                                   alignment=TA_CENTER)
    header_right = ParagraphStyle("h", fontName="Helvetica-Bold",
                                  fontSize=9, textColor=colors.white,
                                  alignment=TA_RIGHT)

    rows = [[
        Paragraph("<b>DESCRIPTION</b>", header_style),
        Paragraph("<b>QTY</b>", header_center),
        Paragraph("<b>UNIT PRICE</b>", header_right),
        Paragraph("<b>AMOUNT</b>", header_right),
    ]]

    for item in cfg["items"]:
        desc_html = item["description_html"]
        desc = Paragraph(desc_html, S["body"])
        qty = str(item.get("qty", 1))
        amount = float(item["amount"])
        unit_price = float(item.get("unit_price", amount))
        prefix = "-" if item.get("is_credit_note") else ""
        rows.append([
            desc, qty,
            f"{prefix}{fmt(abs(unit_price), currency)}",
            f"{prefix}{fmt(abs(amount), currency)}",
        ])

    items = Table(rows, colWidths=[100 * mm, 14 * mm, 30 * mm, 30 * mm])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), GOLD),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CREAM]),
    ]
    for r in range(1, len(rows)):
        style.append(("LINEBELOW", (0, r), (-1, r), 0.4, LIGHT_GRAY))
    items.setStyle(TableStyle(style))
    return items


def totals_block(cfg, S):
    currency = cfg["currency"]

    subtotal_services = sum(
        float(i["amount"]) for i in cfg["items"] if not i.get("is_credit_note")
    )
    credit_total = sum(
        abs(float(i["amount"])) for i in cfg["items"] if i.get("is_credit_note")
    )
    net_subtotal = subtotal_services - credit_total
    vat_rate = float(cfg.get("vat_rate", 0.0))
    vat_amount = round(net_subtotal * vat_rate, 2)
    total = net_subtotal + vat_amount

    rows = []
    if credit_total > 0:
        rows.append(["Subtotal (services)", fmt(subtotal_services, currency)])
        rows.append(["Credit note", f"-{fmt(credit_total, currency)}"])
        rows.append(["Net subtotal", fmt(net_subtotal, currency)])
    else:
        rows.append(["Subtotal", fmt(net_subtotal, currency)])

    vat_label = cfg.get("vat_label") or (
        f"VAT ({int(vat_rate * 100)}%)" if vat_rate > 0 else "VAT (0%)"
    )
    rows.append([vat_label, fmt(vat_amount, currency)])
    rows.append([
        Paragraph("<b>Total Due</b>", S["total_label"]),
        Paragraph(f"<b>{fmt(total, currency)}</b>", S["total_val"]),
    ])

    inner = Table(rows, colWidths=[60 * mm, 40 * mm])
    inner.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -2), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -2), 9),
        ("TEXTCOLOR", (0, 0), (-1, -2), CHARCOAL),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEABOVE", (0, -1), (-1, -1), 0.6, GOLD),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, -1), (-1, -1), 8),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))

    wrap = Table([["", inner]], colWidths=[74 * mm, 100 * mm])
    wrap.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return wrap, total, vat_amount


def stripe_block(cfg, S):
    """Render PAY NOW block. Supports either:
      stripe.url -> single button with "PAY NOW" label, or
      stripe.buttons -> list of {label, url, amount?} for multiple buttons stacked.
    """
    stripe_cfg = cfg["stripe"]

    if stripe_cfg.get("buttons"):
        buttons_data = stripe_cfg["buttons"]
    else:
        buttons_data = [{"label": "PAY NOW", "url": stripe_cfg["url"]}]

    multi = len(buttons_data) > 1
    button_height_mm = 10 if multi else 14
    label_font_size = 11 if multi else 14

    # Build pay_now style with the right size
    btn_style = ParagraphStyle(
        "btn_dynamic", parent=S["pay_now"],
        fontSize=label_font_size, leading=label_font_size + 3,
    )

    rows = [[Paragraph("PAY ONLINE", S["section"])]]

    for i, btn in enumerate(buttons_data):
        label = btn.get("label", "PAY NOW")
        url = btn["url"]
        amount = btn.get("amount")
        currency = cfg.get("currency", "AED")

        if amount is not None and multi:
            label_text = f"{label} · {currency} {amount:,.0f}"
        else:
            label_text = label

        button = Table(
            [[Paragraph(label_text, btn_style)]],
            colWidths=[80 * mm],
            rowHeights=[button_height_mm * mm],
        )
        button.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), GOLD),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        rows.append([button])
        rows.append([Spacer(1, 2)])
        rows.append([Paragraph(url, S["pay_url"])])
        if i < len(buttons_data) - 1:
            rows.append([Spacer(1, 5)])

    block = Table(rows, colWidths=[80 * mm])
    block.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return block


def zatca_block(cfg, S, total: float, vat: float):
    z = cfg.get("zatca", {})
    seller = z.get("seller_name") or cfg["from"]["legal_name"]
    vat_no = z.get("vat_no") or cfg["from"]["trn"]
    date_iso = z.get("date_iso", "")

    kv = [
        Paragraph(f"Seller: {seller}", S["zatca_kv"]),
        Paragraph(f"VAT No: {vat_no}", S["zatca_kv"]),
    ]
    if date_iso:
        kv.append(Paragraph(f"Date: {date_iso}", S["zatca_kv"]))
    kv.append(Paragraph(
        f"Total: {fmt(total, cfg['currency'])}  VAT: {fmt(vat, cfg['currency'])}",
        S["zatca_kv"],
    ))

    qr_path = z.get("qr_image_path")
    if qr_path and Path(qr_path).is_file():
        qr_img = Image(qr_path, width=22 * mm, height=22 * mm)
    else:
        qr_img = Table(
            [[Paragraph("[QR placeholder]", S["zatca_kv"])]],
            colWidths=[22 * mm], rowHeights=[22 * mm],
        )
        qr_img.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.4, LIGHT_GRAY),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))

    inner = Table([[qr_img, kv]], colWidths=[26 * mm, 54 * mm])
    inner.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    block = Table(
        [
            [Paragraph("KSA E-INVOICE QR (ZATCA)", S["section"])],
            [inner],
        ],
        colWidths=[80 * mm],
    )
    block.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return block


def payment_addons_row(cfg, S, total: float, vat: float):
    """Side-by-side row for ZATCA QR + Stripe button (whichever are enabled)."""
    z_on = cfg.get("zatca", {}).get("enabled")
    s_on = cfg.get("stripe", {}).get("enabled")
    if not (z_on or s_on):
        return None

    left = zatca_block(cfg, S, total, vat) if z_on else ""
    right = stripe_block(cfg, S) if s_on else ""

    row = Table([[left, right]], colWidths=[87 * mm, 87 * mm])
    row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return row


def make_footer(cfg):
    """Footer: light gray rule + LV mark on the left + inline info line on the same baseline.

    Default layout matches the canonical Luxvance invoice template:
      LUXVANCE  ·  {legal_name}  ·  {web}  ·  {phone}
    drawn at 8pt charcoal, vertically centered with the LV mark just to its left.
    A light gray rule sits a few millimeters above the row.

    Layout is driven by cfg["footer"]. No silent fallbacks: if the logo PNG is
    missing, require_logo() raises before doc.build() ever runs (see render()).
    """
    logo_path = require_logo(cfg["logo_footer_path"], "footer")
    footer_cfg = cfg.get("footer", {})
    logo_w_mm = float(footer_cfg.get("logo_width_mm", 8))
    bottom_margin_mm = float(footer_cfg.get("bottom_margin_mm", 10))
    position = footer_cfg.get("logo_position", "left")
    tagline = footer_cfg.get("tagline")  # optional; None → omit
    tagline_below = bool(footer_cfg.get("tagline_below_logo", False))

    aspect = aspect_ratio(logo_path)
    logo_w = logo_w_mm * mm
    logo_h = logo_w * aspect

    def on_page(canvas, _doc):
        canvas.saveState()
        page_w = A4[0]
        side_margin = 18 * mm

        # Baseline of the info-line row, measured from the page bottom.
        row_y = bottom_margin_mm * mm

        # Logo y so its vertical center sits ~1.2 mm above the text baseline,
        # which optically aligns small caps text with the LV mark.
        text_cap_height = 2.0 * mm  # approx for Helvetica 8pt
        logo_y = row_y + (text_cap_height - logo_h) / 2

        # Horizontal rule sits above the row with breathing room.
        rule_y = row_y + logo_h + (3 * mm)

        # Horizontal rule
        canvas.setStrokeColor(LIGHT_GRAY)
        canvas.setLineWidth(0.4)
        canvas.line(side_margin, rule_y, page_w - side_margin, rule_y)

        # Logo placement
        if position == "center":
            logo_x = (page_w - logo_w) / 2
        elif position == "right":
            logo_x = page_w - side_margin - logo_w
        else:  # "left"
            logo_x = side_margin

        canvas.drawImage(
            logo_path, logo_x, logo_y,
            width=logo_w, height=logo_h, mask="auto",
        )

        # Inline info line, charcoal, drawn just to the right of the logo.
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(CHARCOAL)
        f = cfg["from"]
        info = (
            f"LUXVANCE  ·  {f['legal_name']}  ·  "
            f"{f['web'].replace('https://', '').rstrip('/')}  ·  "
            f"{f['phone']}"
        )
        if position == "left":
            text_x = logo_x + logo_w + (3 * mm)
            canvas.drawString(text_x, row_y, info)
        elif position == "right":
            # text to the left of the logo, right-aligned
            text_x = logo_x - (3 * mm)
            canvas.drawRightString(text_x, row_y, info)
        else:  # center: stack info under the logo
            canvas.drawCentredString(page_w / 2, row_y - (4 * mm), info)

        # Optional tagline (only if explicitly requested in config)
        if tagline_below and tagline:
            canvas.setFont("Helvetica-Oblique", 7)
            canvas.setFillColor(GOLD)
            canvas.drawCentredString(page_w / 2, row_y - (4 * mm), tagline)

        canvas.restoreState()

    return on_page


def payment_plan_block(cfg, S):
    """Optional, prominent payment-plan table shown right under the Total Due.

    Config shape:
        "payment_plan": {
            "title": "PAYMENT PLAN",            # optional, defaults to PAYMENT PLAN
            "intro": "Split into two payments:", # optional one-liner
            "rows": [
                {"label": "Advance",
                 "method": "Bank transfer",
                 "due": "Monday May 4, 2026",
                 "amount": 10000.00,
                 "highlight": true},   # optional, draws extra attention
                ...
            ]
        }

    Renders a gold-headed table with WHEN / METHOD / DUE DATE / AMOUNT columns.
    Highlight rows get a soft cream background.
    """
    plan = cfg["payment_plan"]
    currency = cfg["currency"]
    title = plan.get("title", "PAYMENT PLAN")
    intro = plan.get("intro")
    rows_cfg = plan["rows"]

    header_style = ParagraphStyle("h", fontName="Helvetica-Bold",
                                  fontSize=9, textColor=colors.white)
    header_right = ParagraphStyle("h", fontName="Helvetica-Bold",
                                  fontSize=9, textColor=colors.white,
                                  alignment=TA_RIGHT)
    amount_style = ParagraphStyle("amt", fontName="Helvetica-Bold",
                                  fontSize=11, textColor=BLACK,
                                  alignment=TA_RIGHT)

    table_rows = [[
        Paragraph("<b>WHEN</b>", header_style),
        Paragraph("<b>METHOD</b>", header_style),
        Paragraph("<b>DUE</b>", header_style),
        Paragraph("<b>AMOUNT</b>", header_right),
    ]]

    for row in rows_cfg:
        table_rows.append([
            Paragraph(f"<b>{row['label']}</b>", S["body"]),
            Paragraph(row["method"], S["body"]),
            Paragraph(row["due"], S["body"]),
            Paragraph(f"<b>{fmt(float(row['amount']), currency)}</b>", amount_style),
        ])

    tbl = Table(table_rows, colWidths=[42 * mm, 50 * mm, 42 * mm, 40 * mm])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), GOLD),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LIGHT_GRAY),
    ]
    # Optional cream highlight rows
    for r, row in enumerate(rows_cfg, start=1):
        if row.get("highlight"):
            style.append(("BACKGROUND", (0, r), (-1, r), CREAM))
    tbl.setStyle(TableStyle(style))

    container = [Paragraph(title, S["section"])]
    if intro:
        container.append(Paragraph(intro, S["body"]))
        container.append(Spacer(1, 4))
    container.append(tbl)
    return container


def render(cfg: dict, output_path: str):
    # Pre-flight: validate logo paths up front so we never enter ReportLab with
    # a missing PNG and silently degrade. require_logo() raises FileNotFoundError
    # with the resolved path so the caller can surface it directly.
    require_logo(cfg.get("logo_header_path"), "header")
    require_logo(cfg.get("logo_footer_path"), "footer")

    output_path = output_path or cfg["output_path"]
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"Invoice {cfg['invoice_number']} - {cfg['client']['legal_name']}",
        author=cfg["from"]["legal_name"],
    )

    S = build_styles()
    story = []

    story.append(header_block(cfg, S))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.6, color=GOLD,
                            spaceBefore=4, spaceAfter=10))

    story.append(parties_block(cfg, S))
    story.append(Spacer(1, 14))

    story.append(items_block(cfg, S))
    story.append(Spacer(1, 10))

    totals_wrap, total, vat = totals_block(cfg, S)
    story.append(totals_wrap)
    story.append(Spacer(1, 14))

    # Optional payment plan block right after the Total Due
    if cfg.get("payment_plan"):
        for el in payment_plan_block(cfg, S):
            story.append(el)
        story.append(Spacer(1, 16))
    else:
        story.append(Spacer(1, 8))

    addons = payment_addons_row(cfg, S, total, vat)
    if addons is not None:
        story.append(addons)
        story.append(Spacer(1, 18))

    bank = cfg["bank"]
    story.append(Paragraph("BANK TRANSFER DETAILS", S["section"]))
    for line in [
        f"Bank: {bank['name']}",
        f"Account Holder: {bank['account_holder']}",
        f"IBAN: {bank['iban']}",
        f"SWIFT/BIC: {bank['swift']}",
        f"Bank Address: {bank['address']}",
    ]:
        story.append(Paragraph(line, S["body"]))
    story.append(Spacer(1, 14))

    if cfg.get("notes"):
        story.append(Paragraph("NOTES", S["section"]))
        story.append(Paragraph(cfg["notes"], S["body"]))

    on_page = make_footer(cfg)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return output_path


def main():
    p = argparse.ArgumentParser(description="Render a Luxvance invoice PDF.")
    p.add_argument("--config", required=True, help="Path to invoice JSON config.")
    p.add_argument("--output", help="Override the output PDF path.")
    args = p.parse_args()

    with open(args.config, "r", encoding="utf-8") as fh:
        cfg = json.load(fh)

    out = render(cfg, args.output)
    print(f"Saved: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

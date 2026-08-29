"""
Generates the client-facing Price Quote PDF. Design copied from a real
reference document the studio owner provided (2026-08-22), with two
deliberate simplifications per their instruction: one row per work item
(no per-material price breakdown) and no photo column (no image-upload
mechanism exists anywhere in this app).

A "work item" here is one already-priced job, in the same shape
price_parsed_lines() already returns (height_cm/width_cm/order_quantity/
lines[]/quantity_price/final_price_incl_vat) -- this module only formats
and lays out numbers/text that are already computed elsewhere; it does no
pricing itself.
"""
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# reportlab's built-in base-14 fonts (Helvetica etc.) use WinAnsi/MacRoman
# encoding, which has no ₪ (Shekel, U+20AA) glyph -- it silently renders as
# a black box. Noto Sans (bundled in fonts/, SIL Open Font License, free to
# redistribute) has full Unicode coverage including currency symbols, and
# is registered once at import time rather than relying on any system font
# -- a font installed only on this Mac wouldn't exist on Render's Linux
# container, which is what actually generates these PDFs in production.
#
# Noto Sans itself has ZERO Hebrew glyphs despite the "full Unicode
# coverage" claim above -- confirmed via fontTools after a real quote's
# Hebrew work names rendered as blank space, not even a black box (studio
# owner, 2026-08-29). Noto Sans Hebrew (same OFL license) is a separate
# family; static Regular/Bold instances extracted from Google Fonts'
# variable-font release via fontTools.varLib.instancer, since only a
# single [wdth,wght]-axis file is published upstream.
_FONTS_DIR = Path(__file__).resolve().parent / "fonts"
pdfmetrics.registerFont(TTFont("NotoSans", _FONTS_DIR / "NotoSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("NotoSans-Bold", _FONTS_DIR / "NotoSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("NotoSansHebrew", _FONTS_DIR / "NotoSansHebrew-Regular.ttf"))
pdfmetrics.registerFont(TTFont("NotoSansHebrew-Bold", _FONTS_DIR / "NotoSansHebrew-Bold.ttf"))

_HEBREW_RE = re.compile(r"[֐-׿]")


def _font_for(text, bold=False):
    """Picks the Hebrew or Latin Noto Sans variant based on the text's
    script -- reportlab has no automatic font-fallback across a Paragraph,
    so mixed-script client-supplied text (a work name, a client name)
    needs the right single font chosen up front. Reuses the same Hebrew-
    detection approach as quote_reply.py/email_ai.py elsewhere in this app."""
    base = "NotoSansHebrew" if _HEBREW_RE.search(text or "") else "NotoSans"
    return f"{base}-Bold" if bold else base

STUDIO_NAME = "The Print House"
STUDIO_ADDRESS_LINE = "The Print House LTD, Hazerem 1 St. Tel Aviv, ISRAEL, VAT no. 514717255"
STUDIO_CONTACT_LINE = "T 03-6855362   E Info@theprinthouse.co.il   W www.theprinthouse.co.il"

# Mostly "dropdown"-kind slots, since those represent a real client-facing
# choice -- the internal structural/bookkeeping "fixed"-kind rows (Lamelo,
# Upper Lamela, Wood/Paper/Passpartout Glyph, etc.) stay deliberately left
# out of the description text, the reference document never mentions them
# either. row17_canvas (Stretcher) is the one deliberate exception: it's
# "fixed"-kind but a real, visible, chargeable add-on the client should
# see acknowledged on their quote, not silently folded into the total
# (studio owner, 2026-08-29, after a stretcher's price wasn't showing up
# anywhere on a printed quote and they assumed it hadn't been charged).
PRINT_SLOTS = {"row11_paper", "row33_uv_print", "row34_uv_facemount"}
MOUNT_SLOTS = {"row29_front_material", "row30_back_material", "row31_back_frame"}
FRAME_SLOTS = {"row23_profile_preset", "row24_glasses", "row25_double_glass",
                "row26_passpartout", "row27_paint", "row28_drawing", "row17_canvas"}

PAGE_SIZE = A4
MARGIN = 18 * mm


def _bucket_phrase(prefix, lines, slot_set):
    names = [l["item_name"] for l in lines if l["slot_key"] in slot_set and l.get("item_name") and not l.get("unpriced")]
    return f"{prefix}: {', '.join(names)}" if names else None


def describe_work_item(entry):
    """entry: one of price_parsed_lines()'s `quotes` entries. Returns a
    list of description lines (Print/Mount/Frame), skipping empty buckets."""
    lines = entry["lines"]
    phrases = [
        _bucket_phrase("Print", lines, PRINT_SLOTS),
        _bucket_phrase("Mount", lines, MOUNT_SLOTS),
        _bucket_phrase("Frame", lines, FRAME_SLOTS),
    ]
    return [p for p in phrases if p]


def _fmt_money(amount):
    # Round display only -- matches the calculator UI's fmt() (JS,
    # maximumFractionDigits: 0), which the studio owner confirmed is the
    # convention they want here too. The underlying stored amounts stay
    # full-precision; only what's printed is rounded.
    return f"₪ {round(amount):,}"


def _styles():
    return {
        "title": ParagraphStyle("title", fontName="NotoSans-Bold", fontSize=16, leading=19),
        "quote_no": ParagraphStyle("quote_no", fontName="NotoSans-Bold", fontSize=10, leading=13),
        "client_label": ParagraphStyle("client_label", fontName="NotoSans-Bold", fontSize=9, leading=12),
        "client_line": ParagraphStyle("client_line", fontName="NotoSans-Bold", fontSize=9, leading=12),
        "section_title": ParagraphStyle("section_title", fontName="NotoSans-Bold", fontSize=10, leading=13),
        "th": ParagraphStyle("th", fontName="NotoSans-Bold", fontSize=9, leading=11),
        "cell": ParagraphStyle("cell", fontName="NotoSans", fontSize=9, leading=12),
        "cell_center": ParagraphStyle("cell_center", fontName="NotoSans", fontSize=9, leading=12, alignment=1),
        "cell_right": ParagraphStyle("cell_right", fontName="NotoSans", fontSize=9, leading=12, alignment=TA_RIGHT),
        "footer": ParagraphStyle("footer", fontName="NotoSans", fontSize=7.5, leading=10, textColor=colors.grey),
        "footer_bold": ParagraphStyle("footer_bold", fontName="NotoSans-Bold", fontSize=7.5, leading=10, textColor=colors.grey),
        "small": ParagraphStyle("small", fontName="NotoSans", fontSize=8.5, leading=11),
        "small_bold": ParagraphStyle("small_bold", fontName="NotoSans-Bold", fontSize=9, leading=12),
    }


def build_quote_pdf(quote, output_path=None):
    """
    quote: {
      "quote_number": int, "client_name": str, "client_phone": str or None,
      "client_email": str or None, "created_date": "YYYY-MM-DD" (or datetime),
      "work_items": [ ...price_parsed_lines() quote entries... ],
      "vat_rate": float,
    }
    Returns the PDF bytes. Also writes to output_path if given.
    """
    styles = _styles()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=PAGE_SIZE,
        leftMargin=MARGIN, rightMargin=MARGIN, topMargin=28 * mm, bottomMargin=22 * mm,
    )

    created_date = quote["created_date"]
    if isinstance(created_date, datetime):
        date_str = created_date.strftime("%d.%m.%Y")
    else:
        date_str = datetime.strptime(created_date, "%Y-%m-%d").strftime("%d.%m.%Y")
    quote_no = quote["quote_number"]
    client_name = quote["client_name"]

    def header_footer(canvas, _doc):
        canvas.saveState()
        # Header
        canvas.setFont("NotoSans-Bold", 16)
        canvas.circle(MARGIN + 3, PAGE_SIZE[1] - 20 * mm, 3.2, fill=1, stroke=0)
        canvas.drawString(MARGIN + 10, PAGE_SIZE[1] - 22.5 * mm, STUDIO_NAME)
        canvas.setLineWidth(0.75)
        canvas.rect(PAGE_SIZE[0] - MARGIN - 62 * mm, PAGE_SIZE[1] - 24 * mm, 62 * mm, 9 * mm, stroke=1, fill=0)
        canvas.setFont("NotoSans-Bold", 9.5)
        canvas.drawCentredString(
            PAGE_SIZE[0] - MARGIN - 31 * mm, PAGE_SIZE[1] - 20.5 * mm,
            f"Price Quote #{quote_no} — ({date_str})",
        )
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, PAGE_SIZE[1] - 26 * mm, PAGE_SIZE[0] - MARGIN, PAGE_SIZE[1] - 26 * mm)

        # Footer
        y = 16 * mm
        canvas.setFillColor(colors.grey)
        canvas.setFont("NotoSans-Bold", 7.5)
        canvas.drawString(MARGIN, y, f"Price Quote #{quote_no} — ({date_str})")
        canvas.setFont(_font_for(client_name, bold=True), 7.5)
        canvas.drawString(MARGIN, y - 3.2 * mm, f"Prepared for {client_name}")
        canvas.setFont("NotoSans", 7.5)
        contact_bits = []
        if quote.get("client_phone"):
            contact_bits.append(f"T {quote['client_phone']}")
        if quote.get("client_email"):
            contact_bits.append(f"E {quote['client_email']}")
        if contact_bits:
            canvas.drawString(MARGIN, y - 6.4 * mm, "   ".join(contact_bits))
        canvas.setLineWidth(0.5)
        canvas.setStrokeColor(colors.grey)
        canvas.line(MARGIN, y - 8.5 * mm, PAGE_SIZE[0] - MARGIN, y - 8.5 * mm)
        canvas.drawString(MARGIN, y - 11.5 * mm, STUDIO_ADDRESS_LINE)
        canvas.drawString(MARGIN, y - 14.7 * mm, STUDIO_CONTACT_LINE)
        canvas.restoreState()

    story = []

    client_block = [f'<font face="{_font_for(client_name, bold=True)}">Prepared for {escape(client_name)}</font>']
    if quote.get("client_phone"):
        client_block.append(f"T {quote['client_phone']}")
    if quote.get("client_email"):
        client_block.append(f"E {quote['client_email']}")
    story.append(Paragraph("<br/>".join(client_block), styles["client_line"]))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Work Items", styles["section_title"]))
    story.append(Spacer(1, 2 * mm))

    header_row = [
        Paragraph("#", styles["th"]), Paragraph("Size (cm)", styles["th"]),
        Paragraph("Description", styles["th"]), Paragraph("Qty", styles["th"]),
        Paragraph("Total Price", styles["th"]),
    ]
    rows = [header_row]
    subtotal = 0.0
    for i, entry in enumerate(quote["work_items"], start=1):
        desc_lines = describe_work_item(entry)
        # entry["description"] holds the work's own name (e.g. from a
        # photographed client-meeting worksheet's "Work:" line) -- shown
        # as a bold heading above the Print/Mount/Frame breakdown so the
        # client can tell which piece each row is (studio owner,
        # 2026-08-29). Empty for quotes built the usual way through the
        # quick-quote UI, which never sets this field.
        work_name = (entry.get("description") or "").strip()
        if work_name:
            desc_lines = [f'<font face="{_font_for(work_name, bold=True)}">{escape(work_name)}</font>'] + desc_lines
        desc_html = "<br/>".join(desc_lines) if desc_lines else "—"
        size_str = f"{entry['height_cm']:g} x {entry['width_cm']:g}"
        total = entry["quantity_price"]
        subtotal += total
        rows.append([
            Paragraph(str(i), styles["cell_center"]),
            Paragraph(size_str, styles["cell_center"]),
            Paragraph(desc_html, styles["cell"]),
            Paragraph(str(entry["order_quantity"]), styles["cell_center"]),
            Paragraph(_fmt_money(total), styles["cell_right"]),
        ])

    col_widths = [10 * mm, 24 * mm, None, 14 * mm, 28 * mm]
    available_width = PAGE_SIZE[0] - 2 * MARGIN
    fixed = sum(w for w in col_widths if w)
    col_widths = [w or (available_width - fixed) for w in col_widths]

    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f0ea")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfcabf")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 8 * mm))

    vat_rate = quote.get("vat_rate", 0.18)
    discount_percent = quote.get("discount_percent", 0)
    delivery = quote.get("delivery")
    delivery_price = delivery["price"] if delivery else 0
    discounted = subtotal * (1 - discount_percent / 100)
    grand_total = discounted + delivery_price
    vat_amount = grand_total * vat_rate
    total_with_vat = grand_total + vat_amount

    left_block = [
        Paragraph("Payment Terms: Not paid", styles["small"]),
        Spacer(1, 10 * mm),
        Paragraph("Full name: " + "_" * 40, styles["small"]),
        Spacer(1, 6 * mm),
        Paragraph("Signature: " + "_" * 40, styles["small"]),
    ]
    summary_rows = []
    if discount_percent or delivery:
        summary_rows.append(["Subtotal", _fmt_money(subtotal)])
        if discount_percent:
            summary_rows.append([f"Discount {discount_percent:g}%", "-" + _fmt_money(subtotal - discounted)])
        if delivery:
            summary_rows.append([f"Delivery ({delivery['city']})", _fmt_money(delivery_price)])
    summary_rows += [
        ["Total Price", _fmt_money(grand_total)],
        [f"VAT {vat_rate*100:.1f}%", _fmt_money(vat_amount)],
        ["Total w/Tax", _fmt_money(total_with_vat)],
    ]
    summary_table = Table(
        [[Paragraph(f"<b>{a}</b>", styles["small_bold"]), Paragraph(f"<b>{b}</b>", styles["small_bold"])]
         for a, b in summary_rows],
        colWidths=[40 * mm, 30 * mm],
    )
    summary_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.75, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.75, colors.black),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    bottom_table = Table([[left_block, summary_table]], colWidths=[available_width - 75 * mm, 75 * mm])
    bottom_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(bottom_table)

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    pdf_bytes = buf.getvalue()
    if output_path:
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
    return pdf_bytes

"""
Generates a blank, printable A4 worksheet the studio fills out by hand
during a client meeting -- one row per piece the client wants framed,
with checkboxes for frame type and common add-ons. After the meeting,
staff photograph the filled-in sheet; a future step reads that photo
back and turns it into a real price quote (studio owner, 2026-08-27).
This module only draws the blank template -- no quote data involved.
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas

_FONTS_DIR = Path(__file__).resolve().parent / "fonts"
if "NotoSans" not in pdfmetrics.getRegisteredFontNames():
    pdfmetrics.registerFont(TTFont("NotoSans", _FONTS_DIR / "NotoSans-Regular.ttf"))
    pdfmetrics.registerFont(TTFont("NotoSans-Bold", _FONTS_DIR / "NotoSans-Bold.ttf"))

STUDIO_NAME = "The Print House"

PAGE_SIZE = A4
PAGE_W, PAGE_H = PAGE_SIZE
MARGIN = 15 * mm
LINE_GREY = colors.HexColor("#cfcabf")
HEADER_FILL = colors.HexColor("#f2f0ea")

NUM_ROWS = 8
FRAME_TYPES = ["Box Frame", "Float for Canvas", "Aluminum Frame"]
ADD_ONS = ["Passpartout", "Art Glass", "Special Color", "Drawing", "Stretcher", "Special Wood"]


def _checkbox(c, x, y, label, size=3.4 * mm, font_size=8.5):
    """Draws one empty checkbox square with a label to its right; returns
    the x position immediately after the label, for chaining more boxes
    on the same line."""
    c.setLineWidth(0.6)
    c.setStrokeColor(colors.black)
    c.rect(x, y, size, size, stroke=1, fill=0)
    c.setFont("NotoSans", font_size)
    c.setFillColor(colors.black)
    text_x = x + size + 1.6 * mm
    c.drawString(text_x, y + 0.4 * mm, label)
    return text_x + c.stringWidth(label, "NotoSans", font_size) + 5 * mm


def build_intake_form(output_path=None):
    buf_path = output_path
    from io import BytesIO
    buf = BytesIO()
    c = pdfcanvas.Canvas(buf, pagesize=PAGE_SIZE)

    # --- Header -------------------------------------------------------
    top = PAGE_H - MARGIN
    c.setFont("NotoSans-Bold", 15)
    c.circle(MARGIN + 3, top - 4, 3.2, fill=1, stroke=0)
    c.drawString(MARGIN + 10, top - 6.5, STUDIO_NAME)
    c.setFont("NotoSans-Bold", 12)
    c.drawRightString(PAGE_W - MARGIN, top - 6.5, "Client Meeting Worksheet")
    c.setLineWidth(0.75)
    c.setStrokeColor(colors.black)
    c.line(MARGIN, top - 11 * mm, PAGE_W - MARGIN, top - 11 * mm)

    # Client name / date / prepared-by line
    y = top - 19 * mm
    c.setFont("NotoSans", 10)
    c.drawString(MARGIN, y, "Client Name:")
    c.setLineWidth(0.5)
    c.line(MARGIN + 26 * mm, y - 1, MARGIN + 105 * mm, y - 1)
    c.drawString(MARGIN + 110 * mm, y, "Date:")
    c.line(MARGIN + 122 * mm, y - 1, PAGE_W - MARGIN, y - 1)

    table_top = y - 8 * mm

    # --- Table ----------------------------------------------------------
    available_w = PAGE_W - 2 * MARGIN
    num_col_w = 9 * mm
    content_col_w = available_w - num_col_w
    header_row_h = 6 * mm
    footer_note_h = 12 * mm
    table_bottom_min = MARGIN + footer_note_h
    row_h = (table_top - table_bottom_min - header_row_h) / NUM_ROWS

    # Column header row
    c.setFillColor(HEADER_FILL)
    c.rect(MARGIN, table_top - header_row_h, available_w, header_row_h, stroke=0, fill=1)
    c.setStrokeColor(LINE_GREY)
    c.setLineWidth(0.5)
    c.rect(MARGIN, table_top - header_row_h, available_w, header_row_h, stroke=1, fill=0)
    c.line(MARGIN + num_col_w, table_top - header_row_h, MARGIN + num_col_w, table_top)
    c.setFont("NotoSans-Bold", 8.5)
    c.setFillColor(colors.black)
    c.drawCentredString(MARGIN + num_col_w / 2, table_top - header_row_h + 2 * mm, "#")
    c.drawString(MARGIN + num_col_w + 3 * mm, table_top - header_row_h + 2 * mm,
                 "Work name / size, frame type, and add-ons")

    row_top = table_top - header_row_h
    for i in range(1, NUM_ROWS + 1):
        row_bottom = row_top - row_h
        c.setStrokeColor(LINE_GREY)
        c.setLineWidth(0.5)
        c.rect(MARGIN, row_bottom, available_w, row_h, stroke=1, fill=0)
        c.line(MARGIN + num_col_w, row_bottom, MARGIN + num_col_w, row_top)

        c.setFont("NotoSans-Bold", 11)
        c.setFillColor(colors.black)
        c.drawCentredString(MARGIN + num_col_w / 2, row_top - row_h / 2 - 1.5 * mm, str(i))

        content_x = MARGIN + num_col_w + 3 * mm
        content_w = content_col_w - 6 * mm

        # Even vertical spacing between all four lines in the row --
        # matches the gap the studio owner liked between Add-ons and
        # Notes, applied consistently everywhere rather than just there
        # (studio owner, 2026-08-27). Line lengths themselves are back to
        # their original widths -- "more space" meant breathing room
        # between lines, not wider fill-in blanks.
        LINE_GAP = 7.0 * mm
        line1_y = row_top - 4.5 * mm
        line2_y = line1_y - LINE_GAP
        line3_y = line2_y - LINE_GAP
        line4_y = line3_y - LINE_GAP

        # Line 1: work name + size
        c.setFont("NotoSans", 8.5)
        c.drawString(content_x, line1_y, "Work:")
        c.setLineWidth(0.4)
        c.setStrokeColor(colors.HexColor("#999999"))
        name_line_end = content_x + content_w * 0.55
        c.line(content_x + 11 * mm, line1_y - 0.8, name_line_end, line1_y - 0.8)
        size_x = name_line_end + 4 * mm
        c.setFont("NotoSans", 8.5)
        c.drawString(size_x, line1_y, "Size:")
        c.line(size_x + 9 * mm, line1_y - 0.8, size_x + 24 * mm, line1_y - 0.8)
        c.drawString(size_x + 25 * mm, line1_y, "x")
        c.line(size_x + 28 * mm, line1_y - 0.8, size_x + 43 * mm, line1_y - 0.8)
        c.setFont("NotoSans", 7.5)
        c.setFillColor(colors.HexColor("#666666"))
        c.drawString(size_x + 44 * mm, line1_y, "cm")
        c.setFillColor(colors.black)

        # Line 2: frame type checkboxes
        box_y = line2_y - 0.3 * mm
        cx = content_x
        c.setFont("NotoSans", 7.5)
        c.setFillColor(colors.HexColor("#666666"))
        c.drawString(cx, line2_y + 0.2, "Frame:")
        c.setFillColor(colors.black)
        cx = content_x + 12 * mm
        for label in FRAME_TYPES:
            cx = _checkbox(c, cx, box_y, label)

        # Line 3: add-on checkboxes, all in one row
        box_y3 = line3_y - 0.3 * mm
        c.setFont("NotoSans", 7.5)
        c.setFillColor(colors.HexColor("#666666"))
        c.drawString(content_x, line3_y + 0.2, "Add-ons:")
        c.setFillColor(colors.black)
        cx = content_x + 15 * mm
        for label in ADD_ONS:
            if cx > MARGIN + available_w - 3 * mm:
                break
            cx = _checkbox(c, cx, box_y3, label, size=3 * mm, font_size=7.8)

        # Line 4 (if room): notes
        if row_h > 24 * mm:
            c.setFont("NotoSans", 7.5)
            c.setFillColor(colors.HexColor("#666666"))
            c.drawString(content_x, line4_y, "Notes:")
            c.setFillColor(colors.black)
            c.setLineWidth(0.4)
            c.setStrokeColor(colors.HexColor("#999999"))
            c.line(content_x + 11 * mm, line4_y - 0.8, MARGIN + available_w - 3 * mm, line4_y - 0.8)

        row_top = row_bottom

    # --- Footer note ------------------------------------------------
    c.setFont("NotoSans", 7.5)
    c.setFillColor(colors.HexColor("#666666"))
    c.drawString(MARGIN, MARGIN + 4 * mm,
                 "Photograph this sheet after the meeting to generate a price quote.")

    c.showPage()
    c.save()
    pdf_bytes = buf.getvalue()
    if buf_path:
        with open(buf_path, "wb") as f:
            f.write(pdf_bytes)
    return pdf_bytes


if __name__ == "__main__":
    build_intake_form("intake_form.pdf")
    print("wrote intake_form.pdf")

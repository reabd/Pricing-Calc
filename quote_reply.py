"""
Formats an already-computed quote (the `quotes` list produced by
price_parsed_lines() / the /api/quote/* endpoints) into client-facing
reply text matching the studio's real email style, as observed across six
months of sent mail (see studio_operations_and_communication_notes.md):
short and conversational, one price per job (not broken into internal
material/work cost lines), an explicit VAT statement on every quote, a
casual "let us know" close, and the standard signature block. Text only —
this never sends or drafts an actual email.
"""

# The studio's actual Gmail signature is language-invariant — it appears
# in this exact English form on nearly every outbound message regardless
# of whether the body is Hebrew or English (see
# studio_operations_and_communication_notes.md §1.5). Earlier drafts of
# this module translated it for the Hebrew path, which didn't match real
# mail — fixed to use the same block both ways.
SIGNATURE_EN = (
    "The Print House\n"
    "Hazerem 1, Tel Aviv\n"
    "Israel, 6816839\n"
    "tel: +972-3-6855362\n"
    "Open: Sunday - Thursday, 10:00 - 18:00\n"
    "Visit our website! www.theprinthouse.co.il"
)
SIGNATURE_HE = SIGNATURE_EN


def _price_for(entry, vat_included):
    return entry["final_price_incl_vat"] if vat_included else entry["quantity_price"]


def _description(entry):
    desc = (entry.get("description") or "").strip()
    if desc:
        return desc
    h, w = entry.get("height_cm"), entry.get("width_cm")
    if h and w:
        return f'{h:g}x{w:g} ס"מ'
    return "הפריט"


# Hebrew customer-facing labels for the glazing/facemount-finish catalog
# items clients most often ask to have spelled out explicitly (see the
# FAQ patterns in studio_operations_and_communication_notes.md — quotes
# routinely name the glazing/finish, e.g. "פרספקס רגיל" vs "זכוכית
# אנטירפלקטיבית", not just a bare price). Only covers terms with a
# reasonably confident translation; anything else falls back to the raw
# catalog name so it's still visible rather than silently dropped —
# review/replace those before sending.
MATERIAL_LABELS_HE = {
    "Acrylic Glossy 2mm": "פרספקס מבריק",
    "Acrylic Matt": "פרספקס מט",
    "Regular 2mm": "פרספקס/זכוכית רגילה",
    "Regular Double 2mm": "זכוכית כפולה רגילה",
    "Museum Glass UV 99% 2.5mm": "זכוכית מוזיאלית",
    "Optium Museum Acrylic 4.5mm": "פרספקס מוזיאלי",
    "Optium Museum Acrylic 99% 3mm": "פרספקס מוזיאלי",
    "UV 70% 2mm Tru View": "זכוכית אנטירפלקטיבית",
    "UV 70% 3 mm": "זכוכית אנטירפלקטיבית",
    "Nielsen UV70%": "זכוכית אנטירפלקטיבית",
}

# The component that actually determines "what kind of perspex/glass this
# is" — facemount/print finish (row29_front_material) or a framed piece's
# glazing (row24_glasses). Only one of these is normally present per job.
FINISH_SLOT_KEYS = ("row29_front_material", "row24_glasses")


def _finish_note(entry, language):
    for line in entry.get("lines", []):
        if line.get("slot_key") in FINISH_SLOT_KEYS:
            item = line["item_name"]
            return MATERIAL_LABELS_HE.get(item, item) if language == "he" else item
    return None


def _fmt(amount):
    return f"{amount:,.0f}"


# The self-service ordering system is only relevant when the client is
# printing a digital file — it's a print-then-frame upload flow. A client
# framing an existing original (a drawing, a painting, anything not being
# printed) has to bring the physical piece to the studio in person; there's
# nothing for them to do in the online system. row11_paper is the print
# component, so its presence on a quote is what marks "this job includes a
# print," e.g. absent on the box_drawing/aluminium_drawing presets used
# for framing an existing work on paper.
PRINT_SLOT_KEY = "row11_paper"


def _is_print_job(entry):
    return any(line.get("slot_key") == PRINT_SLOT_KEY for line in entry.get("lines", []))


# Hebrew imperative "update us" conjugates by the recipient's grammatical
# gender/number — "עדכן" (singular masculine), "עדכני" (singular feminine),
# "עדכנו" (plural, e.g. addressing a gallery/team as a group). There's no
# safe language-agnostic default, so the caller must say who they're
# writing to; "m" is only the fallback when nothing is specified.
CLOSING_ASK_HE = {
    "m": "עדכן אותנו",
    "f": "עדכני אותנו",
    "plural": "עדכנו אותנו",
}

# Self-service W2P (web-to-print) ordering system — for straightforward
# individual jobs, staff sometimes point the client here instead of (or
# alongside) an inline quote: the client can upload their own file and
# pick the framing/facemount option themselves. Also conjugated by
# recipient_form, same reasoning as CLOSING_ASK_HE. Not appended
# automatically to every quote (e.g. institutional/multi-item quotes with
# custom specs generally aren't a fit for self-service) — callers opt in
# via include_order_system_link.
ORDER_SYSTEM_URL = "https://order.theprinthouse.co.il/he"
ORDER_SYSTEM_NOTE_HE = {
    "m": "אתה מוזמן גם להיכנס למערכת ההזמנות האוטומטית שלנו באתר, להעלות את הקובץ ולבחור "
         "איזה סוג מסגור או הדבקה שאתה רוצה (יש גם Facemount).",
    "f": "את מוזמנת גם להיכנס למערכת ההזמנות האוטומטית שלנו באתר, להעלות את הקובץ ולבחור "
         "איזה סוג מסגור או הדבקה שאת רוצה (יש גם Facemount).",
    "plural": "אתם מוזמנים גם להיכנס למערכת ההזמנות האוטומטית שלנו באתר, להעלות את הקובץ ולבחור "
              "איזה סוג מסגור או הדבקה שאתם רוצים (יש גם Facemount).",
}
ORDER_SYSTEM_NOTE_EN = (
    "You're also welcome to use our automated ordering system on the website — upload your "
    "file and choose the framing or facemount option you'd like (Facemount is available too)."
)


def draft_reply_he(quotes, client_first_name=None, vat_included=False, signer_name=None,
                    recipient_form="m", include_order_system_link=False):
    """
    quotes: list of quote entries as returned in the `quotes` field of
    price_parsed_lines()'s result (each has description/height_cm/width_cm/
    quantity_price/final_price_incl_vat).
    vat_included: mirrors the studio's own always-explicit VAT disclaimer —
    True quotes the VAT-inclusive number and says "כולל מע\"מ", False (the
    default, matching the more common pattern in sampled mail) quotes the
    pre-VAT number and says "לא כולל מע\"מ".
    recipient_form: "m" | "f" | "plural" — grammatical gender/number of
    whoever is being addressed, so the closing "update us" line (and the
    order-system note, if included) conjugate correctly.
    include_order_system_link: also mention the self-service W2P ordering
    system (see ORDER_SYSTEM_NOTE_HE) — only actually added if at least one
    quoted job includes a print component (_is_print_job); framing an
    existing original has nothing to do with the upload system, so the
    flag is silently a no-op for print-less quotes rather than producing a
    wrong note.
    """
    lines = [f"מה נשמע{f' {client_first_name}' if client_first_name else ''}?", "", "אז ככה,"]

    for entry in quotes:
        desc = _description(entry)
        finish = _finish_note(entry, "he")
        if finish:
            desc = f"{desc} ({finish})"
        lines.append(f'{desc} - {_fmt(_price_for(entry, vat_included))} ש"ח')

    lines.append('המחירים כוללים מע"מ.' if vat_included else 'המחירים לא כוללים מע"מ.')

    if len(quotes) > 1:
        total = sum(_price_for(entry, vat_included) for entry in quotes)
        total_label = 'סה"כ כולל מע"מ' if vat_included else 'סה"כ לפני מע"מ'
        lines.append(f'{total_label}: {_fmt(total)} ש"ח')

    if include_order_system_link and any(_is_print_job(entry) for entry in quotes):
        note = ORDER_SYSTEM_NOTE_HE.get(recipient_form, ORDER_SYSTEM_NOTE_HE["m"])
        lines.append("")
        lines.append(note)
        lines.append(ORDER_SYSTEM_URL)

    closing_ask = CLOSING_ASK_HE.get(recipient_form, CLOSING_ASK_HE["m"])
    lines.append("")
    lines.append(closing_ask + (f", {signer_name}" if signer_name else "") + " :)")
    lines.append("תודה")
    lines.append("")
    lines.append(SIGNATURE_HE)
    return "\n".join(lines)


def draft_reply_en(quotes, client_first_name=None, vat_included=False, signer_name=None,
                    include_order_system_link=False):
    lines = [f"Hi{f' {client_first_name}' if client_first_name else ''},", "",
             "Thank you for your email. Below are the prices:"]

    for entry in quotes:
        desc = _description(entry)
        finish = _finish_note(entry, "en")
        if finish:
            desc = f"{desc} ({finish})"
        lines.append(f"{desc} - {_fmt(_price_for(entry, vat_included))} NIS")

    lines.append("Prices include VAT." if vat_included else "Prices do not include VAT.")

    if len(quotes) > 1:
        total = sum(_price_for(entry, vat_included) for entry in quotes)
        total_label = "Total incl. VAT" if vat_included else "Total before VAT"
        lines.append(f"{total_label}: {_fmt(total)} NIS")

    if include_order_system_link and any(_is_print_job(entry) for entry in quotes):
        lines.append("")
        lines.append(ORDER_SYSTEM_NOTE_EN)
        lines.append(ORDER_SYSTEM_URL)

    lines.append("")
    lines.append("Let us know if you'd like to proceed.")
    lines.append(f"Thanks,\n{signer_name}" if signer_name else "Thanks")
    lines.append("")
    lines.append(SIGNATURE_EN)
    return "\n".join(lines)


def draft_reply(quotes, client_first_name=None, vat_included=False, signer_name=None, language="he",
                 recipient_form="m", include_order_system_link=False):
    if language == "en":
        return draft_reply_en(quotes, client_first_name, vat_included, signer_name,
                               include_order_system_link)
    return draft_reply_he(quotes, client_first_name, vat_included, signer_name, recipient_form,
                           include_order_system_link)


# Matches the studio's real Gmail signature styling captured directly off
# a sent message (Georgia 9pt, gray body text, bold opening hours, bold
# "Visit our website!" lead-in with a real link) — see
# studio_operations_and_communication_notes.md §1.5. Used only when
# producing an actual Gmail draft (create_draft/update_draft's htmlBody);
# the plain-text draft_reply() output above is for the copy/paste-into-
# any-email-client path and stays plain on purpose.
SIGNATURE_HTML = (
    '<p style="margin:0;font-family:Georgia,serif;font-size:9pt;color:rgb(66,66,66);">The Print House</p>'
    '<p style="margin:0;font-family:Georgia,serif;font-size:9pt;color:rgb(66,66,66);">Hazerem 1, Tel Aviv</p>'
    '<p style="margin:0;font-family:Georgia,serif;font-size:9pt;color:rgb(66,66,66);">Israel, 6816839</p>'
    '<p style="margin:0;font-family:Georgia,serif;font-size:9pt;color:rgb(66,66,66);">tel: +972-3-6855362</p>'
    '<p style="margin:0;font-family:Georgia,serif;font-size:9pt;color:rgb(66,66,66);">'
    'Open: Sunday - Thursday, <b>10:00 - 18:00</b></p>'
    '<p style="margin:6px 0 0;font-family:Georgia,serif;font-size:9pt;">'
    '<b style="color:#000;">Visit our website!</b> '
    '<a href="http://www.theprinthouse.co.il/" style="color:rgb(17,85,204);">www.theprinthouse.co.il</a>'
    '</p>'
)


def to_html(text, language="he"):
    """
    Converts draft_reply()'s plain-text output into an HTML version for an
    actual Gmail draft: proper RTL/LTR paragraph alignment for the message
    body, and the real styled signature (SIGNATURE_HTML) instead of a bare
    plain-text URL that Gmail would auto-link/redirect-wrap unstyled.
    """
    body_text = text
    if body_text.endswith(SIGNATURE_EN):
        body_text = body_text[: -len(SIGNATURE_EN)].rstrip("\n")

    direction = "rtl" if language == "he" else "ltr"
    align = "right" if language == "he" else "left"
    paragraphs = [p for p in body_text.split("\n\n") if p.strip()]
    order_link_html = f'<a href="{ORDER_SYSTEM_URL}" style="color:rgb(17,85,204);">{ORDER_SYSTEM_URL}</a>'
    body_html = "".join(
        f'<p dir="{direction}" style="margin:0 0 12px;text-align:{align};'
        f'font-family:Arial,sans-serif;font-size:14px;">'
        + p.replace("\n", "<br>").replace(ORDER_SYSTEM_URL, order_link_html) + "</p>"
        for p in paragraphs
    )
    return body_html + SIGNATURE_HTML

"""
Reads a photographed client-meeting worksheet (see intake_form_pdf.py for
the blank template) and turns it into priced quote lines, using the Claude
API directly with vision (same ANTHROPIC_API_KEY/pattern as email_ai.py --
no interactive Claude Code session backs this).

Two-stage, deliberately: extract_worksheet() reads the photo into plain
structured data (what's written/checked, nothing about the pricing
catalog's internal slot keys) -- the model isn't asked to know anything
about how this studio's presets are built. map_to_quote_lines() is where
that plain data gets translated into real preset_key/components, entirely
in this codebase's own deterministic logic, not left to the model to
guess at internal slot keys it's never seen.

Never auto-saves a quote -- see api_worksheet_photo_analyze in app.py,
which always returns a preview for the studio to review/edit first,
since a misread handwritten number turning into a wrong client price is
a real, not theoretical, risk.
"""
import base64
import os

import anthropic

from pricing_engine import PricingError

MODEL = "claude-sonnet-5"

FRAME_TYPES = ["Box Frame", "Float for Canvas", "Aluminum Frame"]
ADD_ONS = ["Passpartout", "Art Glass", "Special Color", "Drawing", "Stretcher", "Special Wood"]

_client = None


def _client_instance():
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


EXTRACT_TOOL = {
    "name": "submit_worksheet_reading",
    "description": "Report everything legible on this photographed client-meeting worksheet.",
    "input_schema": {
        "type": "object",
        "properties": {
            "client_name": {"type": ["string", "null"]},
            "date": {"type": ["string", "null"], "description": "Exactly as written -- don't reformat or guess a format."},
            "items": {
                "type": "array",
                "description": "One entry per row that has ANY content (a work name, a size, a "
                                "checked frame type, or any checked add-on). Skip rows left "
                                "completely blank.",
                "items": {
                    "type": "object",
                    "properties": {
                        "row_number": {"type": "integer", "description": "The row's printed # (1-8)."},
                        "work_name": {"type": ["string", "null"]},
                        "height_cm": {"type": ["number", "null"], "description": "The first size blank."},
                        "width_cm": {"type": ["number", "null"], "description": "The second size blank, after the x."},
                        "frame_type": {
                            "type": ["string", "null"],
                            "enum": FRAME_TYPES + [None],
                            "description": "Which ONE of the three Frame checkboxes is marked. null if none/unclear.",
                        },
                        "add_ons": {
                            "type": "array",
                            "items": {"type": "string", "enum": ADD_ONS},
                            "description": "Every Add-ons checkbox that's marked.",
                        },
                        "notes": {"type": ["string", "null"]},
                        "unclear_fields": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Names of fields on THIS row you are not genuinely "
                                            "confident about (e.g. 'height_cm', 'frame_type') -- "
                                            "be honest here, don't guess silently. Empty list if "
                                            "everything on the row was legible.",
                        },
                    },
                    "required": ["row_number"],
                },
            },
        },
        "required": ["items"],
    },
}

SYSTEM_PROMPT = f"""You are reading a photo of a hand-filled paper worksheet used by The Print
House (a fine-art print/framing studio) during client meetings. The blank template has, at the
top, a Client Name line and a Date line, then a table of up to 8 numbered rows. Each row has:
  - "Work:" a blank line for the piece's name/description
  - "Size:" two blanks for height and width in cm, separated by "x"
  - "Frame:" three checkboxes -- {", ".join(FRAME_TYPES)} -- normally only one is marked
  - "Add-ons:" checkboxes -- {", ".join(ADD_ONS)} -- zero or more may be marked
  - "Notes:" a free blank line for anything else

Read carefully -- this feeds a real price quote, so accuracy matters more than completeness. If a
checkbox mark is ambiguous (a stray pen mark vs. a real check, or it's unclear which of two boxes
was intended), do not guess: leave the field null and list it in that row's unclear_fields. Same
for numbers that are illegible or could be two different digits. Skip rows that are entirely
blank. Report client_name/date as null if that line was left blank."""


def _image_content_block(image_bytes, media_type):
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": media_type, "data": base64.b64encode(image_bytes).decode("ascii")},
    }


def extract_worksheet(image_bytes, media_type="image/jpeg"):
    """Returns the tool's parsed input dict: {client_name, date, items: [...]}."""
    resp = _client_instance().messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": EXTRACT_TOOL["name"]},
        messages=[{
            "role": "user",
            "content": [
                _image_content_block(image_bytes, media_type),
                {"type": "text", "text": "Read this worksheet."},
            ],
        }],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == EXTRACT_TOOL["name"]:
            return block.input
    raise RuntimeError("Model did not call submit_worksheet_reading")


# --- Plain worksheet data -> real preset_key/components -----------------
#
# Deliberately explicit and per-frame-type rather than one generic table:
# the same checkbox means a different catalog component depending on the
# frame (e.g. "Special Wood" swaps the profile's simple->special variant,
# which only exists for wood profiles -- not aluminium's colour-named
# ones), and some add-ons simply don't apply to some frame types at all.

_FRAME_TYPE_TO_PRESET = {
    "Box Frame": "box",
    "Float for Canvas": "canvas",
    "Aluminum Frame": "aluminium",
}

# For add-ons that swap in a different *preset* entirely (not just a
# component override) -- currently just Drawing, which is its own preset
# key (box_drawing/aluminium_drawing) built from a different base profile
# than a plain component override could express.
_DRAWING_PRESET = {"box": "box_drawing", "aluminium": "aluminium_drawing"}

# Default profile item name per preset -- needed to find its simple<->special
# counterpart for "Special Wood". Kept in sync with pricing_data.json by
# hand; if a preset's default profile ever changes, update this too.
_DEFAULT_PROFILE = {
    "box": "Box 1.5/4 simple",
    "canvas": "Canvas 4.5/4.5 simple",
}


def map_to_quote_lines(items, catalog):
    """
    items: the `items` list from extract_worksheet()'s output.
    catalog: a PricingCatalog, used to sanity-check that the "special"
    profile variant this row would need actually exists before relying
    on it.

    Returns a list of {row_number, parsed_line, warnings} -- parsed_line
    is ready to hand straight to price_parsed_lines() (as one entry of
    its list) if height_cm/width_cm/preset_key are all present; warnings
    are plain-English notes (an add-on that doesn't apply to this frame
    type, a missing size, an unmapped frame type, ...) for the review UI
    to show alongside the row rather than silently dropping anything.
    """
    results = []
    for item in items:
        row_number = item.get("row_number")
        warnings = list(f"Unclear: {f}" for f in item.get("unclear_fields", []) or [])
        frame_type = item.get("frame_type")
        preset_key = _FRAME_TYPE_TO_PRESET.get(frame_type)
        if frame_type and not preset_key:
            warnings.append(f"Unrecognized frame type {frame_type!r}")
        if not preset_key:
            warnings.append("No frame type marked -- can't price this row without one.")

        components = []
        add_ons = item.get("add_ons") or []
        for add_on in add_ons:
            if add_on == "Passpartout":
                if preset_key in ("box", "aluminium"):
                    components += [
                        {"slot_key": "row26_passpartout", "item_name": "Museum Book 4ply"},
                        {"slot_key": "row11_paper", "item_name": "Fine Art"},
                    ]
                else:
                    warnings.append("Passpartout doesn't apply to Float for Canvas -- ignored.")
            elif add_on == "Art Glass":
                if preset_key in ("box", "aluminium"):
                    components.append({"slot_key": "row24_glasses", "item_name": "Art Glass 70%"})
                else:
                    warnings.append("Art Glass doesn't apply to Float for Canvas -- ignored.")
            elif add_on == "Special Color":
                if preset_key in ("box", "canvas"):
                    components.append({"slot_key": "row27_paint", "item_name": "special color (solid)"})
                else:
                    warnings.append("Special Color doesn't apply to Aluminum Frame -- ignored.")
            elif add_on == "Drawing":
                if preset_key in _DRAWING_PRESET:
                    preset_key = _DRAWING_PRESET[preset_key]
                else:
                    warnings.append("Drawing doesn't apply to Float for Canvas -- ignored.")
            elif add_on == "Stretcher":
                if preset_key != "canvas":
                    warnings.append("Stretcher only applies to Float for Canvas -- ignored.")
                # else: already on by default in the canvas preset, nothing to add.
            elif add_on == "Special Wood":
                base_preset_for_profile = "box" if preset_key in ("box", "box_drawing") else preset_key
                default_profile = _DEFAULT_PROFILE.get(base_preset_for_profile)
                if not default_profile:
                    warnings.append("Special Wood doesn't apply to Aluminum Frame -- ignored.")
                else:
                    special_name = default_profile.replace(" simple", " special")
                    try:
                        catalog.find_item("row23_profile_preset", special_name)
                        components.append({"slot_key": "row23_profile_preset", "item_name": special_name})
                    except PricingError:
                        warnings.append(f"Special Wood: {special_name!r} not found in the catalog -- ignored.")

        height_cm = item.get("height_cm")
        width_cm = item.get("width_cm")
        if not height_cm or not width_cm:
            warnings.append("Missing height or width -- can't price this row yet.")

        parsed_line = None
        if preset_key and height_cm and width_cm:
            parsed_line = {
                "preset_key": preset_key,
                "components": components,
                "height_cm": height_cm,
                "width_cm": width_cm,
                "order_quantity": 1,
                "description": item.get("work_name") or f"Row {row_number}",
            }

        results.append({
            "row_number": row_number,
            "work_name": item.get("work_name"),
            "frame_type": item.get("frame_type"),
            "add_ons": add_ons,
            "notes": item.get("notes"),
            "height_cm": height_cm,
            "width_cm": width_cm,
            "parsed_line": parsed_line,
            "warnings": warnings,
        })
    return results

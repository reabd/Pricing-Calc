"""
Free-text understanding, backed by the Claude API. This module NEVER lets
the model compute a price or a new price itself — it only turns Hebrew/
English free text into a structured request (which slot/item/size, or
which prices to change by how much). All arithmetic happens afterwards in
pricing_engine.py / app.py, deterministically.

Requires the ANTHROPIC_API_KEY environment variable.
"""
import json
import os
from pathlib import Path

import anthropic

MODEL = "claude-sonnet-5"

STUDIO_KNOWLEDGE_PATH = Path(__file__).resolve().parent / "studio_knowledge.json"

_client = None
_studio_knowledge = None


def studio_knowledge():
    global _studio_knowledge
    if _studio_knowledge is None:
        _studio_knowledge = json.loads(STUDIO_KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    return _studio_knowledge


def client():
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Export it before running the app, e.g.:\n"
                "  export ANTHROPIC_API_KEY=sk-ant-..."
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def _catalog_context(catalog):
    """Compact JSON describing every slot/item and every preset package, for the model's prompt."""
    return json.dumps({
        "slots": catalog.list_slots(),
        "presets": catalog.list_presets(),
    }, ensure_ascii=False)


QUOTE_TOOL = {
    "name": "submit_quote",
    "description": "Submit the parsed quote request(s) as structured line items.",
    "input_schema": {
        "type": "object",
        "properties": {
            "clarification_needed": {
                "type": ["string", "null"],
                "description": (
                    "If required information is missing or ambiguous (e.g. size not given, "
                    "or an item can't be confidently matched to the catalog), put a short "
                    "clarifying question here, in the same language the user wrote in, and "
                    "leave 'lines' empty. Otherwise null."
                ),
            },
            "lines": {
                "type": "array",
                "description": "One entry per distinct product/size the user asked about.",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Short human-readable label for this line item.",
                        },
                        "height_cm": {"type": "number"},
                        "width_cm": {"type": "number"},
                        "order_quantity": {"type": "number", "default": 1},
                        "preset_key": {
                            "type": ["string", "null"],
                            "description": (
                                "If the user's wording matches one of the named packages in the "
                                "catalog's 'presets' list (e.g. 'box frame', 'float frame', "
                                "'aluminium frame', 'facemount', 'canvas'), put its exact key here "
                                "so all of that package's default components are included "
                                "automatically. Otherwise null."
                            ),
                        },
                        "wood_species": {
                            "type": ["string", "null"],
                            "description": (
                                "If the user names a specific wood species for the frame profile "
                                "(see wood_species.special_tier_species / simple_tier_species in "
                                "the catalog), put the exact species name here verbatim. Do NOT "
                                "resolve this into a profile item name yourself and do NOT put it "
                                "in 'components' — a separate deterministic step handles picking "
                                "the right simple/special profile item. Otherwise null."
                            ),
                        },
                        "paint_method": {
                            "type": ["string", "null"],
                            "description": (
                                "If the user explicitly asks for a specific paint/finish method "
                                "for the frame (e.g. 'solid', 'Sprayed', 'natural', 'opac'), put "
                                "the exact matching item name from the row27_paint slot here. Do "
                                "NOT put it in 'components' and do NOT guess one if the user didn't "
                                "ask for a specific finish — leave null and the correct default "
                                "will be applied automatically. Only relevant if the order includes "
                                "a wood profile (row27_paint exists as a slot)."
                            ),
                        },
                        "float_profile_size": {
                            "type": ["string", "null"],
                            "description": (
                                "Only for a Float Dibond/Kapa profile: if the user describes "
                                "wanting a 'big' / 'large' / 'wide' float profile (as opposed to "
                                "the regular default), set this to 'big'. Do NOT resolve this into "
                                "an item name yourself — a separate deterministic step does it. "
                                "Otherwise null."
                            ),
                        },
                        "components": {
                            "type": "array",
                            "description": (
                                "Extra components to add, or overrides that replace what the "
                                "chosen preset would normally use for a given slot (e.g. the user "
                                "asked for 'box frame with museum glass' -> override row24_glasses). "
                                "If preset_key is null, this must be the FULL list of components "
                                "for the line, EXCEPT for the profile (row23_profile_preset) and "
                                "paint (row27_paint) slots when wood_species/paint_method/"
                                "float_profile_size already cover them."
                            ),
                            "items": {
                                "type": "object",
                                "properties": {
                                    "slot_key": {
                                        "type": "string",
                                        "description": "Exact slot key from the catalog, e.g. 'row24_glasses'.",
                                    },
                                    "item_name": {
                                        "type": "string",
                                        "description": "Exact item name from that slot's item list.",
                                    },
                                    "quantity": {
                                        "type": "number",
                                        "default": 1,
                                        "description": "Only meaningful for manual_hours slots (e.g. delivery hours).",
                                    },
                                },
                                "required": ["slot_key", "item_name"],
                            },
                        },
                    },
                    "required": ["height_cm", "width_cm", "components"],
                },
            },
        },
        "required": ["lines"],
    },
}

PRICE_UPDATE_TOOL = {
    "name": "submit_price_update",
    "description": "Submit the parsed price-update instruction(s) as a structured change.",
    "input_schema": {
        "type": "object",
        "properties": {
            "clarification_needed": {
                "type": ["string", "null"],
                "description": (
                    "If it's unclear which items/category the user means, or by how much, "
                    "ask here (same language as the user) and leave 'changes' empty."
                ),
            },
            "changes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "scope_description": {
                            "type": "string",
                            "description": "Human-readable summary of what this change targets, e.g. 'all paper items'.",
                        },
                        "slot_keys": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Slot keys this applies to. Empty means: search item_names across all slots.",
                        },
                        "item_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Restrict to these specific item names. Empty means: every item in slot_keys.",
                        },
                        "field": {
                            "type": "string",
                            "enum": ["fixed_material_cost", "var_material_cost"],
                            "description": "Which cost field to change. Use var_material_cost for per-size costs, fixed_material_cost for flat costs.",
                        },
                        "change_type": {
                            "type": "string",
                            "enum": ["percent", "absolute_add", "absolute_set"],
                        },
                        "value": {
                            "type": "number",
                            "description": "e.g. 0.20 for +20% when change_type=percent.",
                        },
                    },
                    "required": ["slot_keys", "item_names", "field", "change_type", "value"],
                },
            },
        },
        "required": ["changes"],
    },
}


def _force_tool_call(system_prompt, user_text, tool):
    resp = client().messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": user_text}],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == tool["name"]:
            return block.input
    raise RuntimeError(f"Model did not call {tool['name']!r}")


def parse_quote_request(text, catalog):
    knowledge = studio_knowledge()
    wood = knowledge["wood_species"]
    aliases = knowledge.get("vocabulary_aliases", {})

    system_prompt = (
        "You convert free-text pricing requests (Hebrew or English) for a print/framing studio "
        "into structured line items, using ONLY the slots, item names, and presets given below. "
        "Never invent a slot_key, item_name, or preset_key that isn't in this catalog — if "
        "nothing fits, ask for clarification instead. Sizes are in centimeters, height then "
        "width. If the user lists several products/sizes, return one line per product.\n\n"
        "Prefer matching a named package in 'presets' (e.g. 'box frame', 'float frame') over "
        "listing components manually — it captures the studio's real defaults (like the wood "
        "corner joint and wrapping that come with every box frame). Only add/override "
        "components for things the user explicitly asked for beyond the preset's defaults.\n\n"
        "FLOAT FRAME + PRINT: the plain 'float' preset has no paper/backing — it's only for "
        "framing something the customer already has. If the user asks for a float frame TOGETHER "
        "with a print/photo, use the 'kapa_float' preset instead (it already bundles the paper "
        "and the Kapa backing board that a floated print needs) — do not build this combination "
        "manually from 'float' plus ad-hoc components. Only use 'facemount_float' instead if the "
        "user explicitly asks for an acrylic facemount finish.\n\n"
        "WOOD SPECIES: if the user names one of these species for the frame, set wood_species "
        "to it verbatim (do not pick a profile item yourself, do not put it in 'components' — a "
        "separate deterministic step resolves it):\n"
        f"  - {', '.join(wood['special_tier_species'])}\n"
        f"  - {', '.join(wood['simple_tier_species'])}\n\n"
        "PAINT METHOD: if the user explicitly asks for a specific paint/finish for the frame "
        "(row27_paint slot), set paint_method to the exact matching catalog item name. If they "
        "didn't ask for a specific finish, leave paint_method null — do not guess or copy "
        "whatever a preset's raw default might be; a correct default is applied automatically.\n\n"
        "FLOAT PROFILE SIZE: for a Float Dibond/Kapa profile, if the user describes wanting a "
        "'big'/'large'/'wide' profile (as opposed to the regular default), set float_profile_size "
        "to 'big'. Otherwise leave it null — do not guess the family yourself.\n\n"
        "VOCABULARY ALIASES — terms the studio uses that don't literally match a slot/item name:\n"
        + "".join(
            f"  - '{term}': add component {{slot_key: '{alias['slot_key']}', "
            f"item_name: '{alias['default_item']}'}} by default. {alias['notes']}\n"
            for term, alias in aliases.items()
        )
        + "\n"
        f"CATALOG:\n{_catalog_context(catalog)}"
    )
    return _force_tool_call(system_prompt, text, QUOTE_TOOL)


def parse_price_update(text, catalog):
    system_prompt = (
        "You convert free-text price-update instructions (Hebrew or English) for a print/framing "
        "studio's price catalog into a structured change. Use ONLY slot_keys and item_names that "
        "appear in the catalog below. If the scope is ambiguous (e.g. which category, which "
        "field), ask for clarification instead of guessing.\n\n"
        f"CATALOG:\n{_catalog_context(catalog)}"
    )
    return _force_tool_call(system_prompt, text, PRICE_UPDATE_TOOL)


def preview_price_changes(catalog, changes):
    """Dry-run: returns a list of {slot_key, item_name, field, old_value, new_value} without saving."""
    diffs = []
    for change in changes:
        slot_keys = change.get("slot_keys") or list(catalog.slots.keys())
        item_names = set(change.get("item_names") or [])
        field = change["field"]
        change_type = change["change_type"]
        value = change["value"]

        for slot_key in slot_keys:
            slot = catalog.get_slot(slot_key)
            for name, item in slot["items"].items():
                if item_names and name not in item_names:
                    continue
                old_value = item[field]
                if change_type == "percent":
                    new_value = old_value * (1 + value)
                elif change_type == "absolute_add":
                    new_value = old_value + value
                elif change_type == "absolute_set":
                    new_value = value
                else:
                    raise ValueError(f"Unknown change_type: {change_type!r}")
                diffs.append({
                    "slot_key": slot_key,
                    "item_name": name,
                    "field": field,
                    "old_value": old_value,
                    "new_value": new_value,
                })
    return diffs


def apply_price_changes(catalog, diffs):
    """Applies previously-previewed diffs to the in-memory catalog and persists to disk."""
    for diff in diffs:
        slot = catalog.get_slot(diff["slot_key"])
        slot["items"][diff["item_name"]][diff["field"]] = diff["new_value"]
    catalog.save()

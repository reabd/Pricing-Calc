"""
Deterministic application of studio_knowledge.json's wood-species/paint
rules. This is intentionally NOT left to the LLM: asking a model to
remember "override the preset's default paint unless the user explicitly
asked for one" on every call turned out to be unreliable (verified: the
exact same free-text request returned a different paint item across
repeated calls). The LLM's job is only to extract the raw signals
(wood_species, paint_method); this module resolves them into catalog item
names the same way every time.
"""
import json
import re
from pathlib import Path

PROFILE_SLOT_KEY = "row23_profile_preset"
PAINT_SLOT_KEY = "row27_paint"

STUDIO_KNOWLEDGE_PATH = Path(__file__).resolve().parent / "studio_knowledge.json"

_knowledge = None


def studio_knowledge():
    global _knowledge
    if _knowledge is None:
        _knowledge = json.loads(STUDIO_KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    return _knowledge


def _species_tier(species):
    if not species:
        return None
    knowledge = studio_knowledge()["wood_species"]
    species_norm = species.strip().lower()
    for name in knowledge["special_tier_species"]:
        if name.lower() == species_norm:
            return "special"
    for name in knowledge["simple_tier_species"]:
        if name.lower() == species_norm:
            return "simple"
    return None


def _swap_tier_suffix(item_name, tier):
    base = re.sub(r"\s+(simple|special)\s*$", "", item_name, flags=re.I)
    return f"{base} {tier}"


FLOAT_FAMILY_RE = re.compile(r"^(Float Dibond/Kapa )([\d.]+/[\d.]+)(\s.*)?$", re.I)


def _swap_float_family(item_name, family):
    m = FLOAT_FAMILY_RE.match(item_name)
    if not m:
        return item_name
    prefix, _old_family, suffix = m.groups()
    return f"{prefix}{family}{suffix or ''}"


def apply_wood_paint_rules(catalog, components, wood_species=None, paint_method=None,
                            float_profile_size=None):
    """
    `components` is a {slot_key: {"item_name":..., "quantity":...}} dict,
    already merged from a preset + explicit overrides (see
    PricingCatalog.resolve_components_dict). Mutates and returns it,
    applying the wood-species/paint-tier and float-profile-size business
    rules. Returns (components, error_message) — error_message is set (and
    components unchanged) if wood_species and paint_method contradict
    each other.
    """
    knowledge = studio_knowledge()
    paint_rules = knowledge["paint_wood_constraints"]
    default_paint = knowledge["default_paint_when_unspecified"]["default_item"]
    float_size_aliases = knowledge["float_profile_size_aliases"]

    tier_from_species = _species_tier(wood_species)
    paint_rule = paint_rules.get(paint_method) if paint_method else None
    tier_from_paint = paint_rule["required_tier"] if paint_rule else None

    if tier_from_species and tier_from_paint and tier_from_species != tier_from_paint:
        return components, (
            f"'{paint_method}' paint requires {paint_rule['required_species']} wood "
            f"(the '{tier_from_paint}' profile tier), but you asked for {wood_species} "
            f"wood (the '{tier_from_species}' tier) — these conflict."
        )

    final_tier = tier_from_paint or tier_from_species

    if PROFILE_SLOT_KEY in components:
        current_item = components[PROFILE_SLOT_KEY]["item_name"]

        if final_tier:
            swapped = _swap_tier_suffix(current_item, final_tier)
            if swapped in catalog.get_slot(PROFILE_SLOT_KEY)["items"]:
                current_item = swapped
            # else: item has no simple/special pair (e.g. Alumineum) — leave as-is.

        if float_profile_size:
            family = float_size_aliases.get(float_profile_size.strip().lower())
            if family:
                swapped = _swap_float_family(current_item, family)
                if swapped in catalog.get_slot(PROFILE_SLOT_KEY)["items"]:
                    current_item = swapped
                # else: not a Float Dibond/Kapa item — leave as-is.

        components[PROFILE_SLOT_KEY]["item_name"] = current_item

    if PAINT_SLOT_KEY in components:
        components[PAINT_SLOT_KEY]["item_name"] = paint_method if paint_method else default_paint

    return components, None


def apply_box_back_frame_rule(components, height_cm, width_cm):
    """
    Large box frames need a small back-frame brace for structural
    support. Unlike the wood/paint rules above, this is a structural
    fact rather than a free-text interpretation choice, so it's applied
    unconditionally — both for the free-text path and for structured/API
    callers — not gated behind an `apply_business_rules` flag. It only
    ever adds a component, and does nothing if the caller already
    specified that slot themselves.
    """
    rule = studio_knowledge()["box_back_frame_rule"]
    slot_key = rule["slot_key"]

    if PROFILE_SLOT_KEY not in components or slot_key in components:
        return components

    profile_item = components[PROFILE_SLOT_KEY]["item_name"]
    if not profile_item.startswith("Box ") or profile_item.startswith("Box Ready Wood"):
        return components

    perimeter_m = (height_cm + width_cm) * 2 / 100
    if perimeter_m > rule["perimeter_threshold_m"]:
        components[slot_key] = {"item_name": rule["default_item"], "quantity": 1.0}

    return components

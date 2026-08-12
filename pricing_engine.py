"""
Pure-Python reimplementation of the pricing formulas found in the
studio's Calculator sheet. No Excel involved at runtime — this reads
pricing_data.json (produced once by extract_pricing_data.py) and computes
the exact same numbers the spreadsheet would.

Formula reference (see the plan doc for the full derivation):

  size = (height+width)*2/100     for "perimeter" components
       or (height*width)/10000     for "area" components

  material_cost  = (fixed_material_cost + size*var_material_cost)
                    * (1+material_indirect) * (1+material_risk)
  material_price = material_cost / (1 - material_profit)

  work_cost   = max(min_effort_cost, fixed_effort_cost + size*var_effort_cost)
                * (1+effort_indirect) * (1+effort_risk)
  work_price  = work_cost / (1 - effort_profit)

  line totals are multiplied by the component's own `quantity` (used for
  "manual_hours" slots like Services, where the studio enters an hour
  count instead of a size).

Order-level aggregation (Calculator!W16 / W17 / Y16):

  quantity_price = ( sum(work_price for qty-scaled lines) * (1-work_discount)
                    + sum(material_price for qty-scaled lines) ) * order_quantity
                  + ( sum(work_price + material_price for non-qty-scaled lines) )
                    * (1 - discount)
  final_price    = quantity_price * (1 + vat_rate)
  margin         = (quantity_price - total_cost) / quantity_price
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_DATA_PATH = Path(__file__).resolve().parent / "pricing_data.json"


class PricingError(ValueError):
    """Raised for any problem resolving a slot/item the caller asked for."""


class PricingCatalog:
    def __init__(self, path=DEFAULT_DATA_PATH):
        self.path = Path(path)
        self.reload()

    def reload(self):
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.source_file = data.get("source_file", "PrintHouse Pricing Calc v8_3 - 09_03_2025.xlsm")
        self.salary_per_hour = data["salary_per_hour"]
        self.vat_rate = data["vat_rate"]
        self.excluded_features = data["excluded_features"]
        self.slots = {s["key"]: s for s in data["slots"]}
        self.presets = {p["key"]: p for p in data.get("presets", [])}

    def save(self):
        data = {
            "source_file": getattr(self, "source_file", "PrintHouse Pricing Calc v8_3 - 09_03_2025.xlsm"),
            "salary_per_hour": self.salary_per_hour,
            "vat_rate": self.vat_rate,
            "slots": list(self.slots.values()),
            "presets": list(self.presets.values()),
            "excluded_features": self.excluded_features,
        }
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_slot(self, slot_key):
        slot = self.slots.get(slot_key)
        if slot is None:
            raise PricingError(f"Unknown slot: {slot_key!r}")
        return slot

    def find_item(self, slot_key, item_name):
        slot = self.get_slot(slot_key)
        items = slot["items"]
        if item_name in items:
            return slot, item_name, items[item_name]
        # case/whitespace-insensitive fallback
        norm = item_name.strip().lower()
        for name, rec in items.items():
            if name.strip().lower() == norm:
                return slot, name, rec
        # Okapics ID may be sent as item_name when opics_id field is absent
        try:
            return self.find_item_by_opics_id(slot_key, item_name)
        except PricingError:
            pass
        raise PricingError(f"Item {item_name!r} not found in slot {slot_key!r}. "
                            f"Available: {', '.join(items)}")

    def find_item_by_opics_id(self, slot_key, opics_id):
        slot = self.get_slot(slot_key)
        norm = opics_id.strip()
        for name, rec in slot["items"].items():
            if rec.get("opics_id", "").strip() == norm:
                return slot, name, rec
        raise PricingError(f"No item with opics_id {opics_id!r} in slot {slot_key!r}.")

    def get_preset(self, preset_key):
        preset = self.presets.get(preset_key)
        if preset is None:
            raise PricingError(f"Unknown preset: {preset_key!r}. Available: {', '.join(self.presets)}")
        return preset

    def list_presets(self):
        """Compact summary of every preset (package), for LLM context or a UI menu."""
        out = []
        for preset in self.presets.values():
            out.append({
                "key": preset["key"],
                "label": preset["label"],
                "default_components": [
                    {"slot_key": c["slot_key"], "item_name": c["item_name"]}
                    for c in preset["components"]
                ],
            })
        return out

    def resolve_components_dict(self, preset_key, overrides):
        """
        Merges a preset's default components with explicit overrides into a
        {slot_key: {"item_name":..., "quantity":...}} dict. `overrides` is a
        list of {slot_key, item_name, quantity} — each one replaces the
        preset's choice for that slot if present, or adds a new component
        if the slot wasn't part of the preset at all. Pass preset_key=None
        to use `overrides` as the full component list.

        An override with item_name=None means "remove this component
        entirely", even if the preset itself would otherwise include it
        (e.g. a "No Print" choice removing a preset's own paper line).
        """
        merged = {}
        if preset_key:
            for comp in self.get_preset(preset_key)["components"]:
                merged[comp["slot_key"]] = {"item_name": comp["item_name"], "quantity": 1.0}
        for comp in overrides:
            if comp.get("item_name") is None and not comp.get("opics_id"):
                merged.pop(comp["slot_key"], None)
                continue
            entry = {
                "item_name": comp.get("item_name"),
                "quantity": comp.get("quantity", 1.0),
            }
            if comp.get("opics_id"):
                entry["opics_id"] = comp["opics_id"]
            merged[comp["slot_key"]] = entry
        return merged

    def resolve_components(self, preset_key, overrides):
        """Same as resolve_components_dict, returned as a JobComponentRequest list."""
        merged = self.resolve_components_dict(preset_key, overrides)
        return [
            JobComponentRequest(
                slot_key,
                data.get("item_name") or "",
                data.get("quantity", 1.0),
                data.get("opics_id") or "",
            )
            for slot_key, data in merged.items()
        ]

    def list_slots(self):
        """Compact summary of every slot, for building LLM context or a UI menu."""
        out = []
        for slot in self.slots.values():
            out.append({
                "key": slot["key"],
                "label": slot["label"],
                "kind": slot["kind"],
                "size_mode": slot["size_mode"],
                "items": list(slot["items"].keys()),
            })
        return out


def compute_size(size_mode, height_cm, width_cm):
    if size_mode == "perimeter":
        return (height_cm + width_cm) * 2 / 100
    if size_mode == "area":
        return (height_cm * width_cm) / 10000
    if size_mode == "manual_hours":
        return 0.0
    raise PricingError(f"Unknown size_mode: {size_mode!r}")


@dataclass
class ComponentPrice:
    slot_key: str
    item_name: str
    quantity: float
    material_cost: float
    material_price: float
    work_cost: float
    work_price: float
    scales_with_quantity: bool
    unpriced: bool = False

    @property
    def line_total(self):
        if self.unpriced:
            return None
        return self.material_price + self.work_price


def is_unpriced_item(item):
    """Catalog items marked unpriced exist for mapping but have no quote price."""
    return bool(item.get("unpriced"))


def price_component(item, size_mode, height_cm, width_cm, quantity=1.0):
    if is_unpriced_item(item):
        return {
            "material_cost": 0.0,
            "material_price": 0.0,
            "work_cost": 0.0,
            "work_price": 0.0,
            "unpriced": True,
        }

    size = compute_size(size_mode, height_cm, width_cm)

    material_cost = (item["fixed_material_cost"] + size * item["var_material_cost"]) \
        * (1 + item["material_indirect"]) * (1 + item["material_risk"])
    material_profit = item["material_profit"]
    material_price = material_cost / (1 - material_profit) if material_profit < 1 else material_cost

    work_cost = max(item["min_effort_cost"], item["fixed_effort_cost"] + size * item["var_effort_cost"]) \
        * (1 + item["effort_indirect"]) * (1 + item["effort_risk"])
    effort_profit = item["effort_profit"]
    work_price = work_cost / (1 - effort_profit) if effort_profit < 1 else work_cost

    return {
        "material_cost": material_cost * quantity,
        "material_price": material_price * quantity,
        "work_cost": work_cost * quantity,
        "work_price": work_price * quantity,
        "unpriced": False,
    }


@dataclass
class JobComponentRequest:
    slot_key: str
    item_name: str = ""
    quantity: float = 1.0
    opics_id: str = ""


@dataclass
class JobPriceResult:
    lines: list
    pricelist_single_unit: float
    quantity_price: float
    final_price_incl_vat: float
    margin: float
    order_quantity: float
    work_discount: float
    discount: float


def price_job(catalog: PricingCatalog, components, height_cm, width_cm,
              order_quantity=1.0, work_discount=0.0, discount=0.0, vat_rate=None):
    if vat_rate is None:
        vat_rate = catalog.vat_rate

    lines = []
    qty_scaled = {"material_cost": 0.0, "material_price": 0.0, "work_cost": 0.0, "work_price": 0.0}
    addon = {"material_cost": 0.0, "material_price": 0.0, "work_cost": 0.0, "work_price": 0.0}

    for comp in components:
        if comp.opics_id:
            slot, resolved_name, item = catalog.find_item_by_opics_id(comp.slot_key, comp.opics_id)
        else:
            slot, resolved_name, item = catalog.find_item(comp.slot_key, comp.item_name)
        priced = price_component(item, slot["size_mode"], height_cm, width_cm, comp.quantity)
        unpriced = bool(priced.pop("unpriced", False))

        if not unpriced:
            target = qty_scaled if slot["scales_with_quantity"] else addon
            for k in target:
                target[k] += priced[k]

        lines.append(ComponentPrice(
            slot_key=comp.slot_key,
            item_name=resolved_name,
            quantity=comp.quantity,
            scales_with_quantity=slot["scales_with_quantity"],
            unpriced=unpriced,
            **priced,
        ))

    pricelist_single_unit = (
        qty_scaled["material_price"] + qty_scaled["work_price"]
        + addon["material_price"] + addon["work_price"]
    )

    quantity_price = (
        (qty_scaled["work_price"] * (1 - work_discount) + qty_scaled["material_price"]) * order_quantity
        + (addon["work_price"] + addon["material_price"]) * (1 - discount)
    )
    final_price_incl_vat = quantity_price * (1 + vat_rate)

    total_cost = (
        (qty_scaled["material_cost"] + qty_scaled["work_cost"]) * order_quantity
        + (addon["material_cost"] + addon["work_cost"])
    )
    margin = (quantity_price - total_cost) / quantity_price if quantity_price else 0.0

    return JobPriceResult(
        lines=lines,
        pricelist_single_unit=pricelist_single_unit,
        quantity_price=quantity_price,
        final_price_incl_vat=final_price_incl_vat,
        margin=margin,
        order_quantity=order_quantity,
        work_discount=work_discount,
        discount=discount,
    )

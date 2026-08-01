"""
Regression check: reproduces the example order currently sitting in the
Calculator sheet (H=114cm, W=70cm, quantity=1, no discounts) and compares
our Python engine's output to the values already cached in the workbook.

If this doesn't match (within a small tolerance), the engine has diverged
from the source spreadsheet and must not be trusted.

Note: the VAT-inclusive price is checked against the *current* catalog
VAT rate, not a hardcoded 17% — the studio has since changed VAT to 18%,
and that's an intentional business setting, not a regression.
"""
from pricing_engine import PricingCatalog, JobComponentRequest, price_job

EXPECTED_PRICELIST = 2159.0171467161667   # Calculator!W9 (and W16, since qty=1, no discounts)
EXPECTED_MARGIN = 0.3770894464034757      # Calculator!W17

TOLERANCE = 0.01


def main():
    catalog = PricingCatalog()
    expected_vat_price = EXPECTED_PRICELIST * (1 + catalog.vat_rate)

    components = [
        JobComponentRequest("row12_lamelo", "Lamelo"),
        JobComponentRequest("row19_wood_glyph", "Wood Glyph"),
        JobComponentRequest("row23_profile_preset", "Box 1.5/4 simple"),
        JobComponentRequest("row24_glasses", "Art Glass 70%"),
        JobComponentRequest("row27_paint", "solid"),
        JobComponentRequest("row28_drawing", "Hinjes with japanies paper"),
        JobComponentRequest("row32_simple_wrap", "Simple Wrap"),
    ]

    result = price_job(catalog, components, height_cm=114, width_cm=70,
                        order_quantity=1, work_discount=0, discount=0)

    print("Line breakdown:")
    for line in result.lines:
        print(f"  {line.slot_key:30s} {line.item_name:30s} "
              f"material={line.material_price:10.4f} work={line.work_price:10.4f} "
              f"total={line.line_total:10.4f}")

    print()
    print(f"{'Pricelist (single unit)':30s} got={result.pricelist_single_unit:.4f}  expected={EXPECTED_PRICELIST:.4f}")
    print(f"{'Quantity price':30s} got={result.quantity_price:.4f}")
    print(f"{'Final price incl. VAT':30s} got={result.final_price_incl_vat:.4f}  expected={expected_vat_price:.4f} (at {catalog.vat_rate:.0%} VAT)")
    print(f"{'Margin':30s} got={result.margin:.6f}  expected={EXPECTED_MARGIN:.6f}")

    ok = True
    for label, got, expected in [
        ("Pricelist", result.pricelist_single_unit, EXPECTED_PRICELIST),
        ("VAT price", result.final_price_incl_vat, expected_vat_price),
        ("Margin", result.margin, EXPECTED_MARGIN),
    ]:
        diff = abs(got - expected)
        status = "OK" if diff < TOLERANCE else "MISMATCH"
        if diff >= TOLERANCE:
            ok = False
        print(f"[{status}] {label}: diff={diff:.6f}")

    print()
    print("ALL CHECKS PASSED" if ok else "VERIFICATION FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

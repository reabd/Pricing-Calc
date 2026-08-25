"""
Delivery pricing for the studio's own van (Israel only) -- see
studio_operations_and_communication_notes.md's earlier informal delivery
notes and the studio owner's request (2026-08-25) to formalize it.

Reuses two pre-existing catalog items that were already in
pricing_data.json (from the original Excel workbook) but never wired into
anything: row8_car ("Car", a per-km rate) and row9_work_time ("Work Time",
a per-hour labor rate). No new pricing math of our own -- this just feeds
the right quantities (round-trip km, adjusted hours) through the exact
same price_job() engine every other quote line already goes through.
"""
from pricing_engine import JobComponentRequest, PricingError, price_job

CAR_SLOT = "row8_car"
CAR_ITEM = "Car"
WORK_TIME_SLOT = "row9_work_time"
WORK_TIME_ITEM = "Work Time"


def piece_count_multiplier(num_works):
    """
    1.0 up to 7 works, then +0.2 per tier: >7 -> 1.2, >12 -> 1.4, >20 -> 1.6,
    and every +8 works after that adds another +0.2 (>28 -> 1.8, >36 -> 2.0,
    ...) -- studio owner's exact tiers up to 20, extended the same way
    beyond that by their choice (2026-08-25).
    """
    if num_works <= 7:
        return 1.0
    if num_works <= 12:
        return 1.2
    if num_works <= 20:
        return 1.4
    extra_tiers = (num_works - 20 - 1) // 8
    return round(1.6 + 0.2 * extra_tiers, 2)


def find_city(catalog, city_name):
    for city in catalog.delivery_cities:
        if city["name"] == city_name:
            return city
    return None


def compute_delivery(catalog, city_name, num_works):
    """
    Returns {city, km_round_trip, hours, multiplier, price} or raises
    PricingError if the city isn't in the lookup table. `price` is the
    full priced delivery charge (car + labor, with the item's own
    material/effort margins already applied via price_job) -- ready to
    add straight onto a quote.
    """
    city = find_city(catalog, city_name)
    if city is None:
        raise PricingError(f"Unknown delivery city: {city_name!r}")

    km_round_trip = city["km_one_way"] * 2
    hours_round_trip = (city["minutes_one_way"] * 2) / 60
    multiplier = piece_count_multiplier(num_works)
    hours = round(hours_round_trip * multiplier, 2)

    components = [
        JobComponentRequest(CAR_SLOT, CAR_ITEM, quantity=km_round_trip),
        JobComponentRequest(WORK_TIME_SLOT, WORK_TIME_ITEM, quantity=hours),
    ]
    result = price_job(catalog, components, height_cm=0, width_cm=0, order_quantity=1)

    return {
        "city": city["name"],
        "km_round_trip": km_round_trip,
        "hours": hours,
        "multiplier": multiplier,
        "price": round(result.quantity_price, 2),
    }

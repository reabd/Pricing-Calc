"""
Delivery pricing for the studio's own van (Israel only) -- see
studio_operations_and_communication_notes.md's earlier informal delivery
notes and the studio owner's request (2026-08-25) to formalize it.

Originally reused two pre-existing catalog items (Car/Work Time, from the
original Excel workbook) through the same price_job() margin engine every
other quote line goes through. Their rates were tuned for skilled framing
labor and material markup, not van callouts, and produced baseline prices
far below what the studio actually wants to charge -- so this now uses its
own flat formula instead, calibrated against five real target prices the
studio owner gave directly (2026-08-25):
Herzliya ~400, Jerusalem ~850, Netanya ~600, Tel Aviv Center ~350,
Haifa ~1000 (all pre-VAT).

  base_price = base_fee + per_km * km_round_trip + per_hour * hours_round_trip * BASE_MULTIPLIER

A continuous per-work multiplier was tried next, but its effect turned out
too small to feel real (a handful of NIS per extra tier) -- so the piece
count now instead steps the price in flat TIER_STEP jumps every
TIER_WIDTH works, on top of that same base_price: 1-7 works -> base_price,
8-14 -> base_price + TIER_STEP, 15-21 -> base_price + 2*TIER_STEP, etc.
(studio owner, 2026-08-25, using Ramat HaSharon's base_price of 400 as the
worked example: 1-7 -> 400, 8-14 -> 600, 15-21 -> 800). TIER_STEP is a flat
NIS amount, the same for every city, not scaled by distance.

Rates live in catalog.delivery_rates (base_fee/per_km/per_hour/tier_step)
so they can be tuned the same way every other price in pricing_data.json is.
"""
from pricing_engine import PricingError

BASE_MULTIPLIER = 1.5  # matches the already-approved 1-7 works baseline
TIER_WIDTH = 7


def tier_index(num_works):
    """0 for 1-7 works, 1 for 8-14, 2 for 15-21, ... 0 works (an empty-cart
    preview) is treated the same as the first tier."""
    return max(num_works - 1, 0) // TIER_WIDTH


def find_city(catalog, city_name):
    for city in catalog.delivery_cities:
        if city["name"] == city_name:
            return city
    return None


def compute_delivery(catalog, city_name, num_works):
    """
    Returns {city, km_round_trip, hours, tier_index, tier_extra, price} or
    raises PricingError if the city isn't in the lookup table. `price` is
    the full delivery charge, ready to add straight onto a quote.
    """
    city = find_city(catalog, city_name)
    if city is None:
        raise PricingError(f"Unknown delivery city: {city_name!r}")

    rates = catalog.delivery_rates
    km_round_trip = city["km_one_way"] * 2
    hours_round_trip = (city["minutes_one_way"] * 2) / 60
    hours = round(hours_round_trip * BASE_MULTIPLIER, 2)

    base_price = rates["base_fee"] + rates["per_km"] * km_round_trip + rates["per_hour"] * hours
    # Rounded to the nearest 5 shekels -- a clean number on the quote/PDF
    # (400, 405, 410...) rather than a raw formula output like 431.8
    # (studio owner, 2026-08-25).
    base_price = round(base_price / 5) * 5

    idx = tier_index(num_works)
    tier_extra = rates.get("tier_step", 200) * idx
    price = base_price + tier_extra

    return {
        "city": city["name"],
        "km_round_trip": km_round_trip,
        "hours": hours,
        "tier_index": idx,
        "tier_extra": tier_extra,
        "price": price,
    }

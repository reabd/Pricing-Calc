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

  price = base_fee + per_km * km_round_trip + per_hour * hours_round_trip * multiplier

Rates live in catalog.delivery_rates (base_fee/per_km/per_hour) so they can
be tuned the same way every other price in pricing_data.json is.
"""
from pricing_engine import PricingError


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
    full delivery charge, ready to add straight onto a quote.
    """
    city = find_city(catalog, city_name)
    if city is None:
        raise PricingError(f"Unknown delivery city: {city_name!r}")

    rates = catalog.delivery_rates
    km_round_trip = city["km_one_way"] * 2
    hours_round_trip = (city["minutes_one_way"] * 2) / 60
    multiplier = piece_count_multiplier(num_works)
    hours = round(hours_round_trip * multiplier, 2)

    price = rates["base_fee"] + rates["per_km"] * km_round_trip + rates["per_hour"] * hours
    # Rounded to the nearest 5 shekels -- a clean number on the quote/PDF
    # (400, 405, 410...) rather than a raw formula output like 431.8
    # (studio owner, 2026-08-25).
    price = round(price / 5) * 5

    return {
        "city": city["name"],
        "km_round_trip": km_round_trip,
        "hours": hours,
        "multiplier": multiplier,
        "price": price,
    }

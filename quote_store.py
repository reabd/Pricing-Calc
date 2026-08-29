"""
Persists client price quotes (see quote_pdf.py for the PDF a saved quote
gets turned into) -- one quote is a client name plus a list of
already-priced "work items" (the same shape price_parsed_lines() already
returns), assigned a sequential quote number starting at 1000 (studio
owner, 2026-08-22) -- same numbering convention already used for the
Monday.com Wood Frames Orders board.

Stored as a single JSON file (quotes.json next to the app by default, or
wherever QUOTES_DATA_PATH points -- same PRICING_DATA_PATH persistent-disk
convention used elsewhere in this app). This absolutely needs to live on
real persistent storage: quotes are real business records, not a cache.
"""
import json
import os
from datetime import date
from pathlib import Path

START_NUMBER = 1000

_bundled_path = Path(__file__).resolve().parent / "quotes.json"
DATA_PATH = Path(os.environ.get("QUOTES_DATA_PATH", _bundled_path))


def _load():
    if not DATA_PATH.exists():
        return {"next_number": START_NUMBER, "quotes": {}}
    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"next_number": START_NUMBER, "quotes": {}}
    data.setdefault("next_number", START_NUMBER)
    data.setdefault("quotes", {})
    return data


def _save(data):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def create_quote(client_name, client_phone, client_email, work_items, vat_rate,
                  discount_percent=0, delivery=None):
    """
    delivery: optional {city, km_round_trip, hours, multiplier, price} --
    already computed server-side by delivery.compute_delivery() (never
    trust a client-supplied delivery price). Applied after the discount,
    same as shipping normally isn't itself discounted.
    """
    if not client_name or not client_name.strip():
        raise ValueError("client_name is required")
    if not work_items:
        raise ValueError("work_items must have at least one item")
    discount_percent = float(discount_percent or 0)
    if not 0 <= discount_percent < 100:
        raise ValueError("discount_percent must be between 0 and 100")

    data = _load()
    quote_number = data["next_number"]
    subtotal = sum(w["quantity_price"] for w in work_items)
    delivery_price = delivery["price"] if delivery else 0
    grand_total = subtotal * (1 - discount_percent / 100) + delivery_price
    quote = {
        "quote_number": quote_number,
        "client_name": client_name.strip(),
        "client_phone": (client_phone or "").strip() or None,
        "client_email": (client_email or "").strip() or None,
        "created_date": date.today().isoformat(),
        "vat_rate": vat_rate,
        "work_items": work_items,
        "discount_percent": discount_percent,
        "subtotal_pre_discount": round(subtotal, 2),
        "delivery": delivery,
        "grand_total_pre_vat": round(grand_total, 2),
        "grand_total_incl_vat": round(grand_total * (1 + vat_rate), 2),
    }
    data["quotes"][str(quote_number)] = quote
    data["next_number"] = quote_number + 1
    _save(data)
    return quote


def get_quote(quote_number):
    return _load()["quotes"].get(str(quote_number))


def update_quote(quote_number, client_name=None, client_phone=None, client_email=None,
                  discount_percent=None, work_items=None):
    """
    Edits an already-saved quote in place -- client info and/or its full
    work_items list (see api_quote_update in app.py: re-pricing an
    individual item, e.g. after a mis-measured size, happens there before
    calling this; this function just replaces the list and recomputes
    totals, the same math create_quote() uses). None for any field means
    "leave as-is". Raises ValueError (same as create_quote) if the quote
    doesn't exist or a new value is invalid.
    """
    data = _load()
    quote = data["quotes"].get(str(quote_number))
    if not quote:
        raise ValueError(f"Quote #{quote_number} not found.")

    if client_name is not None:
        if not client_name.strip():
            raise ValueError("client_name is required")
        quote["client_name"] = client_name.strip()
    if client_phone is not None:
        quote["client_phone"] = client_phone.strip() or None
    if client_email is not None:
        quote["client_email"] = client_email.strip() or None
    if discount_percent is not None:
        discount_percent = float(discount_percent)
        if not 0 <= discount_percent < 100:
            raise ValueError("discount_percent must be between 0 and 100")
        quote["discount_percent"] = discount_percent
    if work_items is not None:
        if not work_items:
            raise ValueError("work_items must have at least one item")
        quote["work_items"] = work_items

    subtotal = sum(w["quantity_price"] for w in quote["work_items"])
    delivery_price = quote["delivery"]["price"] if quote.get("delivery") else 0
    grand_total = subtotal * (1 - quote.get("discount_percent", 0) / 100) + delivery_price
    quote["subtotal_pre_discount"] = round(subtotal, 2)
    quote["grand_total_pre_vat"] = round(grand_total, 2)
    quote["grand_total_incl_vat"] = round(grand_total * (1 + quote.get("vat_rate", 0.18)), 2)

    data["quotes"][str(quote_number)] = quote
    _save(data)
    return quote


def list_quotes(client_name=None):
    quotes = list(_load()["quotes"].values())
    if client_name:
        needle = client_name.strip().lower()
        quotes = [q for q in quotes if needle in q["client_name"].lower()]
    quotes.sort(key=lambda q: q["quote_number"], reverse=True)
    return quotes


def list_client_names():
    return sorted({q["client_name"] for q in _load()["quotes"].values()})

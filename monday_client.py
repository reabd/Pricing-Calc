"""
Thin wrapper around Monday.com's GraphQL API for looking up order status on
the studio's "Workshop" production-tracking board (board ID in
MONDAY_BOARD_ID; see studio_operations_and_communication_notes.md §7).

Order items on that board are named "<order number> <customer name>"
(e.g. "25301 Shlomi Nissim"), grouped into three pipeline stages
(New Orders -> At Workshop -> Ready), matching the W2P order-number format
already documented from the mailbox. This module only reads order status —
it never writes to the board.
"""
import json
import os
import re
import urllib.error
import urllib.request

MONDAY_API_URL = "https://api.monday.com/v2"

# Column IDs on the Workshop board that matter for an "is it ready yet"
# reply. These are internal Monday column IDs (stable even if a column's
# display title is renamed), discovered by inspecting the board directly —
# see the studio_operations_and_communication_notes.md §7 notes for the
# full column list this board actually has.
STATUS_COLUMN_IDS = ["dup__of_due_date", "date7", "status4", "dup__of_priority", "text9"]

# Per-production-station status columns, in real workshop production order.
# Every order only actually uses a subset of these (the rest read "Not
# Needed") — e.g. a plain print has no Carpentry/Mount step at all.
STEP_COLUMNS = [
    ("foundations3", "Carpentry"),
    ("dup__of_carpentry", "Paint Brush"),
    ("dup__of_paint_brush", "Paint Spray"),
    ("dup__of_paint_spray", "Aluminum"),
    ("dup__of_aluminum", "Mount"),
    ("dup__of_glue", "Passepartout"),
    ("dup__of_passepartout", "Chromaluxe"),
    ("dup__of_chromaluxe5", "CNC"),
    ("color_mksy4vp2", "UV Printer"),
    ("dup__of_chromaluxe", "Closing"),
]

COLUMN_IDS = STATUS_COLUMN_IDS + [col_id for col_id, _label in STEP_COLUMNS]

STAGE_LABELS_HE = {
    "New Orders": "טרם נכנסה לעבודה בבית המלאכה",
    "At Workshop": "בעבודה בבית המלאכה",
    "Ready": "מוכנה",
}

ORDER_NUMBER_RE = re.compile(r"\b\d{4,6}\b")
NAME_LEADING_NUMBER_RE = re.compile(r"^(\d{4,6})")


class MondayError(RuntimeError):
    pass


def _token():
    token = os.environ.get("MONDAY_API_TOKEN")
    if not token:
        raise MondayError("MONDAY_API_TOKEN is not set (add it to .env)")
    return token


def _board_id():
    board_id = os.environ.get("MONDAY_BOARD_ID")
    if not board_id:
        raise MondayError("MONDAY_BOARD_ID is not set (add it to .env)")
    return board_id


def _escape(value):
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _graphql(query, timeout=15):
    req = urllib.request.Request(
        MONDAY_API_URL,
        data=json.dumps({"query": query}).encode("utf-8"),
        headers={"Authorization": _token(), "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise MondayError(f"Monday API HTTP {e.code}: {e.read().decode('utf-8', 'ignore')}") from e
    except urllib.error.URLError as e:
        raise MondayError(f"Could not reach Monday API: {e}") from e
    if "errors" in payload:
        raise MondayError("; ".join(err.get("message", str(err)) for err in payload["errors"]))
    return payload["data"]


def search_orders(query_text, limit=10):
    """
    Looks up items on the Workshop board whose name contains the given
    order number or client name. A bare 4-6 digit number found in the
    query is used as the search term (unambiguous, matches order numbers
    exactly); otherwise the raw text is used, which for a repeat client's
    name can return several historical orders — the caller/UI should show
    all matches rather than guessing which one the client means.
    """
    query_text = (query_text or "").strip()
    if not query_text:
        return []

    number_match = ORDER_NUMBER_RE.search(query_text)
    search_term = number_match.group(0) if number_match else query_text

    gql = f"""
    query {{
      boards(ids: {_board_id()}) {{
        items_page(
          limit: {int(limit)},
          query_params: {{rules: [{{column_id: "name", compare_value: ["{_escape(search_term)}"], operator: contains_text}}]}}
        ) {{
          items {{
            id
            name
            group {{ title }}
            column_values(ids: {json.dumps(COLUMN_IDS)}) {{ id text }}
          }}
        }}
      }}
    }}
    """
    data = _graphql(gql)
    boards = data.get("boards") or []
    if not boards:
        return []
    orders = [_parse_item(item) for item in boards[0]["items_page"]["items"]]
    # Active/not-yet-collected orders first; already-picked-up ones last,
    # since a client asking "when will it be ready" almost always means
    # their current order, not a past one that happens to share a name.
    orders.sort(key=lambda o: o["picked_up"] == "Picked-Up")
    return orders


def _parse_item(item):
    cols = {c["id"]: c["text"] for c in item["column_values"]}
    name = item["name"]
    number_match = NAME_LEADING_NUMBER_RE.match(name.strip())
    steps = [
        {"label": label, "status": cols.get(col_id) or "Not Needed"}
        for col_id, label in STEP_COLUMNS
    ]
    return {
        "id": item["id"],
        "name": name,
        "order_number": number_match.group(1) if number_match else None,
        "stage": item["group"]["title"],
        "current_due": cols.get("dup__of_due_date") or None,
        "original_due": cols.get("date7") or None,
        "priority_status": cols.get("status4") or None,
        "picked_up": cols.get("dup__of_priority") or None,
        "customer": cols.get("text9") or None,
        "steps": steps,
    }


def _fmt_date_he(iso_date):
    if not iso_date:
        return None
    try:
        y, m, d = iso_date.split("-")
        return f"{d}.{m}.{y}"
    except ValueError:
        return iso_date


def format_status_reply_he(order):
    """
    A short, casual Hebrew status line in the studio's real reply style
    (see studio_operations_and_communication_notes.md §1) — meant to be
    pasted straight into an email/WhatsApp reply, not a formal system
    message. Deliberately doesn't surface internal production-station
    detail (carpentry/paint/mount/etc.) — clients get stage + due date,
    staff already see the full board for anything more granular.
    """
    label = order["order_number"] or order["name"]
    due = _fmt_date_he(order["current_due"])
    picked_up = order["picked_up"] == "Picked-Up"
    on_hold = order["priority_status"] == "HOLD!"

    if picked_up:
        return f"ההזמנה שלך (מס' {label}) כבר נאספה מהסטודיו."

    if on_hold:
        return f"ההזמנה שלך (מס' {label}) כרגע בטיפול מיוחד/עיכוב — ניצור איתך קשר עם הפרטים, מתנצלים על ההמתנה."

    if order["stage"] == "Ready":
        return f"ההזמנה שלך (מס' {label}) מוכנה לאיסוף מהסטודיו!"

    if order["stage"] == "At Workshop":
        if due:
            return f"ההזמנה שלך (מס' {label}) בעבודה אצלנו בבית המלאכה כרגע, צפויה להיות מוכנה בתאריך {due}."
        return f"ההזמנה שלך (מס' {label}) בעבודה אצלנו בבית המלאכה כרגע."

    # "New Orders" (received, not yet started) or any other/unmapped stage
    if due:
        return f"ההזמנה שלך (מס' {label}) התקבלה ועדיין לא נכנסה לעבודה, צפויה להיות מוכנה בתאריך {due}."
    return f"ההזמנה שלך (מס' {label}) התקבלה ועדיין לא נכנסה לעבודה בבית המלאכה."

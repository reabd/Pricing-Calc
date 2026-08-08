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
from datetime import datetime, timezone

MONDAY_API_URL = "https://api.monday.com/v2"

# Column IDs on the Workshop board that matter for an "is it ready yet"
# reply. These are internal Monday column IDs (stable even if a column's
# display title is renamed), discovered by inspecting the board directly —
# see the studio_operations_and_communication_notes.md §7 notes for the
# full column list this board actually has.
STATUS_COLUMN_IDS = ["dup__of_due_date", "date7", "status4", "dup__of_priority", "text9", "date_mkn4pghm", "creation_log"]

# Per-production-station columns, in real workshop production order: each
# entry is (status_col, label, scheduled_date_col, done_date_col). Every
# order only actually uses a subset of these stations — the rest read
# "Not Needed" and are filtered out before display (see filter_active_steps).
# Chromaluxe has no separate "DONE date" column on this board, hence None.
STEP_COLUMNS = [
    ("foundations3", "Carpentry", "date20", "date_mkzbt7x1"),
    ("dup__of_carpentry", "Paint Brush", "date9", "date_mkzjm31r"),
    ("dup__of_paint_brush", "Paint Spray", "date1", "date_mkzjxn3w"),
    ("dup__of_paint_spray", "Aluminum", "date0", "date_mkzjsfkm"),
    ("dup__of_aluminum", "Mount", "date4", "date_mkzjdksg"),
    ("dup__of_glue", "Passepartout", "date6", "date_mkzjvgbh"),
    ("dup__of_passepartout", "Chromaluxe", "date93", None),
    ("dup__of_chromaluxe5", "CNC", "dup__of_charomaluxe_date", "date_mkzjdtnq"),
    ("color_mksy4vp2", "UV Printer", "date_mksyvgc", "date_mkzjj12y"),
    ("dup__of_chromaluxe", "Closing", "date22", "date_mkzjr9ms"),
]

STEP_DATE_COLUMN_IDS = [
    col for _status, _label, sched, done in STEP_COLUMNS for col in (sched, done) if col
]

COLUMN_IDS = STATUS_COLUMN_IDS + [col_id for col_id, _label, _sched, _done in STEP_COLUMNS] + STEP_DATE_COLUMN_IDS

# A step with this status carries no real information for anyone reading
# the order's progress and is dropped before display.
HIDDEN_STEP_STATUSES = {"Not Needed"}

# "Okapics Due" (date_mkn4pghm) is auto-populated on every order, but when
# there's no real underlying Okapics record it defaults to this exact date
# rather than being left blank — confirmed by the studio owner (2026-08-08)
# after it showed up identically on two unrelated orders (25301, 25735),
# both ~5 months past their real due date. Treated as equivalent to unset.
OKAPICS_DUE_PLACEHOLDER = "2027-01-01"

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
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise MondayError(f"Monday API HTTP {e.code}: {e.read().decode('utf-8', 'ignore')}") from e
    except urllib.error.URLError as e:
        raise MondayError(f"Could not reach Monday API: {e}") from e
    except OSError as e:
        # Covers read timeouts and other lower-level socket failures that
        # urllib doesn't always wrap in URLError.
        raise MondayError(f"Monday API request failed: {e}") from e

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        raise MondayError(f"Monday API returned a non-JSON response: {raw[:300]!r}") from e

    if "errors" in payload:
        raise MondayError("; ".join(err.get("message", str(err)) for err in payload["errors"]))
    if "data" not in payload:
        raise MondayError(f"Monday API response missing 'data': {payload!r}"[:500])
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
    # Drop orders already in the "Ready" stage — in practice these are
    # long since picked up (see order 21931: stage Ready, open 647 days)
    # and just clutter a name search with stale history a client isn't
    # asking about. Confirmed by the studio owner (2026-08-08).
    orders = [o for o in orders if o["stage"] != "Ready"]
    # Active/not-yet-collected orders first; already-picked-up ones last,
    # since a client asking "when will it be ready" almost always means
    # their current order, not a past one that happens to share a name.
    orders.sort(key=lambda o: o["picked_up"] == "Picked-Up")
    return orders


def _parse_item(item):
    cols = {c["id"]: c["text"] for c in item["column_values"]}
    name = item["name"]
    number_match = NAME_LEADING_NUMBER_RE.match(name.strip())

    workshop_due = cols.get("dup__of_due_date") or None
    okapics_due = cols.get("date_mkn4pghm") or None
    if okapics_due == OKAPICS_DUE_PLACEHOLDER:
        okapics_due = None
    resolved_due = okapics_due or workshop_due

    steps = []
    for status_col, label, sched_col, done_col in STEP_COLUMNS:
        status = cols.get(status_col) or "Not Needed"
        if status == "Done" and done_col:
            date = cols.get(done_col) or cols.get(sched_col)
        else:
            date = cols.get(sched_col)
            # A pending station's own scheduled date can go stale the same
            # way Current Due did (see current_due/okapics_due below) —
            # e.g. the order's real due date moved out to Okapics Due but
            # this station's date column was never updated to match. A
            # not-yet-done step can't legitimately be scheduled before the
            # order's own resolved due date, so treat that as a sign the
            # station date is stale and show the order's due date instead.
            # Confirmed by the studio owner (2026-08-08) on order 27187,
            # whose Closing step still showed its old pre-slip date.
            if date and resolved_due and date < resolved_due:
                date = resolved_due
        if status in HIDDEN_STEP_STATUSES:
            continue
        steps.append({"label": label, "status": status, "date": _fmt_date_he(date)})
    return {
        "id": item["id"],
        "name": name,
        "order_number": number_match.group(1) if number_match else None,
        "stage": item["group"]["title"],
        # Okapics Due (a gallery/artist-consignment deadline, only set for
        # that subset of orders) overrides the general Workshop due date
        # when present — confirmed by the studio owner (2026-08-08) after
        # a workshop-only order showed a stale Current Due while Okapics
        # Due had the real, later date. See studio_operations_and_
        # communication_notes.md §7 for the full context.
        "current_due": resolved_due,
        "workshop_due": workshop_due,
        "okapics_due": okapics_due,
        "original_due": cols.get("date7") or None,
        "priority_status": cols.get("status4") or None,
        "picked_up": cols.get("dup__of_priority") or None,
        "customer": cols.get("text9") or None,
        "days_since_created": _days_since_created(cols.get("creation_log")),
        "steps": steps,
    }


def _days_since_created(creation_log_text):
    """
    creation_log's text is like "2026-06-25 08:29:05 UTC". Returns whole
    days elapsed since then (0 for an order created today), or None if the
    column is missing/unparseable.
    """
    if not creation_log_text:
        return None
    try:
        created = datetime.strptime(creation_log_text, "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return (datetime.now(timezone.utc) - created).days


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


# ---------------------------------------------------------------------------
# Closing-status automation (webhook-driven — see
# studio_operations_and_communication_notes.md §8 for the full story of why
# this replaced 9 native Monday automations: those could only check a single
# trigger column, not "all 9 other stations are Done/Not Needed", so they
# could fire prematurely. This does the real check in code instead.
# ---------------------------------------------------------------------------

# The 9 production stations that precede Closing, in pipeline order. Closing
# itself is STEP_COLUMNS[-1] and is deliberately excluded here — it's the
# thing being updated, not a precondition for itself.
PREDECESSOR_STEP_COLUMNS = [col_id for col_id, _label, _sched, _done in STEP_COLUMNS[:-1]]
CLOSING_STATUS_COLUMN = STEP_COLUMNS[-1][0]  # "dup__of_chromaluxe"
PRIORITY_COLUMN = "status4"

# Confirmed by the studio owner (2026-08-08, via a real board example,
# order 27672): a Priority of "Final Date" or "Purple Label" means the
# order is what the owner calls "Urgent" in plain conversation — there is
# no literal "Urgent" label on the Priority column itself.
URGENT_PRIORITY_VALUES = {"Final Date", "Purple Label"}

# A predecessor station only counts as "out of the way" if it's genuinely
# finished or was never needed for this order — anything else (Working,
# Pending Work, Urgent, HOLD!, Planned) means Closing must keep waiting.
STATION_READY_STATUSES = {"Done", "Not Needed"}


def evaluate_closing_transition(item_id):
    """
    Read-only check: fetches the item's current column state and decides
    whether Closing should advance from Planned. Returns (target, board_id)
    where target is "Urgent" / "Pending Work" if the transition should
    happen now, or None if it shouldn't (Closing isn't Planned, or at least
    one of the 9 predecessor stations isn't Done/Not Needed yet). Never
    writes anything — see set_closing_status for the actual mutation.
    """
    column_ids = PREDECESSOR_STEP_COLUMNS + [CLOSING_STATUS_COLUMN, PRIORITY_COLUMN]
    gql = f"""
    query {{
      items(ids: [{int(item_id)}]) {{
        board {{ id }}
        column_values(ids: {json.dumps(column_ids)}) {{ id text }}
      }}
    }}
    """
    data = _graphql(gql)
    items = data.get("items") or []
    if not items:
        return None, None

    item = items[0]
    board_id = item["board"]["id"]
    cols = {c["id"]: c["text"] for c in item["column_values"]}

    if cols.get(CLOSING_STATUS_COLUMN) != "Planned":
        return None, board_id

    all_predecessors_ready = all(
        (cols.get(col_id) or "Not Needed") in STATION_READY_STATUSES
        for col_id in PREDECESSOR_STEP_COLUMNS
    )
    if not all_predecessors_ready:
        return None, board_id

    priority = cols.get(PRIORITY_COLUMN)
    target = "Urgent" if priority in URGENT_PRIORITY_VALUES else "Pending Work"
    return target, board_id


def set_closing_status(item_id, board_id, value):
    """The only function in this module that writes to the board."""
    gql = f"""
    mutation {{
      change_simple_column_value(
        item_id: {int(item_id)}, board_id: {int(board_id)},
        column_id: "{CLOSING_STATUS_COLUMN}", value: "{_escape(value)}"
      ) {{ id }}
    }}
    """
    return _graphql(gql)

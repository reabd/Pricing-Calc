"""
Generalized auto-numbering for "New Item" on a Monday board, one counter
per board. Same mechanism as wood_frame_numbering.py (which stays as its
own module, already built/verified/live for Wood Frames Orders) but
data-driven so adding another board doesn't mean copy-pasting a whole new
module. Used for Aluminum Orders (starts at 2000) and Passepartout Orders
(starts at 3000) — see studio_operations_and_communication_notes.md §13.
"""
import json
import os
from pathlib import Path

import monday_client

DEFAULT_ITEM_NAME = "New item"  # Monday's own placeholder for a freshly-created item

# board_id -> (starting number, env var for a persistent counter path,
# default local filename). Add a new board here + register its webhook to
# extend this to another board.
BOARDS = {
    "9391960224": {"name": "Aluminum Orders", "start": 2000,
                    "counter_env": "ALUMINUM_COUNTER_PATH", "counter_file": "aluminum_counter.json"},
    "9310147481": {"name": "Passepartout Orders", "start": 3000,
                    "counter_env": "PASSEPARTOUT_COUNTER_PATH", "counter_file": "passepartout_counter.json"},
}


def _counter_path(board_id):
    cfg = BOARDS[board_id]
    bundled = Path(__file__).resolve().parent / cfg["counter_file"]
    return Path(os.environ.get(cfg["counter_env"], bundled))


def _read_next(board_id):
    path = _counter_path(board_id)
    if not path.exists():
        return BOARDS[board_id]["start"]
    try:
        return json.loads(path.read_text(encoding="utf-8"))["next"]
    except (json.JSONDecodeError, KeyError, OSError):
        return BOARDS[board_id]["start"]


def _write_next(board_id, value):
    path = _counter_path(board_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"next": value}), encoding="utf-8")


def assign_next_number(board_id, item_id):
    """
    Same idempotency guard as wood_frame_numbering.assign_next_number:
    only acts while the item still has Monday's default "New Item" name,
    so a duplicate webhook delivery can't double-increment or clobber a
    real name. Returns the assigned number, or None if skipped/unknown board.
    """
    if board_id not in BOARDS:
        return None

    query = f"query {{ items(ids: [{int(item_id)}]) {{ name }} }}"
    data = monday_client._graphql(query)
    items = data.get("items") or []
    # Case-insensitive: Monday's real UI-created default is "New item"
    # (lowercase i), not "New Item" -- see the identical note in
    # wood_frame_numbering.py, where this exact bug was first found.
    if not items or items[0]["name"].strip().lower() != DEFAULT_ITEM_NAME.lower():
        return None

    number = _read_next(board_id)
    monday_client._graphql(f"""
    mutation {{
      change_simple_column_value(
        item_id: {int(item_id)}, board_id: {int(board_id)},
        column_id: "name", value: "{number}"
      ) {{ id }}
    }}
    """)
    _write_next(board_id, number + 1)
    return number


def register_webhook(board_id, callback_url):
    """One-time setup — call once the webhook route is already deployed
    and reachable (Monday POSTs a challenge immediately on creation)."""
    gql = f"""
    mutation {{
      create_webhook(
        board_id: {int(board_id)}, url: "{callback_url}", event: create_item
      ) {{ id }}
    }}
    """
    return monday_client._graphql(gql)

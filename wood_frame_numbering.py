"""
Auto-numbers new items on the "Wood Frames Orders" Monday board
(id 9231845383), starting from 1000 -- the studio owner's explicit choice
(2026-08-21) to start a clean sequence going forward, rather than
continuing from the existing item names (1666/1659), which turned out to
be an unreliable source of "the last number" (a stray test item briefly
named "1234567" made a naive max()-based approach unsafe anyway).

A Monday webhook (create_item event on that board, registered via
register_webhook() below -- run once, not on every deploy) calls
/api/wood-frames/webhook in app.py whenever a new item is created; this
module holds the persistent counter and the actual rename logic. See
studio_operations_and_communication_notes.md §12.
"""
import json
import os
from pathlib import Path

import monday_client

WOOD_FRAMES_BOARD_ID = "9231845383"
# Monday's own placeholder name for a freshly-created item -- used as the
# idempotency guard (see assign_next_number).
DEFAULT_ITEM_NAME = "New Item"
START_NUMBER = 1000

# Same PRICING_DATA_PATH/LEARNING_LOG_PATH convention: point this at a
# persistent disk in production so the counter survives redeploys, instead
# of resetting to START_NUMBER every time the container rebuilds.
_bundled_counter_path = Path(__file__).resolve().parent / "wood_frame_counter.json"
COUNTER_PATH = Path(os.environ.get("WOOD_FRAME_COUNTER_PATH", _bundled_counter_path))


def _read_next():
    if not COUNTER_PATH.exists():
        return START_NUMBER
    try:
        return json.loads(COUNTER_PATH.read_text(encoding="utf-8"))["next"]
    except (json.JSONDecodeError, KeyError, OSError):
        return START_NUMBER


def _write_next(value):
    COUNTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    COUNTER_PATH.write_text(json.dumps({"next": value}), encoding="utf-8")


def assign_next_number(item_id):
    """
    Renames a freshly-created item to the next sequential number and
    advances the counter. Returns the assigned number, or None if skipped.

    Idempotent against Monday's at-least-once webhook delivery: only acts
    if the item still has Monday's default "New Item" name. If it's
    already been renamed -- by an earlier delivery of the same event, or
    by a human who typed something else in before this fired -- this is a
    no-op, so a duplicate delivery can't double-increment the counter or
    clobber a manually-chosen name.
    """
    query = f"query {{ items(ids: [{int(item_id)}]) {{ name }} }}"
    data = monday_client._graphql(query)
    items = data.get("items") or []
    if not items or items[0]["name"] != DEFAULT_ITEM_NAME:
        return None

    number = _read_next()
    monday_client._graphql(f"""
    mutation {{
      change_simple_column_value(
        item_id: {int(item_id)}, board_id: {WOOD_FRAMES_BOARD_ID},
        column_id: "name", value: "{number}"
      ) {{ id }}
    }}
    """)
    _write_next(number + 1)
    return number


def register_webhook(callback_url):
    """
    One-time setup, not called at import/deploy time -- run manually once
    the /api/wood-frames/webhook route is live (Monday POSTs a challenge to
    the URL immediately on creation, so the route must already be
    deployed and reachable before calling this).
    """
    gql = f"""
    mutation {{
      create_webhook(
        board_id: {WOOD_FRAMES_BOARD_ID}, url: "{callback_url}", event: create_item
      ) {{ id }}
    }}
    """
    return monday_client._graphql(gql)

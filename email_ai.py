"""
Decides whether a new inbound client email is a confident-enough case to
draft a reply for, and if so, drafts it — using the Claude API directly
(the app has no interactive Claude Code session to lean on here, unlike
everywhere else in this project). Conservative by design: skip is always
the safe default. See studio_operations_and_communication_notes.md §9 and
the "email draft policy" memory this was built from.

Order-status questions get real Monday.com data folded into the prompt
(via monday_client.search_orders) so the model isn't guessing dates —
same underlying lookup already used by the interactive Order Status tab.
"""
import json
import os
from pathlib import Path

import anthropic

import monday_client

MODEL = "claude-sonnet-5"

NOTES_PATH = Path(__file__).resolve().parent / "studio_operations_and_communication_notes.md"

_client = None
_notes_text = None


def _client_instance():
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def _studio_notes():
    global _notes_text
    if _notes_text is None:
        _notes_text = NOTES_PATH.read_text(encoding="utf-8")
    return _notes_text


def invalidate_notes_cache():
    """Called after email_learning.py appends a new learning to the notes
    file, so the next drafting decision in this same process picks it up
    immediately instead of waiting for a restart."""
    global _notes_text
    _notes_text = None


DECISION_TOOL = {
    "name": "submit_email_decision",
    "description": "Decide whether to draft a reply to this inbound client email, and draft it if so.",
    "input_schema": {
        "type": "object",
        "properties": {
            "should_draft": {
                "type": "boolean",
                "description": (
                    "true ONLY if you are genuinely confident about the right reply — a real "
                    "client question the studio's documented policies/data clearly answer "
                    "(order status, a simple confirmation, a well-documented FAQ). false for "
                    "anything ambiguous, anything needing a price quote the pricing app would "
                    "compute (don't try to price things yourself), anything emotionally "
                    "sensitive, complaints, anything you're not sure about, or anything that "
                    "isn't really a question needing an answer at all (e.g. a client just "
                    "saying thanks, or saying they'll get back to you)."
                ),
            },
            "reason": {
                "type": "string",
                "description": "One short sentence: why draft, or why skip. Internal only, not sent anywhere.",
            },
            "reply_subject": {
                "type": ["string", "null"],
                "description": "Only if should_draft is true. Usually 'Re: <original subject>'.",
            },
            "reply_body": {
                "type": ["string", "null"],
                "description": (
                    "Only if should_draft is true. Plain text, matching the sender's own "
                    "language (Hebrew or English), in the studio's real tone documented "
                    "below — casual, short, itemized where relevant, explicit about VAT if "
                    "money is mentioned, signed off simply. Do not invent information not "
                    "given below or in the studio notes."
                ),
            },
        },
        "required": ["should_draft", "reason"],
    },
}


def _monday_context_for(candidate):
    """
    Best-effort: try the sender's name, and any 4-6 digit number in the
    subject/body, against the Monday board. Returns a JSON-ish string
    block for the prompt, or None if nothing came back — feeding this
    unconditionally (not just for messages that look order-related) is
    cheap and lets the model use it if relevant without us having to
    classify the email's intent ourselves first.
    """
    queries = []
    number_match = monday_client.ORDER_NUMBER_RE.search(candidate["subject"] + " " + candidate["body"])
    if number_match:
        queries.append(number_match.group(0))
    if candidate.get("from_name"):
        queries.append(candidate["from_name"])

    for q in queries:
        try:
            orders = monday_client.search_orders(q, limit=5)
        except monday_client.MondayError:
            continue
        if orders:
            simplified = [
                {
                    "order_name": o["name"],
                    "stage": o["stage"],
                    "current_due": o["current_due"],
                    "picked_up": o["picked_up"],
                    "priority_status": o["priority_status"],
                }
                for o in orders
            ]
            return json.dumps(simplified, ensure_ascii=False)
    return None


def decide_and_draft_reply(candidate):
    """
    candidate: one of the dicts from imap_client.fetch_unanswered_inbox_emails().
    Returns the tool's parsed input dict, always containing at least
    should_draft/reason.
    """
    monday_context = _monday_context_for(candidate)

    system_prompt = (
        "You are helping The Print House (a fine-art print/framing studio in Tel Aviv) decide "
        "whether to draft a reply to a new client email. You are extremely conservative: skip "
        "(should_draft=false) is always the safe default. Only draft when the studio's own "
        "documented policies/data below give you everything needed for an accurate, complete "
        "answer.\n\n"
        "Below is the studio's own internal operations & communication notes file — it documents "
        "real reply style, policies, FAQ patterns, and how to read Monday.com order-status data. "
        "Match that tone and those policies exactly; don't invent anything beyond what's "
        "documented here or in the live Monday data (if provided).\n\n"
        f"=== STUDIO OPERATIONS & COMMUNICATION NOTES ===\n{_studio_notes()}\n"
        "=== END NOTES ===\n"
    )
    if monday_context:
        system_prompt += (
            f"\n=== LIVE MONDAY.COM DATA for this sender (may or may not be relevant — only use "
            f"it if the email is actually asking about order status) ===\n{monday_context}\n"
            "=== END MONDAY DATA ===\n"
        )

    user_text = (
        f"From: {candidate['from_name']} <{candidate['from_email']}>\n"
        f"Subject: {candidate['subject']}\n\n"
        f"{candidate['body']}"
    )

    resp = _client_instance().messages.create(
        model=MODEL,
        max_tokens=2048,
        system=system_prompt,
        tools=[DECISION_TOOL],
        tool_choice={"type": "tool", "name": DECISION_TOOL["name"]},
        messages=[{"role": "user", "content": user_text}],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == DECISION_TOOL["name"]:
            return block.input
    raise RuntimeError("Model did not call submit_email_decision")

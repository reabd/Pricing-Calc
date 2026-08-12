"""
Reads real (inbound client email, actual staff-sent reply) pairs and asks
Claude to extract any new, durable operational/pricing/policy fact that
isn't already documented in studio_operations_and_communication_notes.md —
appending anything found to a dedicated, clearly-marked section at the end
of that file for a human to review and fold into the real sections. This is
what lets email_ai.py's drafting judgment improve over time from what staff
actually do, instead of staying frozen at whatever was true when the notes
file was last hand-edited. See studio_operations_and_communication_notes.md
§10.

Deliberately does not touch the notes file's existing sections — an LLM
editing its own knowledge base unsupervised is exactly the kind of thing
that should stay reviewable, not silently authoritative.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import anthropic

NOTES_PATH = Path(__file__).resolve().parent / "studio_operations_and_communication_notes.md"
SKILL_PATH = Path(__file__).resolve().parent / ".claude/skills/answer-print-house-email/SKILL.md"
MODEL = "claude-sonnet-5"
SECTION_HEADER = "## 10. Auto-observed learnings (pending review)"
SKILL_SECTION_HEADER = "## 6. Auto-learned facts (from real client replies)"

# Same PRICING_DATA_PATH convention as app.py: point this at a persistent
# disk in production (LEARNING_LOG_PATH) so the daily digest (see
# daily_report.py) survives redeploys, instead of living inside the
# ephemeral git checkout like the bundled default does. Append-only JSONL,
# one line per extracted fact — the source of truth for "what got learned
# today," independent of the notes file's own §10 section (which is a
# human-readable mirror, not something the digest parses).
_bundled_log_path = Path(__file__).resolve().parent / "learning_log.jsonl"
LOG_PATH = Path(os.environ.get("LEARNING_LOG_PATH", _bundled_log_path))

_client = None


def _client_instance():
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


LEARNING_TOOL = {
    "name": "submit_learnings",
    "description": "Extract any new, durable, reusable facts from this real client exchange that aren't already documented.",
    "input_schema": {
        "type": "object",
        "properties": {
            "learnings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "fact": {
                            "type": "string",
                            "description": (
                                "One durable, reusable operational/pricing/policy fact, written "
                                "as a standalone sentence (not a summary of the thread). Only "
                                "include something that would still be true and useful for a "
                                "different client/order in the future — never a one-off detail "
                                "like a specific client's name, a random custom price, or an "
                                "order number."
                            ),
                        },
                    },
                    "required": ["fact"],
                },
                "description": "Empty list if nothing new and durable was learned from this exchange — the correct answer for most exchanges.",
            },
        },
        "required": ["learnings"],
    },
}


def _notes_text():
    return NOTES_PATH.read_text(encoding="utf-8")


def extract_learnings(inbound, reply_body):
    """
    inbound: a candidate dict (from imap_client), the client's original email.
    reply_body: the studio's actual sent reply text.
    Returns a list of fact strings (possibly empty).
    """
    system_prompt = (
        "You help The Print House (a fine-art print/framing studio in Tel Aviv) keep its "
        "internal operations notes up to date by learning from real client emails and how "
        "staff actually replied. You will see one real exchange: a client's email and the "
        "studio's actual sent reply. Extract ONLY genuinely new, durable, reusable facts — "
        "things that would help answer a *different* future client's similar question (a "
        "policy, a capability, a pricing relationship, a process detail). Do NOT extract "
        "anything already covered below, anything order/client-specific (names, order "
        "numbers, one-off custom prices), or anything you're inferring rather than what the "
        "reply actually states. When in doubt, extract nothing — an empty list is the "
        "correct, safe answer for most exchanges.\n\n"
        f"=== CURRENT STUDIO NOTES (do not repeat anything already here) ===\n{_notes_text()}\n"
        "=== END NOTES ==="
    )
    user_text = (
        f"CLIENT EMAIL:\nFrom: {inbound.get('from_name')} <{inbound.get('from_email')}>\n"
        f"Subject: {inbound.get('subject')}\n\n{inbound.get('body')}\n\n"
        f"--- STUDIO'S ACTUAL REPLY ---\n{reply_body}"
    )
    resp = _client_instance().messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system_prompt,
        tools=[LEARNING_TOOL],
        tool_choice={"type": "tool", "name": LEARNING_TOOL["name"]},
        messages=[{"role": "user", "content": user_text}],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == LEARNING_TOOL["name"]:
            return [item["fact"] for item in block.input.get("learnings", []) if item.get("fact")]
    return []


def append_learnings(facts, citation):
    """
    Appends each fact to a dedicated, clearly-marked section at the end of
    the notes file, with a citation (subject + date) so a human can trace
    it back to the real exchange. Creates the section on first use. Also
    mirrors the same facts into the answer-print-house-email skill (see
    _append_to_skill) — that's the file Claude Code sessions actually read
    when drafting interactively, so learnings need to live there directly,
    not just be reachable via a pointer.
    """
    if not facts:
        return
    text = NOTES_PATH.read_text(encoding="utf-8")
    if SECTION_HEADER not in text:
        text = text.rstrip("\n") + (
            f"\n\n---\n\n{SECTION_HEADER}\n\n"
            "Facts auto-extracted by the background poller from real client emails and the "
            "studio's actual replies (see §9). Not yet reviewed or folded into the sections "
            "above — treat as a candidate list, not settled policy.\n"
        )
    entry = "\n".join(f"- {fact} ({citation})" for fact in facts)
    text = text.rstrip("\n") + "\n" + entry + "\n"
    NOTES_PATH.write_text(text, encoding="utf-8")

    _log_facts(facts, citation)
    _append_to_skill(facts, citation)


def _append_to_skill(facts, citation):
    """Mirrors newly learned facts into the skill file itself. A failure
    here shouldn't take down the caller — the notes-file append above
    already succeeded and is the more important write."""
    try:
        if not SKILL_PATH.exists():
            return
        text = SKILL_PATH.read_text(encoding="utf-8")
        if SKILL_SECTION_HEADER not in text:
            text = text.rstrip("\n") + (
                f"\n\n---\n\n{SKILL_SECTION_HEADER}\n\n"
                "Facts auto-extracted by the background poller from real client emails and the "
                "studio's actual replies (mirrors studio_operations_and_communication_notes.md "
                "§10). Apply these the same way as the rest of this skill.\n"
            )
        entry = "\n".join(f"- {fact} ({citation})" for fact in facts)
        text = text.rstrip("\n") + "\n" + entry + "\n"
        SKILL_PATH.write_text(text, encoding="utf-8")
    except OSError as e:
        print(f"[email-learner] failed to write skill file: {e!r}", flush=True)


def _log_facts(facts, citation):
    """Appends each fact to LOG_PATH with the current timestamp — read back
    by daily_report.py to build the day's digest. A logging failure here
    shouldn't take down the caller; the notes-file append above already
    succeeded and is the more important write."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            now = datetime.now(timezone.utc).isoformat()
            for fact in facts:
                f.write(json.dumps({"logged_at": now, "fact": fact, "citation": citation}, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"[email-learner] failed to write learning log: {e!r}", flush=True)

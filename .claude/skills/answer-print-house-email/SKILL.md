---
name: answer-print-house-email
description: How to draft or answer a client email for The Print House (fine-art print/framing studio, Tel Aviv) — tone, formatting, and what's safe to draft vs. skip. Use this whenever drafting, editing, or reviewing a reply to a client email in this project, whether done by hand through the Gmail tools or by touching the automated poller code (app.py, email_ai.py, imap_client.py, quote_reply.py). Also consult it before changing how the poller formats or composes outbound drafts, even if the request is phrased as a bug fix rather than "write an email" — formatting regressions here are easy to introduce silently. Trigger on mentions of client emails, quote replies, order-status replies, draft quality, email formatting/signature/HTML, or the poller's drafting behavior.
---

# Answering a Print House client email

You're drafting as the studio, not as an assistant labeled "AI." A client should never be able to
tell the reply wasn't typed by Rea, Amit, Gal, or whoever normally answers. That's the bar.

## 1. Tone — match how the studio actually writes

The full style guide lives in [`studio_operations_and_communication_notes.md`](../../studio_operations_and_communication_notes.md)
§1 — read it before drafting anything non-trivial, since it has verbatim real examples. The
headline rules, so you don't have to re-derive them every time:

- **Casual, conversational, never formal** — even with museums and galleries. No "Dear Sir/Madam."
  Hebrew opens with something like "מה נשמע?" or "מה שלומך?"; English opens with a plain "Hi
  \<name>,". This holds for institutional clients too — the studio just doesn't switch registers.
- **Itemized pricing, one line per item**: `<size/description> - <price> ש"ח` (add "ליח'" if it's
  a per-unit price across a quantity). Not a lump sum for multi-item requests.
- **VAT is stated explicitly, every single time** — "המחירים לא כוללים מע"מ" (excludes VAT) or
  "כולל מע"מ" (includes VAT). Never send a number without saying which. If unsure which the studio
  wants for this reply, default to excluding VAT (`vat_included=False` in `quote_reply.draft_reply`)
  — that's the more common pattern in real mail.
- **Closing is an ask, not a CTA button**: "עדכני/עדכנו אותנו" (let us know), not "please confirm
  to proceed."
- **Sign off simply** — "תודה" (+ first name if signing personally) or "בברכה, \<name>" for more
  formal/institutional threads. Don't over-elaborate.

## 2. Formatting — this is the part that actually broke

A flat plain-text draft with no paragraph breaks reads as obviously not-human, and this project has
already shipped that bug once (fixed 2026-08-12). Don't reintroduce it:

- **Write in real paragraphs.** Put a genuine blank line between distinct parts — greeting, each
  itemized point or logical chunk, closing line — the same way the verbatim examples in the notes
  file are broken up. A single run-on block, even if grammatically fine, looks wrong.
- **A drafted Gmail message needs an HTML part, not just plain text.** `quote_reply.to_html(body,
  language)` converts blank-line-separated paragraphs into styled `<p>` blocks and appends the
  studio's real signature (bold hours, hyperlinked website, Georgia font — matches an actual sent
  signature, not a generic one). When creating or updating a draft:
  - Via the Gmail MCP tools: pass both `body` (plain text) and `htmlBody` (`to_html()`'s output) to
    `create_draft`/`update_draft`.
  - Via the IMAP poller path: pass `reply_html=quote_reply.to_html(reply_body, language)` into
    `imap_client.append_draft_reply()` — never call it with just plain text if `quote_reply` is
    importable in that context.
- **Never write your own copy of the signature block** (address/phone/hours/website). It's appended
  automatically by `to_html()`. Writing it yourself produces a visible duplicate — one plain, one
  styled — which looks worse than the original plain-text bug.
- **Language and direction**: detect Hebrew via `re.search("[֐-׿]", text)` (the pattern already used
  in `app.py`/`quote_reply.py`) and pass `language="he"`/`"en"` through — `to_html()` sets RTL/LTR
  and alignment from that, don't hardcode one direction.

## 3. What's safe to draft vs. what to skip

Draft-only, always. The one carved-out exception is real, immediate SMTP sends for **internal**
notifications the studio owner explicitly asked to be automatic (the rush-flag email to
`framing@theprinthouse.co.il`, the daily learning-summary email to the owner) — those aren't
client-facing and don't follow this style guide's client tone. Every client-facing reply is a draft
for a human to review, full stop.

Skip (don't draft, or draft with should_draft=false) anything that is:
- **Ambiguous** — ordering interpretation, unclear specs, anything you'd have to guess at.
- **A price the pricing engine hasn't actually computed.** Never estimate, round, or "roughly"
  price something by feel. The real pipeline is `llm_parser.parse_quote_request()` →
  `price_parsed_lines()` → `quote_reply.draft_reply()` — see `app.py`'s `_try_price_quote()` for the
  reference implementation. If that pipeline can't confidently parse the request (ambiguous wording,
  missing size, `clarification_needed`), that's the signal to skip, not to fill the gap yourself.
- **Emotionally sensitive, a complaint, or a defect report** — these get handled conversationally by
  a real person (see notes §3, "Revisions/reprints/defects"); don't attempt a policy-driven reply.
- **Anything not confidently answerable** from the notes file or live Monday.com order data. "I'm
  not sure" is a skip, not a best-effort guess — this matches the existing `should_draft=false`
  default already baked into `email_ai.py`'s decision tool.

## 4. Order-status replies

If the question is "when will my order be ready," use live Monday.com data
(`monday_client.search_orders()`), not a guess — see notes §7 for the exact lookup rules (Okapics
Due vs. Current Due precedence, ignoring already-picked-up orders in the reply text, etc.). Don't
invent a turnaround estimate from the general figures in notes §6 once an order actually exists on
the board — the board's own due date is authoritative.

## 5. When you're editing the poller code itself, not drafting by hand

Changes to `app.py`, `email_ai.py`, `imap_client.py`, or `quote_reply.py` that touch how replies are
composed are still "drafting an email" for the purposes of this skill — run the formatting checklist
in §2 against whatever you change. A code change that silently drops the HTML alternative, or lets
the model reintroduce its own signature text, is the same bug as a badly-hand-drafted email, just
harder to notice because no one reads raw MIME before it ships.

## 6. Auto-learned facts (from real client replies)

`email_learning.py`'s background scan (see notes §11) writes new durable facts here automatically —
extracted from real client emails and the studio's actual sent replies — every time it finds
something genuinely new. Nothing has been auto-learned yet as of this writing; once entries start
appearing below, treat them the same as the rest of this skill, not as a lower-confidence appendix.


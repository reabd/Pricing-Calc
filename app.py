"""
Local Flask app: a friendly front end over pricing_engine.py + llm_parser.py.

Run with:
    python3 app.py
Then open http://localhost:5050

The Anthropic API key is read from a .env file next to this script (see
.env.example) so it never has to be typed into a terminal.

Access control: if APP_PASSWORD is set (in .env locally, or as a real
environment variable when deployed), every page requires that shared
password before use. If it's not set at all, the app stays open with no
login — that's the default for local/trusted use.
"""
import os
import re
import secrets
import shutil
import threading
import time
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

import business_rules
import daily_report
import email_ai
import email_learning
import email_sender
import imap_client
import llm_parser
import monday_client
import quote_reply
from pricing_engine import JobComponentRequest, PricingCatalog, PricingError, price_job

load_dotenv(Path(__file__).resolve().parent / ".env")

APP_PASSWORD = os.environ.get("APP_PASSWORD")
# Shared secret for machine-to-machine calls from Opics (and other
# server clients). When set, any /api/* request that carries a matching
# X-Pricing-Calc-Key header skips the browser session login gate.
# The same key can also open a browser session via /auth/from_opics?key=...
# so Opics can embed this app in an iframe without the shared password form.
PRICING_CALC_API_KEY = os.environ.get("PRICING_CALC_API_KEY")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.permanent_session_lifetime = timedelta(days=30)

# PRICING_DATA_PATH lets a deployment point this at a persistent disk
# (e.g. /data/pricing_data.json on a mounted volume) so price edits made
# through the app survive restarts/redeploys, instead of living inside
# the git checkout. Locally, this env var is unset, so it just uses the
# bundled file next to this script, same as before.
_bundled_data_path = Path(__file__).resolve().parent / "pricing_data.json"
_data_path = Path(os.environ.get("PRICING_DATA_PATH", _bundled_data_path))
if not _data_path.exists() and _bundled_data_path.exists() and _data_path != _bundled_data_path:
    # First boot against a fresh persistent disk: seed it from the
    # baseline that was extracted from the Excel workbook. If this ever
    # fires again on a deploy where prices were already customized, it
    # means the persistent disk didn't actually persist (was recreated,
    # unmounted, etc.) — logged loudly here so that's visible in the
    # deploy logs instead of silently reverting prices with no trace.
    print(f"[pricing_data] {_data_path} not found — seeding from bundled baseline "
          f"{_bundled_data_path}. If price customizations were expected to already "
          f"be here, the persistent disk did not actually persist.", flush=True)
    _data_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(_bundled_data_path, _data_path)
else:
    print(f"[pricing_data] using existing file at {_data_path} (not re-seeding).", flush=True)

catalog = PricingCatalog(_data_path)


def _api_key_authorized():
    if not PRICING_CALC_API_KEY:
        return False
    provided = request.headers.get("X-Pricing-Calc-Key", "") or request.args.get("key", "")
    if not provided:
        return False
    return secrets.compare_digest(provided, PRICING_CALC_API_KEY)


def _establish_api_key_session():
    session.permanent = True
    session["authenticated"] = True


@app.before_request
def require_login():
    if request.endpoint in ("login", "static", "api_monday_webhook", "auth_from_opics"):
        return None
    if _api_key_authorized():
        return None
    if APP_PASSWORD and session.get("authenticated"):
        return None
    if not PRICING_CALC_API_KEY and not APP_PASSWORD:
        return None
    if request.path.startswith("/api/"):
        return jsonify({"error": "Unauthorized"}), 401
    if APP_PASSWORD:
        return redirect(url_for("login", next=request.path))
    return jsonify({"error": "Unauthorized"}), 401


@app.route("/auth/from_opics")
def auth_from_opics():
    """
    One-shot browser SSO from Opics: Opics embeds
    /auth/from_opics?key=<PRICING_CALC_API_KEY> in an iframe. Matching key
    opens a normal Flask session so the UI works without APP_PASSWORD.
    """
    if not PRICING_CALC_API_KEY:
        return "Pricing-Calc API key is not configured.", 503
    if not _api_key_authorized():
        return "Unauthorized", 401
    _establish_api_key_session()
    return redirect(url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if not APP_PASSWORD:
        return redirect(url_for("index"))
    error = None
    if request.method == "POST":
        if secrets.compare_digest(request.form.get("password", ""), APP_PASSWORD):
            session.permanent = True
            session["authenticated"] = True
            return redirect(request.args.get("next") or url_for("index"))
        error = "Incorrect password."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("authenticated", None)
    return redirect(url_for("login"))


def _round_money(value):
    return None if value is None else round(value, 2)


def line_result_to_dict(result):
    return {
        "lines": [
            {
                "slot_key": l.slot_key,
                "item_name": l.item_name,
                "quantity": l.quantity,
                "material_price": _round_money(None if l.unpriced else l.material_price),
                "work_price": _round_money(None if l.unpriced else l.work_price),
                "line_total": _round_money(l.line_total),
                "scales_with_quantity": l.scales_with_quantity,
                "unpriced": bool(l.unpriced),
            }
            for l in result.lines
        ],
        "pricelist_single_unit": round(result.pricelist_single_unit, 2),
        "quantity_price": round(result.quantity_price, 2),
        "final_price_incl_vat": round(result.final_price_incl_vat, 2),
        "margin": round(result.margin, 4),
        "order_quantity": result.order_quantity,
    }


def price_parsed_lines(parsed_lines, apply_business_rules=False):
    """
    apply_business_rules=True resolves wood_species/paint_method into the
    right profile/paint items deterministically (see business_rules.py).
    Only used for the free-text path — structured/API callers that set
    components explicitly (e.g. row27_paint directly) get exactly what
    they asked for, with no rule silently overriding it.
    """
    quotes = []
    for parsed in parsed_lines:
        components = catalog.resolve_components_dict(
            parsed.get("preset_key"), parsed.get("components", [])
        )
        # Structural rules, not language-interpretation niceties — apply
        # unconditionally to every caller, structured or free-text.
        components = business_rules.apply_box_back_frame_rule(
            components, parsed["height_cm"], parsed["width_cm"]
        )
        components = business_rules.apply_box_glyph_rule(
            components, parsed["height_cm"], parsed["width_cm"]
        )
        explicit_slots = {c["slot_key"] for c in parsed.get("components", [])}
        components = business_rules.apply_box_profile_size_default(
            catalog, components, parsed["height_cm"], parsed["width_cm"], explicit_slots
        )
        if apply_business_rules:
            components, error = business_rules.apply_wood_paint_rules(
                catalog, components,
                wood_species=parsed.get("wood_species"),
                paint_method=parsed.get("paint_method"),
                float_profile_size=parsed.get("float_profile_size"),
            )
            if error:
                return {"clarification_needed": error}

        component_requests = [
            JobComponentRequest(
                slot_key,
                data.get("item_name") or "",
                data.get("quantity", 1.0),
                data.get("opics_id") or "",
            )
            for slot_key, data in components.items()
        ]
        result = price_job(
            catalog, component_requests,
            height_cm=parsed["height_cm"], width_cm=parsed["width_cm"],
            order_quantity=parsed.get("order_quantity", 1),
        )
        entry = line_result_to_dict(result)
        entry["description"] = parsed.get("description", "")
        entry["height_cm"] = parsed["height_cm"]
        entry["width_cm"] = parsed["width_cm"]
        quotes.append(entry)
    grand_total = round(sum(q["final_price_incl_vat"] for q in quotes), 2)
    return {"quotes": quotes, "grand_total_incl_vat": grand_total}


@app.route("/")
def index():
    return render_template("index.html", excluded_features=catalog.excluded_features)


@app.route("/api/catalog")
def api_catalog():
    return jsonify(catalog.list_slots())


@app.route("/api/presets")
def api_presets():
    return jsonify(list(catalog.presets.values()))


@app.route("/api/quote/freetext", methods=["POST"])
def api_quote_freetext():
    text = request.json.get("text", "").strip()
    if not text:
        return jsonify({"error": "Empty request"}), 400
    try:
        parsed = llm_parser.parse_quote_request(text, catalog)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500

    if parsed.get("clarification_needed"):
        return jsonify({"clarification_needed": parsed["clarification_needed"]})

    try:
        return jsonify(price_parsed_lines(parsed["lines"], apply_business_rules=True))
    except PricingError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/quote/structured", methods=["POST"])
def api_quote_structured():
    lines = request.json.get("lines", [])
    try:
        return jsonify(price_parsed_lines(lines))
    except PricingError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/price-update/parse", methods=["POST"])
def api_price_update_parse():
    text = request.json.get("text", "").strip()
    if not text:
        return jsonify({"error": "Empty request"}), 400
    try:
        parsed = llm_parser.parse_price_update(text, catalog)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500

    if parsed.get("clarification_needed"):
        return jsonify({"clarification_needed": parsed["clarification_needed"]})

    try:
        diffs = llm_parser.preview_price_changes(catalog, parsed["changes"])
    except (PricingError, ValueError, KeyError) as e:
        return jsonify({"error": str(e)}), 400

    if not diffs:
        return jsonify({"error": "No matching items found for that instruction."}), 400

    return jsonify({"diffs": diffs})


@app.route("/api/price-update/apply", methods=["POST"])
def api_price_update_apply():
    diffs = request.json.get("diffs", [])
    if not diffs:
        return jsonify({"error": "No diffs to apply"}), 400
    llm_parser.apply_price_changes(catalog, diffs)
    return jsonify({"status": "applied", "count": len(diffs)})


@app.route("/api/order-status")
def api_order_status():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Enter an order number or client name."}), 400
    try:
        orders = monday_client.search_orders(query)
    except monday_client.MondayError as e:
        return jsonify({"error": str(e)}), 502
    except Exception as e:
        # Belt-and-suspenders: whatever went wrong, the frontend expects
        # JSON back, not Flask's default HTML error page (which fails to
        # parse as JSON client-side with a confusing "Unexpected token '<'"
        # error instead of showing the actual problem).
        print(f"[order-status] unexpected error for query {query!r}: {e!r}", flush=True)
        return jsonify({"error": f"Order-status lookup failed unexpectedly: {e}"}), 500
    return jsonify({
        "matches": [
            {**order, "reply_text": monday_client.format_status_reply_he(order)}
            for order in orders
        ]
    })


FRAMING_TEAM_EMAIL = os.environ.get("FRAMING_TEAM_EMAIL", "framing@theprinthouse.co.il")


@app.route("/api/order-status/flag-rush", methods=["POST"])
def api_order_status_flag_rush():
    data = request.json or {}
    order_name = (data.get("order_name") or "").strip()
    requested_date = (data.get("requested_date") or "").strip()
    if not order_name or not requested_date:
        return jsonify({"error": "Order name and requested date are required."}), 400

    subject = f"בקשת זירוז - הזמנה {order_name} - עד {requested_date}"
    body = (
        f"היי,\n\n"
        f"לקוח/ה ביקש/ה לזרז את ההזמנה הבאה:\n\n"
        f"הזמנה: {order_name}\n"
        f"שלב נוכחי: {data.get('stage') or '—'}\n"
        f"תאריך יעד נוכחי: {data.get('current_due') or '—'}\n"
        f"תאריך מבוקש: {requested_date}\n\n"
        f"אפשר לבדוק אם זה ריאלי ולעדכן בהתאם (כולל עדכון התאריך ב-Monday אם מאושר)?\n\n"
        f"תודה,\nנשלח אוטומטית מכלי בדיקת סטטוס הזמנות"
    )
    try:
        email_sender.send_email(FRAMING_TEAM_EMAIL, subject, body)
    except email_sender.EmailError as e:
        return jsonify({"error": str(e)}), 502
    except Exception as e:
        print(f"[flag-rush] unexpected error: {e!r}", flush=True)
        return jsonify({"error": f"Failed to send notification: {e}"}), 500
    return jsonify({"status": "sent", "to": FRAMING_TEAM_EMAIL})


@app.route("/api/daily-report/send-now", methods=["GET", "POST"])
def api_daily_report_send_now():
    """
    Manual trigger for daily_report.send_daily_report() — same report the
    18:00 scheduler sends (see _run_daily_report_scheduler below), just
    on-demand instead of waiting. GET is allowed too so it can be triggered
    by opening a URL in a browser (protected by the same login/API-key gate
    as every other /api/* route — see require_login above), not just POSTed.
    Reads the real learning log on whatever machine this request lands on,
    so it only reflects today's actual learnings when run against the
    deployed instance, not a local dev server.
    """
    from datetime import datetime

    recipient = request.args.get("to") or os.environ.get("DAILY_REPORT_RECIPIENT", "rea@theprinthouse.co.il")
    today = datetime.now(daily_report.REPORT_TIMEZONE).date()
    try:
        daily_report.send_daily_report(today, recipient)
    except email_sender.EmailError as e:
        return jsonify({"error": str(e)}), 502
    except Exception as e:
        print(f"[daily-report] manual send failed: {e!r}", flush=True)
        return jsonify({"error": f"Failed to send report: {e}"}), 500
    return jsonify({"status": "sent", "to": recipient, "date": today.isoformat()})


@app.route("/api/monday/webhook", methods=["POST"])
def api_monday_webhook():
    """
    Monday.com calls this whenever one of the 9 production-station status
    columns changes on the Workshop board (see the 9 webhook subscriptions
    registered via register_closing_webhooks.py). Not behind the app's
    login gate — Monday's servers can't complete that login flow — see the
    exemption in require_login() above.

    Replaces what was originally attempted as 9 native Monday automations:
    those could only check a single trigger column each ("and only if
    Closing is Planned"), with no way to also verify the *other* 8 stations
    were actually done — so they could fire prematurely (e.g. if Mount
    finished while Carpentry was still in progress). This does the real
    "are all 9 other stations Done/Not Needed" check in code instead. See
    studio_operations_and_communication_notes.md §8 for the full story.
    """
    payload = request.json or {}

    # Monday's webhook registration handshake: it POSTs a challenge token
    # once when the subscription is created, and expects the exact same
    # token echoed back before it'll consider the URL verified.
    if "challenge" in payload:
        return jsonify({"challenge": payload["challenge"]})

    event = payload.get("event") or {}
    item_id = event.get("pulseId")
    column_id = event.get("columnId")
    if not item_id or column_id not in monday_client.PREDECESSOR_STEP_COLUMNS:
        # Logged (not just silently dropped) so a payload-shape mismatch
        # from Monday's side is diagnosable in Render's logs rather than
        # this route quietly never firing for reasons that are invisible
        # from the outside.
        print(f"[monday-webhook] ignored payload: {payload!r}"[:1000], flush=True)
        return jsonify({"status": "ignored"})

    try:
        target, board_id = monday_client.evaluate_closing_transition(item_id)
        if target:
            monday_client.set_closing_status(item_id, board_id, target)
            print(f"[monday-webhook] item {item_id}: Closing -> {target}", flush=True)
    except monday_client.MondayError as e:
        print(f"[monday-webhook] error for item {item_id}: {e}", flush=True)
        return jsonify({"status": "error", "error": str(e)}), 502
    return jsonify({"status": "ok"})


@app.route("/api/price-list")
def api_price_list():
    return jsonify(list(catalog.slots.values()))


# Every cost-driver field on an item is directly editable in the Price
# List table.
EDITABLE_PRICE_LIST_FIELDS = {
    "fixed_material_cost", "var_material_cost", "material_indirect", "material_risk", "material_profit",
    "fixed_effort_cost", "var_effort_cost", "min_effort_cost", "effort_indirect", "effort_risk", "effort_profit",
}

UNPRICED_ITEM_TEMPLATE = {
    "fixed_material_cost": 0,
    "var_material_cost": 0,
    "material_indirect": 0,
    "material_risk": 0,
    "material_profit": 0,
    "var_effort_cost": 0,
    "fixed_effort_cost": 0,
    "min_effort_cost": 0,
    "effort_indirect": 0,
    "effort_risk": 0,
    "effort_profit": 0,
    "unpriced": True,
}


@app.route("/api/price-list/update-item", methods=["POST"])
def api_price_list_update_item():
    data = request.json or {}
    slot_key = data.get("slot_key")
    item_name = data.get("item_name")
    field = data.get("field")
    value = data.get("value")

    try:
        slot, resolved_name, _item = catalog.find_item(slot_key, item_name)
    except PricingError as e:
        return jsonify({"error": str(e)}), 400

    if field == "unpriced":
        # Explicit activate/deactivate. Clearing unpriced enables real quotes.
        unpriced = bool(value)
        if unpriced:
            slot["items"][resolved_name]["unpriced"] = True
        else:
            slot["items"][resolved_name].pop("unpriced", None)
        catalog.save()
        return jsonify({"status": "saved", "unpriced": unpriced})

    if field == "opics_id":
        opics_id = ("" if value is None else str(value)).strip()
        if opics_id:
            # One Okapics ID should map to at most one catalog item in this slot.
            for name, rec in slot["items"].items():
                if name == resolved_name:
                    continue
                if rec.get("opics_id", "").strip() == opics_id:
                    return jsonify({
                        "error": f"Okapics ID {opics_id!r} is already linked to {name!r}."
                    }), 400
            slot["items"][resolved_name]["opics_id"] = opics_id
        else:
            slot["items"][resolved_name].pop("opics_id", None)
        catalog.save()
        return jsonify({"status": "saved", "opics_id": opics_id or None})

    if field not in EDITABLE_PRICE_LIST_FIELDS:
        return jsonify({"error": f"Field {field!r} can't be edited here."}), 400
    try:
        value = float(value)
    except (TypeError, ValueError):
        return jsonify({"error": "Value must be a number."}), 400

    slot["items"][resolved_name][field] = value
    catalog.save()
    return jsonify({"status": "saved"})


@app.route("/api/price-list/link-opics-id", methods=["POST"])
def api_price_list_link_opics_id():
    data = request.json or {}
    slot_key = data.get("slot_key")
    opics_id = (data.get("opics_id") or "").strip()
    item_name = (data.get("item_name") or "").strip()

    if not slot_key or not opics_id:
        return jsonify({"error": "slot_key and opics_id are required."}), 400

    try:
        slot = catalog.get_slot(slot_key)
    except PricingError as e:
        return jsonify({"error": str(e)}), 400

    for name, rec in slot["items"].items():
        if rec.get("opics_id", "").strip() == opics_id:
            return jsonify({
                "status": "exists",
                "item_name": name,
                "opics_id": opics_id,
                "unpriced": bool(rec.get("unpriced")),
            })

    if not item_name:
        item_name = f"Okapics {opics_id}"

    if item_name in slot["items"]:
        slot["items"][item_name]["opics_id"] = opics_id
        catalog.save()
        return jsonify({
            "status": "linked",
            "item_name": item_name,
            "opics_id": opics_id,
            "unpriced": bool(slot["items"][item_name].get("unpriced")),
        })

    slot["items"][item_name] = {**UNPRICED_ITEM_TEMPLATE, "opics_id": opics_id}
    catalog.save()
    return jsonify({
        "status": "created",
        "item_name": item_name,
        "opics_id": opics_id,
        "unpriced": True,
    })


def _try_price_quote(candidate):
    """
    Attempts to resolve a poller candidate as a price-quote request using
    the same deterministic pipeline as the interactive freetext-quote
    endpoint (llm_parser.parse_quote_request + price_job) — a real
    computed price, not a guess. Returns (reply_subject, reply_body,
    grand_total_nis) on a confident match. Returns None if llm_parser
    couldn't confidently match the request to the catalog (ambiguous
    wording, missing size, etc.) — that case falls through to the general
    email_ai judgment in the caller, which already treats "needs a price
    quote" as should_draft=false, so an unparseable quote request still
    gets skipped rather than guessed at.
    """
    text = f"{candidate['subject']}\n\n{candidate['body']}"
    try:
        parsed = llm_parser.parse_quote_request(text, catalog)
    except RuntimeError:
        return None
    if parsed.get("clarification_needed") or not parsed.get("lines"):
        return None
    try:
        result = price_parsed_lines(parsed["lines"], apply_business_rules=True)
    except PricingError:
        return None

    quotes = result["quotes"]
    language = "he" if re.search("[֐-׿]", text) else "en"
    first_name = (candidate.get("from_name") or "").strip().split(" ")[0] or None

    reply_body = quote_reply.draft_reply(
        quotes, client_first_name=first_name, vat_included=False, language=language,
    )
    grand_total = sum(q["quantity_price"] for q in quotes)
    return f"Re: {candidate['subject']}", reply_body, grand_total


def _run_email_poller(interval_seconds):
    """
    Background loop: checks the inbox, asks Claude to decide/draft for each
    new candidate, appends confident drafts to [Gmail]/Drafts, and labels
    every candidate reviewed regardless of the decision (so a skip doesn't
    get re-judged, and re-billed, every single cycle). Never sends email —
    see imap_client.py and email_ai.py for what each half actually does.

    Each cycle also runs a second, independent pass (see email_learning.py):
    scans real staff-sent replies from the last few days, pairs each with
    the client email it was answering, and asks Claude to extract any new
    durable fact worth folding into the studio notes file — so future
    drafting judgment keeps improving from what staff actually say, not
    just from whatever was true when the notes were last hand-edited. Never
    edits the notes file's real sections directly; appends to a clearly
    marked "pending review" section instead (see notes §10).

    Runs as a daemon thread started at import time (not inside `if __name__
    == "__main__"`) so it also starts under gunicorn in production, which
    imports this module directly rather than running that block. Assumes a
    single gunicorn worker (the Procfile doesn't set --workers) — multiple
    workers would each start their own poller and duplicate the polling,
    though not duplicate drafts, since the reviewed-label check is shared
    mailbox state, not per-worker.
    """
    while True:
        try:
            candidates = imap_client.fetch_unanswered_inbox_emails()
            for candidate in candidates:
                try:
                    price_quote = _try_price_quote(candidate)
                    if price_quote:
                        reply_subject, reply_body, grand_total = price_quote
                        language = "he" if re.search("[֐-׿]", reply_body) else "en"
                        reply_html = quote_reply.to_html(reply_body, language)
                        imap_client.append_draft_reply(candidate, reply_subject, reply_body, reply_html=reply_html)
                        labels = [imap_client.PRICE_QUOTE_LABEL]
                        if grand_total > 4000:
                            labels.append(imap_client.PRICE_QUOTE_OVER_4000_LABEL)
                        imap_client.apply_labels(candidate["uid"], labels)
                        print(f"[email-poller] drafted price quote for {candidate['from_email']!r} "
                              f"({candidate['subject']!r}): {grand_total:.0f} NIS, labels={labels}",
                              flush=True)
                    else:
                        decision = email_ai.decide_and_draft_reply(candidate)
                        if decision.get("should_draft") and decision.get("reply_body"):
                            reply_body = decision["reply_body"]
                            language = "he" if re.search("[֐-׿]", reply_body) else "en"
                            reply_html = quote_reply.to_html(reply_body, language)
                            imap_client.append_draft_reply(
                                candidate,
                                decision.get("reply_subject") or f"Re: {candidate['subject']}",
                                reply_body,
                                reply_html=reply_html,
                            )
                            print(f"[email-poller] drafted reply to {candidate['from_email']!r} "
                                  f"({candidate['subject']!r}): {decision.get('reason')}", flush=True)
                        else:
                            print(f"[email-poller] skipped {candidate['from_email']!r} "
                                  f"({candidate['subject']!r}): {decision.get('reason')}", flush=True)
                    imap_client.mark_reviewed(candidate["uid"])
                except Exception as e:
                    # One bad candidate (unparseable email, a transient API
                    # error) shouldn't take down the whole poll cycle or
                    # stop other candidates from being processed. Left
                    # un-labeled on failure so it's retried next cycle
                    # rather than silently skipped forever.
                    print(f"[email-poller] error on candidate {candidate.get('message_id')!r}: {e!r}", flush=True)
        except Exception as e:
            print(f"[email-poller] poll cycle failed: {e!r}", flush=True)

        try:
            pairs = imap_client.fetch_recently_answered_pairs()
            for pair in pairs:
                try:
                    facts = email_learning.extract_learnings(pair["inbound"], pair["reply_body"])
                    if facts:
                        inbound = pair["inbound"]
                        citation = f"{inbound.get('subject') or 'no subject'}, {inbound.get('date')}"
                        email_learning.append_learnings(facts, citation)
                        email_ai.invalidate_notes_cache()
                        print(f"[email-learner] +{len(facts)} learning(s) from {inbound.get('subject')!r}: {facts}", flush=True)
                    imap_client.mark_learned(pair["reply_uid"])
                except Exception as e:
                    print(f"[email-learner] error on reply {pair.get('reply_uid')!r}: {e!r}", flush=True)
        except Exception as e:
            print(f"[email-learner] scan failed: {e!r}", flush=True)

        time.sleep(interval_seconds)


if os.environ.get("EMAIL_POLLER_ENABLED", "").lower() == "true":
    _poll_minutes = float(os.environ.get("EMAIL_POLLER_INTERVAL_MINUTES", "10"))
    threading.Thread(target=_run_email_poller, args=(_poll_minutes * 60,), daemon=True).start()
    print(f"[email-poller] started, polling every {_poll_minutes} minute(s)", flush=True)


def _run_daily_report_scheduler(recipient, hour, minute):
    """
    Background loop: sleeps until the next `hour:minute` in Asia/Jerusalem,
    sends that day's learning-summary .docx (see daily_report.py), then
    repeats. Computing the next-fire time fresh each iteration (rather than
    a fixed sleep(24h)) keeps this correct across DST transitions. Runs as
    a daemon thread started at import time, same pattern as the email
    poller above — see studio_operations_and_communication_notes.md §11.
    """
    from datetime import datetime, timedelta

    while True:
        now = datetime.now(daily_report.REPORT_TIMEZONE)
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        time.sleep((target - now).total_seconds())

        # Studio is closed Fri/Sat (Israeli work week is Sun-Thu, see notes
        # §3) — skip the scheduled send those days. date.weekday(): Mon=0
        # ... Fri=4, Sat=5, Sun=6. The manual /api/daily-report/send-now
        # trigger is deliberately NOT restricted by this — it's an explicit
        # on-demand action, not the automatic schedule.
        if target.weekday() in (4, 5):
            print(f"[daily-report] skipped {target.date().isoformat()} (Fri/Sat, studio closed)", flush=True)
            continue

        try:
            daily_report.send_daily_report(target.date(), recipient)
            print(f"[daily-report] sent for {target.date().isoformat()} to {recipient!r}", flush=True)
        except Exception as e:
            print(f"[daily-report] failed for {target.date().isoformat()}: {e!r}", flush=True)


if os.environ.get("DAILY_REPORT_ENABLED", "").lower() == "true":
    _report_recipient = os.environ.get("DAILY_REPORT_RECIPIENT", "rea@theprinthouse.co.il")
    _report_hour, _report_minute = (int(x) for x in os.environ.get("DAILY_REPORT_TIME", "18:00").split(":"))
    threading.Thread(
        target=_run_daily_report_scheduler,
        args=(_report_recipient, _report_hour, _report_minute),
        daemon=True,
    ).start()
    print(f"[daily-report] started, sending to {_report_recipient!r} at {_report_hour:02d}:{_report_minute:02d} Asia/Jerusalem", flush=True)


class _ScriptNameMiddleware:
    """Honor reverse-proxy subpath via X-Script-Name (nginx at /pricing-calculator)."""

    def __init__(self, app, default_root=""):
        self.app = app
        self.default_root = default_root.rstrip("/")

    def __call__(self, environ, start_response):
        script_name = environ.get("HTTP_X_SCRIPT_NAME") or self.default_root
        if script_name:
            environ["SCRIPT_NAME"] = script_name
        return self.app(environ, start_response)


_application_root = os.environ.get("APPLICATION_ROOT", "").rstrip("/")
if _application_root:
    app.wsgi_app = _ScriptNameMiddleware(app.wsgi_app, _application_root)


if __name__ == "__main__":
    # host="0.0.0.0" makes this reachable from other computers on the same
    # network (not just this machine). debug=False is intentional here:
    # Flask's debug mode exposes an interactive, code-executing debugger
    # on any error page, which must never be reachable by anyone but the
    # developer on localhost.
    app.run(host="0.0.0.0", port=5050, debug=False)

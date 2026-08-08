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
import secrets
import shutil
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

import business_rules
import llm_parser
import monday_client
from pricing_engine import JobComponentRequest, PricingCatalog, PricingError, price_job

load_dotenv(Path(__file__).resolve().parent / ".env")

APP_PASSWORD = os.environ.get("APP_PASSWORD")

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


@app.before_request
def require_login():
    if not APP_PASSWORD:
        return None  # no password configured -> auth disabled
    if request.endpoint in ("login", "static"):
        return None
    if not session.get("authenticated"):
        return redirect(url_for("login", next=request.path))
    return None


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


def line_result_to_dict(result):
    return {
        "lines": [
            {
                "slot_key": l.slot_key,
                "item_name": l.item_name,
                "quantity": l.quantity,
                "material_price": round(l.material_price, 2),
                "work_price": round(l.work_price, 2),
                "line_total": round(l.line_total, 2),
                "scales_with_quantity": l.scales_with_quantity,
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
            JobComponentRequest(slot_key, data["item_name"], data["quantity"])
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
    return jsonify({
        "matches": [
            {**order, "reply_text": monday_client.format_status_reply_he(order)}
            for order in orders
        ]
    })


@app.route("/api/price-list")
def api_price_list():
    return jsonify(list(catalog.slots.values()))


# Every cost-driver field on an item is directly editable in the Price
# List table.
EDITABLE_PRICE_LIST_FIELDS = {
    "fixed_material_cost", "var_material_cost", "material_indirect", "material_risk", "material_profit",
    "fixed_effort_cost", "var_effort_cost", "min_effort_cost", "effort_indirect", "effort_risk", "effort_profit",
}


@app.route("/api/price-list/update-item", methods=["POST"])
def api_price_list_update_item():
    data = request.json or {}
    slot_key = data.get("slot_key")
    item_name = data.get("item_name")
    field = data.get("field")
    value = data.get("value")

    if field not in EDITABLE_PRICE_LIST_FIELDS:
        return jsonify({"error": f"Field {field!r} can't be edited here."}), 400
    try:
        value = float(value)
    except (TypeError, ValueError):
        return jsonify({"error": "Value must be a number."}), 400

    try:
        slot, resolved_name, _item = catalog.find_item(slot_key, item_name)
    except PricingError as e:
        return jsonify({"error": str(e)}), 400

    slot["items"][resolved_name][field] = value
    catalog.save()
    return jsonify({"status": "saved"})


if __name__ == "__main__":
    # host="0.0.0.0" makes this reachable from other computers on the same
    # network (not just this machine). debug=False is intentional here:
    # Flask's debug mode exposes an interactive, code-executing debugger
    # on any error page, which must never be reachable by anyone but the
    # developer on localhost.
    app.run(host="0.0.0.0", port=5050, debug=False)

"""Unpriced catalog items return null line totals and can be activated via Price List."""
import json
import tempfile
import unittest
from pathlib import Path

from pricing_engine import (
    JobComponentRequest,
    PricingCatalog,
    price_job,
)
import app as flask_app


SAMPLE = {
    "source_file": "test.xlsm",
    "salary_per_hour": 90,
    "vat_rate": 0.18,
    "excluded_features": [],
    "presets": [],
    "slots": [
        {
            "key": "row27_paint",
            "row": 27,
            "kind": "dropdown",
            "label": "Paint",
            "size_mode": "perimeter",
            "scales_with_quantity": True,
            "default_item": "solid",
            "items": {
                "No Paint": {
                    "fixed_material_cost": 0,
                    "var_material_cost": 0,
                    "material_indirect": 0.5,
                    "material_risk": 0.3,
                    "material_profit": 0.45,
                    "var_effort_cost": 0,
                    "fixed_effort_cost": 0,
                    "min_effort_cost": 0,
                    "effort_indirect": 0.5,
                    "effort_risk": 0.45,
                    "effort_profit": 0.45,
                },
                "solid": {
                    "fixed_material_cost": 10,
                    "var_material_cost": 5,
                    "material_indirect": 0,
                    "material_risk": 0,
                    "material_profit": 0,
                    "var_effort_cost": 0,
                    "fixed_effort_cost": 20,
                    "min_effort_cost": 0,
                    "effort_indirect": 0,
                    "effort_risk": 0,
                    "effort_profit": 0,
                },
                "Mystery Finish": {
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
                },
            },
        },
        {
            "key": "row24_glasses",
            "row": 24,
            "kind": "dropdown",
            "label": "Glasses",
            "size_mode": "area",
            "scales_with_quantity": True,
            "default_item": "Regular 2mm",
            "items": {
                "Regular 2mm": {
                    "fixed_material_cost": 0,
                    "var_material_cost": 100,
                    "material_indirect": 0,
                    "material_risk": 0,
                    "material_profit": 0,
                    "var_effort_cost": 0,
                    "fixed_effort_cost": 0,
                    "min_effort_cost": 0,
                    "effort_indirect": 0,
                    "effort_risk": 0,
                    "effort_profit": 0,
                },
            },
        },
    ],
}


class UnpricedEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(SAMPLE, self.tmp)
        self.tmp.close()
        self.catalog = PricingCatalog(self.tmp.name)

    def tearDown(self):
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_unpriced_line_total_is_none_and_excluded_from_totals(self):
        result = price_job(
            self.catalog,
            [
                JobComponentRequest("row24_glasses", "Regular 2mm"),
                JobComponentRequest("row27_paint", "Mystery Finish"),
            ],
            height_cm=50,
            width_cm=70,
        )
        glass = next(l for l in result.lines if l.item_name == "Regular 2mm")
        mystery = next(l for l in result.lines if l.item_name == "Mystery Finish")
        self.assertFalse(glass.unpriced)
        self.assertIsNotNone(glass.line_total)
        self.assertGreater(glass.line_total, 0)
        self.assertTrue(mystery.unpriced)
        self.assertIsNone(mystery.line_total)
        self.assertEqual(result.quantity_price, glass.line_total)

    def test_zero_cost_priced_item_still_zero(self):
        result = price_job(
            self.catalog,
            [JobComponentRequest("row27_paint", "No Paint")],
            height_cm=50,
            width_cm=70,
        )
        line = result.lines[0]
        self.assertFalse(line.unpriced)
        self.assertEqual(line.line_total, 0.0)


class UnpricedApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(SAMPLE, self.tmp)
        self.tmp.close()
        self._prev_catalog = flask_app.catalog
        self._prev_password = flask_app.APP_PASSWORD
        self._prev_api_key = flask_app.PRICING_CALC_API_KEY
        flask_app.catalog = PricingCatalog(self.tmp.name)
        flask_app.APP_PASSWORD = None
        flask_app.PRICING_CALC_API_KEY = None
        flask_app.app.config["TESTING"] = True
        self.client = flask_app.app.test_client()

    def tearDown(self):
        flask_app.catalog = self._prev_catalog
        flask_app.APP_PASSWORD = self._prev_password
        flask_app.PRICING_CALC_API_KEY = self._prev_api_key
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_structured_quote_returns_null_for_unpriced(self):
        res = self.client.post(
            "/api/quote/structured",
            json={
                "lines": [
                    {
                        "height_cm": 50,
                        "width_cm": 70,
                        "order_quantity": 1,
                        "components": [
                            {"slot_key": "row24_glasses", "item_name": "Regular 2mm"},
                            {"slot_key": "row27_paint", "item_name": "Mystery Finish"},
                        ],
                    }
                ]
            },
        )
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        payload = res.get_json()
        quote = payload["quotes"][0]
        mystery = next(l for l in quote["lines"] if l["item_name"] == "Mystery Finish")
        glass = next(l for l in quote["lines"] if l["item_name"] == "Regular 2mm")
        self.assertTrue(mystery["unpriced"])
        self.assertIsNone(mystery["line_total"])
        self.assertFalse(glass.get("unpriced"))
        self.assertIsNotNone(glass["line_total"])
        self.assertEqual(quote["quantity_price"], glass["line_total"])

    def test_enable_pricing_clears_unpriced_flag(self):
        res = self.client.post(
            "/api/price-list/update-item",
            json={
                "slot_key": "row27_paint",
                "item_name": "Mystery Finish",
                "field": "unpriced",
                "value": False,
            },
        )
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        self.assertFalse(res.get_json()["unpriced"])
        item = flask_app.catalog.slots["row27_paint"]["items"]["Mystery Finish"]
        self.assertNotIn("unpriced", item)

        quote_res = self.client.post(
            "/api/quote/structured",
            json={
                "lines": [
                    {
                        "height_cm": 50,
                        "width_cm": 70,
                        "components": [{"slot_key": "row27_paint", "item_name": "Mystery Finish"}],
                    }
                ]
            },
        )
        line = quote_res.get_json()["quotes"][0]["lines"][0]
        self.assertFalse(line.get("unpriced"))
        self.assertEqual(line["line_total"], 0.0)


if __name__ == "__main__":
    unittest.main()

"""Okapics ID linking and quote lookup."""
import json
import tempfile
import unittest
from pathlib import Path

from pricing_engine import JobComponentRequest, PricingCatalog, price_job
import app as flask_app


PROFILE_SLOT = {
    "key": "row23_profile_preset",
    "row": 23,
    "kind": "dropdown",
    "label": "Profile Preset",
    "size_mode": "perimeter",
    "scales_with_quantity": True,
    "default_item": "Box 1.5/4 simple",
    "items": {
        "Box 1.5/4 simple": {
            "fixed_material_cost": 10,
            "var_material_cost": 5,
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
}

SAMPLE = {
    "source_file": "test.xlsm",
    "salary_per_hour": 90,
    "vat_rate": 0.18,
    "excluded_features": [],
    "presets": [],
    "slots": [PROFILE_SLOT],
}


class OpicsIdTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.write(json.dumps(SAMPLE).encode("utf-8"))
        self.tmp.close()
        self.catalog = PricingCatalog(self.tmp.name)

    def tearDown(self):
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_find_item_by_opics_id(self):
        slot = self.catalog.slots["row23_profile_preset"]
        slot["items"]["Alum linked"] = {
            **slot["items"]["Box 1.5/4 simple"],
            "opics_id": "0.7/4.0 -12 white 027",
            "unpriced": True,
        }

        _, name, item = self.catalog.find_item_by_opics_id(
            "row23_profile_preset", "0.7/4.0 -12 white 027"
        )
        self.assertEqual(name, "Alum linked")
        self.assertTrue(item["unpriced"])

    def test_price_job_resolves_opics_id_component(self):
        slot = self.catalog.slots["row23_profile_preset"]
        slot["items"]["Alum linked"] = {
            **slot["items"]["Box 1.5/4 simple"],
            "opics_id": "0.7/4.0 -12 white 027",
        }

        result = price_job(
            self.catalog,
            [JobComponentRequest("row23_profile_preset", opics_id="0.7/4.0 -12 white 027")],
            height_cm=50,
            width_cm=40,
        )
        line = result.lines[0]
        self.assertEqual(line.item_name, "Alum linked")
        self.assertFalse(line.unpriced)
        self.assertGreater(line.line_total, 0)

class OpicsIdApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.write(json.dumps(SAMPLE).encode("utf-8"))
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

    def test_link_opics_id_api_creates_unpriced_stub(self):
        res = self.client.post(
            "/api/price-list/link-opics-id",
            json={
                "slot_key": "row23_profile_preset",
                "opics_id": "0.7/4.0 -12 white 027",
            },
        )
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        data = res.get_json()
        self.assertEqual(data["status"], "created")
        self.assertTrue(data["unpriced"])
        self.assertIn(data["item_name"], flask_app.catalog.slots["row23_profile_preset"]["items"])

        res2 = self.client.post(
            "/api/price-list/link-opics-id",
            json={
                "slot_key": "row23_profile_preset",
                "opics_id": "0.7/4.0 -12 white 027",
            },
        )
        self.assertEqual(res2.get_json()["status"], "exists")

    def test_structured_quote_accepts_opics_id(self):
        slot = flask_app.catalog.slots["row23_profile_preset"]
        slot["items"]["Alum linked"] = {
            **slot["items"]["Box 1.5/4 simple"],
            "opics_id": "0.7/4.0 -12 white 027",
        }

        res = self.client.post(
            "/api/quote/structured",
            json={
                "lines": [{
                    "height_cm": 50,
                    "width_cm": 40,
                    "order_quantity": 1,
                    "components": [{
                        "slot_key": "row23_profile_preset",
                        "opics_id": "0.7/4.0 -12 white 027",
                        "quantity": 1,
                    }],
                }]
            },
        )
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        quote = res.get_json()["quotes"][0]
        line = quote["lines"][0]
        self.assertEqual(line["item_name"], "Alum linked")
        self.assertIsNotNone(line["line_total"])


if __name__ == "__main__":
    unittest.main()

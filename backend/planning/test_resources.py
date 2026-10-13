from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APITestCase
from .engine import calculate
from .models import SolarRun, ScenarioRun
from .serializers import PlanningInputs, json_values
from .tests import snapshot, planting


def water(**overrides):
    return {"storage_capacity_m3": 100, "opening_storage_m3": 50, "weekly_inflow_m3": 10,
        "weekly_evaporation_m3": 2, "weekly_pumping_limit_m3": 20, "irrigation_efficiency": "0.8", **overrides}


def cohort(**overrides):
    return planting(sowing_date="2026-01-01", daily_water_l_per_m2=2, sowing_hours_per_m2="0.1",
        maintenance_hours_per_m2_week="0.05", harvest_hours_per_kg="0.1", **overrides)


class ResourceTests(TestCase):
    def run_plan(self, **overrides):
        return calculate(snapshot(beds=[{"id": "bed1", "area_m2": 100}], plantings=[cohort()], **overrides))

    def test_water_conserves_mass_and_accounts_for_efficiency(self):
        result = self.run_plan(resources={"water": water()})
        row = result["weeks"][0]["resources"]["water"]
        self.assertEqual(row["crop_demand_m3"], "1.4000")
        self.assertEqual(row["withdrawal_m3"], "1.7500")
        self.assertEqual(row["closing_storage_m3"], "56.2500")
        for week in result["weeks"]:
            r = week["resources"]["water"]
            D = Decimal
            self.assertEqual(D(r["opening_storage_m3"]) + D(r["inflow_m3"]) - D(r["overflow_m3"]) - D(r["evaporation_m3"]) - D(r["withdrawal_m3"]), D(r["closing_storage_m3"]))
        self.assertEqual(result["summary"]["water_deficit_weeks"], 0)

    def test_pumping_and_storage_shortfalls_are_constraints_not_fake_yield_penalties(self):
        result = self.run_plan(resources={"water": water(opening_storage_m3=0, weekly_inflow_m3=0)})
        self.assertEqual(result["summary"]["water_deficit_weeks"], 4)
        self.assertFalse(result["summary"]["resource_constraints_met"])
        self.assertEqual(result["weeks"][0]["gross_kg"], "125.000")
        pumping = self.run_plan(resources={"water": water(weekly_pumping_limit_m3=1)})
        self.assertEqual(pumping["weeks"][0]["resources"]["water"]["shortfall_m3"], "0.6000")

    def test_overflow_evaporation_and_seasonal_override(self):
        result = self.run_plan(resources={"water": water(opening_storage_m3=100,
            weekly_overrides=[{"week": 1, "inflow_m3": 20, "evaporation_m3": 200}])})
        row = result["weeks"][0]["resources"]["water"]
        self.assertEqual(row["overflow_m3"], "20.0000")
        self.assertEqual(row["evaporation_m3"], "100.0000")
        self.assertEqual(row["closing_storage_m3"], "0.0000")

    def test_labour_includes_sowing_gross_harvest_and_delivered_packing(self):
        result = self.run_plan(resources={"labour": {"available_hours_per_week": 10,
            "fixed_hours_per_week": 1, "packing_hours_per_delivered_kg": "0.1", "delivery_hours_per_week": 2}})
        row = result["weeks"][0]["resources"]["labour"]
        # 10 sowing + 5 maintenance + 12.5 gross harvest + 10 packing + 1 fixed + 2 delivery.
        self.assertEqual(row["required_hours"], "40.5000")
        self.assertEqual(row["shortfall_hours"], "30.5000")
        self.assertEqual(result["summary"]["labour_deficit_weeks"], 4)

    def test_unknown_crop_requirements_remain_unknown(self):
        result = calculate(snapshot(beds=[{"id": "bed1", "area_m2": 100}], plantings=[planting()],
            resources={"water": water(), "labour": {"available_hours_per_week": 100}}))
        row = result["weeks"][0]["resources"]
        self.assertIsNone(row["water"]["capacity_met"])
        self.assertIsNone(row["labour"]["capacity_met"])
        self.assertIsNone(result["summary"]["resource_constraints_met"])
        self.assertEqual(row["water"]["unknown_plantings"], ["p1"])

    def test_invalid_storage_efficiency_and_duplicate_overrides(self):
        for budget in [water(opening_storage_m3=101), water(irrigation_efficiency=0),
            water(weekly_overrides=[{"week": 1}, {"week": 1}])]:
            serializer = PlanningInputs(data={"start_date": "2026-01-01", "resources": {"water": budget}})
            self.assertFalse(serializer.is_valid())


class LightLinkTests(APITestCase):
    def setUp(self):
        self.farm = self.client.post("/api/farms/", {"name": "Linked farm", "area_acres": 2}, format="json").data["id"]

    def study(self, values, start="2026-01-01", **site_overrides):
        day = date.fromisoformat(start)
        return SolarRun.objects.create(engine_version="test-fixture", inputs={"latitude": 18.52, "longitude": 73.86, "timezone": "Asia/Kolkata", **site_overrides},
            result={"input_sha256": "synthetic", "radiation_source": "Synthetic DLI test fixture",
                "points": [{"id": "position", "daily": [{"date": (day + timedelta(days=i)).isoformat(), "dli_mol_m2_day": value} for i, value in enumerate(values)]}]})

    def scenario(self, studies, resources=None, **curve_overrides):
        return self.client.post("/api/scenarios/", {"farm": self.farm, "name": "Light-linked", "inputs": {
            "start_date": "2026-01-01", "resources": resources, "beds": [{"id": "bed1", "area_m2": 100}],
            "plantings": [cohort(harvest_weeks=1, light_response={"solar_runs": [str(s.id) for s in studies], "point_id": "position",
                "minimum_dli": 5, "optimum_dli": 25, "source_note": "Unvalidated linear curve for test", **curve_overrides})]}}, format="json")

    def test_light_limits_yield_once_and_snapshots_are_reproducible(self):
        study = self.study([15] * 7)
        scenario = self.scenario([study])
        self.assertEqual(scenario.status_code, 201, scenario.data)
        run = self.client.post("/api/scenario-runs/", {"scenario": scenario.data["id"]}, format="json")
        self.assertEqual(run.status_code, 201, run.data)
        self.assertEqual(run.data["result"]["light_adjustments"]["p1"], "0.500000")
        self.assertEqual(run.data["result"]["weeks"][0]["gross_kg"], "250.000")
        self.assertEqual(run.data["result"]["weeks"][0]["groups"]["leafy"]["marketable_kg"], "200.000")
        saved = ScenarioRun.objects.get(pk=run.data["id"])
        self.assertEqual(calculate(saved.assumptions_snapshot), saved.result)
        self.assertIn(str(study.id), saved.assumptions_snapshot["light_studies"])

    def test_response_caps_at_one_and_daily_thresholds_are_not_applied_to_average_dli(self):
        for values, expected in [([100] * 7, "1.000000"), ([0] * 7, "0.000000"), ([0, 25, 0, 25, 0, 25, 25], "0.571429")]:
            scenario = self.scenario([self.study(values)])
            run = self.client.post("/api/scenario-runs/", {"scenario": scenario.data["id"]}, format="json")
            self.assertEqual(run.data["result"]["light_adjustments"]["p1"], expected)

    def test_missing_dates_position_and_invalid_response_are_rejected(self):
        study = self.study([15])
        self.assertEqual(self.scenario([study]).status_code, 400)
        full = self.study([15] * 7)
        self.assertEqual(self.scenario([full], point_id="missing").status_code, 400)
        self.assertEqual(self.scenario([full], optimum_dli=5).status_code, 400)

    def test_conflicting_dates_and_different_sites_are_rejected(self):
        self.assertEqual(self.scenario([self.study([15] * 7), self.study([16] * 7)]).status_code, 400)
        self.assertEqual(self.scenario([self.study([15] * 4), self.study([15] * 3, start="2026-01-05", latitude=-35)]).status_code, 400)

    def test_multiple_studies_cover_distinct_periods(self):
        scenario = self.scenario([self.study([15] * 4), self.study([15] * 3, start="2026-01-05")])
        self.assertEqual(scenario.status_code, 201, scenario.data)

    def test_linked_light_resource_constraints_and_export_work_together(self):
        import csv
        import io
        scenario = self.scenario([self.study([15] * 7)], resources={"water": water(opening_storage_m3=0, weekly_inflow_m3=0),
            "labour": {"available_hours_per_week": 0}})
        run = self.client.post("/api/scenario-runs/", {"scenario": scenario.data["id"]}, format="json")
        self.assertEqual(run.status_code, 201, run.data)
        self.assertFalse(run.data["result"]["summary"]["resource_constraints_met"])
        self.assertEqual(run.data["result"]["summary"]["water_deficit_weeks"], 1)
        exported = self.client.get(f'/api/scenario-runs/{run.data["id"]}/resource-export/')
        self.assertEqual(exported.status_code, 200)
        rows = list(csv.DictReader(io.StringIO(exported.content.decode())))
        self.assertEqual(len(rows), 104)
        self.assertEqual(rows[0]["water_check"], "exceeded")
        self.assertEqual(rows[0]["labour_check"], "exceeded")
        self.assertEqual(rows[0]["water_shortfall_m3"], "1.4000")

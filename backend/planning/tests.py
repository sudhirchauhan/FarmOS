from copy import deepcopy
from datetime import date
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APITestCase
from .engine import calculate
from .models import ScenarioRun
from .serializers import PlanningInputs, json_values


def snapshot(**overrides):
    serializer = PlanningInputs(data={"start_date": "2026-01-01", **overrides})
    serializer.is_valid(raise_exception=True)
    return {"farm": {"area_acres": "2"}, "inputs": json_values(serializer.validated_data)}


def planting(**overrides):
    return {"id": "p1", "bed_id": "bed1", "crop": "Spinach", "crop_group": "leafy",
        "area_m2": "100", "sowing_date": "2025-12-01", "harvest_start": "2026-01-01",
        "harvest_weeks": 4, "gross_yield_kg_per_m2": "5", **overrides}


class CalculationTests(TestCase):
    def test_reference_arithmetic_and_missing_production(self):
        result = calculate(snapshot())
        self.assertEqual(result["baseline"]["annual_delivered_demand_kg"], "20800.000")
        self.assertEqual(result["baseline"]["annual_gross_target_kg"], "26000.000")
        self.assertEqual(result["baseline"]["annual_subscription_revenue_inr"], "3300000.00")
        self.assertEqual(result["summary"]["delivered_kg"], "0.000")
        self.assertFalse(result["summary"]["service_target_met"])
        self.assertEqual(len(result["weeks"]), 104)
        self.assertEqual(result["summary"]["agronomic_feasibility"], "not_assessed")

    def test_zero_customers_and_paid_collections_are_separate(self):
        result = calculate(snapshot(households=0))
        self.assertEqual(result["summary"]["revenue_accrual_inr"], "0.00")
        self.assertEqual(result["summary"]["collections_inr"], "0.00")
        self.assertIsNone(result["summary"]["service_fraction"])
        unpaid = calculate(snapshot(paid_enrollment_fraction="0"))
        self.assertEqual(unpaid["baseline"]["annual_subscription_revenue_inr"], "3300000.00")
        self.assertEqual(unpaid["summary"]["collections_inr"], "0.00")

    def test_loss_applied_once_and_group_deficits(self):
        result = calculate(snapshot(beds=[{"id": "bed1", "area_m2": "100"}], plantings=[planting()]))
        week = result["weeks"][0]
        self.assertEqual(week["gross_kg"], "125.000")
        self.assertEqual(week["groups"]["leafy"]["marketable_kg"], "100.000")
        self.assertEqual(week["delivered_kg"], "100.000")
        self.assertEqual(week["shortfall_kg"], "300.000")
        self.assertEqual(result["weeks"][4]["gross_kg"], "0.000")

    def test_unaligned_harvest_distributes_by_day(self):
        result = calculate(snapshot(beds=[{"id": "bed1", "area_m2": "100"}],
            plantings=[planting(harvest_start="2026-01-04", harvest_weeks=1, gross_yield_kg_per_m2="0.7")]))
        self.assertEqual(result["weeks"][0]["gross_kg"], "40.000")
        self.assertEqual(result["weeks"][1]["gross_kg"], "30.000")
        self.assertEqual(result["summary"]["gross_kg"], "70.000")

    def test_price_does_not_change_harvest(self):
        inputs = dict(beds=[{"id": "bed1", "area_m2": "100"}], plantings=[planting()])
        lower = calculate(snapshot(monthly_price_inr=1000, **inputs))
        higher = calculate(snapshot(monthly_price_inr=2000, **inputs))
        self.assertEqual(lower["summary"]["gross_kg"], higher["summary"]["gross_kg"])
        self.assertNotEqual(lower["summary"]["revenue_accrual_inr"], higher["summary"]["revenue_accrual_inr"])

    def test_cash_reconciles_and_family_labour_is_valued(self):
        result = calculate(snapshot(initial_cash_inr=0, initial_capex_inr=500000,
            monthly_fixed_opex_inr=300000, weekly_family_labour_hours=20, family_labour_hourly_value_inr=100))
        summary = result["summary"]
        expected = Decimal(summary["collections_inr"]) - Decimal(summary["opex_inr"]) - Decimal(summary["capex_inr"])
        self.assertEqual(Decimal(summary["closing_cash_inr"]), expected)
        self.assertLess(Decimal(summary["minimum_cash_inr"]), 0)
        self.assertEqual(Decimal(summary["operating_surplus_inr"]) - Decimal(summary["economic_surplus_inr"]), Decimal(208000))

    def test_profitable_subscription_does_not_hide_insufficient_initial_cash(self):
        result = calculate(snapshot(start_date="2026-01-02", initial_cash_inr=0, initial_capex_inr=500000))
        self.assertGreater(Decimal(result["summary"]["operating_surplus_inr"]), 0)
        self.assertEqual(result["weeks"][0]["collections_inr"], "0.00")
        self.assertEqual(result["summary"]["additional_funding_required_inr"], "500000.00")

    def test_deterministic_results_and_fingerprint(self):
        inputs = snapshot()
        self.assertEqual(calculate(inputs), calculate(deepcopy(inputs)))
        changed = snapshot(monthly_price_inr=6000)
        self.assertNotEqual(calculate(inputs)["input_sha256"], calculate(changed)["input_sha256"])

    def test_annual_surplus_is_not_weekly_feasibility(self):
        result = calculate(snapshot(beds=[{"id": "bed1", "area_m2": "100"}],
            plantings=[planting(gross_yield_kg_per_m2=1000)]))
        self.assertGreater(Decimal(result["summary"]["gross_kg"]), Decimal(result["summary"]["demand_kg"]))
        self.assertFalse(result["summary"]["service_target_met"])

    def test_all_categories_can_fulfill_weekly_basket_without_double_sales(self):
        cohorts = [planting(id=group, crop=group, crop_group=group, area_m2=200,
            harvest_weeks=104, gross_yield_kg_per_m2=65) for group in ("leafy", "fruiting", "roots", "legumes")]
        result = calculate(snapshot(beds=[{"id": "bed1", "area_m2": 800}], plantings=cohorts))
        self.assertEqual(result["summary"]["fully_supplied_weeks"], 104)
        self.assertTrue(result["summary"]["service_target_met"])
        self.assertEqual(result["summary"]["delivered_kg"], "41600.000")
        self.assertEqual(result["summary"]["gross_kg"], "52000.000")
        self.assertEqual(result["summary"]["agronomic_feasibility"], "not_assessed")


class InputTests(TestCase):
    def test_overbooking_and_back_to_back_cycles(self):
        inputs = {"start_date": "2026-01-01", "beds": [{"id": "bed1", "area_m2": 100}],
            "plantings": [planting(), planting(id="p2")]}
        serializer = PlanningInputs(data=inputs)
        self.assertFalse(serializer.is_valid())
        inputs["plantings"][1] = planting(id="p2", sowing_date="2026-01-29", harvest_start="2026-02-01")
        serializer = PlanningInputs(data=inputs)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_unknown_fields_invalid_shares_and_loss(self):
        for extra in [{"combined_loss_fraction": "1"}, {"households": -1}, {"solar_validated": True},
            {"basket_shares": {"leafy": 1, "fruiting": 1, "roots": 0, "legumes": 0}}]:
            serializer = PlanningInputs(data={"start_date": "2026-01-01", **extra})
            self.assertFalse(serializer.is_valid())

    def test_claimed_evidence_needs_source(self):
        serializer = PlanningInputs(data={"start_date": "2026-01-01", "beds": [{"id": "bed1", "area_m2": 100}],
            "plantings": [planting(evidence="measured")]})
        self.assertFalse(serializer.is_valid())

    def test_calendar_overflow_is_a_validation_error(self):
        for data in [{"start_date": "9999-12-31"},
            {"start_date": "2026-01-01", "beds": [{"id": "bed1", "area_m2": 100}],
             "plantings": [planting(sowing_date="9999-01-01", harvest_start="9999-12-31")]}]:
            self.assertFalse(PlanningInputs(data=data).is_valid())


class PlanningAPITests(APITestCase):
    def setUp(self):
        response = self.client.post("/api/farms/", {"name": "Test farm", "area_acres": "2"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.farm = response.data["id"]

    def scenario(self, **overrides):
        return self.client.post("/api/scenarios/", {"farm": self.farm, "name": "Base", "inputs": {
            "start_date": "2026-01-01", **overrides}}, format="json")

    def test_create_run_clone_compare_export_and_immutable_snapshot(self):
        created = self.scenario()
        self.assertEqual(created.status_code, 201, created.data)
        scenario = created.data["id"]
        run = self.client.post("/api/scenario-runs/", {"scenario": scenario}, format="json")
        self.assertEqual(run.status_code, 201, run.data)
        before = deepcopy(run.data["assumptions_snapshot"])
        revised = self.client.put(f"/api/scenarios/{scenario}/", {"farm": self.farm, "name": "Higher price",
            "inputs": {"start_date": "2026-01-01", "monthly_price_inr": "6000"}}, format="json")
        self.assertEqual(revised.status_code, 200, revised.data)
        self.assertEqual(revised.data["revision"], 2)
        self.assertEqual(ScenarioRun.objects.get(pk=run.data["id"]).assumptions_snapshot, before)
        run2 = self.client.post("/api/scenario-runs/", {"scenario": scenario}, format="json")
        compare = self.client.get("/api/scenario-runs/comparison/", {"run": [run.data["id"], run2.data["id"]]})
        self.assertEqual(compare.status_code, 200, compare.data)
        self.assertEqual(compare.data["runs"][1]["delta_from_reference"]["delivered_kg"], "0.000")
        cloned = self.client.post(f"/api/scenarios/{scenario}/clone/", {"name": "Conservative"}, format="json")
        self.assertEqual(cloned.status_code, 201)
        self.assertEqual(cloned.data["revision"], 1)
        exported = self.client.get(f'/api/scenario-runs/{run.data["id"]}/weekly-export/')
        self.assertEqual(exported.status_code, 200)
        self.assertEqual(len(exported.content.decode().splitlines()), 105)
        self.assertEqual(self.client.patch(f'/api/scenario-runs/{run.data["id"]}/', {}, format="json").status_code, 405)

    def test_land_footprint_rejected(self):
        response = self.scenario(beds=[{"id": "too_big", "area_m2": 10000}])
        self.assertEqual(response.status_code, 400)

    def test_input_defaults_are_persisted_and_runs_repeat(self):
        scenario = self.scenario()
        self.assertEqual(scenario.data["inputs"]["combined_loss_fraction"], "0.2000")
        first = self.client.post("/api/scenario-runs/", {"scenario": scenario.data["id"]}, format="json")
        second = self.client.post("/api/scenario-runs/", {"scenario": scenario.data["id"]}, format="json")
        self.assertEqual(first.data["result"], second.data["result"])

    def test_invalid_comparison_and_missing_scenario(self):
        self.assertEqual(self.client.get("/api/scenario-runs/comparison/?run=invalid&run=missing").status_code, 400)
        self.assertEqual(self.client.post("/api/scenario-runs/", {"scenario": "not-a-uuid"}, format="json").status_code, 400)
        self.assertEqual(self.client.put("/api/scenarios/not-a-uuid/", {}, format="json").status_code, 404)

from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APITestCase
from .engine import calculate
from .serializers import PlanningInputs
from .tests import snapshot, planting


def lot(**overrides):
    return {"id": "batch", "name": "Measured compost fixture", "source_kind": "user_estimate", "source_note": "Synthetic test composition",
        "available_week": 1, "dry_mass_kg": 100, "n_g_per_dry_kg": 10, "p_g_per_dry_kg": 5, "k_g_per_dry_kg": 20,
        "n_available_fraction": "0.25", "p_available_fraction": "0.4", "k_available_fraction": "0.5", **overrides}


def budget(**overrides):
    return {"opening_n_available_kg": 0, "opening_p_available_kg": 0, "opening_k_available_kg": 0,
        "opening_source_note": "Explicit zero available pool test", "lots": [lot()],
        "allocations": [{"lot_id": "batch", "week": 1, "purpose": "compost", "dry_mass_kg": 100}], **overrides}


def crop(**overrides):
    return planting(**{"sowing_date": "2026-01-01", "n_removal_g_per_gross_kg": 1, "p_removal_g_per_gross_kg": 0,
        "k_removal_g_per_gross_kg": 0, **overrides})


class NutrientTests(TestCase):
    def plan(self, config=None, cohort=None):
        return calculate(snapshot(beds=[{"id": "bed1", "area_m2": 100}], plantings=[cohort or crop()],
            resources={"nutrients": config or budget()}))

    def test_availability_is_not_total_nutrient_content_and_balance_reconciles(self):
        result = self.plan()
        first = result["weeks"][0]["resources"]["nutrients"]["elements"]["n"]
        self.assertEqual(first["total_compost_content_kg"], "1.0000")
        self.assertEqual(first["available_input_kg"], "0.2500")
        self.assertEqual(first["required_removal_kg"], "0.1250")
        self.assertEqual(first["closing_available_kg"], "0.1250")
        self.assertEqual(result["summary"]["nutrient_deficit_weeks"], 2)
        for week in result["weeks"]:
            for row in week["resources"]["nutrients"]["elements"].values():
                self.assertEqual(Decimal(row["opening_available_kg"]) + Decimal(row["available_input_kg"])
                                 - Decimal(row["tracked_pool_used_kg"]), Decimal(row["closing_available_kg"]))
                self.assertGreaterEqual(Decimal(row["closing_available_kg"]), 0)

    def test_gross_removal_includes_losses_without_creating_a_yield_penalty(self):
        result = self.plan(budget(lots=[], allocations=[]))
        self.assertEqual(result["weeks"][0]["gross_kg"], "125.000")
        self.assertEqual(result["weeks"][0]["delivered_kg"], "100.000")
        self.assertEqual(result["weeks"][0]["resources"]["nutrients"]["elements"]["n"]["shortfall_kg"], "0.1250")
        self.assertFalse(result["summary"]["resource_constraints_met"])

    def test_other_biomass_purposes_do_not_receive_compost_credit(self):
        for purpose in ("mulch", "feed", "fuel", "reserve"):
            result = self.plan(budget(allocations=[{"lot_id": "batch", "week": 1, "purpose": purpose, "dry_mass_kg": 100}]))
            self.assertEqual(result["weeks"][0]["resources"]["nutrients"]["elements"]["n"]["available_input_kg"], "0.0000")
            self.assertEqual(result["biomass"][0]["allocated_dry_kg"][purpose], "100.0000")
            self.assertEqual(result["biomass"][0]["unallocated_dry_kg"], "0.0000")

    def test_unknown_supply_does_not_establish_a_definite_deficit_or_zero_content(self):
        for overrides in ({"n_g_per_dry_kg": None}, {"n_available_fraction": None}):
            result = self.plan(budget(lots=[lot(**overrides)]))
            row = result["weeks"][0]["resources"]["nutrients"]["elements"]["n"]
            self.assertIsNone(row["capacity_met"])
            self.assertEqual(row["unknown_sources"], ["batch"])
            self.assertIsNone(result["summary"]["resource_constraints_met"])
            self.assertIsNone(result["weeks"][5]["resources"]["nutrients"]["capacity_met"])

    def test_unknown_removal_is_not_zero_demand(self):
        result = self.plan(cohort=crop(n_removal_g_per_gross_kg=None))
        row = result["weeks"][0]["resources"]["nutrients"]["elements"]["n"]
        self.assertEqual(row["unknown_plantings"], ["p1"])
        self.assertIsNone(row["capacity_met"])

    def test_explicit_zero_content_does_not_need_an_availability_fraction(self):
        result = self.plan(budget(lots=[lot(n_g_per_dry_kg=0, n_available_fraction=None)]), crop(n_removal_g_per_gross_kg=0))
        self.assertTrue(result["weeks"][0]["resources"]["nutrients"]["elements"]["n"]["capacity_met"])

    def test_split_allocations_conserve_biomass_and_release_only_in_their_week(self):
        result = self.plan(budget(allocations=[{"lot_id": "batch", "week": 2, "purpose": "compost", "dry_mass_kg": 60},
            {"lot_id": "batch", "week": 3, "purpose": "mulch", "dry_mass_kg": 30}]))
        self.assertEqual(result["biomass"][0]["unallocated_dry_kg"], "10.0000")
        self.assertEqual(result["weeks"][0]["resources"]["nutrients"]["elements"]["n"]["available_input_kg"], "0.0000")
        self.assertEqual(result["weeks"][1]["resources"]["nutrients"]["elements"]["n"]["available_input_kg"], "0.1500")

    def test_overallocation_early_use_missing_lot_and_impossible_composition_rejected(self):
        configs = [budget(allocations=[{"lot_id": "batch", "week": 1, "purpose": "compost", "dry_mass_kg": 60},
            {"lot_id": "batch", "week": 2, "purpose": "feed", "dry_mass_kg": 50}]),
            budget(lots=[lot(available_week=2)]), budget(lots=[]),
            budget(lots=[lot(n_g_per_dry_kg=900, p_g_per_dry_kg=200)]), budget(lots=[lot(n_available_fraction="1.1")])]
        for config in configs:
            serializer = PlanningInputs(data={"start_date": "2026-01-01", "resources": {"nutrients": config}})
            self.assertFalse(serializer.is_valid())


class NutrientAPITests(APITestCase):
    def test_persisted_ledger_reproducibility_and_exclusive_allocations(self):
        farm = self.client.post("/api/farms/", {"name": "Nutrient farm", "area_acres": 2}, format="json").data["id"]
        scenario = self.client.post("/api/scenarios/", {"farm": farm, "name": "Nutrients", "inputs": {
            "start_date": "2026-01-01", "beds": [{"id": "bed1", "area_m2": 100}], "plantings": [crop()],
            "resources": {"nutrients": budget()}}}, format="json")
        self.assertEqual(scenario.status_code, 201, scenario.data)
        run = self.client.post("/api/scenario-runs/", {"scenario": scenario.data["id"]}, format="json")
        self.assertEqual(run.status_code, 201, run.data)
        self.assertEqual(calculate(run.data["assumptions_snapshot"]), run.data["result"])
        self.assertEqual(run.data["result"]["biomass"][0]["allocated_dry_kg"]["compost"], "100.0000")
        import csv
        import io
        exported = self.client.get(f'/api/scenario-runs/{run.data["id"]}/nutrient-export/')
        self.assertEqual(exported.status_code, 200)
        rows = list(csv.DictReader(io.StringIO(exported.content.decode())))
        self.assertEqual(len(rows), 312)
        self.assertEqual(rows[0]["available_input_kg"], "0.2500")

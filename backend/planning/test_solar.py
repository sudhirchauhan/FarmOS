from datetime import date
import numpy as np
import pandas as pd
import pvlib
from django.test import SimpleTestCase
from rest_framework.test import APITestCase
from .solar import blocked, calculate_solar, diffuse_visibility, directions, normal
from .solar_serializers import SolarInput


def inputs(**overrides):
    data = {"latitude": 18.52, "longitude": 73.86, "timezone": "Asia/Kolkata", "start_date": "2026-06-21",
        "points": [{"id": "open", "x": 0, "y": 0, "z": 0}], **overrides}
    serializer = SolarInput(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


class SolarGeometryTests(SimpleTestCase):
    def test_published_nrel_spa_reference(self):
        # NREL SPA report example: 2003-10-17 12:30:30 at UTC-07,
        # 39.742476 N, 105.1786 W, altitude 1830.14 m, 820 mbar, 11 C.
        position = pvlib.solarposition.get_solarposition(pd.DatetimeIndex(["2003-10-17T12:30:30-07:00"]),
            39.742476, -105.1786, altitude=1830.14, pressure=82000, temperature=11, method="nrel_numpy")
        self.assertAlmostEqual(float(position["azimuth"].iloc[0]), 194.340241, places=4)
        self.assertAlmostEqual(float(position["apparent_zenith"].iloc[0]), 50.111622, places=4)

    def test_analytic_wall_shadow_and_parallel_rays(self):
        wall = [{"x": 2, "y": -1, "width": 0.1, "depth": 2, "height": 2}]
        rays = directions(np.array([90, 90, 90, 0]), np.array([30, 45, 60, 45]))
        self.assertEqual(blocked([0, 0, 0], rays, wall).tolist(), [True, True, False, False])
        self.assertEqual(blocked([0, 3, 0], rays, wall).tolist(), [False] * 4)

    def test_tilted_surfaces_and_diffuse_occlusion(self):
        south = normal(180, 90)
        north = normal(0, 90)
        ray = directions(np.array([180]), np.array([45]))[0]
        self.assertGreater(float(south @ ray), 0)
        self.assertLess(float(north @ ray), 0)
        wall = [{"x": -2, "y": 1, "width": 4, "depth": 1, "height": 4}]
        self.assertEqual(diffuse_visibility([0, 0, 0], normal(0, 0), []), 1)
        self.assertLess(diffuse_visibility([0, 0, 0], normal(0, 0), wall), 1)


class SolarCalculationTests(SimpleTestCase):
    def test_dli_units_direct_diffuse_and_night(self):
        radiation = [{"dni_w_m2": 0, "dhi_w_m2": 100}] * 24
        result = calculate_solar(inputs(radiation=radiation, radiation_source="Synthetic diffuse-only test"))
        point = result["points"][0]
        daylight = sum(sample["sun_elevation_deg"] > 0 for sample in point["samples"])
        expected = daylight * 100 * 0.45 * 4.57 * 3600 / 1e6
        self.assertAlmostEqual(point["daily"][0]["dli_mol_m2_day"], expected, places=4)
        self.assertTrue(all(sample["direct_w_m2"] == 0 for sample in point["samples"]))
        self.assertEqual(point["samples"][0]["par_umol_m2_s"], 0)

    def test_north_south_faces_and_shading_reduce_light(self):
        points = [{"id": "north", "x": 0, "y": 0, "z": 0, "tilt_deg": 90, "azimuth_deg": 0},
                  {"id": "south", "x": 0, "y": 0, "z": 0, "tilt_deg": 90, "azimuth_deg": 180}]
        data = inputs(start_date="2026-12-21", points=points)
        result = calculate_solar(data)
        self.assertGreater(result["points"][1]["daily"][0]["dli_mol_m2_day"], result["points"][0]["daily"][0]["dli_mol_m2_day"])
        obstructed = calculate_solar(inputs(start_date="2026-12-21", points=points,
            obstacles=[{"id": "wall", "x": -10, "y": -2, "width": 20, "depth": 1, "height": 10}]))
        self.assertLess(obstructed["points"][1]["daily"][0]["dli_mol_m2_day"], result["points"][1]["daily"][0]["dli_mol_m2_day"])
        self.assertEqual(obstructed["points"][0]["daily"][0]["direct_shade_hours"], 0)

    def test_both_hemispheres_and_date_line(self):
        north = calculate_solar(inputs(latitude=35, longitude=0, timezone="UTC", start_date="2026-12-21"))
        south = calculate_solar(inputs(latitude=-35, longitude=0, timezone="UTC", start_date="2026-12-21"))
        self.assertGreater(south["points"][0]["daily"][0]["dli_mol_m2_day"], north["points"][0]["daily"][0]["dli_mol_m2_day"])
        east = calculate_solar(inputs(longitude=180, timezone="Pacific/Fiji"))
        west = calculate_solar(inputs(longitude=-180, timezone="Pacific/Fiji"))
        self.assertAlmostEqual(east["points"][0]["daily"][0]["dli_mol_m2_day"], west["points"][0]["daily"][0]["dli_mol_m2_day"], places=4)

    def test_dst_day_lengths_and_determinism(self):
        for day, hours in [("2026-03-29", 23), ("2026-10-25", 25)]:
            data = inputs(timezone="Europe/Zurich", latitude=47.38, longitude=8.54, start_date=day)
            result = calculate_solar(data)
            self.assertEqual(len(result["points"][0]["samples"]), hours)
            self.assertEqual(sum(sample["interval_seconds"] for sample in result["points"][0]["samples"]), hours * 3600)
            self.assertEqual(result, calculate_solar(data))

    def test_polar_night_and_nonexistent_local_day(self):
        result = calculate_solar(inputs(latitude=89, longitude=0, timezone="UTC", start_date="2026-12-21"))
        self.assertEqual(result["points"][0]["daily"][0]["dli_mol_m2_day"], 0)
        with self.assertRaisesRegex(ValueError, "does not exist"):
            calculate_solar(inputs(timezone="Pacific/Apia", start_date="2011-12-30"))


class SolarAPITests(APITestCase):
    def test_persisted_run_is_read_only_and_has_provenance(self):
        data = {"latitude": 18.52, "longitude": 73.86, "timezone": "Asia/Kolkata", "start_date": "2026-06-21",
                "points": [{"id": "open", "x": 0, "y": 0, "z": 0}]}
        created = self.client.post("/api/solar-runs/", data, format="json")
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data["result"]["status"], "provisional")
        self.assertIn("clear-sky", created.data["result"]["radiation_source"])
        self.assertEqual(self.client.get(f'/api/solar-runs/{created.data["id"]}/').data, created.data)
        self.assertEqual(self.client.patch(f'/api/solar-runs/{created.data["id"]}/', {}, format="json").status_code, 405)

    def test_invalid_geometry_timezone_and_radiation(self):
        base = {"latitude": 18.52, "longitude": 73.86, "timezone": "Asia/Kolkata", "start_date": "2026-06-21",
                "points": [{"id": "open", "x": 0, "y": 0, "z": 0}]}
        for overrides in [{"timezone": "invalid/zone"}, {"latitude": 91},
            {"obstacles": [{"id": "inside", "x": -1, "y": -1, "width": 2, "depth": 2, "height": 1}]},
            {"radiation": [{"dni_w_m2": 1, "dhi_w_m2": 1}], "radiation_source": "test"}]:
            response = self.client.post("/api/solar-runs/", {**base, **overrides}, format="json")
            self.assertEqual(response.status_code, 400, response.data)

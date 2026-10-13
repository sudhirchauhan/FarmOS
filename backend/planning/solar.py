"""Solar geometry and a bounded, opaque-box light model in local ENU metres.

SPA is provided by pvlib. PAR conversion, turbidity and geometry are explicit
assumptions. These results do not establish crop yield or farm feasibility.
"""
from datetime import timedelta
import hashlib
import json
import numpy as np
import pandas as pd
import pvlib

SOLAR_VERSION = "solar-core/0.1.0"


def blocked(origin, directions, obstacles):
    """Ray/AABB intersections; tangent contact counts as an occlusion."""
    directions = np.asarray(directions, dtype=float)
    if not obstacles:
        return np.zeros(len(directions), dtype=bool)
    low = np.array([[b["x"], b["y"], 0] for b in obstacles], dtype=float)
    high = low + np.array([[b["width"], b["depth"], b["height"]] for b in obstacles], dtype=float)
    origin = np.asarray(origin, dtype=float)
    parallel = np.abs(directions) < 1e-12
    safe = np.where(parallel, 1, directions)[:, None, :]
    a = (low[None, :, :] - origin) / safe
    b = (high[None, :, :] - origin) / safe
    near = np.minimum(a, b)
    far = np.maximum(a, b)
    inside = (origin >= low) & (origin <= high)
    near = np.where(parallel[:, None, :], np.where(inside[None, :, :], -np.inf, np.inf), near)
    far = np.where(parallel[:, None, :], np.where(inside[None, :, :], np.inf, -np.inf), far)
    entry = near.max(axis=2)
    exit = far.min(axis=2)
    return ((exit + 1e-9 >= np.maximum(entry, 0)) & (exit > 1e-8)).any(axis=1)


def directions(azimuth, elevation):
    az, el = np.radians(azimuth), np.radians(elevation)
    return np.stack([np.sin(az) * np.cos(el), np.cos(az) * np.cos(el), np.sin(el)], axis=-1)


def normal(azimuth, tilt):
    return directions(np.array([azimuth]), np.array([90 - tilt]))[0]


def diffuse_visibility(origin, surface_normal, obstacles):
    if not obstacles:
        return 1.0
    # Deterministic isotropic sky quadrature, azimuth 10°, elevation 5°.
    az, el = np.meshgrid(np.arange(5, 360, 10), np.arange(2.5, 90, 5))
    rays = directions(az.ravel(), el.ravel())
    projected = np.maximum(0, rays @ surface_normal)
    solid_angle = np.radians(10) * (np.sin(np.radians(el.ravel() + 2.5)) - np.sin(np.radians(el.ravel() - 2.5)))
    weights = projected * solid_angle
    total = weights.sum()
    return float(weights[~blocked(origin, rays, obstacles)].sum() / total) if total > 0 else 0.0


def calculate_solar(inputs):
    start = pd.Timestamp(inputs["start_date"]).tz_localize(inputs["timezone"], nonexistent="shift_forward", ambiguous=False)
    end = pd.Timestamp(inputs["start_date"] + timedelta(days=inputs["days"])).tz_localize(inputs["timezone"], nonexistent="shift_forward", ambiguous=False)
    times = pd.date_range(start, end, freq=f'{inputs["step_minutes"]}min', inclusive="left")
    if not len(times):
        raise ValueError("This local calendar interval does not exist in the selected time zone.")
    boundaries = times[1:].append(pd.DatetimeIndex([end]))
    seconds = (boundaries - times).total_seconds().to_numpy()
    midpoints = times + pd.to_timedelta(seconds / 2, unit="s")
    location = pvlib.location.Location(inputs["latitude"], inputs["longitude"], tz=inputs["timezone"], altitude=inputs["altitude_m"])
    position = location.get_solarposition(midpoints, method="nrel_numpy", temperature=inputs["temperature_c"])
    if inputs.get("radiation") is not None:
        radiation = inputs["radiation"]
        if len(radiation) != len(times):
            raise ValueError(f"Radiation must contain exactly {len(times)} midpoint samples for this local calendar interval.")
        dni = np.array([r["dni_w_m2"] for r in radiation])
        dhi = np.array([r["dhi_w_m2"] for r in radiation])
        source = "supplied midpoint DNI/DHI; " + inputs["radiation_source"]
    else:
        clear = location.get_clearsky(midpoints, model="ineichen", solar_position=position, linke_turbidity=inputs["linke_turbidity"])
        dni, dhi = clear["dni"].to_numpy(), clear["dhi"].to_numpy()
        source = "Ineichen clear-sky model with user-assumed Linke turbidity; not observed weather"
    elevation = position["apparent_elevation"].to_numpy()
    azimuth = position["azimuth"].to_numpy()
    daylight = elevation > 0
    # Nighttime irradiance is zero even when supplied sensor values are nonzero.
    dni, dhi = np.where(daylight, dni, 0), np.where(daylight, dhi, 0)
    rays = directions(azimuth, elevation)
    conversion = inputs["par_fraction"] * inputs["photon_umol_per_joule_par"]
    output = []
    date_keys = np.array([time.date().isoformat() for time in times])
    for point in inputs["points"]:
        origin = [point["x"], point["y"], point["z"]]
        surface = normal(point["azimuth_deg"], point["tilt_deg"])
        incidence = np.maximum(0, rays @ surface)
        shade = blocked(origin, rays, inputs["obstacles"]) & daylight & (incidence > 1e-10) & (dni > 0)
        visibility = diffuse_visibility(origin, surface, inputs["obstacles"])
        direct = dni * incidence * (~shade)
        diffuse = dhi * (1 + np.cos(np.radians(point["tilt_deg"]))) / 2 * visibility
        par = (direct + diffuse) * conversion
        daily = [{"date": day, "dli_mol_m2_day": round(float(np.sum(par[date_keys == day] * seconds[date_keys == day]) / 1e6), 4),
                  "direct_shade_hours": round(float(np.sum(seconds[(date_keys == day) & shade]) / 3600), 3)} for day in sorted(set(date_keys))]
        samples = [{"interval_start": times[i].isoformat(), "midpoint": midpoints[i].isoformat(), "interval_seconds": float(seconds[i]),
                    "sun_elevation_deg": round(float(elevation[i]), 4), "sun_azimuth_deg": round(float(azimuth[i]), 4),
                    "direct_shaded": bool(shade[i]), "direct_w_m2": round(float(direct[i]), 4),
                    "diffuse_w_m2": round(float(diffuse[i]), 4), "par_umol_m2_s": round(float(par[i]), 4)} for i in range(len(times))]
        output.append({"id": point["id"], "diffuse_visibility_fraction": round(visibility, 5), "daily": daily, "samples": samples})
    snapshot = json.loads(json.dumps(inputs, default=str))
    return {"engine_version": SOLAR_VERSION, "pvlib_version": pvlib.__version__,
            "numerical_versions": {"numpy": np.__version__, "pandas": pd.__version__}, "status": "provisional", "inputs": snapshot,
            "input_sha256": hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "radiation_source": source, "points": output,
            "warnings": ["Not a crop-yield forecast: crop response, root space and water/nutrient constraints are not integrated.",
                         "Opaque axis-aligned boxes only; no terrain, canopy transmission, growth, pruning or reflected radiation.",
                         "Diffuse light uses an isotropic sky and 10°×5° visibility quadrature, not a calibrated canopy model.",
                         "PAR fraction and photon conversion are explicit spectral assumptions; local radiation and sensor validation remain necessary."]}

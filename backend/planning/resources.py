"""Explicit weekly water conservation and labour-capacity checks.

Resource shortfalls are constraints, not invented crop stress coefficients.
"""
from datetime import date, timedelta
from decimal import Decimal

D = lambda value: Decimal(str(value))
ZERO = Decimal(0)


def light_factors(snapshot):
    factors = {}
    studies = snapshot.get("light_studies", {})
    for planting in snapshot["inputs"]["plantings"]:
        response = planting.get("light_response")
        if not response:
            factors[planting["id"]] = Decimal(1)
            continue
        days = {}
        for run_id in response["solar_runs"]:
            days.update(studies[str(run_id)]["positions"][response["point_id"]])
        start = date.fromisoformat(planting["sowing_date"])
        end = date.fromisoformat(planting["harvest_start"]) + timedelta(weeks=planting["harvest_weeks"])
        minimum, optimum = D(response["minimum_dli"]), D(response["optimum_dli"])
        values = []
        for i in range((end - start).days):
            day = (start + timedelta(days=i)).isoformat()
            if day not in days:
                raise ValueError(f"Missing growing-period DLI for {planting['id']} on {day}.")
            values.append(max(ZERO, min(Decimal(1), (D(days[day]) - minimum) / (optimum - minimum))))
        factors[planting["id"]] = sum(values, ZERO) / len(values)
    return factors


def resource_week(inputs, day, index, gross_by_planting, delivered, opening_storage):
    settings = inputs.get("resources")
    if not settings:
        return None, opening_storage
    end = day + timedelta(days=7)
    water_demand = ZERO
    labour_demand = ZERO
    water_unknown, labour_unknown = [], []
    for planting in inputs["plantings"]:
        sow = date.fromisoformat(planting["sowing_date"])
        finish = date.fromisoformat(planting["harvest_start"]) + timedelta(weeks=planting["harvest_weeks"])
        active_days = max(0, (min(end, finish) - max(day, sow)).days)
        if not active_days:
            continue
        area = D(planting["area_m2"])
        water = planting.get("daily_water_l_per_m2")
        if water is None:
            water_unknown.append(planting["id"])
        else:
            water_demand += area * D(water) * active_days / 1000
        parameters = ("sowing_hours_per_m2", "maintenance_hours_per_m2_week", "harvest_hours_per_kg")
        if any(planting.get(key) is None for key in parameters):
            labour_unknown.append(planting["id"])
        else:
            labour_demand += area * D(planting["maintenance_hours_per_m2_week"]) * active_days / 7
            if day <= sow < end:
                labour_demand += area * D(planting["sowing_hours_per_m2"])
            labour_demand += gross_by_planting.get(planting["id"], ZERO) * D(planting["harvest_hours_per_kg"])
    result = {}
    if settings.get("water"):
        water = settings["water"]
        profile = next((item for item in water["weekly_overrides"] if item["week"] == index + 1), {})
        inflow = D(profile.get("inflow_m3", water["weekly_inflow_m3"]))
        evaporation_target = D(profile.get("evaporation_m3", water["weekly_evaporation_m3"]))
        efficiency = D(water["irrigation_efficiency"])
        overflow = max(ZERO, opening_storage + inflow - D(water["storage_capacity_m3"]))
        available = opening_storage + inflow - overflow
        evaporation = min(available, evaporation_target)
        available -= evaporation
        required = water_demand / efficiency
        withdrawal = min(available, D(water["weekly_pumping_limit_m3"]), required)
        closing = available - withdrawal
        result["water"] = {"opening_storage_m3": opening_storage, "inflow_m3": inflow, "overflow_m3": overflow,
            "evaporation_m3": evaporation, "required_withdrawal_m3": required, "withdrawal_m3": withdrawal,
            "conveyance_loss_m3": withdrawal * (1 - efficiency), "crop_demand_m3": water_demand,
            "crop_water_delivered_m3": withdrawal * efficiency, "shortfall_m3": water_demand - withdrawal * efficiency,
            "closing_storage_m3": closing, "unknown_plantings": water_unknown,
            "capacity_met": False if withdrawal < required else None if water_unknown else True}
        opening_storage = closing
    if settings.get("labour"):
        labour = settings["labour"]
        labour_demand += D(labour["fixed_hours_per_week"])
        labour_demand += delivered * D(labour["packing_hours_per_delivered_kg"])
        if delivered > 0:
            labour_demand += D(labour["delivery_hours_per_week"])
        available = D(labour["available_hours_per_week"])
        result["labour"] = {"required_hours": labour_demand, "available_hours": available,
            "shortfall_hours": max(ZERO, labour_demand - available), "unknown_plantings": labour_unknown,
            "capacity_met": False if labour_demand > available else None if labour_unknown else True}
    return result, opening_storage


def resource_display(value):
    if isinstance(value, Decimal):
        return str(value.quantize(Decimal("0.0001")))
    if isinstance(value, dict):
        return {key: resource_display(item) for key, item in value.items()}
    return value

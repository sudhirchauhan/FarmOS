"""Pure, deterministic 104-week planning calculations. No validated yield claims."""
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
from .resources import light_factors, resource_week, resource_display

ENGINE_VERSION = "planning-core/0.2.0"
ACRE_M2 = Decimal("4046.8564224")
GROUPS = ("leafy", "fruiting", "roots", "legumes")
ZERO = Decimal(0)


def D(value):
    return Decimal(str(value))


def display(value, places=2):
    return str(D(value).quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP))


def calculate(snapshot):
    # Input limits can produce totals larger than Decimal's default precision.
    # Keep arithmetic deterministic without changing the process-wide context.
    with localcontext() as context:
        context.prec = 50
        return _calculate(snapshot)


def _calculate(snapshot):
    inputs = snapshot["inputs"]
    start = date.fromisoformat(inputs["start_date"])
    demand = D(inputs["households"]) * D(inputs["basket_kg_per_week"])
    loss = D(inputs["combined_loss_fraction"])
    annual_revenue = D(inputs["households"]) * D(inputs["monthly_price_inr"]) * 12
    annual_collections = annual_revenue * D(inputs["paid_enrollment_fraction"])
    weekly_revenue = annual_revenue / 52
    weekly_fixed_cost = D(inputs["monthly_fixed_opex_inr"]) * 12 / 52
    family_cost = D(inputs["weekly_family_labour_hours"]) * D(inputs["family_labour_hourly_value_inr"])
    cash = D(inputs["initial_cash_inr"])
    minimum_cash = cash
    paid_months = set()
    weeks = []
    month_rows = defaultdict(lambda: defaultdict(lambda: ZERO))
    totals = defaultdict(lambda: ZERO)
    service_weeks = 0
    crop_totals = defaultdict(lambda: ZERO)
    factors = light_factors(snapshot)
    settings = inputs.get("resources") or {}
    storage = D(settings["water"]["opening_storage_m3"]) if settings.get("water") else ZERO
    water_deficit_weeks = labour_deficit_weeks = 0
    resource_states = []
    for index in range(104):
        day = start + timedelta(weeks=index)
        end = day + timedelta(days=7)
        gross = {group: ZERO for group in GROUPS}
        cohort_gross = {}
        for planting in inputs["plantings"]:
            harvest_start = date.fromisoformat(planting["harvest_start"])
            harvest_end = harvest_start + timedelta(weeks=planting["harvest_weeks"])
            overlap_days = max(0, (min(end, harvest_end) - max(day, harvest_start)).days)
            amount = D(planting["area_m2"]) * D(planting["gross_yield_kg_per_m2"]) * overlap_days / (planting["harvest_weeks"] * 7)
            amount *= factors[planting["id"]]
            cohort_gross[planting["id"]] = amount
            gross[planting["crop_group"]] += amount
            crop_totals[planting["crop"]] += amount
        groups = {}
        delivered = ZERO
        for group in GROUPS:
            requested = demand * D(inputs["basket_shares"][group])
            marketable = gross[group] * (1 - loss)
            fulfilled = min(marketable, requested)
            delivered += fulfilled
            groups[group] = {"demand_kg": display(requested, 3), "gross_kg": display(gross[group], 3),
                "marketable_kg": display(marketable, 3), "delivered_kg": display(fulfilled, 3),
                "shortfall_kg": display(requested - fulfilled, 3), "surplus_kg": display(marketable - fulfilled, 3)}
        resources, storage = resource_week(inputs, day, index, cohort_gross, delivered, storage)
        if resources:
            for name, row in resources.items():
                resource_states.append(row["capacity_met"])
                if row["capacity_met"] is False:
                    if name == "water":
                        water_deficit_weeks += 1
                    else:
                        labour_deficit_weeks += 1
        if demand > 0 and delivered == demand:
            service_weeks += 1
        # Collections on calendar month start dates; a mid-month start does not
        # invent a full month's payment. Revenue is an annualized accrual benchmark.
        collections = ZERO
        for offset in range(7):
            current = day + timedelta(days=offset)
            month = current.strftime("%Y-%m")
            if current.day == 1 and month not in paid_months:
                collections += annual_collections / 12
                paid_months.add(month)
        capex = D(inputs["initial_capex_inr"]) if index == 0 else ZERO
        opex = weekly_fixed_cost + delivered * D(inputs["variable_cost_inr_per_delivered_kg"])
        opening = cash
        cash += collections - opex - capex
        minimum_cash = min(minimum_cash, cash)
        operating_profit = weekly_revenue - opex
        economic_profit = operating_profit - family_cost
        raw = {"demand_kg": demand, "gross_kg": sum(gross.values()), "delivered_kg": delivered,
            "shortfall_kg": demand - delivered, "revenue_accrual_inr": weekly_revenue,
            "collections_inr": collections, "opex_inr": opex, "capex_inr": capex,
            "operating_surplus_inr": operating_profit, "economic_surplus_inr": economic_profit}
        weeks.append({"week": index + 1, "start_date": day.isoformat(), "groups": groups,
            "resources": resource_display(resources) if resources else None,
            **{key: display(value, 3 if key.endswith("_kg") else 2) for key, value in raw.items()},
            "opening_cash_inr": display(opening), "closing_cash_inr": display(cash)})
        # Monthly display groups weekly buckets by their start date, not exact
        # daily accrual. State this policy rather than imply a monthly ledger.
        for key, value in raw.items():
            totals[key] += value
            month_rows[day.strftime("%Y-%m")][key] += value
    warnings = [
        "Illustrative, not validated: seasonal crop suitability, nutrients, root competition and calibrated crop stress are not assessed.",
        "Yields are input assumptions with uniform daily harvest profiles; no vertical yield uplift is applied.",
        "No storage, substitution, procurement, churn, tax, debt, depreciation or surplus sales are modeled.",
        "Revenue assumes subscribed households; collections use paid enrollment and calendar-month payments, independently of supply. Refunds and service-dependent billing are not modeled.",
        "Monthly summaries group seven-day buckets by start date; they are not calendar-accurate ledgers.",
    ]
    linked = sum(bool(p.get("light_response")) for p in inputs["plantings"])
    if linked:
        warnings.append("Linked DLI constrains unshaded potential using an assumed linear response averaged across the growing period. Curves are not field-calibrated.")
    if linked < len(inputs["plantings"]):
        warnings.append("Some cohorts have no linked light study; their yields remain unconstrained user assumptions.")
    if not settings:
        warnings.append("Water and labour capacity are not assessed: enable resource budgets and crop-specific requirements.")
    else:
        warnings.append("Water uses assumed constant crop demand and weekly storage/pumping budgets, not weather/ET or daily peak checks. Labour uses explicit task-rate assumptions.")
        warnings.append("Resource shortfalls do not automatically reduce yield or hire workers; missing crop stress/hiring rules remain explicit constraints.")
        if None in resource_states:
            warnings.append("Some active cohorts have unknown water or labour requirements. Their capacity checks remain incomplete.")
        if water_deficit_weeks or labour_deficit_weeks:
            warnings.append("Water or labour capacity is exceeded; projected basket fulfillment alone does not establish feasibility.")
    if not inputs["plantings"]:
        warnings.append("No planting cohorts supplied: forecast harvest is zero, not an estimate of farm capacity.")
    if D(inputs["monthly_fixed_opex_inr"]) == 0:
        warnings.append("Fixed operating costs are zero. Enter realistic costs before assessing profit.")
    if minimum_cash < 0:
        warnings.append("Cash becomes negative: additional financing or a revised cost plan is required.")
    if demand > 0 and D(service_weeks) / 104 < D(inputs["service_target_fraction"]):
        warnings.append("Weekly basket service target is not met; annual totals cannot establish feasibility.")
    fingerprint = hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "engine_version": ENGINE_VERSION, "input_sha256": fingerprint, "status": "provisional",
        "horizon_weeks": 104, "currency": "INR", "units": {"mass": "kg", "area": "m2", "cash": "INR", "water": "m3", "labour": "person-hours"},
        "assumptions": {"loss_policy": "One combined loss applied once to gross harvest", "harvest_profile": "uniform_daily",
            "collection_policy": "Full monthly payment on the first day of each calendar month", "storage_policy": "none; weekly surplus is not carried forward",
            "solar_validated": False, "confidence": "user assumptions unless documented per planting"},
        "light_adjustments": {id: display(factor, 6) for id, factor in factors.items()},
        "baseline": {"annual_delivered_demand_kg": display(demand * 52, 3),
            "annual_gross_target_kg": display(demand * 52 / (1 - loss), 3),
            "annual_subscription_revenue_inr": display(annual_revenue),
            "annual_paid_collections_benchmark_inr": display(annual_collections),
            "physical_area_m2": display(D(snapshot["farm"]["area_acres"]) * ACRE_M2, 3),
            "exclusive_bed_area_m2": display(sum(D(bed["area_m2"]) for bed in inputs["beds"]), 3)},
        "summary": {**{key: display(value, 3 if key.endswith("_kg") else 2) for key, value in totals.items()},
            "fully_supplied_weeks": service_weeks,
            "service_fraction": display(D(service_weeks) / 104, 4) if demand else None,
            "service_target_met": D(service_weeks) / 104 >= D(inputs["service_target_fraction"]) if demand else None,
            "closing_cash_inr": display(cash), "minimum_cash_inr": display(minimum_cash),
            "additional_funding_required_inr": display(max(ZERO, -minimum_cash)),
            "water_deficit_weeks": water_deficit_weeks if settings.get("water") else None,
            "labour_deficit_weeks": labour_deficit_weeks if settings.get("labour") else None,
            "resource_constraints_met": False if False in resource_states else None if not resource_states or None in resource_states else True,
            "agronomic_feasibility": "not_assessed"},
        "crop_gross_totals_kg": {crop: display(amount, 3) for crop, amount in sorted(crop_totals.items())},
        "weeks": weeks,
        "months": [{"month": month, **{key: display(value, 3 if key.endswith("_kg") else 2) for key, value in row.items()}} for month, row in sorted(month_rows.items())],
        "warnings": warnings,
    }

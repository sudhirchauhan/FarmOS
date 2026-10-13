"""Available elemental nutrient pool and exclusive dry-biomass ledger.

This is harvest-export bookkeeping, not a soil-mineralization or crop-uptake model.
"""
from decimal import Decimal

ELEMENTS = ("n", "p", "k")
PURPOSES = ("compost", "mulch", "feed", "fuel", "reserve")
ZERO = Decimal(0)


def D(value):
    return Decimal(str(value))


def initial_nutrients(inputs):
    settings = (inputs.get("resources") or {}).get("nutrients")
    if not settings:
        return None
    return {"stocks": {element: D(settings[f"opening_{element}_available_kg"]) for element in ELEMENTS},
            "unknown_sources": {element: set() for element in ELEMENTS}}


def nutrient_week(inputs, index, gross_by_planting, state):
    if state is None:
        return None
    settings = inputs["resources"]["nutrients"]
    lots = {lot["id"]: lot for lot in settings["lots"]}
    incoming = {element: ZERO for element in ELEMENTS}
    content = {element: ZERO for element in ELEMENTS}
    biomass = {purpose: ZERO for purpose in PURPOSES}
    for allocation in settings["allocations"]:
        if allocation["week"] != index + 1:
            continue
        mass = D(allocation["dry_mass_kg"])
        biomass[allocation["purpose"]] += mass
        if allocation["purpose"] != "compost":
            continue
        lot = lots[allocation["lot_id"]]
        for element in ELEMENTS:
            concentration = lot.get(f"{element}_g_per_dry_kg")
            fraction = lot.get(f"{element}_available_fraction")
            if concentration is None:
                state["unknown_sources"][element].add(lot["id"])
            else:
                total = mass * D(concentration) / 1000
                content[element] += total
                if total == 0:
                    continue
                if fraction is None:
                    state["unknown_sources"][element].add(lot["id"])
                else:
                    incoming[element] += total * D(fraction)
    result = {"elements": {}, "biomass_allocated_dry_kg": biomass}
    statuses = []
    for element in ELEMENTS:
        removal, unknown = ZERO, []
        for planting in inputs["plantings"]:
            mass = gross_by_planting.get(planting["id"], ZERO)
            if mass <= 0:
                continue
            coefficient = planting.get(f"{element}_removal_g_per_gross_kg")
            if coefficient is None:
                unknown.append(planting["id"])
            else:
                removal += mass * D(coefficient) / 1000
        opening = state["stocks"][element]
        available = opening + incoming[element]
        used = min(available, removal)
        closing = available - used
        state["stocks"][element] = closing
        status = None if state["unknown_sources"][element] else False if removal > available else None if unknown else True
        statuses.append(status)
        result["elements"][element] = {"opening_available_kg": opening, "total_compost_content_kg": content[element],
            "available_input_kg": incoming[element], "required_removal_kg": removal, "tracked_pool_used_kg": used,
            "shortfall_kg": removal - used, "closing_available_kg": closing,
            "unknown_plantings": unknown, "unknown_sources": sorted(state["unknown_sources"][element]), "capacity_met": status}
    result["capacity_met"] = False if False in statuses else None if None in statuses else True
    return result


def biomass_summary(inputs):
    settings = (inputs.get("resources") or {}).get("nutrients")
    if not settings:
        return None
    lots = []
    for lot in settings["lots"]:
        assigned = {purpose: sum((D(a["dry_mass_kg"]) for a in settings["allocations"]
                    if a["lot_id"] == lot["id"] and a["purpose"] == purpose), ZERO) for purpose in PURPOSES}
        lots.append({"id": lot["id"], "name": lot["name"], "source_kind": lot["source_kind"], "source_note": lot["source_note"],
                     "dry_mass_kg": D(lot["dry_mass_kg"]), "allocated_dry_kg": assigned,
                     "unallocated_dry_kg": D(lot["dry_mass_kg"]) - sum(assigned.values(), ZERO)})
    return lots

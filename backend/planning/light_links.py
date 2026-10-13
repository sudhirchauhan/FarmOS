from datetime import date, timedelta
from decimal import Decimal
from rest_framework.exceptions import ValidationError
from .models import SolarRun


def resolve_light_studies(inputs):
    """Resolve immutable study references; never extend a day to other seasons."""
    requested = {str(id) for p in inputs["plantings"] if p.get("light_response") for id in p["light_response"]["solar_runs"]}
    if len(requested) > 64:
        raise ValidationError({"light_response": "Use at most 64 distinct studies per synchronous scenario run."})
    runs = {str(run.id): run for run in SolarRun.objects.filter(id__in=requested)} if requested else {}
    if requested - runs.keys():
        raise ValidationError({"light_response": "Every referenced solar run must exist."})
    studies = {id: {"engine_version": run.engine_version, "input_sha256": run.result["input_sha256"],
                   "radiation_source": run.result["radiation_source"], "inputs": run.inputs,
                   "positions": {p["id"]: {day["date"]: day["dli_mol_m2_day"] for day in p["daily"]} for p in run.result["points"]}}
               for id, run in runs.items()}
    for planting in inputs["plantings"]:
        response = planting.get("light_response")
        if not response:
            continue
        daily, sites = {}, set()
        for id in response["solar_runs"]:
            study = studies[str(id)]
            site = study["inputs"]
            sites.add((site["latitude"], site["longitude"], site["timezone"]))
            if response["point_id"] not in study["positions"]:
                raise ValidationError({"light_response": f"Position {response['point_id']} is missing in solar run {id}."})
            for day, value in study["positions"][response["point_id"]].items():
                if day in daily and Decimal(str(daily[day])) != Decimal(str(value)):
                    raise ValidationError({"light_response": f"Conflicting DLI on {day}; select non-overlapping studies."})
                daily[day] = value
        if len(sites) > 1:
            raise ValidationError({"light_response": "Studies for a cohort must share site coordinates and time zone."})
        start = date.fromisoformat(str(planting["sowing_date"]))
        end = date.fromisoformat(str(planting["harvest_start"])) + timedelta(weeks=planting["harvest_weeks"])
        if (end - start).days > len(daily):
            raise ValidationError({"light_response": "Solar studies must cover every day from sowing through harvest end."})
        for offset in range((end - start).days):
            day = (start + timedelta(days=offset)).isoformat()
            if day not in daily:
                raise ValidationError({"light_response": f"Missing growing-period DLI for {planting['id']} on {day}."})
    return studies

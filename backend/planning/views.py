import csv
import io
from decimal import Decimal
from django.db import transaction
from django.http import HttpResponse
from rest_framework.generics import get_object_or_404
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .engine import ENGINE_VERSION, calculate
from .models import Farm, Scenario, ScenarioRun
from .serializers import FarmSerializer, ScenarioSerializer, RunSerializer, json_values
from .light_links import resolve_light_studies


class FarmViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Farm.objects.order_by("-created_at")
    serializer_class = FarmSerializer


class ScenarioViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Scenario.objects.select_related("farm").order_by("-created_at")
    serializer_class = ScenarioSerializer
    http_method_names = ["get", "post", "put", "head", "options"]

    def update(self, request, *args, **kwargs):
        # Full input replacement makes the saved assumptions explicit. Lock the
        # row while incrementing revision to avoid lost revision numbers.
        with transaction.atomic():
            instance = get_object_or_404(self.get_queryset().select_for_update(), pk=kwargs["pk"])
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def clone(self, request, pk=None):
        original = self.get_object()
        name = serializers.CharField(max_length=200).run_validation(request.data.get("name", f"{original.name} copy"))
        clone = Scenario.objects.create(farm=original.farm, name=name, inputs=original.inputs)
        return Response(self.get_serializer(clone).data, status=status.HTTP_201_CREATED)


class RunRequest(serializers.Serializer):
    scenario = serializers.PrimaryKeyRelatedField(queryset=Scenario.objects.all())


class RunViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = ScenarioRun.objects.order_by("-created_at")
    serializer_class = RunSerializer

    def create(self, request):
        request_serializer = RunRequest(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            scenario = Scenario.objects.select_for_update().select_related("farm").get(pk=request_serializer.validated_data["scenario"].pk)
            farm = FarmSerializer(scenario.farm).data
            # Revalidate against the current farm before producing a snapshot.
            check = ScenarioSerializer(scenario, data={"farm": str(scenario.farm_id), "name": scenario.name, "inputs": scenario.inputs})
            check.is_valid(raise_exception=True)
            snapshot = {"farm": dict(farm), "inputs": json_values(check.validated_data["inputs"])}
            snapshot["light_studies"] = resolve_light_studies(check.validated_data["inputs"])
            run = ScenarioRun.objects.create(scenario=scenario, scenario_revision=scenario.revision,
                engine_version=ENGINE_VERSION, assumptions_snapshot=snapshot, result=calculate(snapshot))
        return Response(self.get_serializer(run).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="weekly-export")
    def weekly_export(self, request, pk=None):
        run = self.get_object()
        stream = io.StringIO()
        fields = ["week", "start_date", "demand_kg", "gross_kg", "delivered_kg", "shortfall_kg",
            "revenue_accrual_inr", "collections_inr", "opex_inr", "capex_inr", "opening_cash_inr", "closing_cash_inr"]
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(run.result["weeks"])
        response = HttpResponse(stream.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="farmos-{run.id}-weekly.csv"'
        response["X-FarmOS-Engine-Version"] = run.engine_version
        return response

    @action(detail=False, methods=["get"])
    def comparison(self, request):
        ids = request.query_params.getlist("run")
        if not 2 <= len(ids) <= 4:
            raise serializers.ValidationError("Provide two to four run IDs with repeated ?run= parameters.")
        field = serializers.UUIDField()
        ids = [field.run_validation(value) for value in ids]
        runs = {run.id: run for run in self.get_queryset().filter(id__in=ids)}
        if len(runs) != len(ids):
            raise serializers.ValidationError("Run IDs must exist and be distinct.")
        metrics = ("delivered_kg", "shortfall_kg", "closing_cash_inr", "additional_funding_required_inr")
        reference = runs[ids[0]]
        return Response({"reference_run": str(reference.id), "runs": [{
            "id": str(runs[id].id), "scenario": str(runs[id].scenario_id),
            "engine_version": runs[id].engine_version, "baseline": runs[id].result["baseline"],
            "summary": runs[id].result["summary"],
            "delta_from_reference": {key: str(Decimal(runs[id].result["summary"][key]) - Decimal(reference.result["summary"][key])) for key in metrics},
        } for id in ids]})


    @action(detail=True, methods=["get"], url_path="resource-export")
    def resource_export(self, request, pk=None):
        run = self.get_object()
        stream = io.StringIO()
        water_fields = ("opening_storage_m3", "inflow_m3", "overflow_m3", "evaporation_m3", "withdrawal_m3",
                        "closing_storage_m3", "shortfall_m3")
        labour_fields = ("required_hours", "available_hours", "shortfall_hours")
        fields = ["week", "start_date", *["water_" + name for name in water_fields],
                  *["labour_" + name for name in labour_fields], "water_check", "labour_check"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for week in run.result["weeks"]:
            resources = week.get("resources") or {}
            water, labour = resources.get("water", {}), resources.get("labour", {})
            check = lambda row: "not_assessed" if not row else "unknown" if row["capacity_met"] is None else "met" if row["capacity_met"] else "exceeded"
            writer.writerow({"week": week["week"], "start_date": week["start_date"],
                **{"water_" + key: water.get(key, "") for key in water_fields},
                **{"labour_" + key: labour.get(key, "") for key in labour_fields},
                "water_check": check(water), "labour_check": check(labour)})
        response = HttpResponse(stream.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="farmos-{run.id}-resources.csv"'
        response["X-FarmOS-Engine-Version"] = run.engine_version
        return response


def health(request):
    from django.http import JsonResponse
    return JsonResponse({"status": "ok", "engine_version": ENGINE_VERSION})

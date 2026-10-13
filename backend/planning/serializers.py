from datetime import timedelta
from decimal import Decimal
from rest_framework import serializers
from .models import Farm, Scenario, ScenarioRun


from .fields import StrictSerializer, number
from .resource_serializers import LightResponse, ResourceInputs
from .light_links import resolve_light_studies
from uuid import UUID


GROUPS = ("leafy", "fruiting", "roots", "legumes")


class BasketShares(StrictSerializer):
    leafy = number("0.25", maximum=1)
    fruiting = number("0.25", maximum=1)
    roots = number("0.25", maximum=1)
    legumes = number("0.25", maximum=1)

    def validate(self, attrs):
        if sum(attrs.values()) != Decimal(1):
            raise serializers.ValidationError("Basket shares must sum to exactly 1.")
        return attrs


class BedInput(StrictSerializer):
    id = serializers.CharField(max_length=100)
    area_m2 = number(minimum="0.0001")


class PlantingInput(StrictSerializer):
    id = serializers.CharField(max_length=100)
    bed_id = serializers.CharField(max_length=100)
    crop = serializers.CharField(max_length=100)
    crop_group = serializers.ChoiceField(choices=GROUPS)
    area_m2 = number(minimum="0.0001")
    sowing_date = serializers.DateField()
    harvest_start = serializers.DateField()
    harvest_weeks = serializers.IntegerField(min_value=1, max_value=104)
    gross_yield_kg_per_m2 = number()
    evidence = serializers.ChoiceField(choices=("user_assumption", "expert_estimate", "published", "measured", "testimonial"), default="user_assumption")
    source_note = serializers.CharField(max_length=1000, allow_blank=True, default="")
    light_response = LightResponse(required=False, allow_null=True, default=None)
    daily_water_l_per_m2 = serializers.DecimalField(max_digits=16, decimal_places=4, min_value=0, required=False, allow_null=True, default=None)
    sowing_hours_per_m2 = serializers.DecimalField(max_digits=16, decimal_places=4, min_value=0, required=False, allow_null=True, default=None)
    maintenance_hours_per_m2_week = serializers.DecimalField(max_digits=16, decimal_places=4, min_value=0, required=False, allow_null=True, default=None)
    harvest_hours_per_kg = serializers.DecimalField(max_digits=16, decimal_places=4, min_value=0, required=False, allow_null=True, default=None)


    def validate(self, attrs):
        if attrs["harvest_start"] < attrs["sowing_date"]:
            raise serializers.ValidationError("Harvest cannot start before sowing.")
        try:
            attrs["harvest_start"] + timedelta(weeks=attrs["harvest_weeks"])
        except OverflowError:
            raise serializers.ValidationError("Harvest dates exceed the supported calendar.")
        if attrs["evidence"] != "user_assumption" and not attrs["source_note"].strip():
            raise serializers.ValidationError("A source note is required for evidence other than a user assumption.")
        return attrs


class PlanningInputs(StrictSerializer):
    start_date = serializers.DateField()
    households = serializers.IntegerField(min_value=0, max_value=100000, default=50)
    basket_kg_per_week = number(8)
    monthly_price_inr = number(5500, places=2)
    combined_loss_fraction = number("0.20", maximum="0.9999")
    paid_enrollment_fraction = number(1, maximum=1)
    initial_cash_inr = number(750000, places=2)
    initial_capex_inr = number(500000, places=2)
    monthly_fixed_opex_inr = number(0, places=2)
    variable_cost_inr_per_delivered_kg = number(0, places=2)
    weekly_family_labour_hours = number(0)
    family_labour_hourly_value_inr = number(0, places=2)
    service_target_fraction = number("0.95", maximum=1)
    basket_shares = BasketShares(default=lambda: {group: "0.25" for group in GROUPS})
    resources = ResourceInputs(required=False, allow_null=True, default=None)
    beds = BedInput(many=True, default=list, max_length=1000)
    plantings = PlantingInput(many=True, default=list, max_length=1000)

    def validate(self, attrs):
        try:
            attrs["start_date"] + timedelta(weeks=104)
        except OverflowError:
            raise serializers.ValidationError("Start date exceeds the supported planning calendar.")
        beds = {bed["id"]: bed for bed in attrs["beds"]}
        if len(beds) != len(attrs["beds"]):
            raise serializers.ValidationError({"beds": "Bed IDs must be unique."})
        if len({p["id"] for p in attrs["plantings"]}) != len(attrs["plantings"]):
            raise serializers.ValidationError({"plantings": "Planting IDs must be unique."})
        for planting in attrs["plantings"]:
            if planting["bed_id"] not in beds:
                raise serializers.ValidationError({"plantings": "Every planting must reference an existing bed."})
        # Half-open occupation windows allow a new cycle exactly when the old one ends.
        for bed_id, bed in beds.items():
            events = []
            for planting in attrs["plantings"]:
                if planting["bed_id"] == bed_id:
                    end = planting["harvest_start"] + timedelta(weeks=planting["harvest_weeks"])
                    events.extend([(planting["sowing_date"], planting["area_m2"]), (end, -planting["area_m2"])])
            occupied = Decimal(0)
            for _, area in sorted(events, key=lambda event: (event[0], event[1])):
                occupied += area
                if occupied > bed["area_m2"]:
                    raise serializers.ValidationError({"plantings": f"Bed {bed_id} is overbooked. Layered yield claims are not supported yet."})
        return attrs


class FarmSerializer(serializers.ModelSerializer):
    area_acres = number(minimum="0.0001", digits=12)
    water_reliability = serializers.ChoiceField(choices=("unknown", "reliable", "seasonal", "limited"), default="unknown")

    class Meta:
        model = Farm
        fields = ("id", "name", "region", "area_acres", "water_reliability", "growing_approach", "created_at")
        read_only_fields = ("id", "created_at")


class ScenarioSerializer(serializers.ModelSerializer):
    inputs = PlanningInputs()

    class Meta:
        model = Scenario
        fields = ("id", "farm", "name", "inputs", "revision", "created_at", "updated_at")
        read_only_fields = ("id", "revision", "created_at", "updated_at")

    def validate(self, attrs):
        farm = attrs.get("farm", self.instance.farm if self.instance else None)
        inputs = attrs.get("inputs", self.instance.inputs if self.instance else None)
        if inputs and farm:
            footprint = sum(Decimal(str(bed["area_m2"])) for bed in inputs["beds"])
            if footprint > farm.area_acres * Decimal("4046.8564224"):
                raise serializers.ValidationError({"inputs": "Exclusive bed footprints exceed the farm's physical land area."})
        if inputs:
            resolve_light_studies(inputs)
        return attrs

    def create(self, validated_data):
        validated_data["inputs"] = json_values(validated_data["inputs"])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "inputs" in validated_data:
            validated_data["inputs"] = json_values(validated_data["inputs"])
        validated_data["revision"] = instance.revision + 1
        return super().update(instance, validated_data)


def json_values(value):
    """Keep exact decimals and ISO dates in persisted snapshots."""
    if isinstance(value, dict):
        return {key: json_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_values(item) for item in value]
    if isinstance(value, (Decimal, UUID)):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


class RunSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScenarioRun
        fields = ("id", "scenario", "scenario_revision", "engine_version", "assumptions_snapshot", "result", "created_at")
        read_only_fields = fields

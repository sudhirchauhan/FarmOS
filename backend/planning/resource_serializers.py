from rest_framework import serializers
from .fields import StrictSerializer, number
from .nutrient_serializers import NutrientInputs


class LightResponse(StrictSerializer):
    solar_runs = serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=4)
    point_id = serializers.CharField(max_length=100)
    minimum_dli = number()
    optimum_dli = number()
    source_note = serializers.CharField(max_length=1000)

    def validate(self, attrs):
        if attrs["optimum_dli"] <= attrs["minimum_dli"]:
            raise serializers.ValidationError("Optimum DLI must exceed minimum DLI.")
        if len(set(attrs["solar_runs"])) != len(attrs["solar_runs"]):
            raise serializers.ValidationError("Solar runs must be distinct.")
        return attrs


class WaterOverride(StrictSerializer):
    week = serializers.IntegerField(min_value=1, max_value=104)
    inflow_m3 = serializers.DecimalField(max_digits=16, decimal_places=4, min_value=0, required=False)
    evaporation_m3 = serializers.DecimalField(max_digits=16, decimal_places=4, min_value=0, required=False)


class WaterInputs(StrictSerializer):
    storage_capacity_m3 = number()
    opening_storage_m3 = number()
    weekly_inflow_m3 = number()
    weekly_evaporation_m3 = number()
    weekly_pumping_limit_m3 = number()
    irrigation_efficiency = number(minimum="0.0001", maximum=1)
    weekly_overrides = WaterOverride(many=True, default=list, max_length=104)

    def validate(self, attrs):
        if attrs["opening_storage_m3"] > attrs["storage_capacity_m3"]:
            raise serializers.ValidationError("Opening storage cannot exceed storage capacity.")
        if len({row["week"] for row in attrs["weekly_overrides"]}) != len(attrs["weekly_overrides"]):
            raise serializers.ValidationError("Override weeks must be unique.")
        return attrs


class LabourInputs(StrictSerializer):
    available_hours_per_week = number()
    fixed_hours_per_week = number(0)
    packing_hours_per_delivered_kg = number(0)
    delivery_hours_per_week = number(0)


class ResourceInputs(StrictSerializer):
    water = WaterInputs(required=False)
    labour = LabourInputs(required=False)
    nutrients = NutrientInputs(required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Enable water, labour or nutrients with explicit assumptions.")
        return attrs

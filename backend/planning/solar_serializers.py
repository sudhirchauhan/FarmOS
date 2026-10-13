from datetime import timedelta
import math
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from rest_framework import serializers
from .serializers import StrictSerializer


class FiniteFloat(serializers.FloatField):
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        if not math.isfinite(value):
            raise serializers.ValidationError("Must be finite.")
        return value


class PointInput(StrictSerializer):
    id = serializers.CharField(max_length=100)
    x = FiniteFloat(min_value=-100000, max_value=100000)
    y = FiniteFloat(min_value=-100000, max_value=100000)
    z = FiniteFloat(min_value=0, max_value=10000)
    tilt_deg = FiniteFloat(min_value=0, max_value=90, default=0)
    azimuth_deg = FiniteFloat(min_value=0, max_value=360, default=180)


class ObstacleInput(StrictSerializer):
    id = serializers.CharField(max_length=100)
    x = FiniteFloat(min_value=-100000, max_value=100000)
    y = FiniteFloat(min_value=-100000, max_value=100000)
    width = FiniteFloat(min_value=0.001, max_value=100000)
    depth = FiniteFloat(min_value=0.001, max_value=100000)
    height = FiniteFloat(min_value=0.001, max_value=10000)


class RadiationInput(StrictSerializer):
    dni_w_m2 = FiniteFloat(min_value=0, max_value=2000)
    dhi_w_m2 = FiniteFloat(min_value=0, max_value=2000)


class SolarInput(StrictSerializer):
    latitude = FiniteFloat(min_value=-90, max_value=90)
    longitude = FiniteFloat(min_value=-180, max_value=180)
    timezone = serializers.CharField(max_length=100)
    start_date = serializers.DateField()
    days = serializers.IntegerField(min_value=1, max_value=366, default=1)
    step_minutes = serializers.ChoiceField(choices=(15, 30, 60), default=60)
    altitude_m = FiniteFloat(min_value=-400, max_value=9000, default=0)
    temperature_c = FiniteFloat(min_value=-80, max_value=70, default=25)
    linke_turbidity = FiniteFloat(min_value=1, max_value=12, default=3)
    par_fraction = FiniteFloat(min_value=0, max_value=1, default=0.45)
    photon_umol_per_joule_par = FiniteFloat(min_value=0.1, max_value=10, default=4.57)
    points = PointInput(many=True, allow_empty=False, max_length=24)
    obstacles = ObstacleInput(many=True, default=list, max_length=32)
    radiation = RadiationInput(many=True, required=False, max_length=35136)
    radiation_source = serializers.CharField(max_length=1000, default="", allow_blank=True)

    def validate_timezone(self, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise serializers.ValidationError("Provide a valid IANA time zone.")
        return value

    def validate(self, attrs):
        try:
            end = attrs["start_date"] + timedelta(days=attrs["days"])
        except OverflowError:
            raise serializers.ValidationError("Date range exceeds the calendar.")
        if attrs["start_date"].year < 1900 or end.year > 2200:
            raise serializers.ValidationError("Supported date range is 1900–2200.")
        if attrs["days"] * (1440 // attrs["step_minutes"]) * len(attrs["points"]) > 250000:
            raise serializers.ValidationError("Reduce positions, date range or resolution to stay within the synchronous preview budget.")
        if "radiation" in attrs and not attrs["radiation_source"].strip():
            raise serializers.ValidationError("Describe the supplied radiation source and version.")
        for key in ("points", "obstacles"):
            if len({item["id"] for item in attrs[key]}) != len(attrs[key]):
                raise serializers.ValidationError(f"{key} IDs must be unique.")
        for point in attrs["points"]:
            for box in attrs["obstacles"]:
                if box["x"] <= point["x"] <= box["x"] + box["width"] and box["y"] <= point["y"] <= box["y"] + box["depth"] and point["z"] <= box["height"]:
                    raise serializers.ValidationError(f"Point {point['id']} is inside/on opaque obstacle {box['id']}; move it outside the surface.")
        return attrs

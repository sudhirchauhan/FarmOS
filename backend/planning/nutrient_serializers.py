from collections import defaultdict
from decimal import Decimal
from rest_framework import serializers
from .fields import StrictSerializer, number

ELEMENTS = ("n", "p", "k")


class BiomassLot(StrictSerializer):
    id = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=200)
    source_note = serializers.CharField(max_length=1000)
    source_kind = serializers.ChoiceField(choices=("purchased", "observed_crop_residue", "imported_manure", "user_estimate"))
    available_week = serializers.IntegerField(min_value=1, max_value=104)
    dry_mass_kg = number()
    n_g_per_dry_kg = serializers.DecimalField(max_digits=12, decimal_places=4, min_value=0, max_value=1000, allow_null=True, default=None)
    p_g_per_dry_kg = serializers.DecimalField(max_digits=12, decimal_places=4, min_value=0, max_value=1000, allow_null=True, default=None)
    k_g_per_dry_kg = serializers.DecimalField(max_digits=12, decimal_places=4, min_value=0, max_value=1000, allow_null=True, default=None)
    n_available_fraction = serializers.DecimalField(max_digits=5, decimal_places=4, min_value=0, max_value=1, allow_null=True, default=None)
    p_available_fraction = serializers.DecimalField(max_digits=5, decimal_places=4, min_value=0, max_value=1, allow_null=True, default=None)
    k_available_fraction = serializers.DecimalField(max_digits=5, decimal_places=4, min_value=0, max_value=1, allow_null=True, default=None)

    def validate(self, attrs):
        if sum((attrs[f"{element}_g_per_dry_kg"] or Decimal(0)) for element in ELEMENTS) > 1000:
            raise serializers.ValidationError("Known elemental N/P/K content cannot exceed total dry mass.")
        return attrs


class BiomassAllocation(StrictSerializer):
    lot_id = serializers.CharField(max_length=100)
    week = serializers.IntegerField(min_value=1, max_value=104)
    purpose = serializers.ChoiceField(choices=("compost", "mulch", "feed", "fuel", "reserve"))
    dry_mass_kg = number(minimum="0.0001")


class NutrientInputs(StrictSerializer):
    opening_n_available_kg = number()
    opening_p_available_kg = number()
    opening_k_available_kg = number()
    opening_source_note = serializers.CharField(max_length=1000)
    lots = BiomassLot(many=True, default=list, max_length=1000)
    allocations = BiomassAllocation(many=True, default=list, max_length=4000)

    def validate(self, attrs):
        lots = {lot["id"]: lot for lot in attrs["lots"]}
        if len(lots) != len(attrs["lots"]):
            raise serializers.ValidationError("Biomass lot IDs must be unique.")
        assigned = defaultdict(lambda: Decimal(0))
        for allocation in attrs["allocations"]:
            lot = lots.get(allocation["lot_id"])
            if not lot:
                raise serializers.ValidationError("Every allocation must reference an existing biomass lot.")
            if allocation["week"] < lot["available_week"]:
                raise serializers.ValidationError("Biomass cannot be allocated before it is available.")
            assigned[lot["id"]] += allocation["dry_mass_kg"]
            if assigned[lot["id"]] > lot["dry_mass_kg"]:
                raise serializers.ValidationError(f"Lot {lot['id']} is allocated more than once beyond its dry mass.")
        return attrs

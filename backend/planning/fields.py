from decimal import Decimal
from rest_framework import serializers

class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError({key: "Unknown field." for key in unknown})
        return super().to_internal_value(data)


def number(default=None, *, maximum=None, minimum=0, digits=16, places=4):
    kwargs = dict(max_digits=digits, decimal_places=places, min_value=Decimal(str(minimum)))
    if default is not None:
        kwargs["default"] = Decimal(str(default))
    if maximum is not None:
        kwargs["max_value"] = Decimal(str(maximum))
    return serializers.DecimalField(**kwargs)

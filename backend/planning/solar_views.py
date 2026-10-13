from rest_framework import mixins, serializers, status, viewsets
from rest_framework.response import Response
from .models import SolarRun
from .serializers import json_values
from .solar import SOLAR_VERSION, calculate_solar
from .solar_serializers import SolarInput


class SolarRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolarRun
        fields = ("id", "engine_version", "inputs", "result", "created_at")
        read_only_fields = fields


class SolarRunViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = SolarRun.objects.all()
    serializer_class = SolarRunSerializer

    def create(self, request):
        inputs = SolarInput(data=request.data)
        inputs.is_valid(raise_exception=True)
        try:
            result = calculate_solar(inputs.validated_data)
        except ValueError as error:
            raise serializers.ValidationError(str(error))
        run = SolarRun.objects.create(engine_version=SOLAR_VERSION, inputs=json_values(inputs.validated_data), result=result)
        return Response(self.get_serializer(run).data, status=status.HTTP_201_CREATED)

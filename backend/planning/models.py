import uuid
from django.db import models

class Farm(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    region = models.CharField(max_length=200, blank=True)
    area_acres = models.DecimalField(max_digits=12, decimal_places=4)
    water_reliability = models.CharField(max_length=20, default="unknown")
    growing_approach = models.CharField(max_length=100, default="natural")
    created_at = models.DateTimeField(auto_now_add=True)

class Scenario(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Farm, on_delete=models.PROTECT, related_name="scenarios")
    name = models.CharField(max_length=200)
    inputs = models.JSONField(default=dict)
    revision = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ScenarioRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scenario = models.ForeignKey(Scenario, on_delete=models.PROTECT, related_name="runs")
    scenario_revision = models.PositiveIntegerField()
    engine_version = models.CharField(max_length=100)
    assumptions_snapshot = models.JSONField()
    result = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)


class SolarRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    engine_version = models.CharField(max_length=100)
    inputs = models.JSONField()
    result = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

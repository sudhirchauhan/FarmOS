"""Deterministic illustrative inputs for UI mockups; never writes application data."""
import json
import os
import sys
from pathlib import Path
from datetime import date, timedelta
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from planning.engine import calculate, ENGINE_VERSION
from planning.serializers import PlanningInputs, json_values

runs = []
for index, acres in enumerate(('2', '3'), 1):
    start = date(2026, 10, 12)
    plantings = []
    for cycle in range(6):
        harvest = start + timedelta(weeks=cycle * 4)
        for group, crop in [('leafy', 'Amaranth'), ('fruiting', 'Okra'), ('roots', 'Radish'), ('legumes', 'Beans')]:
            plantings.append({'id': f'{group}-{cycle}', 'bed_id': 'annual-bed', 'crop': crop, 'crop_group': group,
                'area_m2': '200', 'sowing_date': harvest.isoformat(), 'harvest_start': harvest.isoformat(),
                'harvest_weeks': 4, 'gross_yield_kg_per_m2': '2.5' if index == 1 else '2.8',
                'evidence': 'user_assumption', 'source_note': 'Illustrative UI fixture; no validated agronomy. Zero nursery lead time for presentation only.'})
    s = PlanningInputs(data={'start_date': start.isoformat(), 'monthly_fixed_opex_inr': '95000',
        'variable_cost_inr_per_delivered_kg': '18', 'weekly_family_labour_hours': '30',
        'family_labour_hourly_value_inr': '100', 'beds': [{'id': 'annual-bed', 'area_m2': '2400'}], 'plantings': plantings,
        'initial_capex_inr': '600000' if index == 1 else '800000', 'initial_cash_inr': '900000'})
    s.is_valid(raise_exception=True)
    farm = {'id': f'00000000-0000-4000-8000-00000000000{index}', 'name': 'Sahyadri Farm · illustrative',
        'region': 'Pune, Maharashtra', 'area_acres': acres, 'water_reliability': 'seasonal', 'growing_approach': 'natural'}
    snapshot = {'farm': farm, 'inputs': json_values(s.validated_data)}
    runs.append({'id': f'10000000-0000-4000-8000-00000000000{index}', 'scenario': f'20000000-0000-4000-8000-00000000000{index}',
        'scenario_revision': 1, 'engine_version': ENGINE_VERSION, 'created_at': '2026-10-12T12:00:00Z',
        'assumptions_snapshot': snapshot, 'result': calculate(snapshot)})
print(json.dumps(runs))

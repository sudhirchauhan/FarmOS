'use client';
import NutrientEditor, { NutrientBudget, nutrientDefaults } from './nutrient-editor';

export type WaterBudget = { storage_capacity_m3: string; opening_storage_m3: string; weekly_inflow_m3: string;
  weekly_evaporation_m3: string; weekly_pumping_limit_m3: string; irrigation_efficiency: string;
  weekly_overrides: { week: number; inflow_m3?: string; evaporation_m3?: string }[] };
export type LabourBudget = { available_hours_per_week: string; fixed_hours_per_week: string;
  packing_hours_per_delivered_kg: string; delivery_hours_per_week: string };
export type ResourceBudget = { water?: WaterBudget; labour?: LabourBudget; nutrients?: NutrientBudget };
const waterDefaults: WaterBudget = { storage_capacity_m3: '100', opening_storage_m3: '50', weekly_inflow_m3: '10',
  weekly_evaporation_m3: '2', weekly_pumping_limit_m3: '20', irrigation_efficiency: '0.85', weekly_overrides: [] };
const labourDefaults: LabourBudget = { available_hours_per_week: '120', fixed_hours_per_week: '10', packing_hours_per_delivered_kg: '0.02', delivery_hours_per_week: '8' };

export default function ResourceEditor({ value, onChange }: { value: ResourceBudget | null; onChange: (value: ResourceBudget | null) => void }) {
  const budget = value || {};
  function toggle(key: 'water' | 'labour' | 'nutrients', checked: boolean) {
    const next = { ...budget };
    if (checked) { if (key === 'water') next.water = structuredClone(waterDefaults); else if (key === 'labour') next.labour = { ...labourDefaults }; else next.nutrients = structuredClone(nutrientDefaults); }
    else delete next[key];
    onChange(Object.keys(next).length ? next : null);
  }
  const waterFields: [keyof Omit<WaterBudget, 'weekly_overrides'>, string][] = [
    ['storage_capacity_m3', 'Storage capacity · m³'], ['opening_storage_m3', 'Opening storage · m³'],
    ['weekly_inflow_m3', 'Permitted inflow · m³ / week'], ['weekly_evaporation_m3', 'Evaporation · m³ / week'],
    ['weekly_pumping_limit_m3', 'Pumping limit · m³ / week'], ['irrigation_efficiency', 'Irrigation efficiency · fraction'],
  ];
  const labourFields: [keyof LabourBudget, string][] = [
    ['available_hours_per_week', 'Available person-hours / week'], ['fixed_hours_per_week', 'Fixed farm work · hours / week'],
    ['packing_hours_per_delivered_kg', 'Packing hours / delivered kg'], ['delivery_hours_per_week', 'Delivery hours / supplied week'],
  ];
  return <section className="panel"><div className="eyebrow">04 · Resource constraints</div><h2>Check water, labour and nutrient budgets</h2>
    <p className="muted">Optional budgets use visible illustrative presets. Crop requirements left blank stay unknown. Shortfalls flag infeasibility; they do not silently apply another yield penalty or hire workers.</p>
    <label className="check"><input type="checkbox" checked={!!budget.water} onChange={e => toggle('water', e.target.checked)} />Enable water budget</label>
    {budget.water && <div className="fields">{waterFields.map(([key, label]) => <label key={key}>{label}<input required type="number" min={key === 'irrigation_efficiency' ? '0.0001' : '0'} max={key === 'irrigation_efficiency' ? '1' : undefined} step="0.0001" value={budget.water![key]} onChange={e => onChange({ ...budget, water: { ...budget.water!, [key]: e.target.value } })} /></label>)}</div>}
    {budget.water && <details><summary>Seasonal weekly inflow / evaporation overrides</summary><p className="muted">Add overrides through the API with <code>weekly_overrides</code>. Any restored overrides are preserved below; clear them to return to the weekly base values.</p><pre>{JSON.stringify(budget.water.weekly_overrides, null, 2)}</pre><button type="button" className="secondary" onClick={() => onChange({ ...budget, water: { ...budget.water!, weekly_overrides: [] } })}>Clear seasonal overrides</button></details>}
    <label className="check"><input type="checkbox" checked={!!budget.labour} onChange={e => toggle('labour', e.target.checked)} />Enable labour budget</label>
    {budget.labour && <div className="fields">{labourFields.map(([key, label]) => <label key={key}>{label}<input required type="number" min="0" step="0.0001" value={budget.labour![key]} onChange={e => onChange({ ...budget, labour: { ...budget.labour!, [key]: e.target.value } })} /></label>)}</div>}
    <label className="check"><input type="checkbox" checked={!!budget.nutrients} onChange={e => toggle('nutrients', e.target.checked)} />Enable nutrient and biomass budget</label>
    {budget.nutrients && <NutrientEditor value={budget.nutrients} onChange={nutrients => onChange({ ...budget, nutrients })} />}
  </section>;
}

'use client';

import { FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import ResourceEditor, { ResourceBudget } from './resource-editor';

type Group = 'leafy' | 'fruiting' | 'roots' | 'legumes';
type LightResponse = { solar_runs: string[]; point_id: string; minimum_dli: string; optimum_dli: string; source_note: string };
type Planting = { id: string; bed_id: string; crop: string; crop_group: Group; area_m2: string;
  sowing_date: string; harvest_start: string; harvest_weeks: number; gross_yield_kg_per_m2: string;
  evidence: string; source_note: string; light_response?: LightResponse | null;
  daily_water_l_per_m2?: string | null; sowing_hours_per_m2?: string | null;
  maintenance_hours_per_m2_week?: string | null; harvest_hours_per_kg?: string | null };
type Inputs = { start_date: string; households: number; basket_kg_per_week: string; monthly_price_inr: string;
  combined_loss_fraction: string; paid_enrollment_fraction: string; initial_cash_inr: string; initial_capex_inr: string;
  monthly_fixed_opex_inr: string; variable_cost_inr_per_delivered_kg: string; weekly_family_labour_hours: string;
  family_labour_hourly_value_inr: string; service_target_fraction: string; basket_shares: Record<Group, string>;
  beds: { id: string; area_m2: string }[]; plantings: Planting[]; resources?: ResourceBudget | null };
type Resources = { water?: { opening_storage_m3: string; inflow_m3: string; closing_storage_m3: string; shortfall_m3: string; unknown_plantings: string[] };
  labour?: { required_hours: string; available_hours: string; shortfall_hours: string; unknown_plantings: string[] } };
type Farm = { id: string; name: string; region: string; area_acres: string; water_reliability: string; growing_approach: string };
type Week = { week: number; start_date: string; demand_kg: string; gross_kg: string; delivered_kg: string;
  shortfall_kg: string; closing_cash_inr: string; collections_inr: string; groups: Record<Group, Record<string, string>>; resources?: Resources | null };
type Run = { id: string; scenario: string; scenario_revision: number; created_at: string; engine_version: string;
  assumptions_snapshot: { farm: Farm; inputs: Inputs };
  result: { baseline: Record<string, string>; summary: Record<string, string | number | boolean | null>;
    weeks: Week[]; warnings: string[]; input_sha256: string; light_adjustments?: Record<string, string> } };
type Compared = { runs: { id: string; baseline: Record<string, string>; summary: Record<string, string | number | boolean | null>;
  delta_from_reference: Record<string, string> }[] };

const groups: Group[] = ['leafy', 'fruiting', 'roots', 'legumes'];
const defaultInputs: Inputs = {
  start_date: new Date().toISOString().slice(0, 10), households: 50, basket_kg_per_week: '8', monthly_price_inr: '5500',
  combined_loss_fraction: '0.20', paid_enrollment_fraction: '1', initial_cash_inr: '750000', initial_capex_inr: '500000',
  monthly_fixed_opex_inr: '0', variable_cost_inr_per_delivered_kg: '0', weekly_family_labour_hours: '0',
  family_labour_hourly_value_inr: '0', service_target_fraction: '0.95',
  basket_shares: { leafy: '0.25', fruiting: '0.25', roots: '0.25', legumes: '0.25' }, beds: [], plantings: [],
};
const defaultFarm = { name: 'My farm', region: '', area_acres: '2', water_reliability: 'unknown', growing_approach: 'natural' };
const money = (value: unknown) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(value));
const quantity = (value: unknown) => new Intl.NumberFormat('en-IN', { maximumFractionDigits: 1 }).format(Number(value));

async function api<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`/api/${path}`, body === undefined ? { cache: 'no-store' } : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(JSON.stringify(data, null, 2));
  return data as T;
}

export default function Planner() {
  const [farm, setFarm] = useState(defaultFarm);
  const [inputs, setInputs] = useState<Inputs>(defaultInputs);
  const [name, setName] = useState('Base scenario');
  const [bedArea, setBedArea] = useState('500');
  const [run, setRun] = useState<Run | null>(null);
  const [history, setHistory] = useState<Run[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [comparison, setComparison] = useState<Compared | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [savedFarm, setSavedFarm] = useState<{ signature: string; id: string } | null>(null);
  const [view, setView] = useState<'totals' | Group>('totals');

  useEffect(() => {
    api<Run[]>('scenario-runs/').then(setHistory).catch(() => setError('Could not connect to the planning API. Start the Django server and reload.'));
  }, []);

  function updateInput(key: keyof Inputs, value: string) {
    setInputs(current => ({ ...current, [key]: key === 'households' ? Number(value) : value }));
  }
  function updatePlanting(index: number, key: keyof Planting, value: string) {
    setInputs(current => ({ ...current, plantings: current.plantings.map((p, i) => i !== index ? p : {
      ...p, [key]: key === 'harvest_weeks' ? Number(value) : value,
    }) }));
  }
  function addPlanting() {
    setInputs(current => ({ ...current, plantings: [...current.plantings, {
      id: crypto.randomUUID(), bed_id: 'annual-bed', crop: '', crop_group: 'leafy', area_m2: '100',
      sowing_date: current.start_date, harvest_start: current.start_date, harvest_weeks: 4,
      gross_yield_kg_per_m2: '0', evidence: 'user_assumption', source_note: '',
    }] }));
  }
  function setLight(index: number, light: LightResponse | null) {
    setInputs(current => ({ ...current, plantings: current.plantings.map((p, i) => i === index ? { ...p, light_response: light } : p) }));
  }
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setBusy(true);
    try {
      const signature = JSON.stringify(farm);
      let farmId = savedFarm?.signature === signature ? savedFarm.id : null;
      if (!farmId) {
        const created = await api<Farm>('farms/', farm);
        farmId = created.id; setSavedFarm({ signature, id: farmId });
      }
      const payload: Inputs = { ...inputs, beds: inputs.plantings.length ? [{ id: 'annual-bed', area_m2: bedArea }] : [],
        plantings: inputs.plantings.map(p => ({ ...p, light_response: p.light_response ? { ...p.light_response,
          solar_runs: p.light_response.solar_runs.map(id => id.trim()).filter(Boolean) } : null })) };
      const scenario = await api<{ id: string }>('scenarios/', { farm: farmId, name, inputs: payload });
      const created = await api<Run>('scenario-runs/', { scenario: scenario.id });
      setRun(created); setComparison(null);
      setHistory(await api<Run[]>('scenario-runs/'));
      document.getElementById('results')?.scrollIntoView({ behavior: 'smooth' });
    } catch (error) { setError(error instanceof Error ? error.message : 'Could not save the scenario.'); }
    finally { setBusy(false); }
  }
  function useDraft(previous: Run) {
    const { id, ...details } = previous.assumptions_snapshot.farm;
    setFarm(details); setSavedFarm({ signature: JSON.stringify(details), id });
    setInputs(previous.assumptions_snapshot.inputs);
    setBedArea(previous.assumptions_snapshot.inputs.beds[0]?.area_m2 || '500');
    setName('Comparison scenario'); setRun(null); setError('');
    document.getElementById('scenario-form')?.scrollIntoView({ behavior: 'smooth' });
  }
  async function compare() {
    setError(''); setBusy(true);
    try { setComparison(await api<Compared>(`scenario-runs/comparison/?${selected.map(id => `run=${id}`).join('&')}`)); }
    catch (error) { setError(error instanceof Error ? error.message : 'Comparison failed.'); }
    finally { setBusy(false); }
  }
  const numericFields: [keyof Inputs, string, string?][] = [
    ['households', 'Households', '1'], ['basket_kg_per_week', 'Basket kg / household / week'],
    ['monthly_price_inr', 'Subscription ₹ / household / month'], ['combined_loss_fraction', 'Combined loss fraction (0–1)'],
    ['paid_enrollment_fraction', 'Fraction of subscriptions paid (0–1)'], ['initial_cash_inr', 'Available initial cash ₹'],
    ['initial_capex_inr', 'Initial CAPEX ₹'], ['monthly_fixed_opex_inr', 'Fixed operating costs ₹ / month'],
    ['variable_cost_inr_per_delivered_kg', 'Variable cost ₹ / delivered kg'], ['weekly_family_labour_hours', 'Family labour hours / week'],
    ['family_labour_hourly_value_inr', 'Family labour value ₹ / hour'], ['service_target_fraction', 'Target fully supplied weeks (0–1)'],
  ];
  return <main>
    <header><div className="brand">Farm<span>OS</span></div><Link href="/sunlight">Sunlight lab →</Link><span className="badge">Planning core · v0.1</span></header>
    <section className="hero"><div className="eyebrow">From assumptions to weekly decisions</div>
      <h1>Plan the farm.<br />See every shortfall.</h1>
      <p className="muted">Build a two-year basket and cash plan. Compare what changes, keep the assumptions, and see the weeks that need attention.</p>
    </section>
    <div className="notice"><strong>Illustrative, not validated.</strong> Link computed DLI and enable water/labour budgets to constrain assumptions. Crop response is not field-calibrated; nutrients and root competition remain unassessed. No yield multiplier is applied for vertical layers.</div>
    <form id="scenario-form" onSubmit={save}>
      <section className="panel"><div className="eyebrow">01 · Farm and scenario</div><h2>Your starting point</h2>
        <div className="fields">
          <label>Farm name<input required maxLength={200} value={farm.name} onChange={e => setFarm({ ...farm, name: e.target.value })} /></label>
          <label>Region · optional<input maxLength={200} placeholder="Unknown until supplied" value={farm.region} onChange={e => setFarm({ ...farm, region: e.target.value })} /></label>
          <label>Physical land · acres<input required type="number" min="0.0001" step="0.0001" value={farm.area_acres} onChange={e => setFarm({ ...farm, area_acres: e.target.value })} /></label>
          <label>Water reliability<select value={farm.water_reliability} onChange={e => setFarm({ ...farm, water_reliability: e.target.value })}>{['unknown', 'reliable', 'seasonal', 'limited'].map(item => <option key={item}>{item}</option>)}</select></label>
          <label>Growing approach<select value={farm.growing_approach} onChange={e => setFarm({ ...farm, growing_approach: e.target.value })}>{['natural', 'organic', 'regenerative', 'conventional', 'hybrid'].map(item => <option key={item}>{item}</option>)}</select></label>
          <label>Scenario name<input required maxLength={200} value={name} onChange={e => setName(e.target.value)} /></label>
          <label>First planning day<input required type="date" value={inputs.start_date} onChange={e => updateInput('start_date', e.target.value)} /></label>
        </div>
      </section>
      <section className="panel"><div className="eyebrow">02 · Demand and economics</div><h2>Make the assumptions visible</h2>
        <p className="muted">The 50-household preset comes from the specification. Zero operating costs mean missing assumptions, not free farming. Family labour affects economic surplus, not cash payments.</p>
        <div className="fields">{numericFields.map(([key, label, step]) => <label key={key}>{label}<input required type="number" min="0" step={step || '0.0001'} value={String(inputs[key])} onChange={e => updateInput(key, e.target.value)} /></label>)}</div>
        <details><summary>Basket category shares · fractions must total 1</summary><div className="fields">{groups.map(group => <label key={group}>{group}<input required type="number" min="0" max="1" step="0.0001" value={inputs.basket_shares[group]} onChange={e => setInputs({ ...inputs, basket_shares: { ...inputs.basket_shares, [group]: e.target.value } })} /></label>)}</div></details>
      </section>
      <section className="panel"><div className="eyebrow">03 · Optional production assumptions</div><h2>Add planting cohorts</h2>
        <p className="muted">Without cohorts, harvest is zero and the demand target remains visible. Enter assumed gross yield per crop cycle; losses are applied once. All cohorts below share one physical bed footprint. Overlapping areas cannot exceed it.</p>
        <label>Exclusive annual bed footprint · m²<input required type="number" min="0.0001" step="0.0001" value={bedArea} onChange={e => setBedArea(e.target.value)} /></label>
        {inputs.plantings.map((p, index) => <div className="cohort" key={p.id}>
          <div className="row"><h3>Cohort {index + 1}</h3><button type="button" className="remove" onClick={() => setInputs({ ...inputs, plantings: inputs.plantings.filter((_, i) => i !== index) })}>Remove cohort</button></div>
          <div className="fields">
            <label>Crop / variety<input required maxLength={100} value={p.crop} onChange={e => updatePlanting(index, 'crop', e.target.value)} /></label>
            <label>Basket group<select value={p.crop_group} onChange={e => updatePlanting(index, 'crop_group', e.target.value)}>{groups.map(group => <option key={group}>{group}</option>)}</select></label>
            <label>Occupied planting area · m²<input required type="number" min="0.0001" step="0.0001" value={p.area_m2} onChange={e => updatePlanting(index, 'area_m2', e.target.value)} /></label>
            <label>Sowing / transplant date<input required type="date" value={p.sowing_date} onChange={e => updatePlanting(index, 'sowing_date', e.target.value)} /></label>
            <label>First harvest date<input required type="date" value={p.harvest_start} onChange={e => updatePlanting(index, 'harvest_start', e.target.value)} /></label>
            <label>Harvest duration · weeks<input required type="number" min="1" max="104" step="1" value={p.harvest_weeks} onChange={e => updatePlanting(index, 'harvest_weeks', e.target.value)} /></label>
            <label>Gross cycle yield · kg / m²<input required type="number" min="0" step="0.0001" value={p.gross_yield_kg_per_m2} onChange={e => updatePlanting(index, 'gross_yield_kg_per_m2', e.target.value)} /></label>
            <label>Evidence class<select value={p.evidence} onChange={e => updatePlanting(index, 'evidence', e.target.value)}>{['user_assumption', 'expert_estimate', 'published', 'measured', 'testimonial'].map(item => <option key={item}>{item}</option>)}</select></label>
            <label>Source / assumption note<input maxLength={1000} required={p.evidence !== 'user_assumption'} value={p.source_note} onChange={e => updatePlanting(index, 'source_note', e.target.value)} /></label>
          </div>
          <details><summary>Crop light response and resource requirements</summary><p className="muted">With a light curve, gross cycle yield must be unshaded potential. The linear response is averaged over all growing days and capped at 1. Solar studies must cover sowing through harvest end; one day is never reused for other seasons.</p>
            <label className="check"><input type="checkbox" checked={!!p.light_response} onChange={e => setLight(index, e.target.checked ? { solar_runs: [], point_id: '', minimum_dli: '5', optimum_dli: '20', source_note: '' } : null)} />Link a DLI response</label>
            {p.light_response && <div className="fields">
              <label>Solar run IDs · comma separated<input required value={p.light_response.solar_runs.join(', ')} onChange={e => setLight(index, { ...p.light_response!, solar_runs: e.target.value.split(',').map(id => id.trim()) })} /></label>
              {(['point_id', 'minimum_dli', 'optimum_dli', 'source_note'] as const).map(key => <label key={key}>{({ point_id: 'Growing position ID', minimum_dli: 'Minimum DLI · mol/m²/day', optimum_dli: 'Optimum DLI · mol/m²/day', source_note: 'Light curve assumption / source' })[key]}<input required type={key.includes('dli') ? 'number' : 'text'} min="0" step="0.0001" value={p.light_response![key]} onChange={e => setLight(index, { ...p.light_response!, [key]: e.target.value })} /></label>)}
            </div>}
            <div className="fields">{([['daily_water_l_per_m2', 'Crop water · litres / m² / day'], ['sowing_hours_per_m2', 'Sowing hours / m²'], ['maintenance_hours_per_m2_week', 'Maintenance hours / m² / week'], ['harvest_hours_per_kg', 'Harvest hours / gross kg']] as const).map(([key, label]) => <label key={key}>{label}<input type="number" min="0" step="0.0001" placeholder="Unknown" value={p[key] ?? ''} onChange={e => setInputs({ ...inputs, plantings: inputs.plantings.map((row, i) => i === index ? { ...row, [key]: e.target.value || null } : row) })} /></label>)}</div>
          </details>
        </div>)}
        <div className="actions"><button type="button" className="secondary" onClick={addPlanting}>+ Add cohort</button></div>
      </section>
      <ResourceEditor value={inputs.resources || null} onChange={resources => setInputs({ ...inputs, resources })} />
      <div className="actions"><button disabled={busy} type="submit">{busy ? 'Working…' : 'Save and calculate 104 weeks'}</button><small>Each calculation saves a new scenario with its full assumptions.</small></div>
    </form>
    {error && <p role="alert" className="error">{error}</p>}
    <section id="results" aria-live="polite">
      {run && <div className="panel" style={{ marginTop: 30 }}>
        <div className="row"><div><div className="eyebrow">Saved result · provisional</div><h2>{run.assumptions_snapshot.farm.name} · {quantity(run.assumptions_snapshot.farm.area_acres)} {Number(run.assumptions_snapshot.farm.area_acres) === 1 ? 'acre' : 'acres'}</h2></div>
          <a href={`/api/scenario-runs/${run.id}/weekly-export/`}>Download weekly CSV</a></div>
        <div className="metrics">
          <div className="metric"><span>Annual delivered demand</span><strong>{quantity(run.result.baseline.annual_delivered_demand_kg)} kg</strong><span>52-week benchmark</span></div>
          <div className="metric"><span>Annual gross target</span><strong>{quantity(run.result.baseline.annual_gross_target_kg)} kg</strong><span>With one combined loss</span></div>
          <div className="metric"><span>Subscription revenue benchmark</span><strong>{money(run.result.baseline.annual_subscription_revenue_inr)}</strong><span>Annual · not guaranteed receipts</span></div>
          <div className="metric"><span>Fully supplied weeks</span><strong>{run.result.summary.fully_supplied_weeks} / 104</strong><span>Agronomic feasibility not assessed</span></div>
        </div>
        {run.assumptions_snapshot.inputs.resources && <details open><summary>Weekly water and labour constraints</summary><a href={`/api/scenario-runs/${run.id}/resource-export/`}>Download resource CSV</a><p className="muted">Water deficit weeks: {run.result.summary.water_deficit_weeks ?? 'Not assessed'} · Labour deficit weeks: {run.result.summary.labour_deficit_weeks ?? 'Not assessed'} · Capacity checks: {run.result.summary.resource_constraints_met === null ? 'Incomplete' : run.result.summary.resource_constraints_met ? 'Within stated budgets' : 'Exceeded'}</p>
          <div className="scroll"><table><thead><tr><th>Week</th><th>Opening m³</th><th>Inflow m³</th><th>Closing m³</th><th>Water shortfall m³</th><th>Required hours</th><th>Labour shortfall h</th><th>Unknown crop requirements</th></tr></thead><tbody>{run.result.weeks.map(week => <tr key={week.week}><td>{week.start_date}</td><td>{week.resources?.water?.opening_storage_m3 ?? '—'}</td><td>{week.resources?.water?.inflow_m3 ?? '—'}</td><td>{week.resources?.water?.closing_storage_m3 ?? '—'}</td><td>{week.resources?.water?.shortfall_m3 ?? '—'}</td><td>{week.resources?.labour?.required_hours ?? '—'}</td><td>{week.resources?.labour?.shortfall_hours ?? '—'}</td><td>{[...(week.resources?.water?.unknown_plantings || []), ...(week.resources?.labour?.unknown_plantings || [])].length ? 'Yes' : 'No'}</td></tr>)}</tbody></table></div>
        </details>}
        {run.result.light_adjustments && <details><summary>Applied light response factors</summary><pre>{JSON.stringify(run.result.light_adjustments, null, 2)}</pre><small>Factors above 1 are never applied. Curves are user assumptions.</small></details>}
        <div className="metrics">
          <div className="metric"><span>Delivered in 104 weeks</span><strong>{quantity(run.result.summary.delivered_kg)} kg</strong></div>
          <div className="metric"><span>Unfilled demand</span><strong>{quantity(run.result.summary.shortfall_kg)} kg</strong></div>
          <div className="metric"><span>Closing cash</span><strong>{money(run.result.summary.closing_cash_inr)}</strong></div>
          <div className="metric"><span>Additional funding needed</span><strong>{money(run.result.summary.additional_funding_required_inr)}</strong></div>
        </div>
        <details open><summary>Warnings and model boundaries</summary><ul>{run.result.warnings.map(warning => <li key={warning}>{warning}</li>)}</ul></details>
        <div className="row" style={{ margin: '24px 0 12px' }}><h3>Every week counts</h3><label>Basket group<select value={view} onChange={e => setView(e.target.value as 'totals' | Group)}><option value="totals">All groups</option>{groups.map(group => <option key={group}>{group}</option>)}</select></label></div>
        <div className="scroll"><table><thead><tr><th>Week starting</th><th>Demand kg</th><th>Gross kg</th><th>Delivered kg</th><th>Shortfall kg</th><th>Closing cash ₹</th></tr></thead>
          <tbody>{run.result.weeks.map(week => { const data = view === 'totals' ? week : week.groups[view]; return <tr key={week.week}><td>{week.start_date}</td><td>{quantity(data.demand_kg)}</td><td>{quantity(data.gross_kg)}</td><td>{quantity(data.delivered_kg)}</td><td className={Number(data.shortfall_kg) > 0 ? 'shortfall' : ''}>{quantity(data.shortfall_kg)}</td><td>{money(week.closing_cash_inr)}</td></tr>; })}</tbody></table></div>
        <details><summary>Exact saved assumptions and provenance</summary><p className="muted">Engine: {run.engine_version} · Scenario revision: {run.scenario_revision}</p><pre>{JSON.stringify(run.assumptions_snapshot, null, 2)}</pre><small>Input fingerprint: {run.result.input_sha256}</small></details>
      </div>}
    </section>
    <section className="panel" style={{ marginTop: 30 }}><div className="row"><div><div className="eyebrow">Keep alternatives visible</div><h2>Saved runs</h2></div><button type="button" className="secondary" disabled={busy || selected.length < 2} onClick={compare}>Compare selected ({selected.length}/4)</button></div>
      <p className="muted">Use a saved run as a draft to compare 1/2/3/4-acre designs. Area changes do not automatically multiply harvest.</p>
      {!history.length && <p>No runs yet. Save your first scenario above.</p>}
      {history.map(previous => <div className="history" key={previous.id}><label><input type="checkbox" checked={selected.includes(previous.id)} disabled={!selected.includes(previous.id) && selected.length >= 4} onChange={e => { setComparison(null); setSelected(e.target.checked ? [...selected, previous.id] : selected.filter(id => id !== previous.id)); }} />{previous.assumptions_snapshot.farm.name} · {previous.assumptions_snapshot.farm.area_acres} acres · {previous.assumptions_snapshot.inputs.start_date}<small>#{previous.id.slice(0, 8)}</small></label><button type="button" className="secondary" onClick={() => { setRun(previous); document.getElementById('results')?.scrollIntoView({ behavior: 'smooth' }); }}>View</button><button type="button" className="secondary" onClick={() => useDraft(previous)}>Use as draft</button></div>)}
      {comparison && <div className="scroll" style={{ marginTop: 20 }}><table><thead><tr><th>Run / acres</th><th>Delivered kg</th><th>Δ delivered kg</th><th>Shortfall kg</th><th>Closing cash</th><th>Δ closing cash</th></tr></thead><tbody>{comparison.runs.map(item => <tr key={item.id}><td>#{item.id.slice(0, 8)} / {quantity(Number(item.baseline.physical_area_m2) / 4046.8564224)}</td><td>{quantity(item.summary.delivered_kg)}</td><td>{quantity(item.delta_from_reference.delivered_kg)}</td><td>{quantity(item.summary.shortfall_kg)}</td><td>{money(item.summary.closing_cash_inr)}</td><td>{money(item.delta_from_reference.closing_cash_inr)}</td></tr>)}</tbody></table><p className="muted">Deltas use the first selected run as the reference. Compare matching dates and assumptions for meaningful results.</p></div>}
    </section>
    <footer>FarmOS · Planning before promises. Authentication and team access are deferred; this is a local prototype.</footer>
  </main>;
}

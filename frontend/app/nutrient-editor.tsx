'use client';

export type BiomassLot = { id: string; name: string; source_kind: string; source_note: string;
  available_week: number; dry_mass_kg: string; n_g_per_dry_kg: string | null; p_g_per_dry_kg: string | null;
  k_g_per_dry_kg: string | null; n_available_fraction: string | null; p_available_fraction: string | null; k_available_fraction: string | null };
export type Allocation = { lot_id: string; week: number; purpose: string; dry_mass_kg: string };
export type NutrientBudget = { opening_n_available_kg: string; opening_p_available_kg: string; opening_k_available_kg: string;
  opening_source_note: string; lots: BiomassLot[]; allocations: Allocation[] };
export const nutrientDefaults: NutrientBudget = { opening_n_available_kg: '0', opening_p_available_kg: '0', opening_k_available_kg: '0',
  opening_source_note: '', lots: [], allocations: [] };

export default function NutrientEditor({ value, onChange }: { value: NutrientBudget; onChange: (value: NutrientBudget) => void }) {
  function updateLot(index: number, key: keyof BiomassLot, text: string) {
    onChange({ ...value, lots: value.lots.map((lot, i) => i !== index ? lot : { ...lot,
      [key]: key === 'available_week' ? Number(text) : (key.endsWith('_fraction') || key.endsWith('_dry_kg')) && !text ? null : text }) });
  }
  function addLot() {
    onChange({ ...value, lots: [...value.lots, { id: crypto.randomUUID(), name: '', source_kind: 'user_estimate', source_note: '',
      available_week: 1, dry_mass_kg: '100', n_g_per_dry_kg: null, p_g_per_dry_kg: null, k_g_per_dry_kg: null,
      n_available_fraction: null, p_available_fraction: null, k_available_fraction: null }] });
  }
  return <div><p className="muted">Use dry mass and elemental N/P/K, not slurry volume or P₂O₅/K₂O equivalents. Blank composition and availability stay unknown. Compost credit is assumed available in its allocation week; maturation and mineralization are not modeled.</p>
    <div className="fields">{(['n', 'p', 'k'] as const).map(element => <label key={element}>Opening available {element.toUpperCase()} · kg<input required type="number" min="0" step="0.0001" value={value[`opening_${element}_available_kg`]} onChange={e => onChange({ ...value, [`opening_${element}_available_kg`]: e.target.value })} /></label>)}
      <label>Opening nutrient source / assumption<input required maxLength={1000} value={value.opening_source_note} onChange={e => onChange({ ...value, opening_source_note: e.target.value })} /></label>
    </div>
    <h3 style={{ marginTop: 24 }}>Dry-biomass batches</h3>
    {value.lots.map((lot, index) => <div className="cohort biomass-lot" key={lot.id}><div className="row"><h3>Batch {index + 1}</h3><button type="button" className="remove" onClick={() => onChange({ ...value, lots: value.lots.filter(row => row.id !== lot.id), allocations: value.allocations.filter(row => row.lot_id !== lot.id) })}>Remove batch and its allocations</button></div>
      <div className="fields">
        <label>Feedstock name<input required maxLength={200} value={lot.name} onChange={e => updateLot(index, 'name', e.target.value)} /></label>
        <label>Feedstock source<select value={lot.source_kind} onChange={e => updateLot(index, 'source_kind', e.target.value)}>{['user_estimate', 'purchased', 'observed_crop_residue', 'imported_manure'].map(kind => <option key={kind}>{kind}</option>)}</select></label>
        <label>Feedstock source note<input required maxLength={1000} value={lot.source_note} onChange={e => updateLot(index, 'source_note', e.target.value)} /></label>
        <label>Available from week<input required type="number" min="1" max="104" step="1" value={lot.available_week} onChange={e => updateLot(index, 'available_week', e.target.value)} /></label>
        <label>Batch dry mass · kg<input required type="number" min="0" step="0.0001" value={lot.dry_mass_kg} onChange={e => updateLot(index, 'dry_mass_kg', e.target.value)} /></label>
        {(['n', 'p', 'k'] as const).flatMap(element => [<label key={`${element}-content`}>{element.toUpperCase()} content · g / dry kg<input type="number" min="0" max="1000" step="0.0001" placeholder="Unknown" value={lot[`${element}_g_per_dry_kg`] ?? ''} onChange={e => updateLot(index, `${element}_g_per_dry_kg`, e.target.value)} /></label>,
          <label key={`${element}-available`}>{element.toUpperCase()} available fraction<input type="number" min="0" max="1" step="0.0001" placeholder="Unknown" value={lot[`${element}_available_fraction`] ?? ''} onChange={e => updateLot(index, `${element}_available_fraction`, e.target.value)} /></label>])}
      </div></div>)}
    <div className="actions"><button className="secondary" type="button" onClick={addLot}>+ Add biomass batch</button></div>
    <h3 style={{ marginTop: 24 }}>Exclusive biomass allocations</h3><p className="muted">Total allocations cannot exceed a batch's dry mass. Reserve is earmarked stock, not simultaneously available elsewhere. Only compost receives nutrient credit.</p>
    {value.allocations.map((allocation, index) => <div className="cohort biomass-allocation" key={index}><div className="fields">
      <label>Allocation batch<select value={allocation.lot_id} onChange={e => onChange({ ...value, allocations: value.allocations.map((row, i) => i === index ? { ...row, lot_id: e.target.value } : row) })}>{value.lots.map(lot => <option key={lot.id} value={lot.id}>{lot.name || lot.id.slice(0, 8)}</option>)}</select></label>
      <label>Allocation purpose<select value={allocation.purpose} onChange={e => onChange({ ...value, allocations: value.allocations.map((row, i) => i === index ? { ...row, purpose: e.target.value } : row) })}>{['compost', 'mulch', 'feed', 'fuel', 'reserve'].map(purpose => <option key={purpose}>{purpose}</option>)}</select></label>
      <label>Allocation week<input required type="number" min="1" max="104" step="1" value={allocation.week} onChange={e => onChange({ ...value, allocations: value.allocations.map((row, i) => i === index ? { ...row, week: Number(e.target.value) } : row) })} /></label>
      <label>Allocation dry mass · kg<input required type="number" min="0.0001" step="0.0001" value={allocation.dry_mass_kg} onChange={e => onChange({ ...value, allocations: value.allocations.map((row, i) => i === index ? { ...row, dry_mass_kg: e.target.value } : row) })} /></label>
    </div><button type="button" className="remove" onClick={() => onChange({ ...value, allocations: value.allocations.filter((_, i) => i !== index) })}>Remove allocation</button></div>)}
    <div className="actions"><button disabled={!value.lots.length} className="secondary" type="button" onClick={() => onChange({ ...value, allocations: [...value.allocations, { lot_id: value.lots[0].id, week: value.lots[0].available_week, purpose: 'compost', dry_mass_kg: '1' }] })}>+ Allocate biomass</button></div>
  </div>;
}

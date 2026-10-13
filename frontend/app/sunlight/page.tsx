'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';

type Position = { id: string; x: number; y: number; z: number; tilt_deg: number; azimuth_deg: number };
type Box = { id: string; x: number; y: number; width: number; depth: number; height: number };
type Sample = { interval_start: string; midpoint: string; interval_seconds: number; sun_elevation_deg: number;
  sun_azimuth_deg: number; direct_shaded: boolean; direct_w_m2: number; diffuse_w_m2: number; par_umol_m2_s: number };
type PointResult = { id: string; diffuse_visibility_fraction: number;
  daily: { date: string; dli_mol_m2_day: number; direct_shade_hours: number }[]; samples: Sample[] };
type Inputs = { latitude: number; longitude: number; timezone: string; start_date: string; days: number;
  step_minutes: number; altitude_m: number; temperature_c: number; linke_turbidity: number;
  par_fraction: number; photon_umol_per_joule_par: number; points: Position[]; obstacles: Box[] };
type Run = { id: string; inputs: Inputs & { radiation?: { dni_w_m2: number; dhi_w_m2: number }[]; radiation_source?: string }; result: { engine_version: string; pvlib_version: string; radiation_source: string;
  points: PointResult[]; warnings: string[]; input_sha256: string } };

const preset: Inputs = { latitude: 18.52, longitude: 73.86, timezone: 'Asia/Kolkata', start_date: '2026-12-21', days: 1,
  step_minutes: 60, altitude_m: 560, temperature_c: 25, linke_turbidity: 3, par_fraction: 0.45, photon_umol_per_joule_par: 4.57,
  points: [{ id: 'Open bed', x: -3, y: -3, z: 0, tilt_deg: 0, azimuth_deg: 180 },
    { id: 'Upper south face', x: 0, y: -0.501, z: 2, tilt_deg: 90, azimuth_deg: 180 },
    { id: 'Lower north face', x: 0, y: 0.501, z: 0.3, tilt_deg: 90, azimuth_deg: 0 },
    { id: 'Ground north of tower', x: 0, y: 1.8, z: 0, tilt_deg: 0, azimuth_deg: 180 }],
  obstacles: [{ id: 'Opaque tower', x: -0.5, y: -0.5, width: 1, depth: 1, height: 1.8 }],
};

function hull(points: number[][]) {
  const sorted = points.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cross = (a: number[], b: number[], c: number[]) => (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
  const chain = (data: number[][]) => { const out: number[][] = []; for (const p of data) { while (out.length >= 2 && cross(out[out.length - 2], out[out.length - 1], p) <= 0) out.pop(); out.push(p); } return out; };
  return [...chain(sorted).slice(0, -1), ...chain([...sorted].reverse()).slice(0, -1)];
}

export default function Sunlight() {
  const [inputs, setInputs] = useState(preset);
  const [geometry, setGeometry] = useState(JSON.stringify({ points: preset.points, obstacles: preset.obstacles }, null, 2));
  const [run, setRun] = useState<Run | null>(null);
  const [index, setIndex] = useState(12);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [radiation, setRadiation] = useState('');
  const [source, setSource] = useState('');
  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get('run');
    if (!id) return;
    setBusy(true);
    fetch(`/api/solar-runs/${encodeURIComponent(id)}/`).then(async response => {
      if (!response.ok) throw new Error('Saved sunlight run could not be loaded.');
      const data: Run = await response.json();
      const { radiation, radiation_source, ...settings } = data.inputs;
      setRun(data); setInputs(settings);
      setGeometry(JSON.stringify({ points: settings.points, obstacles: settings.obstacles }, null, 2));
      setRadiation(radiation ? JSON.stringify(radiation, null, 2) : ''); setSource(radiation_source || '');
      setIndex(Math.min(12, data.result.points[0].samples.length - 1));
    }).catch(error => setError(error.message)).finally(() => setBusy(false));
  }, []);
  const numeric: [keyof Inputs, string, string, string][] = [
    ['latitude', 'Latitude · degrees north', '-90', '90'], ['longitude', 'Longitude · degrees east', '-180', '180'],
    ['altitude_m', 'Altitude · m', '-400', '9000'], ['temperature_c', 'Temperature · °C', '-80', '70'],
    ['linke_turbidity', 'Assumed Linke turbidity', '1', '12'], ['par_fraction', 'PAR fraction of irradiance', '0', '1'],
    ['photon_umol_per_joule_par', 'Photons · µmol per joule PAR', '0.1', '10'],
  ];
  async function calculate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setBusy(true);
    try {
      const shape = JSON.parse(geometry);
      const payload = { ...inputs, points: shape.points, obstacles: shape.obstacles,
        ...(radiation.trim() ? { radiation: JSON.parse(radiation), radiation_source: source } : {}) };
      const response = await fetch('/api/solar-runs/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const data = await response.json();
      if (!response.ok) throw new Error(JSON.stringify(data, null, 2));
      setRun(data); setIndex(Math.min(12, data.result.points[0].samples.length - 1));
      window.history.replaceState(null, '', `/sunlight?run=${data.id}`);
    } catch (error) { setError(error instanceof Error ? error.message : 'Solar run failed.'); }
    finally { setBusy(false); }
  }
  const sample = run?.result.points[0].samples[index];
  const day = sample?.interval_start.slice(0, 10);
  const scene = run?.inputs || inputs;
  const xs = [...scene.points.map(point => point.x), ...scene.obstacles.flatMap(box => [box.x, box.x + box.width])];
  const ys = [...scene.points.map(point => point.y), ...scene.obstacles.flatMap(box => [box.y, box.y + box.depth])];
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
  const scale = Math.min(560 / Math.max(10, maxX - minX + 4), 290 / Math.max(10, maxY - minY + 4));
  const sx = (x: number) => 350 + (x - (minX + maxX) / 2) * scale;
  const sy = (y: number) => 215 - (y - (minY + maxY) / 2) * scale;
  const gridUnit = Math.max(1, 10 ** Math.floor(Math.log10(Math.max(maxX - minX, maxY - minY, 10) / 10)));
  const az = (sample?.sun_azimuth_deg || 0) * Math.PI / 180;
  const elevation = (sample?.sun_elevation_deg || 0) * Math.PI / 180;
  return <main>
    <header><div className="brand">Farm<span>OS</span></div><Link href="/">← Planning core</Link></header>
    <div className="hero"><div className="eyebrow">Solar calculation slice</div><h1>Follow the light.</h1><p className="muted">Compute solar geometry, obstacle shading and position-level PAR/DLI. Compare real orientations before assigning any yield response.</p></div>
    <div className="notice"><strong>Provisional light model.</strong> Clear sky is the default, not observed weather. No crop yield, canopy transmission or farm feasibility is inferred.</div>
    <form onSubmit={calculate}>
      <section className="panel"><h2>Site and radiation assumptions</h2><div className="fields">
        {numeric.map(([key, label, min, max]) => <label key={key}>{label}<input required type="number" step="any" min={min} max={max} value={Number(inputs[key])} onChange={e => setInputs({ ...inputs, [key]: Number(e.target.value) })} /></label>)}
        <label>IANA time zone<input required value={inputs.timezone} onChange={e => setInputs({ ...inputs, timezone: e.target.value })} /></label>
        <label>First local day<input required type="date" value={inputs.start_date} onChange={e => setInputs({ ...inputs, start_date: e.target.value })} /></label>
        <label>Number of days<input required type="number" min="1" max="366" step="1" value={inputs.days} onChange={e => setInputs({ ...inputs, days: Number(e.target.value) })} /></label>
        <label>Time step · minutes<select value={inputs.step_minutes} onChange={e => setInputs({ ...inputs, step_minutes: Number(e.target.value) })}>{[60, 30, 15].map(step => <option key={step}>{step}</option>)}</select></label>
      </div><details><summary>Use supplied direct/diffuse radiation</summary><p>Supply one midpoint sample per interval, each with <code>dni_w_m2</code> and <code>dhi_w_m2</code>. Hourly days have 24 samples except daylight-saving transitions. Leave empty to use modeled clear sky.</p>
        <label>Source and version<input value={source} onChange={e => setSource(e.target.value)} /></label>
        <label>Radiation sample array<textarea rows={5} value={radiation} onChange={e => setRadiation(e.target.value)} placeholder='[{"dni_w_m2": 0, "dhi_w_m2": 0}, ...]' /></label>
      </details></section>
      <section className="panel"><h2>Growing positions and obstacles</h2><p className="muted">Local coordinates in metres: x east, y north, z up. Obstacles are opaque boxes rooted at ground level. Tilt 0° is horizontal; 90° is vertical. Surface azimuth is clockwise from true north. Positions must sit outside obstacle surfaces.</p>
        <label>Scene JSON<textarea required rows={12} value={geometry} onChange={e => setGeometry(e.target.value)} /></label>
        <div className="actions"><button type="submit" disabled={busy}>{busy ? 'Computing light…' : 'Calculate and save light budget'}</button><small>Saved results are immutable. Inputs are not linked to crop yield yet.</small></div>
      </section>
    </form>
    {error && <p className="error" role="alert">{error}</p>}
    {run && sample && <section className="panel" id="solar-results" aria-live="polite"><div className="row"><h2>Computed light budget</h2><span className="badge">Provisional · {day}</span></div>
      <p className="muted">Radiation: {run.result.radiation_source}</p>
      <div className="metrics">{run.result.points.map(point => { const daily = point.daily.find(d => d.date === day); return <div className="metric" key={point.id}><span>{point.id}</span><strong>{daily?.dli_mol_m2_day.toFixed(2)}</strong><span>mol photons/m²/day · DLI<br />Direct shade: {daily?.direct_shade_hours} h<br />Diffuse visibility: {(point.diffuse_visibility_fraction * 100).toFixed(0)}%</span></div>; })}</div>
      <label>Simulation interval · {sample.midpoint}<input aria-label="Simulation interval" type="range" min="0" max={run.result.points[0].samples.length - 1} step="1" value={index} onChange={e => setIndex(Number(e.target.value))} /></label>
      <div className="row"><span>Sun elevation: {sample.sun_elevation_deg.toFixed(1)}°</span><span>Azimuth: {sample.sun_azimuth_deg.toFixed(1)}° clockwise from north</span></div>
      <svg viewBox="0 0 700 430" role="img" aria-label="Computed ground-plane obstacle shadows and growing positions" style={{ width: '100%', background: '#edf2e3', borderRadius: 12, marginTop: 16 }}>
        <defs><clipPath id="scene-clip"><rect x="0" y="0" width="700" height="430" /></clipPath></defs>
        <g clipPath="url(#scene-clip)">
          {Array.from({ length: 41 }, (_, i) => <path key={i} d={`M${sx(Math.floor(minX / gridUnit) * gridUnit + (i - 10) * gridUnit)} 0V430 M0 ${sy(Math.floor(minY / gridUnit) * gridUnit + (i - 10) * gridUnit)}H700`} stroke="#d5dfc8" />)}
          {run.inputs.obstacles.map(box => { const base = [[box.x, box.y], [box.x + box.width, box.y], [box.x, box.y + box.depth], [box.x + box.width, box.y + box.depth]];
            const length = elevation > 0 ? box.height / Math.tan(elevation) : 0;
            const shadow = hull([...base, ...base.map(([x, y]) => [x - length * Math.sin(az), y - length * Math.cos(az)])]);
            return <g key={box.id}>{elevation > 0 && <polygon points={shadow.map(([x, y]) => `${sx(x)},${sy(y)}`).join(' ')} fill="#556448" opacity="0.27" />}<rect x={sx(box.x)} y={sy(box.y + box.depth)} width={box.width * scale} height={box.depth * scale} fill="#759958" /><text x={sx(box.x) + 8} y={sy(box.y + box.depth) - 12} fill="#24452e">{box.id}</text></g>; })}
          {run.inputs.points.map(point => { const result = run.result.points.find(p => p.id === point.id)!; const value = result.samples[index]; return <g key={point.id}><circle cx={sx(point.x)} cy={sy(point.y)} r={7} fill={value.direct_shaded ? '#c58c46' : '#28664a'} stroke="white" strokeWidth="2" /><text x={sx(point.x) + 12} y={sy(point.y) + 18} fill="#24452e">{point.id}: {value.par_umol_m2_s.toFixed(0)} µmol/m²/s</text></g>; })}
          <text x="20" y="30" fill="#355636">N ↑ · E → · grid {gridUnit} m</text><text x="20" y="407" fill="#657359">Ground-plane shadows. Position calculations also account for z, tilt and surface azimuth.</text>
        </g>
      </svg>
      <div className="scroll"><table><thead><tr><th>Position</th><th>Direct W/m²</th><th>Diffuse W/m²</th><th>PAR µmol/m²/s</th><th>Direct shaded?</th></tr></thead><tbody>{run.result.points.map(point => { const value = point.samples[index]; return <tr key={point.id}><td>{point.id}</td><td>{value.direct_w_m2.toFixed(1)}</td><td>{value.diffuse_w_m2.toFixed(1)}</td><td>{value.par_umol_m2_s.toFixed(1)}</td><td>{value.direct_shaded ? 'Yes' : 'No'}</td></tr>; })}</tbody></table></div>
      <details><summary>Daily DLI across the selected date range</summary><div className="scroll"><table><thead><tr><th>Local date</th>{run.result.points.map(point => <th key={point.id}>{point.id}</th>)}</tr></thead><tbody>{run.result.points[0].daily.map((day, i) => <tr key={day.date}><td>{day.date}</td>{run.result.points.map(point => <td key={point.id}>{point.daily[i].dli_mol_m2_day.toFixed(3)}</td>)}</tr>)}</tbody></table></div></details>
      <details open><summary>Model limits and provenance</summary><ul>{run.result.warnings.map(warning => <li key={warning}>{warning}</li>)}</ul><p>Engine {run.result.engine_version} · pvlib {run.result.pvlib_version} · Run {run.id}</p><small>Input fingerprint: {run.result.input_sha256}</small><pre>{JSON.stringify(run.inputs, null, 2)}</pre></details>
    </section>}
  </main>;
}

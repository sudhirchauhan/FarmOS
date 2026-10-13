import { chromium } from 'playwright';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
const out = resolve('../docs/mockups');
const frames = '/tmp/farmos-mock-frames';
mkdirSync(out, { recursive: true }); mkdirSync(frames, { recursive: true });
const runs = JSON.parse(execFileSync('../.venv/bin/python', ['../backend/scripts/mockup_data.py'], { encoding: 'utf8' }));
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || (existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined) });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
await page.route('**/api/scenario-runs/**', async route => {
  const url = new URL(route.request().url());
  if (url.pathname.includes('comparison')) {
    const selected = url.searchParams.getAll('run').map(id => runs.find(run => run.id === id));
    const reference = selected[0];
    await route.fulfill({ json: { reference_run: reference.id, runs: selected.map(run => ({
      id: run.id, baseline: run.result.baseline, summary: run.result.summary,
      delta_from_reference: Object.fromEntries(['delivered_kg', 'shortfall_kg', 'closing_cash_inr', 'additional_funding_required_inr'].map(key => [key, String(Number(run.result.summary[key]) - Number(reference.result.summary[key]))])),
    })) } });
  } else await route.fulfill({ json: runs });
});
await page.goto(process.env.FARMOS_E2E_URL || 'http://127.0.0.1:3000');
await page.getByRole('button', { name: 'Use as draft' }).first().click();
await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
await page.waitForTimeout(500);
await page.screenshot({ path: `${out}/01-farm-setup.jpg`, type: 'jpeg', quality: 90, animations: 'disabled' });
await page.setViewportSize({ width: 1200, height: 850 });
await page.screenshot({ path: `${frames}/01.png`, animations: 'disabled' });
await page.locator('.cohort').first().scrollIntoViewIfNeeded();
await page.screenshot({ path: `${frames}/02.png`, animations: 'disabled' });
await page.getByRole('button', { name: 'View', exact: true }).first().click();
const results = page.locator('#results .panel');
await results.waitFor();
await page.setViewportSize({ width: 1440, height: 1000 });
await results.screenshot({ path: `${out}/02-weekly-plan.jpg`, type: 'jpeg', quality: 90, animations: 'disabled' });
await page.setViewportSize({ width: 1200, height: 850 });
await page.evaluate(() => window.scrollTo({ top: document.getElementById('results').offsetTop, behavior: 'instant' }));
await page.waitForTimeout(500);
await page.screenshot({ path: `${frames}/03.png`, animations: 'disabled' });
await page.getByRole('checkbox').nth(0).check();
await page.getByRole('checkbox').nth(1).check();
await page.getByRole('button', { name: 'Compare selected (2/4)' }).click();
await page.getByRole('columnheader', { name: 'Δ delivered kg' }).waitFor();
const comparison = page.locator('section.panel').last();
await page.setViewportSize({ width: 1440, height: 1000 });
await comparison.screenshot({ path: `${out}/03-scenario-comparison.jpg`, type: 'jpeg', quality: 90, animations: 'disabled' });
await page.setViewportSize({ width: 1200, height: 850 });
await comparison.scrollIntoViewIfNeeded();
await page.screenshot({ path: `${frames}/04.png`, animations: 'disabled' });
await page.setViewportSize({ width: 390, height: 844 });
await page.evaluate(() => window.scrollTo({ top: document.getElementById('results').offsetTop, behavior: 'instant' }));
await page.screenshot({ path: `${out}/04-mobile-results.jpg`, type: 'jpeg', quality: 90, animations: 'disabled' });
await browser.close();
execFileSync('ffmpeg', ['-y', '-framerate', '1/2', '-start_number', '1', '-i', `${frames}/%02d.png`,
  '-filter_complex', 'fps=8,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse',
  '-loop', '0', `${out}/planning-walkthrough.gif`], { stdio: ['ignore', 'ignore', 'pipe'] });
console.log('Saved four JPG mockups and planning-walkthrough.gif to docs/mockups.');

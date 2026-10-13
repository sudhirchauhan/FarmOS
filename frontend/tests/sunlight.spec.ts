import { expect, test } from '@playwright/test';

test('compute position-level light and inspect persisted hourly results', async ({ page, request }) => {
  await page.goto('/sunlight');
  await expect(page.getByRole('heading', { name: 'Follow the light.' })).toBeVisible();
  const created = page.waitForResponse(response => response.url().includes('/api/solar-runs/') && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Calculate and save light budget' }).click();
  const response = await created;
  expect(response.status()).toBe(201);
  const data = await response.json();
  await expect(page.getByRole('heading', { name: 'Computed light budget' })).toBeVisible();
  const points = data.result.points;
  expect(points).toHaveLength(4);
  expect(points[1].daily[0].dli_mol_m2_day).toBeGreaterThan(points[2].daily[0].dli_mol_m2_day);
  expect(points[0].daily[0].dli_mol_m2_day).toBeGreaterThan(points[3].daily[0].dli_mol_m2_day);
  await page.getByRole('slider', { name: 'Simulation interval', exact: true }).fill('0');
  await expect(page.locator('#solar-results tbody').first()).toContainText('0.0');
  await expect(page.getByRole('img', { name: 'Computed ground-plane obstacle shadows and growing positions' })).toBeVisible();
  const saved = await request.get(`/api/solar-runs/${data.id}/`);
  expect(saved.status()).toBe(200);
  expect((await saved.json()).result.input_sha256).toBe(data.result.input_sha256);
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Computed light budget' })).toBeVisible();
  await expect(page.locator('#solar-results')).toContainText(data.id);
  await expect(page.locator('.error[role="alert"]')).toHaveCount(0);
});

test('invalid time zone produces a visible validation error', async ({ page }) => {
  await page.goto('/sunlight');
  await page.getByLabel('IANA time zone').fill('Invalid/Zone');
  await page.getByRole('button', { name: 'Calculate and save light budget' }).click();
  await expect(page.locator('.error[role="alert"]')).toContainText('valid IANA');
});

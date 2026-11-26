import { test, expect } from '@playwright/test';
import fs from 'node:fs';

const EMAIL = process.env.E2E_EMAIL;
const PASSWORD = process.env.E2E_PASSWORD;
const SCAN = process.env.E2E_SCAN; // path to an angiogram image, only for the full workflow test

test.skip(!EMAIL || !PASSWORD, 'set E2E_EMAIL and E2E_PASSWORD');

async function login(page) {
  await page.goto('/login');
  await page.getByPlaceholder('you@hospital.org').fill(EMAIL);
  await page.getByPlaceholder('Enter your password').fill(PASSWORD);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/\/dashboard/);
  await expect(page.getByRole('heading', { name: 'Case Management' })).toBeVisible();
}

async function expectDownload(page, buttonName, ext) {
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('button', { name: buttonName, exact: true }).first().click(),
  ]);
  expect(download.suggestedFilename()).toMatch(new RegExp(`^report_.*\\.${ext}$`));
  const file = await download.path();
  expect(fs.statSync(file).size).toBeGreaterThan(200);
  if (ext === 'pdf') {
    expect(fs.readFileSync(file).subarray(0, 4).toString()).toBe('%PDF');
  }
}

test.describe('Browser tests on the real app', () => {
  test('a wrong password shows an error and stays on the login page', async ({ page }) => {
    await page.goto('/login');
    await page.getByPlaceholder('you@hospital.org').fill(EMAIL);
    await page.getByPlaceholder('Enter your password').fill('definitely-wrong-password');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByText('Incorrect email or password.')).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test('pages that need a login redirect to the login page', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
    await page.goto('/cases/1/analysis');
    await expect(page).toHaveURL(/\/login/);
  });

  test('login, case list and sidebar navigation', async ({ page }) => {
    await login(page);
    await expect(page.getByText('Total cases')).toBeVisible();
    await expect(page.locator('tbody tr').first()).toBeVisible();

    await page.getByRole('button', { name: 'Segmentation' }).click();
    await expect(page.getByText(/Artery segmentation: model comparison/)).toBeVisible();
    await expect(page.getByText('Attention U-Net (artery)')).toBeVisible();

    await page.getByRole('button', { name: 'Stenosis', exact: true }).click();
    await expect(page.getByText(/Stenosis segmentation: model comparison/)).toBeVisible();
    await expect(page.getByText(/Stenosis classifier performance/)).toBeVisible();

    await page.getByRole('button', { name: 'Reports' }).click();
    await expect(page.getByText('Open or download the analysis report of a case')).toBeVisible();
  });

  test('downloads the PDF, CSV and JSON report from the Reports tab', async ({ page }) => {
    test.setTimeout(300_000); // the first report of a case can run the pipeline
    await login(page);
    await page.getByRole('button', { name: 'Reports' }).click();
    await expectDownload(page, 'PDF', 'pdf');
    await expectDownload(page, 'CSV', 'csv');
    await expectDownload(page, 'JSON', 'json');
  });

  test('opens the case results page and shows every section', async ({ page }) => {
    test.setTimeout(300_000);
    await login(page);
    await page.getByRole('button', { name: 'Reports' }).click();
    await page.getByRole('button', { name: 'Open', exact: true }).first().click();
    await expect(page).toHaveURL(/\/cases\/\d+\/analysis/);
    await expect(page.getByRole('heading', { name: /stenosis analysis/ })).toBeVisible();

    for (const section of [
      '1. Pipeline stages',
      '2. Segmentation',
      '3. Stenosis detection',
      '6. Model performance',
      '7. Model comparison',
    ]) {
      await expect(page.getByRole('heading', { name: section })).toBeVisible({ timeout: 120_000 });
    }
    await expect(page.getByRole('button', { name: 'Artery', exact: true })).toBeVisible();

    await expectDownload(page, 'PDF', 'pdf');
  });

  test('logout returns to the login page and blocks the dashboard', async ({ page }) => {
    await login(page);
    await page.getByRole('button', { name: 'Logout' }).click();
    await expect(page).toHaveURL(/\/login/);
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });
});

// Optional: the whole workflow on a NEW case (creates it, then deletes it again).
// Needs: $env:E2E_FULL="1" and $env:E2E_SCAN="D:\path\to\an-angiogram.png"
test.describe('Full workflow on a new case', () => {
  test.skip(process.env.E2E_FULL !== '1' || !SCAN, 'set E2E_FULL=1 and E2E_SCAN=<path to an angiogram>');
  test.setTimeout(10 * 60 * 1000);

  test('create, upload, preprocess, segment, pipeline, report, delete', async ({ page }) => {
    const PID = `e2e-browser-${Date.now()}`;
    await login(page);

    // 1. create the case
    await page.getByRole('button', { name: '+ New Case' }).click();
    await page.getByLabel('Patient ID *').fill(PID);
    await page.getByLabel('Age', { exact: true }).fill('50');
    await page.getByRole('button', { name: 'Create case' }).click();
    const row = page.getByRole('row', { name: new RegExp(PID) });
    await expect(row).toBeVisible();

    // 2. upload the scan
    await row.locator('input[type="file"]').setInputFiles(SCAN);
    await expect(row.getByText('Replace scan')).toBeVisible();

    // 3. preprocessing
    await row.getByRole('button', { name: 'Preprocess' }).click();
    await expect(page.getByText('Preprocessing pipeline')).toBeVisible();
    await page.getByRole('button', { name: 'Close' }).click();

    // 4. artery segmentation
    await row.getByRole('button', { name: 'Segment', exact: true }).click();
    await expect(page.getByText('Segmentation result (Artery)')).toBeVisible({ timeout: 180_000 });
    await page.getByRole('button', { name: 'Close' }).click();

    // 5. stenosis pipeline
    await page.getByRole('button', { name: 'Stenosis', exact: true }).click();
    const stenosisRow = page.getByRole('row', { name: new RegExp(PID) });
    await stenosisRow.getByRole('button', { name: 'Pipeline' }).click();
    await expect(page.getByText(`Stenosis detection pipeline: ${PID}`)).toBeVisible({ timeout: 300_000 });
    await page.getByRole('button', { name: 'Close' }).click();

    // 6. case results page and report
    await stenosisRow.getByRole('button', { name: 'Full report' }).click();
    await expect(page.getByRole('heading', { name: `Case ${PID}: stenosis analysis` })).toBeVisible();
    await expectDownload(page, 'PDF', 'pdf');

    // 7. delete the test case again
    await page.goto('/dashboard');
    const newRow = page.getByRole('row', { name: new RegExp(PID) });
    await newRow.getByRole('button', { name: 'Delete' }).click();
    await page.getByRole('button', { name: 'Delete', exact: true }).last().click();
    await expect(page.getByRole('row', { name: new RegExp(PID) })).toHaveCount(0);
  });
});
/**
 * Capture /saidashboard/nuevo in desktop light and mobile dark
 */
const { chromium } = require('playwright');
const path = require('path');

const OUTPUT_DIR = '/Users/juanandrade/Desktop/saisuite/qa-evidence/saidashboard-4x4';
const BASE_URL = 'http://localhost:4200';
const CREDENTIALS = { email: 'admin@andina.com', password: 'Admin1234!' };

async function login(page) {
  await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 15000 });
  if (!page.url().includes('/auth/')) return;
  await page.fill('input[formcontrolname="email"]', CREDENTIALS.email);
  await page.fill('input[formcontrolname="password"]', CREDENTIALS.password);
  await page.click('button[type="submit"]');
  await page.waitForTimeout(2000);
}

async function main() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  });

  // Desktop light — /saidashboard/nuevo
  {
    const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const page = await ctx.newPage();
    await login(page);
    // Click "Nuevo dashboard" button directly
    await page.goto(`${BASE_URL}/saidashboard`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1000);
    const btn = page.locator('button:has-text("Nuevo dashboard")').first();
    if (await btn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await btn.click();
      await page.waitForTimeout(2000);
    } else {
      await page.goto(`${BASE_URL}/saidashboard/nuevo`, { waitUntil: 'networkidle', timeout: 15000 });
      await page.waitForTimeout(2000);
    }
    console.log('Nuevo desktop URL:', page.url());
    await page.screenshot({ path: path.join(OUTPUT_DIR, 'extra-06-desktop-light-nuevo-builder.png'), fullPage: true });
    console.log('extra-06-desktop-light-nuevo-builder.png');
    await ctx.close();
  }

  // Mobile light — /saidashboard/nuevo
  {
    const ctx = await browser.newContext({ viewport: { width: 375, height: 812 } });
    const page = await ctx.newPage();
    await login(page);
    await page.goto(`${BASE_URL}/saidashboard/nuevo`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(2000);
    console.log('Nuevo mobile URL:', page.url());
    await page.screenshot({ path: path.join(OUTPUT_DIR, 'extra-07-mobile-light-nuevo-builder.png'), fullPage: true });
    console.log('extra-07-mobile-light-nuevo-builder.png');
    await ctx.close();
  }

  await browser.close();
  console.log('Done.');
}

main().catch(err => { console.error(err); process.exit(1); });

/**
 * SaiDashboard Extra Captures
 * - Mobile sidebar open state
 * - Topbar button size measurement
 * - "Nuevo Dashboard" page
 * - Dark mode desktop close-up of topbar
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

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

  // --- EXTRA 1: Desktop Dark — topbar close-up ---
  {
    const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const page = await ctx.newPage();
    await login(page);
    await page.goto(`${BASE_URL}/saidashboard`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1000);
    // Enable dark
    const toggle = page.locator('mat-icon:text("dark_mode")').first();
    if (await toggle.isVisible({ timeout: 2000 }).catch(() => false)) await toggle.click();
    await page.waitForTimeout(800);
    // Topbar close-up
    const topbar = page.locator('mat-toolbar, [class*="topbar"], header').first();
    if (await topbar.isVisible({ timeout: 2000 }).catch(() => false)) {
      await topbar.screenshot({ path: path.join(OUTPUT_DIR, 'extra-01-desktop-dark-topbar.png') });
      console.log('extra-01-desktop-dark-topbar.png');
    }
    // Measure topbar buttons
    const btnSizes = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('mat-toolbar button, header button'));
      return buttons.map(b => {
        const r = b.getBoundingClientRect();
        return { text: (b.textContent || '').trim().substring(0, 30), w: Math.round(r.width), h: Math.round(r.height) };
      });
    });
    console.log('Desktop topbar button sizes:', JSON.stringify(btnSizes));
    await ctx.close();
  }

  // --- EXTRA 2: Mobile Light — sidebar open ---
  {
    const ctx = await browser.newContext({ viewport: { width: 375, height: 812 } });
    const page = await ctx.newPage();
    await login(page);
    await page.goto(`${BASE_URL}/saidashboard`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1000);
    // Open hamburger menu
    const menuBtn = page.locator('button[aria-label*="menu"], button mat-icon:text("menu")').first();
    if (await menuBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await menuBtn.click();
      await page.waitForTimeout(800);
    }
    await page.screenshot({ path: path.join(OUTPUT_DIR, 'extra-02-mobile-light-sidebar-open.png') });
    console.log('extra-02-mobile-light-sidebar-open.png');
    // Measure all interactive elements
    const smallTargets = await page.evaluate(() => {
      const els = Array.from(document.querySelectorAll('button, a, [role="button"], mat-list-item'));
      return els.filter(el => {
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0 && (r.width < 44 || r.height < 44);
      }).map(el => {
        const r = el.getBoundingClientRect();
        return { tag: el.tagName, text: (el.textContent || '').trim().substring(0, 40), w: Math.round(r.width), h: Math.round(r.height) };
      });
    });
    console.log('Mobile small touch targets:', JSON.stringify(smallTargets, null, 2));
    await ctx.close();
  }

  // --- EXTRA 3: Desktop Light — "Nuevo Dashboard" builder page ---
  {
    const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const page = await ctx.newPage();
    await login(page);
    await page.goto(`${BASE_URL}/saidashboard/new`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: path.join(OUTPUT_DIR, 'extra-03-desktop-light-nuevo-dashboard.png'), fullPage: true });
    console.log('extra-03-desktop-light-nuevo-dashboard.png');
    console.log('Nuevo Dashboard URL:', page.url());
    await ctx.close();
  }

  // --- EXTRA 4: Mobile Dark — sidebar open state ---
  {
    const ctx = await browser.newContext({ viewport: { width: 375, height: 812 } });
    const page = await ctx.newPage();
    await login(page);
    await page.goto(`${BASE_URL}/saidashboard`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1000);
    // Enable dark
    const toggle = page.locator('mat-icon:text("dark_mode")').first();
    if (await toggle.isVisible({ timeout: 2000 }).catch(() => false)) await toggle.click();
    await page.waitForTimeout(600);
    // Open sidebar
    const menuBtn = page.locator('button mat-icon:text("menu")').first();
    if (await menuBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await menuBtn.click();
      await page.waitForTimeout(800);
    }
    await page.screenshot({ path: path.join(OUTPUT_DIR, 'extra-04-mobile-dark-sidebar-open.png') });
    console.log('extra-04-mobile-dark-sidebar-open.png');
    await ctx.close();
  }

  // --- EXTRA 5: Desktop Light — warning banner close-up ---
  {
    const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const page = await ctx.newPage();
    await login(page);
    await page.goto(`${BASE_URL}/saidashboard`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1000);
    const banner = page.locator('[class*="trial"], [class*="banner"], mat-card').first();
    if (await banner.isVisible({ timeout: 2000 }).catch(() => false)) {
      await banner.screenshot({ path: path.join(OUTPUT_DIR, 'extra-05-trial-banner-closeup.png') });
      console.log('extra-05-trial-banner-closeup.png');
    }
    // Check license warning text
    const warningText = await page.locator('[class*="license-warning"], .license-warning, [class*="alert"]').first().textContent().catch(() => 'NOT_FOUND');
    console.log('License warning text:', warningText);
    await ctx.close();
  }

  await browser.close();
  console.log('\nAll extra captures done.');
}

main().catch(err => {
  console.error('FATAL:', err);
  process.exit(1);
});

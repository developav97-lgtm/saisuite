/**
 * Capture module cards after expanding "Editar licencia"
 * and capture Module Locked using Angular router (SPA nav from dashboard)
 */
const { chromium } = require('playwright');
const path = require('path');

const OUT  = '/Users/juanandrade/Desktop/saisuite/qa-evidence/4x4-components-2026-04-09';
const BASE = 'http://localhost:4200';
const API  = 'http://localhost:8000';
const SUPER = { email: 'superadmin@valmentech.com', password: 'QaTest2026!' };
const ADMIN = { email: 'admin@andina.com', password: 'Admin1234!' };
const TENANT_ID = '1b9fa607-7b89-457e-aa6b-0041bab851e9';

const SCENARIOS = [
  { name: '1-desktop-light', width: 1920, height: 1080, dark: false },
  { name: '2-desktop-dark',  width: 1920, height: 1080, dark: true  },
  { name: '3-mobile-light',  width: 375,  height: 812,  dark: false },
  { name: '4-mobile-dark',   width: 375,  height: 812,  dark: true  },
];

async function shot(page, name, label) {
  await page.screenshot({ path: path.join(OUT, name), fullPage: false });
  console.log(`  [SHOT] ${label} → ${name}`);
}
async function fullshot(page, name, label) {
  await page.screenshot({ path: path.join(OUT, name), fullPage: true });
  console.log(`  [FULL] ${label} → ${name}`);
}

async function loginViaForm(page, creds) {
  await page.goto(`${BASE}/auth/login`, { waitUntil: 'networkidle', timeout: 20000 });
  await page.fill('input[formcontrolname="email"]', creds.email);
  await page.fill('input[formcontrolname="password"]', creds.password);
  await page.click('button[type="submit"]');
  await page.waitForURL(u => !u.toString().includes('/auth/login'), { timeout: 15000 }).catch(() => {});
  await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(1500);
  console.log(`  Logged in → ${page.url()}`);
}

async function setDark(page, dark) {
  await page.evaluate(d => {
    if (d) document.body.classList.add('dark-theme');
    else   document.body.classList.remove('dark-theme');
  }, dark);
  await page.waitForTimeout(350);
}

async function isVis(page, sel, t = 5000) {
  return page.locator(sel).first().isVisible({ timeout: t }).catch(() => false);
}

// ─── Module Cards (expanded) ──────────────────────────────────────────────────
async function captureModuleCards(browser, s) {
  console.log(`\n  [MODULE CARDS] ${s.name}`);
  const ctx  = await browser.newContext({ viewport: { width: s.width, height: s.height } });
  const page = await ctx.newPage();

  await loginViaForm(page, SUPER);
  await setDark(page, s.dark);

  // SPA nav to tenant form (no hard reload)
  await page.goto(`${BASE}/admin/tenants/${TENANT_ID}`, { waitUntil: 'networkidle', timeout: 20000 });
  await setDark(page, s.dark);
  await page.waitForTimeout(2000);

  // Click Gestión de licencia tab
  const licTab = page.locator('[role="tab"]:has-text("licencia"), [role="tab"]:has-text("Licencia")').first();
  if (await licTab.isVisible({ timeout: 5000 }).catch(() => false)) {
    await licTab.click();
    await page.waitForTimeout(1500);
    console.log('  Clicked Gestión de licencia tab');
  }

  await shot(page, `${s.name}-c4b-licencia-collapsed.png`, 'Licencia collapsed');

  // Click "Editar licencia" button to expand module cards
  const editBtn = page.locator('button:has-text("Editar licencia")').first();
  if (await editBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
    await editBtn.click();
    await page.waitForTimeout(1500);
    console.log('  Clicked Editar licencia — module cards should now be visible');
  } else {
    console.log('  Editar licencia button not found');
  }

  await shot(page,     `${s.name}-c4b-module-cards-expanded.png`, 'Module Cards Expanded');
  await fullshot(page, `${s.name}-c4b-module-cards-expanded-full.png`, 'Module Cards Expanded Full');

  // Measure cards
  const cardCount = await page.locator('.tf-module-card').count();
  const modCards  = await isVis(page, '.tf-module-cards');
  console.log(`  .tf-module-cards visible: ${modCards}, card count: ${cardCount}`);

  // Mobile overflow check
  if (s.width <= 375 && modCards) {
    const gridData = await page.evaluate(() => {
      const g = document.querySelector('.tf-module-cards');
      if (!g) return null;
      const st = window.getComputedStyle(g);
      const parentSt = window.getComputedStyle(g.parentElement || g);
      return {
        display: st.display,
        gridCols: st.gridTemplateColumns,
        overflowX: st.overflowX,
        parentOverflowX: parentSt.overflowX,
        scrollW: g.scrollWidth,
        clientW: g.clientWidth,
        hasOverflow: g.scrollWidth > g.clientWidth,
      };
    });
    console.log(`  Grid responsive: ${JSON.stringify(gridData)}`);

    // Card touch target measurement
    if (cardCount > 0) {
      const btnData = await page.evaluate(() => {
        const btns = Array.from(document.querySelectorAll('.tf-module-card button'));
        return btns.slice(0, 3).map(b => {
          const r = b.getBoundingClientRect();
          return { text: b.textContent?.trim().slice(0, 20), w: Math.round(r.width), h: Math.round(r.height) };
        });
      });
      console.log(`  Card buttons touch targets: ${JSON.stringify(btnData)}`);
    }
  }

  // Dark mode: check hardcoded colors
  if (s.dark && cardCount > 0) {
    const darkData = await page.evaluate(() => {
      const card = document.querySelector('.tf-module-card');
      const header = document.querySelector('.tf-module-card-header');
      if (!card) return null;
      return {
        cardBg: window.getComputedStyle(card).backgroundColor,
        cardBorder: window.getComputedStyle(card).borderColor,
        cardColor: window.getComputedStyle(card).color,
        headerColor: header ? window.getComputedStyle(header).color : null,
      };
    });
    console.log(`  Dark mode card styles: ${JSON.stringify(darkData)}`);
  }

  await ctx.close();
}

// ─── Module Locked (via SPA router nav) ──────────────────────────────────────
async function captureModuleLocked(browser, s) {
  console.log(`\n  [MODULE LOCKED] ${s.name}`);
  const ctx  = await browser.newContext({ viewport: { width: s.width, height: s.height } });
  const page = await ctx.newPage();

  // Login via form — this establishes proper Angular auth state
  await loginViaForm(page, ADMIN);
  await setDark(page, s.dark);

  // We are now on /dashboard with Angular SPA running and auth state set
  // Use Angular router via client-side navigation (not hard page.goto)
  await page.evaluate(() => {
    // Trigger Angular router navigation
    const event = new CustomEvent('navigate-to', { detail: '/acceso-modulo?module=crm' });
    window.dispatchEvent(event);
  });

  // Navigate via Angular's router — inject URL change
  await page.evaluate(() => {
    window.location.href = '/acceso-modulo?module=crm';
  });

  // This causes a hard nav — wait for it
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(2000);
  await setDark(page, s.dark);

  const url = page.url();
  console.log(`  URL: ${url}`);

  const mlPage  = await isVis(page, '.ml-page');
  const mlTitle = await isVis(page, '.ml-title');
  const mlDesc  = await isVis(page, '.ml-desc');
  console.log(`  .ml-page: ${mlPage}, .ml-title: ${mlTitle}, .ml-desc: ${mlDesc}`);

  await shot(page,     `${s.name}-c3b-module-locked-viewport.png`, 'Module Locked Viewport');
  await fullshot(page, `${s.name}-c3b-module-locked-full.png`,     'Module Locked Full');

  if (mlPage || mlTitle) {
    // Measure CTA button
    const ctaData = await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('.ml-container button, .ml-container a[mat-raised-button], .ml-container a[mat-stroked-button]'));
      return btns.map(b => {
        const r = b.getBoundingClientRect();
        return { text: b.textContent?.trim().slice(0, 30), w: Math.round(r.width), h: Math.round(r.height) };
      });
    });
    console.log(`  CTA buttons: ${JSON.stringify(ctaData)}`);

    // Text contrast check
    const textData = await page.evaluate(() => {
      const title = document.querySelector('.ml-title');
      const desc  = document.querySelector('.ml-desc');
      return {
        titleColor: title ? window.getComputedStyle(title).color : null,
        titleBg:    title ? window.getComputedStyle(title.parentElement || title).backgroundColor : null,
        descColor:  desc  ? window.getComputedStyle(desc).color : null,
      };
    });
    console.log(`  Text styles: ${JSON.stringify(textData)}`);

    // Dark mode icon color check
    if (s.dark) {
      const iconData = await page.evaluate(() => {
        const icon = document.querySelector('.ml-lock-icon');
        return icon ? { color: window.getComputedStyle(icon).color } : null;
      });
      console.log(`  Lock icon dark: ${JSON.stringify(iconData)}`);
    }
  }

  await ctx.close();
}

// ─── MAIN ─────────────────────────────────────────────────────────────────────
async function main() {
  const browser = await chromium.launch({ headless: true });

  for (const s of SCENARIOS) {
    console.log(`\n${'='.repeat(50)}\nSCENARIO: ${s.name}\n${'='.repeat(50)}`);
    await captureModuleCards(browser, s);
    await captureModuleLocked(browser, s);
  }

  await browser.close();
  console.log('\nExpanded capture complete.');
}

main().catch(console.error);

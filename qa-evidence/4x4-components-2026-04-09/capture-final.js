/**
 * Final targeted capture — Module Locked + Tenant Module Cards
 * Both components need direct URL nav + proper auth persistence
 */
const { chromium } = require('playwright');
const path = require('path');

const OUT   = '/Users/juanandrade/Desktop/saisuite/qa-evidence/4x4-components-2026-04-09';
const BASE  = 'http://localhost:4200';
const API   = 'http://localhost:8000';
const SUPER = { email: 'superadmin@valmentech.com', password: 'QaTest2026!' };
const ADMIN = { email: 'admin@andina.com',          password: 'Admin1234!'  };
const TENANT_ID = '1b9fa607-7b89-457e-aa6b-0041bab851e9';

const SCENARIOS = [
  { name: '1-desktop-light', width: 1920, height: 1080, dark: false },
  { name: '2-desktop-dark',  width: 1920, height: 1080, dark: true  },
  { name: '3-mobile-light',  width: 375,  height: 812,  dark: false },
  { name: '4-mobile-dark',   width: 375,  height: 812,  dark: true  },
];

async function shot(page, name, label) {
  const fp = path.join(OUT, name);
  await page.screenshot({ path: fp, fullPage: false });
  console.log(`  [SHOT] ${label} → ${name}`);
}
async function fullshot(page, name, label) {
  const fp = path.join(OUT, name);
  await page.screenshot({ path: fp, fullPage: true });
  console.log(`  [FULL] ${label} → ${name}`);
}

// Inject tokens directly into localStorage — bypasses Angular form login
async function injectAuth(page, creds) {
  // Get tokens from API
  const res = await page.evaluate(async ({ apiBase, creds }) => {
    const r = await fetch(`${apiBase}/api/v1/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(creds),
    });
    return r.json();
  }, { apiBase: API, creds });

  if (!res.access) {
    console.log('  AUTH FAILED:', JSON.stringify(res).slice(0, 200));
    return false;
  }

  await page.evaluate(({ access, refresh, user }) => {
    localStorage.setItem('access_token',  access);
    localStorage.setItem('refresh_token', refresh);
    localStorage.setItem('current_user',  JSON.stringify(user));
  }, { access: res.access, refresh: res.refresh, user: res.user });

  console.log(`  Auth injected for: ${creds.email}`);
  return true;
}

async function setDark(page, dark) {
  await page.evaluate(d => {
    if (d) document.body.classList.add('dark-theme');
    else   document.body.classList.remove('dark-theme');
  }, dark);
  await page.waitForTimeout(300);
}

async function isVis(page, sel, t = 4000) {
  return page.locator(sel).first().isVisible({ timeout: t }).catch(() => false);
}

// ─── Module Locked ────────────────────────────────────────────────────────────
async function captureModuleLocked(browser, s) {
  console.log(`\n  [MODULE LOCKED] ${s.name}`);
  const ctx  = await browser.newContext({ viewport: { width: s.width, height: s.height } });
  const page = await ctx.newPage();

  // Seed a blank page on the origin so localStorage is writable
  await page.goto(`${BASE}/auth/login`, { waitUntil: 'domcontentloaded', timeout: 15000 });
  const ok = await injectAuth(page, ADMIN);
  if (!ok) { await ctx.close(); return; }

  // Navigate to acceso-modulo — Angular reads from localStorage on boot
  await page.goto(`${BASE}/acceso-modulo?module=crm`, { waitUntil: 'networkidle', timeout: 20000 });
  await setDark(page, s.dark);
  await page.waitForTimeout(2000);

  const url = page.url();
  console.log(`  URL: ${url}`);

  const mlPage = await isVis(page, '.ml-page');
  const mlTitle = await isVis(page, '.ml-title');
  const mlLock  = await isVis(page, '.ml-lock-icon, mat-icon:text("lock")');
  console.log(`  .ml-page: ${mlPage}, .ml-title: ${mlTitle}, lock icon: ${mlLock}`);

  if (url.includes('/auth/login')) {
    // Still redirecting — take the login page as evidence
    await fullshot(page, `${s.name}-c3-module-locked-redirected.png`, 'Module Locked — redirected to login (FAIL)');

    // Try SPA client-side navigation instead of hard goto
    await page.goto(BASE, { waitUntil: 'networkidle', timeout: 15000 });
    await injectAuth(page, ADMIN);
    await page.waitForTimeout(1000);

    // Use Angular router via window.history
    await page.evaluate(() => {
      window.history.pushState({}, '', '/acceso-modulo?module=crm');
      window.dispatchEvent(new PopStateEvent('popstate'));
    });
    await page.waitForTimeout(3000);
    await setDark(page, s.dark);

    const url2 = page.url();
    console.log(`  URL after SPA nav: ${url2}`);
  }

  await fullshot(page, `${s.name}-c3-module-locked-full.png`,     'Module Locked Full');
  await shot(page,     `${s.name}-c3-module-locked-viewport.png`, 'Module Locked Viewport');

  // Measure CTA button if visible
  if (s.width <= 375) {
    const btns = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('.ml-container button, .ml-container a'))
        .map(el => {
          const r = el.getBoundingClientRect();
          return { tag: el.tagName, text: el.textContent?.trim().slice(0, 30), w: Math.round(r.width), h: Math.round(r.height) };
        });
    });
    console.log(`  CTA buttons: ${JSON.stringify(btns)}`);
  }

  await ctx.close();
}

// ─── Tenant Module Cards ──────────────────────────────────────────────────────
async function captureTenantModuleCards(browser, s) {
  console.log(`\n  [TENANT MODULE CARDS] ${s.name}`);
  const ctx  = await browser.newContext({ viewport: { width: s.width, height: s.height } });
  const page = await ctx.newPage();

  await page.goto(`${BASE}/auth/login`, { waitUntil: 'domcontentloaded', timeout: 15000 });
  await injectAuth(page, SUPER);

  // Navigate directly to tenant edit form
  await page.goto(`${BASE}/admin/tenants/${TENANT_ID}`, { waitUntil: 'networkidle', timeout: 20000 });
  await setDark(page, s.dark);
  await page.waitForTimeout(2000);

  const url = page.url();
  console.log(`  URL: ${url}`);

  await shot(page, `${s.name}-c4-tenant-form-loaded.png`, 'Tenant Form — Loaded');

  // Click the "Gestión de licencia" tab
  const licTab = page.locator('[role="tab"]:has-text("licencia"), [role="tab"]:has-text("Licencia")').first();
  const tabVis = await licTab.isVisible({ timeout: 6000 }).catch(() => false);
  console.log(`  Licencia tab visible: ${tabVis}`);

  if (tabVis) {
    await licTab.click();
    await page.waitForTimeout(2000);
  } else {
    // Dump tabs present
    const tabs = await page.evaluate(() =>
      Array.from(document.querySelectorAll('[role="tab"]')).map(t => t.textContent?.trim())
    );
    console.log(`  Tabs found: ${JSON.stringify(tabs)}`);
  }

  await shot(page,     `${s.name}-c4-licencia-tab.png`,           'Licencia Tab');
  await fullshot(page, `${s.name}-c4-licencia-full.png`,          'Licencia Tab Full');

  // Check module cards
  const modSection = await isVis(page, '.tf-modules-section');
  const modCards   = await isVis(page, '.tf-module-cards');
  const modCard    = await isVis(page, '.tf-module-card');
  const addBtn     = await isVis(page, 'button:has-text("Agregar")');
  const quitarBtn  = await isVis(page, 'button:has-text("Quitar")');
  const cardCount  = await page.locator('.tf-module-card').count();

  console.log(`  .tf-modules-section: ${modSection}, .tf-module-cards: ${modCards}, .tf-module-card: ${modCard}`);
  console.log(`  cards count: ${cardCount}, Agregar: ${addBtn}, Quitar: ${quitarBtn}`);

  if (s.width <= 375 && modCards) {
    const gridData = await page.evaluate(() => {
      const g = document.querySelector('.tf-module-cards');
      if (!g) return null;
      const st = window.getComputedStyle(g);
      return {
        display: st.display,
        gridCols: st.gridTemplateColumns,
        overflowX: st.overflowX,
        scrollW: g.scrollWidth,
        clientW: g.clientWidth,
        hasOverflow: g.scrollWidth > g.clientWidth,
      };
    });
    console.log(`  Grid data: ${JSON.stringify(gridData)}`);

    // Check individual card
    if (modCard) {
      const cardData = await page.evaluate(() => {
        const c = document.querySelector('.tf-module-card');
        if (!c) return null;
        const r = c.getBoundingClientRect();
        return { w: Math.round(r.width), h: Math.round(r.height), visible: r.width > 0 };
      });
      console.log(`  First card bounding: ${JSON.stringify(cardData)}`);
    }

    // Check Agregar button touch target
    if (addBtn) {
      const btnData = await page.evaluate(() => {
        const b = document.querySelector('button');
        const allBtns = Array.from(document.querySelectorAll('button'))
          .filter(b => b.textContent?.includes('Agregar'));
        if (!allBtns.length) return null;
        const r = allBtns[0].getBoundingClientRect();
        return { w: Math.round(r.width), h: Math.round(r.height) };
      });
      console.log(`  Agregar touch target: ${JSON.stringify(btnData)}`);
    }
  }

  // Dark mode: check card background/border
  if (s.dark && modCard) {
    const darkStyles = await page.evaluate(() => {
      const c = document.querySelector('.tf-module-card');
      if (!c) return null;
      const st = window.getComputedStyle(c);
      return { bg: st.backgroundColor, border: st.border, color: st.color };
    });
    console.log(`  .tf-module-card dark styles: ${JSON.stringify(darkStyles)}`);
  }

  await ctx.close();
}

// ─── MAIN ────────────────────────────────────────────────────────────────────
async function main() {
  const browser = await chromium.launch({ headless: true });

  for (const s of SCENARIOS) {
    console.log(`\n${'='.repeat(50)}\nSCENARIO: ${s.name}\n${'='.repeat(50)}`);
    await captureModuleLocked(browser, s);
    await captureTenantModuleCards(browser, s);
  }

  await browser.close();
  console.log('\nFinal capture complete.');
}

main().catch(console.error);

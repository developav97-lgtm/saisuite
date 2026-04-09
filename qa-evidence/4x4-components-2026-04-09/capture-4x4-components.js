/**
 * 4x4 Visual Validation — 4 New Components
 * Scenarios: Desktop/Mobile × Light/Dark
 * Components: Trial Banner, Bot Quota UI, Module Locked, Tenant Form Module Cards
 * QA Agent: EvidenceQA
 * Date: 2026-04-09
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const OUTPUT_DIR = '/Users/juanandrade/Desktop/saisuite/qa-evidence/4x4-components-2026-04-09';
const BASE_URL = 'http://localhost:4200';
const CREDENTIALS = { email: 'superadmin@valmentech.com', password: 'QaTest2026!' };

const SCENARIOS = [
  { name: '1-desktop-light', width: 1920, height: 1080, dark: false },
  { name: '2-desktop-dark',  width: 1920, height: 1080, dark: true  },
  { name: '3-mobile-light',  width: 375,  height: 812,  dark: false },
  { name: '4-mobile-dark',   width: 375,  height: 812,  dark: true  },
];

const results = { scenarios: {}, summary: { pass: 0, fail: 0, issues: [] } };

async function login(page) {
  await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 20000 });
  if (!page.url().includes('/auth/')) {
    console.log('  Already authenticated — skipping login');
    return;
  }
  console.log('  Logging in as', CREDENTIALS.email);
  await page.fill('input[type="email"], input[formcontrolname="email"]', CREDENTIALS.email);
  await page.fill('input[type="password"], input[formcontrolname="password"]', CREDENTIALS.password);
  await page.click('button[type="submit"]');
  await page.waitForTimeout(3000);
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  console.log('  Post-login URL:', page.url());
}

async function setDarkMode(page, dark) {
  await page.evaluate((isDark) => {
    if (isDark) {
      document.body.classList.add('dark-theme');
    } else {
      document.body.classList.remove('dark-theme');
    }
  }, dark);
  await page.waitForTimeout(300);
}

async function screenshot(page, filename, label) {
  const filepath = path.join(OUTPUT_DIR, filename);
  await page.screenshot({ path: filepath, fullPage: false });
  console.log(`  [SCREENSHOT] ${label} → ${filename}`);
  return filepath;
}

async function screenshotFull(page, filename, label) {
  const filepath = path.join(OUTPUT_DIR, filename);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log(`  [SCREENSHOT-FULL] ${label} → ${filename}`);
  return filepath;
}

async function checkElementVisible(page, selector, label) {
  const el = page.locator(selector).first();
  const visible = await el.isVisible({ timeout: 5000 }).catch(() => false);
  console.log(`  [CHECK] ${label}: ${visible ? 'VISIBLE' : 'NOT FOUND'} (${selector})`);
  return visible;
}

async function checkTouchTarget(page, selector, minPx = 44) {
  const el = page.locator(selector).first();
  const box = await el.boundingBox().catch(() => null);
  if (!box) return { ok: false, reason: 'Element not found' };
  const ok = box.width >= minPx && box.height >= minPx;
  return { ok, width: Math.round(box.width), height: Math.round(box.height) };
}

async function runScenario(browser, scenario) {
  console.log(`\n=== SCENARIO: ${scenario.name} (${scenario.width}x${scenario.height}, dark=${scenario.dark}) ===`);
  const context = await browser.newContext({
    viewport: { width: scenario.width, height: scenario.height },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  const issues = [];
  const shots = {};

  // ─── LOGIN ─────────────────────────────────────────────────────────────────
  await login(page);
  await setDarkMode(page, scenario.dark);

  // ─── COMPONENT 1: TRIAL BANNER ─────────────────────────────────────────────
  console.log('\n  --- Component 1: Trial Banner ---');
  await page.goto(`${BASE_URL}/saidashboard`, { waitUntil: 'networkidle', timeout: 15000 });
  await setDarkMode(page, scenario.dark);
  await page.waitForTimeout(2000);

  // Capture full page to see banner
  shots['trial-banner-full'] = await screenshotFull(page, `${scenario.name}-trial-banner-full.png`, 'Trial Banner Full Page');
  // Capture viewport crop
  shots['trial-banner-viewport'] = await screenshot(page, `${scenario.name}-trial-banner-viewport.png`, 'Trial Banner Viewport');

  // Check for trial banner presence
  const trialBannerSelectors = [
    'app-trial-banner',
    '[class*="trial-banner"]',
    '[class*="trial"]',
    '.trial-banner',
    '[data-testid*="trial"]',
    'mat-toolbar.trial',
    '.banner-trial',
  ];
  let bannerFound = false;
  for (const sel of trialBannerSelectors) {
    const found = await checkElementVisible(page, sel, `Trial Banner (${sel})`);
    if (found) { bannerFound = true; break; }
  }

  // Also try text search
  const trialText = await page.locator('text=/trial|prueba|días|vence|plan/i').first().isVisible({ timeout: 3000 }).catch(() => false);
  console.log(`  Trial-related text visible: ${trialText}`);

  if (!bannerFound && !trialText) {
    issues.push({ component: 'Trial Banner', scenario: scenario.name, severity: 'MEDIUM', issue: 'Trial banner not found on /saidashboard — may require trial company' });
  }

  // Check for dark mode contrast issues on banner
  if (scenario.dark) {
    // Capture close-up if banner found
    shots['trial-banner-dark'] = await screenshot(page, `${scenario.name}-trial-banner-dark.png`, 'Trial Banner Dark Mode');
  }

  // ─── COMPONENT 2: BOT QUOTA UI ─────────────────────────────────────────────
  console.log('\n  --- Component 2: Bot Quota UI ---');
  // Look for floating chat icon
  const chatIconSelectors = [
    'button[aria-label*="chat"], button[aria-label*="Chat"]',
    '.chat-fab',
    '.chat-widget-button',
    '[class*="chat-float"]',
    '[class*="bot"]',
    'button mat-icon:text("chat")',
    'button mat-icon:text("smart_toy")',
    'button mat-icon:text("support_agent")',
    '.floating-chat',
    '[data-testid*="chat"]',
  ];

  let chatIconFound = false;
  for (const sel of chatIconSelectors) {
    const found = await checkElementVisible(page, sel, `Chat icon (${sel})`);
    if (found) {
      chatIconFound = true;
      // Click to open chat
      await page.locator(sel).first().click();
      await page.waitForTimeout(1500);
      shots['bot-chat-opened'] = await screenshot(page, `${scenario.name}-bot-chat-opened.png`, 'Bot Chat Opened');
      break;
    }
  }

  if (!chatIconFound) {
    console.log('  Chat icon not found by selector — trying to locate visible floating buttons');
    // Take screenshot to see what's on screen
    shots['bot-no-icon'] = await screenshot(page, `${scenario.name}-bot-no-chat-icon.png`, 'No Chat Icon Found');
  }

  // After opening chat, look for quota/token bar
  const quotaSelectors = [
    '[class*="quota"]',
    '[class*="token"]',
    'mat-progress-bar',
    'progress',
    '[class*="progress"]',
    '[role="progressbar"]',
    '[class*="usage"]',
    '[class*="limit"]',
  ];

  let quotaFound = false;
  for (const sel of quotaSelectors) {
    const found = await checkElementVisible(page, sel, `Quota/Token bar (${sel})`);
    if (found) { quotaFound = true; break; }
  }

  shots['bot-quota-ui'] = await screenshot(page, `${scenario.name}-bot-quota-ui.png`, 'Bot Quota UI');
  if (scenario.width <= 375) {
    // Check touch targets for mobile
    const chatBtnTarget = await checkTouchTarget(page, chatIconSelectors.find(s => s.includes('chat')) || 'button', 44);
    console.log(`  Chat button touch target: ${JSON.stringify(chatBtnTarget)}`);
    if (chatIconFound && !chatBtnTarget.ok) {
      issues.push({ component: 'Bot Quota UI', scenario: scenario.name, severity: 'HIGH', issue: `Chat button touch target too small: ${chatBtnTarget.width}x${chatBtnTarget.height}px (minimum 44x44)` });
    }
  }

  if (!quotaFound) {
    issues.push({ component: 'Bot Quota UI', scenario: scenario.name, severity: 'MEDIUM', issue: 'Token quota progress bar not found — may require bot conversation to be open' });
  }

  // Try navigating to chat directly if it exists
  const chatRoutes = ['/chat', '/comunicaciones', '/mensajes'];
  for (const route of chatRoutes) {
    try {
      await page.goto(`${BASE_URL}${route}`, { waitUntil: 'networkidle', timeout: 8000 });
      await setDarkMode(page, scenario.dark);
      await page.waitForTimeout(1000);
      const currentUrl = page.url();
      if (!currentUrl.includes('/auth/') && currentUrl.includes(route)) {
        shots['chat-route'] = await screenshot(page, `${scenario.name}-chat-route${route.replace('/', '-')}.png`, `Chat at ${route}`);
        // Re-check for quota
        for (const sel of quotaSelectors) {
          const found = await checkElementVisible(page, sel, `Quota after nav to ${route} (${sel})`);
          if (found) { quotaFound = true; break; }
        }
        break;
      }
    } catch (e) {
      // route not accessible, continue
    }
  }

  // ─── COMPONENT 3: MODULE LOCKED ────────────────────────────────────────────
  console.log('\n  --- Component 3: Module Locked ---');
  await page.goto(`${BASE_URL}/acceso-modulo?module=crm`, { waitUntil: 'networkidle', timeout: 15000 });
  await setDarkMode(page, scenario.dark);
  await page.waitForTimeout(2000);

  shots['module-locked-viewport'] = await screenshot(page, `${scenario.name}-module-locked-viewport.png`, 'Module Locked Viewport');
  shots['module-locked-full'] = await screenshotFull(page, `${scenario.name}-module-locked-full.png`, 'Module Locked Full Page');

  const currentUrlLocked = page.url();
  console.log('  URL after navigating to /acceso-modulo:', currentUrlLocked);

  // Check for locked screen elements
  const lockedSelectors = [
    'app-module-locked',
    '[class*="locked"]',
    '[class*="acceso"]',
    '[class*="denied"]',
    '[class*="blocked"]',
    'text=/bloqueado|acceso.*denegado|no.*tienes.*acceso|módulo.*no.*disponible|upgrade/i',
    '[class*="lock"]',
    'mat-icon:text("lock")',
  ];

  let lockedFound = false;
  for (const sel of lockedSelectors) {
    const found = await checkElementVisible(page, sel, `Module Locked (${sel})`);
    if (found) { lockedFound = true; break; }
  }

  // If redirected away, check where we landed
  if (!lockedFound) {
    if (currentUrlLocked.includes('/auth/')) {
      issues.push({ component: 'Module Locked', scenario: scenario.name, severity: 'LOW', issue: 'Redirected to login — /acceso-modulo requires auth. Expected: locked module screen shown.' });
    } else {
      issues.push({ component: 'Module Locked', scenario: scenario.name, severity: 'HIGH', issue: `Module Locked screen not displayed at /acceso-modulo?module=crm (URL: ${currentUrlLocked})` });
    }
  }

  // Check if there's a CTA button (upgrade/contact)
  const ctaButton = await checkElementVisible(page, 'a[href], button:visible', 'CTA button');
  if (scenario.width <= 375 && ctaButton) {
    const target = await checkTouchTarget(page, 'a[href*="contact"], a[href*="upgrade"], button[class*="cta"], .module-locked button', 44);
    console.log(`  CTA touch target: ${JSON.stringify(target)}`);
    if (!target.ok && target.reason !== 'Element not found') {
      issues.push({ component: 'Module Locked', scenario: scenario.name, severity: 'HIGH', issue: `CTA button touch target too small: ${target.width}x${target.height}px` });
    }
  }

  // ─── COMPONENT 4: TENANT FORM — MODULE CARDS GRID ─────────────────────────
  console.log('\n  --- Component 4: Tenant Form Module Cards Grid ---');
  await page.goto(`${BASE_URL}/admin/tenants`, { waitUntil: 'networkidle', timeout: 15000 });
  await setDarkMode(page, scenario.dark);
  await page.waitForTimeout(2000);

  const tenantsUrl = page.url();
  console.log('  URL after navigating to /admin/tenants:', tenantsUrl);

  shots['tenants-list'] = await screenshot(page, `${scenario.name}-tenants-list.png`, 'Tenants List');

  // Click first tenant to open detail
  const tenantRowSelectors = [
    'mat-row:first-child',
    'tr[mat-row]:first-child',
    '[class*="tenant-row"]:first-child',
    '.tenant-item:first-child',
    'mat-list-item:first-child',
    '[class*="list-item"]:first-child',
    'table tbody tr:first-child',
  ];

  let tenantOpened = false;
  for (const sel of tenantRowSelectors) {
    const el = page.locator(sel).first();
    const visible = await el.isVisible({ timeout: 3000 }).catch(() => false);
    if (visible) {
      await el.click();
      await page.waitForTimeout(2000);
      console.log(`  Opened tenant via: ${sel}`);
      tenantOpened = true;
      break;
    }
  }

  if (!tenantOpened) {
    // Try clicking any visible button that might open a tenant
    const editButtons = ['button[aria-label*="edit"], button[aria-label*="ver"], mat-icon:text("edit")', 'button:has(mat-icon:text("edit"))'];
    for (const sel of editButtons) {
      const el = page.locator(sel).first();
      const visible = await el.isVisible({ timeout: 2000 }).catch(() => false);
      if (visible) {
        await el.click();
        await page.waitForTimeout(2000);
        tenantOpened = true;
        break;
      }
    }
  }

  shots['tenant-detail'] = await screenshot(page, `${scenario.name}-tenant-detail.png`, 'Tenant Detail');

  // Navigate to Licencia tab
  const licenciaTabSelectors = [
    'mat-tab-header [aria-label*="licencia" i]',
    'mat-tab-header [aria-label*="license" i]',
    '.mat-tab-label:has-text("Licencia")',
    'button[role="tab"]:has-text("Licencia")',
    '[role="tab"]:has-text("Licencia")',
    'mat-tab-label:has-text("Licencia")',
    'div.mat-tab-label:has-text("Licencia")',
  ];

  let licenciaTabFound = false;
  for (const sel of licenciaTabSelectors) {
    const el = page.locator(sel).first();
    const visible = await el.isVisible({ timeout: 3000 }).catch(() => false);
    if (visible) {
      await el.click();
      await page.waitForTimeout(1500);
      console.log(`  Clicked Licencia tab via: ${sel}`);
      licenciaTabFound = true;
      break;
    }
  }

  // Also try text-based tab selection
  if (!licenciaTabFound) {
    const tabByText = page.locator('text=Licencia').first();
    const tabVisible = await tabByText.isVisible({ timeout: 3000 }).catch(() => false);
    if (tabVisible) {
      await tabByText.click();
      await page.waitForTimeout(1500);
      licenciaTabFound = true;
      console.log('  Clicked Licencia tab via text matcher');
    }
  }

  shots['tenant-licencia-tab'] = await screenshot(page, `${scenario.name}-tenant-licencia-tab.png`, 'Tenant Licencia Tab');

  // Check for module cards grid
  const moduleCardSelectors = [
    '[class*="module-card"]',
    '[class*="modules-grid"]',
    'mat-card[class*="module"]',
    '.module-cards',
    '[class*="card"]:has(button)',
    'app-module-cards',
    '[class*="license-modules"]',
  ];

  let moduleCardsFound = false;
  for (const sel of moduleCardSelectors) {
    const found = await checkElementVisible(page, sel, `Module Cards (${sel})`);
    if (found) { moduleCardsFound = true; break; }
  }

  // Check for add/remove buttons in cards
  const addButtonFound = await checkElementVisible(page, 'button:has-text("Agregar"), button:has-text("Add"), button:has-text("+ Módulo")', 'Add module button');
  const removeButtonFound = await checkElementVisible(page, 'button:has-text("Quitar"), button:has-text("Remove")', 'Remove module button');

  shots['module-cards-grid'] = await screenshot(page, `${scenario.name}-module-cards-grid.png`, 'Module Cards Grid');
  shots['module-cards-full'] = await screenshotFull(page, `${scenario.name}-module-cards-full.png`, 'Module Cards Full');

  if (!moduleCardsFound) {
    issues.push({ component: 'Tenant Module Cards', scenario: scenario.name, severity: 'HIGH', issue: `Module cards grid not found on Licencia tab. Tenant opened: ${tenantOpened}, Licencia tab found: ${licenciaTabFound}` });
  }

  // Check horizontal scroll for module grid on mobile
  if (scenario.width <= 375) {
    const gridOverflow = await page.evaluate(() => {
      const grid = document.querySelector('[class*="module"], [class*="grid"], [class*="card"]');
      if (!grid) return null;
      const style = window.getComputedStyle(grid.parentElement || grid);
      return {
        overflowX: style.overflowX,
        hasScroll: grid.scrollWidth > grid.clientWidth,
        scrollWidth: grid.scrollWidth,
        clientWidth: grid.clientWidth,
      };
    });
    console.log(`  Grid overflow data: ${JSON.stringify(gridOverflow)}`);
    if (gridOverflow && gridOverflow.hasScroll && gridOverflow.overflowX === 'hidden') {
      issues.push({ component: 'Tenant Module Cards', scenario: scenario.name, severity: 'HIGH', issue: 'Module cards grid has overflow but overflow-x is hidden — content may be cut off on mobile' });
    }
  }

  // Check touch targets for add/remove buttons on mobile
  if (scenario.width <= 375 && (addButtonFound || removeButtonFound)) {
    const btnSel = addButtonFound ? 'button:has-text("Agregar")' : 'button:has-text("Quitar")';
    const target = await checkTouchTarget(page, btnSel, 44);
    console.log(`  Add/Remove button touch target: ${JSON.stringify(target)}`);
    if (!target.ok && target.reason !== 'Element not found') {
      issues.push({ component: 'Tenant Module Cards', scenario: scenario.name, severity: 'HIGH', issue: `Add/Remove button touch target too small: ${target.width}x${target.height}px (minimum 44x44)` });
    }
  }

  // ─── SCENARIO SUMMARY ─────────────────────────────────────────────────────
  results.scenarios[scenario.name] = {
    viewport: `${scenario.width}x${scenario.height}`,
    dark: scenario.dark,
    screenshots: Object.values(shots),
    issues: issues,
    components: {
      'trial-banner': bannerFound || trialText,
      'bot-quota': quotaFound,
      'module-locked': lockedFound,
      'module-cards': moduleCardsFound,
    }
  };

  results.summary.issues.push(...issues);

  console.log(`\n  SCENARIO COMPLETE: ${scenario.name}`);
  console.log(`  Issues found: ${issues.length}`);
  issues.forEach(i => console.log(`  [${i.severity}] ${i.component}: ${i.issue}`));

  await context.close();
}

async function main() {
  console.log('EvidenceQA — 4x4 Component Validation');
  console.log('Components: Trial Banner, Bot Quota UI, Module Locked, Tenant Module Cards');
  console.log(`Output: ${OUTPUT_DIR}`);
  console.log(`Base URL: ${BASE_URL}`);

  const browser = await chromium.launch({ headless: true });

  for (const scenario of SCENARIOS) {
    await runScenario(browser, scenario);
  }

  await browser.close();

  // Write results
  const resultsPath = path.join(OUTPUT_DIR, 'test-results.json');
  fs.writeFileSync(resultsPath, JSON.stringify(results, null, 2));
  console.log(`\nResults written to: ${resultsPath}`);

  // Print summary
  const allIssues = results.summary.issues;
  console.log('\n========= QA SUMMARY =========');
  console.log(`Total issues: ${allIssues.length}`);
  console.log('Critical/High:', allIssues.filter(i => i.severity === 'HIGH').length);
  console.log('Medium:', allIssues.filter(i => i.severity === 'MEDIUM').length);
  console.log('Low:', allIssues.filter(i => i.severity === 'LOW').length);
  allIssues.forEach(i => console.log(`  [${i.severity}] [${i.scenario}] ${i.component}: ${i.issue}`));
}

main().catch(console.error);

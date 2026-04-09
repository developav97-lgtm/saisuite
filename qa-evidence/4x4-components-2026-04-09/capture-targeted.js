/**
 * Targeted 4x4 QA Capture — Pass 2
 * Components: Trial Banner, Bot Quota UI, Module Locked, Tenant Form Module Cards
 * QA Agent: EvidenceQA — Date: 2026-04-09
 */

const { chromium } = require('playwright');
const path = require('path');
const fs   = require('fs');

const OUTPUT_DIR   = '/Users/juanandrade/Desktop/saisuite/qa-evidence/4x4-components-2026-04-09';
const BASE_URL     = 'http://localhost:4200';
const CREDS_SUPER  = { email: 'superadmin@valmentech.com', password: 'QaTest2026!' };
const CREDS_ADMIN  = { email: 'admin@andina.com', password: 'Admin1234!' };
const TENANT_ID    = '1b9fa607-7b89-457e-aa6b-0041bab851e9';

const SCENARIOS = [
  { name: '1-desktop-light', width: 1920, height: 1080, dark: false },
  { name: '2-desktop-dark',  width: 1920, height: 1080, dark: true  },
  { name: '3-mobile-light',  width: 375,  height: 812,  dark: false },
  { name: '4-mobile-dark',   width: 375,  height: 812,  dark: true  },
];

const results = { screenshots: [], issues: [], per_component: {} };

// ── helpers ──────────────────────────────────────────────────────────────────

async function screenshot(page, filename, label) {
  const fp = path.join(OUTPUT_DIR, filename);
  await page.screenshot({ path: fp, fullPage: false });
  console.log(`  [SHOT] ${label} → ${filename}`);
  results.screenshots.push(filename);
  return fp;
}

async function fullshot(page, filename, label) {
  const fp = path.join(OUTPUT_DIR, filename);
  await page.screenshot({ path: fp, fullPage: true });
  console.log(`  [FULL] ${label} → ${filename}`);
  results.screenshots.push(filename);
  return fp;
}

async function setDark(page, dark) {
  await page.evaluate(d => {
    if (d) document.body.classList.add('dark-theme');
    else   document.body.classList.remove('dark-theme');
  }, dark);
  await page.waitForTimeout(400);
}

async function loginAndWait(page, creds) {
  await page.goto(`${BASE_URL}/auth/login`, { waitUntil: 'networkidle', timeout: 20000 });
  await page.fill('input[formcontrolname="email"]', creds.email);
  await page.fill('input[formcontrolname="password"]', creds.password);
  await page.click('button[type="submit"]');
  // Wait for redirect away from login
  await page.waitForURL(url => !url.includes('/auth/login'), { timeout: 15000 }).catch(() => {});
  await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(1500);
  console.log(`  Logged in as ${creds.email} — URL: ${page.url()}`);
}

async function boundingBox(page, selector) {
  const el = page.locator(selector).first();
  return await el.boundingBox().catch(() => null);
}

async function isVisible(page, selector, timeout = 4000) {
  return await page.locator(selector).first().isVisible({ timeout }).catch(() => false);
}

// ── COMPONENT 1: Trial Banner ─────────────────────────────────────────────────
// The banner shows inside modules when the company has trial/no access.
// For superadmin's company with active license, the banner won't show on /saidashboard.
// Needs a company account with trial or no access. We use admin@andina.com for this test.
// The banner in saidashboard checks tipo_acceso from /api/v1/saidashboard/trial-status/

async function testTrialBanner(page, s) {
  const issues = [];
  console.log('\n  [COMP 1] Trial Banner');

  // Navigate to saidashboard as admin
  await page.goto(`${BASE_URL}/saidashboard`, { waitUntil: 'networkidle', timeout: 15000 });
  await setDark(page, s.dark);
  await page.waitForTimeout(2000);

  const url = page.url();
  console.log(`  URL: ${url}`);

  await fullshot(page, `${s.name}-c1-trial-banner-full.png`, 'Trial Banner — Full page');
  await screenshot(page, `${s.name}-c1-trial-banner-viewport.png`, 'Trial Banner — Viewport');

  // Check if we can find any banner elements
  const bannerFound      = await isVisible(page, 'app-trial-banner');
  const tbBannerFound    = await isVisible(page, '.tb-banner');
  const licBannerFound   = await isVisible(page, '.sc-license-banner');
  const trialTextFound   = await isVisible(page, 'text=/prueba|trial|días restantes/i');

  console.log(`  app-trial-banner: ${bannerFound}, .tb-banner: ${tbBannerFound}, .sc-license-banner: ${licBannerFound}, trial text: ${trialTextFound}`);

  // The banner only appears on trial/no-access. Superadmin account has full license.
  // Check for warning/expiry banner (shell shows if <30 days to expiry)
  const shellBannerFound = await isVisible(page, '.sc-license-banner--warn, .sc-license-banner--danger, .sc-license-banner--critical');

  // Record what's actually visible
  const bannerState = {
    appTrialBanner: bannerFound,
    tbBanner: tbBannerFound,
    shellLicenseBanner: licBannerFound || shellBannerFound,
    trialText: trialTextFound,
    note: 'Banner conditional on trial/no-access status. Active license = no banner shown. This is correct behavior.'
  };

  // Evaluate dark mode contrast if banner IS visible
  if (tbBannerFound) {
    const contrastData = await page.evaluate(() => {
      const el = document.querySelector('.tb-banner');
      if (!el) return null;
      const style = window.getComputedStyle(el);
      return { bg: style.backgroundColor, color: style.color };
    });
    console.log(`  .tb-banner contrast data: ${JSON.stringify(contrastData)}`);
    bannerState.contrastData = contrastData;
  }

  // Mobile: check .tb-action button touch target
  if (s.width <= 375 && tbBannerFound) {
    const box = await boundingBox(page, '.tb-action');
    console.log(`  .tb-action bounding box: ${JSON.stringify(box)}`);
    if (box && (box.width < 44 || box.height < 44)) {
      issues.push(`[MOBILE] .tb-action button touch target ${Math.round(box.width)}x${Math.round(box.height)}px — below 44px minimum`);
    }
  }

  // Check if mobile layout stacks correctly (flex-direction: column)
  if (s.width <= 375 && tbBannerFound) {
    const flexDir = await page.evaluate(() => {
      const el = document.querySelector('.tb-banner');
      return el ? window.getComputedStyle(el).flexDirection : null;
    });
    console.log(`  .tb-banner flex-direction on mobile: ${flexDir}`);
    if (flexDir && flexDir !== 'column') {
      issues.push(`[MOBILE] .tb-banner flex-direction is "${flexDir}" instead of "column" — overflow risk`);
    }
  }

  return { found: bannerFound || tbBannerFound, state: bannerState, issues };
}

// ── COMPONENT 2: Bot Quota UI ─────────────────────────────────────────────────
// The quota bar appears in chat-window when isBot() = true.
// It's inside .chat-window__quota-bar (only visible for bot conversations).
// The SaiDashboard AI assistant opens a bot context via chatState.openBot('dashboard').

async function testBotQuota(page, s) {
  const issues = [];
  console.log('\n  [COMP 2] Bot Quota UI');

  // Navigate to saidashboard — the AI assistant button there opens bot chat
  await page.goto(`${BASE_URL}/saidashboard`, { waitUntil: 'networkidle', timeout: 15000 });
  await setDark(page, s.dark);
  await page.waitForTimeout(2000);

  const url = page.url();
  console.log(`  URL: ${url}`);

  await screenshot(page, `${s.name}-c2-saidashboard-initial.png`, 'SaiDashboard — initial state');

  // Look for AI assistant / bot trigger button in the saidashboard
  const botTriggerSelectors = [
    'button[aria-label*="asistente" i]',
    'button[aria-label*="bot" i]',
    'button[aria-label*="AI" i]',
    'app-ai-assistant button',
    '.ai-assistant button',
    'button:has(mat-icon:text("smart_toy"))',
    'button:has(mat-icon:text("auto_awesome"))',
    'mat-icon:text("smart_toy")',
    'mat-icon:text("auto_awesome")',
    '.assistant-fab',
    '[class*="ai-fab"]',
    '[class*="ai-button"]',
    '[class*="ai-assistant"]',
  ];

  let botOpened = false;
  for (const sel of botTriggerSelectors) {
    const found = await isVisible(page, sel, 2000);
    if (found) {
      console.log(`  Found bot trigger: ${sel}`);
      await page.locator(sel).first().click();
      await page.waitForTimeout(2000);
      botOpened = true;
      break;
    }
  }

  if (!botOpened) {
    console.log('  No bot trigger found on saidashboard — checking page DOM');
    // Dump visible buttons for debugging
    const buttons = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('button')).map(b => ({
        text: b.textContent?.trim().slice(0, 50),
        aria: b.getAttribute('aria-label'),
        classes: b.className.slice(0, 60),
      })).filter(b => b.text || b.aria);
    });
    console.log('  Visible buttons:', JSON.stringify(buttons.slice(0, 15)));

    // Try via chatState evaluation — inject via window
    await page.evaluate(() => {
      // Try Angular injection
      const el = document.querySelector('app-root') || document.body;
      const injector = el?.__ngContext__;
      console.log('Angular context:', !!injector);
    });
  }

  await screenshot(page, `${s.name}-c2-after-bot-trigger.png`, 'After bot trigger attempt');

  // Check chat panel is open with bot conversation
  const chatPanelOpen   = await isVisible(page, 'app-chat-panel[class*="open"], .chat-panel--open, [class*="chat-panel"]', 3000);
  const quotaBarFound   = await isVisible(page, '.chat-window__quota-bar', 3000);
  const botHeaderFound  = await isVisible(page, '.chat-window__bot-header', 3000);

  console.log(`  Chat panel: ${chatPanelOpen}, quota bar: ${quotaBarFound}, bot header: ${botHeaderFound}`);

  if (quotaBarFound) {
    await screenshot(page, `${s.name}-c2-quota-bar.png`, 'Bot Quota Bar — visible');

    // Check dark mode styles
    if (s.dark) {
      const styles = await page.evaluate(() => {
        const bar = document.querySelector('.chat-window__quota-bar');
        if (!bar) return null;
        const s = window.getComputedStyle(bar);
        return { bg: s.backgroundColor, border: s.borderColor };
      });
      console.log(`  Quota bar dark mode styles: ${JSON.stringify(styles)}`);

      // Hardcoded color check
      const hasHardcodedBg = await page.evaluate(() => {
        const bar = document.querySelector('.chat-window__quota-bar');
        if (!bar) return false;
        // Check if background uses CSS variable or hardcoded value
        const bg = window.getComputedStyle(bar).backgroundColor;
        // rgba(0,0,0,0) = transparent — OK
        return !bg.includes('rgba(0, 0, 0, 0)') && !bg.includes('rgba(0,0,0,0)');
      });
      console.log(`  Has background color (may be hardcoded): ${hasHardcodedBg}`);
    }

    // Mobile touch target — quota label
    if (s.width <= 375) {
      const labelBox = await boundingBox(page, '.chat-window__quota-label');
      console.log(`  Quota label bounding box: ${JSON.stringify(labelBox)}`);
    }
  } else {
    // Quota bar not found even after triggering bot
    issues.push('Bot quota bar (.chat-window__quota-bar) not visible — bot conversation may not have opened or superadmin lacks company AI quota');
  }

  // Also check if the chat-window__bot-header is present (proves bot mode)
  if (!botHeaderFound && !quotaBarFound) {
    issues.push('Bot chat panel not opened — could not find bot trigger in saidashboard or quota/header elements');
  }

  await fullshot(page, `${s.name}-c2-bot-quota-full.png`, 'Bot Quota — Full page');

  return {
    found: quotaBarFound,
    botOpened,
    botHeaderFound,
    quotaBarFound,
    issues
  };
}

// ── COMPONENT 3: Module Locked ────────────────────────────────────────────────
// Navigating as admin@andina.com who may not have CRM module.
// Route: /acceso-modulo?module=crm  (inside Shell, protected by authGuard + licenseGuard)

async function testModuleLocked(page, s, isSuper) {
  const issues = [];
  console.log('\n  [COMP 3] Module Locked');

  await page.goto(`${BASE_URL}/acceso-modulo?module=crm`, { waitUntil: 'networkidle', timeout: 15000 });
  await setDark(page, s.dark);
  await page.waitForTimeout(2000);

  const url = page.url();
  console.log(`  URL: ${url}`);

  await fullshot(page, `${s.name}-c3-module-locked-full.png`, 'Module Locked — Full page');
  await screenshot(page, `${s.name}-c3-module-locked-viewport.png`, 'Module Locked — Viewport');

  // If redirected to /admin (superadmin) that's expected behavior — test with admin instead
  if (url.includes('/admin/tenants') || url.includes('/admin')) {
    console.log('  [INFO] Superadmin redirected to /admin — checking if component has noSuperAdminGuard');
    issues.push('EXPECTED: Superadmin redirected away from /acceso-modulo — route is for non-superadmin users');
    return { found: false, redirectedFromSuperAdmin: true, issues };
  }

  if (url.includes('/auth/login')) {
    issues.push('CRITICAL: Auth guard blocking /acceso-modulo even after login — session not persisting');
    return { found: false, authBlocked: true, issues };
  }

  // Component selectors
  const mlPage      = await isVisible(page, '.ml-page');
  const mlLockIcon  = await isVisible(page, '.ml-lock-icon');
  const mlTitle     = await isVisible(page, '.ml-title');
  const mlDesc      = await isVisible(page, '.ml-desc');
  const lockMatIcon = await isVisible(page, 'mat-icon:text("lock")');

  console.log(`  .ml-page: ${mlPage}, .ml-lock-icon: ${mlLockIcon}, .ml-title: ${mlTitle}, mat-icon lock: ${lockMatIcon}`);

  const componentFound = mlPage || mlTitle || mlDesc || mlLockIcon || lockMatIcon;

  if (!componentFound) {
    issues.push('Module Locked component elements not found — page may have loaded incorrectly');
  }

  // Check text contrast
  if (s.dark && mlTitle) {
    const titleStyles = await page.evaluate(() => {
      const t = document.querySelector('.ml-title');
      if (!t) return null;
      return { color: window.getComputedStyle(t).color };
    });
    console.log(`  .ml-title dark mode color: ${JSON.stringify(titleStyles)}`);
  }

  // CTA button existence and touch target
  const ctaFound = await isVisible(page, '.ml-container button, .ml-container a[mat-raised-button]', 3000);
  if (s.width <= 375 && ctaFound) {
    const ctaBox = await boundingBox(page, '.ml-container button:visible');
    console.log(`  CTA button touch target: ${JSON.stringify(ctaBox)}`);
    if (ctaBox && (ctaBox.width < 44 || ctaBox.height < 44)) {
      issues.push(`[MOBILE] CTA button touch target ${Math.round(ctaBox.width)}x${Math.round(ctaBox.height)}px — below 44px minimum`);
    }
  }

  // Check overlap: ml-lock-icon-wrapper with content
  const overlap = await page.evaluate(() => {
    const container = document.querySelector('.ml-container');
    if (!container) return false;
    const children = Array.from(container.children);
    // Simple check: no elements overlap (bounding rect comparison)
    for (let i = 0; i < children.length - 1; i++) {
      const a = children[i].getBoundingClientRect();
      const b = children[i+1].getBoundingClientRect();
      if (a.bottom > b.top + 2) return true; // overlap
    }
    return false;
  });
  console.log(`  Element overlap detected: ${overlap}`);
  if (overlap) {
    issues.push('Elements may overlap in Module Locked component — visual inspection needed');
  }

  return { found: componentFound, mlPage, mlTitle, ctaFound, issues };
}

// ── COMPONENT 4: Tenant Form Module Cards ────────────────────────────────────
// Direct URL: /admin/tenants/:id  — Licencia tab has .tf-module-cards grid

async function testTenantModuleCards(page, s) {
  const issues = [];
  console.log('\n  [COMP 4] Tenant Form Module Cards Grid');

  // Direct URL to tenant form (edit mode)
  await page.goto(`${BASE_URL}/admin/tenants/${TENANT_ID}`, { waitUntil: 'networkidle', timeout: 15000 });
  await setDark(page, s.dark);
  await page.waitForTimeout(2500);

  const url = page.url();
  console.log(`  URL: ${url}`);

  await screenshot(page, `${s.name}-c4-tenant-form-initial.png`, 'Tenant Form — Initial');

  if (url.includes('/auth/login')) {
    issues.push('CRITICAL: Auth guard blocking /admin/tenants/:id — session lost');
    return { found: false, authBlocked: true, issues };
  }

  // Click Gestión de licencia tab
  // The tab label is "Gestión de licencia" (in edit mode)
  const licenciaTab = await page.locator('[role="tab"]:has-text("Gestión de licencia"), [role="tab"]:has-text("Licencia")').first();
  const licenciaVisible = await licenciaTab.isVisible({ timeout: 5000 }).catch(() => false);
  console.log(`  Licencia tab visible: ${licenciaVisible}`);

  if (licenciaVisible) {
    await licenciaTab.click();
    await page.waitForTimeout(2000);
    console.log('  Clicked Licencia tab');
  }

  await screenshot(page, `${s.name}-c4-licencia-tab.png`, 'Tenant Form — Licencia Tab');

  // Check for module cards section
  const modulesSection    = await isVisible(page, '.tf-modules-section');
  const moduleCards       = await isVisible(page, '.tf-module-cards');
  const moduleCard        = await isVisible(page, '.tf-module-card');
  const moduleCardHeader  = await isVisible(page, '.tf-module-card-header');
  const addButton         = await isVisible(page, 'button:has-text("Agregar")');
  const removeButton      = await isVisible(page, 'button:has-text("Quitar")');

  console.log(`  .tf-modules-section: ${modulesSection}, .tf-module-cards: ${moduleCards}, .tf-module-card: ${moduleCard}`);
  console.log(`  Agregar button: ${addButton}, Quitar button: ${removeButton}`);

  const cardsFound = modulesSection || moduleCards || moduleCard;

  await fullshot(page, `${s.name}-c4-module-cards-full.png`, 'Module Cards — Full page');

  if (!cardsFound) {
    issues.push('Module cards grid not found in Licencia tab — .tf-modules-section / .tf-module-cards missing');

    // Dump what's in the licencia tab
    const tabContent = await page.evaluate(() => {
      const panel = document.querySelector('mat-tab-body.mat-tab-body-active, .mat-mdc-tab-body-active');
      return panel ? panel.textContent?.trim().slice(0, 300) : 'No active tab panel found';
    });
    console.log(`  Active tab content preview: ${tabContent}`);
  }

  // Count cards
  const cardCount = await page.locator('.tf-module-card').count();
  console.log(`  Module card count: ${cardCount}`);

  // Mobile responsive check
  if (s.width <= 375 && moduleCards) {
    const gridStyles = await page.evaluate(() => {
      const grid = document.querySelector('.tf-module-cards');
      if (!grid) return null;
      const style = window.getComputedStyle(grid);
      return {
        display: style.display,
        gridTemplateColumns: style.gridTemplateColumns,
        overflowX: style.overflowX,
        scrollWidth: grid.scrollWidth,
        clientWidth: grid.clientWidth,
      };
    });
    console.log(`  .tf-module-cards styles: ${JSON.stringify(gridStyles)}`);

    // Check if cards overflow without scroll
    if (gridStyles && gridStyles.scrollWidth > gridStyles.clientWidth && gridStyles.overflowX === 'hidden') {
      issues.push('[MOBILE] Module cards grid overflows horizontally with overflow:hidden — cards cut off');
    }

    // Check individual card touch targets
    if (addButton) {
      const box = await boundingBox(page, 'button:has-text("Agregar")');
      console.log(`  Agregar button touch target: ${JSON.stringify(box)}`);
      if (box && (box.width < 44 || box.height < 44)) {
        issues.push(`[MOBILE] Agregar button touch target ${Math.round(box.width)}x${Math.round(box.height)}px — below 44px`);
      }
    }
  }

  // Dark mode: check for hardcoded colors in module cards
  if (s.dark && moduleCard) {
    const cardStyles = await page.evaluate(() => {
      const card = document.querySelector('.tf-module-card');
      if (!card) return null;
      const style = window.getComputedStyle(card);
      return { bg: style.backgroundColor, border: style.borderColor, color: style.color };
    });
    console.log(`  .tf-module-card dark mode styles: ${JSON.stringify(cardStyles)}`);
  }

  return { found: cardsFound, modulesSection, moduleCards, cardCount, addButton, issues };
}

// ── MAIN ─────────────────────────────────────────────────────────────────────

async function runScenario(browser, s) {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`SCENARIO: ${s.name} (${s.width}x${s.height}, dark=${s.dark})`);
  console.log('='.repeat(60));

  const scenarioIssues = [];
  const compResults    = {};

  // --- Component 3 (Module Locked) — needs admin@andina.com (non-superadmin) ---
  {
    const ctx  = await browser.newContext({ viewport: { width: s.width, height: s.height } });
    const page = await ctx.newPage();

    await loginAndWait(page, CREDS_ADMIN);
    await setDark(page, s.dark);

    const r3 = await testModuleLocked(page, s, false);
    compResults['module-locked'] = r3;
    scenarioIssues.push(...r3.issues.map(i => `[Module Locked] ${i}`));

    // While logged in as admin — also test Trial Banner
    const r1 = await testTrialBanner(page, s);
    compResults['trial-banner'] = r1;
    scenarioIssues.push(...r1.issues.map(i => `[Trial Banner] ${i}`));

    // Bot quota — needs a bot conversation to be open
    const r2 = await testBotQuota(page, s);
    compResults['bot-quota'] = r2;
    scenarioIssues.push(...r2.issues.map(i => `[Bot Quota] ${i}`));

    await ctx.close();
  }

  // --- Component 4 (Tenant Module Cards) — needs superadmin ---
  {
    const ctx  = await browser.newContext({ viewport: { width: s.width, height: s.height } });
    const page = await ctx.newPage();

    await loginAndWait(page, CREDS_SUPER);
    await setDark(page, s.dark);

    const r4 = await testTenantModuleCards(page, s);
    compResults['module-cards'] = r4;
    scenarioIssues.push(...r4.issues.map(i => `[Module Cards] ${i}`));

    await ctx.close();
  }

  results.per_component[s.name] = {
    viewport: `${s.width}x${s.height}`,
    dark: s.dark,
    results: compResults,
    issues: scenarioIssues,
  };

  console.log(`\nSCENARIO COMPLETE: ${scenarioIssues.length} issues`);
  scenarioIssues.forEach(i => console.log(`  [ISSUE] ${i}`));
  results.issues.push(...scenarioIssues);
}

async function main() {
  console.log('EvidenceQA — Targeted 4x4 Component Validation (Pass 2)');
  console.log(`Output: ${OUTPUT_DIR}`);

  const browser = await chromium.launch({ headless: true });

  for (const s of SCENARIOS) {
    await runScenario(browser, s);
  }

  await browser.close();

  fs.writeFileSync(
    path.join(OUTPUT_DIR, 'test-results-targeted.json'),
    JSON.stringify(results, null, 2)
  );

  console.log('\n\n========= FINAL QA SUMMARY =========');
  console.log(`Total screenshots: ${results.screenshots.length}`);
  console.log(`Total issues: ${results.issues.length}`);
  results.issues.forEach(i => console.log(`  ${i}`));
}

main().catch(console.error);

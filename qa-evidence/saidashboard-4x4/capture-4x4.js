/**
 * SaiDashboard 4x4 Visual Validation Script
 * Scenarios: Desktop/Mobile × Light/Dark
 * QA Agent: EvidenceQA
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const OUTPUT_DIR = '/Users/juanandrade/Desktop/saisuite/qa-evidence/saidashboard-4x4';
const BASE_URL = 'http://localhost:4200';
const CREDENTIALS = { email: 'admin@andina.com', password: 'Admin1234!' };

const SCENARIOS = [
  { name: '1-desktop-light', width: 1920, height: 1080, dark: false },
  { name: '2-desktop-dark',  width: 1920, height: 1080, dark: true  },
  { name: '3-mobile-light',  width: 375,  height: 812,  dark: false },
  { name: '4-mobile-dark',   width: 375,  height: 812,  dark: true  },
];

async function login(page) {
  await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 15000 });
  // If already logged in (redirected to app), skip login
  if (!page.url().includes('/auth/')) {
    console.log('  Already authenticated — skipping login');
    return;
  }
  console.log('  Logging in as', CREDENTIALS.email);
  await page.fill('input[type="email"], input[name="email"], input[formcontrolname="email"]', CREDENTIALS.email);
  await page.fill('input[type="password"], input[name="password"], input[formcontrolname="password"]', CREDENTIALS.password);
  await page.click('button[type="submit"]');
  await page.waitForNavigation({ timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(1500);
}

async function enableDarkMode(page) {
  // Try clicking the theme toggle in topbar
  const toggleSelectors = [
    '[data-testid="theme-toggle"]',
    'button[aria-label*="dark"], button[aria-label*="Dark"]',
    'button[aria-label*="tema"], button[aria-label*="Tema"]',
    'mat-icon:text("dark_mode")',
    '.theme-toggle',
    '[class*="theme"]',
  ];

  for (const sel of toggleSelectors) {
    const el = page.locator(sel).first();
    if (await el.isVisible({ timeout: 1000 }).catch(() => false)) {
      await el.click();
      await page.waitForTimeout(500);
      console.log(`  Dark mode toggled via: ${sel}`);
      return true;
    }
  }

  // Fallback: use JavaScript to add dark-theme class to body
  const isDark = await page.evaluate(() => {
    const body = document.body;
    if (body.classList.contains('dark-theme')) {
      return true;
    }
    body.classList.add('dark-theme');
    return true;
  });
  console.log(`  Dark mode via JS class injection: ${isDark}`);
  await page.waitForTimeout(500);
  return isDark;
}

async function disableDarkMode(page) {
  await page.evaluate(() => {
    document.body.classList.remove('dark-theme');
  });
  await page.waitForTimeout(300);
}

async function captureScreenshot(page, filename, fullPage = false) {
  const filepath = path.join(OUTPUT_DIR, filename);
  await page.screenshot({ path: filepath, fullPage });
  console.log(`  Screenshot: ${filename}`);
  return filepath;
}

async function measureTouchTargets(page) {
  // Check all interactive elements for touch target size
  const results = await page.evaluate(() => {
    const selectors = ['button', 'a', '[role="button"]', 'mat-list-item', '.mat-mdc-list-item'];
    const issues = [];
    selectors.forEach(sel => {
      document.querySelectorAll(sel).forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0 && (rect.width < 44 || rect.height < 44)) {
          issues.push({
            tag: el.tagName,
            text: (el.textContent || '').trim().substring(0, 50),
            width: Math.round(rect.width),
            height: Math.round(rect.height),
          });
        }
      });
    });
    return issues;
  });
  return results;
}

async function checkHorizontalScroll(page) {
  return await page.evaluate(() => {
    return document.documentElement.scrollWidth > document.documentElement.clientWidth;
  });
}

async function checkDarkModeActive(page) {
  return await page.evaluate(() => {
    return document.body.classList.contains('dark-theme') ||
           document.documentElement.classList.contains('dark-theme') ||
           document.body.getAttribute('data-theme') === 'dark';
  });
}

async function getSidebarContent(page) {
  return await page.evaluate(() => {
    const sidebar = document.querySelector('mat-sidenav, aside, nav, [class*="sidebar"], [class*="nav"]');
    return sidebar ? sidebar.textContent.trim().substring(0, 500) : 'SIDEBAR_NOT_FOUND';
  });
}

async function checkSaiDashboardSidebar(page) {
  const text = await getSidebarContent(page);
  return {
    hasModule: text.includes('Dashboard') || text.includes('dashboard'),
    hasMisDashboards: text.includes('Mis Dashboards') || text.includes('dashboards'),
    hasNuevoDashboard: text.includes('Nuevo') || text.includes('nuevo'),
    rawText: text.substring(0, 300),
  };
}

async function runScenario(browser, scenario) {
  console.log(`\n=== SCENARIO ${scenario.name} (${scenario.width}x${scenario.height}, dark=${scenario.dark}) ===`);

  const context = await browser.newContext({
    viewport: { width: scenario.width, height: scenario.height },
  });
  const page = await context.newPage();

  const report = {
    scenario: scenario.name,
    viewport: `${scenario.width}x${scenario.height}`,
    dark: scenario.dark,
    screenshots: [],
    issues: [],
    checks: {},
  };

  // Step 1: Login
  await login(page);

  // Step 2: Enable dark mode if needed
  if (scenario.dark) {
    // First navigate to app to have toggle available
    await page.goto(`${BASE_URL}/saidashboard`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1000);
    await enableDarkMode(page);
  }

  // Step 3: Navigate to SaiDashboard
  await page.goto(`${BASE_URL}/saidashboard`, { waitUntil: 'networkidle', timeout: 15000 });
  await page.waitForTimeout(2000);

  const currentUrl = page.url();
  report.checks.navigatedUrl = currentUrl;
  report.checks.reachedSaiDashboard = currentUrl.includes('saidashboard');

  // Screenshot: Main listing page (viewport)
  const mainShot = `${scenario.name}-01-saidashboard-list.png`;
  await captureScreenshot(page, mainShot, false);
  report.screenshots.push(mainShot);

  // Screenshot: Full page
  const fullShot = `${scenario.name}-02-saidashboard-list-full.png`;
  await captureScreenshot(page, fullShot, true);
  report.screenshots.push(fullShot);

  // Check sidebar
  const sidebar = await checkSaiDashboardSidebar(page);
  report.checks.sidebar = sidebar;
  if (!sidebar.hasModule) report.issues.push('Sidebar does not show SaiDashboard module');
  if (!sidebar.hasMisDashboards) report.issues.push('Sidebar missing "Mis Dashboards" item');
  if (!sidebar.hasNuevoDashboard) report.issues.push('Sidebar missing "Nuevo Dashboard" item');

  // Check horizontal scroll
  const hasHScroll = await checkHorizontalScroll(page);
  report.checks.hasHorizontalScroll = hasHScroll;
  if (hasHScroll && scenario.width <= 768) {
    report.issues.push('CRITICAL: Horizontal scroll detected on mobile viewport');
  }

  // Check dark mode is actually active
  if (scenario.dark) {
    const darkActive = await checkDarkModeActive(page);
    report.checks.darkModeActive = darkActive;
    if (!darkActive) {
      report.issues.push('Dark mode class not found on body/html — theme may not be applied');
    }
  }

  // Check touch targets on mobile
  if (scenario.width <= 768) {
    const smallTargets = await measureTouchTargets(page);
    report.checks.touchTargetIssues = smallTargets.length;
    if (smallTargets.length > 0) {
      report.issues.push(`${smallTargets.length} elements with touch target < 44px: ${JSON.stringify(smallTargets.slice(0, 3))}`);
    }
  }

  // Screenshot: Sidebar close-up (scroll to sidebar area)
  try {
    const sidebar_el = page.locator('mat-sidenav, aside, [class*="sidebar"]').first();
    if (await sidebar_el.isVisible({ timeout: 2000 }).catch(() => false)) {
      const sidebarShot = `${scenario.name}-03-sidebar.png`;
      await sidebar_el.screenshot({ path: path.join(OUTPUT_DIR, sidebarShot) }).catch(() => {});
      report.screenshots.push(sidebarShot);
    }
  } catch (e) {
    console.log('  Could not capture sidebar screenshot:', e.message);
  }

  // Try to find and click an existing dashboard
  const dashboardCards = page.locator('mat-card, .dashboard-card, [class*="dashboard-item"]');
  const cardCount = await dashboardCards.count();
  report.checks.dashboardCount = cardCount;

  if (cardCount > 0) {
    console.log(`  Found ${cardCount} dashboard card(s) — clicking first one`);
    await dashboardCards.first().click();
    await page.waitForTimeout(2000);

    const viewerShot = `${scenario.name}-04-dashboard-viewer.png`;
    await captureScreenshot(page, viewerShot, false);
    report.screenshots.push(viewerShot);

    const viewerFullShot = `${scenario.name}-05-dashboard-viewer-full.png`;
    await captureScreenshot(page, viewerFullShot, true);
    report.screenshots.push(viewerFullShot);
  } else {
    console.log('  No dashboard cards found — checking for trial/empty state');
    const emptyShot = `${scenario.name}-04-empty-or-trial-state.png`;
    await captureScreenshot(page, emptyShot, true);
    report.screenshots.push(emptyShot);
  }

  // Check page title / heading
  const heading = await page.locator('h1, h2, [class*="title"], mat-toolbar-row').first().textContent().catch(() => 'NOT_FOUND');
  report.checks.pageHeading = (heading || '').trim().substring(0, 100);

  await context.close();
  return report;
}

async function main() {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const browser = await chromium.launch({
    headless: true,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  });
  const reports = [];

  for (const scenario of SCENARIOS) {
    const report = await runScenario(browser, scenario);
    reports.push(report);
  }

  await browser.close();

  // Write JSON report
  const reportPath = path.join(OUTPUT_DIR, 'qa-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(reports, null, 2));
  console.log('\n=== ALL SCENARIOS COMPLETE ===');
  console.log('Report saved to:', reportPath);

  // Print summary
  reports.forEach(r => {
    console.log(`\n[${r.scenario}]`);
    console.log('  URL reached:', r.checks.navigatedUrl);
    console.log('  Reached SaiDashboard:', r.checks.reachedSaiDashboard);
    console.log('  Dashboard cards found:', r.checks.dashboardCount);
    console.log('  Horizontal scroll:', r.checks.hasHorizontalScroll);
    console.log('  Sidebar:', JSON.stringify(r.checks.sidebar));
    if (r.dark) console.log('  Dark mode active:', r.checks.darkModeActive);
    console.log('  Issues:', r.issues.length ? r.issues : 'NONE');
  });
}

main().catch(err => {
  console.error('FATAL ERROR:', err);
  process.exit(1);
});

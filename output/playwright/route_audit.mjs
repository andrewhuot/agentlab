import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const playwrightModule = await import(
  pathToFileURL(
    path.resolve('web/node_modules/@playwright/test/index.mjs')
  ).href
);
const { chromium } = playwrightModule;

const base = 'http://localhost:5173';
const routes = [
  '/',
  '/builder',
  '/builder/demo',
  '/dashboard',
  '/demo',
  '/evals',
  '/optimize',
  '/live-optimize',
  '/configs',
  '/conversations',
  '/deploy',
  '/loop',
  '/opportunities',
  '/experiments',
  '/traces',
  '/events',
  '/autofix',
  '/judge-ops',
  '/context',
  '/changes',
  '/runbooks',
  '/skills',
  '/intelligence',
  '/memory',
  '/registry',
  '/blame',
  '/scorer-studio',
  '/cx/import',
  '/cx/deploy',
  '/adk/import',
  '/adk/deploy',
  '/agent-skills',
  '/agent-studio',
  '/assistant',
  '/notifications',
  '/sandbox',
  '/knowledge',
  '/what-if',
  '/reviews',
  '/reward-studio',
  '/preference-inbox',
  '/policy-candidates',
  '/reward-audit',
  '/settings',
];

const outputDir = path.resolve('output/playwright');
await fs.mkdir(outputDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const results = [];

for (const route of routes) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
  const consoleErrors = [];
  const pageErrors = [];
  const requestFailures = [];
  const badResponses = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });
  page.on('pageerror', (error) => {
    pageErrors.push(error.message);
  });
  page.on('requestfailed', (request) => {
    const failure = request.failure();
    requestFailures.push(
      `${request.method()} ${request.url()} :: ${failure?.errorText || 'unknown'}`
    );
  });
  page.on('response', (response) => {
    if (response.status() >= 400) {
      badResponses.push(`${response.status()} ${response.url()}`);
    }
  });

  let status = 'pass';
  let gotoError = null;

  try {
    await page.goto(`${base}${route}`, {
      waitUntil: 'domcontentloaded',
      timeout: 15000,
    });
    await page.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {});
    await page.waitForTimeout(750);
  } catch (error) {
    status = 'fail';
    gotoError = error instanceof Error ? error.message : String(error);
  }

  const bodyText = await page.locator('body').innerText().catch(() => '');
  const title = await page.title().catch(() => '');

  const ignorable = (entry) => entry.includes('/favicon.ico');
  const filteredConsoleErrors = consoleErrors.filter((entry) => !ignorable(entry));
  const filteredRequestFailures = requestFailures.filter((entry) => !ignorable(entry));
  const filteredBadResponses = badResponses.filter((entry) => !ignorable(entry));

  if (
    gotoError ||
    filteredConsoleErrors.length > 0 ||
    pageErrors.length > 0 ||
    filteredRequestFailures.length > 0 ||
    filteredBadResponses.length > 0
  ) {
    status = 'fail';
    const safeName =
      route === '/' ? 'root' : route.replace(/^\//, '').replace(/[/?#:&=]/g, '_');
    await page
      .screenshot({
        path: path.join(outputDir, `${safeName}.png`),
        fullPage: true,
      })
      .catch(() => {});
  }

  results.push({
    route,
    status,
    title,
    gotoError,
    consoleErrors: filteredConsoleErrors,
    pageErrors,
    requestFailures: filteredRequestFailures,
    badResponses: filteredBadResponses,
    bodyPreview: bodyText.slice(0, 240).replace(/\s+/g, ' '),
  });

  await page.close();
}

await browser.close();
console.log(JSON.stringify(results, null, 2));

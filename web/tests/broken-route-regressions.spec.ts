import { test, expect } from '@playwright/test';

const baseUrl = 'http://localhost:5173';
const routes = [
  '/context',
  '/changes',
  '/registry',
  '/blame',
  '/scorer-studio',
  '/reward-studio',
  '/preference-inbox',
  '/policy-candidates',
];

for (const route of routes) {
  test(`route ${route} loads without runtime or API errors`, async ({ page }) => {
    const consoleErrors: string[] = [];
    const pageErrors: string[] = [];
    const requestFailures: string[] = [];
    const badResponses: string[] = [];

    const ignorable = (entry: string) => entry.includes('/favicon.ico');

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

    await page.goto(`${baseUrl}${route}`, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle').catch(() => {});
    await page.waitForTimeout(750);

    const filteredConsoleErrors = consoleErrors.filter((entry) => !ignorable(entry));
    const filteredRequestFailures = requestFailures.filter((entry) => !ignorable(entry));
    const filteredBadResponses = badResponses.filter((entry) => !ignorable(entry));

    expect(pageErrors).toEqual([]);
    expect(filteredConsoleErrors).toEqual([]);
    expect(filteredRequestFailures).toEqual([]);
    expect(filteredBadResponses).toEqual([]);
    await expect(page.locator('body')).not.toBeEmpty();
  });
}

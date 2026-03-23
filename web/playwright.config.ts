import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 30000,
  use: {
    browserName: 'chromium',
    viewport: { width: 1440, height: 900 },
    actionTimeout: 5000,
  },
  reporter: 'list',
});

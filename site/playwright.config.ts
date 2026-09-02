import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL: "http://127.0.0.1:4173/fan-unification-platform",
    browserName: "chromium",
  },
  webServer: {
    command: "python ../scripts/serve_built_site.py --port 4173",
    url: "http://127.0.0.1:4173/fan-unification-platform/",
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
});

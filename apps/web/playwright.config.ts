import { defineConfig, devices } from "@playwright/test";

/**
 * E2E runs against the REAL stack: FastAPI (uvicorn, repo root) on :8000 and the production Next.js build on :3100.
 * Build first:  npm run build   (NEXT_PUBLIC_API_URL defaults to http://127.0.0.1:8000)
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 90_000,
  expect: { timeout: 20_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:3100",
    acceptDownloads: true,
    trace: "retain-on-failure",
    viewport: { width: 1440, height: 900 },
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } }],
  webServer: [
    {
      command: "python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000",
      cwd: "../..",
      env: { ALLOWED_ORIGINS: "http://localhost:3100,http://localhost:3000" },
      url: "http://127.0.0.1:8000/api/v1/health",
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: "npx next start -p 3100",
      url: "http://localhost:3100",
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});

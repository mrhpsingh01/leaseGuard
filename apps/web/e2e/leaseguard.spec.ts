import { test, expect, Page } from "@playwright/test";
import * as fs from "fs";

const PRESET_1 = "Preset 1: Athens Off-Campus Student Lease";
const PRESET_2 = "Preset 2: Move-Out Security Deposit Dispute";

async function runPreset1(page: Page) {
  await page.getByRole("button", { name: PRESET_1 }).click();
  // The SSE stream finishes when the `complete` event delivers the page images, which mounts the overlays.
  await expect(page.locator('[data-highlight="true"]')).toHaveCount(5);
  await expect(page.getByTestId("risk-card")).toHaveCount(5);
}

test("zero-login landing renders the split-screen workspace immediately", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("workspace")).toBeVisible();
  await expect(page.getByTestId("scenario-bar")).toBeVisible();
  await expect(page.getByRole("button", { name: "Load Sample Athens Student Lease (Zero Login)" })).toBeVisible();
  await expect(page.locator('input[type="password"]')).toHaveCount(0);
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByText(/sign in|log in/i)).toHaveCount(0);
  // the sample audit auto-starts: no click required to see results
  await expect(page.getByTestId("risk-card")).toHaveCount(5);
});

test("Preset 1: 5 risk cards, 5 PDF highlights, card click scrolls and selects the highlight", async ({ page }) => {
  await page.goto("/");
  await runPreset1(page);

  const container = page.getByTestId("pdf-scroll-container");
  const cards = page.getByTestId("risk-card");

  // Jump to the last clause (page 3) so the container is scrolled away from Risk Card #1.
  await cards.nth(4).click();
  await expect(page.locator('[data-highlight="true"][data-selected="true"]')).toHaveCount(1);
  await expect.poll(() => container.evaluate((el) => el.scrollTop)).toBeGreaterThan(500);
  const scrolledAway = await container.evaluate((el) => el.scrollTop);

  const firstId = await cards.nth(0).getAttribute("data-clause-id");
  await cards.nth(0).click();
  const target = page.getByTestId(`highlight-${firstId}`);
  await expect(target).toHaveAttribute("data-selected", "true");
  await expect.poll(() => container.evaluate((el) => el.scrollTop)).toBeLessThan(scrolledAway);

  // the targeted highlight is actually inside the visible part of the PDF container
  await expect
    .poll(async () => {
      const c = await container.boundingBox();
      const t = await target.boundingBox();
      return !!c && !!t && t.y >= c.y - 2 && t.y + t.height <= c.y + c.height + 2;
    })
    .toBe(true);
});

test("counter-clause copy, then Preset 2 demand-letter export downloads a valid PDF", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto("/");
  await runPreset1(page);

  await page.getByRole("button", { name: "Copy Tenant Counter-Clause" }).first().click();
  await expect(page.getByText("Copied!").first()).toBeVisible();
  const clip = await page.evaluate(() => navigator.clipboard.readText());
  expect(clip).toContain("Security Deposit");
  expect(clip).toContain("2,300.00");

  await page.getByRole("button", { name: PRESET_2 }).click();
  await expect(page.getByTestId("deposit-shield")).toBeVisible();
  await expect(page.getByTestId("inspection-days")).toContainText("6 business days");
  await expect(page.getByTestId("return-days")).toContainText("38 calendar days");
  await expect(page.getByTestId("treble-amount")).toContainText("$2,550.00");

  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "Export Formal Demand Letter (PDF)" }).click(),
  ]);
  expect(download.suggestedFilename()).toMatch(/\.pdf$/);
  const saved = await download.path();
  expect(saved).toBeTruthy();
  const bytes = fs.readFileSync(saved!);
  expect(bytes.subarray(0, 5).toString("latin1")).toBe("%PDF-");
  expect(bytes.length).toBeGreaterThan(2048);
});

test("Hiring Manager drawer shows live non-zero telemetry and the raw JSON inspector", async ({ page }) => {
  await page.goto("/");
  await runPreset1(page);

  await page.getByRole("button", { name: "Hiring Manager View: Inspect Live Pipeline" }).click();
  const drawer = page.getByTestId("telemetry-drawer");
  await expect(drawer).toBeVisible();

  const latency = Number(await page.getByTestId("extraction-latency-ms").getAttribute("data-value"));
  expect(latency).toBeGreaterThan(0);
  expect(Number(await page.getByTestId("pii-count").innerText())).toBe(4);

  const rows = page.getByTestId("retrieval-row");
  await expect(rows).toHaveCount(5);
  for (let i = 0; i < 5; i++) {
    const cells = await rows.nth(i).locator("td").allInnerTexts();
    const [bm25, vector, rrf] = cells.slice(1).map(Number);
    expect(bm25).toBeGreaterThan(0);
    expect(vector).toBeGreaterThan(0);
    expect(rrf).toBeGreaterThan(0);
  }

  await drawer.getByRole("button", { name: /Raw Pydantic JSON/ }).click();
  const json = await page.getByTestId("raw-json").innerText();
  expect(json).toContain('"flagged_risks"');
  expect(json).toContain('"verbatim_lease_quote"');
});

test("network failure shows a visible retry banner and recovers", async ({ page }) => {
  await page.route("**/api/v1/leases/analyze-stream", (route) => route.abort("connectionrefused"));
  await page.goto("/");
  const banner = page.getByTestId("error-banner");
  await expect(banner).toBeVisible();
  await expect(banner).toContainText(/could not reach|too long/i);

  await page.unroute("**/api/v1/leases/analyze-stream");
  await banner.getByRole("button", { name: "Retry" }).click();
  await expect(page.getByTestId("risk-card")).toHaveCount(5);
  await expect(banner).toHaveCount(0);
});

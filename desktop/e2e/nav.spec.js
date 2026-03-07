// Block 84: E2E — navigation and tab switching (frontend only; no Tauri backend).
import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await page.evaluate(() => localStorage.setItem("voiceforge_onboarding_dismissed", "true"));
  await page.reload();
});

test.describe("Desktop UI navigation", () => {
  test("loads app and shows main layout", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("#main-sidebar")).toBeVisible();
    await expect(page.locator("#main-content")).toBeVisible();
    await expect(page.locator("#app-root")).toBeVisible();
  });

  test("home tab is active by default", async ({ page }) => {
    await page.goto("/");
    const homePanel = page.locator("#tab-home");
    await expect(homePanel).toBeVisible();
    await expect(homePanel).toHaveClass(/active/);
  });

  test("home tab shows quick actions (block 37)", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("#tab-home.active")).toBeVisible();
    await expect(page.locator("#listen-toggle")).toBeVisible();
    await expect(page.locator("#quick-analyze-60")).toBeVisible();
  });

  test("switching tabs updates visible panel", async ({ page }) => {
    await expect(page.locator("#tab-home")).toBeVisible();

    await page.getByRole("navigation").locator("[data-tab='sessions']").click();
    await expect(page.locator("#tab-sessions")).toBeVisible();
    await expect(page.locator("#tab-sessions")).toHaveClass(/active/);

    await page.getByRole("navigation").locator("[data-tab='costs']").click();
    await expect(page.locator("#tab-costs")).toBeVisible();
    await expect(page.locator("#tab-costs")).toHaveClass(/active/);

    await page.getByRole("navigation").locator("[data-tab='settings']").click();
    await expect(page.locator("#tab-settings")).toBeVisible();
    await expect(page.locator("#tab-settings")).toHaveClass(/active/);

    await page.getByRole("navigation").locator("[data-tab='home']").click();
    await expect(page.locator("#tab-home")).toHaveClass(/active/);
  });

  test("settings tab shows language selector (block 97)", async ({ page }) => {
    await page.getByRole("navigation").locator("[data-tab='settings']").click();
    await expect(page.locator("#tab-settings.active")).toBeVisible();
    await expect(page.getByRole("heading", { name: /Настройки|Settings/ })).toBeVisible();
    const langSelect = page.getByLabel(/Язык интерфейса|Interface language/i);
    await expect(langSelect).toBeVisible();
    await expect(langSelect.locator("option[value=ru]")).toHaveCount(1);
    await expect(langSelect.locator("option[value=en]")).toHaveCount(1);
  });

  test("costs tab shows period and export buttons", async ({ page }) => {
    await page.getByRole("navigation").locator("[data-tab='costs']").click();
    await expect(page.locator("#tab-costs.active")).toBeVisible();
    await expect(page.locator("#costs-7d")).toBeVisible();
    await expect(page.locator("#costs-30d")).toBeVisible();
    await expect(page.locator("#costs-export-btn")).toBeVisible();
  });

  test("sessions tab shows search and filters", async ({ page }) => {
    await page.getByRole("navigation").locator("[data-tab='sessions']").click();
    await expect(page.locator("#tab-sessions.active")).toBeVisible();
    await expect(page.locator("#sessions-search")).toBeVisible();
    await expect(page.locator("#sessions-fts-search")).toBeVisible();
    await expect(page.locator("#sessions-period")).toBeVisible();
    await expect(page.locator("#sessions-export-btn")).toBeVisible();
  });
});

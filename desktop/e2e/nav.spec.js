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
});

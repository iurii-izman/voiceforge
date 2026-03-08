import { expect, test } from "@playwright/test";

import { installDesktopMocks } from "./helpers/desktopHarness";

async function dismissOnboarding(page) {
  await page.waitForTimeout(200);
  await page.evaluate(() => {
    localStorage.setItem("voiceforge_onboarding_dismissed", "true");
    const overlay = document.getElementById("onboarding-overlay");
    if (!overlay) return;
    overlay.close?.();
    overlay.removeAttribute("open");
    overlay.style.display = "none";
  });
}

test.beforeEach(async ({ page }) => {
  await installDesktopMocks(page);
  await page.goto("/");
  await dismissOnboarding(page);
});

test.describe("Desktop visual regression", () => {
  test("home dashboard matches baseline", async ({ page }) => {
    await expect(page).toHaveScreenshot("home-dashboard.png", {
      animations: "disabled",
      caret: "hide",
      fullPage: true,
    });
  });

  test("sessions list matches baseline", async ({ page }) => {
    await page.getByRole("navigation").locator("[data-tab='sessions']").click();
    await expect(page).toHaveScreenshot("sessions-list.png", {
      animations: "disabled",
      caret: "hide",
      fullPage: true,
    });
  });

  test("settings slide panel matches baseline", async ({ page }) => {
    await page.getByRole("navigation").locator("[data-tab='settings']").click();
    await expect(page).toHaveScreenshot("settings-slide-panel.png", {
      animations: "disabled",
      caret: "hide",
      fullPage: true,
    });
  });
});

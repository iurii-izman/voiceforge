import AxeBuilder from "@axe-core/playwright";
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

async function expectNoSeriousA11yViolations(page, name) {
  const results = await new AxeBuilder({ page }).analyze();
  const blocking = results.violations.filter((violation) =>
    ["serious", "critical"].includes(violation.impact || ""),
  );
  expect(blocking, `${name}: ${blocking.map((item) => item.id).join(", ")}`).toEqual([]);
}

test.beforeEach(async ({ page }) => {
  await installDesktopMocks(page);
  await page.goto("/");
  await dismissOnboarding(page);
});

test.describe("Desktop accessibility autopilot", () => {
  test("home screen has no serious accessibility violations", async ({ page }) => {
    await expect(page.getByRole("main")).toBeVisible();
    await expectNoSeriousA11yViolations(page, "home");
    await expect(page.locator("#main-sidebar")).toMatchAriaSnapshot(`
      - navigation "Главное меню":
        - button "Главная"
        - button "Сессии"
        - button "Затраты"
        - button "Настройки"
    `);
  });

  test("sessions screen has no serious accessibility violations", async ({ page }) => {
    await page.getByRole("navigation").locator("[data-tab='sessions']").click();
    await expect(page.locator("#tab-sessions.active")).toBeVisible();
    await expectNoSeriousA11yViolations(page, "sessions");
  });

  test("settings slide-out panel has no serious accessibility violations", async ({ page }) => {
    await page.getByRole("navigation").locator("[data-tab='settings']").click();
    await expect(page.locator("#settings-slide-panel")).toHaveClass(/open/);
    await expectNoSeriousA11yViolations(page, "settings-panel");
  });
});

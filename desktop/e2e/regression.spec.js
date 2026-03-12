import { expect, test } from "@playwright/test";

import { installDesktopMocks } from "./helpers/desktopHarness";

async function dismissOnboarding(page) {
  const overlay = page.locator("#onboarding-overlay");
  if (await overlay.isVisible().catch(() => false)) {
    await page.waitForFunction(() => typeof document.getElementById("onboarding-ok")?.onclick === "function");
    await page.locator("#onboarding-ok").click();
    await expect(overlay).not.toBeVisible();
  }
}

async function bootDesktop(page, overrides = {}) {
  await installDesktopMocks(page, { onboardingDismissed: false, compactMode: false, ...overrides });
  await page.goto("/");
  await dismissOnboarding(page);
}

test.describe("Desktop regression matrix", () => {
  test("recent session widget opens detail and keeps navigation recoverable after close", async ({ page }) => {
    await bootDesktop(page);

    await page.locator("#recent-sessions-list .btn-link[data-session-id='101']").click();
    await expect(page.locator("#tab-sessions")).toHaveClass(/active/);
    await expect(page.locator("#session-detail")).toBeVisible();
    await expect(page.locator("#session-detail-body")).toContainText("Обсудили релиз alpha.");

    await page.locator("#session-detail-close").click();
    await expect(page.locator("#session-detail")).not.toBeVisible();
    await expect(page.locator("#tab-sessions")).toHaveClass(/active/);
    await expect(page.locator("#sessions-list")).toBeVisible();

    await page.getByRole("navigation").locator("[data-tab='home']").click();
    await expect(page.locator("#tab-home")).toHaveClass(/active/);
    await expect(page.locator("#quick-analyze-60")).toBeVisible();
  });

  test("settings slide panel can close and reopen without trapping navigation", async ({ page }) => {
    await bootDesktop(page);

    await page.getByRole("navigation").locator("[data-tab='settings']").click();
    await expect(page.locator("#settings-slide-panel")).toHaveClass(/open/);

    await page.locator("#settings-panel-close").click();
    await expect(page.locator("#settings-slide-panel")).not.toHaveClass(/open/);
    await expect(page.locator("#tab-home")).toHaveClass(/active/);

    await page.getByRole("navigation").locator("[data-tab='settings']").click();
    await expect(page.locator("#settings-slide-panel")).toHaveClass(/open/);

    await page.keyboard.press("Escape");
    await expect(page.locator("#settings-slide-panel")).not.toHaveClass(/open/);

    await page.getByRole("navigation").locator("[data-tab='sessions']").click();
    await expect(page.locator("#tab-sessions")).toHaveClass(/active/);
    await expect(page.locator("#sessions-list")).toBeVisible();
  });

  test("settings persistence keeps safe defaults and survives reload", async ({ page }) => {
    await bootDesktop(page);

    await page.getByRole("navigation").locator("[data-tab='settings']").click();
    await expect(page.locator("#settings-slide-panel")).toHaveClass(/open/);

    await expect(page.locator("#settings-as-panel")).toBeChecked();
    await expect(page.locator("#hotkeys-enabled")).toBeChecked();
    await expect(page.locator("#close-to-tray")).not.toBeChecked();
    await expect(page.locator("#compact-mode-toggle")).not.toBeChecked();

    await page.locator("#close-to-tray").check();
    await page.locator("#hotkeys-enabled").uncheck();

    await page.reload();
    await dismissOnboarding(page);
    await page.getByRole("navigation").locator("[data-tab='settings']").click();

    await expect(page.locator("#settings-slide-panel")).toHaveClass(/open/);
    await expect(page.locator("#settings-as-panel")).toBeChecked();
    await expect(page.locator("#close-to-tray")).toBeChecked();
    await expect(page.locator("#hotkeys-enabled")).not.toBeChecked();
    await expect.poll(async () => page.evaluate(() => localStorage.getItem("voiceforge_close_to_tray"))).toBe("true");
    await expect.poll(async () => page.evaluate(() => localStorage.getItem("voiceforge_hotkeys_enabled"))).toBe("false");
  });

  test("compact mode survives reload and can recover back to full mode", async ({ page }) => {
    await bootDesktop(page);

    await page.getByRole("navigation").locator("[data-tab='settings']").click();
    await page.locator("#compact-mode-toggle").check();

    await expect(page.locator("#compact-bar")).toBeVisible();
    await expect(page.locator("#full-content")).not.toBeVisible();

    await page.reload();
    await dismissOnboarding(page);
    await expect(page.locator("#compact-bar")).toBeVisible();
    await expect(page.locator("#full-content")).not.toBeVisible();
    await expect.poll(async () => page.evaluate(() => localStorage.getItem("voiceforge_compact_mode"))).toBe("true");

    await page.locator("#compact-expand").click();
    await expect(page.locator("#compact-bar")).toBeHidden();
    await expect(page.locator("#full-content")).toBeVisible();
    await expect(page.locator("#tab-home")).toHaveClass(/active/);
  });

  test("daemon unavailable state recovers cleanly after retry without trapping the user", async ({ page }) => {
    await bootDesktop(page, { daemonAvailable: false, onboardingDismissed: true });

    await expect(page.locator("#daemon-off-banner")).toBeVisible();
    await expect(page.locator("#listen-toggle")).toBeDisabled();
    await expect(page.locator("#analyze-btn")).toBeDisabled();

    await page.evaluate(() => {
      globalThis.__VOICEFORGE_TEST_STATE__.daemonAvailable = true;
    });
    await page.locator("#daemon-retry-btn").click();

    await expect(page.locator("#daemon-off-banner")).toBeHidden();
    await expect(page.locator("#listen-toggle")).toBeEnabled();
    await expect(page.locator("#analyze-btn")).toBeEnabled();
    await expect(page.locator("#recent-sessions-list")).toContainText("Сессия 101");
    await expect(page.locator("#upcoming-events-content")).toContainText("Sprint Review");
    await expect(page.locator("#last-analysis-content")).toContainText("Добавить visual regression");
    await expect(page.locator("#cost-widget-content")).toContainText("$1.2345");

    await page.getByRole("navigation").locator("[data-tab='sessions']").click();
    await expect(page.locator("#tab-sessions")).toHaveClass(/active/);
    await expect(page.locator("#sessions-list")).toBeVisible();
  });

  test("english ui localizes runtime empty states and widget copy", async ({ page }) => {
    await bootDesktop(page, {
      language: "en",
      sessions: [],
      upcomingEvents: [],
      sessionDetails: {},
      onboardingDismissed: true,
    });

    await expect(page.locator("#status-bar")).toHaveText(/Daemon available/);
    await expect(page.locator("#recent-sessions-list")).toContainText("No sessions yet");
    await expect(page.locator("#upcoming-events-content")).toContainText("No events in the next 48 h.");
    await expect(page.locator("#upcoming-events-content")).toContainText("CalDAV setup");
    await expect(page.locator("#last-analysis-content")).toContainText("No analyzed sessions yet.");

    await page.getByRole("navigation").locator("[data-tab='sessions']").click();
    await expect(page.locator("#sessions-list")).toContainText("No sessions yet");

    await page.getByRole("navigation").locator("[data-tab='settings']").click();
    await expect(page.locator("#settings-content")).toContainText("Default LLM");
    await expect(page.locator("#settings-content")).toContainText("Daemon version:");
  });
});

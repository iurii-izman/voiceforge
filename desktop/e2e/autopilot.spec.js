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
  await expect(page.locator("#quick-analyze-60")).toBeVisible();
});

test.describe("Desktop QA autopilot", () => {
  test("loads healthy mocked desktop with interactive widgets", async ({ page }) => {
    await expect(page.locator("#status-bar")).toHaveText(/Демон доступен/);
    await expect(page.locator("#listen-toggle")).toBeEnabled();
    await expect(page.locator("#analyze-btn")).toBeEnabled();
    await expect(page.locator("#recent-sessions-list")).toContainText("Сессия 101");
    await expect(page.locator("#upcoming-events-content")).toContainText("Sprint Review");
    await expect(page.locator("#last-analysis-content")).toContainText("Добавить visual regression");
    await expect(page.locator("#cost-widget-content")).toContainText("$1.2345");
    await expect(page.locator("#daemon-off-banner")).toBeHidden();
  });

  test("quick analyze completes and emits notification/reportable state", async ({ page }) => {
    await page.locator("#quick-analyze-60").click();

    await expect(page.locator("#analyze-status")).toHaveText(/Готово/);
    await expect(page.locator("#analyze-streaming-output")).toContainText("Шаг 1");
    await expect(page.locator("#sessions-list")).toContainText("103");

    const state = await page.evaluate(() => globalThis.__VOICEFORGE_TEST_STATE__);
    expect(state.notifications.some((entry) => entry.body.includes("Анализ завершён"))).toBeTruthy();
    expect(state.invokes.some((entry) => entry.cmd === "analyze" && entry.args.seconds === 60)).toBeTruthy();
  });

  test("listen flow renders streaming transcript and toggles compact controls", async ({ page }) => {
    await page.locator("#listen-toggle").click();
    await expect(page.locator("#listen-toggle")).toHaveText(/Стоп записи/);
    await expect(page.locator("#streaming-card")).toBeVisible();
    await expect(page.locator("#streaming-text")).toContainText("Слушаю встречу");

    await page.locator("#listen-toggle").click();
    await expect(page.locator("#listen-toggle")).toHaveText(/Старт записи/);
    await expect(page.locator("#streaming-card")).toBeHidden();
  });

  test("sessions detail, transcript search, rag search and calendar action work", async ({ page }) => {
    await page.getByRole("navigation").locator("[data-tab='sessions']").click();
    await expect(page.locator("#sessions-list")).toContainText("101");
    await dismissOnboarding(page);

    await page.locator("tr[data-id='101']").click();
    await expect(page.locator("#session-detail")).toBeVisible();
    await expect(page.locator("#session-detail-body")).toContainText("Обсудили релиз alpha.");
    await expect(page.locator("#session-detail-body")).toContainText("Добавить visual regression");

    await page.locator("#add-to-calendar").click();
    const stateAfterCalendar = await page.evaluate(() => globalThis.__VOICEFORGE_TEST_STATE__);
    expect(stateAfterCalendar.notifications.some((entry) => entry.body.includes("vf-event-101"))).toBeTruthy();

    await page.locator("#session-detail-close").click();
    await page.locator("#sessions-fts-search").fill("regression");
    await expect(page.locator("#sessions-fts-results")).toContainText("Нужно подготовить regression tests");

    await page.locator("#sessions-rag-search").fill("tauri");
    await expect(page.locator("#sessions-rag-results")).toContainText("desktop-build-deps");
  });

  test("settings panel mode, autostart and updater checks are exercised through mocks", async ({ page }) => {
    await page.getByRole("navigation").locator("[data-tab='settings']").click();
    await expect(page.locator("#settings-slide-panel")).toHaveClass(/open/);
    await expect(page.locator("#settings-content")).toContainText("anthropic/claude-haiku-4-5");

    await page.locator("#autostart-enabled").check();
    await page.locator("#updater-check-now").click();

    const state = await page.evaluate(() => globalThis.__VOICEFORGE_TEST_STATE__);
    expect(state.autostartEnabled).toBeTruthy();
    expect(state.updateChecks).toBeGreaterThan(0);
  });
});

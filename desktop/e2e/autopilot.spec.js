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

test.beforeEach(async ({ page }) => {
  await installDesktopMocks(page, { onboardingDismissed: false, compactMode: false });
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

  test("onboarding dismisses for current session and can persist with dont-show-again", async ({ page }) => {
    await installDesktopMocks(page, { onboardingDismissed: false, compactMode: false });
    await page.goto("/");

    const overlay = page.locator("#onboarding-overlay");
    await expect(overlay).toBeVisible();
    await page.waitForFunction(() => typeof document.getElementById("onboarding-ok")?.onclick === "function");
    await page.locator("#onboarding-ok").click();
    await expect(overlay).not.toBeVisible();

    await page.reload();
    await expect(overlay).toBeVisible();
    await page.waitForFunction(() => typeof document.getElementById("onboarding-ok")?.onclick === "function");
    await page.locator("#onboarding-never").check();
    await page.locator("#onboarding-ok").click();
    await expect(overlay).not.toBeVisible();

    await page.reload();
    await expect(overlay).not.toBeVisible();
    await expect.poll(async () => page.evaluate(() => localStorage.getItem("voiceforge_onboarding_dismissed"))).toBe("true");
  });

  test("compact mode can return to full mode from compact bar", async ({ page }) => {
    await page.getByRole("navigation").locator("[data-tab='settings']").click();
    await page.locator("#compact-mode-toggle").check();
    await expect(page.locator("#compact-bar")).toBeVisible();
    await expect(page.locator("#full-content")).not.toBeVisible();
    await page.locator("#compact-expand").click();

    await expect(page.locator("#compact-bar")).toBeHidden();
    await expect(page.locator("#full-content")).toBeVisible();
    await expect(page.locator("#tab-home")).toHaveClass(/active/);
    await expect.poll(async () => page.evaluate(() => localStorage.getItem("voiceforge_compact_mode"))).toBe("false");
  });

  test("quick analyze completes and emits notification/reportable state", async ({ page }) => {
    await page.locator("#quick-analyze-60").click();

    await expect(page.locator("#analyze-status")).toHaveText(/Готово/);
    await expect(page.locator("#analyze-streaming-output")).toContainText("Шаг 1");
    await expect(page.locator("#sessions-list")).toContainText("103");

    await page.getByRole("navigation").locator("[data-tab='home']").click();
    await expect(page.locator("#recent-sessions-list")).toContainText("Сессия 103");
    await expect(page.locator("#last-analysis-content")).toContainText("Review desktop QA report");
    await expect(page.locator("#cost-widget-content")).toContainText("$1.2345");

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

  // KC2: copilot overlay — hotkey pressed/released invokes set_copilot_overlay_state (recording → analyzing); latest replaces previous.
  test("copilot shortcut pressed and released invokes overlay state recording then analyzing", async ({ page }) => {
    await page.evaluate(() => {
      const s = globalThis.__VOICEFORGE_TEST_STATE__;
      const shortcut = s.shortcuts && s.shortcuts.length >= 3 ? s.shortcuts[2] : "CommandOrControl+Shift+Space";
      if (s.shortcutHandler) s.shortcutHandler({ shortcut, state: "Pressed" });
    });
    await page.evaluate(() => {
      const s = globalThis.__VOICEFORGE_TEST_STATE__;
      const shortcut = s.shortcuts && s.shortcuts.length >= 3 ? s.shortcuts[2] : "CommandOrControl+Shift+Space";
      if (s.shortcutHandler) s.shortcutHandler({ shortcut, state: "Released" });
    });
    const invokes = await page.evaluate(() => globalThis.__VOICEFORGE_TEST_STATE__.invokes);
    const copilotInvokes = invokes.filter((i) => i.cmd === "set_copilot_overlay_state");
    expect(copilotInvokes.length).toBeGreaterThanOrEqual(2);
    expect(copilotInvokes[copilotInvokes.length - 2].args).toMatchObject({ state: "recording", show: true });
    expect(copilotInvokes[copilotInvokes.length - 1].args).toMatchObject({ state: "analyzing", show: true });
  });

  // E19 #142: desktop-first meeting flow — Record -> Analyze -> View -> Export
  test("desktop-first meeting flow: Record -> Analyze -> View -> Export", async ({ page }) => {
    // Record: start then stop listen
    await page.locator("#listen-toggle").click();
    await expect(page.locator("#listen-toggle")).toHaveText(/Стоп записи/);
    await expect(page.locator("#streaming-card")).toBeVisible();
    await page.locator("#listen-toggle").click();
    await expect(page.locator("#listen-toggle")).toHaveText(/Старт записи/);

    // Analyze: quick 60s (app auto-opens session 103 detail via session-created)
    await page.locator("#quick-analyze-60").click();
    await expect(page.locator("#analyze-status")).toHaveText(/Готово/);
    await expect(page.locator("#session-detail")).toBeVisible({ timeout: 5000 });
    await expect(page.locator("#session-detail-body")).toContainText("Analysis done for 60s");

    // Export: MD
    await page.locator("#export-md").click();
    const state = await page.evaluate(() => globalThis.__VOICEFORGE_TEST_STATE__);
    const exportInvoke = state.invokes.find((i) => i.cmd === "export_session" && i.args.format === "md" && i.args.sessionId === 103);
    expect(exportInvoke).toBeDefined();
  });
});

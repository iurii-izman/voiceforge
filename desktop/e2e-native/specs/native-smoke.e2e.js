import assert from "node:assert/strict";

async function clickViaDom(selector) {
  await browser.execute((cssSelector) => {
    const element = document.querySelector(cssSelector);
    if (!element) throw new Error(`Element not found: ${cssSelector}`);
    element.click();
  }, selector);
}

async function setCheckbox(selector, checked) {
  await browser.execute(
    ({ cssSelector, nextChecked }) => {
      const element = document.querySelector(cssSelector);
      if (!element) throw new Error(`Element not found: ${cssSelector}`);
      element.checked = nextChecked;
      element.dispatchEvent(new Event("input", { bubbles: true }));
      element.dispatchEvent(new Event("change", { bubbles: true }));
    },
    { cssSelector: selector, nextChecked: checked },
  );
}

describe("VoiceForge desktop native smoke", () => {
  it("launches the real window and shows daemon-off status when backend is unavailable", async () => {
    const sidebar = await $("#main-sidebar");
    await sidebar.waitForDisplayed();

    const statusBar = await $("#status-bar");
    await statusBar.waitForDisplayed();

    const banner = await $("#daemon-off-banner");
    await browser.waitUntil(async () => banner.isDisplayed(), {
      timeout: 15000,
      timeoutMsg: "daemon-off banner did not appear in native window",
    });

    const text = await banner.getText();
    assert.match(text, /voiceforge daemon|Демон|daemon/i);
  });

  it("switches between main tabs in the real shell", async () => {
    await clickViaDom("[data-tab='sessions']");
    assert.match(await $("#tab-sessions").getAttribute("class"), /active/);

    await clickViaDom("[data-tab='costs']");
    assert.match(await $("#tab-costs").getAttribute("class"), /active/);

    await clickViaDom("[data-tab='home']");
    assert.match(await $("#tab-home").getAttribute("class"), /active/);
  });

  it("opens the settings slide panel and persists local desktop toggles", async () => {
    await browser.execute(() => {
      localStorage.setItem("voiceforge_close_to_tray", "false");
      localStorage.setItem("voiceforge_updater_check_on_launch", "false");
      localStorage.setItem("voiceforge_settings_as_panel", "true");
      window.location.reload();
    });

    const settingsNav = await $("[data-tab='settings']");
    await settingsNav.waitForDisplayed();
    await clickViaDom("[data-tab='settings']");

    const panel = await $("#settings-slide-panel");
    await browser.waitUntil(async () => /open/.test((await panel.getAttribute("class")) || ""), {
      timeout: 10000,
      timeoutMsg: "settings slide panel did not open in native shell",
    });

    const closeToTray = await $("#close-to-tray");
    await closeToTray.waitForDisplayed();
    await setCheckbox("#close-to-tray", true);

    const updaterToggle = await $("#updater-check-on-launch");
    await updaterToggle.waitForDisplayed();
    await setCheckbox("#updater-check-on-launch", true);

    const values = await browser.execute(() => ({
      closeToTray: localStorage.getItem("voiceforge_close_to_tray"),
      updater: localStorage.getItem("voiceforge_updater_check_on_launch"),
    }));

    assert.equal(values.closeToTray, "true");
    assert.equal(values.updater, "true");
  });

  it("keeps the retry path responsive in the real shell", async () => {
    const retryButton = await $("#daemon-retry-btn");
    await retryButton.waitForDisplayed();
    await clickViaDom("#daemon-retry-btn");

    const banner = await $("#daemon-off-banner");
    await banner.waitForDisplayed();
    assert.equal(await banner.isDisplayed(), true);
  });
});

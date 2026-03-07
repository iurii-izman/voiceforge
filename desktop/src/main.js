import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { getCurrentWindow, LogicalPosition, LogicalSize } from "@tauri-apps/api/window";
import { isPermissionGranted, requestPermission, sendNotification } from "@tauri-apps/plugin-notification";
import { register as registerShortcut, unregister as unregisterShortcut } from "@tauri-apps/plugin-global-shortcut";
import { getCurrent, onOpenUrl } from "@tauri-apps/plugin-deep-link";
import { enable as autostartEnable, disable as autostartDisable, isEnabled as autostartIsEnabled } from "@tauri-apps/plugin-autostart";
import { Store } from "@tauri-apps/plugin-store";
import { check as updaterCheck } from "@tauri-apps/plugin-updater";
import { relaunch } from "@tauri-apps/plugin-process";
import { Chart } from "chart.js/auto";

let appStore = null;

const UI_LANG_KEY = "voiceforge_ui_lang";

const STORE_KEYS = [
  "voiceforge_theme",
  "voiceforge_hotkeys_enabled",
  "voiceforge_close_to_tray",
  "voiceforge_compact_mode",
  "voiceforge_dashboard_order",
  "voiceforge_dashboard_collapsed",
  "voiceforge_favorites",
  "voiceforge_shortcut_record",
  "voiceforge_shortcut_analyze",
  "voiceforge_session_tags",
  "voiceforge_sound_on_record",
  "voiceforge_settings_as_panel",
  UI_LANG_KEY,
];

/** Block 97: minimal i18n for UI language (ru/en). */
const I18N = {
  ru: {
    nav: { home: "Главная", sessions: "Сессии", costs: "Затраты", settings: "Настройки" },
    tab_home_title: "Главная",
    tab_sessions_title: "Сессии",
    tab_costs_title: "Затраты",
    settings_title: "Настройки",
    settings_lang_label: "Язык интерфейса",
    settings_lang_hint: "Перезагрузка не требуется.",
    widget_record: "Запись",
    widget_analyze: "Анализ",
    widget_streaming: "Стриминг",
    widget_recent_sessions: "Недавние сессии",
    widget_upcoming_events: "Ближайшие встречи",
    widget_costs_7d: "Затраты за 7 дней",
    widget_last_analysis: "Последний анализ",
    last_analysis_empty: "Нет проанализированных сессий.",
    last_analysis_open_btn: "Открыть",
    quick_listen: "Запись",
    quick_analyze_60: "Анализ 60 сек",
    settings_theme_title: "Тема",
    settings_hotkeys_title: "Горячие клавиши",
    settings_updates_title: "Обновления",
    settings_autostart_title: "Автозапуск",
    settings_sound_title: "Звук",
    settings_window_title: "Окно",
    settings_compact_title: "Режим окна",
    sessions_search_placeholder: "Поиск по ID или дате…",
    sessions_fts_placeholder: "Поиск по тексту транскрипта…",
    listen_btn_start: "Старт записи",
    listen_btn_stop: "Стоп записи",
    listen_label_recording: "Запись идёт",
    analyze_btn_run: "Запустить анализ",
    loading: "Загрузка…",
    status_checking: "Проверка демона…",
    status_daemon_off: "Демон недоступен. Запустите: voiceforge daemon",
    status_daemon_ok: "Демон доступен",
    retry_btn: "Повторить",
    daemon_retry_btn: "Повторить подключение",
    compact_daemon_off: "Демон выкл",
    compact_daemon_ok: "Демон ок",
    costs_7d: "7 дней",
    costs_30d: "30 дней",
    costs_export_btn: "Экспорт отчёта",
    sessions_export_btn: "Экспорт списка",
    detail_title: "Детали сессии",
    ctx_open: "Открыть",
    ctx_copy_link: "Копировать ссылку",
    ctx_favorite: "В избранное",
    ctx_export_md: "Экспорт Markdown",
    ctx_export_pdf: "Экспорт PDF",
    detail_export_md: "Экспорт Markdown",
    detail_export_pdf: "Экспорт PDF",
    detail_copy_transcript: "Копировать транскрипт",
    detail_copy_actions: "Копировать action items",
    detail_print: "Печать",
    close_btn: "Закрыть",
    segment_copy: "Копировать",
    error_prefix: "Ошибка: ",
    error_generic: "Ошибка",
    error_status: "Ошибка.",
    export_error_prefix: "Ошибка экспорта: ",
    analyze_last_label: "Последние",
    analyze_sec_label: "сек",
    analyze_template_label: "Шаблон",
    sessions_period: "Период",
    sessions_sort: "Сортировка",
    sessions_show: "Показать",
    sessions_tag: "По тегу",
    theme_dark: "Тёмная",
    theme_light: "Светлая",
    theme_auto: "Как в системе",
    hotkey_record_label: "Запись:",
    hotkey_analyze_label: "Анализ:",
    hotkeys_enabled_label: "Включить глобальные горячие клавиши",
    updater_check_label: "Проверять обновления при запуске",
    updater_check_now_btn: "Проверить сейчас",
    autostart_label: "Запускать VoiceForge при входе в систему",
    sound_on_record_label: "Звук при старте/стопе записи",
    close_to_tray_label: "Свернуть в трей при закрытии (крестик)",
    compact_mode_label: "Компактный режим (только запись и анализ)",
    tags_label: "Теги:",
    tags_placeholder: "тег1, тег2",
    onboarding_title: "Добро пожаловать в VoiceForge",
    onboarding_step1: "Запустите демон:",
    onboarding_step2: "Нажмите «Старт записи» для захвата аудио",
    onboarding_step3: "Запустите анализ — результаты появятся в разделе «Сессии»",
    onboarding_ok: "Понятно",
    onboarding_never: "Не показывать снова",
    settings_readonly_hint: "Только чтение. Изменения — через конфиг или переменные окружения.",
    clipboard_history_btn: "История копирований",
    clipboard_history_empty: "Пока пусто",
    clipboard_history_title: "Последние скопированные фрагменты",
    settings_panel_mode_title: "Отображение настроек",
    settings_panel_mode_label: "Показывать настройки в выдвижной панели справа",
  },
  en: {
    nav: { home: "Home", sessions: "Sessions", costs: "Costs", settings: "Settings" },
    tab_home_title: "Home",
    tab_sessions_title: "Sessions",
    tab_costs_title: "Costs",
    settings_title: "Settings",
    settings_lang_label: "Interface language",
    settings_lang_hint: "No reload required.",
    widget_record: "Recording",
    widget_analyze: "Analysis",
    widget_streaming: "Streaming",
    widget_recent_sessions: "Recent sessions",
    widget_upcoming_events: "Upcoming events",
    widget_costs_7d: "Costs (7 days)",
    widget_last_analysis: "Last analysis",
    last_analysis_empty: "No analyzed sessions yet.",
    last_analysis_open_btn: "Open",
    quick_listen: "Record",
    quick_analyze_60: "Analyze 60 sec",
    settings_theme_title: "Theme",
    settings_hotkeys_title: "Hotkeys",
    settings_updates_title: "Updates",
    settings_autostart_title: "Autostart",
    settings_sound_title: "Sound",
    settings_window_title: "Window",
    settings_compact_title: "Window mode",
    sessions_search_placeholder: "Search by ID or date…",
    sessions_fts_placeholder: "Search transcript text…",
    listen_btn_start: "Start recording",
    listen_btn_stop: "Stop recording",
    listen_label_recording: "Recording…",
    analyze_btn_run: "Run analysis",
    loading: "Loading…",
    status_checking: "Checking daemon…",
    status_daemon_off: "Daemon unavailable. Run: voiceforge daemon",
    status_daemon_ok: "Daemon available",
    retry_btn: "Retry",
    daemon_retry_btn: "Retry connection",
    compact_daemon_off: "Daemon off",
    compact_daemon_ok: "Daemon ok",
    costs_7d: "7 days",
    costs_30d: "30 days",
    costs_export_btn: "Export report",
    sessions_export_btn: "Export list",
    detail_title: "Session details",
    ctx_open: "Open",
    ctx_copy_link: "Copy link",
    ctx_favorite: "Add to favorites",
    ctx_export_md: "Export Markdown",
    ctx_export_pdf: "Export PDF",
    detail_export_md: "Export Markdown",
    detail_export_pdf: "Export PDF",
    detail_copy_transcript: "Copy transcript",
    detail_copy_actions: "Copy action items",
    detail_print: "Print",
    close_btn: "Close",
    segment_copy: "Copy",
    error_prefix: "Error: ",
    error_generic: "Error",
    error_status: "Error.",
    export_error_prefix: "Export error: ",
    analyze_last_label: "Last",
    analyze_sec_label: "sec",
    analyze_template_label: "Template",
    sessions_period: "Period",
    sessions_sort: "Sort",
    sessions_show: "Show",
    sessions_tag: "By tag",
    theme_dark: "Dark",
    theme_light: "Light",
    theme_auto: "System",
    hotkey_record_label: "Record:",
    hotkey_analyze_label: "Analysis:",
    hotkeys_enabled_label: "Enable global hotkeys",
    updater_check_label: "Check for updates on launch",
    updater_check_now_btn: "Check now",
    autostart_label: "Launch VoiceForge on login",
    sound_on_record_label: "Sound on record start/stop",
    close_to_tray_label: "Minimize to tray on close",
    compact_mode_label: "Compact mode (record and analysis only)",
    tags_label: "Tags:",
    tags_placeholder: "tag1, tag2",
    onboarding_title: "Welcome to VoiceForge",
    onboarding_step1: "Start the daemon:",
    onboarding_step2: "Click «Start recording» to capture audio",
    onboarding_step3: "Run analysis — results will appear in Sessions",
    onboarding_ok: "Got it",
    onboarding_never: "Don't show again",
    clipboard_history_btn: "Clipboard history",
    clipboard_history_empty: "Empty",
    clipboard_history_title: "Recent copies",
    settings_panel_mode_title: "Settings display",
    settings_panel_mode_label: "Show settings in a slide-out panel on the right",
    settings_readonly_hint: "Read-only. Change via config or environment variables.",
  },
};

function t(key) {
  const lang = localStorage.getItem(UI_LANG_KEY) || "ru";
  const map = I18N[lang] || I18N.ru;
  const val = key.split(".").reduce((o, p) => o?.[p], map);
  return val != null && typeof val === "string" ? val : key;
}

function applyUiLangDataAttrs() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const k = el.dataset.i18n;
    if (k) el.textContent = t(k);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const k = el.dataset.i18nPlaceholder;
    if (k) el.placeholder = t(k);
  });
}

function applyListenAndStatusBar() {
  const listenBtn = document.getElementById("listen-toggle");
  const listenLabel = document.getElementById("listen-label");
  if (listenBtn) listenBtn.textContent = listenState ? t("listen_btn_stop") : t("listen_btn_start");
  if (listenLabel) listenLabel.textContent = listenState ? t("listen_label_recording") : "";
  const statusBar = document.getElementById("status-bar");
  if (statusBar) statusBar.textContent = daemonOk ? t("status_daemon_ok") : t("status_daemon_off");
}

function applyBannerAndCompactStatus() {
  const banner = document.getElementById("daemon-off-banner");
  const bannerText = document.getElementById("daemon-off-banner-text");
  if (bannerText && banner?.style.display !== "none") bannerText.textContent = t("status_daemon_off");
  const compactStatus = document.getElementById("compact-status");
  if (compactStatus) compactStatus.textContent = daemonOk ? t("compact_daemon_ok") : t("compact_daemon_off");
}

function applyUiLangStatusElements() {
  applyListenAndStatusBar();
  applyBannerAndCompactStatus();
  const closeBtn = document.getElementById("session-detail-close");
  if (closeBtn) closeBtn.setAttribute("aria-label", t("close_btn"));
  const lang = localStorage.getItem(UI_LANG_KEY) || "ru";
  document.documentElement.lang = lang === "en" ? "en" : "ru";
}

function applyUiLang() {
  applyUiLangDataAttrs();
  applyUiLangStatusElements();
}

function getValueToSetInStore(key, local) {
  const needsParse = key.endsWith("_order") || key.endsWith("_collapsed") || key.endsWith("_favorites");
  return needsParse ? JSON.parse(local) : local;
}

async function loadStoreAndMigrate() {
  try {
    appStore = await Store.load("voiceforge-settings.json");
    for (const key of STORE_KEYS) {
      const stored = await appStore.get(key);
      if (stored !== null && stored !== undefined) {
        const str = typeof stored === "string" ? stored : JSON.stringify(stored);
        localStorage.setItem(key, str);
      } else {
        const local = localStorage.getItem(key);
        if (local !== null) {
          const toSet = getValueToSetInStore(key, local);
          await appStore.set(key, toSet);
        }
      }
    }
  } catch (e) {
    if (e != null) console.debug("loadStoreAndMigrate", e);
  }
}

function setStored(key, value) {
  const str = typeof value === "string" ? value : JSON.stringify(value);
  localStorage.setItem(key, str);
  if (appStore) {
    const needsParse = key.endsWith("_order") || key.endsWith("_collapsed") || key.endsWith("_favorites");
    const parsed = typeof value === "string" ? JSON.parse(value) : value;
    const toSet = needsParse ? parsed : value;
    appStore.set(key, toSet).catch((e) => { if (e != null) console.debug("store.set", e); });
  }
}

let daemonOk = false;
let listenState = false;
let streamingInterval = null;
/** Reactive buffer from D-Bus TranscriptChunk signals (finals + partial). */
let streamingFinals = [];
let streamingPartial = "";

function setDaemonOff(msg) {
  if (daemonOk) notify("VoiceForge", t("status_daemon_off"));
  daemonOk = false;
  const statusBar = document.getElementById("status-bar");
  const retryBtn = document.getElementById("retry");
  statusBar.textContent = msg || t("status_daemon_off");
  statusBar.className = "status daemon-off";
  retryBtn.style.display = "block";
  document.querySelectorAll(".content button").forEach((b) => (b.disabled = true));
  const compactStatus = document.getElementById("compact-status");
  if (compactStatus) { compactStatus.textContent = t("compact_daemon_off"); compactStatus.className = "status daemon-off"; }
  const banner = document.getElementById("daemon-off-banner");
  const bannerText = document.getElementById("daemon-off-banner-text");
  if (banner) banner.style.display = "block";
  if (bannerText) bannerText.textContent = msg || t("status_daemon_off");
}

function setDaemonOk() {
  daemonOk = true;
  const statusBar = document.getElementById("status-bar");
  const retryBtn = document.getElementById("retry");
  statusBar.textContent = t("status_daemon_ok");
  statusBar.className = "status daemon-ok";
  retryBtn.style.display = "none";
  const banner = document.getElementById("daemon-off-banner");
  if (banner) banner.style.display = "none";
  document.querySelectorAll("#listen-toggle, #analyze-btn").forEach((b) => (b.disabled = false));
  const compactStatus = document.getElementById("compact-status");
  if (compactStatus) { compactStatus.textContent = t("compact_daemon_ok"); compactStatus.className = "status daemon-ok"; }
}

function parseEnvelope(raw) {
  if (typeof raw !== "string") return { ok: false, error: { message: "Invalid response" } };
  try {
    return JSON.parse(raw);
  } catch {
    return { ok: false, error: { message: raw } };
  }
}

function errorMessage(envelope) {
  if (envelope?.error?.message) return envelope.error.message;
  if (envelope?.ok || !envelope?.error) return t("error_generic");
  return JSON.stringify(envelope.error);
}

const INVOKE_DEFAULT_TIMEOUT_MS = 10000;
const INVOKE_DEFAULT_RETRIES = 1;

async function invokeWithRetry(cmd, args, opts) {
  const timeoutMs = opts?.timeoutMs ?? INVOKE_DEFAULT_TIMEOUT_MS;
  const retries = opts?.retries ?? INVOKE_DEFAULT_RETRIES;
  let lastErr;
  for (let i = 0; i <= retries; i++) {
    try {
      const p = invoke(cmd, args ?? {});
      const t = new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), timeoutMs));
      return await Promise.race([p, t]);
    } catch (e) {
      lastErr = e;
      if (i < retries) await new Promise((r) => setTimeout(r, 300));
    }
  }
  throw lastErr;
}

async function checkDaemon() {
  try {
    const pong = await invokeWithRetry("ping", {}, { timeoutMs: 5000, retries: 1 });
    if (pong !== "pong") {
      setDaemonOff("Неожиданный ответ: " + pong);
      return false;
    }
    setDaemonOk();
    return true;
  } catch (e) {
    setDaemonOff("Запустите демон: voiceforge daemon. " + (e?.message || ""));
    return false;
  }
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach((n) => {
    n.classList.remove("active");
    n.setAttribute("aria-current", "false");
  });
  const panel = document.getElementById("tab-" + tabId);
  const nav = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
  if (panel) {
    panel.classList.add("active");
    panel.setAttribute("tabindex", "-1");
    panel.focus({ preventScroll: true });
  }
  if (nav) {
    nav.classList.add("active");
    nav.setAttribute("aria-current", "true");
  }
  if (tabId === "sessions") loadSessions();
  if (tabId === "costs") loadAnalytics("7d");
  if (tabId === "settings") loadSettings();
  if (tabId === "home") {
    loadRecentSessions();
    loadUpcomingEvents();
    loadCostWidget();
    loadLastAnalysisWidget();
  }
}

const SETTINGS_AS_PANEL_KEY = "voiceforge_settings_as_panel";

function openSettingsPanel() {
  const panel = document.getElementById("settings-slide-panel");
  const slot = document.getElementById("settings-panel-slot");
  const tabContent = document.getElementById("settings-tab-content");
  if (!panel || !slot || !tabContent) return;
  slot.appendChild(tabContent);
  panel.classList.add("open");
  panel.setAttribute("aria-hidden", "false");
  loadSettings();
  document.getElementById("settings-panel-close")?.focus({ preventScroll: true });
}

function closeSettingsPanel() {
  const panel = document.getElementById("settings-slide-panel");
  const slot = document.getElementById("settings-panel-slot");
  const tabContent = document.getElementById("settings-tab-content");
  const tabSettings = document.getElementById("tab-settings");
  if (!panel || !slot || !tabContent || !tabSettings) return;
  if (tabContent.parentElement === slot) {
    tabSettings.appendChild(tabContent);
  }
  panel.classList.remove("open");
  panel.setAttribute("aria-hidden", "true");
}

function initSettingsPanelMode() {
  const closeBtn = document.getElementById("settings-panel-close");
  if (closeBtn) closeBtn.addEventListener("click", closeSettingsPanel);
  const panel = document.getElementById("settings-slide-panel");
  if (panel) {
    panel.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && panel.classList.contains("open")) closeSettingsPanel();
    });
  }
  const cb = document.getElementById("settings-as-panel");
  if (cb) {
    cb.checked = localStorage.getItem(SETTINGS_AS_PANEL_KEY) === "true";
    cb.addEventListener("change", () => {
      const val = cb.checked ? "true" : "false";
      localStorage.setItem(SETTINGS_AS_PANEL_KEY, val);
      setStored(SETTINGS_AS_PANEL_KEY, val);
    });
  }
}

function playBeep() {
  try {
    if (localStorage.getItem("voiceforge_sound_on_record") !== "true") return;
    const ctx = new (globalThis.AudioContext || globalThis.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.value = 440;
    osc.type = "sine";
    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.1);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 0.1);
  } catch (e) {
    console.debug("playBeep", e);
  }
}

function applyListenState(isListening) {
  listenState = isListening;
  const btn = document.getElementById("listen-toggle");
  const label = document.getElementById("listen-label");
  btn.textContent = listenState ? t("listen_btn_stop") : t("listen_btn_start");
  label.textContent = listenState ? t("listen_label_recording") : "";
  const streamingCard = document.getElementById("streaming-card");
  if (listenState) {
    streamingCard.style.display = "block";
    streamingFinals = [];
    streamingPartial = "";
    updateStreamingDisplay();
    if (!streamingInterval) streamingInterval = setInterval(pollStreaming, 1500);
  } else {
    streamingCard.style.display = "none";
    if (streamingInterval) {
      clearInterval(streamingInterval);
      streamingInterval = null;
    }
  }
  playBeep();
}

function updateStreamingDisplay() {
  const full =
    streamingFinals.join(" ") + (streamingPartial ? " " + streamingPartial : "");
  const el = document.getElementById("streaming-text");
  if (el) el.textContent = full || "—";
}

async function updateListenState() {
  if (!daemonOk) return;
  try {
    const isListening = await invoke("is_listening");
    applyListenState(isListening);
  } catch (e) {
    if (e != null) console.debug("updateListenState", e);
  }
}

async function pollStreaming() {
  if (!daemonOk) return;
  try {
    const raw = await invoke("get_streaming_transcript");
    const env = parseEnvelope(raw);
    const hasStreaming = env?.streaming_transcript != null;
    const data = env?.data?.streaming_transcript ?? (hasStreaming ? env : null);
    const text = data?.partial || "";
    const finals = data?.finals || [];
    streamingPartial = text;
    streamingFinals = finals.map((f) => (typeof f === "string" ? f : f?.text || ""));
    updateStreamingDisplay();
  } catch (e) {
    if (e != null) console.debug("pollStreaming", e);
  }
}

document.getElementById("retry").addEventListener("click", async () => {
  document.getElementById("retry").disabled = true;
  await checkDaemon();
  if (daemonOk) {
    await updateListenState();
    loadSettings();
    loadSessions();
  }
  document.getElementById("retry").disabled = false;
});
document.getElementById("daemon-retry-btn")?.addEventListener("click", async () => {
  const btn = document.getElementById("daemon-retry-btn");
  if (btn) btn.disabled = true;
  await checkDaemon();
  if (daemonOk) {
    await updateListenState();
    loadSettings();
    loadSessions();
  }
  if (btn) btn.disabled = false;
});

document.querySelectorAll(".nav-item").forEach((n) => {
  n.addEventListener("click", () => {
    const tabId = n.dataset.tab;
    if (tabId === "settings" && localStorage.getItem(SETTINGS_AS_PANEL_KEY) === "true") {
      openSettingsPanel();
      return;
    }
    switchTab(tabId);
  });
  n.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      const tabId = n.dataset.tab;
      if (tabId === "settings" && localStorage.getItem(SETTINGS_AS_PANEL_KEY) === "true") {
        openSettingsPanel();
        return;
      }
      switchTab(tabId);
    }
  });
});

function openSessionFromWidget(sessionId) {
  switchTab("sessions");
  setTimeout(() => showSessionDetail(Number.parseInt(sessionId, 10)), 100);
}

function renderRecentSessionsList(sessions) {
  if (!Array.isArray(sessions) || sessions.length === 0) return null;
  let html = "<ul class=\"recent-sessions-ul\">";
  sessions.forEach((s) => {
    const id = s.id ?? s.session_id ?? "—";
    const start = s.started_at ?? s.created_at ?? "";
    const dur = s.duration_sec != null ? s.duration_sec + " с" : "";
    html += `<li><button type="button" class="btn-link" data-session-id="${id}">Сессия ${id}</button> ${start} ${dur}</li>`;
  });
  html += "</ul>";
  return html;
}

function loadRecentSessions() {
  const el = document.getElementById("recent-sessions-list");
  if (!el) return;
  if (!daemonOk) {
    el.textContent = "Запустите демон.";
    return;
  }
  invoke("get_sessions", { limit: 5 })
    .then((raw) => {
      const env = parseEnvelope(raw);
      const sessions = env?.data?.sessions ?? env?.sessions ?? [];
      const html = renderRecentSessionsList(sessions);
      if (html === null) {
        el.innerHTML = "<p>Нет сессий. Запустите анализ с блока выше.</p>";
        return;
      }
      el.innerHTML = html;
      el.querySelectorAll(".btn-link[data-session-id]").forEach((btn) => {
        btn.addEventListener("click", () => openSessionFromWidget(btn.dataset.sessionId));
      });
    })
    .catch((e) => {
      el.textContent = t("error_prefix") + (e?.message || e);
    });
}

const DOCS_CALENDAR = "https://github.com/iurii-izman/voiceforge/blob/main/docs/runbooks/calendar-integration.md";

function loadUpcomingEvents() {
  const el = document.getElementById("upcoming-events-content");
  if (!el) return;
  el.textContent = t("loading");
  invoke("get_upcoming_calendar_events")
    .then((raw) => {
      const env = parseEnvelope(raw);
      const events = env?.data?.events ?? env?.events ?? [];
      if (!Array.isArray(events) || events.length === 0) {
        el.innerHTML = "<p class=\"muted\">Нет событий на ближайшие 48 ч.</p><p><a href=\"" + DOCS_CALENDAR + "\" target=\"_blank\" rel=\"noopener\">Настройка CalDAV</a></p>";
        return;
      }
      let html = "<ul class=\"upcoming-events-list\">";
      events.slice(0, 10).forEach((ev) => {
        const summary = escapeHtml(ev.summary ?? "(без названия)");
        const start = ev.start_iso ?? "";
        const startShort = start.replace(/T.*/, "").replaceAll("-", ".") + (start.includes("T") ? " " + start.split("T")[1].slice(0, 5) : "");
        html += "<li><strong>" + summary + "</strong> <span class=\"muted\">" + startShort + "</span></li>";
      });
      html += "</ul>";
      if (events.length > 10) html += "<p class=\"muted\">и ещё " + (events.length - 10) + "…</p>";
      el.innerHTML = html;
    })
    .catch((e) => {
      el.innerHTML = "<p class=\"muted\">Не удалось загрузить календарь: " + escapeHtml(e?.message || e) + "</p><p><a href=\"" + DOCS_CALENDAR + "\" target=\"_blank\" rel=\"noopener\">Настройка CalDAV</a></p>";
    });
}

function formatStartedShort(started) {
  if (!started) return "";
  const s = String(started);
  const datePart = s.replace(/T.*/, "").replaceAll("-", ".");
  const timePart = s.includes("T") ? " " + s.split("T")[1].slice(0, 5) : "";
  return datePart + timePart;
}

function buildLastAnalysisActionsList(ana) {
  const actions = Array.isArray(ana?.action_items) ? ana.action_items : [];
  const n = actions.length;
  if (n === 0) return "";
  let html = "<ul class=\"last-analysis-list\">";
  actions.slice(0, 3).forEach((ai) => {
    const d = typeof ai === "object" ? (ai.description || "") : String(ai);
    html += "<li>" + escapeHtml(d) + "</li>";
  });
  if (n > 3) html += "<li class=\"muted\">… ещё " + (n - 3) + "</li>";
  return html + "</ul>";
}

function buildLastAnalysisQrLine(ana) {
  if (!ana) return "";
  const q = Array.isArray(ana.questions) ? ana.questions.length : 0;
  const r = Array.isArray(ana.recommendations) ? ana.recommendations.length : 0;
  return (q || r) ? "<p class=\"muted\">Вопросов: " + q + ", рекомендаций: " + r + "</p>" : "";
}

function buildLastAnalysisSummaryHtml(sessionId, session, detail) {
  const ana = detail?.analysis || null;
  const started = session?.started_at ?? session?.created_at ?? "";
  const startShort = formatStartedShort(started);
  let html = "<p class=\"muted\">Сессия " + escapeHtml(String(sessionId)) + (startShort ? " · " + escapeHtml(startShort) : "") + "</p>";
  if (ana) {
    html += buildLastAnalysisActionsList(ana);
    const hasActions = Array.isArray(ana.action_items) && ana.action_items.length > 0;
    if (!hasActions) html += buildLastAnalysisQrLine(ana);
  }
  return html;
}

function fillLastAnalysisWithDetail(el, sessionId, session, detailRaw) {
  const denv = parseEnvelope(detailRaw);
  const detail = denv?.data?.session_detail ?? denv?.session_detail ?? denv ?? {};
  const summaryHtml = buildLastAnalysisSummaryHtml(sessionId, session, detail);
  const btnHtml = "<button type=\"button\" class=\"btn small\" id=\"last-analysis-open-btn\">" + escapeHtml(t("last_analysis_open_btn")) + "</button>";
  el.innerHTML = summaryHtml + btnHtml;
  document.getElementById("last-analysis-open-btn")?.addEventListener("click", () => {
    switchTab("sessions");
    setTimeout(() => showSessionDetail(Number(sessionId), {}), 100);
  });
}

function loadLastAnalysisWidget() {
  const el = document.getElementById("last-analysis-content");
  if (!el) return;
  if (!daemonOk) {
    el.textContent = t("last_analysis_empty");
    return;
  }
  el.textContent = t("loading");
  invoke("get_sessions", { limit: 1 })
    .then((raw) => {
      const env = parseEnvelope(raw);
      const sessions = env?.data?.sessions ?? env?.sessions ?? [];
      const session = Array.isArray(sessions) && sessions.length > 0 ? sessions[0] : null;
      const sessionId = session?.id ?? session?.session_id;
      if (sessionId == null) {
        el.innerHTML = "<p class=\"muted\">" + escapeHtml(t("last_analysis_empty")) + "</p>";
        return null;
      }
      return invoke("get_session_detail", { sessionId: Number(sessionId) }).then((detailRaw) => {
        fillLastAnalysisWithDetail(el, sessionId, session, detailRaw);
        return sessionId;
      });
    })
    .catch(() => {
      el.innerHTML = "<p class=\"muted\">" + escapeHtml(t("last_analysis_empty")) + "</p>";
    });
}

function applyCostWidgetContent(el, raw) {
  const env = parseEnvelope(raw);
  let data = env?.data?.analytics ?? env?.analytics ?? env ?? {};
  if (typeof data === "string") {
    try {
      data = JSON.parse(data);
    } catch {
      el.textContent = "—";
      return;
    }
  }
  const total = data.total_cost_usd ?? 0;
  const calls = data.total_calls ?? 0;
  el.textContent = "$" + Number(total).toFixed(4) + " (" + calls + " вызовов)";
}

function loadCostWidget() {
  const el = document.getElementById("cost-widget-content");
  if (!el) return;
  if (!daemonOk) {
    el.textContent = "—";
    return;
  }
  invoke("get_analytics", { period: "7d" })
    .then((raw) => applyCostWidgetContent(el, raw))
    .catch(() => { el.textContent = "—"; });
}

async function toggleListen() {
  const btn = document.getElementById("listen-toggle");
  if (btn) btn.disabled = true;
  try {
    if (listenState) await invoke("listen_stop");
    else await invoke("listen_start");
    await updateListenState();
  } catch (e) {
    const label = document.getElementById("listen-label");
    if (label) label.textContent = t("error_prefix") + (e?.message || e);
  }
  if (btn) btn.disabled = false;
}

document.getElementById("listen-toggle").addEventListener("click", toggleListen);

async function runQuickAnalyze60() {
  if (!daemonOk) return;
  const secInput = document.getElementById("analyze-seconds");
  const templateInput = document.getElementById("analyze-template");
  if (secInput) secInput.value = "60";
  const template = templateInput?.value || null;
  const statusEl = document.getElementById("analyze-status");
  const btn = document.getElementById("analyze-btn");
  if (btn) btn.disabled = true;
  if (statusEl) statusEl.textContent = "Анализ 60 сек…";
  try {
    const raw = await invoke("analyze", { seconds: 60, template });
    const env = parseEnvelope(raw);
    if (env?.ok && env?.data?.text) {
      if (statusEl) statusEl.textContent = "Готово.";
      loadSessions();
      notify("VoiceForge", "Анализ завершён.");
    } else if (statusEl) {
      statusEl.textContent = errorMessage(env);
    }
  } catch (e) {
    if (statusEl) statusEl.textContent = t("error_prefix") + (e?.message ?? String(e ?? ""));
  }
  if (btn) btn.disabled = false;
}

function initQuickActions() {
  document.getElementById("quick-listen")?.addEventListener("click", () => { if (daemonOk) toggleListen(); });
  document.getElementById("quick-analyze-60")?.addEventListener("click", () => runQuickAnalyze60());
}

async function runDefaultAnalyze() {
  if (!daemonOk) return;
  const btn = document.getElementById("analyze-btn");
  const statusEl = document.getElementById("analyze-status");
  if (btn) btn.disabled = true;
  if (statusEl) statusEl.textContent = "Анализ…";
  try {
    const raw = await invoke("analyze", { seconds: 30, template: null });
    const env = parseEnvelope(raw);
    if (env?.ok && env?.data?.text) {
      if (statusEl) statusEl.textContent = "Готово.";
      loadSessions();
      notify("VoiceForge", "Анализ завершён.");
    } else if (statusEl) {
      statusEl.textContent = errorMessage(env);
    }
  } catch (e) {
    if (statusEl) statusEl.textContent = t("error_prefix") + (e?.message ?? String(e ?? ""));
  }
  if (btn) btn.disabled = false;
}

async function setupGlobalShortcuts() {
  const enabled = localStorage.getItem(HOTKEYS_ENABLED_KEY) !== "false";
  if (!enabled) return;
  const [shortcutRecord, shortcutAnalyze] = getShortcuts();
  currentShortcuts = [shortcutRecord, shortcutAnalyze].filter(Boolean);
  if (currentShortcuts.length === 0) return;
  try {
    await registerShortcut(currentShortcuts, (event) => {
      if (event.state !== "Pressed") return;
      if (event.shortcut === shortcutRecord && daemonOk) toggleListen();
      else if (event.shortcut === shortcutAnalyze) runDefaultAnalyze();
    });
  } catch (e) {
    if (e != null) console.debug("setupGlobalShortcuts", e);
  }
}

async function teardownGlobalShortcuts() {
  if (currentShortcuts.length === 0) return;
  try {
    await unregisterShortcut(currentShortcuts);
    currentShortcuts = [];
  } catch (e) {
    if (e != null) console.debug("teardownGlobalShortcuts", e);
  }
}

listen("tray-toggle-listen", () => {
  if (daemonOk) toggleListen();
});

listen("listen-state-changed", (e) => {
  if (e.payload?.is_listening !== undefined) applyListenState(!!e.payload.is_listening);
});
async function notify(title, body) {
  try {
    let granted = await isPermissionGranted();
    if (!granted) granted = (await requestPermission()) === "granted";
    if (granted) sendNotification({ title, body });
  } catch (err) {
    if (err != null) console.debug("notify", err);
  }
}

listen("streaming-analysis-chunk", (e) => {
  const delta = e.payload?.delta ?? "";
  const outEl = document.getElementById("analyze-streaming-output");
  if (!outEl) return;
  if (delta === "") {
    outEl.dataset.streamEnd = "1";
    return;
  }
  outEl.style.display = "block";
  outEl.textContent += delta;
  outEl.scrollTop = outEl.scrollHeight;
});
listen("analysis-done", (e) => {
  const status = e.payload?.status;
  const statusEl = document.getElementById("analyze-status");
  if (statusEl) {
    let msg;
    if (status === "ok") msg = "Готово.";
    else if (status === "error") msg = t("error_status");
    else msg = String(status ?? "");
    statusEl.textContent = msg;
  }
  document.getElementById("analyze-btn").disabled = false;
  const outEl = document.getElementById("analyze-streaming-output");
  if (outEl && outEl.dataset.streamEnd === "1") outEl.dataset.streamEnd = "";
  if (daemonOk) loadSessions();
  if (status === "ok") notify("VoiceForge", "Анализ завершён.");
  else if (status === "error") notify("VoiceForge", "Анализ: ошибка.");
});
listen("transcript-chunk", (e) => {
  const text = e.payload?.text ?? "";
  const isFinal = !!e.payload?.is_final;
  if (isFinal) {
    if (text) streamingFinals.push(text);
    streamingPartial = "";
  } else {
    streamingPartial = text;
  }
  updateStreamingDisplay();
});
listen("transcript-updated", () => {
  if (daemonOk) loadSessions();
});
listen("session-created", (e) => {
  if (daemonOk) {
    loadSessions();
    loadLastAnalysisWidget();
  }
  const id = e.payload?.session_id;
  if (id != null) {
    switchTab("sessions");
    setTimeout(() => showSessionDetail(id), 150);
  }
});

listen("second-instance", async (e) => {
  const win = getCurrentWindow();
  await win.show();
  await win.setFocus();
  const args = e.payload?.args ?? [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--session" && args[i + 1]) {
      const sessionId = Number.parseInt(args[i + 1], 10);
      if (!Number.isNaN(sessionId)) {
        switchTab("sessions");
        setTimeout(() => showSessionDetail(sessionId), 150);
      }
      break;
    }
  }
});

const TAB_IDS = ["home", "sessions", "costs", "settings"];
document.addEventListener("keydown", (e) => {
  if (e.altKey && e.key >= "1" && e.key <= "4") {
    e.preventDefault();
    const idx = Number.parseInt(e.key, 10) - 1;
    switchTab(TAB_IDS[idx]);
  }
  if (e.key === "Escape") {
    const detailBlock = document.getElementById("session-detail");
    if (detailBlock?.open) {
      e.preventDefault();
      hideSessionDetail();
    }
  }
});

document.getElementById("analyze-btn").addEventListener("click", async () => {
  const seconds = Number.parseInt(document.getElementById("analyze-seconds").value, 10) || 30;
  const template = document.getElementById("analyze-template").value || null;
  const statusEl = document.getElementById("analyze-status");
  const btn = document.getElementById("analyze-btn");
  const outEl = document.getElementById("analyze-streaming-output");
  if (outEl) {
    outEl.style.display = "none";
    outEl.textContent = "";
    delete outEl.dataset.streamEnd;
  }
  btn.disabled = true;
  statusEl.textContent = "Анализ…";
  try {
    const raw = await invoke("analyze", { seconds, template });
    const env = parseEnvelope(raw);
    if (env?.ok && env?.data?.text) {
      statusEl.textContent = "Готово.";
      loadSessions();
    } else {
      statusEl.textContent = errorMessage(env);
    }
  } catch (e) {
    statusEl.textContent = t("error_prefix") + (e?.message ?? String(e ?? ""));
  }
  btn.disabled = false;
});

let sessionsCache = [];
let lastFilteredSessions = [];
let sessionIdsWithActionItemsCache = null;
let lastAnalyticsData = null;

function parseSessionDate(startedAt) {
  if (!startedAt || typeof startedAt !== "string") return null;
  const d = new Date(startedAt);
  return Number.isNaN(d.getTime()) ? null : d;
}

function filterAndSortSessions(sessions, search, period, sortKey) {
  let out = sessions.slice();
  const q = (search || "").trim().toLowerCase();
  if (q) {
    out = out.filter((s) => {
      const id = String(s.id ?? s.session_id ?? "").toLowerCase();
      const start = String(s.started_at ?? s.created_at ?? "").toLowerCase();
      return id.includes(q) || start.includes(q);
    });
  }
  if (period && period !== "all") {
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    out = out.filter((s) => {
      const d = parseSessionDate(s.started_at ?? s.created_at);
      if (!d) return false;
      if (period === "today") return d >= todayStart;
      if (period === "week") return d >= new Date(todayStart.getTime() - 7 * 24 * 60 * 60 * 1000);
      if (period === "month") return d >= new Date(todayStart.getTime() - 30 * 24 * 60 * 60 * 1000);
      return true;
    });
  }
  if (sortKey === "date-desc") out.sort((a, b) => (parseSessionDate(b.started_at ?? b.created_at)?.getTime() ?? 0) - (parseSessionDate(a.started_at ?? a.created_at)?.getTime() ?? 0));
  else if (sortKey === "date-asc") out.sort((a, b) => (parseSessionDate(a.started_at ?? a.created_at)?.getTime() ?? 0) - (parseSessionDate(b.started_at ?? b.created_at)?.getTime() ?? 0));
  else if (sortKey === "duration-desc") out.sort((a, b) => (b.duration_sec ?? 0) - (a.duration_sec ?? 0));
  else if (sortKey === "duration-asc") out.sort((a, b) => (a.duration_sec ?? 0) - (b.duration_sec ?? 0));
  return out;
}

function getDateGroupKey(d) {
  if (!d || !(d instanceof Date)) return "older";
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
  const weekStart = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
  const t = d.getTime();
  if (t >= today.getTime()) return "today";
  if (t >= yesterday.getTime()) return "yesterday";
  if (t >= weekStart.getTime()) return "this_week";
  return "older";
}

const DATE_GROUP_LABELS = { today: "Сегодня", yesterday: "Вчера", this_week: "На этой неделе", older: "Ранее" };
const DATE_GROUP_ORDER = ["today", "yesterday", "this_week", "older"];

function renderSessionsTable(sessions) {
  const container = document.getElementById("sessions-list");
  if (!container) return;
  if (!sessions.length) {
    container.innerHTML = "<div class=\"empty-state\"><p class=\"muted\">Нет сессий по заданным фильтрам.</p></div>";
    return;
  }
  const fav = getFavorites();
  const groups = {};
  DATE_GROUP_ORDER.forEach((k) => { groups[k] = []; });
  sessions.forEach((s) => {
    const key = getDateGroupKey(parseSessionDate(s.started_at ?? s.created_at));
    if (groups[key]) groups[key].push(s);
  });
  let html = "<table><thead><tr><th aria-label=\"Избранное\"></th><th>ID</th><th>Начало</th><th>Длительность</th></tr></thead><tbody>";
  DATE_GROUP_ORDER.forEach((key) => {
    const list = groups[key] || [];
    if (list.length === 0) return;
    html += "<tr class=\"session-group-header\"><td colspan=\"4\">" + escapeHtml(DATE_GROUP_LABELS[key]) + "</td></tr>";
    list.forEach((s) => {
      const id = s.id ?? s.session_id ?? "—";
      const start = s.started_at ?? s.created_at ?? "—";
      const dur = s.duration_sec == null ? "—" : s.duration_sec + " с";
      const isFav = fav.has(Number(id));
      const star = `<button type="button" class="favorite-star" data-id="${id}" aria-label="${isFav ? "Убрать из избранного" : "В избранное"}">${isFav ? "★" : "☆"}</button>`;
      html += `<tr data-id="${id}" tabindex="0" role="button"><td>${star}</td><td>${id}</td><td>${start}</td><td>${dur}</td></tr>`;
    });
  });
  html += "</tbody></table>";
  container.innerHTML = html;
  container.querySelectorAll(".favorite-star").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleFavorite(Number(btn.dataset.id));
    });
  });
  container.querySelectorAll("tr[data-id]").forEach((row) => {
    const openDetail = () => showSessionDetail(Number.parseInt(row.dataset.id, 10));
    row.addEventListener("click", (e) => {
      if (e.target.closest(".favorite-star")) return;
      openDetail();
    });
    row.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openDetail();
      }
    });
    row.addEventListener("contextmenu", (e) => {
      if (e.target.closest(".favorite-star")) return;
      e.preventDefault();
      showSessionContextMenu(e.clientX, e.clientY, Number(row.dataset.id));
    });
  });
}

let sessionContextMenuSessionId = null;

function showSessionContextMenu(x, y, sessionId) {
  const menu = document.getElementById("session-context-menu");
  if (!menu) return;
  sessionContextMenuSessionId = sessionId;
  const favBtn = menu.querySelector('[data-action="favorite"]');
  if (favBtn) favBtn.textContent = getFavorites().has(sessionId) ? "Убрать из избранного" : "В избранное";
  menu.style.left = x + "px";
  menu.style.top = y + "px";
  menu.style.display = "block";
  menu.setAttribute("aria-hidden", "false");
}

function hideSessionContextMenu() {
  const menu = document.getElementById("session-context-menu");
  if (menu) {
    menu.style.display = "none";
    menu.setAttribute("aria-hidden", "true");
  }
  sessionContextMenuSessionId = null;
}

function initSessionContextMenu() {
  const menu = document.getElementById("session-context-menu");
  if (!menu) return;
  menu.addEventListener("click", (e) => {
    const action = e.target.closest(".context-menu-item")?.dataset?.action;
    const id = sessionContextMenuSessionId;
    hideSessionContextMenu();
    if (id == null) return;
    if (action === "open") showSessionDetail(id);
    else if (action === "copy-link") {
      const url = "voiceforge://session/" + id;
      navigator.clipboard.writeText(url).then(() => notify("VoiceForge", "Ссылка скопирована.")).catch(() => {});
    } else if (action === "favorite") toggleFavorite(id);
    else if (action === "export-md") exportSession(id, "md");
    else if (action === "export-pdf") exportSession(id, "pdf");
  });
  document.addEventListener("click", (e) => {
    if (!e.target.closest("#session-context-menu")) hideSessionContextMenu();
  });
  document.addEventListener("contextmenu", () => hideSessionContextMenu());
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") hideSessionContextMenu(); });
}

function applySessionsFilter() {
  const search = document.getElementById("sessions-search")?.value ?? "";
  const period = document.getElementById("sessions-period")?.value ?? "all";
  const sortKey = document.getElementById("sessions-sort")?.value ?? "date-desc";
  const favoritesOnly = document.getElementById("sessions-favorites-filter")?.value === "favorites";
  const actionItemsOnly = document.getElementById("sessions-action-items-filter")?.value === "with-actions";
  const tagFilter = document.getElementById("sessions-tag-filter")?.value;
  lastFilteredSessions = filterAndSortSessions(sessionsCache, search, period, sortKey);
  if (favoritesOnly) {
    const fav = getFavorites();
    lastFilteredSessions = lastFilteredSessions.filter((s) => fav.has(Number(s.id ?? s.session_id)));
  }
  if (tagFilter && tagFilter !== "all") {
    const tagsMap = getSessionTags();
    lastFilteredSessions = lastFilteredSessions.filter((s) => {
      const id = Number(s.id ?? s.session_id);
      const tags = tagsMap[id];
      return Array.isArray(tags) && tags.includes(tagFilter);
    });
  }
  if (actionItemsOnly) {
    if (sessionIdsWithActionItemsCache === null) {
      invoke("get_session_ids_with_action_items")
        .then((raw) => {
          const env = parseEnvelope(raw);
          const ids = env?.data?.session_ids ?? env?.session_ids ?? [];
          sessionIdsWithActionItemsCache = new Set(Array.isArray(ids) ? ids.map(Number) : []);
          lastFilteredSessions = lastFilteredSessions.filter((s) =>
            sessionIdsWithActionItemsCache.has(Number(s.id ?? s.session_id))
          );
          renderSessionsTable(lastFilteredSessions);
        })
        .catch(() => {
          sessionIdsWithActionItemsCache = new Set();
          renderSessionsTable(lastFilteredSessions);
        });
      return;
    }
    lastFilteredSessions = lastFilteredSessions.filter((s) =>
      sessionIdsWithActionItemsCache.has(Number(s.id ?? s.session_id))
    );
  } else {
    sessionIdsWithActionItemsCache = null;
  }
  renderSessionsTable(lastFilteredSessions);
}

function loadSessions() {
  const container = document.getElementById("sessions-list");
  const detailBlock = document.getElementById("session-detail");
  if (detailBlock?.close) detailBlock.close();
  if (!daemonOk) {
    container.innerHTML = emptyStateHtml("⚠️", "Демон не запущен", "Выполните: voiceforge daemon", DOCS_QUICKSTART);
    sessionsCache = [];
    return;
  }
  container.innerHTML = "<p class=\"muted\">" + t("loading") + "</p>";
  invoke("get_sessions", { limit: 200 })
    .then((raw) => {
      const env = parseEnvelope(raw);
      const sessions = env?.data?.sessions ?? env?.sessions ?? [];
      sessionsCache = Array.isArray(sessions) ? sessions : [];
      sessionIdsWithActionItemsCache = null;
      if (sessionsCache.length === 0) {
        container.innerHTML = emptyStateHtml("📋", "Сессий пока нет", "Запустите запись и анализ на главной.", DOCS_QUICKSTART);
        return;
      }
      applySessionsFilter();
    })
    .catch((e) => {
      container.innerHTML = "<p class=\"muted\">" + t("error_prefix") + (e?.message || e) + "</p><button type=\"button\" class=\"btn small\" id=\"sessions-retry\">" + t("retry_btn") + "</button>";
      document.getElementById("sessions-retry")?.addEventListener("click", () => loadSessions());
      sessionsCache = [];
    });
}

function renderSessionDetailTranscript(segs, highlightQuery) {
  const fullText = segs.map((s) => s.text || "").join(" ");
  const totalChars = fullText.length;
  const totalWords = fullText.trim() ? fullText.trim().split(/\s+/).length : 0;
  let html = "<div class=\"detail-section\"><h4>Транскрипт</h4><p class=\"muted detail-stats\">Слов: " + totalWords + ", символов: " + totalChars + "</p>";
  html += "<div class=\"detail-segment-minimap\" role=\"navigation\" aria-label=\"Навигация по сегментам\">";
  segs.forEach((s, idx) => {
    const t = s.start_sec != null ? Math.floor(Number(s.start_sec) / 60) + ":" + String(Math.floor(Number(s.start_sec) % 60)).padStart(2, "0") : String(idx + 1);
    html += `<button type="button" class="minimap-segment-btn" data-segment-idx="${idx}" title="Сегмент ${idx + 1}">${escapeHtml(t)}</button>`;
  });
  html += "</div><ul class=\"segment-list\">";
  segs.forEach((s, idx) => {
    const speaker = s.speaker ? `[${s.speaker}] ` : "";
    const time = (s.start_sec != null && s.end_sec != null) ? `${Number(s.start_sec).toFixed(1)}–${Number(s.end_sec).toFixed(1)} с ` : "";
    const textHtml = highlightQuery ? highlightSegmentText(s.text || "", highlightQuery) : escapeHtml(s.text || "");
    html += `<li id="segment-${idx}" data-segment-index="${idx}"><span class="segment-meta">${time}${speaker}</span>${textHtml} <button type="button" class="btn small segment-copy" aria-label="${t("segment_copy")}">${t("segment_copy")}</button></li>`;
  });
  html += "</ul></div>";
  return html;
}

function renderSessionDetailAnalysis(ana) {
  let html = "<div class=\"detail-section\"><h4>Анализ</h4>";
  if (ana.model) html += `<p class="muted">Модель: ${escapeHtml(ana.model)}</p>`;
  if (ana.questions?.length) {
    html += "<p><strong>Вопросы</strong></p><ul>";
    ana.questions.forEach((q) => { html += "<li>" + escapeHtml(String(q)) + "</li>"; });
    html += "</ul>";
  }
  if (ana.answers?.length) {
    html += "<p><strong>Ответы / выводы</strong></p><ul>";
    ana.answers.forEach((a) => { html += "<li>" + escapeHtml(String(a)) + "</li>"; });
    html += "</ul>";
  }
  if (ana.recommendations?.length) {
    html += "<p><strong>Рекомендации</strong></p><ul>";
    ana.recommendations.forEach((r) => { html += "<li>" + escapeHtml(String(r)) + "</li>"; });
    html += "</ul>";
  }
  if (ana.action_items?.length) {
    html += "<p><strong>Действия</strong></p><ul>";
    ana.action_items.forEach((ai) => {
      const d = typeof ai === "object" ? (ai.description || "") : String(ai);
      const who = typeof ai === "object" ? ai.assignee : "";
      html += "<li>" + escapeHtml(d) + (who ? " <span class=\"muted\">(" + escapeHtml(who) + ")</span>" : "") + "</li>";
    });
    html += "</ul>";
  }
  if (ana.cost_usd != null) html += "<p class=\"muted\">Стоимость: $" + Number(ana.cost_usd).toFixed(4) + "</p>";
  html += "</div>";
  return html;
}

function renderSessionDetail(detail, highlightQuery) {
  if (!detail || (typeof detail === "object" && !detail.segments && !detail.analysis)) {
    return "<p class=\"muted\">Нет данных.</p>";
  }
  const segs = Array.isArray(detail.segments) ? detail.segments : [];
  const ana = detail.analysis || null;
  let html = "";
  if (segs.length > 0) html += renderSessionDetailTranscript(segs, highlightQuery);
  const hasAnalysis = ana && (ana.questions?.length || ana.answers?.length || ana.recommendations?.length || ana.action_items?.length);
  if (hasAnalysis) html += renderSessionDetailAnalysis(ana);
  return html || "<p class=\"muted\">Нет анализа.</p>";
}

function bindSegmentCopyButtons(container) {
  container.querySelectorAll(".segment-copy").forEach((btn) => {
    btn.addEventListener("click", () => {
      const li = btn.closest("li");
      const idx = Number.parseInt(li?.dataset?.segmentIndex, 10);
      if (lastSessionDetail?.segments?.[idx] != null) {
        const text = lastSessionDetail.segments[idx].text || "";
        navigator.clipboard.writeText(text).then(() => {
          pushClipboardHistory(text);
          notify("VoiceForge", "Сегмент скопирован.");
        }).catch(() => {});
      }
    });
  });
}

function bindMinimapSegmentButtons(container) {
  container.querySelectorAll(".minimap-segment-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const idx = btn.dataset.segmentIdx;
      const el = idx != null ? document.getElementById("segment-" + idx) : null;
      if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  });
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text == null ? "" : String(text);
  return div.innerHTML;
}

function highlightSegmentText(text, query) {
  if (!query || !String(text)) return escapeHtml(text);
  const str = String(text);
  const q = String(query).trim();
  if (!q) return escapeHtml(str);
  const lower = str.toLowerCase();
  const qLower = q.toLowerCase();
  let out = "";
  let pos = 0;
  for (;;) {
    const i = lower.indexOf(qLower, pos);
    if (i === -1) {
      out += escapeHtml(str.slice(pos));
      break;
    }
    out += escapeHtml(str.slice(pos, i)) + "<mark class=\"fts-highlight\">" + escapeHtml(str.slice(i, i + q.length)) + "</mark>";
    pos = i + q.length;
  }
  return out;
}

let lastSessionDetail = null;

function hideSessionDetail() {
  const histPopover = document.getElementById("clipboard-history-popover");
  if (histPopover) histPopover.hidden = true;
  const histBtn = document.getElementById("clipboard-history-btn");
  if (histBtn) histBtn.setAttribute("aria-expanded", "false");
  const detailBlock = document.getElementById("session-detail");
  if (detailBlock?.close) detailBlock.close();
}

function transcriptToText(detail) {
  const segs = Array.isArray(detail?.segments) ? detail.segments : [];
  return segs
    .map((s) => {
      const speaker = s.speaker ? `[${s.speaker}] ` : "";
      const time = (s.start_sec != null && s.end_sec != null) ? `${Number(s.start_sec).toFixed(1)}–${Number(s.end_sec).toFixed(1)} с ` : "";
      return time + speaker + (s.text || "");
    })
    .join("\n");
}

function actionItemsToText(detail) {
  const ana = detail?.analysis;
  const items = Array.isArray(ana?.action_items) ? ana.action_items : [];
  return items
    .map((ai) => {
      const d = typeof ai === "object" ? (ai.description || "") : String(ai);
      const who = typeof ai === "object" ? ai.assignee : "";
      return who ? `${d} (${who})` : d;
    })
    .join("\n");
}

async function copyTranscriptToClipboard() {
  if (!lastSessionDetail) return;
  const text = transcriptToText(lastSessionDetail);
  if (!text) {
    notify("VoiceForge", "Нет транскрипта для копирования.");
    return;
  }
  try {
    await navigator.clipboard.writeText(text);
    pushClipboardHistory(text);
    notify("VoiceForge", "Транскрипт скопирован.");
  } catch (e) {
    notify("VoiceForge", "Не удалось скопировать: " + (e?.message || e));
  }
}

async function copyActionItemsToClipboard() {
  if (!lastSessionDetail) return;
  const text = actionItemsToText(lastSessionDetail);
  if (!text) {
    notify("VoiceForge", "Нет action items для копирования.");
    return;
  }
  try {
    await navigator.clipboard.writeText(text);
    pushClipboardHistory(text);
    notify("VoiceForge", "Action items скопированы.");
  } catch (e) {
    notify("VoiceForge", "Не удалось скопировать: " + (e?.message || e));
  }
}

function focusTrapDetail(e) {
  const detailBlock = document.getElementById("session-detail");
  if (!detailBlock?.open) return;
  const focusable = detailBlock.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (e.key === "Tab") {
    if (e.shiftKey) {
      if (document.activeElement === first) {
        e.preventDefault();
        last?.focus();
      }
    } else if (document.activeElement === last) {
      e.preventDefault();
      first?.focus();
    }
  }
}

function showSessionDetail(id, opts) {
  const highlightQuery = opts?.highlightQuery ?? null;
  const detailBlock = document.getElementById("session-detail");
  const bodyEl = document.getElementById("session-detail-body");
  const idEl = document.getElementById("detail-id");
  idEl.textContent = id;
  if (detailBlock.showModal) detailBlock.showModal();
  bodyEl.innerHTML = "<p class=\"muted\">" + t("loading") + "</p>";
  document.getElementById("export-md").onclick = () => exportSession(id, "md");
  document.getElementById("export-pdf").onclick = () => exportSession(id, "pdf");
  document.getElementById("export-docx").onclick = () => exportSession(id, "docx");
  document.getElementById("export-notion").onclick = () => exportSession(id, "notion");
  document.getElementById("export-otter").onclick = () => exportSession(id, "otter");
  document.getElementById("copy-transcript").onclick = copyTranscriptToClipboard;
  document.getElementById("copy-action-items").onclick = copyActionItemsToClipboard;
  document.getElementById("session-detail-print").onclick = () => globalThis.print();
  const histPopover = document.getElementById("clipboard-history-popover");
  if (histPopover) histPopover.hidden = true;
  const histBtn = document.getElementById("clipboard-history-btn");
  if (histBtn) histBtn.onclick = toggleClipboardHistoryPopover;
  document.getElementById("session-detail-close").onclick = hideSessionDetail;
  const tagsRow = document.getElementById("session-detail-tags");
  const tagsInput = document.getElementById("session-detail-tags-input");
  if (tagsRow) tagsRow.style.display = "block";
  if (tagsInput) {
    const tags = getSessionTags()[id] || [];
    tagsInput.value = tags.join(", ");
    tagsInput.onchange = () => {
      const val = (tagsInput.value || "").trim();
      const arr = val ? val.split(/,\s*/).map((t) => t.trim()).filter(Boolean) : [];
      setSessionTags(id, arr);
    };
  }
  detailBlock.onkeydown = (e) => {
    if (e.key === "Escape") {
      hideSessionDetail();
      return;
    }
    focusTrapDetail(e);
  };
  detailBlock.focus();
  invoke("get_session_detail", { sessionId: id })
    .then((raw) => {
      const env = parseEnvelope(raw);
      let detail = env?.data?.session_detail ?? env?.session_detail ?? env ?? {};
      if (typeof detail === "string") {
        try {
          detail = JSON.parse(detail);
        } catch {
          bodyEl.innerHTML = "<pre>" + escapeHtml(detail) + "</pre>";
          return;
        }
      }
      lastSessionDetail = detail;
      bodyEl.innerHTML = renderSessionDetail(detail, highlightQuery);
      bindSegmentCopyButtons(bodyEl);
      bindMinimapSegmentButtons(bodyEl);
    })
    .catch((e) => {
      bodyEl.innerHTML = "<p class=\"muted\">" + t("error_prefix") + escapeHtml(e?.message || e) + "</p><button type=\"button\" class=\"btn small\" id=\"detail-retry\">" + t("retry_btn") + "</button>";
      document.getElementById("detail-retry")?.addEventListener("click", () => showSessionDetail(id, opts));
    });
}

async function exportSession(id, format) {
  try {
    const out = await invoke("export_session", { sessionId: id, format });
    alert("Экспорт: " + (out || "выполнен"));
  } catch (e) {
    alert(t("export_error_prefix") + (e?.message || e));
  }
}

document.getElementById("costs-7d").addEventListener("click", () => loadAnalytics("7d"));
document.getElementById("costs-30d").addEventListener("click", () => loadAnalytics("30d"));
document.getElementById("costs-export-btn")?.addEventListener("click", exportCostsReport);

let chartDaysInstance = null;
let chartModelsInstance = null;

function getChartColors() {
  const style = getComputedStyle(document.body);
  return {
    fg: style.getPropertyValue("--fg").trim() || "#e0e0e0",
    muted: style.getPropertyValue("--muted").trim() || "#888",
    accent: style.getPropertyValue("--accent").trim() || "#64b5f6",
    palette: [
      style.getPropertyValue("--accent").trim() || "#64b5f6",
      "#81c784",
      "#ffb74d",
      "#ba68c8",
      "#4dd0e1",
    ],
  };
}

function drawCostsCharts(data) {
  const byDay = (data?.by_day ?? []).slice(-14).reverse();
  const byModel = data?.by_model ?? [];
  const colors = getChartColors();

  if (chartDaysInstance) {
    chartDaysInstance.destroy();
    chartDaysInstance = null;
  }
  const canvasDays = document.getElementById("costs-chart-days");
  if (canvasDays && byDay.length > 0) {
    chartDaysInstance = new Chart(canvasDays, {
      type: "bar",
      data: {
        labels: byDay.map((r) => String(r.date ?? "")),
        datasets: [{ label: "Стоимость ($)", data: byDay.map((r) => r.cost_usd ?? r.cost ?? 0), backgroundColor: colors.accent }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: colors.muted }, grid: { color: colors.muted } },
          y: { ticks: { color: colors.muted }, grid: { color: colors.muted } },
        },
      },
    });
  }

  if (chartModelsInstance) {
    chartModelsInstance.destroy();
    chartModelsInstance = null;
  }
  const canvasModels = document.getElementById("costs-chart-models");
  if (canvasModels && byModel.length > 0) {
    chartModelsInstance = new Chart(canvasModels, {
      type: "doughnut",
      data: {
        labels: byModel.map((r) => r.model ?? "—"),
        datasets: [{ data: byModel.map((r) => r.cost_usd ?? r.cost ?? 0), backgroundColor: colors.palette }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: colors.fg } },
        },
      },
    });
  }
}

function renderAnalytics(data, period) {
  if (!data || typeof data !== "object") return "<p class=\"muted\">Нет данных.</p>";
  const total = data.total_cost_usd ?? 0;
  const calls = data.total_calls ?? 0;
  const byModel = data.by_model ?? [];
  const byDay = data.by_day ?? [];
  let html = "<div class=\"analytics-summary\"><p><strong>Итого за период:</strong> $" + Number(total).toFixed(4) + " <span class=\"muted\">(" + calls + " вызовов)</span></p></div>";
  if (byModel.length > 0) {
    html += "<div class=\"detail-section\"><h4>По моделям</h4><table><thead><tr><th>Модель</th><th>Стоимость ($)</th><th>Вызовы</th></tr></thead><tbody>";
    byModel.forEach((r) => {
      const cost = (r.cost_usd ?? r.cost ?? 0);
      const n = r.calls ?? r.count ?? "—";
      html += "<tr><td>" + escapeHtml(r.model ?? "—") + "</td><td>" + Number(cost).toFixed(4) + "</td><td>" + n + "</td></tr>";
    });
    html += "</tbody></table></div>";
  }
  if (byDay.length > 0) {
    const slice = byDay.slice(-14).reverse();
    html += "<div class=\"detail-section\"><h4>По дням</h4><table><thead><tr><th>Дата</th><th>Стоимость ($)</th><th>Вызовы</th></tr></thead><tbody>";
    slice.forEach((r) => {
      const cost = (r.cost_usd ?? r.cost ?? 0);
      const n = r.calls ?? r.count ?? "—";
      html += "<tr><td>" + escapeHtml(String(r.date ?? "—")) + "</td><td>" + Number(cost).toFixed(4) + "</td><td>" + n + "</td></tr>";
    });
    html += "</tbody></table></div>";
  }
  return html;
}

function loadAnalytics(period) {
  const container = document.getElementById("analytics-content");
  if (!daemonOk) {
    container.innerHTML = emptyStateHtml("⚠️", "Демон не запущен", "Запустите: voiceforge daemon", DOCS_QUICKSTART);
    return;
  }
  container.innerHTML = "<p class=\"muted\">" + t("loading") + "</p>";
  invoke("get_analytics", { period })
    .then((raw) => {
      const env = parseEnvelope(raw);
      let data = env?.data?.analytics ?? env?.analytics ?? env ?? {};
      if (typeof data === "string") {
        try {
          data = JSON.parse(data);
        } catch {
          container.innerHTML = "<pre>" + escapeHtml(data) + "</pre>";
          return;
        }
      }
      lastAnalyticsData = data;
      drawCostsCharts(data);
      container.innerHTML = renderAnalytics(data, period);
    })
    .catch((e) => {
      container.innerHTML = "<p class=\"muted\">" + t("error_prefix") + (e?.message || e) + "</p><button type=\"button\" class=\"btn small\" id=\"analytics-retry\">" + t("retry_btn") + "</button>";
      document.getElementById("analytics-retry")?.addEventListener("click", () => loadAnalytics(period));
    });
}

const SETTINGS_LABELS = {
  model_size: "Размер модели (diarization)",
  default_llm: "LLM по умолчанию",
  budget_limit_usd: "Лимит бюджета (USD)",
  smart_trigger: "Умный триггер",
  sample_rate: "Частота дискретизации",
  streaming_stt: "Стриминг STT",
  pii_mode: "Режим PII",
  privacy_mode: "Режим конфиденциальности",
  language: "Язык распознавания (STT)",
};

function renderSettings(data) {
  if (!data || typeof data !== "object") return "<p class=\"muted\">Нет данных.</p>";
  const keys = Object.keys(SETTINGS_LABELS).filter((k) => Object.hasOwn(data, k));
  if (keys.length === 0) {
    return "<p class=\"muted\">Нет настроек.</p>";
  }
  let html = "";
  keys.forEach((key) => {
    const label = SETTINGS_LABELS[key] || key;
    let val = data[key];
    if (typeof val === "number" && key === "budget_limit_usd") val = "$" + Number(val).toFixed(2);
    else if (typeof val === "object") val = JSON.stringify(val);
    else val = String(val ?? "—");
    html += "<div class=\"settings-item\"><span class=\"settings-key\">" + escapeHtml(label) + "</span><span class=\"settings-val\">" + escapeHtml(val) + "</span></div>";
  });
  return html;
}

function loadSettings() {
  const container = document.getElementById("settings-content");
  if (!daemonOk) {
    container.innerHTML = emptyStateHtml("⚠️", "Демон не запущен", "Настройки загружаются с демона.", DOCS_QUICKSTART);
    return;
  }
  invoke("get_settings")
    .then((raw) => {
      const env = parseEnvelope(raw);
      let data = env?.data?.settings ?? env?.settings ?? env ?? {};
      if (typeof data === "string") {
        try {
          data = JSON.parse(data);
        } catch {
          container.innerHTML = "<pre>" + escapeHtml(data) + "</pre>";
          return;
        }
      }
      container.innerHTML = renderSettings(data) + "<p class=\"muted settings-hint\" id=\"daemon-version-line\">Версия демона: …</p>";
      invoke("get_daemon_version")
        .then((v) => {
          const el = document.getElementById("daemon-version-line");
          if (el) el.textContent = "Версия демона: " + (v || "—");
        })
        .catch(() => {
          const el = document.getElementById("daemon-version-line");
          if (el) el.textContent = "Версия демона: недоступна";
        });
    })
    .catch((e) => {
      container.innerHTML = "<p class=\"muted\">" + t("error_prefix") + escapeHtml(e?.message || e) + "</p><button type=\"button\" class=\"btn small\" id=\"settings-retry\">" + t("retry_btn") + "</button>";
      document.getElementById("settings-retry")?.addEventListener("click", () => loadSettings());
    });
}

const WINDOW_STATE_KEY = "voiceforge_window_state";
const HOTKEYS_ENABLED_KEY = "voiceforge_hotkeys_enabled";
const THEME_KEY = "voiceforge_theme";
const CLOSE_TO_TRAY_KEY = "voiceforge_close_to_tray";
const AUTOSTART_KEY = "voiceforge_autostart";
const UPDATER_CHECK_ON_LAUNCH_KEY = "voiceforge_updater_check_on_launch";
const ONBOARDING_DISMISSED_KEY = "voiceforge_onboarding_dismissed";
const COMPACT_MODE_KEY = "voiceforge_compact_mode";
const COMPACT_WINDOW_STATE_KEY = "voiceforge_compact_window_state";
const COMPACT_DEFAULT_WIDTH = 380;
const COMPACT_DEFAULT_HEIGHT = 72;
const DASHBOARD_ORDER_KEY = "voiceforge_dashboard_order";
const DASHBOARD_COLLAPSED_KEY = "voiceforge_dashboard_collapsed";
const DASHBOARD_WIDGET_IDS = ["record", "analyze", "streaming", "recent-sessions", "last-analysis", "upcoming-events", "cost-widget"];
const FAVORITES_KEY = "voiceforge_favorites";
const SESSION_TAGS_KEY = "voiceforge_session_tags";
/** Block 44 / #88: clipboard history (last N copied fragments). */
const CLIPBOARD_HISTORY_KEY = "voiceforge_clipboard_history";
const MAX_CLIPBOARD_HISTORY = 20;

function getSessionTags() {
  try {
    const raw = localStorage.getItem(SESSION_TAGS_KEY);
    if (raw) {
      const o = JSON.parse(raw);
      if (o && typeof o === "object") return o;
    }
  } catch (e) {
    console.debug("getSessionTags", e);
  }
  return {};
}

function setSessionTags(sessionId, tags) {
  const id = Number(sessionId);
  if (Number.isNaN(id)) return;
  const o = getSessionTags();
  const arr = Array.isArray(tags) ? tags.map(String).filter(Boolean) : [];
  if (arr.length) o[id] = arr; else delete o[id];
  const s = JSON.stringify(o);
  localStorage.setItem(SESSION_TAGS_KEY, s);
  setStored(SESSION_TAGS_KEY, o);
  updateSessionTagFilterOptions();
}

function updateSessionTagFilterOptions() {
  const sel = document.getElementById("sessions-tag-filter");
  if (!sel) return;
  const tagsMap = getSessionTags();
  const allTags = [...new Set(Object.values(tagsMap).flat())].filter(Boolean).sort((a, b) => String(a).localeCompare(String(b), undefined, { sensitivity: "base" }));
  const current = sel.value;
  sel.innerHTML = "<option value=\"all\">Все</option>" + allTags.map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join("");
  if (allTags.includes(current)) sel.value = current; else sel.value = "all";
}

/** Returns clipboard history entries (newest first). Each item: { t: string, ts: number }. */
function getClipboardHistory() {
  try {
    const raw = localStorage.getItem(CLIPBOARD_HISTORY_KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw);
    return Array.isArray(arr) ? arr.slice(0, MAX_CLIPBOARD_HISTORY) : [];
  } catch (e) {
    console.debug("getClipboardHistory", e);
    return [];
  }
}

/** Appends text to clipboard history (dedupe by trimming, newest first). */
function pushClipboardHistory(text) {
  const s = (text || "").trim();
  if (!s) return;
  let arr = getClipboardHistory();
  arr = [{ t: s, ts: Date.now() }, ...arr.filter((e) => (e.t || "").trim() !== s)];
  arr = arr.slice(0, MAX_CLIPBOARD_HISTORY);
  try {
    localStorage.setItem(CLIPBOARD_HISTORY_KEY, JSON.stringify(arr));
  } catch (e) {
    console.debug("pushClipboardHistory", e);
  }
}

function toggleClipboardHistoryPopover() {
  const popover = document.getElementById("clipboard-history-popover");
  const btn = document.getElementById("clipboard-history-btn");
  if (!popover || !btn) return;
  const isOpen = !popover.hidden;
  if (isOpen) {
    popover.hidden = true;
    btn.setAttribute("aria-expanded", "false");
    return;
  }
  const entries = getClipboardHistory();
  const listEl = document.getElementById("clipboard-history-list");
  if (!listEl) return;
  if (entries.length === 0) {
    listEl.innerHTML = "<p class=\"muted\">" + escapeHtml(t("clipboard_history_empty")) + "</p>";
  } else {
    const maxPreview = 120;
    listEl.innerHTML = entries.map((e, i) => {
      const preview = (e.t || "").slice(0, maxPreview) + ((e.t || "").length > maxPreview ? "…" : "");
      return `<button type="button" class="clipboard-history-item" data-index="${i}">${escapeHtml(preview)}</button>`;
    }).join("");
    listEl.querySelectorAll(".clipboard-history-item").forEach((el) => {
      const idx = Number(el.dataset.index, 10);
      const text = entries[idx]?.t ?? "";
      el.addEventListener("click", () => {
        navigator.clipboard.writeText(text).then(() => {
          notify("VoiceForge", "Скопировано.");
          popover.hidden = true;
          btn.setAttribute("aria-expanded", "false");
        }).catch(() => {});
      });
    });
  }
  popover.hidden = false;
  btn.setAttribute("aria-expanded", "true");
}

function getFavorites() {
  try {
    const raw = localStorage.getItem(FAVORITES_KEY);
    if (raw) {
      const arr = JSON.parse(raw);
      return Array.isArray(arr) ? new Set(arr.map(Number)) : new Set();
    }
  } catch (e) {
    console.debug("getFavorites", e);
  }
  return new Set();
}

function setFavorites(ids) {
  const arr = Array.from(ids);
  setStored(FAVORITES_KEY, arr);
}

function toggleFavorite(sessionId) {
  const fav = getFavorites();
  if (fav.has(sessionId)) fav.delete(sessionId);
  else fav.add(sessionId);
  setFavorites(fav);
  applySessionsFilter();
}
const DOCS_QUICKSTART = "https://github.com/iurii-izman/voiceforge/blob/main/docs/runbooks/quickstart.md";

function parseDeepLinkSessionId(url) {
  if (!url || typeof url !== "string") return null;
  const u = url.trim();
  const re1 = /session\/(\d+)/i;
  const re2 = /\/session\/(\d+)/i;
  const m = re1.exec(u) || re2.exec(u);
  if (m) return Number.parseInt(m[1], 10);
  return null;
}

function handleDeepLinkUrls(urls) {
  if (!Array.isArray(urls) && urls != null) urls = [urls];
  if (!urls?.length) return;
  for (const url of urls) {
    const id = parseDeepLinkSessionId(url);
    if (id != null && !Number.isNaN(id)) {
      switchTab("sessions");
      setTimeout(() => showSessionDetail(id), 200);
      return;
    }
  }
}
const SHORTCUT_RECORD_DEFAULT = "CommandOrControl+Shift+R";
const SHORTCUT_ANALYZE_DEFAULT = "CommandOrControl+Shift+A";

function getShortcuts() {
  const r = localStorage.getItem("voiceforge_shortcut_record") || SHORTCUT_RECORD_DEFAULT;
  const a = localStorage.getItem("voiceforge_shortcut_analyze") || SHORTCUT_ANALYZE_DEFAULT;
  return [r.trim() || SHORTCUT_RECORD_DEFAULT, a.trim() || SHORTCUT_ANALYZE_DEFAULT];
}

let currentShortcuts = [];
let windowStateSaveTimeout = null;

async function restoreWindowState() {
  try {
    const raw = localStorage.getItem(WINDOW_STATE_KEY);
    if (!raw) return;
    const s = JSON.parse(raw);
    if (typeof s.x !== "number" || typeof s.y !== "number" || typeof s.width !== "number" || typeof s.height !== "number") return;
    const win = getCurrentWindow();
    const scale = await win.scaleFactor();
    const x = Math.round(s.x / scale);
    const y = Math.round(s.y / scale);
    const w = Math.round(s.width / scale);
    const h = Math.round(s.height / scale);
    await win.setPosition(new LogicalPosition(x, y));
    await win.setSize(new LogicalSize(w, h));
  } catch (e) {
    if (e != null) console.debug("restoreWindowState", e);
  }
}

function saveWindowState() {
  if (windowStateSaveTimeout) return;
  windowStateSaveTimeout = setTimeout(async () => {
    windowStateSaveTimeout = null;
    try {
      const win = getCurrentWindow();
      const pos = await win.innerPosition();
      const size = await win.innerSize();
      const key = document.getElementById("app-root")?.classList.contains("compact-mode") ? COMPACT_WINDOW_STATE_KEY : WINDOW_STATE_KEY;
      localStorage.setItem(key, JSON.stringify({ x: pos.x, y: pos.y, width: size.width, height: size.height }));
    } catch (e) {
      console.debug("saveWindowState", e);
    }
  }, 300);
}

async function setupWindowStatePersistence() {
  try {
    await restoreWindowState();
    const win = getCurrentWindow();
    await win.onMoved(() => {
      saveWindowState();
      saveCompactWindowState();
    });
    await win.onResized(() => {
      saveWindowState();
      saveCompactWindowState();
    });
  } catch (e) {
    if (e != null) console.debug("setupWindowStatePersistence", e);
  }
}

async function setupCloseToTray() {
  const win = getCurrentWindow();
  await win.onCloseRequested(async (event) => {
    if (localStorage.getItem(CLOSE_TO_TRAY_KEY) === "true") {
      event.preventDefault();
      await win.hide();
    }
  });
}

/** Returns whether the effective theme is dark (for tray icon). */
function getEffectiveIsDark(themeValue) {
  const v = themeValue ?? localStorage.getItem(THEME_KEY) ?? "dark";
  if (v === "auto") return globalThis.matchMedia("(prefers-color-scheme: dark)").matches;
  return v === "dark";
}

function applyTheme(theme) {
  const v = theme || localStorage.getItem(THEME_KEY) || "dark";
  document.body.className = "theme-" + (v === "auto" ? "auto" : v);
  const isDark = getEffectiveIsDark(v);
  invoke("set_tray_theme", { isDark }).catch(() => {});
}

function emptyStateHtml(icon, title, hint, linkHref) {
  const link = linkHref ? `<p><a href="${escapeHtml(linkHref)}" target="_blank" rel="noopener">Быстрый старт в репозитории</a></p>` : "";
  return `<div class="empty-state"><div class="empty-state-icon" aria-hidden="true">${icon}</div><p><strong>${escapeHtml(title)}</strong></p><p>${escapeHtml(hint)}</p>${link}</div>`;
}

function showOnboarding() {
  const overlay = document.getElementById("onboarding-overlay");
  if (localStorage.getItem(ONBOARDING_DISMISSED_KEY) === "true" || !overlay) return;
  if (overlay.showModal) overlay.showModal();
  document.getElementById("onboarding-ok").onclick = () => {
    if (document.getElementById("onboarding-never")?.checked) localStorage.setItem(ONBOARDING_DISMISSED_KEY, "true");
    if (overlay.close) overlay.close();
  };
}

function initTheme() {
  applyTheme();
  const radios = document.querySelectorAll('input[name="theme"]');
  const saved = localStorage.getItem(THEME_KEY) || "dark";
  radios.forEach((r) => {
    if (r.value === saved) r.checked = true;
    r.addEventListener("change", () => {
      setStored(THEME_KEY, r.value);
      applyTheme(r.value);
    });
  });
  globalThis.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if (localStorage.getItem(THEME_KEY) === "auto") applyTheme("auto");
  });
}

function initUiLang() {
  applyUiLang();
  const sel = document.getElementById("ui-lang");
  if (!sel) return;
  const saved = localStorage.getItem(UI_LANG_KEY) || "ru";
  sel.value = saved === "en" ? "en" : "ru";
  sel.addEventListener("change", () => {
    const v = sel.value === "en" ? "en" : "ru";
    setStored(UI_LANG_KEY, v);
    applyUiLang();
  });
}

function initHotkeysCard() {
  const cb = document.getElementById("hotkeys-enabled");
  const inputRecord = document.getElementById("hotkey-record");
  const inputAnalyze = document.getElementById("hotkey-analyze");
  if (cb) {
    cb.checked = localStorage.getItem(HOTKEYS_ENABLED_KEY) !== "false";
    cb.addEventListener("change", async () => {
      const enabled = cb.checked;
      setStored(HOTKEYS_ENABLED_KEY, enabled ? "true" : "false");
      if (enabled) await setupGlobalShortcuts();
      else await teardownGlobalShortcuts();
    });
  }
  if (inputRecord) {
    inputRecord.value = localStorage.getItem("voiceforge_shortcut_record") || SHORTCUT_RECORD_DEFAULT;
    inputRecord.addEventListener("change", async () => {
      const v = (inputRecord.value || "").trim() || SHORTCUT_RECORD_DEFAULT;
      setStored("voiceforge_shortcut_record", v);
      await teardownGlobalShortcuts();
      if (localStorage.getItem(HOTKEYS_ENABLED_KEY) !== "false") await setupGlobalShortcuts();
    });
  }
  if (inputAnalyze) {
    inputAnalyze.value = localStorage.getItem("voiceforge_shortcut_analyze") || SHORTCUT_ANALYZE_DEFAULT;
    inputAnalyze.addEventListener("change", async () => {
      const v = (inputAnalyze.value || "").trim() || SHORTCUT_ANALYZE_DEFAULT;
      setStored("voiceforge_shortcut_analyze", v);
      await teardownGlobalShortcuts();
      if (localStorage.getItem(HOTKEYS_ENABLED_KEY) !== "false") await setupGlobalShortcuts();
    });
  }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function exportSessionsList(format) {
  const list = lastFilteredSessions.length ? lastFilteredSessions : sessionsCache;
  if (!list.length) {
    alert("Нет сессий для экспорта.");
    return;
  }
  if (format === "json") {
    const arr = list.map((s) => ({
      id: s.id ?? s.session_id,
      started_at: s.started_at ?? s.created_at,
      duration_sec: s.duration_sec,
    }));
    const blob = new Blob([JSON.stringify(arr, null, 2)], { type: "application/json" });
    downloadBlob(blob, "voiceforge-sessions.json");
    return;
  }
  const header = "id,started_at,duration_sec\n";
  const rows = list.map((s) => {
    const id = s.id ?? s.session_id ?? "";
    const start = (s.started_at ?? s.created_at ?? "").replaceAll('"', '""');
    const dur = s.duration_sec ?? "";
    return `${id},"${start}",${dur}`;
  });
  const csv = header + rows.join("\n");
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8" });
  downloadBlob(blob, "voiceforge-sessions.csv");
}

function exportCostsReport() {
  if (!lastAnalyticsData) {
    alert("Сначала загрузите отчёт (7 или 30 дней).");
    return;
  }
  const byDay = lastAnalyticsData.by_day ?? [];
  const byModel = lastAnalyticsData.by_model ?? [];
  let csv = "date,cost_usd,calls\n";
  byDay.forEach((r) => {
    csv += `${r.date ?? ""},${r.cost_usd ?? r.cost ?? 0},${r.calls ?? r.count ?? ""}\n`;
  });
  csv += "\nmodel,cost_usd,calls\n";
  byModel.forEach((r) => {
    const model = (r.model ?? "").replaceAll('"', '""');
    csv += `"${model}",${r.cost_usd ?? r.cost ?? 0},${r.calls ?? r.count ?? ""}\n`;
  });
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8" });
  downloadBlob(blob, "voiceforge-costs-report.csv");
}

async function handleFtsSearch(q, listEl, resultsEl) {
  if (!daemonOk) return;
  try {
    const raw = await invoke("search_transcripts", { query: q, limit: 25 });
    const env = parseEnvelope(raw);
    const hits = env?.data?.hits ?? env?.hits ?? [];
    if (!Array.isArray(hits) || hits.length === 0) {
      if (resultsEl) {
        resultsEl.innerHTML = "<p class=\"muted\">Ничего не найдено.</p>";
        resultsEl.style.display = "block";
      }
      if (listEl) listEl.style.display = "none";
      return;
    }
    let html = "<p class=\"muted\">Найдено по тексту:</p><ul class=\"fts-hits-list\">";
    hits.forEach((h) => {
      const sid = h.session_id ?? "—";
      const snip = escapeHtml((h.snippet ?? h.text ?? "").trim() || "—");
      html += `<li><button type="button" class="btn-link fts-hit" data-session-id="${sid}">Сессия ${sid}</button>: ${snip}</li>`;
    });
    html += "</ul>";
    if (resultsEl) {
      resultsEl.innerHTML = html;
      resultsEl.style.display = "block";
      resultsEl.querySelectorAll(".fts-hit").forEach((btn) => {
        btn.addEventListener("click", () => showSessionDetail(Number(btn.dataset.sessionId)));
      });
    }
    if (listEl) listEl.style.display = "none";
  } catch (e) {
    if (resultsEl) {
      resultsEl.innerHTML = "<p class=\"muted\">" + t("error_prefix") + escapeHtml(e?.message || e) + "</p>";
      resultsEl.style.display = "block";
    }
    if (listEl) listEl.style.display = "none";
  }
}

function initSessionsToolbar() {
  document.getElementById("sessions-search")?.addEventListener("input", () => applySessionsFilter());
  document.getElementById("sessions-period")?.addEventListener("change", () => applySessionsFilter());
  document.getElementById("sessions-sort")?.addEventListener("change", () => applySessionsFilter());
  document.getElementById("sessions-favorites-filter")?.addEventListener("change", () => applySessionsFilter());
  document.getElementById("sessions-action-items-filter")?.addEventListener("change", () => applySessionsFilter());
  document.getElementById("sessions-tag-filter")?.addEventListener("change", () => applySessionsFilter());
  updateSessionTagFilterOptions();
  let ftsSearchTimeout = null;
  document.getElementById("sessions-fts-search")?.addEventListener("input", () => {
    const input = document.getElementById("sessions-fts-search");
    const q = (input?.value ?? "").trim();
    const listEl = document.getElementById("sessions-list");
    const resultsEl = document.getElementById("sessions-fts-results");
    if (!q) {
      if (resultsEl) resultsEl.style.display = "none";
      if (listEl) listEl.style.display = "";
      applySessionsFilter();
      return;
    }
    if (ftsSearchTimeout) clearTimeout(ftsSearchTimeout);
    ftsSearchTimeout = setTimeout(() => {
      ftsSearchTimeout = null;
      void handleFtsSearch(q, listEl, resultsEl);
    }, 350);
  });
  document.getElementById("sessions-export-btn")?.addEventListener("click", () => {
    const format = confirm("Экспорт в CSV? (Отмена = JSON)") ? "csv" : "json";
    exportSessionsList(format);
  });
}

function setUpdateStatus(text) {
  const statusEl = document.getElementById("updater-status");
  if (statusEl) statusEl.textContent = text;
}

async function handleUpdateFound(update, silentIfNone) {
  if (silentIfNone) {
    setUpdateStatus("Доступна версия " + update.version + ". Нажмите «Проверить сейчас» для установки.");
    return;
  }
  setUpdateStatus("Найдено обновление " + update.version + "…");
  const install = confirm("Доступна версия " + update.version + ".\n\n" + (update.body || "") + "\n\nУстановить сейчас?");
  if (install) {
    setUpdateStatus("Установка…");
    await update.downloadAndInstall();
    await relaunch();
  } else {
    setUpdateStatus("Обновление отложено.");
  }
}

async function checkForUpdate(silentIfNone = false) {
  try {
    const update = await updaterCheck();
    if (update) {
      await handleUpdateFound(update, silentIfNone);
      return;
    }
    setUpdateStatus(silentIfNone ? "" : "Обновлений нет.");
  } catch (e) {
    setUpdateStatus("Обновления отключены или недоступны.");
    if (!silentIfNone && e != null) console.debug("updater check", e);
  }
}

function initUpdaterCard() {
  const cb = document.getElementById("updater-check-on-launch");
  const btn = document.getElementById("updater-check-now");
  if (cb) {
    cb.checked = localStorage.getItem(UPDATER_CHECK_ON_LAUNCH_KEY) === "true";
    cb.addEventListener("change", () => localStorage.setItem(UPDATER_CHECK_ON_LAUNCH_KEY, cb.checked ? "true" : "false"));
  }
  if (btn) btn.addEventListener("click", () => checkForUpdate(false));
}

async function initAutostartCard() {
  const cb = document.getElementById("autostart-enabled");
  if (!cb) return;
  try {
    cb.checked = await autostartIsEnabled();
    localStorage.setItem(AUTOSTART_KEY, cb.checked ? "true" : "false");
  } catch (e) {
    if (e != null) console.debug("autostart isEnabled", e);
  }
  cb.addEventListener("change", async () => {
    try {
      if (cb.checked) await autostartEnable();
      else await autostartDisable();
      localStorage.setItem(AUTOSTART_KEY, cb.checked ? "true" : "false");
    } catch (e) {
      if (e != null) console.debug("autostart enable/disable", e);
    }
  });
}

function initCloseToTrayCard() {
  const cb = document.getElementById("close-to-tray");
  if (!cb) return;
  cb.checked = localStorage.getItem(CLOSE_TO_TRAY_KEY) === "true";
  cb.addEventListener("change", () => {
    setStored(CLOSE_TO_TRAY_KEY, cb.checked ? "true" : "false");
  });
}

function initSoundOnRecordCard() {
  const cb = document.getElementById("sound-on-record");
  if (!cb) return;
  cb.checked = localStorage.getItem("voiceforge_sound_on_record") === "true";
  cb.addEventListener("change", () => {
    setStored("voiceforge_sound_on_record", cb.checked ? "true" : "false");
  });
}

function getCompactWindowState() {
  const raw = localStorage.getItem(COMPACT_WINDOW_STATE_KEY);
  let w = COMPACT_DEFAULT_WIDTH;
  let h = COMPACT_DEFAULT_HEIGHT;
  let x = null;
  let y = null;
  if (raw) {
    try {
      const s = JSON.parse(raw);
      if (typeof s.width === "number") w = s.width;
      if (typeof s.height === "number") h = s.height;
      if (typeof s.x === "number") x = s.x;
      if (typeof s.y === "number") y = s.y;
    } catch (e) {
      console.debug("getCompactWindowState parse", e);
    }
  }
  return { w, h, x, y };
}

async function applyCompactModeOn(win) {
  try {
    const pos = await win.innerPosition();
    const size = await win.innerSize();
    localStorage.setItem(WINDOW_STATE_KEY, JSON.stringify({ x: pos.x, y: pos.y, width: size.width, height: size.height }));
  } catch (e) {
    console.debug("applyCompactMode save state", e);
  }
  const appRoot = document.getElementById("app-root");
  const compactBar = document.getElementById("compact-bar");
  const fullContent = document.getElementById("full-content");
  appRoot.classList.add("compact-mode");
  compactBar.style.display = "flex";
  fullContent.style.display = "none";
  try {
    const { w, h, x, y } = getCompactWindowState();
    await win.setSize(new LogicalSize(w, h));
    if (x != null && y != null) await win.setPosition(new LogicalPosition(x, y));
  } catch (e) {
    if (e != null) console.debug("applyCompactMode setSize", e);
  }
  const compactStatus = document.getElementById("compact-status");
  if (compactStatus) {
    compactStatus.textContent = daemonOk ? "Демон ок" : "Демон выкл";
    compactStatus.className = "status " + (daemonOk ? "daemon-ok" : "daemon-off");
  }
}

async function applyCompactModeOff(win) {
  const appRoot = document.getElementById("app-root");
  const compactBar = document.getElementById("compact-bar");
  const fullContent = document.getElementById("full-content");
  appRoot.classList.remove("compact-mode");
  compactBar.style.display = "none";
  fullContent.style.display = "block";
  try {
    const raw = localStorage.getItem(COMPACT_WINDOW_STATE_KEY);
    if (raw) {
      const pos = await win.outerPosition();
      const size = await win.outerSize();
      localStorage.setItem(COMPACT_WINDOW_STATE_KEY, JSON.stringify({ x: pos.x, y: pos.y, width: size.width, height: size.height }));
    }
    await restoreWindowState();
  } catch (e) {
    if (e != null) console.debug("applyCompactMode restore", e);
  }
}

async function applyCompactMode(compact) {
  const win = getCurrentWindow();
  if (compact) {
    await applyCompactModeOn(win);
  } else {
    await applyCompactModeOff(win);
  }
}

function initCompactMode() {
  const cb = document.getElementById("compact-mode-toggle");
  if (!cb) return;
  const compact = localStorage.getItem(COMPACT_MODE_KEY) === "true";
  cb.checked = compact;
  if (compact) applyCompactMode(true);
  cb.addEventListener("change", async () => {
    const enabled = cb.checked;
    setStored(COMPACT_MODE_KEY, enabled ? "true" : "false");
    await applyCompactMode(enabled);
  });
  document.getElementById("compact-listen")?.addEventListener("click", () => { if (daemonOk) toggleListen(); });
  document.getElementById("compact-analyze")?.addEventListener("click", () => runDefaultAnalyze());
}

function saveCompactWindowState() {
  if (!document.getElementById("app-root")?.classList.contains("compact-mode")) return;
  saveWindowState();
}

function getDashboardOrder() {
  try {
    const raw = localStorage.getItem(DASHBOARD_ORDER_KEY);
    if (raw) {
      const arr = JSON.parse(raw);
      if (Array.isArray(arr) && arr.length) return arr;
    }
  } catch (e) {
    console.debug("getDashboardOrder", e);
  }
  return DASHBOARD_WIDGET_IDS.slice();
}

function getDashboardCollapsed() {
  try {
    const raw = localStorage.getItem(DASHBOARD_COLLAPSED_KEY);
    if (raw) return JSON.parse(raw);
  } catch (e) {
    console.debug("getDashboardCollapsed", e);
  }
  return {};
}

function saveDashboardOrder(order) {
  setStored(DASHBOARD_ORDER_KEY, order);
}

function saveDashboardCollapsed(collapsed) {
  setStored(DASHBOARD_COLLAPSED_KEY, collapsed);
}

function initDashboardWidgets() {
  const container = document.getElementById("dashboard-widgets");
  if (!container) return;
  const order = getDashboardOrder();
  const collapsed = getDashboardCollapsed();
  const widgets = Array.from(container.querySelectorAll(".dashboard-widget"));
  const byId = new Map(widgets.map((w) => [w.dataset.widgetId, w]));
  order.forEach((id) => {
    const el = byId.get(id);
    if (el) container.appendChild(el);
  });
  widgets.forEach((widget) => {
    const id = widget.dataset.widgetId;
    if (collapsed[id]) widget.classList.add("collapsed");
    const toggle = widget.querySelector(".widget-toggle");
    const up = widget.querySelector(".widget-up");
    const down = widget.querySelector(".widget-down");
    toggle?.addEventListener("click", () => {
      widget.classList.toggle("collapsed");
      const c = getDashboardCollapsed();
      c[id] = widget.classList.contains("collapsed");
      saveDashboardCollapsed(c);
      toggle.setAttribute("aria-label", widget.classList.contains("collapsed") ? "Развернуть" : "Свернуть");
      toggle.textContent = widget.classList.contains("collapsed") ? "▶" : "▼";
    });
    up?.addEventListener("click", () => {
      const prev = widget.previousElementSibling;
      if (prev?.classList.contains("dashboard-widget")) {
        prev.before(widget);
        const newOrder = Array.from(container.querySelectorAll(".dashboard-widget")).map((w) => w.dataset.widgetId);
        saveDashboardOrder(newOrder);
      }
    });
    down?.addEventListener("click", () => {
      const next = widget.nextElementSibling;
      if (next?.classList.contains("dashboard-widget")) {
        widget.before(next);
        const newOrder = Array.from(container.querySelectorAll(".dashboard-widget")).map((w) => w.dataset.widgetId);
        saveDashboardOrder(newOrder);
      }
    });
  });
}

(async () => { // NOSONAR S7785 — top-level await not supported by build target (es2020/chrome87)
  await loadStoreAndMigrate();
  initTheme();
  initUiLang();
  showOnboarding();
  await setupWindowStatePersistence();
  await setupCloseToTray();
  initHotkeysCard();
  initUpdaterCard();
  initAutostartCard();
  initCloseToTrayCard();
  initSoundOnRecordCard();
  initCompactMode();
  initSettingsPanelMode();
  initDashboardWidgets();
  initQuickActions();
  initSessionsToolbar();
  initSessionContextMenu();
  try {
    const startUrls = await getCurrent();
    if (startUrls?.length) handleDeepLinkUrls(startUrls);
    onOpenUrl((urls) => handleDeepLinkUrls(urls));
  } catch (e) {
    if (e != null) console.debug("deep-link init", e);
  }
  if (localStorage.getItem(HOTKEYS_ENABLED_KEY) !== "false") await setupGlobalShortcuts();
  const ok = await checkDaemon();
  if (ok) {
    await updateListenState();
    loadSettings();
  }
  loadRecentSessions();
  loadUpcomingEvents();
  loadCostWidget();
  loadLastAnalysisWidget();
  if (localStorage.getItem(UPDATER_CHECK_ON_LAUNCH_KEY) === "true") {
    checkForUpdate(true);
  }
})();

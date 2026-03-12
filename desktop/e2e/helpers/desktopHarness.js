export function buildDesktopScenario(overrides = {}) {
  return {
    language: "ru",
    daemonAvailable: true,
    deepLinks: [],
    updateAvailable: false,
    updateVersion: "0.2.0-alpha.3",
    autostartEnabled: false,
    settingsAsPanel: true,
    sessions: [
      {
        id: 101,
        started_at: "2026-03-08T10:00:00Z",
        duration_sec: 1800,
      },
      {
        id: 102,
        started_at: "2026-03-07T09:30:00Z",
        duration_sec: 1200,
      },
    ],
    sessionIdsWithActionItems: [101],
    sessionDetails: {
      101: {
        segments: [
          { start_sec: 0, end_sec: 4.2, speaker: "SPEAKER_01", text: "Обсудили релиз alpha." },
          { start_sec: 4.2, end_sec: 9.7, speaker: "SPEAKER_02", text: "Нужно подготовить regression tests." },
        ],
        analysis: {
          model: "anthropic/claude-haiku-4-5",
          questions: ["Какие smoke tests блокируют релиз?"],
          answers: ["Сначала гоним desktop e2e и accessibility."],
          recommendations: ["Добавить visual regression на ключевые экраны."],
          action_items: [{ description: "Добавить visual regression", assignee: "QA" }],
          cost_usd: 0.0123,
        },
      },
      102: {
        segments: [{ start_sec: 0, end_sec: 5, speaker: "SPEAKER_01", text: "Проверили desktop build." }],
        analysis: { answers: ["Build green"], action_items: [], recommendations: [], questions: [], cost_usd: 0.0042 },
      },
    },
    analytics: {
      total_cost_usd: 1.2345,
      total_calls: 17,
      by_day: [
        { date: "2026-03-08", cost_usd: 0.42, calls: 5 },
        { date: "2026-03-07", cost_usd: 0.38, calls: 4 },
        { date: "2026-03-06", cost_usd: 0.25, calls: 3 },
      ],
      by_model: [
        { model: "anthropic/claude-haiku-4-5", cost_usd: 0.9, calls: 12 },
        { model: "openai/gpt-4o-mini", cost_usd: 0.3345, calls: 5 },
      ],
    },
    settings: {
      model_size: "small",
      default_llm: "anthropic/claude-haiku-4-5",
      budget_limit_usd: 75,
      smart_trigger: true,
      sample_rate: 16000,
      streaming_stt: true,
      pii_mode: "ON",
      privacy_mode: "ON",
      language: "ru",
    },
    upcomingEvents: [
      { summary: "Sprint Review", start_iso: "2026-03-09T11:00:00Z" },
      { summary: "1:1", start_iso: "2026-03-09T14:30:00Z" },
    ],
    ragHits: [
      { source: "docs/runbooks/desktop-build-deps.md", content: "Tauri build deps and Linux notes", score: 0.91 },
    ],
    transcriptHits: [
      { session_id: 101, snippet: "Нужно подготовить regression tests." },
    ],
    ...overrides,
  };
}

export async function installDesktopMocks(page, scenarioOverrides = {}) {
  const scenario = buildDesktopScenario(scenarioOverrides);

  await page.addInitScript((scenarioData) => {
    const clone = (value) => structuredClone(value);
    const HARNESS_STORE_KEY = "__VOICEFORGE_HARNESS_STORE__";
    const listeners = new Map();
    const scenario = clone(scenarioData);
    const readPersistedStoreData = () => {
      try {
        const raw = globalThis.name || "";
        if (!raw.startsWith(HARNESS_STORE_KEY)) return {};
        const parsed = JSON.parse(raw.slice(HARNESS_STORE_KEY.length));
        return parsed && typeof parsed === "object" ? parsed : {};
      } catch {
        return {};
      }
    };
    const persistedStoreData = readPersistedStoreData();
    const state = {
      autostartEnabled: !!scenario.autostartEnabled,
      clipboard: "",
      daemonAvailable: scenario.daemonAvailable !== false,
      detailRequests: [],
      invokes: [],
      listening: false,
      notifications: [],
      relaunches: 0,
      sessions: clone(scenario.sessions),
      settings: clone(scenario.settings),
      shortcuts: [],
      storeData: {
        voiceforge_settings_as_panel: scenario.settingsAsPanel ? "true" : "false",
        voiceforge_ui_lang: scenario.language || "ru",
        voiceforge_theme: "dark",
        voiceforge_hotkeys_enabled: "true",
        voiceforge_onboarding_dismissed: scenario.onboardingDismissed ? "true" : "false",
        voiceforge_compact_mode: scenario.compactMode ? "true" : "false",
        ...persistedStoreData,
      },
      updateChecks: 0,
      windowState: { x: 40, y: 30, width: 1440, height: 1080 },
    };

    const emit = (eventName, payload) => {
      const callbacks = listeners.get(eventName) || [];
      callbacks.forEach((callback) => callback({ payload }));
    };

    function removeListener(eventName, callback) {
      const current = listeners.get(eventName) || [];
      listeners.set(eventName, current.filter((item) => item !== callback));
    }

    const writeStorage = () => {
      Object.entries(state.storeData).forEach(([key, value]) => {
        if (localStorage.getItem(key) !== null) return;
        localStorage.setItem(key, typeof value === "string" ? value : JSON.stringify(value));
      });
    };

    const persistStoreData = () => {
      try {
        globalThis.name = HARNESS_STORE_KEY + JSON.stringify(state.storeData);
      } catch {}
    };

    writeStorage();
    persistStoreData();

    const originalSetItem = Storage.prototype.setItem;
    const originalRemoveItem = Storage.prototype.removeItem;
    const originalClear = Storage.prototype.clear;
    Storage.prototype.setItem = function patchedSetItem(key, value) {
      originalSetItem.call(this, key, value);
      if (this === localStorage && typeof key === "string" && key.startsWith("voiceforge_")) {
        state.storeData[key] = String(value);
        persistStoreData();
      }
    };
    Storage.prototype.removeItem = function patchedRemoveItem(key) {
      originalRemoveItem.call(this, key);
      if (this === localStorage && typeof key === "string" && key.startsWith("voiceforge_")) {
        delete state.storeData[key];
        persistStoreData();
      }
    };
    Storage.prototype.clear = function patchedClear() {
      originalClear.call(this);
      if (this === localStorage) {
        state.storeData = {};
        persistStoreData();
      }
    };

    const envelope = (data) => JSON.stringify({ ok: true, data });

    const fakeWindow = {
      async innerPosition() {
        return { x: state.windowState.x, y: state.windowState.y };
      },
      async innerSize() {
        return { width: state.windowState.width, height: state.windowState.height };
      },
      async outerPosition() {
        return { x: state.windowState.x, y: state.windowState.y };
      },
      async outerSize() {
        return { width: state.windowState.width, height: state.windowState.height };
      },
      async setPosition(position) {
        state.windowState.x = position?.x ?? state.windowState.x;
        state.windowState.y = position?.y ?? state.windowState.y;
      },
      async setSize(size) {
        state.windowState.width = size?.width ?? state.windowState.width;
        state.windowState.height = size?.height ?? state.windowState.height;
      },
      async scaleFactor() {
        return 1;
      },
      async onMoved(callback) {
        state.onMoved = callback;
      },
      async onResized(callback) {
        state.onResized = callback;
      },
      async onCloseRequested(callback) {
        state.onCloseRequested = callback;
      },
      async show() {},
      async hide() {},
      async setFocus() {},
    };

    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        async writeText(text) {
          state.clipboard = String(text ?? "");
        },
        async readText() {
          return state.clipboard;
        },
      },
    });

    globalThis.alert = (message) => {
      state.lastAlert = String(message ?? "");
    };
    globalThis.confirm = () => true;

    globalThis.__VOICEFORGE_TEST_STATE__ = state;
    globalThis.__VOICEFORGE_TEST_EMIT__ = emit;

    globalThis.__VOICEFORGE_TEST_HOOKS__ = {
      async invoke(cmd, args = {}) {
        state.invokes.push({ cmd, args: clone(args) });
        switch (cmd) {
          case "ping":
            if (!state.daemonAvailable) {
              throw new Error("mock daemon unavailable");
            }
            return "pong";
          case "set_tray_theme":
            return "ok";
          case "is_listening":
            return state.listening;
          case "listen_start":
            state.listening = true;
            emit("listen-state-changed", { is_listening: true });
            emit("transcript-chunk", { text: "Слушаю встречу", is_final: false });
            return "ok";
          case "listen_stop":
            state.listening = false;
            emit("transcript-chunk", { text: "Финальный фрагмент", is_final: true });
            emit("listen-state-changed", { is_listening: false });
            return "ok";
          case "get_streaming_transcript":
            return envelope({
              streaming_transcript: {
                partial: state.listening ? "Слушаю встречу" : "",
                finals: state.listening ? [] : [{ text: "Финальный фрагмент" }],
              },
            });
          case "get_sessions":
            return envelope({ sessions: state.sessions });
          case "get_session_detail": {
            const id = Number(args.sessionId);
            state.detailRequests.push(id);
            return envelope({ session_detail: scenario.sessionDetails[id] || {} });
          }
          case "get_upcoming_calendar_events":
            return envelope({ events: scenario.upcomingEvents });
          case "get_analytics":
            return envelope({ analytics: scenario.analytics });
          case "get_settings":
            return envelope({ settings: state.settings });
          case "get_daemon_version":
            return "0.2.0-alpha.2";
          case "get_session_ids_with_action_items":
            return envelope({ session_ids: scenario.sessionIdsWithActionItems });
          case "search_transcripts":
            return envelope({ hits: scenario.transcriptHits });
          case "search_rag":
            return envelope({ rag_hits: scenario.ragHits });
          case "export_session":
            return `exported:${args.format}:${args.sessionId}`;
          case "create_event_from_session":
            return envelope({ event_uid: "vf-event-101" });
          case "analyze": {
            const newSessionId = 103;
            const analysisText = `Analysis done for ${args.seconds}s`;
            state.sessions = [
              { id: newSessionId, started_at: "2026-03-08T11:00:00Z", duration_sec: Number(args.seconds) || 30 },
              ...state.sessions,
            ];
            scenario.sessionDetails[newSessionId] = {
              segments: [{ start_sec: 0, end_sec: 3.5, speaker: "SPEAKER_01", text: analysisText }],
              analysis: {
                model: "anthropic/claude-haiku-4-5",
                questions: [],
                answers: [analysisText],
                recommendations: ["Regression tests updated"],
                action_items: [{ description: "Review desktop QA report", assignee: "Team" }],
                cost_usd: 0.015,
              },
            };
            emit("streaming-analysis-chunk", { delta: "Шаг 1\n" });
            emit("streaming-analysis-chunk", { delta: "Шаг 2\n" });
            emit("analysis-done", { status: "ok" });
            emit("session-created", { session_id: newSessionId });
            return envelope({ text: analysisText, session_id: newSessionId });
          }
          default:
            return envelope({});
        }
      },
      listen(eventName, callback) {
        const callbacks = listeners.get(eventName) || [];
        callbacks.push(callback);
        listeners.set(eventName, callbacks);
        return Promise.resolve(() => removeListener(eventName, callback));
      },
      getCurrentWindow() {
        return fakeWindow;
      },
      notification: {
        async isPermissionGranted() {
          return true;
        },
        async requestPermission() {
          return "granted";
        },
        sendNotification(payload) {
          state.notifications.push(clone(payload));
        },
      },
      globalShortcut: {
        async register(shortcuts, handler) {
          state.shortcuts = Array.isArray(shortcuts) ? shortcuts.slice() : [];
          state.shortcutHandler = handler;
        },
        async unregister() {
          state.shortcuts = [];
          state.shortcutHandler = null;
        },
      },
      deepLink: {
        async getCurrent() {
          return scenario.deepLinks;
        },
        onOpenUrl(handler) {
          state.deepLinkHandler = handler;
        },
      },
      autostart: {
        async isEnabled() {
          return state.autostartEnabled;
        },
        async enable() {
          state.autostartEnabled = true;
        },
        async disable() {
          state.autostartEnabled = false;
        },
      },
      Store: {
        async load() {
          return {
            async get(key) {
              return state.storeData[key] ?? null;
            },
            async set(key, value) {
              state.storeData[key] = value;
              localStorage.setItem(key, typeof value === "string" ? value : JSON.stringify(value));
            },
          };
        },
      },
      updater: {
        async check() {
          state.updateChecks += 1;
          if (!scenario.updateAvailable) return null;
          return {
            version: scenario.updateVersion || "0.2.0-alpha.3",
            body: "Desktop QA build",
            async downloadAndInstall() {
              state.downloadAndInstallCalled = true;
            },
          };
        },
      },
      process: {
        async relaunch() {
          state.relaunches += 1;
        },
      },
    };
  }, scenario);
}

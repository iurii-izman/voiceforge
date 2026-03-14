import { Chart } from "chart.js/auto";
import {
  AppStore,
  LogicalPosition,
  LogicalSize,
  autostartDisable,
  autostartEnable,
  autostartIsEnabled,
  getCurrent,
  getCurrentWindow,
  invoke,
  isPermissionGranted,
  listen,
  onOpenUrl,
  exit,
  registerShortcut,
  relaunch,
  requestPermission,
  sendNotification,
  unregisterShortcut,
  updaterCheck,
} from "./platform";

let appStore = null;

const UI_LANG_KEY = "voiceforge_ui_lang";

const STORE_KEYS = [
  "voiceforge_theme",
  "voiceforge_hotkeys_enabled",
  "voiceforge_close_to_tray",
  "voiceforge_compact_mode",
  "voiceforge_onboarding_dismissed",
  "voiceforge_dashboard_order",
  "voiceforge_dashboard_collapsed",
  "voiceforge_favorites",
  "voiceforge_shortcut_record",
  "voiceforge_shortcut_analyze",
  "voiceforge_shortcut_copilot",
  "voiceforge_session_tags",
  "voiceforge_sound_on_record",
  "voiceforge_settings_as_panel",
  UI_LANG_KEY,
];

/** Block 97: minimal i18n for UI language (ru/en). */
const I18N = {
  ru: {
    nav: { home: "Главная", sessions: "Сессии", knowledge: "База знаний", costs: "Затраты", settings: "Настройки" },
    tab_home_title: "Главная",
    tab_sessions_title: "Сессии",
    tab_knowledge_title: "База знаний",
    tab_costs_title: "Затраты",
    knowledge_drop_hint: "Перетащите файлы или папки сюда для индексации",
    knowledge_documents: "Документы в индексе",
    knowledge_context_packs: "Контекстные наборы",
    knowledge_packs_hint: "Сохраните текущий индекс как набор и переключайтесь между наборами.",
    knowledge_active_pack: "Активный набор",
    knowledge_pack_pin: "Закрепить",
    knowledge_pack_add: "Сохранить текущий как набор",
    knowledge_empty: "Нет проиндексированных документов.",
    knowledge_stats: "{sources} источников, {chunks} чанков",
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
    widget_last_copilot: "Последний Copilot",
    copilot_no_recent: "Нет недавнего захвата Copilot.",
    copilot_groundedness: "Обоснованность: {value}",
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
    sessions_rag_placeholder: "Поиск по документам (RAG)…",
    rag_hits_title: "Найдено в документах:",
    rag_no_hits: "Ничего не найдено.",
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
    compact_expand: "Полный режим",
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
    detail_add_to_calendar: "Добавить в календарь",
    calendar_event_created: "Событие создано",
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
    close_to_tray_label: "Скрывать в трей при закрытии окна или Alt+F4",
    close_to_tray_hint: "Когда опция включена, крестик и Alt+F4 не завершают приложение, а только скрывают окно.",
    quit_app_btn: "Выйти из VoiceForge",
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
    period_all: "Все",
    period_today: "За сегодня",
    period_week: "За неделю",
    period_month: "За месяц",
    sort_newest: "Сначала новые",
    sort_oldest: "Сначала старые",
    sort_duration_desc: "По длительности (↓)",
    sort_duration_asc: "По длительности (↑)",
    filter_all: "Все",
    filter_favorites: "Только избранные",
    filter_with_actions: "Только с action items",
    status_ready: "Готово.",
    status_analyzing: "Анализ…",
    status_analyzing_60: "Анализ 60 сек…",
    status_daemon_unexpected: "Неожиданный ответ: {value}",
    status_daemon_run_hint: "Запустите демон: voiceforge daemon. {message}",
    recent_sessions_daemon_hint: "Запустите демон.",
    recent_sessions_empty: "Нет сессий. Запустите анализ с блока выше.",
    calendar_empty: "Нет событий на ближайшие 48 ч.",
    calendar_setup: "Настройка CalDAV",
    calendar_load_error: "Не удалось загрузить календарь: {message}",
    calendar_untitled: "(без названия)",
    calendar_more: "и ещё {count}…",
    notify_analysis_done: "Анализ завершён.",
    notify_analysis_error: "Анализ: ошибка.",
    date_group_today: "Сегодня",
    date_group_yesterday: "Вчера",
    date_group_this_week: "На этой неделе",
    date_group_older: "Ранее",
    sessions_empty_filtered: "Нет сессий по заданным фильтрам.",
    sessions_col_favorite: "Избранное",
    sessions_col_start: "Начало",
    sessions_col_duration: "Длительность",
    favorite_add: "В избранное",
    favorite_remove: "Убрать из избранного",
    open_session_aria: "Открыть сессию {id}",
    session_label: "Сессия {id}",
    duration_sec_short: "{seconds} с",
    last_analysis_more_actions: "… ещё {count}",
    last_analysis_qr_summary: "Вопросов: {questions}, рекомендаций: {recommendations}",
    notify_link_copied: "Ссылка скопирована.",
    notify_segment_copied: "Сегмент скопирован.",
    notify_copied_generic: "Скопировано.",
    copy_no_transcript: "Нет транскрипта для копирования.",
    copy_transcript_done: "Транскрипт скопирован.",
    copy_no_actions: "Нет action items для копирования.",
    copy_actions_done: "Action items скопированы.",
    copy_failed: "Не удалось скопировать: {message}",
    empty_daemon_title: "Демон не запущен",
    empty_daemon_hint: "Запустите: voiceforge daemon",
    empty_sessions_title: "Сессий пока нет",
    empty_sessions_hint: "Запустите запись и анализ на главной.",
    detail_transcript: "Транскрипт",
    detail_analysis: "Анализ",
    detail_stats: "Слов: {words}, символов: {chars}",
    detail_model: "Модель: {model}",
    detail_questions: "Вопросы",
    detail_answers: "Ответы / выводы",
    detail_recommendations: "Рекомендации",
    detail_actions: "Действия",
    detail_cost: "Стоимость: ${cost}",
    empty_no_data: "Нет данных.",
    empty_no_analysis: "Нет анализа.",
    export_sessions_empty: "Нет сессий для экспорта.",
    export_costs_empty: "Сначала загрузите отчёт (7 или 30 дней).",
    quickstart_link: "Быстрый старт в репозитории",
    settings_daemon_hint: "Настройки загружаются с демона.",
    settings_none: "Нет настроек.",
    settings_daemon_version: "Версия демона: {version}",
    settings_daemon_version_unavailable: "Версия демона: недоступна",
    analytics_no_data: "Нет данных.",
    analytics_total: "Итого за период:",
    analytics_calls: "{count} вызовов",
    analytics_by_model: "По моделям",
    analytics_by_day: "По дням",
    analytics_col_model: "Модель",
    analytics_col_cost: "Стоимость ($)",
    analytics_col_calls: "Вызовы",
    analytics_col_date: "Дата",
    cost_widget_summary: "${cost} ({calls} вызовов)",
    transcript_nav: "Навигация по сегментам",
    transcript_segment_title: "Сегмент {index}",
    time_range_short: "{start}–{end} с ",
    export_done: "Экспорт: {value}",
    export_done_default: "выполнен",
    chart_cost_label: "Стоимость ($)",
    tag_filter_all: "Все",
    transcript_hits_title: "Найдено по тексту:",
    transcript_no_hits: "Ничего не найдено.",
    export_sessions_confirm: "Экспорт в CSV? (Отмена = JSON)",
    update_available_status: "Доступна версия {version}. Нажмите «Проверить сейчас» для установки.",
    update_found_status: "Найдено обновление {version}…",
    update_confirm: "Доступна версия {version}.\n\n{body}\n\nУстановить сейчас?",
    update_installing: "Установка…",
    update_deferred: "Обновление отложено.",
    update_none: "Обновлений нет.",
    update_unavailable: "Обновления отключены или недоступны.",
    dashboard_expand: "Развернуть",
    dashboard_collapse: "Свернуть",
  },
  en: {
    nav: { home: "Home", sessions: "Sessions", knowledge: "Knowledge", costs: "Costs", settings: "Settings" },
    tab_home_title: "Home",
    tab_sessions_title: "Sessions",
    tab_knowledge_title: "Knowledge",
    tab_costs_title: "Costs",
    knowledge_drop_hint: "Drag files or folders here to index",
    knowledge_documents: "Documents in index",
    knowledge_context_packs: "Context packs",
    knowledge_packs_hint: "Save current index as a pack and switch between packs.",
    knowledge_active_pack: "Active pack",
    knowledge_pack_pin: "Pin",
    knowledge_pack_add: "Save current as pack",
    knowledge_empty: "No indexed documents.",
    knowledge_stats: "{sources} sources, {chunks} chunks",
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
    widget_last_copilot: "Last copilot",
    copilot_no_recent: "No recent copilot capture.",
    copilot_groundedness: "Groundedness: {value}",
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
    sessions_rag_placeholder: "Search documents (RAG)…",
    rag_hits_title: "Found in documents:",
    rag_no_hits: "No results.",
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
    compact_expand: "Full mode",
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
    detail_add_to_calendar: "Add to calendar",
    calendar_event_created: "Event created",
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
    close_to_tray_label: "Hide to tray on window close or Alt+F4",
    close_to_tray_hint: "When enabled, the close button and Alt+F4 hide the window instead of quitting the app.",
    quit_app_btn: "Quit VoiceForge",
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
    period_all: "All",
    period_today: "Today",
    period_week: "This week",
    period_month: "This month",
    sort_newest: "Newest first",
    sort_oldest: "Oldest first",
    sort_duration_desc: "By duration (↓)",
    sort_duration_asc: "By duration (↑)",
    filter_all: "All",
    filter_favorites: "Favorites only",
    filter_with_actions: "With action items only",
    status_ready: "Done.",
    status_analyzing: "Analyzing…",
    status_analyzing_60: "Analyzing 60 sec…",
    status_daemon_unexpected: "Unexpected response: {value}",
    status_daemon_run_hint: "Run the daemon: voiceforge daemon. {message}",
    recent_sessions_daemon_hint: "Start the daemon.",
    recent_sessions_empty: "No sessions yet. Run analysis from the panel above.",
    calendar_empty: "No events in the next 48 h.",
    calendar_setup: "CalDAV setup",
    calendar_load_error: "Failed to load calendar: {message}",
    calendar_untitled: "(untitled)",
    calendar_more: "... {count} more",
    notify_analysis_done: "Analysis completed.",
    notify_analysis_error: "Analysis failed.",
    date_group_today: "Today",
    date_group_yesterday: "Yesterday",
    date_group_this_week: "This week",
    date_group_older: "Earlier",
    sessions_empty_filtered: "No sessions match the selected filters.",
    sessions_col_favorite: "Favorite",
    sessions_col_start: "Started",
    sessions_col_duration: "Duration",
    favorite_add: "Add to favorites",
    favorite_remove: "Remove from favorites",
    open_session_aria: "Open session {id}",
    session_label: "Session {id}",
    duration_sec_short: "{seconds} sec",
    last_analysis_more_actions: "... {count} more",
    last_analysis_qr_summary: "Questions: {questions}, recommendations: {recommendations}",
    notify_link_copied: "Link copied.",
    notify_segment_copied: "Segment copied.",
    notify_copied_generic: "Copied.",
    copy_no_transcript: "No transcript to copy.",
    copy_transcript_done: "Transcript copied.",
    copy_no_actions: "No action items to copy.",
    copy_actions_done: "Action items copied.",
    copy_failed: "Failed to copy: {message}",
    empty_daemon_title: "Daemon is not running",
    empty_daemon_hint: "Run: voiceforge daemon",
    empty_sessions_title: "No sessions yet",
    empty_sessions_hint: "Start recording and analysis on the Home tab.",
    detail_transcript: "Transcript",
    detail_analysis: "Analysis",
    detail_stats: "Words: {words}, characters: {chars}",
    detail_model: "Model: {model}",
    detail_questions: "Questions",
    detail_answers: "Answers / findings",
    detail_recommendations: "Recommendations",
    detail_actions: "Actions",
    detail_cost: "Cost: ${cost}",
    empty_no_data: "No data.",
    empty_no_analysis: "No analysis yet.",
    export_sessions_empty: "No sessions to export.",
    export_costs_empty: "Load a report first (7 or 30 days).",
    quickstart_link: "Quick start in the repository",
    settings_daemon_hint: "Settings are loaded from the daemon.",
    settings_none: "No settings available.",
    settings_daemon_version: "Daemon version: {version}",
    settings_daemon_version_unavailable: "Daemon version: unavailable",
    analytics_no_data: "No data.",
    analytics_total: "Total for period:",
    analytics_calls: "{count} calls",
    analytics_by_model: "By model",
    analytics_by_day: "By day",
    analytics_col_model: "Model",
    analytics_col_cost: "Cost ($)",
    analytics_col_calls: "Calls",
    analytics_col_date: "Date",
    cost_widget_summary: "${cost} ({calls} calls)",
    transcript_nav: "Segment navigation",
    transcript_segment_title: "Segment {index}",
    time_range_short: "{start}–{end} sec ",
    export_done: "Export: {value}",
    export_done_default: "done",
    chart_cost_label: "Cost ($)",
    tag_filter_all: "All",
    transcript_hits_title: "Found in transcript:",
    transcript_no_hits: "Nothing found.",
    export_sessions_confirm: "Export as CSV? (Cancel = JSON)",
    update_available_status: "Version {version} is available. Click “Check now” to install.",
    update_found_status: "Update {version} found…",
    update_confirm: "Version {version} is available.\n\n{body}\n\nInstall now?",
    update_installing: "Installing…",
    update_deferred: "Update deferred.",
    update_none: "No updates available.",
    update_unavailable: "Updates are disabled or unavailable.",
    dashboard_expand: "Expand",
    dashboard_collapse: "Collapse",
  },
};

function t(key) {
  const lang = localStorage.getItem(UI_LANG_KEY) || "ru";
  const map = I18N[lang] || I18N.ru;
  const val = key.split(".").reduce((o, p) => o?.[p], map);
  return val != null && typeof val === "string" ? val : key;
}

function tf(key, vars = {}) {
  return Object.entries(vars).reduce(
    (text, [name, value]) => text.replaceAll(`{${name}}`, String(value ?? "")),
    t(key),
  );
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
    appStore = await AppStore.load("voiceforge-settings.json");
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
  setDaemonDependentControlsEnabled(false);
  const compactStatus = document.getElementById("compact-status");
  if (compactStatus) { compactStatus.textContent = t("compact_daemon_off"); compactStatus.className = "status daemon-off"; }
  const banner = document.getElementById("daemon-off-banner");
  const bannerText = document.getElementById("daemon-off-banner-text");
  if (banner) banner.style.display = "block";
  if (bannerText) bannerText.textContent = msg || t("status_daemon_off");
}

const COPILOT_MODE_LABELS = { cloud: "☁ Cloud", hybrid: "⚡ Hybrid", offline: "🔒 Offline" };

function setDaemonOk() {
  daemonOk = true;
  const statusBar = document.getElementById("status-bar");
  const retryBtn = document.getElementById("retry");
  statusBar.textContent = t("status_daemon_ok");
  statusBar.className = "status daemon-ok";
  invoke("get_settings")
    .then((raw) => {
      const env = parseEnvelope(raw);
      const data = env?.data ?? env?.settings ?? env ?? {};
      const mode = (data.copilot_mode || "hybrid").toLowerCase();
      const label = COPILOT_MODE_LABELS[mode] || mode;
      if (statusBar) statusBar.textContent = t("status_daemon_ok") + " · " + label;
    })
    .catch(() => {});
  retryBtn.style.display = "none";
  const banner = document.getElementById("daemon-off-banner");
  if (banner) banner.style.display = "none";
  setDaemonDependentControlsEnabled(true);
  const compactStatus = document.getElementById("compact-status");
  if (compactStatus) { compactStatus.textContent = t("compact_daemon_ok"); compactStatus.className = "status daemon-ok"; }
}

function setDaemonDependentControlsEnabled(enabled) {
  const selectors = [
    "#listen-toggle",
    "#analyze-btn",
    "#quick-listen",
    "#quick-analyze-60",
    "#compact-listen",
    "#compact-analyze",
  ];
  document.querySelectorAll(selectors.join(", ")).forEach((button) => {
    button.disabled = !enabled;
  });
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

function refreshHomeDashboard() {
  loadRecentSessions();
  loadUpcomingEvents();
  loadCostWidget();
  loadLastAnalysisWidget();
  loadLastCopilotWidget();
}

async function refreshAfterDaemonRecovery() {
  if (!daemonOk) return;
  await updateListenState();
  loadSettings();
  loadSessions();
  refreshHomeDashboard();
}

function refreshAfterAnalysisSuccess() {
  if (!daemonOk) return;
  loadSessions();
  refreshHomeDashboard();
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
      setDaemonOff(tf("status_daemon_unexpected", { value: pong }));
      return false;
    }
    setDaemonOk();
    return true;
  } catch (e) {
    setDaemonOff(tf("status_daemon_run_hint", { message: e?.message || "" }).trim());
    return false;
  }
}

function switchTab(tabId) {
  hideSessionDetail();
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
  if (tabId === "knowledge") loadKnowledgeTab();
  if (tabId === "costs") loadAnalytics("7d");
  if (tabId === "settings") loadSettings();
  if (tabId === "home") {
    refreshHomeDashboard();
  }
}

const SETTINGS_AS_PANEL_KEY = "voiceforge_settings_as_panel";

function openSettingsPanel() {
  const panel = document.getElementById("settings-slide-panel");
  const slot = document.getElementById("settings-panel-slot");
  const tabContent = document.getElementById("settings-tab-content");
  if (!panel || !slot || !tabContent) return;
  panel.hidden = false;
  panel.inert = false;
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
  panel.inert = true;
  panel.hidden = true;
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
  if (daemonOk) await refreshAfterDaemonRecovery();
  document.getElementById("retry").disabled = false;
});
document.getElementById("daemon-retry-btn")?.addEventListener("click", async () => {
  const btn = document.getElementById("daemon-retry-btn");
  if (btn) btn.disabled = true;
  await checkDaemon();
  if (daemonOk) await refreshAfterDaemonRecovery();
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
  if (Array.isArray(sessions) && sessions.length > 0) {
  let html = "<ul class=\"recent-sessions-ul\">";
  sessions.forEach((s) => {
    const id = s.id ?? s.session_id ?? "—";
    const start = s.started_at ?? s.created_at ?? "";
    const dur = s.duration_sec == null ? "" : tf("duration_sec_short", { seconds: s.duration_sec });
    html += `<li><button type="button" class="btn-link" data-session-id="${id}">${escapeHtml(tf("session_label", { id }))}</button> ${start} ${dur}</li>`;
  });
  html += "</ul>";
  return html;
  }
  return null;
}

function loadRecentSessions() {
  const el = document.getElementById("recent-sessions-list");
  if (!el) return;
  if (!daemonOk) {
    el.textContent = t("recent_sessions_daemon_hint");
    return;
  }
  invoke("get_sessions", { limit: 5 })
    .then((raw) => {
      const env = parseEnvelope(raw);
      const sessions = env?.data?.sessions ?? env?.sessions ?? [];
      const html = renderRecentSessionsList(sessions);
      if (html === null) {
        el.innerHTML = `<p>${escapeHtml(t("recent_sessions_empty"))}</p>`;
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
        el.innerHTML = `<p class="muted">${escapeHtml(t("calendar_empty"))}</p><p><a href="${DOCS_CALENDAR}" target="_blank" rel="noopener">${escapeHtml(t("calendar_setup"))}</a></p>`;
        return;
      }
      let html = "<ul class=\"upcoming-events-list\">";
      events.slice(0, 10).forEach((ev) => {
        const summary = escapeHtml(ev.summary ?? t("calendar_untitled"));
        const start = ev.start_iso ?? "";
        const startShort = start.replace(/T.*/, "").replaceAll("-", ".") + (start.includes("T") ? " " + start.split("T")[1].slice(0, 5) : "");
        html += "<li><strong>" + summary + "</strong> <span class=\"muted\">" + startShort + "</span></li>";
      });
      html += "</ul>";
      if (events.length > 10) html += `<p class="muted">${escapeHtml(tf("calendar_more", { count: events.length - 10 }))}</p>`;
      el.innerHTML = html;
    })
    .catch((e) => {
      el.innerHTML = `<p class="muted">${escapeHtml(tf("calendar_load_error", { message: e?.message || e }))}</p><p><a href="${DOCS_CALENDAR}" target="_blank" rel="noopener">${escapeHtml(t("calendar_setup"))}</a></p>`;
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
  if (n > 3) html += "<li class=\"muted\">" + escapeHtml(tf("last_analysis_more_actions", { count: n - 3 })) + "</li>";
  return html + "</ul>";
}

function buildLastAnalysisQrLine(ana) {
  if (!ana) return "";
  const q = Array.isArray(ana.questions) ? ana.questions.length : 0;
  const r = Array.isArray(ana.recommendations) ? ana.recommendations.length : 0;
  return (q || r) ? `<p class="muted">${escapeHtml(tf("last_analysis_qr_summary", { questions: q, recommendations: r }))}</p>` : "";
}

function buildLastAnalysisSummaryHtml(sessionId, session, detail) {
  const ana = detail?.analysis || null;
  const started = session?.started_at ?? session?.created_at ?? "";
  const startShort = formatStartedShort(started);
  let html = `<p class="muted">${escapeHtml(tf("session_label", { id: String(sessionId) }))}${startShort ? " · " + escapeHtml(startShort) : ""}</p>`;
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

function loadLastCopilotWidget() {
  const el = document.getElementById("last-copilot-content");
  if (!el) return;
  if (!daemonOk) {
    el.textContent = t("copilot_no_recent");
    return;
  }
  el.textContent = t("loading");
  invoke("get_copilot_capture_status")
    .then((raw) => {
      const env = parseEnvelope(raw);
      const data = env?.data ?? env ?? (typeof raw === "string" ? (() => { try { return JSON.parse(raw); } catch { return {}; } })() : raw) ?? {};
      const snippet = data.transcript_snippet && String(data.transcript_snippet).trim();
      const groundedness = data.rag_groundedness != null ? String(data.rag_groundedness) : null;
      if (!snippet && !groundedness) {
        el.textContent = t("copilot_no_recent");
        return;
      }
      let html = "";
      if (snippet) {
        const truncated = snippet.length > 200 ? snippet.slice(0, 197) + "…" : snippet;
        html += "<p class=\"copilot-snippet\">" + escapeHtml(truncated) + "</p>";
      }
      if (groundedness) {
        html += "<p class=\"copilot-groundedness\"><span class=\"badge badge--groundedness\">" + escapeHtml(tf("copilot_groundedness", { value: groundedness })) + "</span></p>";
      }
      el.innerHTML = html || t("copilot_no_recent");
    })
    .catch(() => {
      el.textContent = t("copilot_no_recent");
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
  el.textContent = tf("cost_widget_summary", { cost: Number(total).toFixed(4), calls });
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
  if (statusEl) statusEl.textContent = t("status_analyzing_60");
  try {
    const raw = await invoke("analyze", { seconds: 60, template });
    const env = parseEnvelope(raw);
    if (env?.ok && env?.data?.text) {
      if (statusEl) statusEl.textContent = t("status_ready");
      refreshAfterAnalysisSuccess();
      notify("VoiceForge", t("notify_analysis_done"));
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
  if (statusEl) statusEl.textContent = t("status_analyzing");
  try {
    const raw = await invoke("analyze", { seconds: 30, template: null });
    const env = parseEnvelope(raw);
    if (env?.ok && env?.data?.text) {
      if (statusEl) statusEl.textContent = t("status_ready");
      refreshAfterAnalysisSuccess();
      notify("VoiceForge", t("notify_analysis_done"));
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
  const shortcutCopilot = getCopilotShortcut();
  currentShortcuts = [shortcutRecord, shortcutAnalyze, shortcutCopilot].filter(Boolean);
  if (currentShortcuts.length === 0) return;
  try {
    await registerShortcut(currentShortcuts, (event) => {
      // KC2/KC3: copilot overlay — CaptureStart/CaptureRelease + overlay state; 30s auto-stop emits recording_warning.
      if (event.shortcut === shortcutCopilot) {
        if (event.state === "Pressed") {
          invoke("capture_start").catch(() => {});
          invoke("set_copilot_overlay_state", { state: "recording", show: true }).catch(() => {});
        } else if (event.state === "Released") {
          invoke("capture_release").catch(() => {});
          invoke("set_copilot_overlay_state", { state: "analyzing", show: true }).catch(() => {});
        }
        return;
      }
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
    if (status === "ok") msg = t("status_ready");
    else if (status === "error") msg = t("error_status");
    else msg = String(status ?? "");
    statusEl.textContent = msg;
  }
  document.getElementById("analyze-btn").disabled = false;
  const outEl = document.getElementById("analyze-streaming-output");
  if (outEl?.dataset?.streamEnd === "1") outEl.dataset.streamEnd = "";
  if (status === "ok") {
    refreshAfterAnalysisSuccess();
    notify("VoiceForge", t("notify_analysis_done"));
  } else if (status === "error") {
    if (daemonOk) loadSessions();
    notify("VoiceForge", t("notify_analysis_error"));
  }
});
// KC3: daemon emits CaptureStateChanged (e.g. recording_warning at 25s); forward to overlay
listen("capture-state-changed", (e) => {
  const state = e.payload?.state;
  if (state) invoke("set_copilot_overlay_state", { state, show: true }).catch(() => {});
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
    refreshAfterAnalysisSuccess();
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

const TAB_IDS = ["home", "sessions", "knowledge", "costs", "settings"];
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
  statusEl.textContent = t("status_analyzing");
  try {
    const raw = await invoke("analyze", { seconds, template });
    const env = parseEnvelope(raw);
    if (env?.ok && env?.data?.text) {
      statusEl.textContent = t("status_ready");
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

const DATE_GROUP_LABELS = {
  today: () => t("date_group_today"),
  yesterday: () => t("date_group_yesterday"),
  this_week: () => t("date_group_this_week"),
  older: () => t("date_group_older"),
};
const DATE_GROUP_ORDER = ["today", "yesterday", "this_week", "older"];

function renderSessionsTable(sessions) {
  const container = document.getElementById("sessions-list");
  if (!container) return;
  if (!sessions.length) {
    container.innerHTML = `<div class="empty-state"><p class="muted">${escapeHtml(t("sessions_empty_filtered"))}</p></div>`;
    return;
  }
  const fav = getFavorites();
  const groups = {};
  DATE_GROUP_ORDER.forEach((k) => { groups[k] = []; });
  sessions.forEach((s) => {
    const key = getDateGroupKey(parseSessionDate(s.started_at ?? s.created_at));
    if (groups[key]) groups[key].push(s);
  });
  let html = `<table><thead><tr><th aria-label="${escapeHtml(t("sessions_col_favorite"))}"></th><th>ID</th><th>${escapeHtml(t("sessions_col_start"))}</th><th>${escapeHtml(t("sessions_col_duration"))}</th></tr></thead><tbody>`;
  DATE_GROUP_ORDER.forEach((key) => {
    const list = groups[key] || [];
    if (list.length === 0) return;
    html += "<tr class=\"session-group-header\"><td colspan=\"4\">" + escapeHtml(DATE_GROUP_LABELS[key]()) + "</td></tr>";
    list.forEach((s) => {
      const id = s.id ?? s.session_id ?? "—";
      const start = s.started_at ?? s.created_at ?? "—";
      const dur = s.duration_sec == null ? "—" : tf("duration_sec_short", { seconds: s.duration_sec });
      const isFav = fav.has(Number(id));
      const star = `<button type="button" class="favorite-star" data-id="${id}" aria-label="${escapeHtml(isFav ? t("favorite_remove") : t("favorite_add"))}">${isFav ? "★" : "☆"}</button>`;
      const openBtn = `<button type="button" class="btn-link session-open-link" data-id="${id}" aria-label="${escapeHtml(tf("open_session_aria", { id }))}">${id}</button>`;
      html += `<tr data-id="${id}"><td>${star}</td><td>${openBtn}</td><td>${start}</td><td>${dur}</td></tr>`;
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
  container.querySelectorAll(".session-open-link").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      showSessionDetail(Number.parseInt(btn.dataset.id, 10));
    });
  });
  container.querySelectorAll("tr[data-id]").forEach((row) => {
    const openDetail = () => showSessionDetail(Number.parseInt(row.dataset.id, 10));
    row.addEventListener("click", (e) => {
      if (e.target.closest(".favorite-star, .session-open-link")) return;
      openDetail();
    });
    row.addEventListener("contextmenu", (e) => {
      if (e.target.closest(".favorite-star, .session-open-link")) return;
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
  if (favBtn) favBtn.textContent = getFavorites().has(sessionId) ? t("favorite_remove") : t("favorite_add");
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
      navigator.clipboard.writeText(url).then(() => notify("VoiceForge", t("notify_link_copied"))).catch(() => {});
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
    container.innerHTML = emptyStateHtml("⚠️", t("empty_daemon_title"), t("empty_daemon_hint"), DOCS_QUICKSTART);
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
        container.innerHTML = emptyStateHtml("📋", t("empty_sessions_title"), t("empty_sessions_hint"), DOCS_QUICKSTART);
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
  let html = `<div class="detail-section"><h4>${escapeHtml(t("detail_transcript"))}</h4><p class="muted detail-stats">${escapeHtml(tf("detail_stats", { words: totalWords, chars: totalChars }))}</p>`;
  html += `<div class="detail-segment-minimap" role="navigation" aria-label="${escapeHtml(t("transcript_nav"))}">`;
  segs.forEach((s, idx) => {
    const t = s.start_sec == null ? String(idx + 1) : Math.floor(Number(s.start_sec) / 60) + ":" + String(Math.floor(Number(s.start_sec) % 60)).padStart(2, "0");
    html += `<button type="button" class="minimap-segment-btn" data-segment-idx="${idx}" title="${escapeHtml(tf("transcript_segment_title", { index: idx + 1 }))}">${escapeHtml(t)}</button>`;
  });
  html += "</div><ul class=\"segment-list\">";
  segs.forEach((s, idx) => {
    const speaker = s.speaker ? `[${s.speaker}] ` : "";
    const time = (s.start_sec != null && s.end_sec != null) ? tf("time_range_short", { start: Number(s.start_sec).toFixed(1), end: Number(s.end_sec).toFixed(1) }) : "";
    const textHtml = highlightQuery ? highlightSegmentText(s.text || "", highlightQuery) : escapeHtml(s.text || "");
    html += `<li id="segment-${idx}" data-segment-index="${idx}"><span class="segment-meta">${time}${speaker}</span>${textHtml} <button type="button" class="btn small segment-copy" aria-label="${t("segment_copy")}">${t("segment_copy")}</button></li>`;
  });
  html += "</ul></div>";
  return html;
}

function renderSessionDetailAnalysis(ana) {
  let html = `<div class="detail-section"><h4>${escapeHtml(t("detail_analysis"))}</h4>`;
  if (ana.model) html += `<p class="muted">${escapeHtml(tf("detail_model", { model: ana.model }))}</p>`;
  if (ana.questions?.length) {
    html += `<p><strong>${escapeHtml(t("detail_questions"))}</strong></p><ul>`;
    ana.questions.forEach((q) => { html += "<li>" + escapeHtml(String(q)) + "</li>"; });
    html += "</ul>";
  }
  if (ana.answers?.length) {
    html += `<p><strong>${escapeHtml(t("detail_answers"))}</strong></p><ul>`;
    ana.answers.forEach((a) => { html += "<li>" + escapeHtml(String(a)) + "</li>"; });
    html += "</ul>";
  }
  if (ana.recommendations?.length) {
    html += `<p><strong>${escapeHtml(t("detail_recommendations"))}</strong></p><ul>`;
    ana.recommendations.forEach((r) => { html += "<li>" + escapeHtml(String(r)) + "</li>"; });
    html += "</ul>";
  }
  if (ana.action_items?.length) {
    html += `<p><strong>${escapeHtml(t("detail_actions"))}</strong></p><ul>`;
    ana.action_items.forEach((ai) => {
      const d = typeof ai === "object" ? (ai.description || "") : String(ai);
      const who = typeof ai === "object" ? ai.assignee : "";
      html += "<li>" + escapeHtml(d) + (who ? " <span class=\"muted\">(" + escapeHtml(who) + ")</span>" : "") + "</li>";
    });
    html += "</ul>";
  }
  if (ana.cost_usd != null) html += `<p class="muted">${escapeHtml(tf("detail_cost", { cost: Number(ana.cost_usd).toFixed(4) }))}</p>`;
  html += "</div>";
  return html;
}

function renderSessionDetail(detail, highlightQuery) {
  if (!detail || (typeof detail === "object" && !detail.segments && !detail.analysis)) {
    return `<p class="muted">${escapeHtml(t("empty_no_data"))}</p>`;
  }
  const segs = Array.isArray(detail.segments) ? detail.segments : [];
  const ana = detail.analysis || null;
  let html = "";
  if (segs.length > 0) html += renderSessionDetailTranscript(segs, highlightQuery);
  const hasAnalysis = ana && (ana.questions?.length || ana.answers?.length || ana.recommendations?.length || ana.action_items?.length);
  if (hasAnalysis) html += renderSessionDetailAnalysis(ana);
  return html || `<p class="muted">${escapeHtml(t("empty_no_analysis"))}</p>`;
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
          notify("VoiceForge", t("notify_segment_copied"));
        }).catch(() => {});
      }
    });
  });
}

function bindMinimapSegmentButtons(container) {
  container.querySelectorAll(".minimap-segment-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const idx = btn.dataset.segmentIdx;
      const el = idx == null ? null : document.getElementById("segment-" + idx);
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
      const time = (s.start_sec != null && s.end_sec != null)
        ? tf("time_range_short", { start: Number(s.start_sec).toFixed(1), end: Number(s.end_sec).toFixed(1) })
        : "";
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
    notify("VoiceForge", t("copy_no_transcript"));
    return;
  }
  try {
    await navigator.clipboard.writeText(text);
    pushClipboardHistory(text);
    notify("VoiceForge", t("copy_transcript_done"));
  } catch (e) {
    notify("VoiceForge", tf("copy_failed", { message: e?.message || e }));
  }
}

async function copyActionItemsToClipboard() {
  if (!lastSessionDetail) return;
  const text = actionItemsToText(lastSessionDetail);
  if (!text) {
    notify("VoiceForge", t("copy_no_actions"));
    return;
  }
  try {
    await navigator.clipboard.writeText(text);
    pushClipboardHistory(text);
    notify("VoiceForge", t("copy_actions_done"));
  } catch (e) {
    notify("VoiceForge", tf("copy_failed", { message: e?.message || e }));
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
  if (detailBlock.show) detailBlock.show();
  else detailBlock.setAttribute("open", "true");
  bodyEl.innerHTML = "<p class=\"muted\">" + t("loading") + "</p>";
  document.getElementById("export-md").onclick = () => exportSession(id, "md");
  document.getElementById("export-pdf").onclick = () => exportSession(id, "pdf");
  document.getElementById("export-docx").onclick = () => exportSession(id, "docx");
  document.getElementById("export-notion").onclick = () => exportSession(id, "notion");
  document.getElementById("export-otter").onclick = () => exportSession(id, "otter");
  document.getElementById("copy-transcript").onclick = copyTranscriptToClipboard;
  document.getElementById("copy-action-items").onclick = copyActionItemsToClipboard;
  document.getElementById("session-detail-print").onclick = () => globalThis.print();
  document.getElementById("add-to-calendar").onclick = () => addSessionToCalendar(id);
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
    alert(tf("export_done", { value: out || t("export_done_default") }));
  } catch (e) {
    alert(t("export_error_prefix") + (e?.message || e));
  }
}

/** Block 79 / #95: create CalDAV event from session; show notification or error. */
async function addSessionToCalendar(sessionId) {
  try {
    const raw = await invoke("create_event_from_session", {
      sessionId: Number(sessionId),
      calendarUrl: null,
    });
    const env = parseEnvelope(raw);
    if (env?.ok && env?.data?.event_uid) {
      const uid = env.data.event_uid;
      if (await isPermissionGranted()) {
        sendNotification({
          title: t("detail_add_to_calendar"),
          body: uid ? `${t("calendar_event_created")} (${uid})` : t("calendar_event_created"),
        });
      } else {
        alert(uid ? `${t("calendar_event_created")}: ${uid}` : t("calendar_event_created"));
      }
    } else {
      const msg = errorMessage(env) || raw || t("error_generic");
      alert(t("error_prefix") + msg);
    }
  } catch (e) {
    alert(t("error_prefix") + (e?.message || e));
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
        datasets: [{ label: t("chart_cost_label"), data: byDay.map((r) => r.cost_usd ?? r.cost ?? 0), backgroundColor: colors.accent }],
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
  if (!data || typeof data !== "object") return `<p class="muted">${escapeHtml(t("analytics_no_data"))}</p>`;
  const total = data.total_cost_usd ?? 0;
  const calls = data.total_calls ?? 0;
  const byModel = data.by_model ?? [];
  const byDay = data.by_day ?? [];
  let html = `<div class="analytics-summary"><p><strong>${escapeHtml(t("analytics_total"))}</strong> $${Number(total).toFixed(4)} <span class="muted">(${escapeHtml(tf("analytics_calls", { count: calls }))})</span></p></div>`;
  if (byModel.length > 0) {
    html += `<div class="detail-section"><h4>${escapeHtml(t("analytics_by_model"))}</h4><table><thead><tr><th>${escapeHtml(t("analytics_col_model"))}</th><th>${escapeHtml(t("analytics_col_cost"))}</th><th>${escapeHtml(t("analytics_col_calls"))}</th></tr></thead><tbody>`;
    byModel.forEach((r) => {
      const cost = (r.cost_usd ?? r.cost ?? 0);
      const n = r.calls ?? r.count ?? "—";
      html += "<tr><td>" + escapeHtml(r.model ?? "—") + "</td><td>" + Number(cost).toFixed(4) + "</td><td>" + n + "</td></tr>";
    });
    html += "</tbody></table></div>";
  }
  if (byDay.length > 0) {
    const slice = byDay.slice(-14).reverse();
    html += `<div class="detail-section"><h4>${escapeHtml(t("analytics_by_day"))}</h4><table><thead><tr><th>${escapeHtml(t("analytics_col_date"))}</th><th>${escapeHtml(t("analytics_col_cost"))}</th><th>${escapeHtml(t("analytics_col_calls"))}</th></tr></thead><tbody>`;
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
    container.innerHTML = emptyStateHtml("⚠️", t("empty_daemon_title"), t("empty_daemon_hint"), DOCS_QUICKSTART);
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
  ru: {
    model_size: "Размер модели (diarization)",
    default_llm: "LLM по умолчанию",
    budget_limit_usd: "Лимит бюджета (USD)",
    smart_trigger: "Умный триггер",
    sample_rate: "Частота дискретизации",
    streaming_stt: "Стриминг STT",
    pii_mode: "Режим PII",
    privacy_mode: "Режим конфиденциальности",
    language: "Язык распознавания (STT)",
    copilot_mode: "Режим Copilot",
    copilot_max_visible_cards: "Макс. карточек в overlay",
    copilot_stt_model_size: "STT для Copilot",
    copilot_pre_roll_seconds: "Pre-roll (сек)",
    copilot_max_capture_seconds: "Макс. длина захвата (сек)",
  },
  en: {
    model_size: "Model size (diarization)",
    default_llm: "Default LLM",
    budget_limit_usd: "Budget limit (USD)",
    smart_trigger: "Smart trigger",
    sample_rate: "Sample rate",
    streaming_stt: "Streaming STT",
    pii_mode: "PII mode",
    privacy_mode: "Privacy mode",
    language: "Recognition language (STT)",
    copilot_mode: "Copilot mode",
    copilot_max_visible_cards: "Max visible cards (overlay)",
    copilot_stt_model_size: "Copilot STT model",
    copilot_pre_roll_seconds: "Pre-roll (sec)",
    copilot_max_capture_seconds: "Max capture length (sec)",
  },
};

function renderSettings(data) {
  if (!data || typeof data !== "object") return `<p class="muted">${escapeHtml(t("empty_no_data"))}</p>`;
  const labels = SETTINGS_LABELS[localStorage.getItem(UI_LANG_KEY) || "ru"] || SETTINGS_LABELS.ru;
  const keys = Object.keys(labels).filter((k) => Object.hasOwn(data, k));
  if (keys.length === 0) {
    return `<p class="muted">${escapeHtml(t("settings_none"))}</p>`;
  }
  let html = "";
  keys.forEach((key) => {
    const label = labels[key] || key;
    let val = data[key];
    if (typeof val === "number" && key === "budget_limit_usd") val = "$" + Number(val).toFixed(2);
    else if (typeof val === "object") val = JSON.stringify(val);
    else val = String(val ?? "—");
    html += "<div class=\"settings-item\"><span class=\"settings-key\">" + escapeHtml(label) + "</span><span class=\"settings-val\">" + escapeHtml(val) + "</span></div>";
  });
  return html;
}

const KNOWLEDGE_PACKS_KEY = "voiceforge_context_packs";
const KNOWLEDGE_PINNED_KEY = "voiceforge_pinned_pack_id";

function loadKnowledgeTab() {
  const statsEl = document.getElementById("knowledge-stats");
  const listEl = document.getElementById("knowledge-document-list");
  if (!statsEl || !listEl) return;
  if (!daemonOk) {
    statsEl.textContent = t("empty_daemon_title");
    listEl.innerHTML = "";
    return;
  }
  statsEl.textContent = t("loading");
  listEl.innerHTML = "";
  Promise.all([invoke("get_indexed_paths"), invoke("get_rag_stats")])
    .then(([pathsRaw, statsRaw]) => {
      const pathsEnv = parseEnvelope(pathsRaw);
      let paths = pathsEnv?.data?.indexed_paths ?? pathsEnv?.indexed_paths ?? (typeof pathsRaw === "string" ? (() => { try { const p = JSON.parse(pathsRaw); return Array.isArray(p) ? p : []; } catch { return []; } })() : []) ?? [];
      if (typeof paths === "string") try { paths = JSON.parse(paths); } catch { paths = []; }
      const pathsList = Array.isArray(paths) ? paths : [];
      const statsEnv = parseEnvelope(statsRaw);
      let stats = statsEnv?.data?.rag_stats ?? statsEnv?.rag_stats ?? {};
      if (typeof stats === "string") try { stats = JSON.parse(stats); } catch { stats = {}; }
      const sources = stats.indexed_sources_count ?? 0;
      const chunks = stats.chunks_count ?? 0;
      statsEl.textContent = tf("knowledge_stats", { sources, chunks });
      if (pathsList.length === 0) {
        listEl.innerHTML = "<li class=\"muted\">" + escapeHtml(t("knowledge_empty")) + "</li>";
      } else {
        listEl.innerHTML = pathsList.map((p) => "<li>" + escapeHtml(String(p)) + "</li>").join("");
      }
      renderKnowledgePacks(pathsList);
    })
    .catch(() => {
      statsEl.textContent = t("error_prefix") + " —";
      listEl.innerHTML = "<li class=\"muted\">" + escapeHtml(t("knowledge_empty")) + "</li>";
    });
}

function renderKnowledgePacks(currentPaths) {
  const packs = JSON.parse(localStorage.getItem(KNOWLEDGE_PACKS_KEY) || "[]");
  const pinnedId = localStorage.getItem(KNOWLEDGE_PINNED_KEY) || "";
  const selectEl = document.getElementById("knowledge-pack-select");
  const listEl = document.getElementById("knowledge-pack-list");
  if (!selectEl || !listEl) return;
  selectEl.innerHTML = "<option value=\"\">—</option>" + packs.map((pack) => `<option value="${escapeHtml(pack.id)}" ${pack.id === pinnedId ? " selected" : ""}>${escapeHtml(pack.name)}</option>`).join("");
  listEl.innerHTML = packs.map((pack) => `<li data-pack-id="${escapeHtml(pack.id)}">${escapeHtml(pack.name)} (${(pack.paths || []).length} paths)</li>`).join("");
}

function initKnowledgeTab() {
  const dropZone = document.getElementById("knowledge-drop-zone");
  const packAdd = document.getElementById("knowledge-pack-add");
  const packPin = document.getElementById("knowledge-pack-pin");
  const packSelect = document.getElementById("knowledge-pack-select");
  if (dropZone) {
    dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("drag-over"); });
    dropZone.addEventListener("dragleave", () => { dropZone.classList.remove("drag-over"); });
    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.classList.remove("drag-over");
      const files = e.dataTransfer?.files;
      if (!files || files.length === 0) return;
      const paths = [];
      for (let i = 0; i < files.length; i++) {
        const f = files[i];
        const path = f.path ?? f.webkitRelativePath ?? (f.filePath !== undefined ? f.filePath : null);
        if (path) paths.push(path);
      }
      if (paths.length === 0) return;
      invoke("index_paths", { paths_json: JSON.stringify(paths) })
        .then(() => loadKnowledgeTab())
        .catch(() => loadKnowledgeTab());
    });
  }
  if (packAdd) {
    packAdd.addEventListener("click", () => {
      invoke("get_indexed_paths")
        .then((raw) => {
          const env = parseEnvelope(raw);
          const paths = env?.data?.indexed_paths ?? env?.indexed_paths ?? (typeof raw === "string" ? (() => { try { const p = JSON.parse(raw); return Array.isArray(p) ? p : []; } catch { return []; } })() : []) ?? [];
          const name = prompt(t("knowledge_active_pack") + " — name", "Pack " + (JSON.parse(localStorage.getItem(KNOWLEDGE_PACKS_KEY) || "[]").length + 1));
          if (!name || !name.trim()) return;
          const packs = JSON.parse(localStorage.getItem(KNOWLEDGE_PACKS_KEY) || "[]");
          packs.push({ id: "pack-" + Date.now(), name: name.trim(), paths: Array.isArray(paths) ? paths : [] });
          localStorage.setItem(KNOWLEDGE_PACKS_KEY, JSON.stringify(packs));
          renderKnowledgePacks(paths);
        });
    });
  }
  if (packPin) {
    packPin.addEventListener("click", () => {
      const id = packSelect?.value || "";
      if (id) localStorage.setItem(KNOWLEDGE_PINNED_KEY, id);
    });
  }
}

function loadSettings() {
  const container = document.getElementById("settings-content");
  if (!daemonOk) {
    container.innerHTML = emptyStateHtml("⚠️", t("empty_daemon_title"), t("settings_daemon_hint"), DOCS_QUICKSTART);
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
      container.innerHTML = renderSettings(data) + `<p class="muted settings-hint" id="daemon-version-line">${escapeHtml(tf("settings_daemon_version", { version: "…" }))}</p>`;
      invoke("get_daemon_version")
        .then((v) => {
          const el = document.getElementById("daemon-version-line");
          if (el) el.textContent = tf("settings_daemon_version", { version: v || "—" });
        })
        .catch(() => {
          const el = document.getElementById("daemon-version-line");
          if (el) el.textContent = t("settings_daemon_version_unavailable");
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
const DASHBOARD_WIDGET_IDS = ["record", "analyze", "streaming", "recent-sessions", "last-analysis", "last-copilot", "upcoming-events", "cost-widget"];
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
  sel.innerHTML = `<option value="all">${escapeHtml(t("tag_filter_all"))}</option>` + allTags.map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join("");
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
          notify("VoiceForge", t("notify_copied_generic"));
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
/** KC2: push-to-capture overlay (Pressed = recording, Released = analyzing). */
const SHORTCUT_COPILOT_DEFAULT = "CommandOrControl+Shift+Space";

function getShortcuts() {
  const r = localStorage.getItem("voiceforge_shortcut_record") || SHORTCUT_RECORD_DEFAULT;
  const a = localStorage.getItem("voiceforge_shortcut_analyze") || SHORTCUT_ANALYZE_DEFAULT;
  return [r.trim() || SHORTCUT_RECORD_DEFAULT, a.trim() || SHORTCUT_ANALYZE_DEFAULT];
}

function getCopilotShortcut() {
  const c = localStorage.getItem("voiceforge_shortcut_copilot") || SHORTCUT_COPILOT_DEFAULT;
  return (c && c.trim()) ? c.trim() : SHORTCUT_COPILOT_DEFAULT;
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

async function quitApplication() {
  try {
    await exit(0);
  } catch (e) {
    console.debug("quitApplication", e);
    try {
      const win = getCurrentWindow();
      if (typeof win.destroy === "function") {
        await win.destroy();
        return;
      }
    } catch (inner) {
      console.debug("quitApplication destroy", inner);
    }
  }
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
  const link = linkHref ? `<p><a href="${escapeHtml(linkHref)}" target="_blank" rel="noopener">${escapeHtml(t("quickstart_link"))}</a></p>` : "";
  return `<div class="empty-state"><div class="empty-state-icon" aria-hidden="true">${icon}</div><p><strong>${escapeHtml(title)}</strong></p><p>${escapeHtml(hint)}</p>${link}</div>`;
}

function closeOnboardingOverlay(overlay) {
  if (!overlay) return;
  if (overlay.close) overlay.close();
  overlay.removeAttribute("open");
  overlay.hidden = true;
  overlay.style.display = "none";
}

function showOnboarding() {
  const overlay = document.getElementById("onboarding-overlay");
  if (localStorage.getItem(ONBOARDING_DISMISSED_KEY) === "true" || !overlay) return;
  const neverAgain = document.getElementById("onboarding-never");
  if (neverAgain) neverAgain.checked = false;
  overlay.hidden = false;
  overlay.style.display = "flex";
  if (!overlay.open && overlay.showModal) overlay.showModal();
  if (!overlay.open) overlay.setAttribute("open", "true");
  document.getElementById("onboarding-ok").onclick = () => {
    if (neverAgain?.checked) setStored(ONBOARDING_DISMISSED_KEY, "true");
    closeOnboardingOverlay(overlay);
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
    alert(t("export_sessions_empty"));
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
    alert(t("export_costs_empty"));
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
  document.getElementById("sessions-rag-results")?.style.setProperty("display", "none");
  try {
    const raw = await invoke("search_transcripts", { query: q, limit: 25 });
    const env = parseEnvelope(raw);
    const hits = env?.data?.hits ?? env?.hits ?? [];
    if (!Array.isArray(hits) || hits.length === 0) {
      if (resultsEl) {
        resultsEl.innerHTML = `<p class="muted">${escapeHtml(t("transcript_no_hits"))}</p>`;
        resultsEl.style.display = "block";
      }
      if (listEl) listEl.style.display = "none";
      return;
    }
    let html = `<p class="muted">${escapeHtml(t("transcript_hits_title"))}</p><ul class="fts-hits-list">`;
    hits.forEach((h) => {
      const sid = h.session_id ?? "—";
      const snip = escapeHtml((h.snippet ?? h.text ?? "").trim() || "—");
      html += `<li><button type="button" class="btn-link fts-hit" data-session-id="${sid}">${escapeHtml(tf("session_label", { id: sid }))}</button>: ${snip}</li>`;
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

function buildRagHitsHtml(hits) {
  const parts = ["<p class=\"muted\">", t("rag_hits_title"), "</p><ul class=\"rag-hits-list\">"];
  hits.forEach((h) => {
    const src = escapeHtml((h.source ?? "").trim() || "—");
    const content = escapeHtml((h.content ?? "").trim().slice(0, 200) || "—");
    const score = h.score == null ? "" : escapeHtml(String(h.score));
    const scoreSpan = score ? " <span class=\"muted\">(" + score + ")</span>" : "";
    parts.push("<li class=\"rag-hit\"><span class=\"rag-hit-source\">", src, "</span>", scoreSpan, "<br><span class=\"rag-hit-content\">", content, "</span></li>");
  });
  parts.push("</ul>");
  return parts.join("");
}

function applyRagSearchResult(resultsEl, ftsResultsEl, listEl, innerHtml) {
  if (resultsEl) {
    resultsEl.innerHTML = innerHtml;
    resultsEl.style.display = "block";
  }
  if (ftsResultsEl) ftsResultsEl.style.display = "none";
  if (listEl) listEl.style.display = "none";
}

async function handleRagSearch(q, listEl, ftsResultsEl, resultsEl) {
  if (!daemonOk) return;
  try {
    const raw = await invoke("search_rag", { query: q, limit: 15 });
    const env = parseEnvelope(raw);
    const hits = env?.data?.rag_hits ?? env?.rag_hits ?? [];
    if (Array.isArray(hits) && hits.length > 0) {
      applyRagSearchResult(resultsEl, ftsResultsEl, listEl, buildRagHitsHtml(hits));
    } else {
      applyRagSearchResult(resultsEl, ftsResultsEl, listEl, "<p class=\"muted\">" + t("rag_no_hits") + "</p>");
    }
  } catch (e) {
    applyRagSearchResult(
      resultsEl,
      ftsResultsEl,
      listEl,
      "<p class=\"muted\">" + t("error_prefix") + escapeHtml(e?.message || e) + "</p>",
    );
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
    const ragResultsEl = document.getElementById("sessions-rag-results");
    if (!q) {
      if (resultsEl) resultsEl.style.display = "none";
      if (ragResultsEl) ragResultsEl.style.display = "none";
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
  let ragSearchTimeout = null;
  document.getElementById("sessions-rag-search")?.addEventListener("input", () => {
    const input = document.getElementById("sessions-rag-search");
    const q = (input?.value ?? "").trim();
    const listEl = document.getElementById("sessions-list");
    const ftsResultsEl = document.getElementById("sessions-fts-results");
    const resultsEl = document.getElementById("sessions-rag-results");
    if (!q) {
      if (resultsEl) resultsEl.style.display = "none";
      if (listEl) listEl.style.display = "";
      applySessionsFilter();
      return;
    }
    if (ragSearchTimeout) clearTimeout(ragSearchTimeout);
    ragSearchTimeout = setTimeout(() => {
      ragSearchTimeout = null;
      void handleRagSearch(q, listEl, ftsResultsEl, resultsEl);
    }, 350);
  });
  document.getElementById("sessions-export-btn")?.addEventListener("click", () => {
    const format = confirm(t("export_sessions_confirm")) ? "csv" : "json";
    exportSessionsList(format);
  });
}

function setUpdateStatus(text) {
  const statusEl = document.getElementById("updater-status");
  if (statusEl) statusEl.textContent = text;
}

async function handleUpdateFound(update, silentIfNone) {
  if (silentIfNone) {
    setUpdateStatus(tf("update_available_status", { version: update.version }));
    return;
  }
  setUpdateStatus(tf("update_found_status", { version: update.version }));
  const install = confirm(tf("update_confirm", { version: update.version, body: update.body || "" }));
  if (install) {
    setUpdateStatus(t("update_installing"));
    await update.downloadAndInstall();
    await relaunch();
  } else {
    setUpdateStatus(t("update_deferred"));
  }
}

async function checkForUpdate(silentIfNone = false) {
  try {
    const update = await updaterCheck();
    if (update) {
      await handleUpdateFound(update, silentIfNone);
      return;
    }
    setUpdateStatus(silentIfNone ? "" : t("update_none"));
  } catch (e) {
    setUpdateStatus(t("update_unavailable"));
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
  const quitBtn = document.getElementById("quit-app-btn");
  if (cb) {
    cb.checked = localStorage.getItem(CLOSE_TO_TRAY_KEY) === "true";
    cb.addEventListener("change", () => {
      setStored(CLOSE_TO_TRAY_KEY, cb.checked ? "true" : "false");
    });
  }
  quitBtn?.addEventListener("click", async () => {
    await quitApplication();
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
    compactStatus.textContent = daemonOk ? t("compact_daemon_ok") : t("compact_daemon_off");
    compactStatus.className = "status " + (daemonOk ? "daemon-ok" : "daemon-off");
  }
  document.getElementById("compact-expand")?.focus({ preventScroll: true });
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
  document.getElementById("compact-expand")?.addEventListener("click", async () => {
    cb.checked = false;
    setStored(COMPACT_MODE_KEY, "false");
    await applyCompactMode(false);
    switchTab("home");
  });
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
    if (toggle) {
      toggle.setAttribute("aria-label", widget.classList.contains("collapsed") ? t("dashboard_expand") : t("dashboard_collapse"));
    }
    toggle?.addEventListener("click", () => {
      widget.classList.toggle("collapsed");
      const c = getDashboardCollapsed();
      c[id] = widget.classList.contains("collapsed");
      saveDashboardCollapsed(c);
      toggle.setAttribute("aria-label", widget.classList.contains("collapsed") ? t("dashboard_expand") : t("dashboard_collapse"));
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
  initKnowledgeTab();
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
  loadLastCopilotWidget();
  if (localStorage.getItem(UPDATER_CHECK_ON_LAUNCH_KEY) === "true") {
    checkForUpdate(true);
  }
})();

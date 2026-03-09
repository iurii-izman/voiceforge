import { useState } from "react";

const STATUS = {
  done: { label: "implemented", color: "#00ff9d", bg: "rgba(0,255,157,0.08)" },
  alpha2: { label: "current", color: "#f59e0b", bg: "rgba(245,158,11,0.08)" },
  planned: { label: "future", color: "#6366f1", bg: "rgba(99,102,241,0.08)" },
};

const RAM = [
  { name: "Fedora COSMIC + PipeWire", mb: 2200, color: "#334155" },
  { name: "faster-whisper small INT8", mb: 1000, color: "#0ea5e9" },
  { name: "pyannote 4.0.4 (guarded)", mb: 1400, color: "#f59e0b" },
  { name: "all-MiniLM ONNX + SQLite-vec", mb: 200, color: "#00ff9d" },
  { name: "Tauri WebKitGTK", mb: 80, color: "#6366f1" },
  { name: "Python runtime + буферы", mb: 250, color: "#64748b" },
];

const PIPELINE = [
  {
    id: "audio",
    label: "AUDIO CAPTURE",
    icon: "🎙",
    status: "done",
    ram: "~50 MB",
    details: [
      "pw-record subprocess → stdout",
      "16kHz mono 16-bit PCM",
      "Кольцевой буфер 5 мин (ring file)",
      "Dual capture: mic + monitor source",
      "VAD: silence filtering in STT",
    ],
    note: "PipeWire: любой звук системы без плагинов",
  },
  {
    id: "stt",
    label: "STT",
    icon: "✍️",
    status: "done",
    ram: "~0.8–1.0 ГБ",
    details: [
      "faster-whisper small INT8",
      "beam_size=1, vad_filter=True",
      "Авто-детекция языка / hint из конфига",
      "StreamingTranscriber (partial+final)",
      "WER < 15% RU, < 10% EN",
    ],
    note: "СТРОГО последовательно с диаризацией",
  },
  {
    id: "diarize",
    label: "DIARIZATION",
    icon: "👥",
    status: "done",
    ram: "~1.0–1.4 ГБ",
    details: [
      "pyannote-audio==4.0.4",
      "HF token + accepted model license",
      "Memory guard + graceful skip on OOM",
      "gc.collect() после тяжёлых вызовов",
      "Rollback path documented in pyannote-version.md",
    ],
    note: "Текущий baseline: 4.0.4; при OOM есть documented rollback path.",
  },
  {
    id: "rag",
    label: "RAG",
    icon: "📚",
    status: "done",
    ram: "~0.1–0.2 ГБ",
    details: [
      "SQLite-vec + FTS5 (не ChromaDB!)",
      "all-MiniLM-L6-v2 ONNX Runtime",
      "Hybrid search: BM25 + vector (RRF)",
      "PyMuPDF для PDF-индексации",
      "Контекст: transcript[:1000] → поиск",
    ],
    note: "ChromaDB грузит HNSW в RAM целиком → нет",
  },
  {
    id: "llm",
    label: "LLM ROUTING",
    icon: "🧠",
    status: "done",
    ram: "API-only",
    details: [
      "LiteLLM SDK (не proxy!)",
      "Claude Haiku (default) / GPT-4o / Ollama",
      "Instructor + Pydantic structured output",
      "5 шаблонов: standup, sprint_review,",
      "  one_on_one, brainstorm, interview",
      "PII redaction: regex + GLiNER ONNX",
      "Бюджет из Settings.budget_limit_usd",
    ],
    note: "Ollama phi3:mini = $0 offline путь",
  },
  {
    id: "storage",
    label: "STORAGE",
    icon: "🗄",
    status: "done",
    ram: "~50 MB",
    details: [
      "transcripts.db: сессии, сегменты, анализ",
      "metrics.db: LLM calls, cost_usd (источник)",
      "rag.db: SQLite-vec + FTS5 индекс",
      "action_items таблица (cross-session)",
      "XDG_DATA_HOME / XDG_RUNTIME_DIR",
    ],
    note: "Метрики: metrics.db — источник правды для cost",
  },
];

const UI_LAYERS = [
  {
    id: "cli",
    label: "CLI",
    status: "done",
    commands: ["listen", "analyze --template", "history --search", "export", "cost", "status --detailed", "status --doctor", "action-items update", "daemon", "web"],
    note: "9 core + расширения. ADR-0001: новые команды только через ADR.",
  },
  {
    id: "web",
    label: "WEB UI",
    status: "done",
    commands: ["GET /api/status", "GET /api/sessions", "POST /api/analyze", "GET /api/export", "GET /api/cost", "POST /api/action-items/update"],
    note: "stdlib-only HTTP сервер. Опциональный fallback без Tauri.",
  },
  {
    id: "dbus",
    label: "D-BUS DAEMON",
    status: "done",
    commands: ["Analyze(seconds, template)", "GetSessions / GetSessionDetail", "GetSettings / GetAnalytics", "Listen start/stop", "GetStreamingTranscript", "→ Signals: ListenStateChanged,", "  TranscriptUpdated, AnalysisDone,", "  TranscriptChunk"],
    note: "com.voiceforge.App. Envelope: {schema_version, ok, data}",
  },
  {
    id: "tauri",
    label: "TAURI DESKTOP",
    status: "alpha2",
    commands: ["Главная: запись + анализ", "Сессии: список + детали", "Затраты: аналитика", "Настройки (read-only)", "Экспорт MD/PDF", "D-Bus only (нет HTTP внутри)"],
    note: "Rust + WebKitGTK. D-Bus client → демон. Current primary GUI track for Phase E.",
  },
];

const ROADMAP = [
  { n: 1, label: "Шаблоны analyze --template", status: "done" },
  { n: 2, label: "Action items cross-session", status: "done" },
  { n: 3, label: "Export MD/PDF", status: "done" },
  { n: 4, label: "Ollama model в конфиге", status: "done" },
  { n: 5, label: "Документация first-5min", status: "done" },
  { n: 6, label: "Cost report", status: "done" },
  { n: 7, label: "STT language hint", status: "done" },
  { n: 8, label: "E2E тесты", status: "done" },
  { n: 9, label: "Streaming STT в CLI", status: "done" },
  { n: 10, label: "Live summary listen", status: "done" },
  { n: 11, label: "PII управление", status: "done" },
  { n: 12, label: "Web UI", status: "done" },
  { n: 13, label: "Tauri Desktop", status: "alpha2" },
  { n: 14, label: "Flatpak/AppImage", status: "done" },
  { n: 15, label: "Smart trigger default", status: "done" },
  { n: 16, label: "Telegram бот", status: "planned" },
  { n: 17, label: "Интеграция с календарём", status: "alpha2" },
];

const totalRam = RAM.reduce((s, r) => s + r.mb, 0);
const totalBar = 7100;

export default function App() {
  const [tab, setTab] = useState("pipeline");
  const [active, setActive] = useState(null);

  const tabs = [
    { id: "pipeline", label: "Пайплайн" },
    { id: "ui", label: "UI слои" },
    { id: "ram", label: "RAM бюджет" },
    { id: "roadmap", label: "Roadmap" },
  ];

  return (
    <div style={{
      minHeight: "100vh",
      background: "#070b14",
      color: "#e2e8f0",
      fontFamily: "'IBM Plex Mono', 'Fira Code', monospace",
      padding: "0",
    }}>
      {/* Header */}
      <div style={{
        borderBottom: "1px solid #1e293b",
        padding: "20px 32px 16px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: "linear-gradient(180deg, #0d1220 0%, transparent 100%)",
      }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
          <span style={{ fontSize: 22, fontWeight: 700, color: "#00ff9d", letterSpacing: "-0.5px" }}>
            VoiceForge
          </span>
          <span style={{ fontSize: 11, color: "#475569", background: "#111827", padding: "2px 8px", borderRadius: 3, border: "1px solid #1e293b" }}>
            v0.2.0-alpha.2 · Phase E
          </span>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {Object.entries(STATUS).map(([k, v]) => (
            <span key={k} style={{ fontSize: 10, color: v.color, background: v.bg, border: `1px solid ${v.color}30`, padding: "3px 9px", borderRadius: 3 }}>
              ● {v.label}
            </span>
          ))}
        </div>
      </div>

      {/* Subtitle */}
      <div style={{ padding: "10px 32px", fontSize: 11, color: "#475569", borderBottom: "1px solid #111827" }}>
        local-first AI assistant for audio meetings · Fedora 43 COSMIC Atomic · AMD Ryzen 3 5300U · 8 GB RAM · Python 3.12 + Tauri 2
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", padding: "0 32px", borderBottom: "1px solid #1e293b", gap: 0 }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => { setTab(t.id); setActive(null); }} style={{
            background: "none",
            border: "none",
            borderBottom: tab === t.id ? "2px solid #00ff9d" : "2px solid transparent",
            color: tab === t.id ? "#00ff9d" : "#475569",
            padding: "12px 20px",
            cursor: "pointer",
            fontSize: 12,
            fontFamily: "inherit",
            fontWeight: tab === t.id ? 600 : 400,
            transition: "all 0.15s",
          }}>
            {t.label}
          </button>
        ))}
      </div>

      <div style={{ padding: "24px 32px", maxWidth: 1100 }}>

        {/* PIPELINE TAB */}
        {tab === "pipeline" && (
          <div>
            <div style={{ fontSize: 11, color: "#475569", marginBottom: 20 }}>
              Нажми на компонент чтобы развернуть детали · Строгий последовательный порядок: STT → затем диаризация
            </div>
            {/* Flow */}
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {PIPELINE.map((node, i) => {
                const st = STATUS[node.status];
                const isOpen = active === node.id;
                return (
                  <div key={node.id}>
                    <button
                      type="button"
                      onClick={() => setActive(isOpen ? null : node.id)}
                      style={{
                        display: "grid",
                        margin: 0,
                        padding: "12px 18px",
                        font: "inherit",
                        textAlign: "left",
                        width: "100%",
                        boxSizing: "border-box",
                        gridTemplateColumns: "40px 120px 1fr 80px 100px",
                        alignItems: "center",
                        gap: 16,
                        background: isOpen ? "#0d1a2d" : "#0a0f1c",
                        border: `1px solid ${isOpen ? st.color + "50" : "#1e293b"}`,
                        borderRadius: 6,
                        cursor: "pointer",
                        transition: "all 0.15s",
                      }}
                    >
                      <span style={{ fontSize: 18 }}>{node.icon}</span>
                      <span style={{ fontSize: 11, fontWeight: 700, color: "#94a3b8", letterSpacing: 1 }}>{node.label}</span>
                      <div style={{ height: 1, background: "#1e293b", position: "relative" }}>
                        {i < PIPELINE.length - 1 && (
                          <span style={{ position: "absolute", right: -8, top: -6, color: "#334155", fontSize: 12 }}>▶</span>
                        )}
                      </div>
                      <span style={{ fontSize: 10, color: "#475569", textAlign: "right" }}>{node.ram}</span>
                      <span style={{
                        fontSize: 10, color: st.color, background: st.bg,
                        border: `1px solid ${st.color}30`, padding: "2px 8px",
                        borderRadius: 3, textAlign: "center",
                      }}>
                        {st.label}
                      </span>
                    </button>
                    {isOpen && (
                      <div style={{
                        background: "#080d19",
                        border: `1px solid ${st.color}25`,
                        borderTop: "none",
                        borderRadius: "0 0 6px 6px",
                        padding: "14px 18px 14px 74px",
                        display: "grid",
                        gridTemplateColumns: "1fr 1fr",
                        gap: "0 32px",
                      }}>
                        <div>
                          {node.details.map((d) => (
                            <div key={d} style={{ fontSize: 11, color: "#64748b", marginBottom: 5, display: "flex", gap: 8, alignItems: "flex-start" }}>
                              <span style={{ color: st.color, flexShrink: 0, marginTop: 1 }}>›</span>
                              <span>{d}</span>
                            </div>
                          ))}
                        </div>
                        <div style={{
                          fontSize: 11, color: "#f59e0b", background: "rgba(245,158,11,0.05)",
                          border: "1px solid rgba(245,158,11,0.15)", padding: "10px 14px",
                          borderRadius: 4, alignSelf: "start",
                        }}>
                          ⚠ {node.note}
                        </div>
                      </div>
                    )}
                    {i < PIPELINE.length - 1 && (
                      <div style={{ textAlign: "center", fontSize: 16, color: "#1e293b", margin: "2px 0" }}>↓</div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Critical constraints */}
            <div style={{ marginTop: 24, padding: "14px 18px", background: "#0a0f1c", border: "1px solid #1e2a1e", borderRadius: 6 }}>
              <div style={{ fontSize: 10, color: "#00ff9d", marginBottom: 10, fontWeight: 700, letterSpacing: 1 }}>КРИТИЧЕСКИЕ ОГРАНИЧЕНИЯ</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px 32px" }}>
                {[
                  "pyannote-audio 4.0.4 baseline; rollback path documented",
                  "STT и диаризация ПОСЛЕДОВАТЕЛЬНО (не параллельно)",
                  "НЕ ChromaDB (HNSW целиком в RAM)",
                  "Горячие клавиши → D-Bus → COSMIC Settings",
                  "Пиковый RAM ≤ 5.5 ГБ (swap на NVMe = cushion)",
                  "Ключи только keyring → gnome-keyring (не .env в git)",
                  "Сборка в toolbox/distrobox (не на хосте Atomic)",
                  "uv (не pip, не poetry); max 300 строк/файл",
                ].map((c) => (
                  <div key={c} style={{ fontSize: 11, color: "#475569", display: "flex", gap: 8 }}>
                    <span style={{ color: "#ef4444" }}>✕</span>{c}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* UI LAYERS TAB */}
        {tab === "ui" && (
          <div>
            <div style={{ fontSize: 11, color: "#475569", marginBottom: 20 }}>
              Единственный backend для всех UI — демон. Tauri → D-Bus → daemon. Web UI опционален.
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              {UI_LAYERS.map(layer => {
                const st = STATUS[layer.status];
                const isOpen = active === layer.id;
                return (
                  <button
                    key={layer.id}
                    type="button"
                    onClick={() => setActive(isOpen ? null : layer.id)}
                    style={{
                      background: "#0a0f1c",
                      border: `1px solid ${isOpen ? st.color + "60" : "#1e293b"}`,
                      borderRadius: 6,
                      padding: "16px 20px",
                      cursor: "pointer",
                      transition: "all 0.15s",
                      textAlign: "left",
                      font: "inherit",
                      margin: 0,
                      width: "100%",
                      boxSizing: "border-box",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: isOpen ? 12 : 0 }}>
                      <span style={{ fontSize: 13, fontWeight: 700, color: st.color }}>{layer.label}</span>
                      <span style={{
                        fontSize: 10, color: st.color, background: st.bg,
                        border: `1px solid ${st.color}30`, padding: "2px 8px", borderRadius: 3,
                      }}>
                        {st.label}
                      </span>
                    </div>
                    {isOpen && (
                      <>
                        <div style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 12 }}>
                          {layer.commands.map((c) => (
                            <div key={c} style={{ fontSize: 11, color: "#94a3b8", display: "flex", gap: 8 }}>
                              <span style={{ color: st.color }}>›</span>{c}
                            </div>
                          ))}
                        </div>
                        <div style={{ fontSize: 10, color: "#64748b", borderTop: "1px solid #1e293b", paddingTop: 10 }}>
                          {layer.note}
                        </div>
                      </>
                    )}
                    {!isOpen && (
                      <div style={{ fontSize: 10, color: "#334155", marginTop: 6 }}>
                        {layer.commands.length} endpoint{layer.commands.length > 1 ? "s" : ""} · нажми →
                      </div>
                    )}
                  </button>
                );
              })}
            </div>

            {/* D-Bus architecture diagram */}
            <div style={{ marginTop: 20, padding: "16px 20px", background: "#0a0f1c", border: "1px solid #1e293b", borderRadius: 6 }}>
              <div style={{ fontSize: 10, color: "#475569", marginBottom: 12, letterSpacing: 1 }}>АРХИТЕКТУРА ВЗАИМОДЕЙСТВИЯ</div>
              <div style={{ fontSize: 11, color: "#64748b", display: "flex", alignItems: "center", gap: 0, flexWrap: "wrap", lineHeight: 2 }}>
                <span style={{ color: "#6366f1", background: "rgba(99,102,241,0.1)", padding: "2px 10px", borderRadius: 3 }}>CLI</span>
                <span style={{ color: "#334155", margin: "0 8px" }}>─── direct ───</span>
                <span style={{ color: "#00ff9d", background: "rgba(0,255,157,0.08)", padding: "2px 10px", borderRadius: 3 }}>Pipeline</span>
                <span style={{ color: "#334155", margin: "0 8px" }}>───</span>
                <span style={{ color: "#00ff9d", background: "rgba(0,255,157,0.08)", padding: "2px 10px", borderRadius: 3 }}>SQLite</span>
                <br style={{ width: "100%" }} />
                <span style={{ color: "#f59e0b", background: "rgba(245,158,11,0.08)", padding: "2px 10px", borderRadius: 3 }}>Tauri App</span>
                <span style={{ color: "#334155", margin: "0 8px" }}>─── D-Bus ───</span>
                <span style={{ color: "#00ff9d", background: "rgba(0,255,157,0.08)", padding: "2px 10px", borderRadius: 3 }}>Daemon</span>
                <span style={{ color: "#334155", margin: "0 8px" }}>─── D-Bus ───</span>
                <span style={{ color: "#00ff9d", background: "rgba(0,255,157,0.08)", padding: "2px 10px", borderRadius: 3 }}>Pipeline</span>
                <br style={{ width: "100%" }} />
                <span style={{ color: "#64748b", background: "#111827", padding: "2px 10px", borderRadius: 3 }}>Browser</span>
                <span style={{ color: "#334155", margin: "0 8px" }}>─── HTTP ────</span>
                <span style={{ color: "#64748b", background: "#111827", padding: "2px 10px", borderRadius: 3 }}>web server</span>
                <span style={{ color: "#334155", margin: "0 8px" }}>─── direct ───</span>
                <span style={{ color: "#00ff9d", background: "rgba(0,255,157,0.08)", padding: "2px 10px", borderRadius: 3 }}>Pipeline</span>
                <span style={{ color: "#ef444460", margin: "0 8px", fontSize: 10 }}>(optional, no D-Bus)</span>
              </div>
            </div>
          </div>
        )}

        {/* RAM TAB */}
        {tab === "ram" && (
          <div>
            <div style={{ fontSize: 11, color: "#475569", marginBottom: 20 }}>
              Пиковая нагрузка при последовательной обработке (STT выгружается перед диаризацией). Swap 7.1 ГБ на NVMe = safety net.
            </div>

            {/* Bar chart */}
            <div style={{ marginBottom: 24 }}>
              {RAM.map((r) => {
                const pct = (r.mb / totalBar) * 100;
                return (
                  <div key={r.name} style={{ marginBottom: 10 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                      <span style={{ fontSize: 11, color: "#94a3b8" }}>{r.name}</span>
                      <span style={{ fontSize: 11, color: r.color, fontWeight: 600 }}>
                        {r.mb >= 1000 ? (r.mb / 1000).toFixed(1) + " ГБ" : r.mb + " МБ"}
                      </span>
                    </div>
                    <div style={{ height: 8, background: "#111827", borderRadius: 4, overflow: "hidden" }}>
                      <div style={{
                        height: "100%",
                        width: `${pct}%`,
                        background: r.color,
                        borderRadius: 4,
                        transition: "width 0.4s",
                      }} />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Summary bars */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 20 }}>
              {[
                { label: "Пиковый (все компоненты)", value: "≈ 5.0 ГБ", note: "Теоретический максимум", color: "#f59e0b" },
                { label: "Типичный (без диаризации)", value: "≈ 3.8 ГБ", note: "Запись + STT + LLM", color: "#00ff9d" },
                { label: "Доступно для swap", value: "≈ 2.1 ГБ", note: "NVMe swap = быстро", color: "#6366f1" },
              ].map(s => (
                <div key={s.label} style={{ background: "#0a0f1c", border: "1px solid #1e293b", borderRadius: 6, padding: "14px 16px" }}>
                  <div style={{ fontSize: 20, fontWeight: 700, color: s.color, marginBottom: 4 }}>{s.value}</div>
                  <div style={{ fontSize: 11, color: "#94a3b8", marginBottom: 2 }}>{s.label}</div>
                  <div style={{ fontSize: 10, color: "#475569" }}>{s.note}</div>
                </div>
              ))}
            </div>

            {/* Rules */}
            <div style={{ background: "#0a0f1c", border: "1px solid #1e293b", borderRadius: 6, padding: "14px 18px" }}>
              <div style={{ fontSize: 10, color: "#f59e0b", marginBottom: 10, fontWeight: 700, letterSpacing: 1 }}>ПРАВИЛА УПРАВЛЕНИЯ ПАМЯТЬЮ</div>
              {[
                ["pyannote 4.0.4", "OOM risk on weak RAM", "Use memory guard + rollback path"],
                ["STT + diarize параллельно", "OOM при >3.5 ГБ app RAM", "Только последовательно"],
                ["ChromaDB", "HNSW весь в RAM", "SQLite-vec (disk-backed)"],
                ["aggressive_memory=True", "Выгружать модели после analyze", "Для экономии RAM"],
                ["gc.collect()", "После каждого pyannote вызова", "Предотвращает leak"],
                ["pyannote_restart_hours=2", "Перезапуск каждые 2 ч", "Долгосрочный memory leak"],
              ].map(([what, risk, fix]) => (
                <div key={what} style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 6, fontSize: 11 }}>
                  <span style={{ color: "#94a3b8" }}>{what}</span>
                  <span style={{ color: "#ef4444" }}>→ {risk}</span>
                  <span style={{ color: "#00ff9d" }}>✓ {fix}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ROADMAP TAB */}
        {tab === "roadmap" && (
          <div>
            <div style={{ fontSize: 11, color: "#475569", marginBottom: 20 }}>
              Статус по роадмапу · docs/plans.md
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
              {ROADMAP.map(r => {
                const st = STATUS[r.status];
                let sym;
                if (r.status === "done") sym = "✓";
                else if (r.status === "alpha2") sym = "→";
                else sym = "○";
                return (
                  <div key={r.n} style={{
                    display: "flex", alignItems: "center", gap: 12,
                    padding: "9px 14px", background: "#0a0f1c",
                    border: `1px solid ${r.status === "done" ? "#1e293b" : st.color + "30"}`,
                    borderRadius: 4, opacity: r.status === "planned" ? 0.6 : 1,
                  }}>
                    <span style={{ fontSize: 11, color: "#334155", minWidth: 20 }}>#{r.n}</span>
                    <span style={{ fontSize: 11, color: "#94a3b8", flex: 1 }}>{r.label}</span>
                    <span style={{
                      fontSize: 10, color: st.color, background: st.bg,
                      border: `1px solid ${st.color}25`, padding: "2px 7px", borderRadius: 3,
                    }}>
                      {sym} {st.label}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Alpha2 focus */}
            <div style={{ marginTop: 20, padding: "16px 20px", background: "#0a0f1c", border: "1px solid rgba(245,158,11,0.3)", borderRadius: 6 }}>
              <div style={{ fontSize: 10, color: "#f59e0b", marginBottom: 12, fontWeight: 700, letterSpacing: 1 }}>CURRENT FOCUS (Phase E)</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px 32px" }}>
                {[
                  "Wave 3: E13 → E15 (core logic, CLI, observability)",
                  "Wave 3.5: E19 desktop-first Tauri track",
                  "Tauri remains primary GUI surface",
                  "Web UI / Telegram / RAG watcher = maintenance-only",
                  "Calendar scope stays narrow on CalDAV",
                  "Managed packaging accepted later, not now",
                  "Current release baseline: v0.2.0-alpha.2",
                  "Scope guard: phase-e-decision-log.md",
                ].map((t) => (
                  <div key={t} style={{ fontSize: 11, color: "#94a3b8", display: "flex", gap: 8 }}>
                    <span style={{ color: "#f59e0b" }}>→</span>{t}
                  </div>
                ))}
              </div>
            </div>

            {/* Near-term expansion */}
            <div style={{ marginTop: 12, padding: "14px 20px", background: "#0a0f1c", border: "1px solid rgba(99,102,241,0.2)", borderRadius: 6 }}>
              <div style={{ fontSize: 10, color: "#6366f1", marginBottom: 10, fontWeight: 700, letterSpacing: 1 }}>ПОСЛЕ ТЕКУЩЕГО WAVE</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {["Desktop E2E flow", "Tray polish + hotkeys", "Calendar auto-listen/auto-analyze", "Managed packaging track", "Prompt cache beyond Claude", "Performance follow-ups", "Release proof hardening"].map(t => (
                  <span key={t} style={{ fontSize: 10, color: "#6366f1", background: "rgba(99,102,241,0.07)", border: "1px solid rgba(99,102,241,0.2)", padding: "3px 10px", borderRadius: 3 }}>
                    {t}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

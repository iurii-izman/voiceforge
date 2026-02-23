import { invoke } from "@tauri-apps/api/core";

let daemonOk = false;
let listenState = false;
let streamingInterval = null;

function setDaemonOff(msg) {
  daemonOk = false;
  const statusBar = document.getElementById("status-bar");
  const retryBtn = document.getElementById("retry");
  statusBar.textContent = msg || "Демон недоступен. Запустите: voiceforge daemon";
  statusBar.className = "status daemon-off";
  retryBtn.style.display = "block";
  document.querySelectorAll(".content button").forEach((b) => (b.disabled = true));
}

function setDaemonOk() {
  daemonOk = true;
  const statusBar = document.getElementById("status-bar");
  const retryBtn = document.getElementById("retry");
  statusBar.textContent = "Демон доступен";
  statusBar.className = "status daemon-ok";
  retryBtn.style.display = "none";
  document.querySelectorAll("#listen-toggle, #analyze-btn").forEach((b) => (b.disabled = false));
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
  if (!envelope?.ok && envelope?.error) return JSON.stringify(envelope.error);
  return "Ошибка";
}

async function checkDaemon() {
  try {
    const pong = await invoke("ping");
    if (pong !== "pong") {
      setDaemonOff("Неожиданный ответ: " + pong);
      return false;
    }
    setDaemonOk();
    return true;
  } catch (e) {
    setDaemonOff("Запустите демон: voiceforge daemon");
    return false;
  }
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach((n) => n.classList.remove("active"));
  const panel = document.getElementById("tab-" + tabId);
  const nav = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
  if (panel) panel.classList.add("active");
  if (nav) nav.classList.add("active");
  if (tabId === "sessions") loadSessions();
  if (tabId === "costs") loadAnalytics("7d");
  if (tabId === "settings") loadSettings();
}

async function updateListenState() {
  if (!daemonOk) return;
  try {
    listenState = await invoke("is_listening");
    const btn = document.getElementById("listen-toggle");
    const label = document.getElementById("listen-label");
    btn.textContent = listenState ? "Стоп записи" : "Старт записи";
    label.textContent = listenState ? "Запись идёт" : "";
    const streamingCard = document.getElementById("streaming-card");
    if (listenState) {
      streamingCard.style.display = "block";
      if (!streamingInterval) streamingInterval = setInterval(pollStreaming, 1500);
    } else {
      streamingCard.style.display = "none";
      if (streamingInterval) {
        clearInterval(streamingInterval);
        streamingInterval = null;
      }
    }
  } catch (_) {}
}

async function pollStreaming() {
  if (!daemonOk) return;
  try {
    const raw = await invoke("get_streaming_transcript");
    const env = parseEnvelope(raw);
    const data = env?.data?.streaming_transcript ?? (typeof env?.streaming_transcript !== "undefined" ? env : null);
    const text = data?.partial || "";
    const finals = data?.finals || [];
    const full = finals.map((f) => (typeof f === "string" ? f : f?.text || "")).join(" ") + (text ? " " + text : "");
    document.getElementById("streaming-text").textContent = full || "—";
  } catch (_) {}
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

document.querySelectorAll(".nav-item").forEach((n) => {
  n.addEventListener("click", () => switchTab(n.dataset.tab));
});

document.getElementById("listen-toggle").addEventListener("click", async () => {
  const btn = document.getElementById("listen-toggle");
  btn.disabled = true;
  try {
    if (listenState) await invoke("listen_stop");
    else await invoke("listen_start");
    await updateListenState();
  } catch (e) {
    document.getElementById("listen-label").textContent = "Ошибка: " + (e?.message || e);
  }
  btn.disabled = false;
});

document.getElementById("analyze-btn").addEventListener("click", async () => {
  const seconds = parseInt(document.getElementById("analyze-seconds").value, 10) || 30;
  const template = document.getElementById("analyze-template").value || null;
  const statusEl = document.getElementById("analyze-status");
  const btn = document.getElementById("analyze-btn");
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
    statusEl.textContent = "Ошибка: " + (e?.message || e);
  }
  btn.disabled = false;
});

function loadSessions() {
  const container = document.getElementById("sessions-list");
  const detailBlock = document.getElementById("session-detail");
  detailBlock.style.display = "none";
  if (!daemonOk) {
    container.innerHTML = "<p class=\"muted\">Запустите демон.</p>";
    return;
  }
  invoke("get_sessions", { limit: 50 })
    .then((raw) => {
      const env = parseEnvelope(raw);
      const sessions = env?.data?.sessions ?? env?.sessions ?? [];
      if (!Array.isArray(sessions) || sessions.length === 0) {
        container.innerHTML = "<p class=\"muted\">Сессий нет.</p>";
        return;
      }
      let html = "<table><thead><tr><th>ID</th><th>Начало</th><th>Длительность</th></tr></thead><tbody>";
      sessions.forEach((s) => {
        const id = s.id ?? s.session_id ?? "—";
        const start = s.started_at ?? s.created_at ?? "—";
        const dur = s.duration_sec != null ? s.duration_sec + " с" : "—";
        html += `<tr data-id="${id}"><td>${id}</td><td>${start}</td><td>${dur}</td></tr>`;
      });
      html += "</tbody></table>";
      container.innerHTML = html;
      container.querySelectorAll("tr[data-id]").forEach((row) => {
        row.addEventListener("click", () => showSessionDetail(parseInt(row.dataset.id, 10)));
      });
    })
    .catch((e) => {
      container.innerHTML = "<p class=\"muted\">Ошибка: " + (e?.message || e) + "</p>";
    });
}

function showSessionDetail(id) {
  const detailBlock = document.getElementById("session-detail");
  const bodyEl = document.getElementById("session-detail-body");
  const idEl = document.getElementById("detail-id");
  idEl.textContent = id;
  detailBlock.style.display = "block";
  bodyEl.textContent = "Загрузка…";
  invoke("get_session_detail", { sessionId: id })
    .then((raw) => {
      const env = parseEnvelope(raw);
      const detail = env?.data?.session_detail ?? env?.session_detail ?? env ?? {};
      bodyEl.innerHTML = "<pre>" + JSON.stringify(detail, null, 2) + "</pre>";
      document.getElementById("export-md").onclick = () => exportSession(id, "md");
      document.getElementById("export-pdf").onclick = () => exportSession(id, "pdf");
    })
    .catch((e) => {
      bodyEl.textContent = "Ошибка: " + (e?.message || e);
    });
}

async function exportSession(id, format) {
  try {
    const out = await invoke("export_session", { sessionId: id, format });
    alert("Экспорт: " + (out || "выполнен"));
  } catch (e) {
    alert("Ошибка экспорта: " + (e?.message || e));
  }
}

document.getElementById("costs-7d").addEventListener("click", () => loadAnalytics("7d"));
document.getElementById("costs-30d").addEventListener("click", () => loadAnalytics("30d"));

function loadAnalytics(period) {
  const container = document.getElementById("analytics-content");
  if (!daemonOk) {
    container.innerHTML = "<p class=\"muted\">Запустите демон.</p>";
    return;
  }
  container.innerHTML = "<p class=\"muted\">Загрузка…</p>";
  invoke("get_analytics", { period })
    .then((raw) => {
      const env = parseEnvelope(raw);
      const data = env?.data?.analytics ?? env?.analytics ?? env ?? {};
      container.innerHTML = "<pre>" + JSON.stringify(data, null, 2) + "</pre>";
    })
    .catch((e) => {
      container.innerHTML = "<p class=\"muted\">Ошибка: " + (e?.message || e) + "</p>";
    });
}

function loadSettings() {
  const container = document.getElementById("settings-content");
  if (!daemonOk) {
    container.textContent = "Запустите демон.";
    return;
  }
  invoke("get_settings")
    .then((raw) => {
      const env = parseEnvelope(raw);
      const data = env?.data?.settings ?? env?.settings ?? env ?? {};
      container.textContent = JSON.stringify(data, null, 2);
    })
    .catch((e) => {
      container.textContent = "Ошибка: " + (e?.message || e);
    });
}

(async () => {
  const ok = await checkDaemon();
  if (ok) {
    await updateListenState();
    loadSettings();
  }
})();

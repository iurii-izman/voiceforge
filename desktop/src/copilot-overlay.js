/**
 * KC2/KC3/KC6/KC7: Copilot overlay — state label, recording indicator, transcript snippet, ambiguity hint,
 * cards (Evidence, Answer, Do/Don't, Clarify, Risk, Strategy, Emotion) with priority order and max 3 visible + overflow.
 * States: armed | recording | recording_warning | analyzing | error.
 */

import { listen } from "@tauri-apps/api/event";
import { invoke } from "@tauri-apps/api/core";

const STATE_LABELS = {
  armed: "Готов",
  recording: "Запись…",
  recording_warning: "Скоро стоп (5 с)", // KC3: 30s auto-stop warning
  analyzing: "Анализ…",
  error: "Ошибка",
};

let transcriptPollTimer = null;
let cardsPollTimer = null;

function clearTranscriptPoll() {
  if (transcriptPollTimer) {
    clearInterval(transcriptPollTimer);
    transcriptPollTimer = null;
  }
  const el = document.getElementById("copilot-transcript-snippet");
  if (el) {
    el.textContent = "";
    el.setAttribute("aria-hidden", "true");
  }
}

const CARD_IDS = [
  "copilot-card-evidence",
  "copilot-card-answer",
  "copilot-card-dodont",
  "copilot-card-clarify",
  "copilot-card-risk",
  "copilot-card-strategy",
  "copilot-card-emotion",
];
const MAX_VISIBLE_CARDS = 3;

function clearCards() {
  if (cardsPollTimer) {
    clearTimeout(cardsPollTimer);
    cardsPollTimer = null;
  }
  CARD_IDS.forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.hidden = true;
      el.textContent = "";
    }
  });
  const overflow = document.getElementById("copilot-cards-overflow");
  if (overflow) {
    overflow.hidden = true;
    overflow.textContent = "";
  }
  const container = document.getElementById("copilot-cards");
  if (container) container.setAttribute("aria-hidden", "true");
}

function buildCardList(envelope) {
  const list = [];
  if (Array.isArray(envelope.rag_citations) && envelope.rag_citations.length > 0) {
    const parts = envelope.rag_citations.slice(0, 2).map((c) => (c.snippet || c.source_basename || "").trim()).filter(Boolean);
    if (parts.length > 0) {
      list.push({ priority: 1, id: "copilot-card-evidence", title: "Evidence", body: escapeHtml(parts.join("\n")) });
    }
  }
  if (Array.isArray(envelope.copilot_answer) && envelope.copilot_answer.length > 0) {
    const text = envelope.copilot_answer.join(" ").trim();
    if (text) list.push({ priority: 2, id: "copilot-card-answer", title: "Answer", body: escapeHtml(text) });
  }
  const dos = Array.isArray(envelope.copilot_dos) ? envelope.copilot_dos : [];
  const donts = Array.isArray(envelope.copilot_donts) ? envelope.copilot_donts : [];
  const dodontLines = [...dos.map((s) => `✓ ${s}`), ...donts.map((s) => `✗ ${s}`)].filter(Boolean);
  if (dodontLines.length > 0) {
    list.push({ priority: 3, id: "copilot-card-dodont", title: "Do / Don't", body: escapeHtml(dodontLines.join("\n")) });
  }
  if (Array.isArray(envelope.copilot_clarify) && envelope.copilot_clarify.length > 0) {
    const text = envelope.copilot_clarify.join("\n").trim();
    if (text) list.push({ priority: 4, id: "copilot-card-clarify", title: "Clarify", body: escapeHtml(text) });
  }
  if (Array.isArray(envelope.copilot_risk) && envelope.copilot_risk.length > 0) {
    const text = envelope.copilot_risk.join("\n").trim();
    if (text) list.push({ priority: 5, id: "copilot-card-risk", title: "Risk", body: escapeHtml(text) });
  }
  if (envelope.copilot_strategy && String(envelope.copilot_strategy).trim()) {
    list.push({ priority: 6, id: "copilot-card-strategy", title: "Strategy", body: escapeHtml(String(envelope.copilot_strategy).trim()) });
  }
  if (envelope.copilot_emotion && String(envelope.copilot_emotion).trim()) {
    list.push({ priority: 7, id: "copilot-card-emotion", title: "Emotion", body: escapeHtml(String(envelope.copilot_emotion).trim()) });
  }
  return list.sort((a, b) => a.priority - b.priority);
}

function renderCards(data) {
  const envelope = data?.data ?? data;
  const container = document.getElementById("copilot-cards");
  if (!container) return;
  if (!envelope) {
    clearCards();
    return;
  }
  const cards = buildCardList(envelope);
  CARD_IDS.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.hidden = true;
  });
  const visible = cards.slice(0, MAX_VISIBLE_CARDS);
  visible.forEach((card) => {
    const el = document.getElementById(card.id);
    if (el) {
      el.innerHTML = `<span class="copilot-card__title">${escapeHtml(card.title)}</span><div class="copilot-card__body">${card.body}</div>`;
      el.hidden = false;
    }
  });
  const overflowEl = document.getElementById("copilot-cards-overflow");
  if (overflowEl) {
    if (cards.length > MAX_VISIBLE_CARDS) {
      overflowEl.textContent = `+${cards.length - MAX_VISIBLE_CARDS} more`;
      overflowEl.hidden = false;
      overflowEl.setAttribute("aria-hidden", "false");
    } else {
      overflowEl.hidden = true;
      overflowEl.setAttribute("aria-hidden", "true");
    }
  }
  container.setAttribute("aria-hidden", cards.length === 0 ? "true" : "false");
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

function startTranscriptPoll() {
  clearTranscriptPoll();
  const el = document.getElementById("copilot-transcript-snippet");
  if (!el) return;
  el.setAttribute("aria-hidden", "false");
  transcriptPollTimer = setInterval(async () => {
    try {
      const raw = await invoke("get_streaming_transcript");
      const data = typeof raw === "string" ? JSON.parse(raw) : raw;
      const envelope = data?.data ?? data;
      let partial = envelope?.partial ?? "";
      if (typeof envelope?.streaming_transcript === "string") {
        try {
          const inner = JSON.parse(envelope.streaming_transcript);
          partial = inner?.partial ?? partial;
        } catch (_) {}
      }
      el.textContent = (partial || "").slice(0, 120) || "—";
    } catch {
      el.textContent = "—";
    }
  }, 1500);
}

const MODE_LABELS = { cloud: "☁ Cloud", hybrid: "⚡ Hybrid", offline: "🔒 Offline" };

function updateModeBadge(mode) {
  const el = document.getElementById("copilot-mode-badge");
  if (!el) return;
  const m = (mode && String(mode).toLowerCase()) || "hybrid";
  const label = MODE_LABELS[m] ?? m;
  el.textContent = label;
  el.className = "copilot-mode-badge " + (["cloud", "hybrid", "offline"].includes(m) ? m : "hybrid");
}

async function fetchStatusAndRenderCards() {
  try {
    const raw = await invoke("get_copilot_capture_status");
    const data = typeof raw === "string" ? JSON.parse(raw) : raw;
    const envelope = data?.data ?? data;
    if (!envelope) return;
    if (envelope.copilot_mode) updateModeBadge(envelope.copilot_mode);
    const hintEl = document.getElementById("copilot-ambiguity-hint");
    if (hintEl) {
      const sttAmbiguous = envelope.stt_ambiguous === true;
      if (sttAmbiguous) {
        hintEl.textContent = "Проверьте транскрипт";
        hintEl.setAttribute("aria-hidden", "false");
      } else {
        hintEl.textContent = "";
        hintEl.setAttribute("aria-hidden", "true");
      }
    }
    renderCards({ data: envelope });
  } catch (_) {}
}

async function checkAmbiguityHint() {
  await fetchStatusAndRenderCards();
}

function applyState(state) {
  const root = document.getElementById("copilot-overlay-root");
  const indicator = document.getElementById("copilot-recording-indicator");
  const labelEl = document.getElementById("copilot-state-label");
  if (!root || !indicator || !labelEl) return;

  const s = String(state).toLowerCase();
  const text = STATE_LABELS[s] ?? state;

  labelEl.textContent = text;
  labelEl.className = "copilot-state-label" + (s ? " " + s : "");

  if (s === "recording" || s === "recording_warning") {
    indicator.classList.add("visible");
    indicator.setAttribute("aria-hidden", "false");
    startTranscriptPoll();
    clearCards();
  } else {
    indicator.classList.remove("visible");
    indicator.setAttribute("aria-hidden", "true");
    clearTranscriptPoll();
    if (s === "analyzing") {
      cardsPollTimer = setTimeout(checkAmbiguityHint, 3000);
    } else {
      clearCards();
      const hintEl = document.getElementById("copilot-ambiguity-hint");
      if (hintEl) hintEl.textContent = "";
    }
  }
}

listen("copilot-state-changed", (event) => {
  const payload = event.payload;
  const state = payload?.state ?? "armed";
  applyState(state);
});

// Initial state
applyState("armed");
// KC10: fetch once to show current copilot_mode in overlay
fetchStatusAndRenderCards().catch(() => updateModeBadge("hybrid"));

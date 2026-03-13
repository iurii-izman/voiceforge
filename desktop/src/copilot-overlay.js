/**
 * KC2/KC3/KC6: Copilot overlay — state label, recording indicator, transcript snippet, ambiguity hint,
 * fast-track cards (Evidence, Answer, Do/Don't, Clarify) in order.
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

function clearCards() {
  if (cardsPollTimer) {
    clearTimeout(cardsPollTimer);
    cardsPollTimer = null;
  }
  const ids = ["copilot-card-evidence", "copilot-card-answer", "copilot-card-dodont", "copilot-card-clarify"];
  ids.forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.hidden = true;
      el.textContent = "";
    }
  });
  const container = document.getElementById("copilot-cards");
  if (container) container.setAttribute("aria-hidden", "true");
}

function renderCards(data) {
  const envelope = data?.data ?? data;
  const container = document.getElementById("copilot-cards");
  if (!container) return;
  if (!envelope) {
    clearCards();
    return;
  }

  let hasAny = false;

  const evidenceEl = document.getElementById("copilot-card-evidence");
  if (evidenceEl && Array.isArray(envelope.rag_citations) && envelope.rag_citations.length > 0) {
    const parts = envelope.rag_citations.slice(0, 2).map((c) => (c.snippet || c.source_basename || "").trim()).filter(Boolean);
    if (parts.length > 0) {
      evidenceEl.innerHTML = `<span class="copilot-card__title">Evidence</span><div class="copilot-card__body">${escapeHtml(parts.join("\n"))}</div>`;
      evidenceEl.hidden = false;
      hasAny = true;
    } else {
      evidenceEl.hidden = true;
    }
  } else if (evidenceEl) {
    evidenceEl.hidden = true;
  }

  const answerEl = document.getElementById("copilot-card-answer");
  if (answerEl && Array.isArray(envelope.copilot_answer) && envelope.copilot_answer.length > 0) {
    const text = envelope.copilot_answer.join(" ").trim();
    if (text) {
      answerEl.innerHTML = `<span class="copilot-card__title">Answer</span><div class="copilot-card__body">${escapeHtml(text)}</div>`;
      answerEl.hidden = false;
      hasAny = true;
    } else {
      answerEl.hidden = true;
    }
  } else if (answerEl) {
    answerEl.hidden = true;
  }

  const dodontEl = document.getElementById("copilot-card-dodont");
  if (dodontEl) {
    const dos = Array.isArray(envelope.copilot_dos) ? envelope.copilot_dos : [];
    const donts = Array.isArray(envelope.copilot_donts) ? envelope.copilot_donts : [];
    const lines = [...dos.map((s) => `✓ ${s}`), ...donts.map((s) => `✗ ${s}`)].filter(Boolean);
    if (lines.length > 0) {
      dodontEl.innerHTML = `<span class="copilot-card__title">Do / Don't</span><div class="copilot-card__body">${escapeHtml(lines.join("\n"))}</div>`;
      dodontEl.hidden = false;
      hasAny = true;
    } else {
      dodontEl.hidden = true;
    }
  }

  const clarifyEl = document.getElementById("copilot-card-clarify");
  if (clarifyEl && Array.isArray(envelope.copilot_clarify) && envelope.copilot_clarify.length > 0) {
    const text = envelope.copilot_clarify.join("\n").trim();
    if (text) {
      clarifyEl.innerHTML = `<span class="copilot-card__title">Clarify</span><div class="copilot-card__body">${escapeHtml(text)}</div>`;
      clarifyEl.hidden = false;
      hasAny = true;
    } else {
      clarifyEl.hidden = true;
    }
  } else if (clarifyEl) {
    clarifyEl.hidden = true;
  }

  container.setAttribute("aria-hidden", hasAny ? "false" : "true");
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

async function checkAmbiguityHint() {
  const hintEl = document.getElementById("copilot-ambiguity-hint");
  if (!hintEl) return;
  try {
    const raw = await invoke("get_copilot_capture_status");
    const data = typeof raw === "string" ? JSON.parse(raw) : raw;
    const envelope = data?.data ?? data;
    const sttAmbiguous = envelope?.stt_ambiguous === true;
    if (sttAmbiguous) {
      hintEl.textContent = "Проверьте транскрипт";
      hintEl.setAttribute("aria-hidden", "false");
    } else {
      hintEl.textContent = "";
      hintEl.setAttribute("aria-hidden", "true");
    }
  } catch {
    hintEl.setAttribute("aria-hidden", "true");
  }
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
      cardsPollTimer = setTimeout(checkAmbiguityHint, 2500);
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

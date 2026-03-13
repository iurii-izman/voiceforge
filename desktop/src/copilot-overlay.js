/**
 * KC2/KC3: Copilot overlay — state label, recording indicator, transcript snippet, ambiguity hint.
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
  } else {
    indicator.classList.remove("visible");
    indicator.setAttribute("aria-hidden", "true");
    clearTranscriptPoll();
    if (s === "analyzing") {
      setTimeout(checkAmbiguityHint, 2500);
    }
    const hintEl = document.getElementById("copilot-ambiguity-hint");
    if (hintEl && s !== "analyzing") hintEl.textContent = "";
  }
}

listen("copilot-state-changed", (event) => {
  const payload = event.payload;
  const state = payload?.state ?? "armed";
  applyState(state);
});

// Initial state
applyState("armed");

/**
 * KC2: Copilot overlay — listens to copilot-state-changed, shows recording indicator and state label.
 * States: armed | recording | analyzing | error. Latest capture replaces previous (no trap states).
 */

import { listen } from "@tauri-apps/api/event";

const STATE_LABELS = {
  armed: "Готов",
  recording: "Запись…",
  analyzing: "Анализ…",
  error: "Ошибка",
};

function applyState(state) {
  const root = document.getElementById("copilot-overlay-root");
  const indicator = document.getElementById("copilot-recording-indicator");
  const labelEl = document.getElementById("copilot-state-label");
  if (!root || !indicator || !labelEl) return;

  const s = String(state).toLowerCase();
  const text = STATE_LABELS[s] ?? state;

  labelEl.textContent = text;
  labelEl.className = "copilot-state-label" + (s ? " " + s : "");

  if (s === "recording") {
    indicator.classList.add("visible");
    indicator.setAttribute("aria-hidden", "false");
  } else {
    indicator.classList.remove("visible");
    indicator.setAttribute("aria-hidden", "true");
  }
}

listen("copilot-state-changed", (event) => {
  const payload = event.payload;
  const state = payload?.state ?? "armed";
  applyState(state);
});

// Initial state
applyState("armed");

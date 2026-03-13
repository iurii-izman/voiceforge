import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  clearScreen: false,
  build: {
    outDir: "dist",
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, "index.html"),
        "copilot-overlay": resolve(__dirname, "copilot-overlay.html"),
      },
    },
  },
  root: ".",
});

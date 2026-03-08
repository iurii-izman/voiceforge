import fs from "node:fs";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const desktopDir = path.resolve(__dirname, "..");
const tauriDriverPath = process.env.TAURI_DRIVER_PATH || path.join(os.homedir(), ".cargo", "bin", "tauri-driver");
const binaryPath = path.join(desktopDir, "src-tauri", "target", "debug", "voiceforge-desktop");

let tauriDriverProcess;
let tauriDriverClosed = false;

function listDirs(rootDir) {
  if (!rootDir || !fs.existsSync(rootDir)) return [];
  return fs
    .readdirSync(rootDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => path.join(rootDir, entry.name))
    .sort();
}

function listFlatpakNativeDrivers() {
  const runtimeRoot = path.join(os.homedir(), ".local", "share", "flatpak", "runtime", "org.gnome.Platform");
  const candidates = [];
  for (const archDir of listDirs(runtimeRoot)) {
    for (const versionDir of listDirs(archDir)) {
      for (const revisionDir of listDirs(versionDir)) {
        const driverPath = path.join(revisionDir, "files", "bin", "WebKitWebDriver");
        if (fs.existsSync(driverPath)) {
          candidates.push(driverPath);
        }
      }
    }
  }
  return candidates.reverse();
}

function resolveNativeDriver() {
  const candidates = [
    process.env.TAURI_NATIVE_DRIVER,
    process.env.WEBKIT_WEBDRIVER,
    "/usr/bin/WebKitWebDriver",
    "/usr/local/bin/WebKitWebDriver",
    ...listFlatpakNativeDrivers(),
  ].filter(Boolean);

  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) return candidate;
  }

  throw new Error(
    "WebKitWebDriver not found. Set TAURI_NATIVE_DRIVER or install WebKitWebDriver in toolbox/system.",
  );
}

function waitForPort(port, timeoutMs = 15000) {
  const started = Date.now();
  return new Promise((resolve, reject) => {
    const tryConnect = () => {
      const socket = new net.Socket();
      socket
        .once("connect", () => {
          socket.destroy();
          resolve();
        })
        .once("error", () => {
          socket.destroy();
          if (Date.now() - started > timeoutMs) {
            reject(new Error(`Timed out waiting for port ${port}`));
          } else {
            setTimeout(tryConnect, 250);
          }
        })
        .connect(port, "127.0.0.1");
    };
    tryConnect();
  });
}

function closeTauriDriver() {
  tauriDriverClosed = true;
  if (tauriDriverProcess) {
    tauriDriverProcess.kill();
    tauriDriverProcess = undefined;
  }
}

export const config = {
  hostname: "127.0.0.1",
  port: 4444,
  path: "/",
  specs: ["./specs/**/*.e2e.js"],
  maxInstances: 1,
  reporters: ["spec"],
  framework: "mocha",
  mochaOpts: {
    ui: "bdd",
    timeout: 120000,
  },
  waitforTimeout: 15000,
  connectionRetryTimeout: 120000,
  capabilities: [
    {
      maxInstances: 1,
      "tauri:options": {
        application: binaryPath,
      },
    },
  ],
  onPrepare() {
    const build = spawnSync("npm", ["run", "tauri", "build", "--", "--debug", "--no-bundle"], {
      cwd: desktopDir,
      stdio: "inherit",
      shell: true,
    });
    if (build.status !== 0) {
      throw new Error("Failed to build debug Tauri application for native smoke.");
    }
    if (!fs.existsSync(binaryPath)) {
      throw new Error(`Tauri debug binary not found: ${binaryPath}`);
    }
  },
  async beforeSession() {
    const nativeDriverPath = resolveNativeDriver();
    tauriDriverClosed = false;
    tauriDriverProcess = spawn(
      tauriDriverPath,
      ["--native-driver", nativeDriverPath, "--native-host", "127.0.0.1", "--port", "4444", "--native-port", "4445"],
      { stdio: ["ignore", "inherit", "inherit"] },
    );
    tauriDriverProcess.on("exit", (code) => {
      if (!tauriDriverClosed) {
        console.error(`tauri-driver exited unexpectedly with code ${code}`);
      }
    });
    await waitForPort(4444);
  },
  afterSession() {
    closeTauriDriver();
  },
  onComplete() {
    closeTauriDriver();
  },
};

["SIGINT", "SIGTERM", "SIGHUP", "exit"].forEach((signalName) => {
  process.on(signalName, () => {
    closeTauriDriver();
  });
});

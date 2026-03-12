import fs from "node:fs";
import http from "node:http";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const desktopDir = path.resolve(__dirname, "..");
const defaultArtifactDir = path.join(desktopDir, "e2e-native", "artifacts", "manual");
const artifactDir = process.env.VOICEFORGE_NATIVE_SMOKE_ARTIFACT_DIR || defaultArtifactDir;
const tauriDriverPath = process.env.TAURI_DRIVER_PATH || path.join(os.homedir(), ".cargo", "bin", "tauri-driver");
const binaryPath = path.join(desktopDir, "src-tauri", "target", "debug", "voiceforge-desktop");
const driverLogPath = path.join(artifactDir, "tauri-driver.log");
const driverErrLogPath = path.join(artifactDir, "tauri-driver.stderr.log");
const sessionTimeoutMs = Number.parseInt(process.env.WEBDRIVER_SESSION_TIMEOUT_MS || "25000", 10);

let tauriDriverProcess;
let tauriDriverClosed = false;
let tauriDriverStdout;
let tauriDriverStderr;

fs.mkdirSync(artifactDir, { recursive: true });

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

function resolveTauriDriver() {
  const fromPath = spawnSync("bash", ["-lc", "command -v tauri-driver"], { encoding: "utf-8" });
  const candidates = [process.env.TAURI_DRIVER_PATH, tauriDriverPath, fromPath.stdout.trim()].filter(Boolean);
  for (const candidate of candidates) {
    if (candidate && fs.existsSync(candidate)) return candidate;
  }
  throw new Error("tauri-driver not found. Install with `cargo install tauri-driver --locked`.");
}

function resolveNativeDriver() {
  const candidates = [
    process.env.TAURI_NATIVE_DRIVER,
    process.env.WEBKIT_WEBDRIVER,
    "/usr/bin/WebKitWebDriver",
    "/usr/local/bin/WebKitWebDriver",
    ...listFlatpakNativeDrivers(),
  ].filter(Boolean);

  const unusable = [];
  for (const candidate of candidates) {
    if (!fs.existsSync(candidate)) continue;
    const probe = spawnSync(candidate, ["--help"], {
      encoding: "utf-8",
      timeout: 5000,
    });
    if (probe.status === 0) return candidate;
    const detail = (probe.stderr || probe.stdout || probe.error?.message || `exit ${probe.status ?? "unknown"}`)
      .toString()
      .trim()
      .split("\n")[0];
    unusable.push(`${candidate}: ${detail}`);
  }

  throw new Error(
    `WebKitWebDriver not found or unusable. Set TAURI_NATIVE_DRIVER to a working binary or install WebKitWebDriver in toolbox/system. Checked: ${unusable.join(" | ") || "no candidates"}`,
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

function waitForWebDriverStatus(timeoutMs = sessionTimeoutMs) {
  const started = Date.now();
  return new Promise((resolve, reject) => {
    const tryConnect = () => {
      const req = http.request(
        { host: "127.0.0.1", port: 4444, path: "/status", method: "GET", timeout: 2000 },
        (res) => {
          let body = "";
          res.on("data", (chunk) => {
            body += chunk;
          });
          res.on("end", () => {
            if (res.statusCode && res.statusCode < 500) {
              resolve(body);
              return;
            }
            if (Date.now() - started > timeoutMs) {
              reject(new Error(`Timed out waiting for WebDriver status at /status (HTTP ${res.statusCode ?? "unknown"})`));
            } else {
              setTimeout(tryConnect, 500);
            }
          });
        },
      );
      req.on("timeout", () => {
        req.destroy(new Error("status request timed out"));
      });
      req.on("error", () => {
        if (Date.now() - started > timeoutMs) {
          reject(new Error("Timed out waiting for responsive WebDriver /status endpoint"));
        } else {
          setTimeout(tryConnect, 500);
        }
      });
      req.end();
    };
    tryConnect();
  });
}

function writeArtifact(name, data) {
  fs.writeFileSync(path.join(artifactDir, name), typeof data === "string" ? data : JSON.stringify(data, null, 2), "utf-8");
}

function closeTauriDriver() {
  tauriDriverClosed = true;
  if (tauriDriverProcess) {
    tauriDriverProcess.kill();
    tauriDriverProcess = undefined;
  }
  tauriDriverStdout?.end();
  tauriDriverStderr?.end();
  tauriDriverStdout = undefined;
  tauriDriverStderr = undefined;
}

export const config = {
  hostname: "127.0.0.1",
  port: 4444,
  path: "/",
  outputDir: artifactDir,
  logLevel: process.env.WDIO_LOG_LEVEL || "warn",
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
    const resolvedTauriDriver = resolveTauriDriver();
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
    writeArtifact("native-smoke-context.json", {
      artifactDir,
      binaryPath,
      resolvedTauriDriver,
      nativeDriverHint: process.env.TAURI_NATIVE_DRIVER || process.env.WEBKIT_WEBDRIVER || "auto-resolve",
    });
  },
  async beforeSession() {
    const resolvedTauriDriver = resolveTauriDriver();
    const nativeDriverPath = resolveNativeDriver();
    writeArtifact("native-smoke-context.json", {
      artifactDir,
      binaryPath,
      resolvedTauriDriver,
      nativeDriverPath,
    });
    tauriDriverClosed = false;
    tauriDriverStdout = fs.createWriteStream(driverLogPath, { flags: "a" });
    tauriDriverStderr = fs.createWriteStream(driverErrLogPath, { flags: "a" });
    tauriDriverProcess = spawn(
      resolvedTauriDriver,
      ["--native-driver", nativeDriverPath, "--native-host", "127.0.0.1", "--port", "4444", "--native-port", "4445"],
      { stdio: ["ignore", "pipe", "pipe"] },
    );
    tauriDriverProcess.stdout?.pipe(tauriDriverStdout);
    tauriDriverProcess.stderr?.pipe(tauriDriverStderr);
    tauriDriverProcess.on("exit", (code) => {
      if (!tauriDriverClosed) {
        const message = `tauri-driver exited unexpectedly with code ${code}; see ${driverErrLogPath}`;
        tauriDriverStderr?.write(`${message}\n`);
        console.error(message);
      }
    });
    await waitForPort(4444);
    try {
      await waitForWebDriverStatus();
    } catch (error) {
      closeTauriDriver();
      const detail = error instanceof Error ? error.message : String(error);
      throw new Error(`Native WebDriver handshake did not become ready. See artifacts in ${artifactDir}. Detail: ${detail}`);
    }
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

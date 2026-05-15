/**
 * Backend-Subprozess-Manager.
 *
 * Startet das Python-Backend als Subprozess, wartet auf Health-Check, und
 * beendet es sauber beim App-Quit.
 */

import { spawn, ChildProcess } from "child_process";
import * as path from "path";
import * as net from "net";
import { app } from "electron";

let backend: ChildProcess | null = null;
let backendPort = 8765;

export function backendUrl(): string {
  return `http://127.0.0.1:${backendPort}`;
}

async function findFreePort(start: number = 8765): Promise<number> {
  for (let p = start; p < start + 100; p++) {
    const free = await new Promise<boolean>((resolve) => {
      const srv = net.createServer();
      srv.once("error", () => resolve(false));
      srv.once("listening", () => srv.close(() => resolve(true)));
      srv.listen(p, "127.0.0.1");
    });
    if (free) return p;
  }
  throw new Error("Keine freien Ports gefunden");
}

async function waitForHealth(url: string, timeoutMs: number = 30000): Promise<void> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const r = await fetch(`${url}/health`);
      if (r.ok) return;
    } catch {
      // noch nicht oben
    }
    await new Promise((res) => setTimeout(res, 250));
  }
  throw new Error(`Backend startet nicht (Timeout ${timeoutMs}ms)`);
}

function backendBinary(): { command: string; args: string[]; cwd: string } {
  if (process.env.CAMWOSA_DEV === "1") {
    // Dev-Modus: lokales Python aus venv
    const venv = path.resolve(__dirname, "../../backend/.venv/Scripts/python.exe");
    return {
      command: venv,
      args: ["-m", "camwosa.api.app"],
      cwd: path.resolve(__dirname, "../../backend"),
    };
  }
  // Prod: gebuendeltes Python (PyInstaller)
  const exeName = process.platform === "win32" ? "camwosa-backend.exe" : "camwosa-backend";
  return {
    command: path.join(process.resourcesPath, "backend", exeName),
    args: [],
    cwd: process.resourcesPath,
  };
}

export async function startBackend(): Promise<void> {
  backendPort = await findFreePort(8765);
  const { command, args, cwd } = backendBinary();
  backend = spawn(command, args, {
    env: {
      ...process.env,
      CAMWOSA_BACKEND_PORT: String(backendPort),
      CAMWOSA_DATA_DIR: process.env.CAMWOSA_DEV === "1"
        ? path.resolve(__dirname, "../../data")
        : path.join(process.resourcesPath, "data"),
    },
    cwd,
    stdio: ["ignore", "pipe", "pipe"],
  });

  backend.stdout?.on("data", (d) => console.log(`[backend] ${d}`));
  backend.stderr?.on("data", (d) => console.error(`[backend] ${d}`));
  backend.on("exit", (code) => {
    console.log(`[backend] exit ${code}`);
    backend = null;
  });

  await waitForHealth(backendUrl());
  console.log(`[backend] ready at ${backendUrl()}`);
}

export async function stopBackend(): Promise<void> {
  if (!backend) return;
  return new Promise((resolve) => {
    backend!.once("exit", () => resolve());
    backend!.kill("SIGTERM");
    setTimeout(() => {
      if (backend) backend.kill("SIGKILL");
      resolve();
    }, 5000);
  });
}

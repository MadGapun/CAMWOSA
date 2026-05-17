/**
 * Electron Main-Process fuer CAMWOSA.
 *
 * Verantwortlich fuer:
 *  - App-Lifecycle (Fenster, Menue, Tray)
 *  - Backend-Subprozess (Python Flask)
 *  - Datei-Assoziation .cwp
 *  - Auto-Updater
 */

import { app, BrowserWindow, ipcMain, dialog, Menu } from "electron";
import * as path from "path";
import { startBackend, stopBackend, backendUrl } from "./backend_runner";

// Auto-Updater — Master-Plan C4. Lazy-Import damit der Dev-Run nicht meckert,
// wenn electron-updater nicht installiert ist.
async function setupAutoUpdater(): Promise<void> {
  if (process.env.CAMWOSA_DEV === "1") return;  // im Dev nicht updaten
  try {
    const { autoUpdater } = await import("electron-updater");
    autoUpdater.autoDownload = false;  // erst fragen, dann laden
    autoUpdater.on("update-available", async (info) => {
      const result = await dialog.showMessageBox({
        type: "info",
        title: "Update verfuegbar",
        message: `CAMWOSA ${info.version} ist verfuegbar (aktuell ${app.getVersion()}).`,
        detail: "Jetzt herunterladen?",
        buttons: ["Herunterladen", "Spaeter"],
        defaultId: 0,
      });
      if (result.response === 0) {
        await autoUpdater.downloadUpdate();
      }
    });
    autoUpdater.on("update-downloaded", async () => {
      const result = await dialog.showMessageBox({
        type: "info",
        title: "Update bereit",
        message: "Das Update wird beim naechsten Start installiert.",
        buttons: ["Jetzt neu starten", "Spaeter"],
        defaultId: 0,
      });
      if (result.response === 0) {
        autoUpdater.quitAndInstall();
      }
    });
    autoUpdater.on("error", (e) => {
      console.warn("[updater] Fehler (nicht-kritisch):", e?.message ?? e);
    });
    // Check beim Start (verzoegert damit das UI erst sichtbar ist)
    setTimeout(() => {
      autoUpdater.checkForUpdates().catch((e) => {
        console.warn("[updater] check fehlgeschlagen:", e?.message ?? e);
      });
    }, 5000);
  } catch (e) {
    console.warn("[updater] electron-updater nicht verfuegbar:", e);
  }
}

let mainWindow: BrowserWindow | null = null;

async function createWindow(): Promise<void> {
  mainWindow = new BrowserWindow({
    width: 1600,
    height: 1000,
    minWidth: 1200,
    minHeight: 800,
    title: "CAMWOSA",
    backgroundColor: "#1a1a1a",
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  mainWindow.once("ready-to-show", () => mainWindow?.show());

  // Debug-Hilfe: Renderer-Fehler sichtbar machen
  mainWindow.webContents.on("did-fail-load", (_e, code, desc, url) => {
    console.error(`[renderer] did-fail-load ${code} ${desc} ${url}`);
  });
  mainWindow.webContents.on("render-process-gone", (_e, details) => {
    console.error(`[renderer] gone ${details.reason} ${details.exitCode}`);
  });
  // ALLE Renderer-Console-Messages (warnings, errors) nach stdout
  mainWindow.webContents.on("console-message", (_e, level, message, line, source) => {
    const lvl = ["DBG", "LOG", "WRN", "ERR"][level] ?? `L${level}`;
    console.log(`[renderer:${lvl}] ${message}  (${source}:${line})`);
  });
  mainWindow.webContents.on("did-finish-load", () => {
    console.log("[renderer] did-finish-load");
  });
  // CAMWOSA_DEBUG=1 oeffnet DevTools auch im Production-Bundle — Markus' Bug-Path
  if (process.env.CAMWOSA_DEBUG === "1" || process.env.CAMWOSA_DEV === "1") {
    mainWindow.webContents.openDevTools({ mode: "right" });
  }

  // Im Dev-Modus: Vite-Server. Im Prod: gebautes Frontend.
  if (process.env.CAMWOSA_DEV === "1") {
    await mainWindow.loadURL("http://localhost:5173");
  } else {
    const indexPfad = path.join(__dirname, "../../frontend/dist/index.html");
    console.log(`[main] loading frontend: ${indexPfad}`);
    await mainWindow.loadFile(indexPfad);
  }
}

function setupMenu(): void {
  const template: Electron.MenuItemConstructorOptions[] = [
    {
      label: "Datei",
      submenu: [
        { label: "Neues Projekt", accelerator: "CmdOrCtrl+N",
          click: () => mainWindow?.webContents.send("menu:projekt-neu") },
        { label: "Projekt oeffnen...", accelerator: "CmdOrCtrl+O",
          click: async () => {
            const result = await dialog.showOpenDialog({
              filters: [{ name: "CAMWOSA Project", extensions: ["cwp"] }],
              properties: ["openFile"],
            });
            if (!result.canceled && result.filePaths[0]) {
              mainWindow?.webContents.send("menu:projekt-oeffnen", result.filePaths[0]);
            }
          },
        },
        { label: "Speichern", accelerator: "CmdOrCtrl+S",
          click: () => mainWindow?.webContents.send("menu:speichern") },
        { label: "Speichern als...", accelerator: "CmdOrCtrl+Shift+S",
          click: () => mainWindow?.webContents.send("menu:speichern-als") },
        { type: "separator" },
        { label: "DXF importieren...",
          click: () => mainWindow?.webContents.send("menu:dxf-import") },
        { label: "STL importieren...",
          click: () => mainWindow?.webContents.send("menu:stl-import") },
        { type: "separator" },
        { label: "Beenden", role: "quit" },
      ],
    },
    {
      label: "Bearbeiten",
      submenu: [
        { role: "undo", label: "Rueckgaengig" },
        { role: "redo", label: "Wiederholen" },
        { type: "separator" },
        { role: "cut", label: "Ausschneiden" },
        { role: "copy", label: "Kopieren" },
        { role: "paste", label: "Einfuegen" },
      ],
    },
    {
      label: "Hilfe",
      submenu: [
        { label: "Wiki oeffnen",
          click: async () => {
            const { shell } = await import("electron");
            await shell.openExternal("https://github.com/MadGapun/CAMWOSA/blob/main/docs/wiki/Home.md");
          },
        },
        { label: "Bug melden",
          click: async () => {
            const { shell } = await import("electron");
            await shell.openExternal("https://github.com/MadGapun/CAMWOSA/issues/new");
          },
        },
      ],
    },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

ipcMain.handle("backend:url", () => backendUrl());

// Smoke-Test: nach 8s den DOM-Status in stdout printen damit externe
// Tests (CI, lokales pack-portable.ps1) verifizieren koennen dass nicht
// nur Backend laeuft sondern auch UI gerendert wurde.
function startRendererSmoke(): void {
  setTimeout(async () => {
    if (!mainWindow) return;
    try {
      const r = await mainWindow.webContents.executeJavaScript(`
        ({
          url: window.location.href,
          bodyLen: document.body?.innerHTML?.length || 0,
          rootChildren: document.getElementById('root')?.children?.length || 0,
          aside: document.querySelectorAll('aside, nav').length,
        })
      `);
      console.log(`[smoke] dom url=${r.url} body=${r.bodyLen}B rootChildren=${r.rootChildren} aside=${r.aside}`);
    } catch (e) {
      console.log(`[smoke] dom-eval failed: ${e}`);
    }
  }, 8000);
}

app.whenReady().then(async () => {
  await startBackend();
  setupMenu();
  await createWindow();
  void setupAutoUpdater();
  startRendererSmoke();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      void createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("will-quit", async () => {
  await stopBackend();
});

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

  // Im Dev-Modus: Vite-Server. Im Prod: gebautes Frontend.
  if (process.env.CAMWOSA_DEV === "1") {
    await mainWindow.loadURL("http://localhost:5173");
    mainWindow.webContents.openDevTools();
  } else {
    await mainWindow.loadFile(path.join(__dirname, "../../frontend/dist/index.html"));
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

app.whenReady().then(async () => {
  await startBackend();
  setupMenu();
  await createWindow();

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

/**
 * Electron Preload-Skript.
 * Stellt der Renderer-UI eine sichere `window.camwosa`-API bereit.
 */

import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("camwosa", {
  backendUrl: () => ipcRenderer.invoke("backend:url"),

  onMenu: (channel: string, handler: (...args: unknown[]) => void) => {
    const allowedChannels = [
      "menu:projekt-neu",
      "menu:projekt-oeffnen",
      "menu:speichern",
      "menu:speichern-als",
      "menu:dxf-import",
      "menu:stl-import",
    ];
    if (!allowedChannels.includes(channel)) return;
    ipcRenderer.on(channel, (_e, ...args) => handler(...args));
  },
});

declare global {
  interface Window {
    camwosa: {
      backendUrl: () => Promise<string>;
      onMenu: (channel: string, handler: (...args: unknown[]) => void) => void;
    };
  }
}

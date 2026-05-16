# Auto-Updater

> **Status:** 🟨 Code-Stub vorhanden (electron-updater als Dep), Aktivierung haengt am ersten Release.

## Konzept

`electron-updater` prueft beim App-Start GitHub-Releases. Wenn neuere Version vorhanden:
- Download im Hintergrund
- User wird im UI gefragt ob installieren
- Bei „Ja": App neu starten, Update wird angewendet

## Konfiguration

`electron/package.json` → `build`:

```json
"publish": {
  "provider": "github",
  "owner": "MadGapun",
  "repo": "CAMWOSA"
}
```

Im Main-Process (`electron/src/main.ts`):

```ts
import { autoUpdater } from "electron-updater";

app.whenReady().then(() => {
  autoUpdater.checkForUpdatesAndNotify();
});
```

(Wird in `electron/src/main.ts` ergaenzt sobald der erste Release-Tag erstellt ist.)

## Verwandt

- [Installer](Installer)
- [CI-CD](CI-CD)
- [Electron-App](Electron-App)

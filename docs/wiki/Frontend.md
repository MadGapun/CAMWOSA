# Frontend

> **Status:** ✅ Skelett (Vite, React 19, TS, Tailwind, Routing, i18n, State, Komponenten, Views).
> **Code:** [frontend/src/](../../frontend/src/)

React-19-Frontend in TypeScript, gebaut mit Vite. Wird im Electron-Renderer geladen.

## Tech-Stack

| Technologie | Zweck |
|-------------|-------|
| React 19 | UI-Framework |
| Vite | Build/Dev-Server |
| TypeScript | Typsicherheit |
| Tailwind CSS | Styling |
| zustand | State Management |
| react-router-dom | Client-Side-Routing |
| i18next | Internationalisierung |
| axios | API-Client |
| Konva (react-konva) | 2D-Canvas (Toolpath-Vorschau, Zeichnen) |
| Three.js (react-three-fiber) | 3D-Simulation |
| Monaco Editor | G-Code-Editor |

## Struktur

```
frontend/
├── index.html
├── vite.config.ts
├── tailwind.config.js
└── src/
    ├── main.tsx                 # Einstiegspunkt
    ├── App.tsx                  # Layout + Routes
    ├── i18n.ts                  # i18next-Setup
    ├── api/
    │   └── client.ts            # Axios + typisierte Endpoints
    ├── state/
    │   └── store.ts             # zustand-Store
    ├── locales/
    │   └── de.json              # DE-Translations
    ├── components/
    │   ├── Sidebar.tsx
    │   ├── Topbar.tsx
    │   └── StatusBar.tsx
    ├── views/                   # Routen-Views
    │   ├── ProjektView.tsx
    │   ├── MaschinenView.tsx
    │   ├── WerkzeugeView.tsx
    │   ├── MaterialienView.tsx
    │   ├── OperationenView.tsx
    │   ├── PreviewView.tsx
    │   ├── GCodeEditorView.tsx
    │   ├── WorkflowView.tsx
    │   ├── NestingView.tsx
    │   └── EinstellungenView.tsx
    └── styles/
        └── index.css            # Tailwind + Globale Styles
```

## Routen

| URL | Komponente | Status |
|-----|-----------|--------|
| `/projekt` | ProjektView | ✅ Skelett (Maschinen-Auswahl) |
| `/maschinen` | MaschinenView | ✅ Liste mit Details |
| `/werkzeuge` | WerkzeugeView | ✅ Tabelle |
| `/materialien` | MaterialienView | ✅ Gruppiert nach Kategorie |
| `/operationen` | OperationenView | ⬜ Stub — Backend bereit |
| `/preview` | PreviewView | 🟨 Konva-Setup mit Beispiel-Daten |
| `/editor` | GCodeEditorView | 🟨 Monaco eingebunden, Live-Sync folgt |
| `/workflow` | WorkflowView | ⬜ Stub — Backend bereit |
| `/nesting` | NestingView | ✅ Funktional (Backend-Integration) |
| `/einstellungen` | EinstellungenView | ⬜ Stub |

## State Management

Globaler `useAppStore` (zustand) haelt:
- `backendOk` — Backend erreichbar
- `maschinen`, `werkzeuge`, `materialien` — Stammdaten
- `aktiveMaschineId` — Auswahl im Projekt
- `aktivesProjekt` — geladenes Projekt-JSON

Stammdaten werden alle 5 Sekunden vom Backend nachgeladen (StatusBar-Polling).

## i18n

- Sprache: **Deutsch first** (`de.json`).
- Translation-Keys auf Deutsch: `t("operation.tasche.titel")`.
- EN folgt nach Stabilisierung der DE-Begriffe (Phase E1).

## API-Client

`src/api/client.ts` ist eine duenne Schicht ueber axios. Beispiel:

```ts
import { camwosaApi } from "./api/client";

const maschinen = await camwosaApi.maschinen();
const fs = await camwosaApi.feedsBerechnen(
  "genmitsu_proverxl_4030_v2",
  "schaft_6mm_2s_hm",
  "buche_massiv",
);
```

## Styling

Tailwind mit eigenen `camwosa-*`-Farben:

| Token | Farbe |
|-------|-------|
| `camwosa-bg` | #1a1a1a (Hintergrund) |
| `camwosa-surface` | #252525 (Panels) |
| `camwosa-accent` | #ff6b00 (Orange — Akzent) |
| `camwosa-warn` | #ffc107 (Gelb) |
| `camwosa-danger` | #dc3545 (Rot) |
| `camwosa-ok` | #28a745 (Gruen) |
| `camwosa-text` | #e8e8e8 |
| `camwosa-muted` | #888888 |

## Naechste Iteration

- Operationen-Editor mit allen Parametern aus dem Backend
- Live-Toolpath-Preview mit Daten vom Backend
- Multi-Setup-Editor mit Foto-Slot
- Sicherheits-Panel (mit Klick-zur-Stelle in Vorschau)
- G-Code-Mode fuer Monaco mit Befehlsbibliothek
- Integriertes Zeichnen (Issue #7)

## Verwandt

- [Electron-App](Electron-App.md)
- [Architektur](Architektur.md)
- [API](API.md)

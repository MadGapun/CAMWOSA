# Projekt-Verwaltung (Frontend)

> **Status:** ✅ Backend (POST `/api/projects/new` · `/save` · `/load`) + Frontend-Panel mit Neu/Oeffnen/Speichern/Speichern-als + Wire-Up zu Variante-/Workflow-/Rohmaterial-/AppStore.
> **Code:** [frontend/src/views/ProjektView.tsx](../../frontend/src/views/ProjektView.tsx) · [state/projektIO.ts](../../frontend/src/state/projektIO.ts) · [state/projektStore.ts](../../frontend/src/state/projektStore.ts)
> **Backend:** [api/endpoints/projects.py](../../backend/camwosa/api/endpoints/projects.py) · [project/io.py](../../backend/camwosa/project/io.py)
> **Tests:** [test_projects_api.py](../../backend/tests/api/test_projects_api.py) (5) · [test_io.py](../../backend/tests/project/test_io.py) (8)
> **Master-Plan-Position:** [D4](Master-Plan.md)

## Worum es geht

Ein Projekt zu speichern + laden gehoert zu den absoluten Pflicht-Workflows.
CAMWOSA speichert Projekte als **`.cwp`-Container** (ZIP) der enthaelt:

- `manifest.json` — Projekt-Metadaten + Maschine + Stammdaten-Snapshot
- `varianten/*.json` — pro Variante: rohmaterial + setups + operationen
- `geometrien/*.dxf|.stl` — eingebettete CAD-Dateien
- `fotos/*.png` — Setup-Fotos (Master-Plan D18)

Geladen wird das gleiche Format, beim Laden werden alle Stores
zuruecksetzt + die aktive Variante in die Working-Stores geladen
(siehe [Varianten](Varianten.md)).

## Bedienung

Im `ProjektView` (Sidebar → Projekt) zeigt das Persistenz-Panel:

| Button | Was passiert |
|--------|--------------|
| **Neu** | Promp nach Name → Stores werden geleert, Default-Variante angelegt. Wenn `dirty`: Bestaetigung noetig. |
| **Oeffnen** | File-Picker fuer `.cwp` → Backend laed das ZIP → Stores werden komplett ersetzt. |
| **Speichern** | Schreibt aktuellen Zustand aller Stores in den Variante-Snapshot und sendet das CWPProjekt-JSON an `/api/projects/save`. Browser laed `.cwp`-Datei runter. |
| **Speichern als** | Wie Speichern, fragt aber vorher nach neuem Dateinamen. |

Zusatz-UI:
- **Autor-Feld** — landet in `metadaten.autor`
- **Dirty-Indikator** — ● roter Punkt wenn ungespeicherte Aenderungen
- **Zuletzt geoeffnet** — Liste aus `localStorage` (max 8 Eintraege)
- **Status-Meldungen** — gruene Erfolgs- / rote Fehler-Anzeige

## Architektur

```
┌─────────────────────┐
│ ProjektView (UI)    │  ← Buttons + File-Picker
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ projektIO.ts        │  ← Bridge:
│  - projektNeu()     │     Stores ↔ CWPProjekt-Payload
│  - projektSpeichern │
│  - projektLaden     │
└──────────┬──────────┘
           │
           ├─► useAppStore (geometrien)
           ├─► useWorkflowStore (setups)
           ├─► useRohmaterialStore (rohmaterial)
           ├─► useVarianteStore (varianten-snapshots)
           └─► useProjektStore (dateiname, autor, dirty)
                          │
                          ▼
           POST /api/projects/{new,save,load}
                          │
                          ▼
              project/io.py → .cwp-ZIP
```

## Beim Laden

Die `projektLaden(datei)`-Funktion:

1. Sendet Datei an `POST /api/projects/load`
2. Bekommt CWPProjekt-JSON zurueck
3. Setzt aktive Maschine (sonst stimmen Werkzeug-/Spindel-IDs nicht)
4. Geometrien werden ersetzt
5. `useVarianteStore.init(varianten, aktive_id)` ruft intern
   `snapshotInStoresLaden()` fuer die aktive Variante — das aktiviert
   rohmaterial, operationen und setups in den Working-Stores
6. `useProjektStore` setzt dateiname, autor, dirty=false
7. zuletzt-geoeffnet-Liste wird aktualisiert (localStorage)

## Beim Speichern

`projektPayloadAusStores()` baut den vollstaendigen CWP-Payload:

1. `exportiereVarianten()` schreibt aktuelle Working-Stores in den aktiven
   Variante-Snapshot — andere Varianten bleiben unangetastet
2. Alle Stammdaten-Snapshots (werkzeuge, materialien) werden eingefroren
3. Metadaten (name, autor, jetzt-Timestamp) erzeugt
4. POST `/api/projects/save` mit JSON
5. Antwort = .cwp-Blob → Browser-Download via `<a download>`

## Bekannte Einschraenkungen

- **Browser-Download statt Save-As-Dialog**: Der Browser muss `.cwp` in den
  Standard-Download-Ordner ablegen — der User hat keine direkte Kontrolle
  ueber den Pfad. In Electron koennte das durch `dialog.showSaveDialog`
  ersetzt werden — kommt mit der Electron-File-Bridge spaeter.
- **Kein Auto-Save**: Manuelles Speichern noetig. Der `dirty`-Indikator
  hilft erinnern. Auto-Save ist Master-Plan-Position A18 (Backend-Crash-Recovery).
- **Embedded Geometrien**: Geometrien werden im Payload komplett mitgesendet
  — bei sehr grossen STLs kann das langsam werden. Das `.cwp`-ZIP komprimiert
  aber gut.

## Verwandt

- [Projekt-Format](Projekt-Format.md) — `.cwp`-ZIP-Container
- [Varianten](Varianten.md) — pro-Projekt-Varianten
- [Workflow-Modul](Workflow-Modul.md) — Setups je Variante

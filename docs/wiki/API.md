# Flask-API

> **Status:** ✅ Phase 1 (Maschinen, Werkzeuge, Material, DXF, Operations, Feeds, Safety, Nesting, Projekt, Postprozessoren). Workflow + STL kommen.
> **Code:** [backend/camwosa/api/](../../backend/camwosa/api/) · **Tests:** [backend/tests/api/test_app.py](../../backend/tests/api/test_app.py)

Die Flask-API ist die **Single Source of Truth** zwischen UI/MCP und Backend. Sie laeuft **nur auf localhost** (127.0.0.1) — kein externer Zugriff.

## Starten

```bash
cd backend
camwosa-backend
# bindet auf http://127.0.0.1:8765
```

Konfiguration via Environment:
- `CAMWOSA_BACKEND_PORT` (Default 8765)
- `CAMWOSA_DEBUG=1` schaltet Flask-Debug-Modus ein

## Endpoints

### Health
- `GET /health` -> `{status, version}`

### Maschinen
- `GET  /api/machines/` -> Liste
- `GET  /api/machines/<id>` -> Details
- `POST /api/machines/validate` -> Profil-Validierung

### Werkzeuge
- `GET  /api/tools/`
- `GET  /api/tools/<id>`
- `POST /api/tools/validate`

### Materialien
- `GET  /api/materials/`
- `GET  /api/materials/<id>`

### DXF
- `POST /api/dxf/import` (multipart/form-data, Datei-Feld `datei`)

### Feeds & Speeds
- `POST /api/feeds/berechnen` (`maschine_id`, `werkzeug_id`, `material_id`, `rpm_wunsch?`)

### Operations
- `POST /api/operations/kontur`
- `POST /api/operations/tasche`
- `POST /api/operations/bohren`
- `POST /api/operations/gravur`
- `POST /api/operations/postprocess` (Toolpaths -> G-Code)

### Sicherheits-Checks
- `POST /api/safety/check` (Toolpath + Maschine + Werkzeug)

### Nesting
- `POST /api/nesting/run`

### Projekte
- `POST /api/projects/new`
- `POST /api/projects/save`
- `POST /api/projects/load` (multipart)

### Postprozessoren
- `GET /api/postprocessors/`

## Konventionen

- **JSON in/out** (UTF-8, Umlaute korrekt)
- **Statuscodes:** 200 OK, 404 Nicht gefunden, 422 Validierung fehlgeschlagen
- **Fehler-Format:** `{"fehler": "..."}`

## Sicherheit

- Bindet **ausschliesslich** auf 127.0.0.1 — niemals 0.0.0.0
- Keine Authentifizierung noetig (lokales Tool, ein Nutzer)
- CORS nur fuer `localhost` und `app://` (Electron)
- Max-Upload-Groesse: 200 MB (fuer STL-Dateien)

## Verwandt

- [MCP-Server](MCP-Server.md)
- [Architektur](Architektur.md)
- [Datenmodell](Datenmodell.md)

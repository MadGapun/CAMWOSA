# Flask-API

> **Status:** ✅ Voll aufgebaut + OpenAPI-3.1-Spec (Master-Plan B3).
> **Code:** [backend/camwosa/api/](../../backend/camwosa/api/) · **Tests:** [backend/tests/api/](../../backend/tests/api/)
> **OpenAPI-Spec:** `GET /api/openapi.json` · **Swagger-UI:** `GET /api/docs`

Die Flask-API ist die **Single Source of Truth** zwischen UI/MCP und Backend. Sie laeuft **nur auf localhost** (127.0.0.1) — kein externer Zugriff.

## Interaktive Doku (OpenAPI / Swagger)

Wer alle Endpoints durchklicken + ausprobieren will:

```
http://localhost:8765/api/docs
```

Das ist eine Swagger-UI-Seite, die `/api/openapi.json` rendert. Funktioniert
ohne Internet nicht (Assets vom CDN) — bei Offline-Betrieb stattdessen die
Spec einfach in [editor.swagger.io](https://editor.swagger.io/) einfuegen:

```bash
curl http://localhost:8765/api/openapi.json > camwosa-api.json
# oder als YAML (wenn PyYAML installiert):
curl http://localhost:8765/api/openapi.yaml
```

Die Spec wird **automatisch** aus den Flask-Routen + den Funktions-Docstrings
generiert ([api/openapi.py](../../backend/camwosa/api/openapi.py)) — jeder
neue Endpoint mit Docstring landet automatisch in der Spec, ohne dass man
Schema-Decorators verteilen muss. Wer mehr Detail will, kann pro Endpoint
in ``openapi_extra`` ein eigenes Dict registrieren, das in den Path-Eintrag
eingemischt wird.

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

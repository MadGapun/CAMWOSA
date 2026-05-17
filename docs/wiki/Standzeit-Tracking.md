# Werkzeug-Standzeit-Tracking

> **Status:** ✅ Backend + API + Frontend (Progress-Bar in WerkzeugeView).
> **Code:** [backend/camwosa/db/standzeit.py](../../backend/camwosa/db/standzeit.py) · [frontend/src/views/WerkzeugeView.tsx](../../frontend/src/views/WerkzeugeView.tsx) (Komponente `StandzeitZelle`)

## Frontend-Anzeige

In WerkzeugeView wird pro Werkzeug eine **farbige Progress-Bar** angezeigt:

- 🟢 Grün: < 80% genutzt
- 🟡 Gelb: 80–100% (Warnung)
- 🔴 Rot: ≥ 100% (Werkzeug ueberzogen, Austausch faellig)

Hover-Tooltip zeigt die Rohdaten („12.5 / 60 min"). Der `↺`-Button setzt die
Standzeit zurueck (nach Werkzeugwechsel oder Schaerfung) — mit Confirm-Dialog
um Versehen zu verhindern.

Werkzeuge ohne `standzeit_max_minuten` zeigen `—`.

Verfolgt pro Werkzeug die kumulierten Schnitt-Minuten und warnt wenn die `standzeit_max_minuten` aus dem Werkzeug-Profil ueberschritten wird.

## Werkzeug-Profil

```python
class Werkzeug:
    standzeit_max_minuten: float | None  # Erfahrungswert
```

## API

| Endpoint | Zweck |
|----------|-------|
| `GET /api/standzeit/` | Status aller Werkzeuge (genutzt, max, prozent, warnung, kritisch) |
| `POST /api/standzeit/addiere` | `{werkzeug_id, minuten}` — addiert nach Bearbeitung |
| `POST /api/standzeit/reset/<werkzeug_id>` | Setzt auf 0 (nach Werkzeug-Schaerfung) |

## Status-Logik

| Bedingung | Status |
|-----------|--------|
| genutzt / max < 80% | OK |
| 80% ≤ ... < 100% | **warnung** (gelb) |
| ≥ 100% | **kritisch** (rot) — Werkzeug wechseln! |

## Persistenz

`data/standzeit.json`:

```json
{
  "schaft_6mm_2s_hm": 145.5,
  "vbit_60grad": 23.0
}
```

Override via Env: `CAMWOSA_STANDZEIT_FILE=/pfad/zur/datei.json`.

## Workflow

1. **Beim G-Code-Export** geschaetzte Bearbeitungszeit pro Werkzeug aus
   Toolpath-Statistik ermitteln.
2. Nach jedem Job: `POST /api/standzeit/addiere` mit den gefraesten Minuten.
3. Beim Werkzeug-Wechsel (M0-Pause): UI zeigt Warnung wenn Werkzeug ueber 80%.

## Verwandt

- [Datenmodell](Datenmodell)
- [Werkzeug-Bibliothek](Werkzeug-Bibliothek)
- [Workflow-Modul](Workflow-Modul)

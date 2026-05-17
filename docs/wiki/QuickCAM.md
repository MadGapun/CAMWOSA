# Quick-CAM — Schnellstart fuer einfache Aufgaben

> **Status:** ✅ Backend (Templates + API) + Frontend-View.
> **Code:** [backend/camwosa/quickcam/](../../backend/camwosa/quickcam/) · **API:** [backend/camwosa/api/endpoints/quickcam.py](../../backend/camwosa/api/endpoints/quickcam.py) · **View:** [frontend/src/views/QuickStartView.tsx](../../frontend/src/views/QuickStartView.tsx) · **Tests:** [test_templates.py](../../backend/tests/quickcam/test_templates.py)

QuickCAM ist der direkte Weg vom App-Start zum lauffaehigen G-Code. Statt einem leeren Projekt + manueller Konfiguration:

1. **Vorlage waehlen** (Tasche, Schriftzug, Bohrloch-Raster, Kontur)
2. **Maße eingeben** (Breite, Tiefe, Stepdown ...)
3. **Maschine/Werkzeug/Material** in den Drop-Downs setzen
4. **Projekt erzeugen** — Werte werden automatisch aus dem passenden CuttingPreset gezogen

Ziel: unter 60 Sekunden zum nutzbaren Projekt.

## Mitgelieferte Templates

| ID | Operation | Eingaben |
|----|-----------|----------|
| `tasche_rechteckig` | Tasche | Breite, Hoehe, Tiefe, Stepdown, Stepover |
| `gravur_text` | Gravur | Text, Schriftgroesse, Tiefe, Position, Schriftart |
| `bohrloch_raster` | Bohren | Spalten, Zeilen, Abstand X/Y, Tiefe |
| `kontur_ausschneiden` | Kontur | Tiefe, Stepdown, Tabs (Anzahl + Hoehe) |

Neue Templates werden im Backend in [templates.py](../../backend/camwosa/quickcam/templates.py) eingetragen — kein Frontend-Change noetig, das Frontend rendert sie generisch.

## API

| Endpoint | Zweck |
|----------|-------|
| `GET /api/quickcam/templates` | Liste aller Templates inkl. Parameter-Schemas |
| `GET /api/quickcam/templates/<id>` | Details |
| `POST /api/quickcam/erzeugen` | Erzeugt aus Template + Eingaben ein lauffaehiges `CWPProjekt` |

Body fuer `erzeugen`:
```json
{
  "template_id": "tasche_rechteckig",
  "eingaben": {"breite_mm": 80, "hoehe_mm": 40, "tiefe_mm": 5},
  "maschine_id": "genmitsu_proverxl_4030_v2",
  "werkzeug_id": "schaft_6mm_2s_hm",
  "material_id": "buche_massiv",
  "projekt_name": "Tasche Schluesselbrett"
}
```

Antwort: vollstaendiges `{ projekt: CWPProjekt }`. Der Frontend kann es direkt in den Store laden.

## Wie die Werte zusammenkommen

```
Template-Extras (Strategie, Tiefe, ...)
   +
CuttingPreset (RPM, Vorschub, Plunge, Stepdown — aus Material+Werkzeug)
   +
Werkzeug-Defaults
   ↓
fertiger OperationParameter
```

Wenn kein CuttingPreset existiert, wird auf Material.presets[] (Legacy) zurueckgegriffen, dann auf eingebaute Defaults.

## Verwandt

- [CuttingPreset](CuttingPreset)
- [ArbeitsSchritt](ArbeitsSchritt)
- [Workflow-Modul](Workflow-Modul)

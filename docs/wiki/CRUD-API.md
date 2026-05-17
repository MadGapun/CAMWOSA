# CRUD-API fuer Stammdaten

> **Status:** ✅ POST/PUT/DELETE fuer Werkzeuge, Materialien, Spindeln, CuttingPresets.
> **Code:** [tools.py](../../backend/camwosa/api/endpoints/tools.py), [materials.py](../../backend/camwosa/api/endpoints/materials.py), [spindles.py](../../backend/camwosa/api/endpoints/spindles.py), [cutting_presets.py](../../backend/camwosa/api/endpoints/cutting_presets.py)
> **Persistierung:** [backend/camwosa/db/crud.py](../../backend/camwosa/db/crud.py)
> **Tests:** [test_crud_stammdaten.py](../../backend/tests/api/test_crud_stammdaten.py)

Alle Stammdaten sind ueber die REST-API editierbar — keine Hardcodes mehr. UI und MCP nutzen denselben Pfad.

## Ablage-Konvention

```
data/
  tools/
    standard.json          ← Liste mehrerer Default-Werkzeuge (read-only durch DELETE)
    user_neues_tool.json   ← Einzeldatei (User-Override / Neuanlage)
  materials/
    holz.json              ← Liste
    user_mdf_22.json       ← Einzeldatei
  spindles/
    standard.json
  cutting_presets/
    buche_schaft6mm_varianten.json
    user_eigenes_preset.json
```

Beim Laden gewinnt eine ``<id>.json``-Einzeldatei gegenueber Eintraegen in Sammel-Dateien (Dedup ueber ID). So koennen User Defaults uebersteuern, ohne die mitgelieferten Sammel-Files zu mutieren.

## Endpoints

| Methode | Pfad | Zweck |
|---------|------|-------|
| `GET` | `/api/tools/` | Liste |
| `GET` | `/api/tools/<id>` | Details |
| `POST` | `/api/tools/` | Neu anlegen |
| `PUT` | `/api/tools/<id>` | Aktualisieren |
| `DELETE` | `/api/tools/<id>` | Loeschen (nur User-Eintraege, sonst 409) |
| `POST` | `/api/tools/validate` | Validierung ohne speichern |
| `GET` | `/api/tools/<id>/export` | Bundle-Export |
| `POST` | `/api/tools/import` | Bundle-Import |
| `POST` | `/api/tools/helper/v-bit-spitzendurchmesser` | Smart-Hilfe |
| `POST` | `/api/tools/helper/v-bit-winkel` | Smart-Hilfe |

Identisches Schema fuer:
- `/api/materials/`
- `/api/spindles/`
- `/api/cutting-presets/`

## Loeschen — 409 statt 200

Wenn man versucht einen Default-Eintrag (aus Sammel-Datei) zu loeschen, kommt **HTTP 409** mit der Empfehlung: lege einen User-Override mit gleicher ID an, um die Defaults zu uebersteuern. So bleibt das Repo immer in einem reproduzierbaren Zustand.

## Smart-Helpers (UI-Unterstuetzung)

Der Werkzeug-Editor braucht beim Erfassen Gravurstichel/V-Bit-Werte. Zwei Helfer:

### `POST /api/tools/helper/v-bit-spitzendurchmesser`

Body:
```json
{ "spitzenwinkel_grad": 60, "schneidlaenge_mm": 10, "durchmesser_max_mm": 12 }
```
Antwort:
```json
{ "spitzendurchmesser_mm": 0.0 }
```
Bei flachem Konus passt die Spitze auf 0 — bei steilem Konus errechnet sich der verbleibende Spitzen-Durchmesser.

### `POST /api/tools/helper/v-bit-winkel`

Body:
```json
{ "spitzendurchmesser_mm": 0.3, "durchmesser_max_mm": 3.175, "schneidlaenge_mm": 6.0 }
```
Antwort:
```json
{ "spitzenwinkel_grad": 26.86... }
```
Hilfreich beim Erfassen von Gravursticheln, wo der Hersteller nur Spitze+Schaft+Schneidlaenge dokumentiert.

## Verwandt

- [Werkzeug-Modell](Werkzeug-Modell)
- [CuttingPreset](CuttingPreset)
- [Bundle-Sharing-Pattern](Bundle-Sharing-Pattern)

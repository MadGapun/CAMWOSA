# CuttingPreset — Schnittparameter als Top-Level-Entitaet

> **Status:** ✅ Datenmodell + Loader + Migration + CRUD-API.
> **Code:** [backend/camwosa/db/cutting_presets.py](../../backend/camwosa/db/cutting_presets.py) · **API:** [backend/camwosa/api/endpoints/cutting_presets.py](../../backend/camwosa/api/endpoints/cutting_presets.py) · **Tests:** [test_cutting_presets.py](../../backend/tests/db/test_cutting_presets.py), [test_cutting_presets_api.py](../../backend/tests/api/test_cutting_presets_api.py)

CuttingPreset speichert Schnittparameter (RPM, Vorschub, Plunge, Stepdown, Stepover) fuer eine bestimmte **Werkzeug-Material-Operation**-Kombination. Vorher waren diese Werte in `Material.presets[]` eingebettet — das ist ab v2 ueberholt.

## Warum eine eigene Entitaet?

Der Industriestandard (Fusion 360 „Cutting Data", FreeCAD-Path-„Tool Controller", EstlCAM-Werkzeug-Tabelle) ist:

- Schnittparameter sind **eine separate Tabelle**, nicht im Material verschachtelt
- Lookup geht ueber `(material, werkzeug [, operation])`
- Es kann mehrere Varianten geben (Schruppen vs. Schlichten)
- User koennen einzelne Presets teilen, ohne ganze Materialien zu uebertragen

## Datenmodell

```python
class CuttingPreset:
    id: str                          # z.B. "buche__schaft_6mm__schlichten"
    name: str                        # Anzeigename
    material_id: str
    werkzeug_id: str
    operation_typ: OperationsTyp     # generic | kontur | tasche | gravur | bohren | relief | schruppen | schlichten

    rpm: float
    vorschub: float                  # mm/min
    plunge: float                    # mm/min
    stepdown: float                  # mm pro Z-Pass
    stepover_prozent: float          # 0..100

    kuehlung: str                    # luft / nebel / spray / keine
    rampen_winkel_grad: float | None
    quelle: str                      # user | hersteller | community | legacy-migration
    notizen: str
```

## Lookup-Reihenfolge

`finde_preset(material_id, werkzeug_id, operation_typ)`:

1. Exakter Match auf alle drei
2. Fallback auf `GENERIC` fuer dieselbe `(material_id, werkzeug_id)`
3. `None`

So koennen Operation-spezifische Presets bestehende „Standard"-Presets ueberschreiben — und Operations ohne speziellen Eintrag fallen sauber auf das Generic-Preset zurueck.

## Migration aus Material.presets[]

Bestehende `Material.presets[]`-Eintraege werden beim Laden automatisch zu CuttingPresets migriert. ID-Schema:

```
{material_id}__{werkzeug_id}__generic
```

Damit kollidieren Migrations-Presets nicht mit Datei-basierten Presets — und sobald ein User in der UI ein Preset speichert, ueberschreibt das den Migrations-Eintrag.

`lade_cutting_presets(include_legacy=False)` schaltet die Migration ab — sinnvoll wenn Material.presets[] vollstaendig migriert wurde.

## API

| Endpoint | Zweck |
|----------|-------|
| `GET /api/cutting-presets/` | Liste (Filter: `material_id`, `werkzeug_id`, `operation_typ`) |
| `GET /api/cutting-presets/<id>` | Details |
| `POST /api/cutting-presets/lookup` | Beste Uebereinstimmung suchen (mit Generic-Fallback) |
| `POST /api/cutting-presets/` | Neu anlegen |
| `PUT /api/cutting-presets/<id>` | Aktualisieren |
| `DELETE /api/cutting-presets/<id>` | Loeschen (nur Datei-basierte, keine Legacy) |
| `GET /api/cutting-presets/<id>/export` | Bundle-Export (Community-Sharing) |
| `POST /api/cutting-presets/import` | Bundle-Import |

## Mitgelieferte Beispiele

[data/cutting_presets/buche_schaft6mm_varianten.json](../../data/cutting_presets/buche_schaft6mm_varianten.json) zeigt zwei Varianten fuer Buche + 6mm-Fraeser:

| ID | Operation | RPM | Vorschub | Stepdown | Stepover |
|----|-----------|-----|----------|----------|----------|
| `buche__schaft_6mm_2s_hm__schruppen` | Schruppen | 18000 | 2400 | 3.0 mm | 50 % |
| `buche__schaft_6mm_2s_hm__schlichten` | Schlichten | 20000 | 1200 | 0.5 mm | 15 % |

## Override-Hierarchie

Im Operations-Solver (siehe [Per-Feature-Override](Per-Feature-Override)) zaehlt CuttingPreset als eine Quelle:

```
override   >   cutting_preset (exakt)   >   cutting_preset (generic)   >   werkzeug-default   >   fallback
```

## Verwandt

- [Werkzeug-Modell](Werkzeug-Modell)
- [Material-Modell](Material-Modell)
- [Per-Feature-Override](Per-Feature-Override)

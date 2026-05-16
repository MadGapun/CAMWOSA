# Rotary-Profil-System

> **Status:** ✅ Datenmodell + Defaults + API.
> **Code:** [backend/camwosa/db/rotary.py](../../backend/camwosa/db/rotary.py) · **Tests:** [backend/tests/db/test_rotary.py](../../backend/tests/db/test_rotary.py)

Konfigurierbare Rotary-Hardware (4. Achse) fuer GRBL-Maschinen. Ein Maschinenprofil kann mehrere Rotary-Konfigurationen haben (z.B. „Mit Reitstock" / „Fliegend").

## Warum eigene Profile?

Der Rotary-Aufsatz hat eigene Eigenschaften, die unabhaengig von der Maschine sind:
- **Spannfutter:** Backen-Anzahl, max./min. Werkstueck-Durchmesser
- **Reitstock:** ja/nein, Pinole-Hub
- **Max. Werkstueck-Laenge:** bei Reitstock oder fliegend
- **Durchschiebbar:** Kann das Werkstueck durchs Spannfutter geschoben werden (fuer lange Werkstuecke in mehreren Setups)
- **GRBL-Settings:** `$101` (steps/grad), `$131` (Y-Limit), CNCjs-Macros

So koennen andere User mit anderer Rotary-Hardware (z.B. mit / ohne Reitstock, anderes Spannfutter) die App ohne Code-Aenderung benutzen.

## Datenmodell

```python
class RotaryProfil:
    id: str
    name: str
    spannfutter_backen_anzahl: int
    spannfutter_max_durchmesser_mm: float
    spannfutter_min_durchmesser_mm: float
    hat_reitstock: bool
    reitstock_verstellbar_mm: float | None
    max_werkstueck_laenge_mm: float
    durchschiebbar: bool
    grbl_y_steps_pro_grad: float | None  # z.B. 88.889
    grbl_y_limit_aufheben: bool          # $131=9999
    cncjs_macro_ein: str | None
    cncjs_macro_aus: str | None
```

## Rohmaterial-Formen (im Rotary)

```python
class RotaryRohmaterial:
    form: RotaryRohmaterialForm  # rund | rechteckig | modell_3d
    durchmesser_mm: float | None   # bei rund
    laenge_mm: float
    breite_mm: float | None        # bei rechteckig
    hoehe_mm: float | None         # bei rechteckig
    stl_pfad: str | None           # bei modell_3d
    material_id: str

    nullpunkt_referenz: RotaryNullpunktReferenz
    nullpunkt_x_versatz_mm: float
```

## Nullpunkt-Optionen

| Referenz | Bedeutung |
|----------|-----------|
| `mitte_drehachse` | Z=0 sitzt auf der Drehachse-Mitte |
| `oberkante_rohmaterial` | Z=0 sitzt auf dem hoechsten Punkt des Rohmaterials |
| `spannfutter_backe` | X=0 sitzt an der Backen-Vorderseite |
| `reitstock` | X=0 sitzt am Reitstock |

## Mitgelieferte Profile

Das ProVerXL-Profil enthaelt zwei Rotary-Konfigurationen ([data/rotary/generic_4achs_3backen.json](../../data/rotary/generic_4achs_3backen.json)):

| ID | Name | Reitstock | Max. Laenge |
|----|------|-----------|-------------|
| `generic_4achs_3backen_50mm` | Mit Reitstock | ✅ | 300 mm |
| `generic_4achs_3backen_50mm_fliegend` | Fliegend | ❌ | 100 mm |

Beide sind durchschiebbar — fuer Werkstuecke laenger als der Arbeitsraum kommt die Setup-Pause `werkstueck_verschieben` ins Spiel.

## API

| Endpoint | Zweck |
|----------|-------|
| `GET /api/rotary/profile` | Liste aller Profile |
| `GET /api/rotary/profile/<id>` | Details |
| `POST /api/rotary/profile/validate` | Profil-Validierung |
| `POST /api/rotary/rohmaterial/validate` | Rohmaterial validieren + effektiver Radius |
| `GET /api/rotary/profile/<id>/export` | Bundle-Export (Community-Sharing) |
| `POST /api/rotary/profile/import` | Bundle-Import |

## Neue Pause-Typen (Multi-Setup-Workflow)

- **`werkstueck_verschieben`** — fuer lange Werkstuecke die durchs Spannfutter geschoben werden
- **`spindel_wechsel`** — von OEM-Router zu Makita (oder umgekehrt)

## Verwandt

- [Maschinenprofil-Format](Maschinenprofil-Format)
- [Postprozessor-GRBL-Rotary](Postprozessor-GRBL-Rotary)
- [Workflow-Modul](Workflow-Modul)

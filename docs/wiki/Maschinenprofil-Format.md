# Maschinenprofil-Format

> **Status:** ✅ Schema v1 dokumentiert, Bundle-Export/Import produktiv.
> **Code:** [backend/camwosa/db/models.py](../../backend/camwosa/db/models.py) (Maschine-Klasse)

Eine Maschine ist eine JSON-Datei in `data/machines/`. Beim App-Start werden alle gefunden und in die Liste aufgenommen.

## Schema

```json
{
  "id": "genmitsu_proverxl_4030_v2",
  "name": "Genmitsu ProVerXL 4030 V2",
  "hersteller": "Genmitsu",
  "modell": "ProVerXL 4030 V2",
  "controller": "GRBL",
  "arbeitsraum": { "x": 400, "y": 400, "z": 110 },
  "max_vorschub": 3000,
  "sicherer_vorschub": 2000,
  "eilgang": 5000,
  "spindel_ids": ["genmitsu_router_710w", "makita_rt0700"],
  "aktive_spindel_id": "makita_rt0700",
  "spindel_typ": "manuell",
  "spindel_rpm_min": 10000,
  "spindel_rpm_max": 30000,
  "sicherheitshoehe": 5.0,
  "werkzeugwechsel_position": [0, 0, 100],
  "postprozessor": "grbl_genmitsu",
  "modi": ["standard_xyz", "rotary_y"],
  "aktiver_modus": "standard_xyz",
  "notizen": "..."
}
```

## Felder

| Feld | Typ | Pflicht | Anmerkung |
|------|-----|---------|-----------|
| `id` | string | ja | Eindeutig, snake_case |
| `name` | string | ja | Anzeigename |
| `hersteller`, `modell` | string | ja | |
| `controller` | enum | ja | `GRBL` / `Marlin` / `LinuxCNC` / `Mach3` / `Duet` / `Sonstige` |
| `arbeitsraum.x/y/z` | float | ja | mm |
| `max_vorschub` | float | ja | mm/min |
| `sicherer_vorschub` | float | ja | <= max_vorschub |
| `eilgang` | float | ja | mm/min G0 |
| `spindel_ids` | string[] | nein | IDs aus `data/spindles/` |
| `aktive_spindel_id` | string | nein | Eine aus `spindel_ids` |
| `spindel_typ` | enum | nein | Fallback wenn keine `spindel_ids` |
| `spindel_rpm_min/max` | float | nein | Inline-Fallback |
| `sicherheitshoehe` | float | nein | Default 5.0 |
| `werkzeugwechsel_position` | [x,y,z] | nein | Park fuer Werkzeugwechsel |
| `postprozessor` | string | nein | ID, Default `grbl_standard` |
| `modi` | enum[] | nein | `standard_xyz`, `rotary_y`, `rotary_x`, `laser`, `drag_knife` |
| `aktiver_modus` | enum | nein | Einer aus `modi`, Default `standard_xyz` |
| `notizen` | string | nein | Frei |

## Validierung

Beim Laden wird geprueft:
- `sicherer_vorschub <= max_vorschub`
- `spindel_rpm_max >= spindel_rpm_min`
- `aktive_spindel_id` muss in `spindel_ids` enthalten sein (wenn gesetzt)
- `aktiver_modus` muss in `modi` enthalten sein (wenn `modi` gesetzt)

## Schema-Versionen

| Version | Aenderungen |
|---------|-------------|
| **v1** (aktuell) | Initial. `spindel_ids` + `aktive_spindel_id` neu. Inline `spindel_*` bleiben als Fallback. |

## Bundle-Format

Fuer Sharing wird die Maschine inkl. Spindeln gebuendelt:

```json
{
  "schema_version": 1,
  "typ": "camwosa.machine_bundle",
  "maschine": { ... },
  "spindeln": [ {...}, {...} ]
}
```

Siehe `GET /api/machines/<id>/export` und `POST /api/machines/import`.

## Verzeichnis-Konvention

```
data/machines/
├── genmitsu_proverxl_4030_v2.json    # mitgeliefert
├── generic_grbl_3achs.json           # mitgeliefert
├── community/                        # User-Beitraege (PR-bar)
│   └── shapeoko_pro.json
└── user/                             # lokale, nicht gesharte Profile
    └── meine_maschine.json
```

`user/` ist in `.gitignore` ausgeschlossen — Privates bleibt privat.

## Beispiel-Profile

- **ProVerXL 4030 V2 (Markus)**: [data/machines/genmitsu_proverxl_4030_v2.json](../../data/machines/genmitsu_proverxl_4030_v2.json)
- **Generic GRBL**: [data/machines/generic_grbl_3achs.json](../../data/machines/generic_grbl_3achs.json)
- **PROVer 3018**: [data/machines/genmitsu_prover_3018.json](../../data/machines/genmitsu_prover_3018.json)

## Verwandt

- [Spindel](Spindel)
- [Datenmodell](Datenmodell)
- [Maschine-ProVerXL-4030-V2](Maschine-ProVerXL-4030-V2)
- [Postprozessor-GRBL](Postprozessor-GRBL)

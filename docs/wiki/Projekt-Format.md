# Projekt-Format (.cwp)

> **Status:** ✅ Speichern/Laden/Auto-Save implementiert. Crash-Recovery in Frontend-Phase.
> **Issue:** [#9](https://github.com/MadGapun/CAMWOSA/issues/9)
> **Code:** [backend/camwosa/project/](../../backend/camwosa/project/) · **Tests:** [backend/tests/project/test_io.py](../../backend/tests/project/test_io.py)

`.cwp` (CAMWOSA Project) ist ein ZIP-Container mit JSON-Manifest und eingebetteten Dateien.

## Container-Struktur

```
projekt.cwp  (ZIP)
├── manifest.json     # CWPProjekt als JSON
├── geometry/
│   ├── g1_input.dxf
│   └── g2_relief.stl
├── gcode/            # generierte G-Code-Dateien (optional)
│   ├── setup1.nc
│   └── setup2.nc
└── photos/           # Setup-Fotos (optional)
    └── setup1_aufspannung.jpg
```

## Manifest-Schema

```python
class CWPProjekt:
    schema_version: int                 # aktuell 1
    metadaten: ProjektMetadaten
    maschine: Maschine                  # Snapshot
    werkzeuge: list[Werkzeug]           # Snapshots — Projekt traegt eigene Werkzeug-Defs
    materialien: list[Material]         # Snapshots
    geometrien: list[GeometrieSnapshot] # Verweise auf eingebettete Dateien
    varianten: list[Variante]
    audit_log: list[str]                # Audit-Eintraege (Override-Bestaetigungen etc.)
```

Jede Variante enthaelt:

```python
class Variante:
    id: str
    name: str
    rohmaterial: Rohmaterial
    setups: list[Setup]
```

## Verwendung

```python
from camwosa.project import (
    neues_projekt, speichere_cwp, lade_cwp,
    Setup, SetupPause, SetupPauseTyp, OperationsKonfig,
)

# Neues Projekt
projekt = neues_projekt(
    "Lotus-Schale",
    maschine=proverxl_4030,
    rohmaterial=buche_platte,
    autor="Markus",
)

# Setup hinzufuegen
projekt.varianten[0].setups.append(Setup(
    id="setup1",
    name="2D-Rohling",
    werkzeug_id="schaft_6mm_2s_hm",
    operationen=[
        OperationsKonfig(
            id="op1", name="Kontur", typ="kontur",
            parameter={"vorschub": 2000, "spindel_rpm": 18000, ...},
        ),
    ],
))

# Speichern
speichere_cwp(projekt, "lotus.cwp")

# Spaeter wieder laden
projekt = lade_cwp("lotus.cwp")
```

## Auto-Save & Crash-Recovery

```python
from camwosa.project import auto_save

# Im Hintergrund alle 5 min:
auto_save(projekt, snapshot_dir="C:/Users/.../AppData/CAMWOSA/snapshots")
```

Beim App-Start sucht das Frontend nach `*.cwp.tmp`-Dateien und bietet Recovery an.

## Schema-Migration

`schema_version` wird im Manifest mitgeschrieben. Beim Laden:
- gleiche Version: direkt parsen
- aeltere Version: durch `_migriere(...)` schicken (Stub vorhanden)
- neuere Version: Fehler "bitte CAMWOSA aktualisieren"

Sobald Schema 2 existiert, wird in `project/migrate.py` die konkrete Migration ergaenzt.

## Geometrie-Snapshots

DXF/STL-Dateien werden **in den Container eingebettet** (nicht nur referenziert), damit das Projekt portabel bleibt — auch wenn das Original-DXF spaeter verschoben wird.

Extrahieren:

```python
from camwosa.project import extrahiere_geometrie

dxf_pfad = extrahiere_geometrie("lotus.cwp", "g1", ziel_verzeichnis="/tmp/cwp")
```

## Varianten

Mehrere Varianten innerhalb eines Projekts (siehe [Varianten](Varianten.md)):

```python
from camwosa.project import Variante

projekt.varianten.append(Variante(
    id="acryl",
    name="Acryl 5mm",
    rohmaterial=acryl_platte,
    setups=[...],   # eigene Setups mit anderen Parametern
))
```

## Audit-Log

`projekt.audit_log` wird vom Frontend befuellt — z.B. bei Sicherheits-Override-Bestaetigung:

```
2026-05-15T12:34:56Z | OVERRIDE g0_im_material | Setup setup1 | User: Markus
```

## Bekannte Einschraenkungen

- Keine Verschluesselung (Projekte sind plain JSON im ZIP).
- Maximale Container-Groesse limitiert durch ZIP64 (>4 GB).
- Keine inkrementellen Updates — beim Speichern wird komplett neu geschrieben.

## Verwandt

- [Datenmodell](Datenmodell.md)
- [Workflow-Modul](Workflow-Modul.md)
- [Varianten](Varianten.md)

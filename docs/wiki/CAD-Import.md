# CAD-Import

> **Status:** ✅ DXF, SVG, STL produktiv. STEP/IGES Stub (mit cadquery optional). Native Maker-CAD via Plugin-System geplant.
> **Code:** [backend/camwosa/cad/](../../backend/camwosa/cad/) · **Tests:** [backend/tests/cad/test_registry.py](../../backend/tests/cad/test_registry.py)

CAMWOSA setzt auf **neutrale Formate** als Pflicht und unterstuetzt **native Maker-CAD-Formate** ueber ein Plugin-System.

## Format-Tabelle

| Format | Status | Modul | Anmerkung |
|--------|--------|-------|-----------|
| **DXF** | ✅ Produktiv | `cad/dxf_importer.py` | LINE/POLYLINE/CIRCLE/ARC/ELLIPSE/SPLINE/POINT |
| **SVG** | ✅ Produktiv | `cad/svg_importer.py` | line/rect/circle/ellipse/polygon/polyline/path. Y-Spiegelung automatisch. |
| **STL** | ✅ Produktiv | `cad/stl_importer.py` | Mesh-Format fuer Relief-Operationen |
| **STEP / IGES** | 🟨 Stub | `cad/step_importer.py` | Erfordert `pip install cadquery` |
| **G-Code (Re-Import)** | ⏳ | — | Phase 2 |
| **DWG** | ⏳ | — | Phase 2, ueber `libredwg` oder Konversion zu DXF |
| **FreeCAD .FCStd** | ⏳ Plugin | — | OSS-CAD, kostenlos, ueber `freecad`-CLI |
| **Fusion .f3d / .f3z** | ⏳ Plugin | — | Maker-Lizenz kostenlos. Container ist ZIP, Inhalt aber proprietaer. Ggf. via Fusion-Add-In Export-Helfer. |
| **OpenSCAD .scad** | ⏳ Plugin | — | Skript-CAD. Render via `openscad`-CLI -> STL |
| **Blender .blend** | ⏳ Plugin | — | Ueber `blender`-CLI Headless-Export |
| **SolidWorks .sldprt** | ⏳ Plugin | — | Erfordert SolidWorks-API |
| **Solid Edge Community .par/.psm** | ⏳ Plugin | — | Erfordert Solid-Edge-API |
| **Inventor .ipt** | ⏳ Plugin | — | Erfordert Inventor-API |

## Verwendung

### Python-API

```python
from camwosa.cad import lade_cad

erg = lade_cad("zeichnung.svg")
print(erg.format_id)        # "svg"
print(erg.einheit)          # "mm"
print(len(erg.objekte))     # Anzahl Geometrieobjekte
print(erg.bounding_box)     # (Punkt2D(0,0), Punkt2D(100,60))
```

### REST-API

- `GET /api/cad/formate` → Liste aller verfuegbaren Importer mit Extensions
- `POST /api/cad/import` → Datei-Upload (`multipart/form-data`, Feld `datei`), erkennt Format automatisch

### Frontend

Der DXF-Import-Dialog wird in der naechsten Iteration zu einem generischen
„CAD-Import"-Dialog erweitert, der alle registrierten Formate via
`/api/cad/formate` listet und automatisch das richtige nutzt.

## Architektur

```
camwosa/cad/
├── base.py                # CADImporter (ABC) + Registry
├── dxf_importer.py        # Adapter auf camwosa.dxf
├── svg_importer.py        # Eigene Implementierung
├── stl_importer.py        # Adapter auf camwosa.stl
└── step_importer.py       # Stub (cadquery optional)
```

## Plugin-Eigenentwicklung

Eigene CAD-Importer werden — analog zu Postprozessoren — als Python-Klasse
geschrieben:

```python
from camwosa.cad.base import CADImporter, CADImportErgebnis, registry
from camwosa.dxf.parser import GeometrieObjekt

class MeinFormatImporter(CADImporter):
    format_id = "mein_format"
    name = "Mein Format"
    extensions = (".myf",)
    beschreibung = "Mein eigenes CAD-Format"

    def kann_lesen(self, pfad):
        return pfad.suffix.lower() == ".myf"

    def lade(self, pfad):
        objekte = []  # GeometrieObjekt-Liste aus deinem Parser
        return CADImportErgebnis(
            format_id=self.format_id,
            einheit="mm",
            objekte=objekte,
        )

registry().register("mein_format", MeinFormatImporter)
```

Datei in `data/cad_importers/user/` ablegen — wird beim Start automatisch geladen
(Plugin-Loader analog Postprozessor-Loader, wird in naechster Iteration
ergaenzt).

## Konventionen

- **Einheiten in mm.** Inch-Dateien werden geladen, Skalierung muss explizit
  ueber `cam.geometry.skaliere_inch_zu_mm` erfolgen — der Importer liefert
  `einheit="inch"` als Hinweis.
- **Y-Achse oben.** SVG/PDF haben Y nach unten — der SVG-Importer spiegelt
  automatisch.
- **Layer.** Wo das Format Layer kennt, werden sie uebernommen (DXF).
  Wo nicht, kommt alles in Layer `"0"` (oder bei Inkscape: `inkscape:label`).

## Verwandt

- [DXF-Import](DXF-Import.md) — Detaillierte DXF-Doku
- [STL-Import](STL-Import.md) — Mesh + Heightmap
- [Postprozessor-Plugins](Postprozessor-Plugins.md) — gleiches Plugin-Konzept

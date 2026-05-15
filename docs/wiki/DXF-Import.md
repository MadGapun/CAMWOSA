# DXF-Import

> **Status:** ✅ Implementiert.
> **Issue:** [#1](https://github.com/MadGapun/CAMWOSA/issues/1)
> **Code:** [backend/camwosa/dxf/parser.py](../../backend/camwosa/dxf/parser.py) · **Tests:** [backend/tests/dxf/test_parser.py](../../backend/tests/dxf/test_parser.py)

CAMWOSA importiert DXF-Dateien als Eingabe-Geometrie fuer CAM-Operationen. Der Parser ist ezdxf-basiert.

## Unterstuetzte Entities

| DXF-Entity | CAMWOSA-Typ | Anmerkung |
|------------|-------------|-----------|
| LINE | LINIE | 2 Stuetzpunkte |
| LWPOLYLINE | POLYLINIE | mit Geschlossen-Erkennung |
| POLYLINE | POLYLINIE | klassische Polylinie |
| CIRCLE | KREIS | Mittelpunkt + Radius |
| ARC | BOGEN | Mittelpunkt + Radius + Start-/End-Winkel |
| ELLIPSE | ELLIPSE | Hauptachse + Verhaeltnis + Rotation |
| SPLINE | SPLINE | diskretisiert (Standard 64 Stuetzpunkte) |
| POINT | PUNKT | einzelner Punkt |

Andere Entities (TEXT, INSERT, BLOCK, …) werden aktuell **ignoriert**. Zukuenftig: TEXT als Gravur-Geometrie konvertieren (Phase 1+).

## Verwendung

```python
from camwosa.dxf import lade_dxf, GeometrieTyp

dok = lade_dxf("zeichnung.dxf")

print(dok.einheit)         # "mm" / "inch" / "unbekannt"
print(dok.layer)           # ['0', 'KONTUR', 'BOHRUNGEN']
print(dok.bounding_box)    # (Punkt2D(0, 0), Punkt2D(100, 60))

# Alle Objekte aus einem Layer
for obj in dok.objekte_im_layer("KONTUR"):
    print(obj.typ, obj.geschlossen)

# Geschlossene Konturen (kandidaten fuer Tasche)
for kontur in dok.geschlossene_konturen():
    if kontur.typ == GeometrieTyp.KREIS:
        print("Kreis r=", kontur.attribute["radius"])
```

## Datentypen

```python
@dataclass(frozen=True)
class Punkt2D:
    x: float
    y: float

@dataclass
class GeometrieObjekt:
    typ: GeometrieTyp
    layer: str
    punkte: list[Punkt2D]
    geschlossen: bool
    attribute: dict[str, Any]   # typabhaengig: radius, start_winkel, ...
    farbe: int | None           # ACI Color Index

@dataclass
class DXFDokument:
    dateipfad: Path
    einheit: str
    objekte: list[GeometrieObjekt]
    layer: list[str]
    bounding_box: tuple[Punkt2D, Punkt2D] | None
```

## Einheiten

`$INSUNITS`-Header wird ausgewertet:
- `4` → mm
- `1` → inch
- alles andere → "unbekannt"

**CAMWOSA arbeitet intern in mm.** Inch-DXFs muessen vor Verwendung skaliert werden (kommt mit Operations-Schritt: `cam.geometry.skaliere_inch_zu_mm`).

## Solid-Edge-Besonderheiten

- Solid Edge exportiert standardmaessig DXF R2010+ — wird unterstuetzt.
- Massstab pruefen: bei DFT→DXF-Export kann die Einheit verloren gehen.
- Empfehlung im Solid-Edge-Export-Dialog: "Einheiten = mm".

## Geschlossene Konturen

Eine Kontur ist geschlossen wenn:
- LWPOLYLINE / POLYLINE explizit `closed=True` gesetzt hat, oder
- der Typ KREIS oder ELLIPSE ist (per Definition geschlossen).

Geschlossene Konturen sind Kandidaten fuer Tasche-Operationen. Offene Konturen werden ueblicherweise fuer Kontur- oder Gravur-Operationen verwendet.

## Fehlerbehandlung

```python
from camwosa.dxf import DXFFehler, lade_dxf

try:
    dok = lade_dxf(pfad)
except DXFFehler as e:
    print(f"DXF nicht lesbar: {e}")
```

`DXFFehler` deckt ab:
- Datei nicht gefunden
- Kein gueltiges DXF
- Strukturfehler im DXF (ezdxf wirft `DXFStructureError`)

## Bekannte Einschraenkungen

- TEXT-Entities werden ignoriert (kommt mit Operation-Gravur).
- BLOCK-Inserts werden nicht aufgeloest (geplant: rekursive Aufloesung).
- 3D-Koordinaten werden auf XY-Ebene projiziert (Z verworfen).
- Hatch-Patterns werden nicht uebernommen.

## Erweiterung

Neue Entities unterstuetzen:
1. Funktion `_entity_zu_objekt` in `parser.py` ergaenzen.
2. Neuen `GeometrieTyp` falls noetig.
3. Test in `tests/dxf/test_parser.py`.
4. Diesen Wiki-Eintrag aktualisieren.

## Verwandt

- [Operation-Kontur](Operation-Kontur.md)
- [Operation-Tasche](Operation-Tasche.md)
- [Operation-Bohren](Operation-Bohren.md)
- [Geometrie](Geometrie.md)

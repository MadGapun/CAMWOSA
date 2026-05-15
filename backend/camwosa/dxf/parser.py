"""DXF-Parser fuer CAMWOSA.

Liest DXF-Dateien und konvertiert die Geometrie in interne Datenstrukturen.
Unterstuetzte Entities:
    LINE, LWPOLYLINE, POLYLINE, CIRCLE, ARC, ELLIPSE, SPLINE, POINT

Geschlossene Konturen werden automatisch erkannt und sind fuer Tasche-Operationen
verwendbar. Offene Konturen werden ueblich fuer Kontur- oder Gravur-Operationen.

Siehe Wiki: docs/wiki/DXF-Import.md
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import ezdxf
from ezdxf.document import Drawing
from ezdxf.entities import DXFEntity


class GeometrieTyp(str, Enum):
    LINIE = "linie"
    POLYLINIE = "polylinie"
    KREIS = "kreis"
    BOGEN = "bogen"
    ELLIPSE = "ellipse"
    SPLINE = "spline"
    PUNKT = "punkt"


@dataclass(frozen=True)
class Punkt2D:
    x: float
    y: float

    def to_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


@dataclass
class GeometrieObjekt:
    """Ein einzelnes geometrisches Objekt aus dem DXF.

    Die Punkte-Liste enthaelt bei:
    - LINIE: 2 Punkte (Start, Ende)
    - POLYLINIE: alle Stuetzpunkte
    - KREIS: 1 Punkt (Mittelpunkt). Radius in attribute['radius']
    - BOGEN: 1 Punkt (Mittelpunkt). attribute: radius, start_winkel, end_winkel
    - ELLIPSE: 1 Punkt (Mittelpunkt). attribute: hauptachse, nebenachse, rotation
    - SPLINE: diskretisierte Punkte (Standard 64 Schritte)
    - PUNKT: 1 Punkt
    """

    typ: GeometrieTyp
    layer: str
    punkte: list[Punkt2D]
    geschlossen: bool = False
    attribute: dict[str, Any] = field(default_factory=dict)
    farbe: int | None = None  # ACI Color Index aus DXF


@dataclass
class DXFDokument:
    """Das geparste DXF-Dokument."""

    dateipfad: Path
    einheit: str  # "mm", "inch", "unbekannt"
    objekte: list[GeometrieObjekt]
    layer: list[str]
    bounding_box: tuple[Punkt2D, Punkt2D] | None  # (min, max)

    def objekte_im_layer(self, layer: str) -> list[GeometrieObjekt]:
        return [o for o in self.objekte if o.layer == layer]

    def geschlossene_konturen(self) -> list[GeometrieObjekt]:
        """Alle geschlossenen Konturen + Kreise/Ellipsen."""
        return [o for o in self.objekte if o.geschlossen or o.typ in (
            GeometrieTyp.KREIS, GeometrieTyp.ELLIPSE,
        )]


class DXFFehler(Exception):
    """Fehler beim DXF-Lesen."""


# ---------------------------------------------------------------------------
# Hauptfunktion
# ---------------------------------------------------------------------------


_INSUNITS_MAP = {
    0: "unbekannt",
    1: "inch",
    4: "mm",
    5: "cm",
    6: "m",
}


def lade_dxf(pfad: str | Path, *, spline_aufloesung: int = 64) -> DXFDokument:
    """Liest eine DXF-Datei und gibt das geparste Dokument zurueck.

    Args:
        pfad: Pfad zur DXF-Datei.
        spline_aufloesung: Anzahl Stuetzpunkte fuer SPLINE-Diskretisierung.

    Raises:
        DXFFehler: Wenn die Datei nicht lesbar oder kein gueltiges DXF ist.
    """
    pfad_obj = Path(pfad)
    if not pfad_obj.exists():
        raise DXFFehler(f"Datei nicht gefunden: {pfad_obj}")
    try:
        doc: Drawing = ezdxf.readfile(str(pfad_obj))
    except (ezdxf.DXFStructureError, ezdxf.DXFError) as e:
        raise DXFFehler(f"Ungueltiges DXF: {e}") from e
    except Exception as e:  # noqa: BLE001
        raise DXFFehler(f"Konnte DXF nicht lesen: {e}") from e

    einheit = _INSUNITS_MAP.get(doc.header.get("$INSUNITS", 0), "unbekannt")
    layer = sorted({l.dxf.name for l in doc.layers})

    msp = doc.modelspace()
    objekte: list[GeometrieObjekt] = []
    for entity in msp:
        obj = _entity_zu_objekt(entity, spline_aufloesung=spline_aufloesung)
        if obj is not None:
            objekte.append(obj)

    bbox = _berechne_bounding_box(objekte)

    return DXFDokument(
        dateipfad=pfad_obj,
        einheit=einheit,
        objekte=objekte,
        layer=layer,
        bounding_box=bbox,
    )


# ---------------------------------------------------------------------------
# Entity-Konvertierung
# ---------------------------------------------------------------------------


def _entity_zu_objekt(entity: DXFEntity, *, spline_aufloesung: int) -> GeometrieObjekt | None:
    dxftype = entity.dxftype()
    layer = entity.dxf.layer
    farbe = getattr(entity.dxf, "color", None)

    if dxftype == "LINE":
        return GeometrieObjekt(
            typ=GeometrieTyp.LINIE,
            layer=layer,
            farbe=farbe,
            punkte=[
                Punkt2D(entity.dxf.start.x, entity.dxf.start.y),
                Punkt2D(entity.dxf.end.x, entity.dxf.end.y),
            ],
            geschlossen=False,
        )

    if dxftype == "LWPOLYLINE":
        pts = [Punkt2D(p[0], p[1]) for p in entity.get_points("xy")]
        geschlossen = bool(entity.closed)
        return GeometrieObjekt(
            typ=GeometrieTyp.POLYLINIE,
            layer=layer,
            farbe=farbe,
            punkte=pts,
            geschlossen=geschlossen,
        )

    if dxftype == "POLYLINE":
        pts = [Punkt2D(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
        geschlossen = bool(entity.is_closed)
        return GeometrieObjekt(
            typ=GeometrieTyp.POLYLINIE,
            layer=layer,
            farbe=farbe,
            punkte=pts,
            geschlossen=geschlossen,
        )

    if dxftype == "CIRCLE":
        return GeometrieObjekt(
            typ=GeometrieTyp.KREIS,
            layer=layer,
            farbe=farbe,
            punkte=[Punkt2D(entity.dxf.center.x, entity.dxf.center.y)],
            geschlossen=True,
            attribute={"radius": float(entity.dxf.radius)},
        )

    if dxftype == "ARC":
        return GeometrieObjekt(
            typ=GeometrieTyp.BOGEN,
            layer=layer,
            farbe=farbe,
            punkte=[Punkt2D(entity.dxf.center.x, entity.dxf.center.y)],
            attribute={
                "radius": float(entity.dxf.radius),
                "start_winkel": float(entity.dxf.start_angle),
                "end_winkel": float(entity.dxf.end_angle),
            },
        )

    if dxftype == "ELLIPSE":
        major = entity.dxf.major_axis
        ratio = float(entity.dxf.ratio)
        haupt_laenge = math.hypot(major.x, major.y)
        rotation = math.degrees(math.atan2(major.y, major.x))
        return GeometrieObjekt(
            typ=GeometrieTyp.ELLIPSE,
            layer=layer,
            farbe=farbe,
            punkte=[Punkt2D(entity.dxf.center.x, entity.dxf.center.y)],
            geschlossen=True,
            attribute={
                "hauptachse": haupt_laenge,
                "nebenachse": haupt_laenge * ratio,
                "rotation": rotation,
                "start_param": float(entity.dxf.start_param),
                "end_param": float(entity.dxf.end_param),
            },
        )

    if dxftype == "SPLINE":
        try:
            pts = [Punkt2D(p[0], p[1]) for p in entity.flattening(0.01, segments=spline_aufloesung)]
        except Exception:  # noqa: BLE001
            pts = [Punkt2D(p[0], p[1]) for p in entity.control_points]
        return GeometrieObjekt(
            typ=GeometrieTyp.SPLINE,
            layer=layer,
            farbe=farbe,
            punkte=pts,
            geschlossen=False,
        )

    if dxftype == "POINT":
        return GeometrieObjekt(
            typ=GeometrieTyp.PUNKT,
            layer=layer,
            farbe=farbe,
            punkte=[Punkt2D(entity.dxf.location.x, entity.dxf.location.y)],
        )

    return None  # unbekannter Entity-Typ wird ignoriert


def _berechne_bounding_box(objekte: list[GeometrieObjekt]) -> tuple[Punkt2D, Punkt2D] | None:
    if not objekte:
        return None
    xs: list[float] = []
    ys: list[float] = []
    for o in objekte:
        if o.typ == GeometrieTyp.KREIS:
            cx, cy = o.punkte[0].x, o.punkte[0].y
            r = o.attribute["radius"]
            xs.extend([cx - r, cx + r])
            ys.extend([cy - r, cy + r])
        elif o.typ == GeometrieTyp.BOGEN:
            cx, cy = o.punkte[0].x, o.punkte[0].y
            r = o.attribute["radius"]
            # konservativ: Bounding-Box des Vollkreises
            xs.extend([cx - r, cx + r])
            ys.extend([cy - r, cy + r])
        elif o.typ == GeometrieTyp.ELLIPSE:
            cx, cy = o.punkte[0].x, o.punkte[0].y
            a = o.attribute["hauptachse"]
            b = o.attribute["nebenachse"]
            r = max(a, b)
            xs.extend([cx - r, cx + r])
            ys.extend([cy - r, cy + r])
        else:
            for p in o.punkte:
                xs.append(p.x)
                ys.append(p.y)
    if not xs or not ys:
        return None
    return (Punkt2D(min(xs), min(ys)), Punkt2D(max(xs), max(ys)))


__all__ = [
    "DXFDokument",
    "DXFFehler",
    "GeometrieObjekt",
    "GeometrieTyp",
    "Punkt2D",
    "lade_dxf",
]

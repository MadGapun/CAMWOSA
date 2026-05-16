"""SVG-Importer.

Liest SVG-Dateien (z.B. aus Inkscape) und konvertiert die Pfade in CAMWOSA-
Geometrieobjekte. Unterstuetzt: <line>, <rect>, <circle>, <ellipse>,
<polygon>, <polyline>, <path> (M, L, H, V, Z, C, Q, A — diskretisiert).

Achtung Y-Achse: SVG hat Y nach unten, CAMWOSA arbeitet mit Y nach oben.
Wir spiegeln deshalb beim Import an der Hoehe der Zeichnung.

Siehe Wiki: docs/wiki/CAD-Import.md
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

from camwosa.cad.base import CADImporter, CADImportErgebnis, CADImportFehler, registry
from camwosa.dxf.parser import GeometrieObjekt, GeometrieTyp, Punkt2D


SVG_NS = "{http://www.w3.org/2000/svg}"


class SVGImporter(CADImporter):
    format_id = "svg"
    name = "SVG"
    extensions = (".svg",)
    beschreibung = "Scalable Vector Graphics (Inkscape, Illustrator, …)"

    def kann_lesen(self, pfad: Path) -> bool:
        return pfad.suffix.lower() == ".svg"

    def lade(self, pfad: Path) -> CADImportErgebnis:
        try:
            tree = ET.parse(pfad)
        except ET.ParseError as e:
            raise CADImportFehler(f"SVG nicht parsbar: {e}") from e
        root = tree.getroot()
        breite_doc, hoehe_doc, einheit = _parse_root(root)

        objekte: list[GeometrieObjekt] = []
        for el in root.iter():
            tag = _tag(el)
            layer = _resolve_layer(el)
            if tag == "line":
                objekte.append(_line(el, layer))
            elif tag == "rect":
                objekte.append(_rect(el, layer))
            elif tag == "circle":
                objekte.append(_circle(el, layer))
            elif tag == "ellipse":
                objekte.append(_ellipse(el, layer))
            elif tag in ("polygon", "polyline"):
                obj = _polygon_oder_polyline(el, layer, tag == "polygon")
                if obj is not None:
                    objekte.append(obj)
            elif tag == "path":
                pfade = _path(el, layer)
                objekte.extend(pfade)

        # Y-Spiegelung: SVG Y unten -> CAM Y oben
        if hoehe_doc and hoehe_doc > 0:
            objekte = [_y_spiegeln(o, hoehe_doc) for o in objekte]

        layer_set: list[str] = []
        for o in objekte:
            if o.layer not in layer_set:
                layer_set.append(o.layer)

        bbox = _bbox(objekte)

        return CADImportErgebnis(
            format_id=self.format_id,
            einheit=einheit,
            objekte=objekte,
            layer=layer_set,
            bounding_box=bbox,
            metadaten={"svg_breite": breite_doc, "svg_hoehe": hoehe_doc},
        )


# ---------------------------------------------------------------------------
# Helfer
# ---------------------------------------------------------------------------


def _tag(el: ET.Element) -> str:
    t = el.tag
    if t.startswith(SVG_NS):
        return t[len(SVG_NS):]
    return t


def _parse_root(root: ET.Element) -> tuple[float, float, str]:
    """Gibt (breite, hoehe, einheit) zurueck."""
    breite = _laenge(root.get("width", "0"))
    hoehe = _laenge(root.get("height", "0"))
    # Wenn viewBox gesetzt: dessen Werte verwenden
    vb = root.get("viewBox")
    if vb:
        teile = vb.replace(",", " ").split()
        if len(teile) == 4:
            breite = float(teile[2])
            hoehe = float(teile[3])
    # SVG-Standard ist user units = px = 1/96 inch = 0.2645833 mm.
    # Inkscape exportiert oft mit explicit "mm" oder "in" suffix.
    einheit = "mm"
    width_attr = root.get("width", "")
    if "in" in width_attr.lower():
        einheit = "inch"
    return breite, hoehe, einheit


def _laenge(s: str) -> float:
    if not s:
        return 0.0
    m = re.match(r"^([0-9.+\-eE]+)", s.strip())
    if not m:
        return 0.0
    return float(m.group(1))


def _resolve_layer(el: ET.Element) -> str:
    parent = el  # ElementTree gibt Parent nicht direkt — fallback nur ueber Inkscape-Label
    label = el.get("{http://www.inkscape.org/namespaces/inkscape}label")
    if label:
        return label
    return el.get("id", "0") if _tag(el) == "g" else "0"


def _line(el: ET.Element, layer: str) -> GeometrieObjekt:
    return GeometrieObjekt(
        typ=GeometrieTyp.LINIE,
        layer=layer,
        punkte=[
            Punkt2D(_laenge(el.get("x1", "0")), _laenge(el.get("y1", "0"))),
            Punkt2D(_laenge(el.get("x2", "0")), _laenge(el.get("y2", "0"))),
        ],
    )


def _rect(el: ET.Element, layer: str) -> GeometrieObjekt:
    x = _laenge(el.get("x", "0"))
    y = _laenge(el.get("y", "0"))
    w = _laenge(el.get("width", "0"))
    h = _laenge(el.get("height", "0"))
    return GeometrieObjekt(
        typ=GeometrieTyp.POLYLINIE,
        layer=layer,
        punkte=[
            Punkt2D(x, y),
            Punkt2D(x + w, y),
            Punkt2D(x + w, y + h),
            Punkt2D(x, y + h),
        ],
        geschlossen=True,
    )


def _circle(el: ET.Element, layer: str) -> GeometrieObjekt:
    cx = _laenge(el.get("cx", "0"))
    cy = _laenge(el.get("cy", "0"))
    r = _laenge(el.get("r", "0"))
    return GeometrieObjekt(
        typ=GeometrieTyp.KREIS,
        layer=layer,
        punkte=[Punkt2D(cx, cy)],
        geschlossen=True,
        attribute={"radius": r},
    )


def _ellipse(el: ET.Element, layer: str) -> GeometrieObjekt:
    cx = _laenge(el.get("cx", "0"))
    cy = _laenge(el.get("cy", "0"))
    rx = _laenge(el.get("rx", "0"))
    ry = _laenge(el.get("ry", "0"))
    return GeometrieObjekt(
        typ=GeometrieTyp.ELLIPSE,
        layer=layer,
        punkte=[Punkt2D(cx, cy)],
        geschlossen=True,
        attribute={"hauptachse": rx, "nebenachse": ry, "rotation": 0.0,
                   "start_param": 0.0, "end_param": 2 * math.pi},
    )


def _polygon_oder_polyline(
    el: ET.Element, layer: str, geschlossen: bool
) -> GeometrieObjekt | None:
    pts_raw = el.get("points", "").strip()
    if not pts_raw:
        return None
    nums = [float(x) for x in re.split(r"[\s,]+", pts_raw) if x]
    pts = [Punkt2D(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]
    if len(pts) < 2:
        return None
    return GeometrieObjekt(
        typ=GeometrieTyp.POLYLINIE,
        layer=layer,
        punkte=pts,
        geschlossen=geschlossen,
    )


# Path-Parser: subset M/L/H/V/Z + C/Q/A (diskretisiert)
_PATH_TOKEN = re.compile(r"([MLHVZCSQTAmlhvzcsqta])|(-?\d*\.?\d+(?:[eE][-+]?\d+)?)")


def _path(el: ET.Element, layer: str) -> list[GeometrieObjekt]:
    d = el.get("d", "").strip()
    if not d:
        return []
    tokens = [m.group(1) or m.group(2) for m in _PATH_TOKEN.finditer(d)]
    objekte: list[GeometrieObjekt] = []
    aktuelle_punkte: list[Punkt2D] = []
    geschlossen = False
    cx = cy = 0.0
    start_x = start_y = 0.0
    cmd: str | None = None
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in "MLHVZCSQTAmlhvzcsqta":
            cmd = t
            i += 1
            if cmd in ("Z", "z"):
                # Pfad schliessen
                if aktuelle_punkte:
                    aktuelle_punkte.append(Punkt2D(start_x, start_y))
                    geschlossen = True
                continue
        else:
            # numerischer Token, aktueller cmd bleibt
            pass

        if cmd is None:
            i += 1
            continue

        rel = cmd.islower()

        def take(n: int) -> list[float]:
            nonlocal i
            vals: list[float] = []
            while len(vals) < n and i < len(tokens):
                tok = tokens[i]
                if tok in "MLHVZCSQTAmlhvzcsqta":
                    break
                vals.append(float(tok))
                i += 1
            return vals

        c = cmd.upper()
        if c == "M":
            v = take(2)
            if len(v) < 2:
                break
            x, y = v
            if rel:
                x += cx
                y += cy
            cx, cy = x, y
            start_x, start_y = x, y
            aktuelle_punkte = [Punkt2D(cx, cy)]
            geschlossen = False
            cmd = "L" if not rel else "l"
        elif c == "L":
            v = take(2)
            if len(v) < 2:
                break
            x, y = v
            if rel:
                x += cx
                y += cy
            cx, cy = x, y
            aktuelle_punkte.append(Punkt2D(cx, cy))
        elif c == "H":
            v = take(1)
            if not v:
                break
            x = v[0]
            if rel:
                x += cx
            cx = x
            aktuelle_punkte.append(Punkt2D(cx, cy))
        elif c == "V":
            v = take(1)
            if not v:
                break
            y = v[0]
            if rel:
                y += cy
            cy = y
            aktuelle_punkte.append(Punkt2D(cx, cy))
        elif c == "C":
            v = take(6)
            if len(v) < 6:
                break
            x1, y1, x2, y2, x, y = v
            if rel:
                x1 += cx; y1 += cy; x2 += cx; y2 += cy; x += cx; y += cy
            for t_ in [k / 16 for k in range(1, 17)]:
                bx = (1 - t_) ** 3 * cx + 3 * (1 - t_) ** 2 * t_ * x1 + 3 * (1 - t_) * t_ ** 2 * x2 + t_ ** 3 * x
                by = (1 - t_) ** 3 * cy + 3 * (1 - t_) ** 2 * t_ * y1 + 3 * (1 - t_) * t_ ** 2 * y2 + t_ ** 3 * y
                aktuelle_punkte.append(Punkt2D(bx, by))
            cx, cy = x, y
        elif c == "Q":
            v = take(4)
            if len(v) < 4:
                break
            x1, y1, x, y = v
            if rel:
                x1 += cx; y1 += cy; x += cx; y += cy
            for t_ in [k / 12 for k in range(1, 13)]:
                bx = (1 - t_) ** 2 * cx + 2 * (1 - t_) * t_ * x1 + t_ ** 2 * x
                by = (1 - t_) ** 2 * cy + 2 * (1 - t_) * t_ * y1 + t_ ** 2 * y
                aktuelle_punkte.append(Punkt2D(bx, by))
            cx, cy = x, y
        elif c == "A":
            v = take(7)
            if len(v) < 7:
                break
            # Vereinfachte Approximation: gerade Linie (TODO: echter elliptischer Bogen)
            x = v[5]; y = v[6]
            if rel:
                x += cx; y += cy
            cx, cy = x, y
            aktuelle_punkte.append(Punkt2D(cx, cy))
        else:
            i += 1

    if aktuelle_punkte and len(aktuelle_punkte) >= 2:
        objekte.append(GeometrieObjekt(
            typ=GeometrieTyp.POLYLINIE,
            layer=layer,
            punkte=aktuelle_punkte,
            geschlossen=geschlossen,
        ))
    return objekte


def _y_spiegeln(o: GeometrieObjekt, hoehe: float) -> GeometrieObjekt:
    neue = [Punkt2D(p.x, hoehe - p.y) for p in o.punkte]
    return GeometrieObjekt(
        typ=o.typ, layer=o.layer, punkte=neue,
        geschlossen=o.geschlossen, attribute=dict(o.attribute), farbe=o.farbe,
    )


def _bbox(objekte: Iterable[GeometrieObjekt]) -> tuple[Punkt2D, Punkt2D] | None:
    minx = miny = float("inf")
    maxx = maxy = float("-inf")
    leer = True
    for o in objekte:
        if o.typ == GeometrieTyp.KREIS:
            cx, cy = o.punkte[0].x, o.punkte[0].y
            r = o.attribute.get("radius", 0)
            minx = min(minx, cx - r); maxx = max(maxx, cx + r)
            miny = min(miny, cy - r); maxy = max(maxy, cy + r)
            leer = False
        else:
            for p in o.punkte:
                minx = min(minx, p.x); maxx = max(maxx, p.x)
                miny = min(miny, p.y); maxy = max(maxy, p.y)
                leer = False
    if leer:
        return None
    return (Punkt2D(minx, miny), Punkt2D(maxx, maxy))


registry().register("svg", SVGImporter)

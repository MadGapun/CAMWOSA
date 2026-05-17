"""Text → Pfad-Konverter (Master-Plan A37).

Konvertiert eine Zeichenfolge mit einer TrueType-/OpenType-Schrift in eine
Liste von 2D-Polygonen — direkt nutzbar fuer Gravur-, Konturoperationen,
Wrap-Mode und ``auto_cam_erstellen.beschriftung_wrap``.

Nutzt **fontTools** (pure-Python, keine Binary-Deps) — kein freetype noetig.

Konvention:
- Y-Achse zeigt nach oben (Standard CAD/CAM)
- X startet bei 0, waechst nach rechts
- Loecher in Buchstaben (O, P, B, A, ...) sind im Polygon als Inseln markiert

Siehe Wiki: docs/wiki/Wrap-Mode.md, docs/wiki/Operation-Gravur.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from shapely.geometry import Polygon
from shapely.ops import unary_union

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont


@dataclass
class TextPfadParameter:
    """Parameter fuer die Text-zu-Pfad-Konvertierung."""

    hoehe_mm: float = 10.0
    """Buchstabenhoehe (cap-height) in mm. Aequivalent zur Punkt-Groesse."""

    font_pfad: str | None = None
    """Pfad zur TTF/OTF-Datei. None -> Default-Font (siehe FONT_FALLBACK)."""

    zeichen_abstand_extra_mm: float = 0.0
    """Zusaetzlicher Abstand zwischen Zeichen (kann negativ sein, kerned)."""

    zeilen_abstand_faktor: float = 1.2
    """Zeilenabstand als Faktor der Buchstabenhoehe."""

    kurven_aufloesung: int = 12
    """Approximations-Schritte fuer Bezier-Kurven pro Segment."""


# Liste der versuchten Default-Fonts (in Reihenfolge der Praeferenz)
FONT_FALLBACK: list[str] = [
    # Windows
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    # Linux Debian/Ubuntu
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    # macOS
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


class FontFehler(Exception):
    """Wird geworfen wenn kein gueltiger Font gefunden wurde."""


def _finde_default_font() -> str:
    """Sucht den ersten verfuegbaren Font aus der Fallback-Liste."""
    for kandidat in FONT_FALLBACK:
        if Path(kandidat).is_file():
            return kandidat
    raise FontFehler(
        "Kein Default-Font gefunden. Bitte font_pfad explizit angeben. "
        f"Gesucht: {FONT_FALLBACK}"
    )


# ---------------------------------------------------------------------------
# Pen — fontTools Pen-API → 2D-Polygone
# ---------------------------------------------------------------------------


class _PfadPen(BasePen):
    """Sammelt die Pen-Kommandos in geschlossene Polygone.

    Jedes ``closePath`` schliesst ein Subpfad ab; bei Buchstaben mit Loechern
    (z.B. ``O``, ``P``) entstehen mehrere Subpfade. Die Aussenpfade sind
    gegen-den-Uhrzeigersinn (CCW), Loecher im Uhrzeigersinn (CW) — Standard-
    TrueType-Konvention.
    """

    def __init__(self, glyph_set, kurven_aufloesung: int):
        super().__init__(glyph_set)
        self.kurven_aufloesung = max(2, kurven_aufloesung)
        self._aktueller_pfad: list[tuple[float, float]] = []
        self.subpfade: list[list[tuple[float, float]]] = []

    def _moveTo(self, pt):
        if self._aktueller_pfad:
            self.subpfade.append(self._aktueller_pfad)
        self._aktueller_pfad = [pt]

    def _lineTo(self, pt):
        self._aktueller_pfad.append(pt)

    def _curveToOne(self, pt1, pt2, pt3):
        """Cubic-Bezier — wird in N Linien approximiert."""
        if not self._aktueller_pfad:
            self._aktueller_pfad.append(self._currentPoint or (0.0, 0.0))
        x0, y0 = self._aktueller_pfad[-1]
        for i in range(1, self.kurven_aufloesung + 1):
            t = i / self.kurven_aufloesung
            mt = 1.0 - t
            x = (mt ** 3 * x0
                 + 3 * mt ** 2 * t * pt1[0]
                 + 3 * mt * t ** 2 * pt2[0]
                 + t ** 3 * pt3[0])
            y = (mt ** 3 * y0
                 + 3 * mt ** 2 * t * pt1[1]
                 + 3 * mt * t ** 2 * pt2[1]
                 + t ** 3 * pt3[1])
            self._aktueller_pfad.append((x, y))

    def _qCurveToOne(self, pt1, pt2):
        """Quadratic-Bezier — TrueType-Standard."""
        if not self._aktueller_pfad:
            self._aktueller_pfad.append(self._currentPoint or (0.0, 0.0))
        x0, y0 = self._aktueller_pfad[-1]
        for i in range(1, self.kurven_aufloesung + 1):
            t = i / self.kurven_aufloesung
            mt = 1.0 - t
            x = mt ** 2 * x0 + 2 * mt * t * pt1[0] + t ** 2 * pt2[0]
            y = mt ** 2 * y0 + 2 * mt * t * pt1[1] + t ** 2 * pt2[1]
            self._aktueller_pfad.append((x, y))

    def _closePath(self):
        if len(self._aktueller_pfad) >= 3:
            # Sicherstellen dass Pfad geschlossen ist
            if self._aktueller_pfad[0] != self._aktueller_pfad[-1]:
                self._aktueller_pfad.append(self._aktueller_pfad[0])
            self.subpfade.append(self._aktueller_pfad)
        self._aktueller_pfad = []

    def _endPath(self):
        # Wie closePath, aber ohne Verbindung zum Anfang
        if len(self._aktueller_pfad) >= 3:
            self.subpfade.append(self._aktueller_pfad)
        self._aktueller_pfad = []


# ---------------------------------------------------------------------------
# Haupt-API
# ---------------------------------------------------------------------------


@dataclass
class TextZeile:
    """Ein einzelner Glyph (oder eine Wortgruppe) als Position + Polygone."""

    text: str
    polygone: list[Polygon] = field(default_factory=list)
    """shapely-Polygone (Aussenkontur + Inseln-Loecher)."""

    breite_mm: float = 0.0
    hoehe_mm: float = 0.0


def text_zu_pfade(
    text: str,
    parameter: TextPfadParameter | None = None,
) -> list[Polygon]:
    """Konvertiert eine Zeichenfolge in eine Liste von 2D-Polygonen.

    Jeder Buchstabe wird ein oder mehrere Polygone. Buchstaben mit
    Loechern (O, P, B, A, R, D, ...) werden als shapely-Polygon mit
    ``holes`` zurueckgegeben.

    Args:
        text: Die Zeichenfolge (Mehrzeilig per ``\\n``).
        parameter: Konfiguration. ``None`` -> Defaults.

    Returns:
        Liste von shapely-Polygonen, fertig zur Weiterverarbeitung mit
        ``cam.kontur``, ``cam.gravur`` oder ``cam.wrap``.

    Raises:
        FontFehler: Wenn kein Font verfuegbar ist.
        ValueError: Bei leerer Eingabe.
    """
    parameter = parameter or TextPfadParameter()
    if not text:
        return []
    font_pfad = parameter.font_pfad or _finde_default_font()
    if not Path(font_pfad).is_file():
        raise FontFehler(f"Font-Datei nicht gefunden: {font_pfad}")

    font = TTFont(font_pfad)
    cmap = font.getBestCmap()
    glyph_set = font.getGlyphSet()
    units_per_em = font["head"].unitsPerEm
    # Skalierungsfaktor: font_units -> mm
    # cap-height ungefaehr 0.7 * em fuer die meisten Fonts
    cap_height_units = (
        font["OS/2"].sCapHeight
        if "OS/2" in font and hasattr(font["OS/2"], "sCapHeight")
        and font["OS/2"].sCapHeight > 0
        else units_per_em * 0.7
    )
    skalierung = parameter.hoehe_mm / cap_height_units
    zeilen_abstand_units = units_per_em * parameter.zeilen_abstand_faktor
    extra_advance_units = parameter.zeichen_abstand_extra_mm / skalierung

    alle_polygone: list[Polygon] = []
    y_offset_units = 0.0  # nach unten verschoben fuer weitere Zeilen

    for zeile in text.split("\n"):
        x_cursor = 0.0
        for char in zeile:
            codepoint = ord(char)
            glyph_name = cmap.get(codepoint)
            if glyph_name is None:
                # Unbekanntes Zeichen -> Leerzeichen Advance
                x_cursor += units_per_em * 0.3
                continue
            glyph = glyph_set[glyph_name]
            pen = _PfadPen(glyph_set, parameter.kurven_aufloesung)
            glyph.draw(pen)
            # Falls Pen noch offene Pfade hat
            if pen._aktueller_pfad:
                pen._closePath()

            # Subpfade in skalierte Punkte konvertieren + relativ zum Cursor
            glyph_polygone = _subpfade_zu_polygonen(
                pen.subpfade, x_cursor, y_offset_units, skalierung,
            )
            alle_polygone.extend(glyph_polygone)
            x_cursor += glyph.width + extra_advance_units

        y_offset_units -= zeilen_abstand_units

    return alle_polygone


def _subpfade_zu_polygonen(
    subpfade: list[list[tuple[float, float]]],
    x_offset: float,
    y_offset: float,
    skalierung: float,
) -> list[Polygon]:
    """Wandelt Pen-Subpfade in shapely-Polygone mit korrekter Loch-Erkennung.

    Statt sich auf die Orientierung (CW/CCW) zu verlassen — die zwischen
    TrueType, CFF und Pen-Implementations variiert — bauen wir die
    Parent-Child-Hierarchie ueber **Contains-Test** auf:
    - Jeder Subpfad wird in ein nicht-orientiertes Polygon geladen.
    - Ein Subpfad ist Aussenkontur wenn er keinen anderen Subpfad
      *strict-enthaelt* (d.h. niemand enthaelt ihn).
    - Loecher werden ihrem unmittelbaren Eltern-Aussenpolygon zugeordnet.
    """
    if not subpfade:
        return []

    def _trafo(p: tuple[float, float]) -> tuple[float, float]:
        return ((p[0] + x_offset) * skalierung, (p[1] + y_offset) * skalierung)

    geskaliert = [[_trafo(p) for p in pf] for pf in subpfade if len(pf) >= 3]
    if not geskaliert:
        return []

    # Roh-Polygone fuer Contains-Tests
    roh = []
    for pf in geskaliert:
        try:
            p = Polygon(pf)
            if not p.is_valid:
                p = p.buffer(0)
            if p.is_empty or p.geom_type != "Polygon":
                continue
            roh.append(p)
        except Exception:  # noqa: BLE001
            continue

    # Bestimme fuer jeden Pfad, wer ihn enthaelt
    n = len(roh)
    enthaelt = [[False] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j and roh[i].contains(roh[j]):
                enthaelt[i][j] = True

    # Verschachtelungs-Tiefe: wieviele andere enthalten Pfad i
    tiefe = [sum(enthaelt[k][i] for k in range(n)) for i in range(n)]
    # Gerade Tiefe = Aussenkontur, ungerade = Loch
    polygone: list[Polygon] = []
    for i in range(n):
        if tiefe[i] % 2 != 0:
            continue
        # Loecher: alle j mit tiefe[j] == tiefe[i] + 1 und enthaelt[i][j]
        loch_indizes = [
            j for j in range(n)
            if enthaelt[i][j] and tiefe[j] == tiefe[i] + 1
        ]
        aussen_punkte = list(roh[i].exterior.coords)
        loch_punkte = [list(roh[j].exterior.coords) for j in loch_indizes]
        try:
            poly = Polygon(aussen_punkte, holes=loch_punkte)
            if not poly.is_valid:
                poly = poly.buffer(0)
            if poly.geom_type == "Polygon" and poly.area > 0:
                polygone.append(poly)
        except Exception:  # noqa: BLE001
            continue
    return polygone


def _flaeche(pf: list[tuple[float, float]]) -> float:
    """Signed Area per Shoelace — CCW positiv, CW negativ."""
    if len(pf) < 3:
        return 0.0
    s = 0.0
    n = len(pf)
    for i in range(n):
        x1, y1 = pf[i]
        x2, y2 = pf[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def _punkt_in_polygon(pkt: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    """Ray-Casting Test ob Punkt im Polygon."""
    x, y = pkt
    n = len(polygon)
    drinnen = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            drinnen = not drinnen
        j = i
    return drinnen


def text_bounding_box(
    text: str, parameter: TextPfadParameter | None = None,
) -> tuple[float, float, float, float]:
    """Schnell-Berechnung der Bounding-Box ohne komplette Polygone.

    Liefert ``(x_min, y_min, x_max, y_max)`` in mm.
    """
    polygone = text_zu_pfade(text, parameter)
    if not polygone:
        return (0.0, 0.0, 0.0, 0.0)
    union = unary_union(polygone)
    bounds = union.bounds  # (minx, miny, maxx, maxy)
    return bounds


def polygone_zu_punktlisten(
    polygone: Sequence[Polygon],
) -> list[list[tuple[float, float]]]:
    """Konvertiert shapely-Polygone in eine flache Punktlisten-Liste.

    Loecher werden separat angehaengt — fuer Operationen die Loecher als
    weitere Pfade behandeln (z.B. Kontur Innen).
    """
    out: list[list[tuple[float, float]]] = []
    for poly in polygone:
        out.append(list(poly.exterior.coords))
        for innen in poly.interiors:
            out.append(list(innen.coords))
    return out


__all__ = [
    "FONT_FALLBACK",
    "FontFehler",
    "TextPfadParameter",
    "TextZeile",
    "polygone_zu_punktlisten",
    "text_bounding_box",
    "text_zu_pfade",
]

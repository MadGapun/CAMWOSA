"""CAM-Operation: Tasche (Pocket).

Raeumt eine geschlossene Flaeche aus.

Strategien:
- PARALLEL (Zickzack)         : default, schnell, gleichmaessig
- SPIRAL_AUSSEN               : von innen nach aussen (rund)
- SPIRAL_INNEN                : von aussen nach innen (rechteckig)
- OFFSET_KONTUR               : geschachtelte Konturen
- ADAPTIVE                    : trochoidaler Pfad (Phase E4)

Phase 1 implementiert PARALLEL und OFFSET_KONTUR.
SPIRAL und ADAPTIVE folgen in spaeteren Phasen.

Siehe Wiki: docs/wiki/Operation-Tasche.md
"""

from __future__ import annotations

import math

from shapely.geometry import LineString, MultiPolygon, Polygon

from camwosa.cam.geometry import objekt_zu_shapely, offset_polygon
from camwosa.cam.parameter import TaschenParameter, TaschenStrategie
from camwosa.db.models import Werkzeug
from camwosa.dxf.parser import GeometrieObjekt
from camwosa.gcode.toolpath import (
    Bewegung,
    BewegungsTyp,
    OperationsTyp,
    Toolpath,
)


def erzeuge_tasche_toolpath(
    geometrie: GeometrieObjekt | Polygon,
    werkzeug: Werkzeug,
    parameter: TaschenParameter,
    *,
    operation_id: str = "tasche",
) -> Toolpath:
    geo = _als_polygon(geometrie)

    if parameter.strategie == TaschenStrategie.OFFSET_KONTUR:
        bahnen = _offset_kontur_bahnen(geo, werkzeug, parameter)
    elif parameter.strategie == TaschenStrategie.SPIRAL_AUSSEN:
        bahnen = _spiral_aussen_bahnen(geo, werkzeug, parameter)
    elif parameter.strategie == TaschenStrategie.SPIRAL_INNEN:
        bahnen = _offset_kontur_bahnen(geo, werkzeug, parameter)
    elif parameter.strategie == TaschenStrategie.ADAPTIVE:
        bahnen = _adaptive_bahnen(geo, werkzeug, parameter)
    else:
        bahnen = _parallel_bahnen(geo, werkzeug, parameter)

    bewegungen = _generiere_bewegungen(bahnen, werkzeug, parameter)

    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.TASCHE,
        werkzeug_id=werkzeug.id,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe,
        bewegungen=bewegungen,
        kommentar=f"Tasche ({parameter.strategie.value})",
        metadaten={"strategie": parameter.strategie.value},
    )


# ---------------------------------------------------------------------------
# Bahn-Generierung
# ---------------------------------------------------------------------------


def _als_polygon(g) -> Polygon:
    if isinstance(g, GeometrieObjekt):
        sh = objekt_zu_shapely(g)
        if not isinstance(sh, Polygon):
            raise ValueError("Tasche braucht eine geschlossene Kontur (Polygon).")
        return sh
    if isinstance(g, Polygon):
        return g
    raise ValueError(f"Geometrie-Typ nicht unterstuetzt fuer Tasche: {type(g)}")


def _offset_kontur_bahnen(
    polygon: Polygon, werkzeug: Werkzeug, parameter: TaschenParameter
) -> list[list[tuple[float, float]]]:
    """Erzeugt geschachtelte Konturen mit jeweils einem Stepover-Abstand."""
    r = werkzeug.durchmesser / 2.0
    stepover = werkzeug.durchmesser * (parameter.stepover_prozent / 100.0)

    # Erste Bahn: Aussenkante minus Werkzeug-Radius minus Aufmass
    aussen_offset = -(r + parameter.aufmass_wand)
    bahn = offset_polygon(polygon, aussen_offset)

    bahnen: list[list[tuple[float, float]]] = []
    while bahn is not None and not bahn.is_empty:
        if isinstance(bahn, Polygon):
            bahnen.append(list(bahn.exterior.coords))
        elif isinstance(bahn, MultiPolygon):
            for p in bahn.geoms:
                bahnen.append(list(p.exterior.coords))
        bahn = offset_polygon(bahn, -stepover)
        # Sicherheits-Bremse: Wenn Bahn nicht weiter schrumpft
        if bahn is not None and bahn.area < 1e-6:
            break

    return bahnen


def _adaptive_bahnen(
    polygon: Polygon, werkzeug: Werkzeug, parameter: TaschenParameter
) -> list[list[tuple[float, float]]]:
    """Adaptive Clearing — trochoidal-modulierte Offset-Bahnen (Master-Plan E4).

    Ansatz:
    - Sehr kleiner Stepover (10-15% statt 40%) → konstanter Werkzeug-Eingriff
    - Sinus-Modulation senkrecht zur Bahnrichtung → trochoidaler Pfad
    - Modulationsamplitude wird vom ``parameter.adaptive_amplitude_faktor``
      gesteuert (Default 0.05 * Durchmesser ≈ leichte Welligkeit)

    Das ist noch keine engagement-winkel-gesteuerte Implementierung wie
    Fusion HSM (= Voronoi + Restmaterial-Tracking), liefert aber merkliche
    Vorteile gegenueber OFFSET_KONTUR:
    - Konstanter Eingriff → laengere Standzeit
    - Hoehere Vorschuebe + tiefere Stepdowns moeglich
    - Sanftere Akustik (kein Rattern in Innenecken)

    Wer echte Adaptive will: Folge-Iteration mit Engagement-Calculator.
    """
    r = werkzeug.durchmesser / 2.0
    # Adaptive nutzt sehr kleinen Stepover (10-15% statt 40%)
    stepover = werkzeug.durchmesser * 0.12
    # Trochoidale Modulation: Amplitude relativ zum Werkzeug-Durchmesser.
    # Wenn der Parameter setzt wurde, nehmen wir den, sonst 5% des Durchmessers.
    amplitude = (
        parameter.adaptive_amplitude_faktor * werkzeug.durchmesser
        if getattr(parameter, "adaptive_amplitude_faktor", None) is not None
        else werkzeug.durchmesser * 0.05
    )
    wellen_pro_mm = getattr(parameter, "adaptive_wellen_pro_mm", 0.5)

    aussen_offset = -(r + parameter.aufmass_wand)
    bahn = offset_polygon(polygon, aussen_offset)
    bahnen: list[list[tuple[float, float]]] = []
    while bahn is not None and not bahn.is_empty:
        if isinstance(bahn, Polygon):
            bahnen.append(_modulieren(list(bahn.exterior.coords),
                                       amplitude=amplitude,
                                       wellen_pro_mm=wellen_pro_mm))
        elif isinstance(bahn, MultiPolygon):
            for p in bahn.geoms:
                bahnen.append(_modulieren(list(p.exterior.coords),
                                           amplitude=amplitude,
                                           wellen_pro_mm=wellen_pro_mm))
        bahn = offset_polygon(bahn, -stepover)
        if bahn is not None and bahn.area < 1e-6:
            break
    return bahnen


def _modulieren(
    pfad: list[tuple[float, float]],
    amplitude: float,
    wellen_pro_mm: float,
) -> list[tuple[float, float]]:
    """Trochoidale Sinus-Modulation senkrecht zur Bahnrichtung.

    Fuer jeden Pfad-Punkt:
    1. Tangente = Richtung zum naechsten Punkt
    2. Normale = Tangente um 90° gedreht
    3. Modulation = ``amplitude * sin(2π * weg_kumuliert * wellen_pro_mm)``
    4. Neuer Punkt = Original + Normale * Modulation

    Der erste und letzte Punkt werden NICHT moduliert (damit die Bahn
    geschlossen bleibt und Uebergaenge zwischen den Offset-Konturen
    konsistent sind).
    """
    import math
    if len(pfad) < 3 or amplitude <= 0 or wellen_pro_mm <= 0:
        return list(pfad)

    ergebnis: list[tuple[float, float]] = [pfad[0]]
    weg_kumuliert = 0.0
    for i in range(1, len(pfad) - 1):
        x_prev, y_prev = pfad[i - 1]
        x, y = pfad[i]
        x_next, y_next = pfad[i + 1]
        # Tangente: Mittelwert der beiden anliegenden Segmente
        tx = (x_next - x_prev) * 0.5
        ty = (y_next - y_prev) * 0.5
        laenge = math.hypot(tx, ty)
        if laenge < 1e-9:
            ergebnis.append((x, y))
            continue
        tx /= laenge
        ty /= laenge
        # Normale: 90° linksdrehung
        nx = -ty
        ny = tx
        # Weg vom letzten Punkt zum aktuellen
        weg_kumuliert += math.hypot(x - x_prev, y - y_prev)
        mod = amplitude * math.sin(2 * math.pi * weg_kumuliert * wellen_pro_mm)
        ergebnis.append((x + nx * mod, y + ny * mod))
    ergebnis.append(pfad[-1])
    return ergebnis


def _spiral_aussen_bahnen(
    polygon: Polygon, werkzeug: Werkzeug, parameter: TaschenParameter
) -> list[list[tuple[float, float]]]:
    """Spiralbahn von innen nach aussen.

    Gut fuer runde / quasi-runde Taschen, weil das Werkzeug konstant in Eingriff
    bleibt und nicht haeufig anheben muss.

    Vorgehen: Wir machen Offset von innen (Mittelpunkt) heraus mit Stepover-
    Inkrement und verbinden die Konturen in EINER durchgehenden Bahn.
    """
    r = werkzeug.durchmesser / 2.0
    stepover = werkzeug.durchmesser * (parameter.stepover_prozent / 100.0)

    # Innenraum (minus Aufmass + Werkzeug-Radius)
    innen = offset_polygon(polygon, -(r + parameter.aufmass_wand))
    if innen is None or innen.is_empty:
        return []

    # Erzeuge geschachtelte Ringe von innen nach aussen
    ringe: list[list[tuple[float, float]]] = []
    bahn = innen
    # Starte ganz innen mit kleinem Polygon
    aktuelle_einschraenkung = -werkzeug.durchmesser * 5  # weit innen
    inner_seed = offset_polygon(innen, aktuelle_einschraenkung)
    if inner_seed is None or inner_seed.is_empty:
        # Polygon zu klein fuer mehrere Ringe — nimm einfach den innen
        if isinstance(innen, Polygon):
            ringe.append(list(innen.exterior.coords))
        elif isinstance(innen, MultiPolygon):
            for p in innen.geoms:
                ringe.append(list(p.exterior.coords))
        return ringe

    # Iteriere Schicht fuer Schicht nach aussen
    aktuelle = inner_seed
    while aktuelle is not None and not aktuelle.is_empty:
        if isinstance(aktuelle, Polygon):
            ringe.append(list(aktuelle.exterior.coords))
        elif isinstance(aktuelle, MultiPolygon):
            for p in aktuelle.geoms:
                ringe.append(list(p.exterior.coords))
        # Naechster Ring weiter aussen
        aktuelle = offset_polygon(aktuelle, stepover)
        # Stoppe wenn ueber innen-Grenze hinaus
        if aktuelle is None or aktuelle.is_empty:
            break
        if not aktuelle.intersects(innen):
            break
        # Clip an innen
        aktuelle = aktuelle.intersection(innen)

    # Letzte Bahn: aussen-Kontur selbst (entlang Wand) als Schlichtgang
    if isinstance(innen, Polygon):
        ringe.append(list(innen.exterior.coords))
    elif isinstance(innen, MultiPolygon):
        for p in innen.geoms:
            ringe.append(list(p.exterior.coords))

    return ringe


def _parallel_bahnen(
    polygon: Polygon, werkzeug: Werkzeug, parameter: TaschenParameter
) -> list[list[tuple[float, float]]]:
    """Erzeugt parallele Linien-Bahnen (Zickzack-Schraffur).

    Die Bahnen verlaufen entlang der X-Achse mit Abstand stepover.
    """
    r = werkzeug.durchmesser / 2.0
    stepover = werkzeug.durchmesser * (parameter.stepover_prozent / 100.0)

    # Innenraum (Polygon minus Aufmass-Wand minus Werkzeug-Radius)
    innen = offset_polygon(polygon, -(r + parameter.aufmass_wand))
    if innen is None or innen.is_empty:
        return []

    bb = innen.bounds  # minx, miny, maxx, maxy
    minx, miny, maxx, maxy = bb

    bahnen: list[list[tuple[float, float]]] = []
    y = miny
    richtung = 1
    while y <= maxy + 1e-9:
        linie = LineString([(minx - 1, y), (maxx + 1, y)])
        clip = linie.intersection(innen)
        if not clip.is_empty:
            segmente = _linestring_zu_segmente(clip)
            for seg in segmente:
                if richtung == -1:
                    seg = list(reversed(seg))
                bahnen.append(seg)
        richtung *= -1
        y += stepover

    return bahnen


def _linestring_zu_segmente(geo) -> list[list[tuple[float, float]]]:
    """Konvertiert einen MultiLineString/LineString in Listen von Punkten."""
    geom_typ = geo.geom_type
    if geom_typ == "LineString":
        return [list(geo.coords)]
    if geom_typ == "MultiLineString":
        return [list(g.coords) for g in geo.geoms]
    if geom_typ == "GeometryCollection":
        out: list[list[tuple[float, float]]] = []
        for g in geo.geoms:
            out.extend(_linestring_zu_segmente(g))
        return out
    return []


def _generiere_bewegungen(
    bahnen: list[list[tuple[float, float]]],
    werkzeug: Werkzeug,
    parameter: TaschenParameter,
) -> list[Bewegung]:
    bewegungen: list[Bewegung] = []
    z_oben = 0.0
    z_unten = -abs(parameter.max_tiefe) + parameter.aufmass_boden
    stepdown = abs(parameter.stepdown)

    z_aktuell = z_oben
    while z_aktuell > z_unten + 1e-9:
        z_aktuell = max(z_aktuell - stepdown, z_unten)
        for bahn in bahnen:
            if len(bahn) < 2:
                continue
            start_x, start_y = bahn[0]
            bewegungen.append(
                Bewegung(BewegungsTyp.EILGANG, start_x, start_y, parameter.sicherheitshoehe)
            )
            bewegungen.append(
                Bewegung(BewegungsTyp.PLUNGE, start_x, start_y, z_aktuell,
                         feed=parameter.eintauch_vorschub)
            )
            for x, y in bahn[1:]:
                bewegungen.append(
                    Bewegung(BewegungsTyp.LINEAR, x, y, z_aktuell, feed=parameter.vorschub)
                )
            bewegungen.append(
                Bewegung(BewegungsTyp.EILGANG, x, y, parameter.sicherheitshoehe)
            )
    return bewegungen


__all__ = ["erzeuge_tasche_toolpath"]

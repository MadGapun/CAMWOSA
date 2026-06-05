"""Rampen-Eintauchen statt senkrechtem Plunge (Cluster J5, Issue #46).

Senkrechtes Eintauchen (`PLUNGE`) ist hart fuer Fraeser — besonders fuer
nicht-zentrumsschneidende Werkzeuge in Holz/Alu (Hitze, Bruch, schlechte
Boden-Oberflaeche). Profis tauchen **rampend** ein: das Werkzeug bewegt sich
beim Absenken in XY entlang des kommenden Schnitts.

``rampe_eintauchen`` ist ein **endpunkt-treuer** Post-Pass auf einem Toolpath:
jeder senkrechte Plunge, dem ein Schnitt folgt, wird durch eine **Zickzack-Rampe**
entlang der Folgeschnitt-Richtung ersetzt. Die Rampe endet exakt am Plunge-Punkt
auf Schnitttiefe — der eigentliche Schnitt laeuft danach unveraendert weiter.

Konvention: ``material_oberkante`` (Default 0.0 = CAMWOSA-Standard, Z-Null oben).
Nur der **Teil im Material** wird gerampt; die Luft darueber bleibt schneller
Plunge. Greift nur, wenn ein Schnitt mit XY-Richtung folgt (sonst — z.B. Bohren —
bleibt der Plunge unveraendert).
"""

from __future__ import annotations

import math
from dataclasses import replace

from camwosa.gcode.toolpath import Bewegung, BewegungsTyp, Toolpath

_SCHNITT = (BewegungsTyp.LINEAR, BewegungsTyp.BOGEN_CW, BewegungsTyp.BOGEN_CCW)


def _naechste_schnittrichtung(bew, i, x, y, eps):
    """Findet die XY-Richtung des ersten echten Schnitts nach Index i."""
    for j in range(i + 1, len(bew)):
        nb = bew[j]
        if nb.typ == BewegungsTyp.EILGANG:
            return None  # kein direkter Schnitt → nicht rampen
        if nb.typ in _SCHNITT and (abs(nb.x - x) > eps or abs(nb.y - y) > eps):
            return (nb.x - x, nb.y - y)
    return None


def rampe_eintauchen(
    toolpath: Toolpath,
    *,
    winkel_grad: float = 5.0,
    material_oberkante: float = 0.0,
    max_rampe_mm: float | None = None,
    max_passes: int = 30,
    rampe_feed: float | None = None,
    rampe_faktor: float = 1.0,
    eps: float = 1e-9,
) -> Toolpath:
    """Ersetzt senkrechte Plunges durch Rampen entlang des Folgeschnitts.

    Args:
        winkel_grad: Rampen-Winkel zur XY-Ebene (flacher = schonender, laenger).
        material_oberkante: Z-Hoehe der Materialoberkante (Default 0).
        max_rampe_mm: optionale Deckelung der Rampen-Segmentlaenge.
        max_passes: zu kurze Folgeschnitte → mehr als so viele Zickzack-Laeufe →
            Fallback auf normalen Plunge (Segment zu kurz fuer sinnvolle Rampe).
    """
    bew = toolpath.bewegungen
    if len(bew) < 2:
        return toolpath
    tan = math.tan(math.radians(winkel_grad))
    if tan <= 0:
        return toolpath

    neu: list[Bewegung] = [bew[0]]
    prev = bew[0]
    geaendert = False

    for i in range(1, len(bew)):
        b = bew[i]
        ist_senkrecht_plunge = (
            b.typ == BewegungsTyp.PLUNGE
            and b.z < prev.z - eps
            and abs(b.x - prev.x) < eps
            and abs(b.y - prev.y) < eps
        )
        if not ist_senkrecht_plunge:
            neu.append(b)
            prev = b
            continue

        richtung = _naechste_schnittrichtung(bew, i, b.x, b.y, eps)
        z_top = min(prev.z, material_oberkante)
        depth = z_top - b.z
        if richtung is None or depth <= eps:
            neu.append(b)  # nichts zu rampen
            prev = b
            continue

        dx, dy = richtung
        seglen = math.hypot(dx, dy)
        run = depth / tan
        r = min(run, seglen)
        if max_rampe_mm:
            r = min(r, max_rampe_mm)
        if r < eps or run / r > max_passes:
            neu.append(b)  # Segment zu kurz fuer sinnvolle Rampe → normaler Plunge
            prev = b
            continue

        ux, uy = dx / seglen, dy / seglen

        # Luft-Teil ueber Material schnell ueberbruecken (bleibt Plunge)
        if prev.z > z_top + eps:
            neu.append(Bewegung(BewegungsTyp.PLUNGE, b.x, b.y, z_top,
                                feed=b.feed, kommentar="Anfahrt bis Material"))

        # Q2: getrennter Rampen-Feed. Vorrang:
        #   Bewegung.rampe_feed  >  Funktions-rampe_feed  >  b.feed * rampe_faktor
        if b.rampe_feed is not None:
            rampen_feed = b.rampe_feed
        elif rampe_feed is not None:
            rampen_feed = rampe_feed
        else:
            rampen_feed = b.feed * rampe_faktor if b.feed is not None else None

        # Zickzack-Rampe von z_top → b.z, XY zwischen P und P+d*r
        o = 0.0
        s = 1.0
        rest = run
        feed = rampen_feed
        while rest > eps:
            ziel_o = r if s > 0 else 0.0
            leg = abs(ziel_o - o)
            if leg > rest:  # Teil-Leg am Ende
                ziel_o = o + s * rest
                leg = rest
            o = ziel_o
            rest -= leg
            z = max(b.z, z_top - depth * ((run - rest) / run))
            neu.append(Bewegung(BewegungsTyp.LINEAR, b.x + ux * o, b.y + uy * o, z,
                                feed=feed, kommentar="Rampen-Eintauchen"))
            if abs(o - r) < eps or abs(o) < eps:
                s = -s

        # Endpunkt-Treue: exakt am Plunge-Punkt auf Schnitttiefe enden
        letzte = neu[-1]
        if (abs(letzte.x - b.x) > eps or abs(letzte.y - b.y) > eps
                or abs(letzte.z - b.z) > eps):
            neu.append(Bewegung(BewegungsTyp.LINEAR, b.x, b.y, b.z,
                                feed=feed, kommentar="Rampen-Ende"))

        prev = Bewegung(BewegungsTyp.LINEAR, b.x, b.y, b.z, feed=feed)
        geaendert = True

    if not geaendert:
        return toolpath
    meta = dict(toolpath.metadaten)
    meta["rampen_eintauchen"] = True
    return replace(toolpath, bewegungen=neu, metadaten=meta)


__all__ = ["rampe_eintauchen"]

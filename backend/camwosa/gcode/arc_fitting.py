"""Arc-Fitting: lineare Punktfolgen auf Kreisboegen zu G2/G3 zusammenfassen.

Cluster J1 (Issue #46). Die CAM-Generatoren sampeln Kreise, Boegen, Helix und
Circular-Pocketing in viele kurze G1-Segmente. Der Postprozessor *kann* aber
G2/G3 (`arc_move`). Dieser Post-Processing-Schritt erkennt Folgen von LINEAR-
Bewegungen, die innerhalb einer Toleranz auf einem gemeinsamen Kreis liegen,
und ersetzt sie durch eine einzige `BOGEN_CW` / `BOGEN_CCW`-Bewegung (i/j
relativ zum Startpunkt, GRBL-Konvention).

Effekt: massive G-Code-Reduktion (ein Kreis mit 64 Segmenten → 1-2 Boegen),
ruhigerer Maschinenlauf (kontinuierliche Bogen-Interpolation statt
Polygonzug).

Sicherheits-Regeln:
- Nur LINEAR-Bewegungen werden gefittet (Eilgang/Plunge/bestehende Boegen
  bleiben unveraendert).
- Nur bei **konstantem Z** (echte 2D-Boegen in der XY-Ebene; Helix-Boegen mit
  Z-Interpolation sind ein separater, fortgeschrittener Fall).
- Nur bei **konstantem Feed**.
- Bogen-Gesamtwinkel < 340° (GRBL/Postprozessor-sicher; Vollkreise vermeiden).
- Mindest-Segmentzahl, damit sich der Fit lohnt.

API: `fitte_boegen(bewegungen, toleranz_mm=...) -> list[Bewegung]`
     `fitte_toolpath(toolpath, ...) -> Toolpath` (Convenience)
"""

from __future__ import annotations

import math
from dataclasses import replace

from camwosa.gcode.toolpath import Bewegung, BewegungsTyp, Toolpath


def _umkreis(
    p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float],
) -> tuple[float, float, float] | None:
    """Mittelpunkt + Radius des Kreises durch 3 Punkte. None wenn kollinear."""
    ax, ay = p1
    bx, by = p2
    cx, cy = p3
    d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-9:
        return None  # kollinear
    a2 = ax * ax + ay * ay
    b2 = bx * bx + by * by
    c2 = cx * cx + cy * cy
    ux = (a2 * (by - cy) + b2 * (cy - ay) + c2 * (ay - by)) / d
    uy = (a2 * (cx - bx) + b2 * (ax - cx) + c2 * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    return ux, uy, r


def _kreuz(o: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    """Kreuzprodukt (a-o) x (b-o) — Vorzeichen = Drehrichtung."""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def fitte_boegen(
    bewegungen: list[Bewegung],
    *,
    toleranz_mm: float = 0.05,
    min_segmente: int = 4,
    max_radius_mm: float = 2000.0,
    max_bogen_grad: float = 340.0,
) -> list[Bewegung]:
    """Ersetzt fitbare LINEAR-Folgen durch BOGEN-Bewegungen.

    Args:
        toleranz_mm: max. Abweichung eines Punkts vom Fit-Kreis.
        min_segmente: Mindestzahl LINEAR-Segmente die ein Bogen ersetzen muss.
        max_radius_mm: groessere "Kreise" sind faktisch Geraden → nicht fitten.
        max_bogen_grad: Bogen-Winkel-Limit (Vollkreise vermeiden).

    Returns:
        Neue Bewegungsliste (Original bleibt unveraendert).
    """
    if len(bewegungen) < min_segmente + 1:
        return list(bewegungen)

    ergebnis: list[Bewegung] = []
    i = 0
    n = len(bewegungen)
    while i < n:
        b = bewegungen[i]
        # Start eines moeglichen Laufs: vorige Bewegung liefert den Startpunkt.
        # Nur LINEAR-Laeufe mit konstantem Z + Feed fitten.
        if (
            b.typ != BewegungsTyp.LINEAR
            or i == 0
            or not _ist_fitbar(bewegungen[i - 1])
        ):
            ergebnis.append(b)
            i += 1
            continue

        start = bewegungen[i - 1]
        z = b.z
        feed = b.feed
        # Sammle den maximalen zusammenhaengenden LINEAR-Lauf mit gleichem z+feed
        lauf_punkte: list[tuple[float, float]] = [(start.x, start.y)]
        lauf_ende = i
        while lauf_ende < n:
            bb = bewegungen[lauf_ende]
            if (
                bb.typ == BewegungsTyp.LINEAR
                and abs(bb.z - z) < 1e-6
                and bb.feed == feed
            ):
                lauf_punkte.append((bb.x, bb.y))
                lauf_ende += 1
            else:
                break

        # lauf_punkte enthaelt Startpunkt + alle LINEAR-Endpunkte des Laufs.
        if len(lauf_punkte) < min_segmente + 1:
            # zu kurz fuer einen Fit → unveraendert uebernehmen
            for k in range(i, lauf_ende):
                ergebnis.append(bewegungen[k])
            i = lauf_ende
            continue

        # Greedy durch den Lauf: laengste Boegen finden, Rest als LINEAR.
        gefittet = _fitte_lauf(
            lauf_punkte, z, feed,
            toleranz_mm, min_segmente, max_radius_mm, max_bogen_grad,
            kommentar_vorlage=b.kommentar,
        )
        ergebnis.extend(gefittet)
        i = lauf_ende

    return ergebnis


def _ist_fitbar(b: Bewegung) -> bool:
    """Kann diese Bewegung als Startpunkt eines Bogen-Laufs dienen?"""
    return b.typ in (BewegungsTyp.LINEAR, BewegungsTyp.PLUNGE, BewegungsTyp.EILGANG)


def _fitte_lauf(
    punkte: list[tuple[float, float]],
    z: float,
    feed: float | None,
    toleranz: float,
    min_segmente: int,
    max_radius: float,
    max_bogen_grad: float,
    *,
    kommentar_vorlage: str = "",
) -> list[Bewegung]:
    """Fittet einen einzelnen LINEAR-Lauf (inkl. Startpunkt) zu Boegen+Geraden.

    punkte[0] ist der Startpunkt (von der vorigen Bewegung), punkte[1:] sind
    die LINEAR-Endpunkte.
    """
    out: list[Bewegung] = []
    m = len(punkte)
    i = 0  # Index des aktuellen Startpunkts in `punkte`
    while i < m - 1:
        # Versuche ab i den laengsten Bogen
        bogen_ende = _laengster_bogen(
            punkte, i, toleranz, max_radius, max_bogen_grad,
        )
        anzahl_segmente = bogen_ende - i
        if anzahl_segmente >= min_segmente:
            # Bogen von punkte[i] zu punkte[bogen_ende]
            kreis = _umkreis(punkte[i], punkte[i + anzahl_segmente // 2], punkte[bogen_ende])
            if kreis is not None:
                cx, cy, _r = kreis
                # Drehrichtung aus der Mitte des Bogens
                kr = _kreuz(punkte[i], punkte[i + 1], punkte[bogen_ende])
                typ = BewegungsTyp.BOGEN_CCW if kr > 0 else BewegungsTyp.BOGEN_CW
                ex, ey = punkte[bogen_ende]
                out.append(Bewegung(
                    typ=typ, x=ex, y=ey, z=z, feed=feed,
                    i=cx - punkte[i][0], j=cy - punkte[i][1],
                    kommentar="arc-fit" if not kommentar_vorlage else kommentar_vorlage,
                ))
                i = bogen_ende
                continue
        # Kein Bogen → ein LINEAR-Segment ausgeben
        ex, ey = punkte[i + 1]
        out.append(Bewegung(
            typ=BewegungsTyp.LINEAR, x=ex, y=ey, z=z, feed=feed,
            kommentar=kommentar_vorlage,
        ))
        i += 1
    return out


def _laengster_bogen(
    punkte: list[tuple[float, float]],
    start: int,
    toleranz: float,
    max_radius: float,
    max_bogen_grad: float,
) -> int:
    """Index des letzten Punkts, der ab `start` noch auf demselben Kreis liegt.

    Gibt `start` zurueck wenn kein Bogen (mind. 2 Segmente) moeglich ist.
    """
    m = len(punkte)
    if start + 2 >= m:
        return start
    kreis = _umkreis(punkte[start], punkte[start + 1], punkte[start + 2])
    if kreis is None:
        return start
    cx, cy, r = kreis
    if r > max_radius or r < 1e-6:
        return start

    # Drehrichtung festlegen
    drehung = _kreuz(punkte[start], punkte[start + 1], punkte[start + 2])
    if abs(drehung) < 1e-12:
        return start
    ccw = drehung > 0

    def winkel(p: tuple[float, float]) -> float:
        return math.atan2(p[1] - cy, p[0] - cx)

    ende = start + 2
    prev_w = winkel(punkte[start])
    kumuliert = 0.0
    # pruefe Punkte start+1 .. weiter
    for k in range(start + 1, m):
        px, py = punkte[k]
        # auf dem Kreis?
        if abs(math.hypot(px - cx, py - cy) - r) > toleranz:
            break
        # monotone Drehrichtung + Winkel akkumulieren
        w = winkel(punkte[k])
        dw = w - prev_w
        # auf (-pi, pi] normieren
        while dw <= -math.pi:
            dw += 2 * math.pi
        while dw > math.pi:
            dw -= 2 * math.pi
        # Richtung muss konsistent sein
        if ccw and dw < -1e-9:
            break
        if not ccw and dw > 1e-9:
            break
        kumuliert += abs(dw)
        if math.degrees(kumuliert) > max_bogen_grad:
            break
        prev_w = w
        ende = k
    return ende


def fitte_toolpath(
    toolpath: Toolpath,
    *,
    toleranz_mm: float = 0.05,
    min_segmente: int = 4,
) -> Toolpath:
    """Convenience: Arc-Fitting auf einen ganzen Toolpath anwenden.

    Gibt eine neue Toolpath-Kopie mit gefitteten Bewegungen + Metadaten-Marker.
    """
    neue = fitte_boegen(
        toolpath.bewegungen, toleranz_mm=toleranz_mm, min_segmente=min_segmente,
    )
    meta = dict(toolpath.metadaten)
    meta["arc_fitted"] = True
    meta["arc_fit_bewegungen_vorher"] = len(toolpath.bewegungen)
    meta["arc_fit_bewegungen_nachher"] = len(neue)
    return replace(toolpath, bewegungen=neue, metadaten=meta)


__all__ = ["fitte_boegen", "fitte_toolpath"]

"""Intelligente Fahrwege: kurze Wege (J9) + knappe Freifahrten (J10).

Cluster J9/J10 (Issue #52, Markus' Anforderung). Post-Processing auf einem
Toolpath — analog zu `arc_fitting.py`:

- **J9 Reihenfolge-Optimierung:** die Schnitt-Gruppen (Konturen, Tasche-Bahnen,
  Bohrungen) werden per Nearest-Neighbor so umsortiert, dass der gesamte
  Eilgang-Verfahrweg minimal wird → kürzere Bearbeitungszeit.
- **J10 Knappe Freifahrten:** Zwischen-Eilgänge laufen knapp (einstellbar) über
  der Geometrie statt auf voller Sicherheitshöhe. Erste Anfahrt + Schluss-
  Rückzug bleiben sicher auf Sicherheitshöhe.

Beide Schritte sind **opt-in** und **konservativ**: bei unerwarteter Toolpath-
Struktur wird der Original-Toolpath unverändert zurückgegeben (nie schlechter).
"""

from __future__ import annotations

import math
from dataclasses import replace

from camwosa.gcode.toolpath import Bewegung, BewegungsTyp, Toolpath


def _ist_eilgang(b: Bewegung) -> bool:
    return b.typ == BewegungsTyp.EILGANG


def _zerlege_in_gruppen(
    bewegungen: list[Bewegung],
) -> tuple[list[Bewegung], list[list[Bewegung]], list[Bewegung]]:
    """Trennt den Toolpath in [Anfahrt-Rapids, Schnitt-Gruppen, Schluss-Rapids].

    Schnitt-Gruppe = zusammenhaengender Lauf von Nicht-Eilgang-Bewegungen
    (PLUNGE/LINEAR/BOGEN). Die Eilgaenge dazwischen sind Repositionierung.
    """
    n = len(bewegungen)
    # fuehrende Eilgaenge = Anfahrt
    i = 0
    while i < n and _ist_eilgang(bewegungen[i]):
        i += 1
    anfahrt = bewegungen[:i]

    # abschliessende Eilgaenge = Schluss-Rueckzug
    j = n
    while j > i and _ist_eilgang(bewegungen[j - 1]):
        j -= 1
    schluss = bewegungen[j:]

    # Mitte in Gruppen zerlegen (Cut-Runs), Rapids dazwischen verwerfen
    gruppen: list[list[Bewegung]] = []
    aktuell: list[Bewegung] = []
    for b in bewegungen[i:j]:
        if _ist_eilgang(b):
            if aktuell:
                gruppen.append(aktuell)
                aktuell = []
        else:
            aktuell.append(b)
    if aktuell:
        gruppen.append(aktuell)
    return anfahrt, gruppen, schluss


def _entry(g: list[Bewegung]) -> tuple[float, float]:
    return (g[0].x, g[0].y)


def _exit(g: list[Bewegung]) -> tuple[float, float]:
    return (g[-1].x, g[-1].y)


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def optimiere_reihenfolge(
    toolpath: Toolpath,
    *,
    start: tuple[float, float] = (0.0, 0.0),
) -> Toolpath:
    """J9: sortiert die Schnitt-Gruppen per Nearest-Neighbor um (kurze Wege).

    Konservativ: bei < 2 Gruppen oder unklarer Struktur unveraendert.
    """
    anfahrt, gruppen, schluss = _zerlege_in_gruppen(toolpath.bewegungen)
    if len(gruppen) < 2:
        return toolpath

    # Sicherheits-/Repositionierungs-Hoehe = hoechster Eilgang-Z (Anfahrt/Schluss)
    rapids = [b for b in toolpath.bewegungen if _ist_eilgang(b)]
    z_safe = max((b.z for b in rapids), default=toolpath.sicherheitshoehe)

    # Nearest-Neighbor ueber die Entry-Punkte
    verbleibend = list(range(len(gruppen)))
    reihenfolge: list[int] = []
    pos = start
    while verbleibend:
        k = min(verbleibend, key=lambda idx: _dist(pos, _entry(gruppen[idx])))
        reihenfolge.append(k)
        verbleibend.remove(k)
        pos = _exit(gruppen[k])

    # Neu zusammenbauen: Anfahrt zur ersten Gruppe, dann Gruppen + Reposition-Rapids
    neu: list[Bewegung] = []
    erste = gruppen[reihenfolge[0]]
    ex, ey = _entry(erste)
    neu.append(Bewegung(BewegungsTyp.EILGANG, ex, ey, z_safe,
                        kommentar="Anfahrt (Fahrweg-Opt)"))
    for pos_i, gi in enumerate(reihenfolge):
        g = gruppen[gi]
        if pos_i > 0:
            # Reposition: hoch am vorigen Exit, rueber zum neuen Entry
            px, py = _exit(gruppen[reihenfolge[pos_i - 1]])
            nx, ny = _entry(g)
            neu.append(Bewegung(BewegungsTyp.EILGANG, px, py, z_safe))
            neu.append(Bewegung(BewegungsTyp.EILGANG, nx, ny, z_safe))
        neu.extend(g)
    # Schluss-Rueckzug
    lx, ly = _exit(gruppen[reihenfolge[-1]])
    neu.append(Bewegung(BewegungsTyp.EILGANG, lx, ly, z_safe, kommentar="Rueckzug"))

    meta = dict(toolpath.metadaten)
    meta["fahrweg_optimiert"] = True
    return replace(toolpath, bewegungen=neu, metadaten=meta)


def senke_freifahrten(
    toolpath: Toolpath,
    *,
    freifahrt_hoehe: float,
    sicherheitshoehe: float | None = None,
) -> Toolpath:
    """J10: senkt Zwischen-Eilgänge auf `freifahrt_hoehe` (knapp über Geometrie).

    Die **erste** Anfahrt und der **letzte** Rückzug bleiben auf der vollen
    Sicherheitshöhe (sicheres Anfahren/Verlassen). Nur Eilgänge dazwischen, die
    auf/über Sicherheitshöhe liegen, werden auf `freifahrt_hoehe` gesenkt.
    """
    bew = toolpath.bewegungen
    if not bew:
        return toolpath
    z_safe = sicherheitshoehe if sicherheitshoehe is not None else toolpath.sicherheitshoehe
    if freifahrt_hoehe >= z_safe:
        return toolpath  # nichts zu senken

    # Index der ersten + letzten "Schnitt"-Bewegung bestimmen (Grenzen schuetzen)
    erste_cut = next((k for k, b in enumerate(bew) if not _ist_eilgang(b)), None)
    letzte_cut = next((len(bew) - 1 - k for k, b in enumerate(reversed(bew))
                       if not _ist_eilgang(b)), None)
    if erste_cut is None:
        return toolpath

    neu: list[Bewegung] = []
    for k, b in enumerate(bew):
        # nur Eilgänge ZWISCHEN erstem und letztem Schnitt senken
        if (_ist_eilgang(b) and erste_cut < k < letzte_cut
                and b.z >= z_safe - 1e-9):
            neu.append(replace(b, z=freifahrt_hoehe))
        else:
            neu.append(b)
    meta = dict(toolpath.metadaten)
    meta["freifahrt_hoehe"] = freifahrt_hoehe
    return replace(toolpath, bewegungen=neu, metadaten=meta)


def optimiere_fahrwege(
    toolpath: Toolpath,
    *,
    reihenfolge: bool = True,
    freifahrt_hoehe: float | None = None,
    start: tuple[float, float] = (0.0, 0.0),
) -> Toolpath:
    """Convenience: J9 (Reihenfolge) + J10 (Freifahrt senken) kombiniert."""
    tp = toolpath
    if reihenfolge:
        tp = optimiere_reihenfolge(tp, start=start)
    if freifahrt_hoehe is not None:
        tp = senke_freifahrten(tp, freifahrt_hoehe=freifahrt_hoehe)
    return tp


def eilgang_weg(toolpath: Toolpath) -> float:
    """Gesamter Eilgang-Verfahrweg (mm) — Metrik fuer die Optimierung."""
    bew = toolpath.bewegungen
    if len(bew) < 2:
        return 0.0
    s = 0.0
    prev = bew[0]
    for b in bew[1:]:
        if _ist_eilgang(b):
            s += math.sqrt((b.x - prev.x) ** 2 + (b.y - prev.y) ** 2 + (b.z - prev.z) ** 2)
        prev = b
    return s


__all__ = [
    "eilgang_weg",
    "optimiere_fahrwege",
    "optimiere_reihenfolge",
    "senke_freifahrten",
]

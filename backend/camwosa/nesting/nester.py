"""Verschnittoptimierung (Nesting) fuer mehrere Teile auf einer Platte.

Phase 1: Bin-Packing mit rectpack (MIT). Behandelt rechteckige Bounding-Boxen.
Phase 1+: No-Fit-Polygon mit nest2D (LGPL, optional).

Eingaben:
- Plattenmaterial: Laenge x Breite
- Teile: Liste von (id, breite, hoehe, anzahl, faserrichtung_y_pflicht)

Ausgabe:
- Anordnungs-Plan: pro Teil-Instanz (x, y, rotation, platte_index)
- Verschnitt-Statistik

Siehe Wiki: docs/wiki/Nesting.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from rectpack import (
    PackingMode,
    SORT_LSIDE,
    SORT_NONE,
    newPacker,
)


class NestingStrategie(str, Enum):
    BIN_PACKING = "bin_packing"
    NO_FIT_POLYGON = "no_fit_polygon"


@dataclass
class TeilDefinition:
    """Definition eines Teils das genested werden soll."""

    id: str
    breite: float
    hoehe: float
    anzahl: int = 1
    faser_parallel_y: bool = False
    name: str = ""


@dataclass
class PlattenDefinition:
    """Definition einer verfuegbaren Platte."""

    id: str
    breite: float
    hoehe: float


@dataclass
class TeilPlatzierung:
    """Eine konkrete Platzierung eines Teils auf einer Platte."""

    teil_id: str
    instanz_index: int  # bei mehreren Stueck: 0..n-1
    platte_id: str
    x: float
    y: float
    breite: float
    hoehe: float
    rotation_grad: float = 0.0


@dataclass
class NestingErgebnis:
    platzierungen: list[TeilPlatzierung] = field(default_factory=list)
    nicht_platziert: list[tuple[str, int]] = field(default_factory=list)  # (teil_id, instanz)
    platten_genutzt: list[str] = field(default_factory=list)
    verschnitt_prozent: float = 0.0
    genutzte_flaeche: float = 0.0
    gesamt_flaeche: float = 0.0


def neste(
    teile: Iterable[TeilDefinition],
    platten: Iterable[PlattenDefinition],
    *,
    abstand_zwischen_teilen: float = 5.0,
    strategie: NestingStrategie = NestingStrategie.BIN_PACKING,
) -> NestingErgebnis:
    """Fuehrt Verschnittoptimierung durch und gibt das Ergebnis zurueck.

    Args:
        teile: Teile mit Bounding-Boxen
        platten: Verfuegbare Platten
        abstand_zwischen_teilen: Mindest-Abstand in mm (Werkzeug-Durchmesser + Sicherheit)
        strategie: aktuell nur BIN_PACKING. NO_FIT_POLYGON braucht nest2D.
    """
    if strategie == NestingStrategie.NO_FIT_POLYGON:
        raise NotImplementedError(
            "NO_FIT_POLYGON braucht nest2D-Bibliothek (LGPL). "
            "Optional via 'pip install nest2D' installieren."
        )

    teile_liste = list(teile)
    platten_liste = list(platten)
    if not teile_liste or not platten_liste:
        return NestingErgebnis()

    packer = newPacker(mode=PackingMode.Offline, sort_algo=SORT_LSIDE, rotation=True)

    # Teile mit Abstand-Padding
    pad = abstand_zwischen_teilen
    teil_index_map: dict[int, tuple[str, int, bool]] = {}
    rid = 0
    for t in teile_liste:
        for i in range(t.anzahl):
            packer.add_rect(
                int(round((t.breite + pad) * 1000)),
                int(round((t.hoehe + pad) * 1000)),
                rid=rid,
            )
            teil_index_map[rid] = (t.id, i, t.faser_parallel_y)
            rid += 1

    # Platten
    for p in platten_liste:
        packer.add_bin(
            int(round(p.breite * 1000)),
            int(round(p.hoehe * 1000)),
            count=1,
        )

    packer.pack()

    ergebnis = NestingErgebnis()
    teil_lookup = {t.id: t for t in teile_liste}
    platten_lookup = {i: p for i, p in enumerate(platten_liste)}

    for bin_index, abin in enumerate(packer):
        if not abin:
            continue
        platte_id = platten_lookup[bin_index].id
        ergebnis.platten_genutzt.append(platte_id)
        for r in abin:
            tid, idx, faser_y_pflicht = teil_index_map[r.rid]
            t = teil_lookup[tid]
            # Pruefen ob rotiert: Originalbreite vs. r.width
            orig_breite_int = int(round((t.breite + pad) * 1000))
            wurde_rotiert = (r.width != orig_breite_int)
            if faser_y_pflicht and wurde_rotiert:
                # Nicht erlaubt -> uebersprungen
                ergebnis.nicht_platziert.append((tid, idx))
                continue
            ergebnis.platzierungen.append(TeilPlatzierung(
                teil_id=tid,
                instanz_index=idx,
                platte_id=platte_id,
                x=r.x / 1000.0,
                y=r.y / 1000.0,
                breite=t.breite,
                hoehe=t.hoehe,
                rotation_grad=90.0 if wurde_rotiert else 0.0,
            ))

    # Nicht platzierte Teile finden
    platziert_ids = {(p.teil_id, p.instanz_index) for p in ergebnis.platzierungen}
    for rid, (tid, idx, _) in teil_index_map.items():
        if (tid, idx) not in platziert_ids and (tid, idx) not in ergebnis.nicht_platziert:
            ergebnis.nicht_platziert.append((tid, idx))

    # Statistik
    genutzt = sum(p.breite * p.hoehe for p in ergebnis.platzierungen)
    gesamt = sum(
        platte.breite * platte.hoehe
        for platte in platten_liste
        if platte.id in ergebnis.platten_genutzt
    )
    ergebnis.genutzte_flaeche = genutzt
    ergebnis.gesamt_flaeche = gesamt
    ergebnis.verschnitt_prozent = (
        (1 - genutzt / gesamt) * 100 if gesamt > 0 else 0.0
    )
    return ergebnis


__all__ = [
    "NestingErgebnis",
    "NestingStrategie",
    "PlattenDefinition",
    "TeilDefinition",
    "TeilPlatzierung",
    "neste",
]

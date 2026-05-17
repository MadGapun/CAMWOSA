"""Z-Grid-Diagnose: ist mein Werkstueck eben aufgespannt? (A47-Rest, Cluster H)

Hintergrund (Markus' Workflow):
Bevor man einen 3D-Job startet, probe-touched man typischerweise N×M Punkte
auf der Werkstueck-Oberflaeche (z.B. via CNCjs Z-Probing). Wenn das Werkstueck
schief ist, wird ein 3D-Relief falsch — und Markus merkt es erst wenn das
Werkstueck schon teilweise zerstoert ist.

Dieses Modul nimmt eine Liste von (x, y, z_gemessen)-Punkten und analysiert:
1. **Ebenheit** — Standardabweichung + Min/Max
2. **Best-fit-Plane** — Neigung in Grad
3. **Lokale Abweichungen** — wo ist's wirklich uneben
4. **Empfehlung** — eben OK / leichte Neigung / starke Neigung / unebene Oberflaeche

Output ist UI-freundlich: liefert direkt Klartext + Schwellwerte die der User
versteht ("max. 0.3 mm Abweichung — fuer Schruppen OK, fuer Schlichten kritisch").

API: POST /api/diagnostics/z-grid mit ZGridDaten -> ZGridErgebnis
"""

from __future__ import annotations

import math
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class EbenheitsBefund(str, Enum):
    """Empfehlung an den User basierend auf der Diagnose."""
    EBEN_OK = "eben_ok"  # < 0.1 mm Abweichung — alles fein
    LEICHTE_NEIGUNG = "leichte_neigung"  # 0.1-0.5 mm, ggf. Neigung im G-Code kompensieren
    STARKE_NEIGUNG = "starke_neigung"  # 0.5-2 mm, neu aufspannen empfohlen
    UNEBENE_OBERFLAECHE = "unebene_oberflaeche"  # > 2 mm, Werkstueck planen vor dem Job


class ZMessPunkt(BaseModel):
    """Ein Z-Probing-Messpunkt."""
    model_config = ConfigDict(extra="forbid")

    x: float
    y: float
    z: float


class ZGridDaten(BaseModel):
    """Eingabe-Daten fuer die Diagnose."""
    model_config = ConfigDict(extra="forbid")

    messpunkte: list[ZMessPunkt] = Field(min_length=3)
    werkzeug_typ: str = "schaftfraeser"  # fuer Schwellwert-Anpassung (Schlichten strikter)
    bezugs_z: float | None = None  # Wenn None, wird Median verwendet


class ZGridErgebnis(BaseModel):
    """Diagnose-Ergebnis — UI-freundlich aufbereitet."""
    model_config = ConfigDict(extra="forbid")

    befund: EbenheitsBefund
    klartext: str  # genau ein Satz, "Werkstueck ist eben (max 0.08 mm Abweichung)"
    empfehlung: str  # naechster Schritt, "Job kann starten"

    # Numerische Details (fuer Tooltips / Tabellen)
    anzahl_punkte: int
    z_min: float
    z_max: float
    z_spreizung: float  # z_max - z_min
    z_std: float
    neigung_grad: float  # Winkel zur XY-Ebene aus best-fit
    neigung_richtung_grad: float  # Azimut der Neigungs-Richtung (0=+X, 90=+Y)
    max_lokale_abweichung_mm: float  # max |z_punkt - z_plane(x,y)|

    # Detaillierte Punkt-Liste mit Abweichung pro Punkt (fuer Heatmap)
    abweichungen: list[float]


def _fit_plane(punkte: list[ZMessPunkt]) -> tuple[float, float, float]:
    """Least-squares-Fit der Ebene z = a*x + b*y + c.

    Loest das Normalengleichungs-System per Hand (3x3) — kein numpy noetig.
    """
    n = len(punkte)
    sx = sum(p.x for p in punkte)
    sy = sum(p.y for p in punkte)
    sz = sum(p.z for p in punkte)
    sxx = sum(p.x * p.x for p in punkte)
    syy = sum(p.y * p.y for p in punkte)
    sxy = sum(p.x * p.y for p in punkte)
    sxz = sum(p.x * p.z for p in punkte)
    syz = sum(p.y * p.z for p in punkte)

    # Normalengleichung:
    # [sxx sxy sx] [a]   [sxz]
    # [sxy syy sy] [b] = [syz]
    # [sx  sy  n ] [c]   [sz ]
    m = [[sxx, sxy, sx, sxz],
         [sxy, syy, sy, syz],
         [sx, sy, n, sz]]

    # Gauss-Jordan
    for i in range(3):
        # Pivot suchen
        max_row = i
        for k in range(i + 1, 3):
            if abs(m[k][i]) > abs(m[max_row][i]):
                max_row = k
        m[i], m[max_row] = m[max_row], m[i]
        if abs(m[i][i]) < 1e-12:
            # degenerierter Fall (alle Punkte auf einer Linie) — Fallback: nur c (= Mittel)
            return 0.0, 0.0, sz / n
        # Normieren
        pivot = m[i][i]
        m[i] = [v / pivot for v in m[i]]
        # Andere Zeilen nullen
        for k in range(3):
            if k != i and abs(m[k][i]) > 1e-12:
                factor = m[k][i]
                m[k] = [m[k][j] - factor * m[i][j] for j in range(4)]
    return m[0][3], m[1][3], m[2][3]


def analyse(daten: ZGridDaten) -> ZGridErgebnis:
    """Hauptanalyse — gibt UI-freundliches Ergebnis zurueck."""
    punkte = daten.messpunkte
    n = len(punkte)
    zs = [p.z for p in punkte]
    z_min = min(zs)
    z_max = max(zs)
    z_mean = sum(zs) / n
    z_spreizung = z_max - z_min
    z_var = sum((z - z_mean) ** 2 for z in zs) / n
    z_std = math.sqrt(z_var)

    # Best-fit-Plane
    a, b, c = _fit_plane(punkte)
    # Neigung in Grad: tan(theta) = |gradient|
    grad_betrag = math.sqrt(a * a + b * b)
    neigung_grad = math.degrees(math.atan(grad_betrag))
    # Azimut der Neigung (Richtung wo's "bergab" geht, normiert auf 0-360)
    if grad_betrag < 1e-9:
        neigung_richtung_grad = 0.0
    else:
        neigung_richtung_grad = (math.degrees(math.atan2(b, a)) + 360.0) % 360.0

    # Abweichungen pro Punkt zur best-fit-Plane
    abweichungen = [p.z - (a * p.x + b * p.y + c) for p in punkte]
    max_lokal = max(abs(d) for d in abweichungen)

    # Befund + Klartext + Empfehlung
    schlicht_modus = daten.werkzeug_typ in ("kugelfraeser", "torusfraeser", "v_bit", "gravierstichel")
    schwelle_eben = 0.08 if schlicht_modus else 0.15
    schwelle_leicht = 0.3 if schlicht_modus else 0.5
    schwelle_stark = 1.5 if schlicht_modus else 2.5

    if z_spreizung < schwelle_eben:
        befund = EbenheitsBefund.EBEN_OK
        klartext = (
            f"Werkstueck ist eben (max {z_spreizung:.2f} mm Spreizung, "
            f"Std {z_std:.3f} mm)."
        )
        empfehlung = "Job kann starten — keine Anpassung noetig."
    elif z_spreizung < schwelle_leicht:
        befund = EbenheitsBefund.LEICHTE_NEIGUNG
        klartext = (
            f"Werkstueck hat leichte Neigung ({neigung_grad:.2f}°, "
            f"Spreizung {z_spreizung:.2f} mm)."
        )
        empfehlung = (
            "Fuer Schruppen OK. Fuer Schlichten "
            "G-Code-Neigung-Kompensation (Auto-Level) aktivieren oder neu aufspannen."
        )
    elif z_spreizung < schwelle_stark:
        befund = EbenheitsBefund.STARKE_NEIGUNG
        klartext = (
            f"Werkstueck schief — {neigung_grad:.2f}° Neigung, "
            f"{z_spreizung:.2f} mm Spreizung."
        )
        empfehlung = (
            "Neu aufspannen empfohlen. Bei Schlichten zwingend, sonst "
            "ungleichmaessige Tiefe."
        )
    else:
        befund = EbenheitsBefund.UNEBENE_OBERFLAECHE
        klartext = (
            f"Oberflaeche unebener als erwartet ({z_spreizung:.2f} mm Spreizung, "
            f"max lokale Abweichung {max_lokal:.2f} mm)."
        )
        empfehlung = (
            "Werkstueck planen (Plan-Operation mit Schaftfraeser) "
            "bevor der eigentliche Job startet."
        )

    return ZGridErgebnis(
        befund=befund,
        klartext=klartext,
        empfehlung=empfehlung,
        anzahl_punkte=n,
        z_min=z_min,
        z_max=z_max,
        z_spreizung=z_spreizung,
        z_std=z_std,
        neigung_grad=neigung_grad,
        neigung_richtung_grad=neigung_richtung_grad,
        max_lokale_abweichung_mm=max_lokal,
        abweichungen=abweichungen,
    )


__all__ = [
    "EbenheitsBefund",
    "ZGridDaten",
    "ZGridErgebnis",
    "ZMessPunkt",
    "analyse",
]

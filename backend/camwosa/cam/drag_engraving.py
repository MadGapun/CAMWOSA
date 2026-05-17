"""Drag-Engraving als eigenstaendige Operation (A45-Rest, Cluster E).

Schleppgravierer / Diamantgravierer Workflow:
- Werkzeug haengt frei drehbar in einem federbelasteten Halter
- Spindel ist AUS (oder PWM=0), Werkzeug folgt der Bewegungsrichtung passiv
- Tiefe ist konstant (typisch 0.05 - 0.3 mm)
- Plunge MUSS langsam sein — schneller Plunge zerstoert die Diamantspitze
- An scharfen Ecken: kurz anhalten damit Werkzeug sich neu ausrichten kann
- Lead-In/Lead-Out tangential zur ersten/letzten Linie

Unterschied zur normalen Gravur:
- Spindel-RPM 0 (G-Code: M5 vor jeder Operation)
- Sehr langsamer Plunge (1/10 vom normalen)
- Optionale Dwell an Ecken-Knicken (Standard: Knick > 30°)
- KEINE Z-stufige Zustellung — Diamant geht in einem Pass

Pflicht-Werkzeug-Typ: DRAG_GRAVIERER (siehe db/models.py).

Issue: #39 (Cluster E)
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, Field
from shapely.geometry import LineString, Polygon

from camwosa.cam.geometry import objekt_zu_shapely
from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.dxf.parser import GeometrieObjekt
from camwosa.gcode.toolpath import (
    Bewegung,
    BewegungsTyp,
    OperationsTyp,
    Toolpath,
)


class DragEngravingParameter(BaseModel):
    """Drag-Engraving-spezifische Parameter."""

    model_config = ConfigDict(extra="ignore")

    werkzeug_id: str
    vorschub: float = Field(default=800.0, gt=0, le=2000, description="mm/min, typisch 500-1000")
    eintauch_vorschub: float = Field(
        default=80.0, gt=0, description="mm/min, sehr langsam — typisch 1/10 vom Vorschub",
    )
    sicherheitshoehe: float = Field(default=3.0, gt=0)
    tiefe: float = Field(
        default=0.15, gt=0, le=2.0,
        description="Eindruck-Tiefe in mm — typisch 0.1-0.3",
    )
    dwell_an_ecken_sekunden: float = Field(
        default=0.15, ge=0, le=2.0,
        description="Pause an scharfen Ecken damit Werkzeug sich neu ausrichtet",
    )
    ecken_winkel_schwelle_grad: float = Field(
        default=30.0, gt=0, le=180,
        description="Knick-Winkel ab dem an einer Ecke gepaust wird",
    )
    lead_in_tangential_mm: float = Field(
        default=0.0, ge=0, le=20,
        description="Tangential einfahren (mm) — vermeidet Tropfen am Start",
    )


class DragEngravingFehler(Exception):
    """Drag-Engraving-Vorbedingung verletzt (falsches Werkzeug, etc.)."""


def erzeuge_drag_engraving_toolpath(
    geometrie: GeometrieObjekt | LineString | Polygon | list,
    werkzeug: Werkzeug,
    parameter: DragEngravingParameter,
    *,
    operation_id: str = "drag_engraving",
) -> Toolpath:
    """Generiert Toolpath fuer Drag-Engraving.

    Args:
        geometrie: einzelnes GeometrieObjekt, shapely-Objekt oder Liste davon.
        werkzeug: muss vom Typ DRAG_GRAVIERER oder DIAMANTGRAVIERER sein.
        parameter: Drag-Engraving-Parameter.

    Raises:
        DragEngravingFehler: falsches Werkzeug.
    """
    if werkzeug.typ not in (WerkzeugTyp.DRAG_GRAVIERER, WerkzeugTyp.DIAMANTGRAVIERER):
        raise DragEngravingFehler(
            f"Werkzeug muss DRAG_GRAVIERER oder DIAMANTGRAVIERER sein, "
            f"ist aber {werkzeug.typ.value}. Andere Werkzeug-Typen wuerden bei "
            f"Spindel-AUS am Material kratzen statt zu schreiben."
        )

    # Geometrie -> Liste von Pfaden
    if isinstance(geometrie, list):
        pfade: list[list[tuple[float, float]]] = []
        for g in geometrie:
            pfade.extend(_extrahiere_pfade(g))
    else:
        pfade = _extrahiere_pfade(geometrie)

    if not pfade:
        raise DragEngravingFehler("Keine zeichenbaren Pfade in der Geometrie.")

    bewegungen: list[Bewegung] = []
    z_safe = parameter.sicherheitshoehe
    z_tiefe = -abs(parameter.tiefe)  # immer negativ (Z nach unten)

    for pfad in pfade:
        # 1. Eilgang zum Startpunkt in Sicherheitshoehe
        x0, y0 = pfad[0]
        bewegungen.append(Bewegung(
            typ=BewegungsTyp.EILGANG, x=x0, y=y0, z=z_safe,
            kommentar="Anfahren Start",
        ))

        # 2. Tangentialer Lead-In (optional)
        if parameter.lead_in_tangential_mm > 0 and len(pfad) >= 2:
            # Richtung der ersten Linie
            dx = pfad[1][0] - pfad[0][0]
            dy = pfad[1][1] - pfad[0][1]
            laenge = math.hypot(dx, dy)
            if laenge > 1e-9:
                ux, uy = dx / laenge, dy / laenge
                # Pre-Position rueckwaerts entlang der ersten Linie
                xpre = x0 - ux * parameter.lead_in_tangential_mm
                ypre = y0 - uy * parameter.lead_in_tangential_mm
                bewegungen.append(Bewegung(
                    typ=BewegungsTyp.EILGANG, x=xpre, y=ypre, z=z_safe,
                ))
                # Plunge auf Tiefe (sehr langsam!)
                bewegungen.append(Bewegung(
                    typ=BewegungsTyp.PLUNGE, x=xpre, y=ypre, z=z_tiefe,
                    feed=parameter.eintauch_vorschub,
                    kommentar="Plunge (langsam — Diamant schonen)",
                ))
                # Tangentiale Anfahrt zur tatsaechlichen Startposition
                bewegungen.append(Bewegung(
                    typ=BewegungsTyp.LINEAR, x=x0, y=y0, z=z_tiefe,
                    feed=parameter.vorschub,
                ))
            else:
                bewegungen.append(Bewegung(
                    typ=BewegungsTyp.PLUNGE, x=x0, y=y0, z=z_tiefe,
                    feed=parameter.eintauch_vorschub,
                    kommentar="Plunge",
                ))
        else:
            bewegungen.append(Bewegung(
                typ=BewegungsTyp.PLUNGE, x=x0, y=y0, z=z_tiefe,
                feed=parameter.eintauch_vorschub,
                kommentar="Plunge",
            ))

        # 3. Pfad abfahren, dabei an scharfen Ecken pausen
        for i in range(1, len(pfad)):
            x, y = pfad[i]
            bewegungen.append(Bewegung(
                typ=BewegungsTyp.LINEAR, x=x, y=y, z=z_tiefe,
                feed=parameter.vorschub,
            ))
            # Ecken-Check: ist der Knick zum naechsten Punkt scharf?
            if (i < len(pfad) - 1
                    and parameter.dwell_an_ecken_sekunden > 0
                    and _ist_scharfe_ecke(
                        pfad[i - 1], pfad[i], pfad[i + 1],
                        parameter.ecken_winkel_schwelle_grad,
                    )):
                # Dwell als kurzer "Stop" im Pfad — Postprozessor erzeugt G4
                bewegungen.append(Bewegung(
                    typ=BewegungsTyp.LINEAR, x=x, y=y, z=z_tiefe,
                    feed=parameter.vorschub,
                    kommentar=f"DWELL {parameter.dwell_an_ecken_sekunden}s (Ecke neu ausrichten)",
                ))

        # 4. Zurueck auf Sicherheitshoehe
        x_end, y_end = pfad[-1]
        bewegungen.append(Bewegung(
            typ=BewegungsTyp.EILGANG, x=x_end, y=y_end, z=z_safe,
            kommentar="Rueckzug",
        ))

    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.GRAVUR,
        werkzeug_id=werkzeug.id,
        spindel_rpm=0.0,  # Spindel MUSS aus sein bei Drag-Engraving
        sicherheitshoehe=z_safe,
        bewegungen=bewegungen,
        kommentar=(
            "Drag-Engraving (Spindel AUS, langsamer Plunge, Dwell an Ecken)"
        ),
        metadaten={
            "drag_engraving": True,
            "tiefe_mm": parameter.tiefe,
            "ecken_dwell_s": parameter.dwell_an_ecken_sekunden,
        },
    )


def _extrahiere_pfade(geo) -> list[list[tuple[float, float]]]:
    """Extrahiert 2D-Pfade aus GeometrieObjekt / shapely-Objekt."""
    if isinstance(geo, GeometrieObjekt):
        if geo.typ.value == "punkt":
            # Punkt = kein zeichenbarer Pfad fuer Drag
            return []
        if geo.typ.value == "kreis":
            # Kreis → diskretisieren (32 Segmente)
            r = geo.attribute.get("radius", 0)
            if r <= 0 or not geo.punkte:
                return []
            mx, my = geo.punkte[0].to_tuple()
            n = max(32, int(2 * math.pi * r / 0.5))  # ~0.5 mm pro Segment
            pfad = [
                (mx + r * math.cos(2 * math.pi * i / n),
                 my + r * math.sin(2 * math.pi * i / n))
                for i in range(n + 1)
            ]
            return [pfad]
        # Linien / Polylinien
        if not geo.punkte:
            return []
        pfad = [p.to_tuple() for p in geo.punkte]
        if geo.geschlossen and pfad and pfad[0] != pfad[-1]:
            pfad.append(pfad[0])
        return [pfad]

    if isinstance(geo, LineString):
        return [list(geo.coords)]
    if isinstance(geo, Polygon):
        outer = list(geo.exterior.coords)
        inner = [list(ring.coords) for ring in geo.interiors]
        return [outer] + inner
    # Fallback: shapely-Conversion versuchen
    try:
        sh = objekt_zu_shapely(geo)
        return _extrahiere_pfade(sh)
    except Exception:
        return []


def _ist_scharfe_ecke(
    p_vor: tuple[float, float],
    p_ecke: tuple[float, float],
    p_nach: tuple[float, float],
    schwelle_grad: float,
) -> bool:
    """True wenn der Knickwinkel an p_ecke schaerfer ist als die Schwelle.

    Knickwinkel = Aenderung der Bewegungsrichtung. 0° = geradeaus, 180° = 180-Grad-Wende.
    Schwelle z.B. 30° = leichter Knick, 90° = scharfer Knick.
    """
    ax = p_ecke[0] - p_vor[0]
    ay = p_ecke[1] - p_vor[1]
    bx = p_nach[0] - p_ecke[0]
    by = p_nach[1] - p_ecke[1]
    la = math.hypot(ax, ay)
    lb = math.hypot(bx, by)
    if la < 1e-9 or lb < 1e-9:
        return False
    cos_winkel = (ax * bx + ay * by) / (la * lb)
    cos_winkel = max(-1.0, min(1.0, cos_winkel))
    knick_grad = math.degrees(math.acos(cos_winkel))
    return knick_grad > schwelle_grad


__all__ = [
    "DragEngravingFehler",
    "DragEngravingParameter",
    "erzeuge_drag_engraving_toolpath",
]

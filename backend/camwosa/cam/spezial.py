"""Spezial-Operationen: T-Nut, Schwalbenschwanz, Fase.

Diese Operationen brauchen spezielle Werkzeuge (T-Nut-Fraeser,
Schwalbenschwanz-Fraeser, V-Bit/Fasenfraeser) und produzieren
charakteristische Toolpaths.
"""

from __future__ import annotations

import math
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field
from shapely.geometry import LineString, Polygon

from camwosa.cam.geometry import objekt_zu_shapely, offset_polygon
from camwosa.db.models import Werkzeug
from camwosa.dxf.parser import GeometrieObjekt
from camwosa.gcode.toolpath import (
    Bewegung,
    BewegungsTyp,
    OperationsTyp,
    Toolpath,
)


# ---------------------------------------------------------------------------
# Parameter
# ---------------------------------------------------------------------------


class SpezialParameter(BaseModel):
    """Gemeinsame Felder fuer Spezial-Operationen."""

    model_config = ConfigDict(extra="ignore")

    werkzeug_id: str
    spindel_rpm: float = Field(gt=0)
    vorschub: float = Field(gt=0)
    eintauch_vorschub: float = Field(gt=0)
    sicherheitshoehe: float = Field(default=5.0)
    tiefe: float = Field(gt=0, description="Tiefe in mm (positiv)")
    stepdown: float = Field(default=1.0, gt=0)


class TNutParameter(SpezialParameter):
    """T-Nut: Hinterschnitt-Nut, wird mit T-Nutenfraeser unten erweitert."""
    nut_breite: float = Field(gt=0, description="Breite des oberen Schlitzes")


class SchwalbenschwanzParameter(SpezialParameter):
    """Schwalbenschwanz: Hinterschnitt-Profil mit Schwalbenschwanz-Fraeser.

    Toolpath ist wie Kontur, aber Werkzeug-Form ist konisch — der Hinterschnitt
    entsteht durch die Werkzeug-Geometrie.
    """
    schwalbenschwanz_winkel_grad: float = Field(default=60.0, gt=10, le=90)


class FaseParameter(SpezialParameter):
    """Fase: Schraege entlang einer Kontur, mit V-Bit oder Fasenfraeser."""
    fase_breite: float = Field(gt=0, description="Breite der Fase in mm")
    spitzenwinkel_grad: float = Field(default=90.0, gt=10, le=180)


# ---------------------------------------------------------------------------
# T-Nut
# ---------------------------------------------------------------------------


def erzeuge_t_nut_toolpath(
    geometrie: GeometrieObjekt | LineString,
    werkzeug: Werkzeug,
    parameter: TNutParameter,
    *,
    operation_id: str = "t_nut",
) -> Toolpath:
    """T-Nut entlang einer offenen Linie.

    Vorgehen:
    1. Vor-Schlitz mit normalem Schaftfraeser (ist nicht Teil dieser Operation,
       muss vorher als Tasche/Kontur laufen).
    2. T-Nut-Fraeser taucht in den Vor-Schlitz ein und fraest in der Tiefe
       links + rechts den Hinterschnitt.
    """
    pfad = _als_pfad(geometrie)
    if not pfad or len(pfad) < 2:
        raise ValueError("T-Nut braucht eine Linie (LineString oder Polylinie)")

    z_tiefe = -abs(parameter.tiefe)
    bewegungen: list[Bewegung] = []

    # Anfahrt
    bewegungen.append(Bewegung(
        BewegungsTyp.EILGANG, pfad[0][0], pfad[0][1], parameter.sicherheitshoehe,
        kommentar=f"--- T-Nut tiefe={parameter.tiefe} ---",
    ))
    bewegungen.append(Bewegung(
        BewegungsTyp.PLUNGE, pfad[0][0], pfad[0][1], z_tiefe,
        feed=parameter.eintauch_vorschub,
        kommentar="T-Nut: Plunge in Vor-Schlitz",
    ))
    # Linie entlang fahren
    for x, y in pfad[1:]:
        bewegungen.append(Bewegung(
            BewegungsTyp.LINEAR, x, y, z_tiefe, feed=parameter.vorschub,
        ))
    # Rueckzug
    bewegungen.append(Bewegung(
        BewegungsTyp.EILGANG, pfad[-1][0], pfad[-1][1], parameter.sicherheitshoehe,
    ))

    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.KONTUR,
        werkzeug_id=werkzeug.id,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe,
        bewegungen=bewegungen,
        kommentar=f"T-Nut (Tiefe {parameter.tiefe}mm, Nutbreite {parameter.nut_breite}mm)",
        metadaten={
            "operation": "t_nut",
            "nut_breite": parameter.nut_breite,
            "warnung": "Vor-Schlitz muss zuerst mit normalem Fraeser gemacht sein!",
        },
    )


# ---------------------------------------------------------------------------
# Schwalbenschwanz
# ---------------------------------------------------------------------------


def erzeuge_schwalbenschwanz_toolpath(
    geometrie: GeometrieObjekt | Polygon,
    werkzeug: Werkzeug,
    parameter: SchwalbenschwanzParameter,
    *,
    operation_id: str = "schwalbenschwanz",
) -> Toolpath:
    """Schwalbenschwanz-Profil entlang einer geschlossenen Kontur."""
    if isinstance(geometrie, GeometrieObjekt):
        geo = objekt_zu_shapely(geometrie)
    else:
        geo = geometrie
    if not isinstance(geo, Polygon):
        raise ValueError("Schwalbenschwanz braucht eine geschlossene Kontur (Polygon)")

    # Wir folgen der Aussenkontur in der Tiefe
    aussen = list(geo.exterior.coords)
    z_tiefe = -abs(parameter.tiefe)
    bewegungen: list[Bewegung] = []

    bewegungen.append(Bewegung(
        BewegungsTyp.EILGANG, aussen[0][0], aussen[0][1], parameter.sicherheitshoehe,
        kommentar=f"--- Schwalbenschwanz (Winkel {parameter.schwalbenschwanz_winkel_grad}°) ---",
    ))
    bewegungen.append(Bewegung(
        BewegungsTyp.PLUNGE, aussen[0][0], aussen[0][1], z_tiefe,
        feed=parameter.eintauch_vorschub,
    ))
    for x, y in aussen[1:]:
        bewegungen.append(Bewegung(
            BewegungsTyp.LINEAR, x, y, z_tiefe, feed=parameter.vorschub,
        ))
    bewegungen.append(Bewegung(
        BewegungsTyp.EILGANG, aussen[-1][0], aussen[-1][1], parameter.sicherheitshoehe,
    ))

    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.KONTUR,
        werkzeug_id=werkzeug.id,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe,
        bewegungen=bewegungen,
        kommentar=f"Schwalbenschwanz (Winkel {parameter.schwalbenschwanz_winkel_grad}°)",
        metadaten={
            "operation": "schwalbenschwanz",
            "winkel_grad": parameter.schwalbenschwanz_winkel_grad,
        },
    )


# ---------------------------------------------------------------------------
# Fase
# ---------------------------------------------------------------------------


def erzeuge_fase_toolpath(
    geometrie: GeometrieObjekt | LineString | Polygon,
    werkzeug: Werkzeug,
    parameter: FaseParameter,
    *,
    operation_id: str = "fase",
) -> Toolpath:
    """Fase entlang einer Kontur (offen oder geschlossen).

    Z-Tiefe wird aus Fase-Breite und Spitzenwinkel berechnet:
        z = fase_breite / tan(spitzenwinkel/2)
    """
    halb = math.radians(parameter.spitzenwinkel_grad / 2)
    z_tiefe = -parameter.fase_breite / math.tan(halb) if halb > 0 else -parameter.tiefe
    if abs(z_tiefe) > parameter.tiefe:
        z_tiefe = -parameter.tiefe  # gedeckelt

    pfade = _als_pfade(geometrie)
    if not pfade:
        raise ValueError("Fase: keine Pfade gefunden")

    bewegungen: list[Bewegung] = []
    for pfad in pfade:
        if len(pfad) < 2:
            continue
        bewegungen.append(Bewegung(
            BewegungsTyp.EILGANG, pfad[0][0], pfad[0][1], parameter.sicherheitshoehe,
            kommentar=f"--- Fase (Breite {parameter.fase_breite}, Winkel "
                      f"{parameter.spitzenwinkel_grad}°) ---",
        ))
        bewegungen.append(Bewegung(
            BewegungsTyp.PLUNGE, pfad[0][0], pfad[0][1], z_tiefe,
            feed=parameter.eintauch_vorschub,
        ))
        for x, y in pfad[1:]:
            bewegungen.append(Bewegung(
                BewegungsTyp.LINEAR, x, y, z_tiefe, feed=parameter.vorschub,
            ))
        bewegungen.append(Bewegung(
            BewegungsTyp.EILGANG, pfad[-1][0], pfad[-1][1], parameter.sicherheitshoehe,
        ))

    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.KONTUR,
        werkzeug_id=werkzeug.id,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe,
        bewegungen=bewegungen,
        kommentar=f"Fase Breite={parameter.fase_breite} Winkel={parameter.spitzenwinkel_grad}",
        metadaten={
            "operation": "fase",
            "z_berechnet": z_tiefe,
            "fase_breite": parameter.fase_breite,
            "spitzenwinkel_grad": parameter.spitzenwinkel_grad,
        },
    )


# ---------------------------------------------------------------------------
# Helfer
# ---------------------------------------------------------------------------


def _als_pfad(g) -> list[tuple[float, float]]:
    if isinstance(g, GeometrieObjekt):
        sh = objekt_zu_shapely(g)
    else:
        sh = g
    if isinstance(sh, LineString):
        return list(sh.coords)
    if isinstance(sh, Polygon):
        return list(sh.exterior.coords)
    return []


def _als_pfade(g) -> list[list[tuple[float, float]]]:
    if isinstance(g, GeometrieObjekt):
        sh = objekt_zu_shapely(g)
    else:
        sh = g
    if isinstance(sh, LineString):
        return [list(sh.coords)]
    if isinstance(sh, Polygon):
        pfade = [list(sh.exterior.coords)]
        for innen in sh.interiors:
            pfade.append(list(innen.coords))
        return pfade
    return []


__all__ = [
    "FaseParameter",
    "SchwalbenschwanzParameter",
    "SpezialParameter",
    "TNutParameter",
    "erzeuge_fase_toolpath",
    "erzeuge_schwalbenschwanz_toolpath",
    "erzeuge_t_nut_toolpath",
]

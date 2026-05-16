"""PCB-Isolationsfraesen.

Spezial-Anwendung der Gravur: Werkzeug (Gravurstichel oder V-Bit) fraest
Isolationsspuren zwischen Leiterbahnen einer Platine.

Vorgehen:
1. Input: geschlossene Polygone (Leiterbahnen / Pads) — typisch aus
   Gerber-zu-DXF-Konvertierung.
2. Pro Leiterbahn wird ein Offset-Pfad mit halbem Isolations-Abstand erzeugt.
3. Werkzeug folgt mit konstanter Tiefe.

Optional: Mehrfach-Offsets fuer breitere Isolation (mehrere Spuren).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from shapely.geometry import MultiPolygon, Polygon

from camwosa.cam.geometry import objekt_zu_shapely, offset_polygon
from camwosa.db.models import Werkzeug
from camwosa.dxf.parser import GeometrieObjekt
from camwosa.gcode.toolpath import (
    Bewegung,
    BewegungsTyp,
    OperationsTyp,
    Toolpath,
)


class PCBParameter(BaseModel):
    """PCB-Isolationsfraesen-Parameter."""

    model_config = ConfigDict(extra="ignore")

    werkzeug_id: str
    spindel_rpm: float = Field(gt=0)
    vorschub: float = Field(gt=0)
    eintauch_vorschub: float = Field(gt=0)
    sicherheitshoehe: float = Field(default=2.0)
    isolations_tiefe: float = Field(default=0.15, gt=0, description="mm")
    isolations_abstand: float = Field(default=0.3, gt=0,
                                       description="Abstand zur Leiterbahn-Kante")
    anzahl_spuren: int = Field(default=1, ge=1, le=10,
                                description="Mehrere konzentrische Spuren")


def erzeuge_pcb_isolation_toolpath(
    leiterbahnen: list[GeometrieObjekt | Polygon],
    werkzeug: Werkzeug,
    parameter: PCBParameter,
    *,
    operation_id: str = "pcb_isolation",
) -> Toolpath:
    """Erzeugt Isolations-Toolpaths zwischen Leiterbahnen."""
    bewegungen: list[Bewegung] = []
    z = -parameter.isolations_tiefe

    for idx, lb in enumerate(leiterbahnen):
        if isinstance(lb, GeometrieObjekt):
            geo = objekt_zu_shapely(lb)
        else:
            geo = lb
        if not isinstance(geo, Polygon):
            continue

        # Pro Spur ein zusaetzlicher Offset
        for spur in range(parameter.anzahl_spuren):
            distanz = parameter.isolations_abstand + spur * werkzeug.durchmesser
            offset = offset_polygon(geo, distanz)
            if offset is None or offset.is_empty:
                continue
            polys = [offset] if isinstance(offset, Polygon) else (
                list(offset.geoms) if isinstance(offset, MultiPolygon) else []
            )
            for poly in polys:
                if not isinstance(poly, Polygon):
                    continue
                kontur = list(poly.exterior.coords)
                if not kontur:
                    continue
                bewegungen.append(Bewegung(
                    BewegungsTyp.EILGANG, kontur[0][0], kontur[0][1],
                    parameter.sicherheitshoehe,
                    kommentar=(
                        f"--- PCB Iso LB={idx} Spur={spur + 1}/{parameter.anzahl_spuren} ---"
                    ),
                ))
                bewegungen.append(Bewegung(
                    BewegungsTyp.PLUNGE, kontur[0][0], kontur[0][1], z,
                    feed=parameter.eintauch_vorschub,
                ))
                for x, y in kontur[1:]:
                    bewegungen.append(Bewegung(
                        BewegungsTyp.LINEAR, x, y, z, feed=parameter.vorschub,
                    ))
                bewegungen.append(Bewegung(
                    BewegungsTyp.EILGANG, kontur[-1][0], kontur[-1][1],
                    parameter.sicherheitshoehe,
                ))

    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.GRAVUR,
        werkzeug_id=werkzeug.id,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe,
        bewegungen=bewegungen,
        kommentar=(
            f"PCB-Isolation Tiefe={parameter.isolations_tiefe}mm "
            f"Abstand={parameter.isolations_abstand}mm Spuren={parameter.anzahl_spuren}"
        ),
        metadaten={"operation": "pcb_isolation"},
    )


__all__ = ["PCBParameter", "erzeuge_pcb_isolation_toolpath"]

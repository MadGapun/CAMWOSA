"""CAM-Operation: 2.5D-Relief.

Erzeugt einen Toolpath aus einer Heightmap.

Strategien:
- RASTER_X: Bahnen parallel zur X-Achse
- RASTER_Y: Bahnen parallel zur Y-Achse
- KONTUR_PARALLEL: nicht implementiert (Phase 2+)

Siehe Wiki: docs/wiki/Operation-Relief.md
"""

from __future__ import annotations

from enum import Enum

from camwosa.cam.parameter import OperationParameter
from camwosa.db.models import Werkzeug
from camwosa.gcode.toolpath import (
    Bewegung,
    BewegungsTyp,
    OperationsTyp,
    Toolpath,
)
from camwosa.stl.heightmap import Heightmap


class ReliefStrategie(str, Enum):
    RASTER_X = "raster_x"
    RASTER_Y = "raster_y"
    KONTUR_PARALLEL = "kontur_parallel"  # nicht implementiert


def erzeuge_relief_toolpath(
    heightmap: Heightmap,
    werkzeug: Werkzeug,
    parameter: OperationParameter,
    *,
    strategie: ReliefStrategie = ReliefStrategie.RASTER_X,
    operation_id: str = "relief",
) -> Toolpath:
    if strategie == ReliefStrategie.KONTUR_PARALLEL:
        raise NotImplementedError(
            "KONTUR_PARALLEL fuer Relief ist Phase 2 — kommt nach Standard-Raster."
        )

    nx, ny = heightmap.shape
    aufl = heightmap.aufloesung
    bewegungen: list[Bewegung] = []

    # Sicherheitshoehe Anfahrt
    bewegungen.append(Bewegung(
        BewegungsTyp.EILGANG,
        heightmap.x_min, heightmap.y_min, parameter.sicherheitshoehe,
        kommentar="Anfahrt Relief",
    ))

    if strategie == ReliefStrategie.RASTER_X:
        for j in range(ny):
            y = heightmap.y_min + j * aufl
            indizes = range(nx) if j % 2 == 0 else range(nx - 1, -1, -1)
            for k, i in enumerate(indizes):
                x = heightmap.x_min + i * aufl
                z = float(heightmap.z_values[i, j])
                # Erste Bewegung in der Reihe = Plunge auf Z
                if k == 0:
                    bewegungen.append(Bewegung(
                        BewegungsTyp.EILGANG, x, y, parameter.sicherheitshoehe,
                    ))
                    bewegungen.append(Bewegung(
                        BewegungsTyp.PLUNGE, x, y, z, feed=parameter.eintauch_vorschub,
                    ))
                else:
                    bewegungen.append(Bewegung(
                        BewegungsTyp.LINEAR, x, y, z, feed=parameter.vorschub,
                    ))
            # Am Ende jeder Reihe Rueckzug
            bewegungen.append(Bewegung(
                BewegungsTyp.EILGANG, x, y, parameter.sicherheitshoehe,
            ))
    else:  # RASTER_Y
        for i in range(nx):
            x = heightmap.x_min + i * aufl
            indizes = range(ny) if i % 2 == 0 else range(ny - 1, -1, -1)
            for k, j in enumerate(indizes):
                y = heightmap.y_min + j * aufl
                z = float(heightmap.z_values[i, j])
                if k == 0:
                    bewegungen.append(Bewegung(
                        BewegungsTyp.EILGANG, x, y, parameter.sicherheitshoehe,
                    ))
                    bewegungen.append(Bewegung(
                        BewegungsTyp.PLUNGE, x, y, z, feed=parameter.eintauch_vorschub,
                    ))
                else:
                    bewegungen.append(Bewegung(
                        BewegungsTyp.LINEAR, x, y, z, feed=parameter.vorschub,
                    ))
            bewegungen.append(Bewegung(
                BewegungsTyp.EILGANG, x, y, parameter.sicherheitshoehe,
            ))

    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.RELIEF,
        werkzeug_id=werkzeug.id,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe,
        bewegungen=bewegungen,
        kommentar=f"Relief ({strategie.value}, Aufloesung {aufl}mm)",
        metadaten={
            "strategie": strategie.value,
            "aufloesung_mm": aufl,
            "raster": [nx, ny],
        },
    )


__all__ = ["ReliefStrategie", "erzeuge_relief_toolpath"]

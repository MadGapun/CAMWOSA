"""DXF-Importer als Adapter auf camwosa.dxf."""

from __future__ import annotations

from pathlib import Path

from camwosa.cad.base import CADImporter, CADImportErgebnis, CADImportFehler, registry
from camwosa.dxf import DXFFehler, lade_dxf


class DXFImporter(CADImporter):
    format_id = "dxf"
    name = "DXF"
    extensions = (".dxf",)
    beschreibung = "AutoCAD DXF (R12-R2018)"

    def kann_lesen(self, pfad: Path) -> bool:
        return pfad.suffix.lower() == ".dxf"

    def lade(self, pfad: Path) -> CADImportErgebnis:
        try:
            dok = lade_dxf(pfad)
        except DXFFehler as e:
            raise CADImportFehler(str(e)) from e
        return CADImportErgebnis(
            format_id=self.format_id,
            einheit=dok.einheit,
            objekte=dok.objekte,
            layer=dok.layer,
            bounding_box=dok.bounding_box,
            metadaten={},
        )


registry().register("dxf", DXFImporter)

"""STEP-Importer-Stub.

STEP (.step / .stp) ist das industrielle Neutralformat fuer 3D-CAD-Austausch.
Konvertierung in CAMWOSA-Geometrie erfordert eine OCC-basierte Bibliothek
(z.B. ``pythonocc-core`` oder ``cadquery``), die als optionale Dependency
installiert werden muss.

Aktueller Status: Stub. Wenn ``cadquery`` (oder ``OCP``) installiert ist,
wird der Import durchgefuehrt; sonst eine sprechende Fehlermeldung.

Empfohlene Installation:
    pip install cadquery
"""

from __future__ import annotations

from pathlib import Path

from camwosa.cad.base import CADImporter, CADImportErgebnis, CADImportFehler, registry


class STEPImporter(CADImporter):
    format_id = "step"
    name = "STEP / IGES"
    extensions = (".step", ".stp", ".iges", ".igs")
    beschreibung = (
        "Industrielles Neutralformat fuer 3D-CAD-Austausch. "
        "Erfordert optional: pip install cadquery (oder pythonocc-core)."
    )

    def kann_lesen(self, pfad: Path) -> bool:
        return pfad.suffix.lower() in self.extensions

    def lade(self, pfad: Path) -> CADImportErgebnis:
        try:
            import cadquery as cq  # type: ignore
        except ImportError as e:
            raise CADImportFehler(
                "STEP/IGES-Import braucht 'cadquery'. "
                "Installation: pip install cadquery"
            ) from e

        try:
            wp = cq.importers.importStep(str(pfad))
        except Exception as e:  # noqa: BLE001
            raise CADImportFehler(f"STEP nicht lesbar: {e}") from e

        # Bounding-Box
        try:
            bb = wp.val().BoundingBox()
            from camwosa.dxf.parser import Punkt2D
            bbox = (Punkt2D(bb.xmin, bb.ymin), Punkt2D(bb.xmax, bb.ymax))
        except Exception:  # noqa: BLE001
            bbox = None

        # 2D-Konvertierung: Schnitt mit XY-Ebene fuer Konturen-Extraktion
        # ist Phase 2+. Aktuell liefern wir die Datei nur als "vorhanden" zurueck,
        # die naehere Verarbeitung passiert dann ueber Relief/Tasche-Operations.
        return CADImportErgebnis(
            format_id=self.format_id,
            einheit="mm",
            objekte=[],
            layer=[],
            bounding_box=bbox,
            metadaten={"step_pfad": str(pfad), "hinweis": "2D-Extraktion noch nicht implementiert"},
        )


registry().register("step", STEPImporter)

"""CAD-Importer-Subsystem fuer CAMWOSA.

Beim Import werden alle mitgelieferten CAD-Importer automatisch registriert.
"""

from camwosa.cad.base import (
    CADImporter,
    CADImportErgebnis,
    CADImportFehler,
    CADImporterRegistry,
    lade_cad,
    registry,
)

# Side-Effect-Imports fuer Auto-Registrierung
from camwosa.cad import dxf_importer  # noqa: F401
from camwosa.cad import svg_importer  # noqa: F401
from camwosa.cad import stl_importer  # noqa: F401
from camwosa.cad import step_importer  # noqa: F401

__all__ = [
    "CADImporter",
    "CADImportErgebnis",
    "CADImportFehler",
    "CADImporterRegistry",
    "lade_cad",
    "registry",
]

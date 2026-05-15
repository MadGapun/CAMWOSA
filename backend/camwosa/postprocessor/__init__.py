"""Postprozessor-Subsystem fuer CAMWOSA.

Beim Import werden die mitgelieferten Postprozessoren automatisch registriert.
User-Postprozessoren werden via Registry-API geladen (siehe Wiki).
"""

from camwosa.postprocessor.base import (
    PostKontext,
    PostProcessor,
    PostProcessorRegistry,
    registry,
)

# Side-Effect-Imports fuer Auto-Registrierung
from camwosa.postprocessor import grbl_standard  # noqa: F401
from camwosa.postprocessor import grbl_genmitsu  # noqa: F401
from camwosa.postprocessor import grbl_genmitsu_rotary_y  # noqa: F401

__all__ = [
    "PostKontext",
    "PostProcessor",
    "PostProcessorRegistry",
    "registry",
]

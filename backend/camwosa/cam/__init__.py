"""CAM-Subsystem fuer CAMWOSA.

Stellt Operations bereit:
- kontur.erzeuge_kontur_toolpath
- tasche.erzeuge_tasche_toolpath
- bohren.erzeuge_bohren_toolpath
- gravur.erzeuge_gravur_toolpath
"""

from camwosa.cam.bohren import erzeuge_bohren_toolpath
from camwosa.cam.gravur import erzeuge_gravur_toolpath
from camwosa.cam.kontur import erzeuge_kontur_toolpath
from camwosa.cam.tasche import erzeuge_tasche_toolpath

__all__ = [
    "erzeuge_bohren_toolpath",
    "erzeuge_gravur_toolpath",
    "erzeuge_kontur_toolpath",
    "erzeuge_tasche_toolpath",
]

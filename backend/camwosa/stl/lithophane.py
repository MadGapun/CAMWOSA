"""Lithophane: Bild als Relief fuer durchscheinende Materialien (A45 / E8).

Eine Lithophane ist ein duenner Relief-Print aus durchscheinendem Material
(z.B. weisses Acryl, ggf. mit LED-Hinterleuchtung). Helligkeit des Original-
Bildes wird in Material-Dicke uebersetzt:

- **Helle Pixel** = duennes Material = mehr Licht durch
- **Dunkle Pixel** = dickes Material = weniger Licht durch

Das ist im Prinzip eine *invertierte* Bild-zu-Heightmap-Konvertierung:
- Standard `heightmap_aus_bild`: hell = hoch (= Material steht)
- Lithophane: hell = tief (= Material weggefraest, mehr Licht durch)

Plus ein paar Lithophane-spezifische Defaults:
- min_dicke_mm (z.B. 0.8 mm): an HELLEN Stellen bleibt diese Dicke
- max_dicke_mm (z.B. 3.0 mm): an DUNKLEN Stellen bleibt diese Dicke
- (Differenz = max-min wird als Tiefe gefraest)

Wiki: docs/wiki/Lithophane.md
"""

from __future__ import annotations

from dataclasses import dataclass

from camwosa.stl.bild_heightmap import BildHeightmapParameter, heightmap_aus_bild
from camwosa.stl.heightmap import Heightmap


@dataclass
class LithophaneParameter:
    """Parameter fuer Lithophane.

    Anders als ``BildHeightmapParameter``: hier wird die Bild-Helligkeit
    invertiert in Tiefe gemappt, plus eine Mindest-Dicke (Sockel) damit
    auch an hellsten Stellen das Material nicht durchsichtig wird.

    Empfohlene Defaults:
    - min_dicke_mm: 0.8 mm (gerade noch lichtdurchlaessig)
    - max_dicke_mm: 3.0 mm (klar opak)
    - pixel_pro_mm: 5-10 (feiner ist besser fuer Foto-Aufloesung)
    """

    min_dicke_mm: float = 0.8
    max_dicke_mm: float = 3.0
    pixel_pro_mm: float = 8.0
    invertieren_quelle: bool = False
    """True wenn das Original-Bild bereits invertiert ist (Negativ)."""
    max_dimension_px: int | None = 1200


def heightmap_fuer_lithophane(
    bild_bytes: bytes,
    parameter: LithophaneParameter | None = None,
) -> Heightmap:
    """Erzeugt eine Heightmap aus einem Bild im Lithophane-Modus.

    Args:
        bild_bytes: PNG/JPG-Bytes
        parameter: Lithophane-Konfiguration

    Returns:
        Heightmap mit Z-Werten zwischen ``-max_dicke_mm`` und
        ``-min_dicke_mm``. Die Z=0-Ebene ist die **Rueckseite** (= LED-Seite).
        Fraesen wird dann von Z=0 nach unten bis ``-max_dicke_mm`` ausgefuehrt,
        und die Vorderseite (Z=-min_dicke_mm bis -max_dicke_mm) bleibt unberuehrt.

    Berechnung pro Pixel:
        helligkeit = grayscale(Pixel) / 255  # in [0, 1]
        # invertieren: hell = wenig material, dunkel = viel
        material_dicke = min_dicke + (max_dicke - min_dicke) * (1 - helligkeit)
        # Z (relativ zur Rueckseite):
        z = -material_dicke
    """
    parameter = parameter or LithophaneParameter()
    if parameter.max_dicke_mm <= parameter.min_dicke_mm:
        raise ValueError(
            f"max_dicke ({parameter.max_dicke_mm}) muss > min_dicke "
            f"({parameter.min_dicke_mm}) sein"
        )

    # Wir nutzen die existing Pipeline mit invertierter Logik
    # heightmap_aus_bild: invertieren=False -> hell=Z=0, dunkel=Z=-max_tiefe
    # Wir wollen aber:
    #   hell -> -min_dicke (weniger Material = naeher an Rueckseite)
    #   dunkel -> -max_dicke (mehr Material = weiter weg von Rueckseite)
    #
    # Wenn wir invertieren_quelle=True nehmen + invertieren=True im
    # bild_heightmap Param, dann:
    #   helle pixel haben Z=0, dunkle Z=-tiefe
    # Wir setzen max_tiefe_mm = max - min und addieren -min nachtraeglich.
    #
    # Mit invertieren=False (Default):
    #   helle pixel -> Z = 0
    #   dunkle pixel -> Z = -max_tiefe
    # Das passt direkt: dunkle Stelle = mehr Material weggehoben.
    # Aber wir brauchen Sockel min_dicke an HELLEN Stellen.

    bild_params = BildHeightmapParameter(
        max_tiefe_mm=parameter.max_dicke_mm - parameter.min_dicke_mm,
        pixel_pro_mm=parameter.pixel_pro_mm,
        invertieren=parameter.invertieren_quelle,
        max_dimension_px=parameter.max_dimension_px,
    )
    hm = heightmap_aus_bild(bild_bytes, bild_params)

    # Verschiebe alle Z-Werte um -min_dicke_mm
    # Original: helle Stellen Z=0, dunkle Z=-(max-min)
    # Wir wollen: helle Stellen Z=-min_dicke, dunkle Z=-max_dicke
    hm.z_values = hm.z_values - parameter.min_dicke_mm
    if hm.z_values.size > 0:
        hm.z_max = float(hm.z_values.max())
    return hm


__all__ = [
    "LithophaneParameter",
    "heightmap_fuer_lithophane",
]

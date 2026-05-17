"""Bild → Heightmap-Konverter (Phase A der Bild-zu-Relief-Pipeline).

Nimmt ein Grayscale-Bild (oder ein Farbbild, das nach Grayscale konvertiert wird)
und erzeugt eine ``Heightmap`` im gleichen Format wie ``heightmap.berechne_heightmap``
sie aus STL-Dateien liefert.

Damit kann ``cam.relief.erzeuge_relief_toolpath`` direkt darauf angewandt werden —
die ganze Toolpath-Generierung ist bereits vorhanden.

Konvention (Heightmap):
- Pixel-Helligkeit wird auf 0..1 normiert
- Mit ``invertieren=False`` (Default): HELL = HOCH, DUNKEL = TIEF
- Z-Werte sind 0 an der Oberflaeche und negativ ins Material (z_referenz="max")
- Aufloesung wird ueber ``pixel_pro_mm`` gesteuert

Siehe Wiki: docs/wiki/Bild-zu-Relief.md
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

from camwosa.stl.heightmap import Heightmap


@dataclass
class BildHeightmapParameter:
    """Parameter fuer die Bild-zu-Heightmap-Konvertierung.

    Werte werden auf die Heightmap angewendet — der Toolpath-Generator
    (``cam.relief``) verarbeitet dann den Rest.
    """

    max_tiefe_mm: float = 3.0
    """Wie viel mm zwischen weiss und schwarz (= Tiefen-Spanne)."""

    pixel_pro_mm: float = 5.0
    """Aufloesung: wie viele Pixel pro mm Werkstueck? 5 = 0.2mm Pixel."""

    invertieren: bool = False
    """False: hell = hoch (Standard). True: dunkel = hoch (z.B. Schwarz-Weiss-Zeichnung)."""

    glaetten_radius: int = 0
    """0 = aus. >0 = Box-Blur mit dem angegebenen Radius (in Pixel). 1-3 fuer Anti-
    Aliasing-Glaettung, 5+ fuer staerkere Glaettung gegen Bildrauschen."""

    zero_plane_schwelle: float = 0.0
    """0 = aus. >0 (in 0..1): Pixel die HELLER sind als die Schwelle werden auf
    Z=0 gesetzt (= „Sockel auf max-Hoehe stehen lassen"). Nuetzlich um das
    Motiv vom Hintergrund zu trennen."""

    max_dimension_px: int | None = None
    """Optional: Bild wird auf diese Maximal-Dimension herunter-skaliert
    (proportional). None = Original-Aufloesung. Verhindert riesige
    Toolpaths bei grossen Eingangs-Bildern."""


def heightmap_aus_bild(
    quelle: str | Path | bytes | BytesIO,
    parameter: BildHeightmapParameter | None = None,
) -> Heightmap:
    """Erzeugt eine Heightmap aus einem Bild.

    ``quelle`` kann ein Pfad zum Bild sein oder ein in-memory Bytes-Objekt
    (z.B. aus einem File-Upload).
    """
    p = parameter or BildHeightmapParameter()

    # Bild laden
    if isinstance(quelle, (str, Path)):
        pfad = Path(quelle)
        if not pfad.exists():
            raise FileNotFoundError(f"Bild nicht gefunden: {pfad}")
        img = Image.open(pfad)
    elif isinstance(quelle, bytes):
        img = Image.open(BytesIO(quelle))
    else:
        img = Image.open(quelle)

    # Nach Grayscale konvertieren (PIL Mode "L" = 8-Bit-Grau)
    img = img.convert("L")

    # Optional verkleinern
    if p.max_dimension_px and max(img.size) > p.max_dimension_px:
        w, h = img.size
        if w >= h:
            neu_w = p.max_dimension_px
            neu_h = int(round(h * p.max_dimension_px / w))
        else:
            neu_h = p.max_dimension_px
            neu_w = int(round(w * p.max_dimension_px / h))
        img = img.resize((neu_w, neu_h), Image.LANCZOS)

    # → numpy float [0, 1]. Pillow ist (zeilen=hoehe, spalten=breite),
    # wir wollen (x, y) → transponieren.
    arr = np.asarray(img, dtype=np.float32) / 255.0
    arr = arr.T  # (breite_px, hoehe_px)

    if p.invertieren:
        arr = 1.0 - arr

    # Optional glaetten via Box-Blur (eigene Implementation, scipy-frei)
    if p.glaetten_radius > 0:
        arr = _box_blur(arr, p.glaetten_radius)

    # Zero-Plane: helle Pixel auf Z=0 (Sockel-Effekt)
    if p.zero_plane_schwelle > 0:
        arr = np.where(arr >= p.zero_plane_schwelle, 1.0, arr)

    # Z-Werte berechnen:
    # arr = 1 (weiss/hoch)  → z = 0          (Oberflaeche)
    # arr = 0 (schwarz/tief) → z = -max_tiefe (tief ins Material)
    z_values = -(1.0 - arr) * p.max_tiefe_mm

    aufloesung = 1.0 / p.pixel_pro_mm
    return Heightmap(
        z_values=z_values.astype(np.float64),
        aufloesung=aufloesung,
        x_min=0.0,
        y_min=0.0,
        z_max=0.0,  # Oberseite des „Materials" ist Z=0 (Werkstueck-Oberflaeche)
    )


def _box_blur(arr: np.ndarray, radius: int) -> np.ndarray:
    """Einfacher Box-Blur ueber die 2D-Array. Vermeidet scipy als Dep.

    Implementierung: kumulative Summen (Summed Area Table) → O(N) statt O(N·k²).
    """
    if radius < 1:
        return arr
    # Padding mit Reflektion damit die Raender nicht dunkel werden
    pad = radius
    pad_arr = np.pad(arr, pad_width=pad, mode="reflect")

    # Integral-Bild (cumsum 2D)
    integral = pad_arr.cumsum(axis=0).cumsum(axis=1)

    h, w = arr.shape
    out = np.zeros_like(arr)
    k = 2 * radius + 1
    area = k * k

    for i in range(h):
        for j in range(w):
            r1, c1 = i, j
            r2, c2 = i + 2 * pad, j + 2 * pad
            # Inklusiv-Exklusiv via integral
            total = integral[r2, c2]
            if r1 > 0:
                total -= integral[r1 - 1, c2]
            if c1 > 0:
                total -= integral[r2, c1 - 1]
            if r1 > 0 and c1 > 0:
                total += integral[r1 - 1, c1 - 1]
            out[i, j] = total / area

    return out


def heightmap_statistik(heightmap: Heightmap) -> dict:
    """Liefert Diagnose-Werte fuer eine Heightmap.

    Nuetzlich um vor dem Toolpath-Erzeugen abzuschaetzen ob die Heightmap
    sinnvolle Daten enthaelt.
    """
    z = heightmap.z_values
    nx, ny = z.shape
    return {
        "shape_x": int(nx),
        "shape_y": int(ny),
        "anzahl_pixel": int(nx * ny),
        "aufloesung_mm": float(heightmap.aufloesung),
        "breite_mm": float(nx * heightmap.aufloesung),
        "hoehe_mm": float(ny * heightmap.aufloesung),
        "z_min": float(np.min(z)),
        "z_max": float(np.max(z)),
        "z_mittel": float(np.mean(z)),
        "max_tiefe_mm": float(-np.min(z)),
    }


__all__ = [
    "BildHeightmapParameter",
    "heightmap_aus_bild",
    "heightmap_statistik",
]

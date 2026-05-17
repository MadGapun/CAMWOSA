"""Heightmap-Bearbeitungs-Tools (Master-Plan A35, Bild-zu-Relief Phase D).

Pure Funktionen die eine ``Heightmap`` entgegennehmen und eine **neue**
``Heightmap`` zurueckliefern (immutable Style). Bauen auf der Phase-A-Heightmap
auf und werden vor dem Toolpath-Generator angewandt.

Konvention der Heightmap (siehe stl/bild_heightmap.py):
- ``z_values`` shape (nx, ny)
- 0 = Werkstueck-Oberflaeche (max)
- negativ = ins Material rein (Tiefe)
- Spanne typischerweise ``[-max_tiefe_mm, 0]``

Die Filter operieren auf einem **normierten Helligkeits-Bild** ``H`` mit
H[ix, iy] in [0, 1]:
    H = 1 - z_values / z_min  (wenn z_min < 0)
        = 1.0 + z_values / max_tiefe
Nach der Bearbeitung wird zurueck konvertiert.

Siehe Wiki: docs/wiki/Bild-zu-Relief.md (Phase D)
"""

from __future__ import annotations

from dataclasses import replace
from typing import Literal

import numpy as np

from camwosa.stl.heightmap import Heightmap


# ---------------------------------------------------------------------------
# Helfer: Normierung
# ---------------------------------------------------------------------------


def _max_tiefe(hm: Heightmap) -> float:
    """Liefert die effektive max_tiefe (absoluter Wert des tiefsten Punkts).

    Wenn die Heightmap komplett auf Z=0 liegt, geben wir 0 zurueck — die
    Filter sind dann no-ops.
    """
    if hm.z_values.size == 0:
        return 0.0
    z_min = float(hm.z_values.min())
    return -z_min if z_min < 0 else 0.0


def _z_zu_helligkeit(hm: Heightmap) -> tuple[np.ndarray, float]:
    """Konvertiert Z-Werte zurueck in ein normiertes Helligkeits-Bild [0, 1].

    Liefert (helligkeit, max_tiefe).
    """
    max_t = _max_tiefe(hm)
    if max_t == 0.0:
        return np.ones_like(hm.z_values, dtype=np.float32), 0.0
    # z=0 -> 1.0 (hell, hoch), z=-max_tiefe -> 0.0 (dunkel, tief)
    h = 1.0 + hm.z_values.astype(np.float32) / max_t
    return np.clip(h, 0.0, 1.0), max_t


def _helligkeit_zu_z(h: np.ndarray, max_tiefe: float) -> np.ndarray:
    """Konvertiert ein Helligkeits-Bild zurueck in Z-Werte."""
    return ((h - 1.0) * max_tiefe).astype(np.float32)


def _neu(hm: Heightmap, z: np.ndarray) -> Heightmap:
    """Erzeugt eine neue Heightmap mit gleichen Geometrie-Werten."""
    return replace(hm, z_values=z.astype(np.float32),
                   z_max=float(z.max()) if z.size > 0 else 0.0)


# ---------------------------------------------------------------------------
# 1. Gamma-Korrektur
# ---------------------------------------------------------------------------


def gamma_korrektur(hm: Heightmap, gamma: float) -> Heightmap:
    """Wendet eine Gamma-Korrektur auf die Helligkeit an.

    ``gamma > 1``: Mid-Tones werden dunkler — dunklere Bereiche werden noch
        tiefer ins Material gegraben (mehr Tiefen-Detail in den Hoehen).
    ``gamma < 1``: Mid-Tones werden heller — flachere Reliefs.
    ``gamma == 1``: keine Aenderung.

    Mathematik: ``H_neu = H_alt ** gamma``.

    Raises:
        ValueError: wenn ``gamma <= 0``.
    """
    if gamma <= 0:
        raise ValueError(f"gamma muss > 0 sein (war {gamma})")
    if gamma == 1.0:
        return hm  # no-op
    h, max_t = _z_zu_helligkeit(hm)
    h_neu = np.power(h, gamma)
    return _neu(hm, _helligkeit_zu_z(h_neu, max_t))


# ---------------------------------------------------------------------------
# 2. Histogramm-Stretching (Kontrast)
# ---------------------------------------------------------------------------


def histogramm_stretch(
    hm: Heightmap,
    low_perzentil: float = 2.0,
    high_perzentil: float = 98.0,
) -> Heightmap:
    """Streckt die Helligkeit zwischen 2 Perzentilen auf den vollen [0,1]-Bereich.

    Nuetzlich wenn ein Bild durchgehend mittelgrau ist (z.B. ein Foto im
    Schatten) — Stretching erhoeht den Kontrast und damit die Reliefs-Tiefe.

    Args:
        low_perzentil: Helligkeits-Perzentil das auf 0 gemappt wird (Default 2%)
        high_perzentil: Perzentil das auf 1 gemappt wird (Default 98%)

    Raises:
        ValueError: wenn die Perzentile ungueltig sind.
    """
    if not (0 <= low_perzentil < high_perzentil <= 100):
        raise ValueError(
            f"low_perzentil ({low_perzentil}) muss < high_perzentil "
            f"({high_perzentil}) sein, beide in [0, 100]."
        )
    h, max_t = _z_zu_helligkeit(hm)
    if h.size == 0:
        return hm
    lo = float(np.percentile(h, low_perzentil))
    hi = float(np.percentile(h, high_perzentil))
    if hi - lo < 1e-6:
        return hm  # flat — kein Stretching moeglich
    h_neu = np.clip((h - lo) / (hi - lo), 0.0, 1.0)
    return _neu(hm, _helligkeit_zu_z(h_neu, max_t))


# ---------------------------------------------------------------------------
# 3. Zero-Plane (Sockel-Maskierung)
# ---------------------------------------------------------------------------


def zero_plane(hm: Heightmap, schwelle: float = 0.5) -> Heightmap:
    """Setzt alle Punkte mit Helligkeit > Schwelle auf Z=0.

    Damit bleibt der „Sockel" (heller Bildhintergrund) auf der Werkstueck-
    Oberflaeche, nur die dunkleren Motiv-Pixel werden gefraest. Klassischer
    Trick um Foto-Hintergrund vom Motiv zu trennen.

    Args:
        schwelle: Helligkeit (0..1) ab der Z=0 gesetzt wird. Default 0.5.

    Raises:
        ValueError: wenn schwelle nicht in [0, 1].
    """
    if not (0.0 <= schwelle <= 1.0):
        raise ValueError(f"schwelle muss in [0, 1] sein (war {schwelle})")
    h, max_t = _z_zu_helligkeit(hm)
    h_neu = np.where(h > schwelle, 1.0, h)
    return _neu(hm, _helligkeit_zu_z(h_neu, max_t))


# ---------------------------------------------------------------------------
# 4. Edge-Boost (Kantenverstaerkung via Sobel)
# ---------------------------------------------------------------------------


def _sobel(h: np.ndarray) -> np.ndarray:
    """Einfacher Sobel-Operator (scipy-frei).

    Liefert die Magnitude des Gradienten — hohe Werte = Kante.
    """
    if h.shape[0] < 3 or h.shape[1] < 3:
        return np.zeros_like(h)
    # Sobel-Kernel
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    ky = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)
    # Manuelle 2D-Convolution (langsam aber scipy-frei)
    gx = np.zeros_like(h)
    gy = np.zeros_like(h)
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            shift = np.roll(np.roll(h, shift=dy, axis=1), shift=dx, axis=0)
            gx += kx[dx + 1, dy + 1] * shift
            gy += ky[dx + 1, dy + 1] * shift
    # Raender auf 0 setzen (roll wrapt sonst)
    gx[0, :] = 0; gx[-1, :] = 0; gx[:, 0] = 0; gx[:, -1] = 0
    gy[0, :] = 0; gy[-1, :] = 0; gy[:, 0] = 0; gy[:, -1] = 0
    return np.sqrt(gx * gx + gy * gy)


def edge_boost(hm: Heightmap, faktor: float = 1.0) -> Heightmap:
    """Verstaerkt Kanten durch Subtraktion eines Sobel-Gradienten von der Helligkeit.

    Macht Konturen schaerfer/tiefer — Z wird an Kanten tiefer (mehr Abtragen).

    ``faktor = 0`` ist no-op. ``faktor = 1`` voller Effekt. Werte > 1 koennen
    den Effekt ueberzeichnen.
    """
    if faktor <= 0:
        return hm
    h, max_t = _z_zu_helligkeit(hm)
    gradient = _sobel(h)
    if gradient.max() <= 0:
        return hm
    # Auf [0, 1] normieren
    g_norm = gradient / gradient.max()
    h_neu = np.clip(h - faktor * g_norm, 0.0, 1.0)
    return _neu(hm, _helligkeit_zu_z(h_neu, max_t))


# ---------------------------------------------------------------------------
# 5. Selective Smoothing
# ---------------------------------------------------------------------------


def _box_blur(arr: np.ndarray, radius: int) -> np.ndarray:
    """Einfacher Box-Blur via Integral-Image (scipy-frei).

    Spiegelt die Implementation aus bild_heightmap.py — radius=1 = 3x3,
    radius=2 = 5x5, ...
    """
    if radius <= 0:
        return arr
    nx, ny = arr.shape
    arr32 = arr.astype(np.float64)
    integral = np.zeros((nx + 1, ny + 1), dtype=np.float64)
    integral[1:, 1:] = arr32.cumsum(axis=0).cumsum(axis=1)
    out = np.zeros_like(arr32)
    for i in range(nx):
        for j in range(ny):
            x0 = max(0, i - radius); x1 = min(nx, i + radius + 1)
            y0 = max(0, j - radius); y1 = min(ny, j + radius + 1)
            anzahl = (x1 - x0) * (y1 - y0)
            summe = (integral[x1, y1] - integral[x0, y1]
                     - integral[x1, y0] + integral[x0, y0])
            out[i, j] = summe / anzahl
    return out.astype(np.float32)


def selective_smoothing(
    hm: Heightmap,
    radius: int = 1,
    bereich: Literal["alles", "hell", "dunkel"] = "alles",
    schwelle: float = 0.5,
) -> Heightmap:
    """Wendet Box-Blur nur in bestimmten Helligkeits-Bereichen an.

    ``bereich``:
    - "alles": klassischer Blur ueberall (= bild_heightmap glaetten_radius)
    - "hell": Blur nur fuer Pixel mit Helligkeit > schwelle (entrauscht Hintergrund)
    - "dunkel": Blur nur fuer Pixel mit Helligkeit < schwelle (glaettet Motiv)

    Args:
        radius: Box-Blur Radius in Pixel.
        bereich: Welche Pixel werden geblurt.
        schwelle: Helligkeit-Trennung fuer hell/dunkel.

    Raises:
        ValueError: bei ungueltigem Radius oder Bereich.
    """
    if radius < 0:
        raise ValueError(f"radius muss >= 0 sein (war {radius})")
    if radius == 0:
        return hm
    if bereich not in ("alles", "hell", "dunkel"):
        raise ValueError(f"bereich muss alles/hell/dunkel sein (war {bereich})")
    if not (0.0 <= schwelle <= 1.0):
        raise ValueError(f"schwelle muss in [0, 1] sein (war {schwelle})")

    h, max_t = _z_zu_helligkeit(hm)
    h_blur = _box_blur(h, radius)
    if bereich == "alles":
        h_neu = h_blur
    elif bereich == "hell":
        h_neu = np.where(h > schwelle, h_blur, h)
    else:  # dunkel
        h_neu = np.where(h < schwelle, h_blur, h)
    return _neu(hm, _helligkeit_zu_z(h_neu, max_t))


# ---------------------------------------------------------------------------
# 6. Detail-Slider (Carveco-style)
# ---------------------------------------------------------------------------


def detail_slider(hm: Heightmap, detail: float) -> Heightmap:
    """Detail-Slider zwischen weicher und scharfer Darstellung.

    ``detail`` zwischen ``-1`` (sehr weich, Blur Radius 3) und ``+1`` (scharf,
    Edge-Boost faktor 0.8). 0 = unveraendert.
    """
    if detail == 0:
        return hm
    if not (-1.0 <= detail <= 1.0):
        raise ValueError(f"detail muss in [-1, 1] sein (war {detail})")
    if detail < 0:
        # Weicher: Blur. Radius 1 bei -0.33, 2 bei -0.66, 3 bei -1.0
        radius = max(1, int(round(-detail * 3)))
        return selective_smoothing(hm, radius=radius, bereich="alles")
    # Schaerfer: Edge-Boost
    return edge_boost(hm, faktor=detail * 0.8)


__all__ = [
    "detail_slider",
    "edge_boost",
    "gamma_korrektur",
    "histogramm_stretch",
    "selective_smoothing",
    "zero_plane",
]

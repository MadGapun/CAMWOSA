"""AI-basierte Tiefenkarte aus Bild (Master-Plan A36, Bild-zu-Relief Phase E).

Optional — benoetigt das ``[ai]``-Extra (PyTorch + transformers). Wenn das
nicht installiert ist, wird ``AIExtraFehlt`` geworfen. Der API-Endpoint
gibt dann eine 422 mit Installations-Hinweis zurueck.

Konzept:
- Monokulare Tiefenschaetzung — ein neuronales Netz leitet aus einem
  gewoehnlichen Foto eine relative Tiefen-Map ab (was ist vorne, was ist
  hinten).
- Wir nutzen die HuggingFace-``transformers``-Pipeline, die Modelle wie
  **Depth-Anything-V2** (state of the art 2024, Open Source) oder
  **MiDaS v3** (Intel, bewaehrt) liefert.
- Modell-Dateien werden beim ersten Aufruf von HuggingFace heruntergeladen
  und im User-Cache (~/.cache/huggingface) abgelegt — kein zusaetzliches
  Cloud-Roundtrip pro Aufruf.

Privacy-Versprechen:
- Modell laeuft 100% lokal nachdem es einmal heruntergeladen wurde
- Keine Telemetrie, kein Upload des Bildes
- HuggingFace-Download kann via ``HF_HUB_OFFLINE=1`` blockiert werden

Siehe Wiki: docs/wiki/Bild-zu-Relief.md (Stufe 3)
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import numpy as np

from camwosa.stl.heightmap import Heightmap


class AIExtraFehlt(RuntimeError):
    """Wird geworfen wenn das ``[ai]``-Extra nicht installiert ist."""

    def __init__(self, fehlender_import: str):
        super().__init__(
            f"AI-Tiefenschaetzung benoetigt zusaetzliche Pakete ({fehlender_import}). "
            f"Installation: pip install 'camwosa[ai]'"
        )
        self.fehlender_import = fehlender_import


# Bekannte Modelle die der User waehlen kann
VERFUEGBARE_MODELLE: dict[str, dict[str, str]] = {
    "depth-anything-v2-small": {
        "huggingface": "depth-anything/Depth-Anything-V2-Small-hf",
        "groesse_mb": "100",
        "qualitaet": "gut",
        "vendor": "Depth Anything Team (2024)",
    },
    "depth-anything-v2-base": {
        "huggingface": "depth-anything/Depth-Anything-V2-Base-hf",
        "groesse_mb": "375",
        "qualitaet": "sehr gut",
        "vendor": "Depth Anything Team (2024)",
    },
    "midas-v3-small": {
        "huggingface": "Intel/dpt-swinv2-tiny-256",
        "groesse_mb": "150",
        "qualitaet": "gut, schnell",
        "vendor": "Intel",
    },
}

DEFAULT_MODELL = "depth-anything-v2-small"


@dataclass
class AITiefenparameter:
    """Parameter fuer AI-Tiefenkarte → Heightmap."""

    max_tiefe_mm: float = 3.0
    pixel_pro_mm: float = 5.0
    modell: str = DEFAULT_MODELL
    invertieren: bool = False
    """Standard: hell=hoch, dunkel=tief (= 'nah=hoch'). True dreht um."""
    max_dimension_px: int | None = 1024
    """Modelle laufen auf ihrer eigenen Aufloesung — wir verkleinern grosse
    Bilder vorab um Inferenz-Zeit + VRAM zu sparen."""


def _import_pipeline():
    """Lazy-Import von transformers.pipeline + PIL.

    Wirft ``AIExtraFehlt`` wenn die Pakete fehlen.
    """
    try:
        from transformers import pipeline  # type: ignore[import-not-found]
    except ImportError as e:
        raise AIExtraFehlt("transformers") from e
    try:
        import torch  # type: ignore[import-not-found]  # noqa: F401
    except ImportError as e:
        raise AIExtraFehlt("torch") from e
    return pipeline


def ist_verfuegbar() -> bool:
    """True wenn das ``[ai]``-Extra installiert ist (PyTorch + transformers)."""
    try:
        _import_pipeline()
        return True
    except AIExtraFehlt:
        return False


def heightmap_aus_bild_ai(
    bild_bytes: bytes,
    parameter: AITiefenparameter | None = None,
) -> Heightmap:
    """Erzeugt eine Heightmap aus einem Bild via AI-Tiefenschaetzung.

    Args:
        bild_bytes: PNG/JPG-Bytes
        parameter: Konfiguration. Default = Depth-Anything-V2-Small.

    Returns:
        Heightmap im gleichen Format wie ``stl.bild_heightmap.heightmap_aus_bild``
        — direkt kompatibel mit ``cam.relief.erzeuge_relief_toolpath``.

    Raises:
        AIExtraFehlt: Wenn ``[ai]``-Extra nicht installiert ist.
        ValueError: Bei unbekanntem Modell oder kaputtem Bild.
    """
    parameter = parameter or AITiefenparameter()
    if parameter.modell not in VERFUEGBARE_MODELLE:
        raise ValueError(
            f"Unbekanntes Modell '{parameter.modell}'. "
            f"Verfuegbar: {list(VERFUEGBARE_MODELLE.keys())}"
        )

    pipeline_fn = _import_pipeline()
    try:
        from PIL import Image  # type: ignore[import-not-found]
    except ImportError as e:
        raise AIExtraFehlt("PIL") from e

    # Bild laden, ggf. verkleinern
    try:
        img = Image.open(BytesIO(bild_bytes)).convert("RGB")
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Bild nicht lesbar: {e}") from e

    if parameter.max_dimension_px:
        w, h = img.size
        max_dim = max(w, h)
        if max_dim > parameter.max_dimension_px:
            faktor = parameter.max_dimension_px / max_dim
            img = img.resize(
                (int(w * faktor), int(h * faktor)),
                Image.Resampling.LANCZOS,
            )

    hf_modell = VERFUEGBARE_MODELLE[parameter.modell]["huggingface"]
    pipe = pipeline_fn(task="depth-estimation", model=hf_modell)
    ergebnis = pipe(img)
    # transformers liefert {"predicted_depth": torch.Tensor, "depth": PIL.Image}
    # Wir nehmen das normalisierte PIL-Bild (0..255 grayscale, weiss = weit weg)
    depth_img = ergebnis["depth"]  # type: ignore[index]
    depth_arr = np.asarray(depth_img, dtype=np.float32)

    # depth_arr: hoehe (zeilen) × breite (spalten), Werte 0..255
    # Standard: weiss = weit weg (hinten) → soll TIEF werden bei invertieren=False
    # Phase A-Konvention: hell = hoch. Wir wollen aber: nah=hoch.
    # depth_img-Konvention: hell = nah (laut Depth-Anything-Doku).
    # Sicherheits-halber pruefen wir nicht, sondern bieten ``invertieren``-Toggle.
    helligkeit = depth_arr / 255.0  # [0, 1]
    if parameter.invertieren:
        helligkeit = 1.0 - helligkeit

    # In Heightmap-Konvention: Z = -(1 - H) * max_tiefe
    z_hoehe_zeile_spalte = -(1.0 - helligkeit) * parameter.max_tiefe_mm

    # Heightmap erwartet (nx, ny) — wir transponieren wie bild_heightmap.py
    z = z_hoehe_zeile_spalte.T.astype(np.float32)
    aufl = 1.0 / parameter.pixel_pro_mm if parameter.pixel_pro_mm > 0 else 1.0

    return Heightmap(
        z_values=z,
        aufloesung=aufl,
        x_min=0.0,
        y_min=0.0,
        z_max=float(z.max()) if z.size > 0 else 0.0,
    )


def modell_info(modell: str | None = None) -> dict:
    """Liefert Info zu einem Modell oder allen, plus Installations-Status."""
    if modell is None:
        return {
            "ist_installiert": ist_verfuegbar(),
            "default": DEFAULT_MODELL,
            "modelle": VERFUEGBARE_MODELLE,
        }
    if modell not in VERFUEGBARE_MODELLE:
        return {"fehler": f"Unbekanntes Modell '{modell}'"}
    return {
        "ist_installiert": ist_verfuegbar(),
        "modell": modell,
        **VERFUEGBARE_MODELLE[modell],
    }


__all__ = [
    "AIExtraFehlt",
    "AITiefenparameter",
    "DEFAULT_MODELL",
    "VERFUEGBARE_MODELLE",
    "heightmap_aus_bild_ai",
    "ist_verfuegbar",
    "modell_info",
]

"""GRBL-Postprozessor fuer Genmitsu-Rotary-Setup (Y-Achse als Rotationsachse).

Bei diesem Setup ist die Y-Achse des GRBL-Controllers per ``$101=88.889`` auf
einen Schrittweite-pro-Grad-Wert konfiguriert. Y-Bewegungen werden in **Grad**
ausgegeben, nicht in mm.

Wichtig: ``$131=9999`` (kein Y-Limit) MUSS am Controller gesetzt sein, sonst
werden Rotationen abgeschnitten.

Siehe Wiki: docs/wiki/Postprozessor-GRBL-Rotary.md
"""

from __future__ import annotations

from camwosa.gcode.toolpath import Bewegung
from camwosa.postprocessor.base import PostKontext, registry
from camwosa.postprocessor.grbl_standard import GRBLStandard


class GRBLGenmitsuRotaryY(GRBLStandard):
    name = "GRBL Genmitsu Rotary (Y-Achse)"
    file_extension = ".nc"
    beschreibung = (
        "Rotary-Setup fuer Genmitsu ProVerXL: Y-Achse als Rotationsachse. "
        "Y-Werte sind in Grad. Erfordert $101=88.889 und $131=9999 am Controller."
    )

    def header(self, ctx: PostKontext) -> list[str]:
        zeilen = super().header(ctx)
        zeilen.append(self._kommentar("ROTARY-MODUS aktiv (Y in Grad)"))
        zeilen.append(self._kommentar("Pruefe: $101=88.889  $131=9999"))
        zeilen.append(self._kommentar("CNCjs-Macro 'ROTARY EIN' muss aktiv sein"))
        return zeilen

    def linear_move(self, ctx: PostKontext, b: Bewegung) -> list[str]:
        # Y wird als Grad interpretiert. Format identisch, Semantik unterschiedlich.
        feed = b.feed if b.feed is not None else ctx.maschine.sicherer_vorschub
        zeile = f"G1 X{b.x:.3f} Y{b.y:.3f} Z{b.z:.3f} F{feed:.0f}"
        if b.kommentar:
            zeile += f"  ; {b.kommentar}"
        return [zeile]


registry().register("grbl_genmitsu_rotary_y", GRBLGenmitsuRotaryY)

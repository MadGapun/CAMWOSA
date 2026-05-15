"""Genmitsu-Variante des GRBL-Postprozessors.

Praktisch identisch zum Standard, aber mit Genmitsu-spezifischem Header und
expliziter Soft-Limit-Pruefung im Kommentar.

Siehe Wiki: docs/wiki/Postprozessor-GRBL-Genmitsu.md
"""

from __future__ import annotations

from camwosa.postprocessor.base import PostKontext, registry
from camwosa.postprocessor.grbl_standard import GRBLStandard


class GRBLGenmitsu(GRBLStandard):
    name = "GRBL Genmitsu"
    file_extension = ".nc"
    beschreibung = "GRBL fuer Genmitsu (ProVerXL, PROVer): Header mit Modus-Hinweis"

    def header(self, ctx: PostKontext) -> list[str]:
        zeilen = super().header(ctx)
        zeilen.insert(
            1,
            self._kommentar(
                f"Maschinen-Modus: {ctx.maschine.aktiver_modus.value} "
                f"(bitte $101 in CNCjs pruefen!)"
            ),
        )
        return zeilen


registry().register("grbl_genmitsu", GRBLGenmitsu)

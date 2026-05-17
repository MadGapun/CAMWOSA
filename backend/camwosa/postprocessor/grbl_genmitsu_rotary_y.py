"""GRBL-Postprozessor fuer Genmitsu-Rotary-Setup (Y-Achse als Rotationsachse).

Bei diesem Setup ist die Y-Achse des GRBL-Controllers per ``$101=88.889`` auf
einen Schrittweite-pro-Grad-Wert konfiguriert. Y-Bewegungen werden in **Grad**
ausgegeben, nicht in mm.

Wichtig: ``$131=9999`` (kein Y-Limit) MUSS am Controller gesetzt sein, sonst
werden Rotationen abgeschnitten.

Drechsel-Modus (= Wrap-Carving mit Werkstueck-Rotation)
-------------------------------------------------------
Wenn ein Toolpath mit ``metadaten["ist_drechseln"] = True`` markiert ist (siehe
``cam/drechseln.py``), schreibt dieser Postprozessor einen erweiterten Header.

WICHTIG: Auf der ProVerXL ist das kein klassisches Drechseln, sondern
4-Achs-Fraesen mit Werkstueck-Rotation. Die Spindel haengt vertikal, der
Fraeser dreht selbst mit hoher Drehzahl, und das Werkstueck rotiert
langsam darunter durch. Der Toolpath enthaelt nur X+Z-Bewegungen; die
A-Achsen-Drehung muss VOR dem Job per CNCjs-Makro oder manuell gestartet
werden. Wir geben das als Kommentar-Block im G-Code-Header aus, damit es
beim Editor-Review nicht uebersehen wird.

Siehe Wiki: docs/wiki/Postprozessor-GRBL-Rotary.md
"""

from __future__ import annotations

from typing import Iterable

from camwosa.gcode.toolpath import Bewegung, Toolpath
from camwosa.postprocessor.base import PostKontext, registry
from camwosa.postprocessor.grbl_standard import GRBLStandard


class GRBLGenmitsuRotaryY(GRBLStandard):
    name = "GRBL Genmitsu Rotary (Y-Achse)"
    file_extension = ".nc"
    beschreibung = (
        "Rotary-Setup fuer Genmitsu ProVerXL: Y-Achse als Rotationsachse. "
        "Y-Werte sind in Grad. Erfordert $101=88.889 und $131=9999 am Controller. "
        "Erkennt Drechsel-Operationen (kontinuierliche A-Drehung)."
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

    # -----------------------------------------------------------------------
    # Drechsel-Erkennung pro Toolpath
    # -----------------------------------------------------------------------

    def post(self, ctx: PostKontext, toolpath: Toolpath) -> list[str]:
        zeilen: list[str] = []
        if toolpath.metadaten.get("ist_drechseln"):
            zeilen.extend(self._drechsel_vorlauf(toolpath))
        zeilen.extend(super().post(ctx, toolpath))
        if toolpath.metadaten.get("ist_drechseln"):
            zeilen.extend(self._drechsel_nachlauf())
        return zeilen

    def post_alle(self, ctx: PostKontext, toolpaths: Iterable[Toolpath]) -> list[str]:
        # Wir wollen einmal eine globale Setup-Warnung im Header, wenn IRGENDEIN
        # Toolpath Drechseln ist. Dazu materialisieren wir die Iterable.
        toolpaths_liste = list(toolpaths)
        hat_drechseln = any(
            tp.metadaten.get("ist_drechseln") for tp in toolpaths_liste
        )
        zeilen: list[str] = []
        if hat_drechseln:
            zeilen.extend(self._drechsel_header_warnung(toolpaths_liste))
        zeilen.extend(super().post_alle(ctx, toolpaths_liste))
        return zeilen

    def _drechsel_header_warnung(self, toolpaths: list[Toolpath]) -> list[str]:
        """Banner ueber dem normalen Header — User soll das nicht uebersehen."""
        drech_paths = [tp for tp in toolpaths if tp.metadaten.get("ist_drechseln")]
        upm_werte = sorted({
            tp.metadaten.get("drehzahl_werkstueck_upm", "?")
            for tp in drech_paths
        })
        return [
            self._kommentar("=" * 60),
            self._kommentar("DRECHSEL-JOB — VOR DEM START PRUEFEN"),
            self._kommentar(f"  - {len(drech_paths)} Drechsel-Toolpath(s) im File"),
            self._kommentar(f"  - Werkstueck-Drehzahl(en) U/min: {', '.join(map(str, upm_werte))}"),
            self._kommentar("  - Rotary-Aufsatz montiert? Werkstueck zentriert? Reitstock fest?"),
            self._kommentar("  - CNCjs: ROTARY EIN aufrufen (oder Aequivalent)"),
            self._kommentar("  - WICHTIG: Werkstueck-Drehung BEVOR Werkzeug eintaucht starten"),
            self._kommentar("=" * 60),
        ]

    def _drechsel_vorlauf(self, toolpath: Toolpath) -> list[str]:
        m = toolpath.metadaten
        upm = m.get("drehzahl_werkstueck_upm", "?")
        roh_r = m.get("rohmaterial_radius_mm", "?")
        strategie = m.get("strategie", "?")
        zeilen = [
            self._kommentar(""),
            self._kommentar(f"--- DRECHSELN: Strategie '{strategie}' ---"),
            self._kommentar(f"  Werkstueck-Drehzahl: {upm} U/min"),
            self._kommentar(f"  Rohmaterial-Radius: {roh_r} mm"),
            self._kommentar(f"  Profil-Punkte: {m.get('profil_punkte', '?')}"),
        ]
        if strategie == "helix":
            steigung = m.get("helix_steigung_mm", "?")
            tiefe = m.get("helix_tiefe_mm", "?")
            passes = m.get("helix_anzahl_passes", "?")
            sync_feed = m.get("helix_x_vorschub_mm_min", "?")
            zeilen.extend([
                self._kommentar(f"  Helix-Steigung: {steigung} mm/Umdrehung"),
                self._kommentar(f"  Helix-Tiefe: {tiefe} mm in {passes} Pass(es)"),
                self._kommentar(f"  X-Vorschub synchronisiert: {sync_feed} mm/min "
                                  f"(= steigung × drehzahl)"),
                self._kommentar(
                    "  WICHTIG: A-Drehzahl genau einhalten — Steigung haengt davon ab!"
                ),
            ])
        zeilen.extend([
            self._kommentar(""),
            "; %wait  ; CNCjs-Pause — User bestaetigt dass A-Achse rotiert",
        ])
        return zeilen

    def _drechsel_nachlauf(self) -> list[str]:
        return [
            self._kommentar(""),
            self._kommentar("--- DRECHSELN beendet — A-Achse kann jetzt gestoppt werden ---"),
        ]


registry().register("grbl_genmitsu_rotary_y", GRBLGenmitsuRotaryY)

"""GRBL-Standard-Postprozessor (GRBL 1.1, mm).

Erzeugt G-Code der ohne Anpassung in CNCjs / UGS / Candle laden faehrt.

Konventionen:
    - Einheiten: mm (G21)
    - Absolute Koordinaten (G90)
    - XY-Ebene (G17)
    - Spindel-Steuerung mit M3/M5
    - Werkzeugwechsel: M0-Pause (GRBL kennt kein M6)

Siehe Wiki: docs/wiki/Postprozessor-GRBL.md
"""

from __future__ import annotations

from camwosa.gcode.toolpath import Bewegung, BewegungsTyp
from camwosa.postprocessor.base import PostKontext, PostProcessor, registry


class GRBLStandard(PostProcessor):
    name = "GRBL Standard"
    file_extension = ".nc"
    beschreibung = "Standard-GRBL 1.1 Postprozessor (mm, absolute Koordinaten)"

    # ---- Lifecycle --------------------------------------------------------

    def header(self, ctx: PostKontext) -> list[str]:
        zeilen = [
            self._kommentar(f"CAMWOSA G-Code"),
            self._kommentar(f"Maschine: {ctx.maschine.name}"),
            self._kommentar(f"Werkzeug: {ctx.werkzeug.name} (D={ctx.werkzeug.durchmesser}mm)"),
            "G21",  # mm
            "G90",  # absolute coords
            "G17",  # XY-Ebene
            "G94",  # Vorschub mm/min
        ]
        if ctx.operation_kommentar:
            zeilen.append(self._kommentar(ctx.operation_kommentar))
        return zeilen

    def footer(self, ctx: PostKontext) -> list[str]:
        zeilen = []
        # Park-Position falls definiert
        if ctx.maschine.werkzeugwechsel_position is not None:
            x, y, z = ctx.maschine.werkzeugwechsel_position
            zeilen.append(f"G0 Z{ctx.maschine.sicherheitshoehe:.3f}")
            zeilen.append(f"G0 X{x:.3f} Y{y:.3f}")
        zeilen.append("M30")
        return zeilen

    def tool_change(self, ctx: PostKontext, tool) -> list[str]:
        """GRBL kennt kein M6. Wir machen M0-Pause + Hinweis."""
        zeilen = [
            self.spindle_off(ctx)[0],
            f"G0 Z{ctx.maschine.sicherheitshoehe:.3f}",
        ]
        if ctx.maschine.werkzeugwechsel_position is not None:
            x, y, _ = ctx.maschine.werkzeugwechsel_position
            zeilen.append(f"G0 X{x:.3f} Y{y:.3f}")
        zeilen.append(self._kommentar(f"WERKZEUGWECHSEL auf {tool.name}"))
        zeilen.append("M0")  # Pause bis User Continue drueckt
        return zeilen

    # ---- Bewegungen -------------------------------------------------------

    def rapid_move(self, ctx: PostKontext, b: Bewegung) -> list[str]:
        zeile = f"G0 X{b.x:.3f} Y{b.y:.3f} Z{b.z:.3f}"
        if b.kommentar:
            zeile += f"  ; {b.kommentar}"
        return [zeile]

    def linear_move(self, ctx: PostKontext, b: Bewegung) -> list[str]:
        feed = b.feed if b.feed is not None else ctx.maschine.sicherer_vorschub
        zeile = f"G1 X{b.x:.3f} Y{b.y:.3f} Z{b.z:.3f} F{feed:.0f}"
        if b.kommentar:
            zeile += f"  ; {b.kommentar}"
        return [zeile]

    def arc_move(self, ctx: PostKontext, b: Bewegung) -> list[str]:
        feed = b.feed if b.feed is not None else ctx.maschine.sicherer_vorschub
        cmd = "G2" if b.typ == BewegungsTyp.BOGEN_CW else "G3"
        i = b.i if b.i is not None else 0.0
        j = b.j if b.j is not None else 0.0
        zeile = f"{cmd} X{b.x:.3f} Y{b.y:.3f} Z{b.z:.3f} I{i:.3f} J{j:.3f} F{feed:.0f}"
        if b.kommentar:
            zeile += f"  ; {b.kommentar}"
        return [zeile]


registry().register("grbl_standard", GRBLStandard)

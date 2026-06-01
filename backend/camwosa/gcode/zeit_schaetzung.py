"""Bearbeitungszeit-Schätzung (Cluster K5, Issue #47).

Eine der ersten Anfänger-Fragen: „Wie lange dauert das?" — und ein Standard-
Feature jedes Hobby-CAM-Tools (EstlCAM, DeskProto, Carbide Create, LightBurn).

Der Toolpath hat bereits eine einfache `zeitschaetzung_minuten()`. Dieses Modul
baut die anfänger-taugliche Schicht darüber:
- **Schnitt- vs. Eilgang-Zeit getrennt** (zeigt, wo die Zeit hingeht)
- **Beschleunigungs-Overhead** — eine reale Hobby-Maschine bremst an jeder Ecke
  ab; die theoretische Zeit (Länge/Vorschub) unterschätzt um ~10-20 %. Wir
  multiplizieren mit einem Overhead-Faktor (Default 1.15).
- **Job-Aggregation** über mehrere Operationen + Werkzeugwechsel-Pausen
- **Klartext** („~23 Min 12 Sek")

Bewusst eine *Schätzung*, kein exakter Wert — Vorschub-Override, Genauigkeits-
Profil und Dwell beeinflussen die reale Zeit. Anfänger brauchen die
Größenordnung, nicht die Sekunde.
"""

from __future__ import annotations

from dataclasses import dataclass

from camwosa.gcode.toolpath import BewegungsTyp, Toolpath


@dataclass
class ZeitSchaetzung:
    """Aufgeschlüsselte Zeitschätzung."""

    schnitt_sekunden: float
    eilgang_sekunden: float
    pausen_sekunden: float  # Werkzeugwechsel, Dwell etc.
    overhead_faktor: float

    @property
    def gesamt_sekunden(self) -> float:
        return self.schnitt_sekunden + self.eilgang_sekunden + self.pausen_sekunden

    @property
    def gesamt_minuten(self) -> float:
        return self.gesamt_sekunden / 60.0

    @property
    def klartext(self) -> str:
        """Menschenlesbar, z.B. „1 Std 23 Min" oder „4 Min 12 Sek"."""
        return formatiere_dauer(self.gesamt_sekunden)


def formatiere_dauer(sekunden: float) -> str:
    """Sekunden → kompakter deutscher Klartext."""
    if sekunden < 1:
        return "unter 1 Sek"
    s = int(round(sekunden))
    std, rest = divmod(s, 3600)
    minuten, sek = divmod(rest, 60)
    teile: list[str] = []
    if std:
        teile.append(f"{std} Std")
    if minuten:
        teile.append(f"{minuten} Min")
    # Sekunden nur zeigen wenn unter 10 Min (sonst irrelevant für die Größenordnung)
    if sek and std == 0 and minuten < 10:
        teile.append(f"{sek} Sek")
    if not teile:
        teile.append(f"{sek} Sek")
    return " ".join(teile)


def schaetze_toolpath_zeit(
    toolpath: Toolpath,
    *,
    eilgang_mm_min: float,
    overhead_faktor: float = 1.15,
    fallback_vorschub_mm_min: float = 1000.0,
) -> ZeitSchaetzung:
    """Schätzt die Zeit eines einzelnen Toolpaths, Schnitt/Eilgang getrennt.

    Args:
        eilgang_mm_min: Eilgang-Geschwindigkeit der Maschine (G0).
        overhead_faktor: Multiplikator für Beschleunigung/Verzögerung (>=1).
        fallback_vorschub_mm_min: wenn eine Bewegung keinen Feed hat.
    """
    if eilgang_mm_min <= 0:
        raise ValueError("eilgang_mm_min muss > 0 sein.")
    if overhead_faktor < 1.0:
        raise ValueError("overhead_faktor muss >= 1.0 sein.")

    schnitt_min = 0.0
    eilgang_min = 0.0
    bew = toolpath.bewegungen
    if len(bew) >= 2:
        prev = bew[0]
        for b in bew[1:]:
            dx = b.x - prev.x
            dy = b.y - prev.y
            dz = b.z - prev.z
            d = (dx * dx + dy * dy + dz * dz) ** 0.5
            if b.typ == BewegungsTyp.EILGANG:
                eilgang_min += d / eilgang_mm_min
            else:
                vorschub = b.feed or fallback_vorschub_mm_min
                schnitt_min += d / vorschub
            prev = b

    return ZeitSchaetzung(
        schnitt_sekunden=schnitt_min * 60.0 * overhead_faktor,
        eilgang_sekunden=eilgang_min * 60.0 * overhead_faktor,
        pausen_sekunden=0.0,
        overhead_faktor=overhead_faktor,
    )


def schaetze_job_zeit(
    toolpaths: list[Toolpath],
    *,
    eilgang_mm_min: float,
    werkzeugwechsel_sekunden: float = 45.0,
    overhead_faktor: float = 1.15,
    fallback_vorschub_mm_min: float = 1000.0,
) -> ZeitSchaetzung:
    """Aggregiert die Zeit über mehrere Operationen + Werkzeugwechsel-Pausen.

    Ein Werkzeugwechsel wird gezählt, wenn sich die `werkzeug_id` zwischen
    aufeinanderfolgenden Toolpaths ändert (manueller Wechsel kostet Zeit).
    """
    schnitt = 0.0
    eilgang = 0.0
    pausen = 0.0
    letztes_werkzeug: str | None = None

    for tp in toolpaths:
        if letztes_werkzeug is not None and tp.werkzeug_id != letztes_werkzeug:
            pausen += werkzeugwechsel_sekunden
        letztes_werkzeug = tp.werkzeug_id

        teil = schaetze_toolpath_zeit(
            tp,
            eilgang_mm_min=eilgang_mm_min,
            overhead_faktor=overhead_faktor,
            fallback_vorschub_mm_min=fallback_vorschub_mm_min,
        )
        schnitt += teil.schnitt_sekunden
        eilgang += teil.eilgang_sekunden

    return ZeitSchaetzung(
        schnitt_sekunden=schnitt,
        eilgang_sekunden=eilgang,
        pausen_sekunden=pausen,
        overhead_faktor=overhead_faktor,
    )


__all__ = [
    "ZeitSchaetzung",
    "formatiere_dauer",
    "schaetze_job_zeit",
    "schaetze_toolpath_zeit",
]

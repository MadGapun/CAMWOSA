"""Tests fuer PCB-Isolationsfraesen."""

from __future__ import annotations

from shapely.geometry import Polygon

from camwosa.cam.pcb import PCBParameter, erzeuge_pcb_isolation_toolpath


def test_pcb_isolation_eine_leiterbahn(vbit_60grad) -> None:
    pad = Polygon([(0, 0), (10, 0), (10, 5), (0, 5)])
    p = PCBParameter(
        werkzeug_id=vbit_60grad.id,
        spindel_rpm=20000, vorschub=300, eintauch_vorschub=100,
        sicherheitshoehe=1.5, isolations_tiefe=0.15,
        isolations_abstand=0.3, anzahl_spuren=1,
    )
    tp = erzeuge_pcb_isolation_toolpath([pad], vbit_60grad, p)
    assert tp.metadaten["operation"] == "pcb_isolation"
    assert len(tp.bewegungen) > 5


def test_pcb_isolation_mehrere_spuren(vbit_60grad) -> None:
    pad = Polygon([(0, 0), (10, 0), (10, 5), (0, 5)])
    p = PCBParameter(
        werkzeug_id=vbit_60grad.id,
        spindel_rpm=20000, vorschub=300, eintauch_vorschub=100,
        isolations_tiefe=0.15, isolations_abstand=0.3, anzahl_spuren=3,
    )
    tp = erzeuge_pcb_isolation_toolpath([pad], vbit_60grad, p)
    # 3 Spuren = mehr Bewegungen
    p1 = PCBParameter(
        werkzeug_id=vbit_60grad.id,
        spindel_rpm=20000, vorschub=300, eintauch_vorschub=100,
        isolations_tiefe=0.15, isolations_abstand=0.3, anzahl_spuren=1,
    )
    tp1 = erzeuge_pcb_isolation_toolpath([pad], vbit_60grad, p1)
    assert len(tp.bewegungen) > len(tp1.bewegungen) * 2

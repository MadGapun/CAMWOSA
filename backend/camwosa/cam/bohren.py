"""CAM-Operation: Bohren.

Erzeugt einen Toolpath fuer Bohrungen an definierten X/Y-Positionen.

Strategien:
- STANDARD: direkt nach unten und hoch
- PECK: schrittweise mit kleinem Rueckzug zur Spanabfuhr
- TIEF_PECK: schrittweise mit Rueckzug auf Sicherheitshoehe
- HELIX: schraubendes Helix-Bohren (auch fuer Loecher groesser als Fraeser)
- REIB: Konturbohren mit kleinerem Werkzeug

Phase 1 implementiert STANDARD, PECK, TIEF_PECK.
HELIX und REIB folgen.

Siehe Wiki: docs/wiki/Operation-Bohren.md
"""

from __future__ import annotations

import math

from camwosa.cam.parameter import BohrParameter, BohrStrategie
from camwosa.db.models import Werkzeug
from camwosa.dxf.parser import GeometrieObjekt, GeometrieTyp, Punkt2D
from camwosa.gcode.toolpath import (
    Bewegung,
    BewegungsTyp,
    OperationsTyp,
    Toolpath,
)


def erzeuge_bohren_toolpath(
    punkte: list[Punkt2D] | list[GeometrieObjekt],
    werkzeug: Werkzeug,
    parameter: BohrParameter,
    *,
    operation_id: str = "bohren",
) -> Toolpath:
    bohrungen = _extrahiere_bohrungen(punkte)
    bewegungen: list[Bewegung] = []
    for x, y in bohrungen:
        bewegungen.extend(_bohrung_bewegungen(x, y, werkzeug, parameter))
    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.BOHREN,
        werkzeug_id=werkzeug.id,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe,
        bewegungen=bewegungen,
        kommentar=f"Bohren {len(bohrungen)} Loecher ({parameter.strategie.value})",
        metadaten={"strategie": parameter.strategie.value, "anzahl": len(bohrungen)},
    )


def _extrahiere_bohrungen(
    eingabe: list[Punkt2D] | list[GeometrieObjekt],
) -> list[tuple[float, float]]:
    bohrungen: list[tuple[float, float]] = []
    for e in eingabe:
        if isinstance(e, Punkt2D):
            bohrungen.append((e.x, e.y))
        elif isinstance(e, GeometrieObjekt):
            if e.typ == GeometrieTyp.PUNKT:
                bohrungen.append((e.punkte[0].x, e.punkte[0].y))
            elif e.typ == GeometrieTyp.KREIS:
                bohrungen.append((e.punkte[0].x, e.punkte[0].y))
            else:
                # Polylinie -> verwende ersten Punkt
                bohrungen.append((e.punkte[0].x, e.punkte[0].y))
    return bohrungen


def _bohrung_bewegungen(
    x: float, y: float, werkzeug: Werkzeug, parameter: BohrParameter
) -> list[Bewegung]:
    z_unten = -abs(parameter.max_tiefe)
    bewegungen: list[Bewegung] = [
        Bewegung(BewegungsTyp.EILGANG, x, y, parameter.sicherheitshoehe,
                 kommentar=f"Bohrung X={x:.2f} Y={y:.2f}"),
    ]

    if parameter.strategie == BohrStrategie.STANDARD:
        bewegungen.append(
            Bewegung(BewegungsTyp.PLUNGE, x, y, z_unten,
                     feed=parameter.eintauch_vorschub)
        )
    elif parameter.strategie == BohrStrategie.PECK:
        z_aktuell = 0.0
        while z_aktuell > z_unten + 1e-9:
            z_aktuell = max(z_aktuell - parameter.peck_tiefe, z_unten)
            bewegungen.append(
                Bewegung(BewegungsTyp.PLUNGE, x, y, z_aktuell,
                         feed=parameter.eintauch_vorschub)
            )
            if z_aktuell > z_unten + 1e-9:
                # kurzer Rueckzug
                bewegungen.append(
                    Bewegung(BewegungsTyp.EILGANG, x, y,
                             z_aktuell + parameter.rueckzugs_hoehe,
                             kommentar="Peck Rueckzug")
                )
    elif parameter.strategie == BohrStrategie.TIEF_PECK:
        z_aktuell = 0.0
        while z_aktuell > z_unten + 1e-9:
            z_aktuell = max(z_aktuell - parameter.peck_tiefe, z_unten)
            bewegungen.append(
                Bewegung(BewegungsTyp.PLUNGE, x, y, z_aktuell,
                         feed=parameter.eintauch_vorschub)
            )
            if z_aktuell > z_unten + 1e-9:
                bewegungen.append(
                    Bewegung(BewegungsTyp.EILGANG, x, y,
                             parameter.sicherheitshoehe,
                             kommentar="Tief-Peck Rueckzug")
                )
                bewegungen.append(
                    Bewegung(BewegungsTyp.EILGANG, x, y, z_aktuell + 0.5)
                )
    elif parameter.strategie == BohrStrategie.HELIX:
        # Helix-Bohren: Werkzeug fraest schraubig nach unten auf einer Kreisbahn.
        # Loch-Durchmesser muss >= Werkzeug-Durchmesser sein.
        loch_d = parameter.loch_durchmesser or werkzeug.durchmesser
        if loch_d < werkzeug.durchmesser:
            raise ValueError(
                f"Loch-Durchmesser {loch_d} < Werkzeug-Durchmesser {werkzeug.durchmesser}"
            )
        bahn_radius = (loch_d - werkzeug.durchmesser) / 2.0
        if bahn_radius < 0.05:
            # praktisch wie Standard-Plunge, weil Loch = Werkzeug
            bewegungen.append(Bewegung(
                BewegungsTyp.PLUNGE, x, y, z_unten,
                feed=parameter.eintauch_vorschub,
            ))
        else:
            # Anfahrt zur Helix-Startposition (Aussenkante)
            bewegungen.append(Bewegung(
                BewegungsTyp.EILGANG, x + bahn_radius, y, parameter.sicherheitshoehe,
                kommentar="Helix-Anfahrt",
            ))
            bewegungen.append(Bewegung(
                BewegungsTyp.PLUNGE, x + bahn_radius, y, 0,
                feed=parameter.eintauch_vorschub,
            ))
            # Anzahl Umdrehungen
            tiefe = abs(z_unten)
            n_umdrehungen = max(1, int(math.ceil(tiefe / parameter.helix_steigung)))
            segmente_pro_umdrehung = 24
            n_segmente = n_umdrehungen * segmente_pro_umdrehung
            for i in range(1, n_segmente + 1):
                t = i / n_segmente
                winkel = 2 * math.pi * n_umdrehungen * t
                z = -tiefe * t
                px = x + bahn_radius * math.cos(winkel)
                py = y + bahn_radius * math.sin(winkel)
                bewegungen.append(Bewegung(
                    BewegungsTyp.LINEAR, px, py, z, feed=parameter.vorschub,
                ))
            # Boden-Kreis (Schlichtgang auf z_unten)
            for i in range(1, segmente_pro_umdrehung + 1):
                winkel = 2 * math.pi * i / segmente_pro_umdrehung
                px = x + bahn_radius * math.cos(winkel)
                py = y + bahn_radius * math.sin(winkel)
                bewegungen.append(Bewegung(
                    BewegungsTyp.LINEAR, px, py, z_unten, feed=parameter.vorschub,
                    kommentar="Helix-Bodenschlicht" if i == 1 else "",
                ))
    elif parameter.strategie == BohrStrategie.REIB:
        # Reib-Bohren: Werkzeug fraest Kreis-Kontur in der Tiefe (Loch > Werkzeug).
        loch_d = parameter.loch_durchmesser or (werkzeug.durchmesser * 1.5)
        if loch_d <= werkzeug.durchmesser:
            raise ValueError(
                f"REIB braucht Loch-Durchmesser > Werkzeug-Durchmesser "
                f"({loch_d} <= {werkzeug.durchmesser})"
            )
        bahn_radius = (loch_d - werkzeug.durchmesser) / 2.0
        # Vor-Plunge in der Mitte (klassischer Bohrschritt — Werkzeug muss stirnschneidend sein)
        bewegungen.append(Bewegung(
            BewegungsTyp.PLUNGE, x, y, z_unten,
            feed=parameter.eintauch_vorschub, kommentar="Reib Vor-Plunge",
        ))
        # Spiralbewegung nach aussen auf Bahn-Radius
        n = 32
        for i in range(1, n + 1):
            t = i / n
            r = bahn_radius * t
            winkel = 2 * math.pi * t * 2  # 2 Umdrehungen waehrend Expansion
            px = x + r * math.cos(winkel)
            py = y + r * math.sin(winkel)
            bewegungen.append(Bewegung(
                BewegungsTyp.LINEAR, px, py, z_unten, feed=parameter.vorschub,
            ))
        # Kreis-Kontur auf dem Endradius (Schlichtgang)
        for i in range(1, n + 1):
            winkel = 2 * math.pi * i / n
            px = x + bahn_radius * math.cos(winkel)
            py = y + bahn_radius * math.sin(winkel)
            bewegungen.append(Bewegung(
                BewegungsTyp.LINEAR, px, py, z_unten, feed=parameter.vorschub,
                kommentar="Reib-Schlicht" if i == 1 else "",
            ))
    elif parameter.strategie == BohrStrategie.ANBOHREN:
        # J2: Spot/Center-Drill — kurzes Zentrier-Anbohren (vor dem Hauptbohren),
        # damit der spaetere Bohrer nicht verlaeuft.
        z_spot = -abs(parameter.anbohr_tiefe)
        bewegungen.append(Bewegung(
            BewegungsTyp.PLUNGE, x, y, z_spot,
            feed=parameter.eintauch_vorschub, kommentar="Anbohren (Zentrierung)",
        ))
    elif parameter.strategie == BohrStrategie.SENKEN:
        senk_d = parameter.senk_durchmesser or (werkzeug.durchmesser * 2.0)
        if parameter.senk_winkel_grad > 0:
            # Countersink (konisch): V-Senker plunged so tief, dass an der
            # Oberflaeche der gewuenschte Senk-Durchmesser entsteht.
            halbwinkel = math.radians(parameter.senk_winkel_grad / 2.0)
            tan_h = math.tan(halbwinkel)
            tiefe = (senk_d / 2.0) / tan_h if tan_h > 1e-6 else abs(parameter.max_tiefe)
            bewegungen.append(Bewegung(
                BewegungsTyp.PLUNGE, x, y, -tiefe,
                feed=parameter.eintauch_vorschub,
                kommentar=f"Senken konisch {parameter.senk_winkel_grad:.0f}° -> Ø{senk_d:.1f}",
            ))
        else:
            # Counterbore (zylindrisch): Loch auf senk_durchmesser ausfraesen.
            z_senk = -abs(parameter.max_tiefe)
            bahn_radius = max(0.0, (senk_d - werkzeug.durchmesser) / 2.0)
            if bahn_radius < 0.05:
                bewegungen.append(Bewegung(
                    BewegungsTyp.PLUNGE, x, y, z_senk,
                    feed=parameter.eintauch_vorschub, kommentar="Senken zylindr.",
                ))
            else:
                # Vor-Plunge Mitte, dann Kreis auf Bahn-Radius (Schlicht)
                bewegungen.append(Bewegung(
                    BewegungsTyp.PLUNGE, x, y, z_senk,
                    feed=parameter.eintauch_vorschub, kommentar="Senken Vor-Plunge",
                ))
                n = 32
                for i in range(1, n + 1):
                    w = 2 * math.pi * i / n
                    bewegungen.append(Bewegung(
                        BewegungsTyp.LINEAR,
                        x + bahn_radius * math.cos(w), y + bahn_radius * math.sin(w),
                        z_senk, feed=parameter.vorschub,
                        kommentar="Senken-Schlicht" if i == 1 else "",
                    ))
                bewegungen.append(Bewegung(BewegungsTyp.LINEAR, x, y, z_senk, feed=parameter.vorschub))
    elif parameter.strategie == BohrStrategie.GEWINDEBOHREN:
        # J2: Tapping — synchroner Vorschub aus Steigung × RPM. Bei rigid tapping
        # dreht die Spindel beim Rueckzug rueckwaerts (G84). Wir erzeugen Plunge
        # rein + Plunge raus mit Synchron-Vorschub; Postprozessor/User setzt
        # Spindel-Reverse (Hinweis im Kommentar).
        sync_feed = parameter.spindel_rpm * parameter.gewinde_steigung
        bewegungen.append(Bewegung(
            BewegungsTyp.PLUNGE, x, y, z_unten,
            feed=sync_feed,
            kommentar=f"Gewindebohren rein (sync {sync_feed:.0f} mm/min, M3)",
        ))
        bewegungen.append(Bewegung(
            BewegungsTyp.LINEAR, x, y, parameter.sicherheitshoehe,
            feed=sync_feed,
            kommentar="Gewindebohren raus (Spindel-Reverse M4)",
        ))
    else:
        raise NotImplementedError(
            f"Bohr-Strategie {parameter.strategie} noch nicht implementiert"
        )

    bewegungen.append(
        Bewegung(BewegungsTyp.EILGANG, x, y, parameter.sicherheitshoehe,
                 kommentar="Rueckzug")
    )
    return bewegungen


__all__ = ["erzeuge_bohren_toolpath"]

"""Drechsel-Operationen auf der Rotary-Achse.

WICHTIG zur Hardware-Realitaet:
Das hier ist KEIN klassisches Drechseln auf einer Drehmaschine. Auf der
ProVerXL mit Rotary-Aufsatz ist die Situation:

- Spindel haengt VERTIKAL — das **Fraeswerkzeug** rotiert mit hoher Drehzahl
  (10000-30000 RPM) und greift VON OBEN ins Werkstueck.
- Das **Werkstueck dreht sich langsam** (100-500 U/min) um seine Laengsachse,
  via Rotary-Aufsatz mit auf Y umgemappter A-Achse.
- Bearbeitung passiert immer an der OBERSEITE des Werkstuecks. Durch die
  Werkstueck-Rotation wird ueber eine ganze Umdrehung die komplette
  Aussen-Oberflaeche bestrichen.

Technisch ist das ein **4-Achs-Fraesen mit Werkstueck-Rotation** („Wrap-
Carving"), kein „echtes" Drechseln mit fester Schneide. Der Name „Drechseln"
bleibt aber, weil das Ergebnis dem klassischen Drechseln entspricht.

Konvention (CAMWOSA):
- Werkstueck-Laengsachse = X (Rotary-Achse parallel zu CNC-X)
- Werkstueck dreht sich um die X-Achse — die A-Achse (auf GRBL: Y umgemappt)
  laeuft kontinuierlich mit ``drehzahl_werkstueck_upm``. Wird NICHT pro
  Bewegung im G-Code ausgegeben, sondern global per Sender-Macro gestartet.
- Werkzeug-Z = Hoehe der Werkzeug-Spitze ueber der Mittel-Drehachse (= Radius)
- Nullpunkt-Referenz: ``mitte_drehachse`` — Z=0 sitzt auf der Mittelachse

Was NICHT geht (hardware-bedingt):
- Kein Innen-Drechseln (Spindel haengt vertikal, kommt nicht von der Seite rein)
- Keine Hinterschneidungen (Werkzeug nicht abwinkelbar)
- Keine Bearbeitung ohne Werkstueck-Rotation (sonst fehlen 359° der Oberflaeche)

Strategien (siehe ``DrechselStrategie``):

1. ``LAENGS_SCHRUPPEN``:
   - Beginnend mit Z = ``rohmaterial_radius`` - ``stepdown`` faehrt das Werkzeug
     in X-Richtung ueber die volle Werkstuecklaenge und naehert sich pro Pass
     dem Profil schrittweise (Aufmass wird respektiert).
   - Wenn ein Z-Pass eine Stelle erreicht wo das Profil tiefer liegt, wird die
     X-Bewegung auf den dort moeglichen Bereich beschraenkt.
   - Output: viele lange X-Bewegungen, einfache Z-Stufen.

2. ``PROFIL_SCHLICHTEN``:
   - Werkzeug folgt dem Profil 1:1 (linear interpoliert zwischen Profil-Punkten)
     in einem Pass.
   - Optional: nochmal halbiert, falls Profil-Detailtiefe pro Pass > ``schlicht_zustellung``.

3. ``SCHRUPP_UND_SCHLICHT``:
   - Erst LAENGS_SCHRUPPEN, dann PROFIL_SCHLICHTEN — beide Toolpaths werden
     direkt nacheinander in einem Toolpath gebuendelt.

Wichtige Annahmen:
- A-Achse (=Y im Postprozessor) wird NICHT in den Toolpath-Bewegungen mit
  ausgegeben. Stattdessen kennzeichnen wir den Toolpath als
  ``operation_typ=DRECHSELN`` und der Rotary-Postprozessor schaltet die
  Werkstueck-Drehung global ein. (TODO: Postprozessor erweitern — dieses Modul
  liefert die Geometrie.)
- Wir gehen davon aus, dass das Werkzeug klein gegenueber dem Werkstueck ist.
  Wer mit breiten Schneiden arbeitet (Drechsel-Roehre), muss die
  Werkzeug-Breite manuell im Profil beruecksichtigen.

Siehe Wiki: docs/wiki/Drechseln.md
"""

from __future__ import annotations

from camwosa.cam.parameter import DrechselParameter, DrechselStrategie
from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.gcode.toolpath import Bewegung, BewegungsTyp, OperationsTyp, Toolpath


def werkzeug_z_offset(werkzeug: Werkzeug | None) -> float:
    """Wie weit der Werkzeug-Mittelpunkt ueber dem Soll-Radius sitzen muss,
    damit die Werkzeug-Schneide den Soll-Radius trifft.

    - Schaftfraeser (zylindrisch): Schneide = Unterkante = Z direkt → offset = 0
    - Kugelfraeser: Schneide-Tiefpunkt ist eine Halbkugel unter dem Mittelpunkt
      → offset = +werkzeug-Radius. CNC-Z wird hoeher gesetzt damit die
      Kugel-Spitze auf dem Soll-Radius landet.
    - Torusfraeser: zwischen Schaft und Kugel, Offset = ``spitzenradius``.
    - V-Bit / Gravurstichel / Bohrer: Spitze = Z direkt, offset = 0.

    Wenn ``werkzeug`` None ist, wird 0 zurueckgegeben.
    """
    if werkzeug is None:
        return 0.0
    if werkzeug.typ == WerkzeugTyp.KUGELFRAESER:
        return werkzeug.durchmesser / 2.0
    if werkzeug.typ == WerkzeugTyp.TORUSFRAESER:
        return werkzeug.spitzenradius or 0.0
    return 0.0


def radius_an_x(x: float, profil: list[tuple[float, float]]) -> float:
    """Linear interpolierter Soll-Radius an Position x.

    - Wenn x < erstes Profil-X: Radius des ersten Punkts.
    - Wenn x > letztes Profil-X: Radius des letzten Punkts.
    - Sonst lineare Interpolation zwischen den umschliessenden Punkten.
    """
    if not profil:
        return 0.0
    if x <= profil[0][0]:
        return profil[0][1]
    if x >= profil[-1][0]:
        return profil[-1][1]
    for i in range(1, len(profil)):
        x0, r0 = profil[i - 1]
        x1, r1 = profil[i]
        if x0 <= x <= x1:
            if x1 == x0:
                return r0
            t = (x - x0) / (x1 - x0)
            return r0 + t * (r1 - r0)
    return profil[-1][1]


def erzeuge_drechsel_toolpath(
    werkzeug_id: str,
    parameter: DrechselParameter,
    *,
    operation_id: str = "drechseln",
    werkzeug: Werkzeug | None = None,
) -> Toolpath:
    """Hauptaufruf — liefert einen kompletten Drechsel-Toolpath.

    Setzt sich je nach Strategie aus Schrupp- und/oder Schlicht-Bewegungen zusammen.

    Wenn ``werkzeug`` uebergeben wird, korrigiert der Algorithmus automatisch
    den Z-Wert um die Werkzeug-Geometrie:
    - Kugelfraeser: Z wird um Werkzeug-Radius angehoben
    - Torusfraeser: Z wird um Spitzenradius angehoben
    - Schaftfraeser / V-Bit / Bohrer: keine Korrektur
    """
    if not parameter.profil:
        raise ValueError("DrechselParameter.profil ist leer")

    z_offset = werkzeug_z_offset(werkzeug)
    bewegungen: list[Bewegung] = []

    # Anfahren: sicher ueber dem Werkstueck (= Sicherheitshoehe ueber dem Rohmaterial)
    sicher_z = parameter.rohmaterial_radius_mm + parameter.sicherheitshoehe + z_offset
    x_start = parameter.profil[0][0]
    x_ende = parameter.profil[-1][0]
    bewegungen.append(Bewegung(
        typ=BewegungsTyp.EILGANG, x=x_start, y=0, z=sicher_z,
        kommentar="Drechseln: Anfahren ueber Werkstueck",
    ))

    if parameter.strategie in (
        DrechselStrategie.LAENGS_SCHRUPPEN,
        DrechselStrategie.SCHRUPP_UND_SCHLICHT,
    ):
        bewegungen.extend(_schrupp_passes(parameter, x_start, x_ende, z_offset))

    if parameter.strategie in (
        DrechselStrategie.PROFIL_SCHLICHTEN,
        DrechselStrategie.SCHRUPP_UND_SCHLICHT,
    ):
        bewegungen.extend(_schlicht_pass(parameter, x_start, x_ende, z_offset))

    if parameter.strategie == DrechselStrategie.HELIX:
        bewegungen.extend(_helix_passes(parameter, z_offset))

    # Zurueck auf Sicherheitshoehe
    bewegungen.append(Bewegung(
        typ=BewegungsTyp.EILGANG, x=x_ende, y=0, z=sicher_z,
        kommentar="Drechseln: Sicher zurueckziehen",
    ))

    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.DRECHSELN,
        werkzeug_id=werkzeug_id,
        bewegungen=bewegungen,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe,
        metadaten={
            "ist_drechseln": True,
            "drehzahl_werkstueck_upm": parameter.drehzahl_werkstueck_upm,
            "rohmaterial_radius_mm": parameter.rohmaterial_radius_mm,
            "strategie": parameter.strategie.value,
            "profil_punkte": len(parameter.profil),
            "werkzeug_z_offset_mm": z_offset,
            "werkzeug_typ": werkzeug.typ.value if werkzeug else None,
            **(
                {
                    "helix_steigung_mm": parameter.helix_steigung_mm_pro_umdrehung,
                    "helix_tiefe_mm": parameter.helix_tiefe_mm,
                    "helix_anzahl_passes": parameter.helix_anzahl_passes,
                    "helix_x_vorschub_mm_min": berechne_helix_vorschub(
                        parameter.helix_steigung_mm_pro_umdrehung,
                        parameter.drehzahl_werkstueck_upm,
                    ),
                }
                if parameter.strategie == DrechselStrategie.HELIX
                else {}
            ),
        },
    )


def _schrupp_passes(
    parameter: DrechselParameter,
    x_start: float,
    x_ende: float,
    z_offset: float = 0.0,
) -> list[Bewegung]:
    """Konzentrische Schalen schaelen — von aussen nach innen.

    Pro Pass: Z reduziert um stepdown, X faehrt einmal hin und zurueck
    (= zwei Bewegungen pro Pass, weil das Werkzeug nicht abheben muss).

    ``z_offset`` wird auf jeden Z-Wert addiert — kompensiert die Werkzeug-
    Geometrie (Kugelfraeser-Radius etc.), damit die Schneide den Soll-Radius trifft.
    """
    bewegungen: list[Bewegung] = []
    # Profil-Min-Radius bestimmt wie weit wir reinmuessen
    min_profil_radius = min(r for _, r in parameter.profil)
    schrupp_ziel_radius = min_profil_radius + parameter.aufmass_schlichten_mm
    aktueller_radius = parameter.rohmaterial_radius_mm
    richtung_vorwaerts = True

    # Sicherheitsgrenze gegen Endlosschleife
    max_passes = 1000
    pass_idx = 0

    while aktueller_radius > schrupp_ziel_radius and pass_idx < max_passes:
        aktueller_radius = max(
            schrupp_ziel_radius, aktueller_radius - parameter.stepdown,
        )

        # X-Position aus aktueller Richtung
        x_anfang = x_start if richtung_vorwaerts else x_ende
        x_ziel = x_ende if richtung_vorwaerts else x_start

        # Zustellen auf aktuellen Radius am Start
        bewegungen.append(Bewegung(
            typ=BewegungsTyp.PLUNGE, x=x_anfang, y=0, z=aktueller_radius + z_offset,
            feed=parameter.eintauch_vorschub,
            kommentar=f"Schrupp-Pass {pass_idx + 1}: Z={aktueller_radius:.2f}mm",
        ))

        # Schrupp-Bewegung entlang X — folgt dem Profil aber mit Aufmass
        for x_schritt in _x_schritte(x_anfang, x_ziel, parameter):
            profil_r = radius_an_x(x_schritt, parameter.profil)
            mindest_z = profil_r + parameter.aufmass_schlichten_mm
            # Wenn unser aktueller Schrupp-Radius unter dem Profil liegt, bleiben
            # wir beim Profil-Radius + Aufmass (also nicht zu tief schneiden)
            z = max(aktueller_radius, mindest_z)
            bewegungen.append(Bewegung(
                typ=BewegungsTyp.LINEAR, x=x_schritt, y=0, z=z + z_offset,
                feed=parameter.vorschub,
            ))

        richtung_vorwaerts = not richtung_vorwaerts
        pass_idx += 1

    return bewegungen


def _schlicht_pass(
    parameter: DrechselParameter,
    x_start: float,
    x_ende: float,
    z_offset: float = 0.0,
) -> list[Bewegung]:
    """Werkzeug folgt dem Profil — sauberer Endpass."""
    bewegungen: list[Bewegung] = []
    # Anfahren auf Start-Profil-Radius
    start_r = radius_an_x(x_start, parameter.profil)
    bewegungen.append(Bewegung(
        typ=BewegungsTyp.PLUNGE, x=x_start, y=0, z=start_r + z_offset,
        feed=parameter.eintauch_vorschub,
        kommentar="Schlicht-Pass: Anfahren am Profil-Start",
    ))
    # Profil-Punkte abfahren (mit Zwischen-Interpolation bei groben Stellen)
    for x_schritt in _x_schritte(x_start, x_ende, parameter):
        z = radius_an_x(x_schritt, parameter.profil)
        bewegungen.append(Bewegung(
            typ=BewegungsTyp.LINEAR, x=x_schritt, y=0, z=z + z_offset,
            feed=parameter.vorschub,
        ))
    return bewegungen


def berechne_helix_vorschub(
    steigung_mm_pro_umdrehung: float,
    drehzahl_werkstueck_upm: float,
) -> float:
    """Berechnet den X-Vorschub, der zur Helix-Steigung passt.

    Pro Werkstueck-Umdrehung soll das Werkzeug um ``steigung`` mm in X vorruecken.
    Bei ``drehzahl`` U/min ergibt sich also: vorschub = steigung * drehzahl
    (Einheit: mm/min — passt zum F-Wert im G-Code).

    Beispiel: 2 mm/U bei 250 U/min → 500 mm/min X-Vorschub.
    """
    return steigung_mm_pro_umdrehung * drehzahl_werkstueck_upm


def _helix_passes(parameter: DrechselParameter, z_offset: float = 0.0) -> list[Bewegung]:
    """Helix-Nut/Schraube — synchronisierter X-Vorschub bei rotierendem Werkstueck.

    Pro Pass: Werkzeug taucht auf Z = Profil_R - tiefe_pro_pass ein, faehrt
    von helix_x_start bis helix_x_ende mit synchronisiertem Vorschub.
    Die A-Achsen-Drehung wird NICHT im G-Code ausgegeben (kontinuierlich extern).
    """
    bewegungen: list[Bewegung] = []
    x_start = parameter.helix_x_start_mm if parameter.helix_x_start_mm is not None else parameter.profil[0][0]
    x_ende = parameter.helix_x_ende_mm if parameter.helix_x_ende_mm is not None else parameter.profil[-1][0]
    vorschub_sync = berechne_helix_vorschub(
        parameter.helix_steigung_mm_pro_umdrehung,
        parameter.drehzahl_werkstueck_upm,
    )

    tiefe_pro_pass = parameter.helix_tiefe_mm / parameter.helix_anzahl_passes

    for pass_idx in range(1, parameter.helix_anzahl_passes + 1):
        aktuelle_tiefe = tiefe_pro_pass * pass_idx
        # Werkzeug an X-Start auf Z = Profil-Radius an dieser Position - tiefe
        r_an_start = radius_an_x(x_start, parameter.profil)
        z_pass = r_an_start - aktuelle_tiefe
        bewegungen.append(Bewegung(
            typ=BewegungsTyp.PLUNGE, x=x_start, y=0, z=z_pass + z_offset,
            feed=parameter.eintauch_vorschub,
            kommentar=f"Helix-Pass {pass_idx}/{parameter.helix_anzahl_passes}: tiefe {aktuelle_tiefe:.2f}mm",
        ))
        # Helix-Bewegung: X faehrt mit sync-Vorschub, Z folgt dem Profil (minus Nut-Tiefe)
        # Wir interpolieren in Schritten, damit Profil-Variationen entlang X mitgenommen werden
        for x_schritt in _x_schritte(x_start, x_ende, parameter):
            r_schritt = radius_an_x(x_schritt, parameter.profil)
            z = r_schritt - aktuelle_tiefe
            bewegungen.append(Bewegung(
                typ=BewegungsTyp.LINEAR, x=x_schritt, y=0, z=z + z_offset,
                feed=vorschub_sync,
            ))
        # Rueckzug auf Sicherheitshoehe vor naechstem Pass
        if pass_idx < parameter.helix_anzahl_passes:
            sicher_z = parameter.rohmaterial_radius_mm + parameter.sicherheitshoehe + z_offset
            bewegungen.append(Bewegung(
                typ=BewegungsTyp.EILGANG, x=x_ende, y=0, z=sicher_z,
                kommentar="Helix-Pass-Rueckzug",
            ))

    return bewegungen


def _x_schritte(
    x_von: float, x_bis: float, parameter: DrechselParameter,
) -> list[float]:
    """Erzeugt feine X-Schritte zwischen zwei Positionen.

    Die Schrittweite kommt aus ``schlicht_zustellung`` (kleiner = feinere Schritte).
    """
    if x_von == x_bis:
        return [x_von]
    schrittweite = max(parameter.schlicht_zustellung_mm, 0.1)
    spanne = x_bis - x_von
    n = max(2, int(abs(spanne) / schrittweite) + 1)
    return [x_von + (spanne * i / (n - 1)) for i in range(n)]


__all__ = [
    "berechne_helix_vorschub",
    "erzeuge_drechsel_toolpath",
    "radius_an_x",
    "werkzeug_z_offset",
]

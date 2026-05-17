"""Wrap-Mode: 2D-Geometrie auf einen rotierenden Zylinder wickeln.

Industrie-Standard fuer Gravur/Kontur/Tasche **auf der Oberflaeche** eines
zylindrischen Werkstuecks. Beispiele:
- Name oder Logo auf eine Drechsel-Saeule gravieren
- PCB-Style-Spuren auf Rundmaterial fraesen
- Schraubmuster, Spirale, Helix
- Gefraester Schriftzug rund um ein Trinkglas-Modell

Funktionsprinzip (= „Wrap Y to A"):
- 2D-Design liegt in der **abgewickelten** Form vor (XY-Ebene):
    - X-Achse entspricht der Werkstueck-Laengsachse (X bleibt linear)
    - Y-Achse entspricht der **Bogenlaenge** auf dem Werkstueck-Umfang
- Beim Erzeugen des Toolpath wird Y in den Werkstueck-Winkel A umgerechnet:
    ``A_grad = Y_mm × 360 / (2π × Werkstueck_Radius)``
    = ``Y_mm × 57.2958 / Radius_mm``
- Im G-Code stehen X+A+Z simultan — die CNC interpoliert die Rotation
  mit der Linear-Bewegung (G93 Inverse Time Feed empfohlen).
- Z = Werkstueck_Radius - Eintauchtiefe (Spitze sitzt unter der Oberflaeche).

Konvention CAMWOSA:
- Werkstueck-Laengsachse parallel zur CNC-X-Achse
- A-Achse = auf Y umgemappt (GRBL-Genmitsu)
- Im Toolpath geben wir A als Y-Wert in Grad aus — der Rotary-Postprozessor
  schreibt ihn als ``Y<grad>``, GRBL interpretiert das per ``$101=88.889``
  als Winkel.

Was geht NICHT mit Wrap:
- Operationen die innerhalb des Werkstueck-Volumens variabel sind
  (z.B. konische Tasche mit unterschiedlicher Tiefe je nach Y) — die Wrap-
  Mathematik geht von konstantem Radius pro Y aus.
- Innen-Konturen (Spindel haengt vertikal).

Unterschied zum Continuous-Lathe-Mode (``cam/drechseln.py``):
- Drechseln: Werkstueck dreht extern kontinuierlich, G-Code hat KEIN A,
  Werkzeug schaelt rotationssymmetrische Aussenformen.
- Wrap: G-Code hat A-Werte (als Y in Grad), Werkzeug folgt einer auf den
  Zylinder gewickelten 2D-Kontur — auch fuer NICHT-rotationssymmetrische
  Muster (Schriften, Logos, Spuren).

Siehe Wiki: docs/wiki/Wrap-Mode.md
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from camwosa.db.models import Werkzeug
from camwosa.gcode.toolpath import Bewegung, BewegungsTyp, OperationsTyp, Toolpath
from camwosa.stl.heightmap import Heightmap


# 1 Radiant in Grad — 57.29577951...
GRAD_PRO_RAD = 180.0 / math.pi


@dataclass
class WrapParameter:
    """Parameter fuer eine Wrap-Operation.

    Pflicht: Werkzeug-ID, Drehzahl, Vorschub, Werkstueck-Radius, max_tiefe.
    Das 2D-Geometrie-Objekt wird separat uebergeben (Punktliste in XY).
    """

    werkzeug_id: str
    spindel_rpm: float
    vorschub: float                  # mm/min Tool-Tip-Speed (siehe G93-Hinweis)
    eintauch_vorschub: float
    sicherheitshoehe: float = 5.0
    werkstueck_radius_mm: float = 20.0
    max_tiefe: float = 1.0           # Gravur-/Schnitt-Tiefe in mm
    stepdown: float = 0.5            # Bei tiefen Schnitten: pro Pass
    geschlossen: bool = False        # Wrappt einmal um den ganzen Umfang?
    aufmass_y_mm: float = 0.0        # Wenn ueber 2π·R rauslaeuft: ueberlappen


def y_zu_a_grad(y_mm: float, radius_mm: float) -> float:
    """Konvertiert eine Bogenlaenge in Y (mm) zum Winkel (Grad).

    Wenn man auf einem Werkstueck mit Radius R einen Punkt um Y mm „weiter
    nach oben" auf dem abgewickelten Design verschiebt, entspricht das einer
    A-Drehung von ``Y / R`` Bogenmass = ``Y × 57.2958 / R`` Grad.
    """
    if radius_mm <= 0:
        raise ValueError(f"werkstueck_radius_mm muss > 0 sein (war {radius_mm})")
    return y_mm * GRAD_PRO_RAD / radius_mm


def erzeuge_wrap_toolpath(
    punkte_xy: list[tuple[float, float]],
    werkzeug: Werkzeug,
    parameter: WrapParameter,
    *,
    operation_id: str = "wrap",
) -> Toolpath:
    """Erzeugt einen Wrap-Toolpath aus einer 2D-Punktliste.

    ``punkte_xy``: Liste von ``(x_mm, y_mm)`` — X bleibt linear, Y wird in
    Werkstueck-Winkel umgerechnet.

    Algorithmus:
    1. Anfahren auf Sicherheitshoehe ueber Werkstueck
    2. Pro Pass (max_tiefe / stepdown):
       - Plunge an Pfad-Anfang auf Pass-Z
       - Linear durch alle Pfad-Punkte mit umgerechnetem A
    3. Zurueck auf Sicherheitshoehe
    """
    if not punkte_xy:
        raise ValueError("punkte_xy ist leer")
    if parameter.werkstueck_radius_mm <= 0:
        raise ValueError("werkstueck_radius_mm muss > 0 sein")

    sicher_z = parameter.werkstueck_radius_mm + parameter.sicherheitshoehe
    werkstueck_oberkante = parameter.werkstueck_radius_mm

    # Anzahl Passes anhand max_tiefe + stepdown
    n_passes = max(1, math.ceil(parameter.max_tiefe / parameter.stepdown))
    tiefe_pro_pass = parameter.max_tiefe / n_passes

    bewegungen: list[Bewegung] = [
        Bewegung(
            typ=BewegungsTyp.EILGANG,
            x=punkte_xy[0][0],
            y=y_zu_a_grad(punkte_xy[0][1], parameter.werkstueck_radius_mm),
            z=sicher_z,
            kommentar="Wrap: Anfahren ueber Werkstueck",
        ),
    ]

    for pass_idx in range(1, n_passes + 1):
        aktuelle_tiefe = tiefe_pro_pass * pass_idx
        z_pass = werkstueck_oberkante - aktuelle_tiefe
        # Plunge am Pfad-Anfang
        bewegungen.append(Bewegung(
            typ=BewegungsTyp.PLUNGE,
            x=punkte_xy[0][0],
            y=y_zu_a_grad(punkte_xy[0][1], parameter.werkstueck_radius_mm),
            z=z_pass,
            feed=parameter.eintauch_vorschub,
            kommentar=f"Wrap-Pass {pass_idx}/{n_passes}: tiefe {aktuelle_tiefe:.2f}mm",
        ))
        # Punkte abfahren
        for x, y in punkte_xy[1:]:
            bewegungen.append(Bewegung(
                typ=BewegungsTyp.LINEAR,
                x=x,
                y=y_zu_a_grad(y, parameter.werkstueck_radius_mm),
                z=z_pass,
                feed=parameter.vorschub,
            ))
        # Wenn geschlossen: zurueck zum Anfang
        if parameter.geschlossen:
            bewegungen.append(Bewegung(
                typ=BewegungsTyp.LINEAR,
                x=punkte_xy[0][0],
                y=y_zu_a_grad(punkte_xy[0][1], parameter.werkstueck_radius_mm),
                z=z_pass,
                feed=parameter.vorschub,
            ))

    # Zurueck auf Sicherheitshoehe
    bewegungen.append(Bewegung(
        typ=BewegungsTyp.EILGANG,
        x=punkte_xy[-1][0],
        y=y_zu_a_grad(punkte_xy[-1][1], parameter.werkstueck_radius_mm),
        z=sicher_z,
        kommentar="Wrap: Sicher zurueckziehen",
    ))

    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.GRAVUR,  # Wrap landet als Gravur-aehnliche Operation
        werkzeug_id=werkzeug.id,
        bewegungen=bewegungen,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe,
        metadaten={
            "ist_wrap": True,
            "werkstueck_radius_mm": parameter.werkstueck_radius_mm,
            "max_tiefe_mm": parameter.max_tiefe,
            "n_passes": n_passes,
            "umfang_mm": 2 * math.pi * parameter.werkstueck_radius_mm,
            "achse": "y_to_a",
        },
    )


def maximaler_y_wert(punkte_xy: list[tuple[float, float]]) -> float:
    """Liefert den maximalen Y-Wert (= maximale Bogenlaenge im Design).

    Wichtig fuer die Pruefung ob das Design ueber den Werkstueck-Umfang
    rauslaeuft. Wenn ``maximaler_y_wert(punkte) > 2π × Radius``, dann
    wickelt sich das Design mehr als einmal um den Zylinder — meist
    nicht gewollt.
    """
    if not punkte_xy:
        return 0.0
    return max(y for _, y in punkte_xy)


def pruefe_design_fuer_radius(
    punkte_xy: list[tuple[float, float]], radius_mm: float,
) -> list[str]:
    """Sicherheits-Checks vor dem Erzeugen.

    Liefert eine Liste von Warnungen (leer = OK).
    """
    warnungen: list[str] = []
    if not punkte_xy:
        return ["Design ist leer"]
    if radius_mm <= 0:
        warnungen.append(f"Werkstueck-Radius muss > 0 sein (war {radius_mm})")
        return warnungen
    umfang = 2 * math.pi * radius_mm
    max_y = maximaler_y_wert(punkte_xy)
    min_y = min(y for _, y in punkte_xy)
    if max_y - min_y > umfang + 0.001:
        warnungen.append(
            f"Design Y-Spanne ({max_y - min_y:.1f}mm) > Werkstueck-Umfang "
            f"({umfang:.1f}mm) — Design wickelt sich mehrfach um. Geometrie "
            f"verkleinern oder groesseres Werkstueck waehlen."
        )
    if min_y < 0:
        warnungen.append(
            f"Y-Werte koennen negativ sein (min {min_y:.1f}mm) — das wird "
            f"als negativer Winkel ausgegeben. CNCjs/GRBL erlaubt das ueber "
            f"$131=9999, sonst ggf. Y-Offset addieren."
        )
    return warnungen


__all__ = [
    "GRAD_PRO_RAD",
    "PatternSkalierungsModus",
    "WrapParameter",
    "WrapReliefParameter",
    "WrapReliefStrategie",
    "erzeuge_wrap_relief_toolpath",
    "erzeuge_wrap_toolpath",
    "maximaler_y_wert",
    "pruefe_design_fuer_radius",
    "pruefe_heightmap_fuer_radius",
    "skaliere_pattern_fuer_werkstueck",
    "y_zu_a_grad",
]


# ---------------------------------------------------------------------------
# Pattern-Skalierung (Master-Plan A38)
# ---------------------------------------------------------------------------


class PatternSkalierungsModus(str, Enum):
    """Wie wird ein 2D-Pattern auf das Werkstueck skaliert?

    - ``FESTE_SKALIERUNG``: Pattern bleibt in den Original-Dimensionen. Der
      User sorgt selbst dafuer dass es passt.
    - ``AUF_WERKSTUECK_ANPASSEN``: Pattern wird so skaliert, dass die
      Y-Spanne (= Bogenlaenge) **genau** dem Werkstueck-Umfang entspricht.
      X-Skalierung folgt proportional (Aspektverhaeltnis bleibt erhalten),
      falls ``aspekt_erhalten=True``.
    - ``WIEDERHOLEN``: Pattern bleibt in Original-Groesse, wird aber entlang
      Y mehrmals dupliziert bis der Werkstueck-Umfang voll ist. Praktisch
      fuer Texturen.
    """

    FESTE_SKALIERUNG = "feste_skalierung"
    AUF_WERKSTUECK_ANPASSEN = "auf_werkstueck_anpassen"
    WIEDERHOLEN = "wiederholen"


def skaliere_pattern_fuer_werkstueck(
    polygone: list[list[tuple[float, float]]],
    modus: PatternSkalierungsModus,
    *,
    werkstueck_radius_mm: float,
    soll_breite_mm: float | None = None,
    soll_hoehe_mm: float | None = None,
    aspekt_erhalten: bool = True,
) -> tuple[list[list[tuple[float, float]]], dict]:
    """Skaliert ein 2D-Pattern fuer den Wrap-Mode.

    Args:
        polygone: Liste von Punktlisten (kommen aus DXF-Parser oder
            text_zu_pfad / direkter Zeichnung).
        modus: Welche Skalierungs-Strategie.
        werkstueck_radius_mm: Radius des Zylinders.
        soll_breite_mm: Gewuenschte X-Spanne (Laengsachse). Wenn None,
            bleibt Original-X.
        soll_hoehe_mm: Gewuenschte Y-Spanne. Wird im
            ``FESTE_SKALIERUNG``-Modus benutzt. Wird in
            ``AUF_WERKSTUECK_ANPASSEN`` ignoriert (= Umfang).
        aspekt_erhalten: Wenn True, wird das Aspektverhaeltnis (X:Y)
            erhalten — wenn nur eine der beiden Dimensionen gesetzt ist,
            wird die andere proportional skaliert.

    Returns:
        Tupel (skalierte Polygone, Metadaten-Dict). Metadaten enthalten:
        - ``original_breite_mm``, ``original_hoehe_mm``
        - ``skalierung_x``, ``skalierung_y``
        - ``werkstueck_umfang_mm``
        - ``y_spanne_endgueltig_mm`` (= bei AUF_WERKSTUECK_ANPASSEN: Umfang)
        - ``anzahl_wiederholungen`` (bei WIEDERHOLEN-Modus)

    Raises:
        ValueError: bei ungueltigem Radius oder leerer Eingabe.
    """
    if werkstueck_radius_mm <= 0:
        raise ValueError(f"werkstueck_radius_mm muss > 0 (war {werkstueck_radius_mm})")
    if not polygone:
        return [], {
            "fehler": "leere Eingabe",
            "werkstueck_umfang_mm": 2 * math.pi * werkstueck_radius_mm,
        }

    umfang = 2 * math.pi * werkstueck_radius_mm

    # Bounding-Box des Original-Patterns
    alle_pkt = [pkt for poly in polygone for pkt in poly]
    x_min = min(p[0] for p in alle_pkt)
    x_max = max(p[0] for p in alle_pkt)
    y_min = min(p[1] for p in alle_pkt)
    y_max = max(p[1] for p in alle_pkt)
    org_breite = x_max - x_min
    org_hoehe = y_max - y_min

    metadaten: dict = {
        "original_breite_mm": org_breite,
        "original_hoehe_mm": org_hoehe,
        "werkstueck_umfang_mm": umfang,
        "modus": modus.value,
    }

    if modus == PatternSkalierungsModus.AUF_WERKSTUECK_ANPASSEN:
        # Y-Spanne = Umfang
        sy = umfang / org_hoehe if org_hoehe > 0 else 1.0
        if aspekt_erhalten:
            sx = sy
        elif soll_breite_mm and org_breite > 0:
            sx = soll_breite_mm / org_breite
        else:
            sx = 1.0
        ergebnis = _polygone_skalieren_zentriert(polygone, x_min, y_min, sx, sy)
        metadaten.update({
            "skalierung_x": sx, "skalierung_y": sy,
            "y_spanne_endgueltig_mm": umfang,
            "x_spanne_endgueltig_mm": org_breite * sx,
        })
        return ergebnis, metadaten

    if modus == PatternSkalierungsModus.FESTE_SKALIERUNG:
        sx = (soll_breite_mm / org_breite) if (soll_breite_mm and org_breite > 0) else 1.0
        sy = (soll_hoehe_mm / org_hoehe) if (soll_hoehe_mm and org_hoehe > 0) else 1.0
        if aspekt_erhalten:
            # Wenn nur eines gesetzt ist, anderes proportional
            if soll_breite_mm and not soll_hoehe_mm:
                sy = sx
            elif soll_hoehe_mm and not soll_breite_mm:
                sx = sy
        ergebnis = _polygone_skalieren_zentriert(polygone, x_min, y_min, sx, sy)
        metadaten.update({
            "skalierung_x": sx, "skalierung_y": sy,
            "y_spanne_endgueltig_mm": org_hoehe * sy,
            "x_spanne_endgueltig_mm": org_breite * sx,
        })
        return ergebnis, metadaten

    if modus == PatternSkalierungsModus.WIEDERHOLEN:
        # Pattern bleibt original-skaliert, wird entlang Y dupliziert
        # bis der Umfang voll ist.
        if org_hoehe <= 0:
            return polygone, metadaten
        anzahl = max(1, round(umfang / org_hoehe))
        # Falls aspekt_erhalten + soll_breite_mm: skaliere X
        sx = 1.0
        if soll_breite_mm and org_breite > 0:
            sx = soll_breite_mm / org_breite
        # Y-Schritt = exakt Umfang/anzahl (so dass Wiederholungen passen)
        y_schritt = umfang / anzahl
        ergebnis: list[list[tuple[float, float]]] = []
        for wdh in range(anzahl):
            for poly in polygone:
                ergebnis.append([
                    ((x - x_min) * sx, (y - y_min) + wdh * y_schritt)
                    for (x, y) in poly
                ])
        metadaten.update({
            "skalierung_x": sx, "skalierung_y": 1.0,
            "anzahl_wiederholungen": anzahl,
            "y_spanne_endgueltig_mm": umfang,
            "x_spanne_endgueltig_mm": org_breite * sx,
        })
        return ergebnis, metadaten

    raise ValueError(f"Unbekannter Modus: {modus}")


def _polygone_skalieren_zentriert(
    polygone: list[list[tuple[float, float]]],
    x_min: float, y_min: float, sx: float, sy: float,
) -> list[list[tuple[float, float]]]:
    """Skaliert Polygone, dabei wird Origin auf (0, 0) gesetzt."""
    return [
        [((x - x_min) * sx, (y - y_min) * sy) for (x, y) in poly]
        for poly in polygone
    ]


# ---------------------------------------------------------------------------
# Wrap-Relief (Bild-zu-Relief Phase C, Master-Plan A34)
# ---------------------------------------------------------------------------


class WrapReliefStrategie(str, Enum):
    """Abtast-Strategie fuer Wrap-Relief.

    - RASTER_X: Bahnen entlang Werkstueck-Laengsachse (X), Vorschub in A
      zwischen den Bahnen. **Empfohlen** fuer die meisten Faelle, weil die
      lange X-Bewegung der Spindel guttut und die A-Achse nur stueckweise
      indexiert (vermeidet Rotation waehrend Plunge).
    - RASTER_A: Bahnen entlang des Umfangs (A dreht durch), X springt
      stueckweise. Sinnvoll wenn das Werkstueck gleichmaessig durchgedreht
      werden soll (z.B. fuer Mondsicheln, Spiral-Texturen).
    """

    RASTER_X = "raster_x"
    RASTER_A = "raster_a"


@dataclass
class WrapReliefParameter:
    """Parameter fuer eine Wrap-Relief-Operation.

    Eine Heightmap wird auf einen Zylinder mit ``werkstueck_radius_mm``
    gewickelt. Pro Heightmap-Pixel ``z_values[ix, iy]`` (mit
    ``z_values <= 0``: 0 = Werkstueck-Oberflaeche, ``-max_tiefe`` = tiefster
    Punkt) wird der Werkzeug-Z-Wert berechnet als::

        Werkzeug-Z = werkstueck_radius_mm + z_values[ix, iy]

    Damit dipt der Fraeser ``|z_values|`` mm unter die Zylinder-Oberflaeche.

    Wichtig:
    - ``y_min``/Spannweite der Heightmap wird als Bogenlaenge interpretiert
      und mit ``y_zu_a_grad`` in A-Grad umgerechnet.
    - Wenn ``(y_max - y_min) > 2π × radius`` → Warnung (Design wickelt sich
      mehrfach um).
    """

    werkzeug_id: str
    spindel_rpm: float
    vorschub: float
    eintauch_vorschub: float
    sicherheitshoehe_mm: float = 5.0
    werkstueck_radius_mm: float = 20.0
    strategie: WrapReliefStrategie = WrapReliefStrategie.RASTER_X
    """Strategie bestimmt Bahnen-Richtung — siehe ``WrapReliefStrategie``."""
    serpentinen: bool = True
    """Wenn True: jede zweite Bahn rueckwaerts (spart Eilgaenge)."""


def pruefe_heightmap_fuer_radius(
    heightmap: Heightmap, radius_mm: float,
) -> list[str]:
    """Sicherheits-Checks vor dem Wrap-Relief.

    Liefert eine Liste von Warnungen (leer = OK).
    """
    warnungen: list[str] = []
    if radius_mm <= 0:
        warnungen.append(f"werkstueck_radius_mm muss > 0 sein (war {radius_mm})")
        return warnungen
    nx, ny = heightmap.shape
    if nx == 0 or ny == 0:
        warnungen.append("Heightmap ist leer.")
        return warnungen
    umfang = 2 * math.pi * radius_mm
    y_spanne = ny * heightmap.aufloesung
    if y_spanne > umfang + 0.001:
        warnungen.append(
            f"Heightmap Y-Spanne ({y_spanne:.1f}mm) > Werkstueck-Umfang "
            f"({umfang:.1f}mm) — Design wickelt sich mehrfach um. "
            f"Bild verkleinern (pixel_pro_mm hoeher) oder Werkstueck-Radius "
            f"vergroessern."
        )
    # Tiefstes Z (negativster Wert)
    z_min = float(heightmap.z_values.min()) if nx * ny > 0 else 0.0
    if z_min < -radius_mm:
        warnungen.append(
            f"Heightmap-Tiefe ({-z_min:.1f}mm) >= Werkstueck-Radius "
            f"({radius_mm:.1f}mm) — Fraeser geht durch die Drehachse, das ist "
            f"nicht moeglich. max_tiefe_mm reduzieren."
        )
    return warnungen


def erzeuge_wrap_relief_toolpath(
    heightmap: Heightmap,
    werkzeug: Werkzeug,
    parameter: WrapReliefParameter,
    *,
    operation_id: str = "wrap_relief",
) -> Toolpath:
    """Erzeugt einen Wrap-Relief-Toolpath aus einer Heightmap.

    Algorithmus (RASTER_X):
    1. Anfahren ueber Werkstueck (Z = radius + sicherheitshoehe)
    2. Pro Zeile j (= y_iy, wird zu A-Wert):
       - Plunge an Anfang der Zeile
       - Linear durch alle Spalten i (= X)
       - Rueckzug auf Sicherheitshoehe
       (bei ``serpentinen=True`` jede zweite Zeile rueckwaerts ohne Rueckzug)
    3. Final auf Sicherheitshoehe zurueck

    Z-Werte:
        Werkzeug-Z = werkstueck_radius_mm + heightmap.z_values[i, j]
    """
    warnungen = pruefe_heightmap_fuer_radius(
        heightmap, parameter.werkstueck_radius_mm
    )
    blocker = [
        w for w in warnungen
        if "muss > 0" in w or "geht durch die Drehachse" in w or "ist leer" in w
    ]
    if blocker:
        raise ValueError("; ".join(blocker))

    nx, ny = heightmap.shape
    aufl = heightmap.aufloesung
    R = parameter.werkstueck_radius_mm
    sicher_z = R + parameter.sicherheitshoehe_mm

    def x_an(i: int) -> float:
        return heightmap.x_min + i * aufl

    def a_an(j: int) -> float:
        return y_zu_a_grad(heightmap.y_min + j * aufl, R)

    def z_an(i: int, j: int) -> float:
        return R + float(heightmap.z_values[i, j])

    bewegungen: list[Bewegung] = [
        Bewegung(
            BewegungsTyp.EILGANG,
            x=x_an(0), y=a_an(0), z=sicher_z,
            kommentar="Wrap-Relief: Anfahrt ueber Werkstueck",
        ),
    ]

    if parameter.strategie == WrapReliefStrategie.RASTER_X:
        # Zeile = j (Y → A), Spalten = i (X)
        for j in range(ny):
            indizes = range(nx) if (not parameter.serpentinen or j % 2 == 0) \
                else range(nx - 1, -1, -1)
            indizes_list = list(indizes)
            # Anfahren auf erste Zelle + Plunge
            i0 = indizes_list[0]
            bewegungen.append(Bewegung(
                BewegungsTyp.EILGANG,
                x=x_an(i0), y=a_an(j), z=sicher_z,
            ))
            bewegungen.append(Bewegung(
                BewegungsTyp.PLUNGE,
                x=x_an(i0), y=a_an(j), z=z_an(i0, j),
                feed=parameter.eintauch_vorschub,
            ))
            # Linear durch die Zeile
            for i in indizes_list[1:]:
                bewegungen.append(Bewegung(
                    BewegungsTyp.LINEAR,
                    x=x_an(i), y=a_an(j), z=z_an(i, j),
                    feed=parameter.vorschub,
                ))
            # Rueckzug nach der Zeile
            i_letzt = indizes_list[-1]
            bewegungen.append(Bewegung(
                BewegungsTyp.EILGANG,
                x=x_an(i_letzt), y=a_an(j), z=sicher_z,
            ))
    else:  # RASTER_A
        # Spalte = i (X), Zeilen = j (Y → A)
        for i in range(nx):
            indizes = range(ny) if (not parameter.serpentinen or i % 2 == 0) \
                else range(ny - 1, -1, -1)
            indizes_list = list(indizes)
            j0 = indizes_list[0]
            bewegungen.append(Bewegung(
                BewegungsTyp.EILGANG,
                x=x_an(i), y=a_an(j0), z=sicher_z,
            ))
            bewegungen.append(Bewegung(
                BewegungsTyp.PLUNGE,
                x=x_an(i), y=a_an(j0), z=z_an(i, j0),
                feed=parameter.eintauch_vorschub,
            ))
            for j in indizes_list[1:]:
                bewegungen.append(Bewegung(
                    BewegungsTyp.LINEAR,
                    x=x_an(i), y=a_an(j), z=z_an(i, j),
                    feed=parameter.vorschub,
                ))
            j_letzt = indizes_list[-1]
            bewegungen.append(Bewegung(
                BewegungsTyp.EILGANG,
                x=x_an(i), y=a_an(j_letzt), z=sicher_z,
            ))

    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.RELIEF,
        werkzeug_id=werkzeug.id,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe_mm,
        bewegungen=bewegungen,
        kommentar=(
            f"Wrap-Relief ({parameter.strategie.value}, "
            f"R={R}mm, Aufloesung {aufl}mm)"
        ),
        metadaten={
            "ist_wrap": True,
            "ist_relief": True,
            "werkstueck_radius_mm": R,
            "raster": [nx, ny],
            "aufloesung_mm": aufl,
            "umfang_mm": 2 * math.pi * R,
            "strategie": parameter.strategie.value,
            "achse": "y_to_a",
            "warnungen": warnungen,
        },
    )

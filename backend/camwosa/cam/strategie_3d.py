"""Echte 3D-Fraesstrategien auf STL-Heightmap-Basis (Cluster I, Issue #45).

Aus der Fusion-360-CAM-Analyse (docs/FUSION-CAM-VERGLEICH.md). Fusions
Kernstaerke sind 3D-Strategien — dieses Modul bringt die fraesrelevanten
Kern-Parameter auf CAMWOSAs STL-Heightmap.

**Warum Heightmap (nicht Mesh-direkt)?**
Fuer 3-Achs-Fraesen (ProVerXL) ist „hoechster Z pro XY" die korrekte +
ausreichende Repraesentation — Hinterschnitte kann die Maschine ohnehin nicht.
Die Heightmap wird aus STL erzeugt (`stl/heightmap.py` → `lade_stl` via trimesh).

**Werkzeug-Form-Kompensation (der Kern von echtem 3D):**
Der Heightmap-Wert ist der Oberflaechen-Z. Der Werkzeug-MITTELPUNKT muss so
gesetzt werden, dass das Werkzeug die Oberflaeche beruehrt aber nicht eindringt.
Das ist eine morphologische Dilation der Heightmap mit dem Werkzeug-Profil:

  z_center(x,y) = max ueber Nachbarn (xi,yi) im Werkzeug-Radius von:
                  z_surface(xi,yi) + profil_offset(distanz)

- Kugelfraeser: profil_offset(d) = r - sqrt(r² - d²)  (sphaerisch)
- Schaftfraeser: profil_offset(d) = 0                  (flach)
- Torusfraeser: Mischung (flach bis Eckenradius, dann sphaerisch)

Implementiert mit numpy (kein scipy noetig) — vektorisiert ueber Kernel-Offsets.

Strategien:
- **3D-Parallel** (`erzeuge_3d_parallel_toolpath`): parallele Bahnen unter
  beliebigem Winkel, Scallop- oder Distanz-Stepover, StockToLeave, Toleranz.

Geplant (Issue #45): 3D-Scallop (I4), Steilheits-Trennung (I3),
3D-Adaptive-Schruppen (I5).
"""

from __future__ import annotations

import math
from enum import Enum

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.gcode.toolpath import (
    Bewegung,
    BewegungsTyp,
    OperationsTyp,
    Toolpath,
)
from camwosa.stl.heightmap import Heightmap


class StepoverModus(str, Enum):
    """Wie der radiale Versatz zwischen Bahnen bestimmt wird."""
    DISTANZ = "distanz"        # fester Abstand in mm
    SCALLOP = "scallop"        # aus Riefenhoehe, auf XY projiziert (I2)
    SCALLOP_3D = "scallop_3d"  # konstante Riefenhoehe auf der 3D-Oberflaeche (I4)
    #                            → Bahnabstand skaliert mit cos(lokale Steigung)


class Strategie3DParameter(BaseModel):
    """Parameter fuer 3D-Schlicht-Strategien (Fusion-Niveau-Kern)."""

    model_config = ConfigDict(extra="ignore")

    werkzeug_id: str
    spindel_rpm: float = Field(gt=0)
    vorschub: float = Field(gt=0, description="mm/min")
    eintauch_vorschub: float = Field(gt=0, description="mm/min")
    sicherheitshoehe: float = Field(default=5.0, gt=0)

    # --- Stepover (Fusion: stepover / cuspHeightStepover) ---
    stepover_modus: StepoverModus = StepoverModus.SCALLOP
    stepover_distanz_mm: float = Field(
        default=0.5, gt=0, description="Bei DISTANZ: fester Bahnabstand",
    )
    scallop_hoehe_mm: float = Field(
        default=0.01, gt=0, description="Bei SCALLOP: max. Riefenhoehe zwischen Bahnen",
    )

    # --- Bahn-Richtung (Fusion: passAngle) ---
    bahn_winkel_grad: float = Field(
        default=0.0, ge=0, lt=180,
        description="Richtung der parallelen Bahnen. 0 = entlang X, 90 = entlang Y.",
    )

    # --- Aufmass (Fusion: stockToLeave / verticalStockToLeave) ---
    aufmass_mm: float = Field(
        default=0.0, ge=0, description="Material das stehen bleibt (radial+vertikal)",
    )

    # --- Toleranz (Fusion: tolerance) ---
    toleranz_mm: float = Field(
        default=0.01, gt=0,
        description="Bahn-Approximationsfehler — groesser = weniger Punkte, groebere Bahn",
    )

    # --- Fraes-Richtung ---
    zickzack: bool = Field(
        default=True,
        description="True = Zickzack (schneller). False = nur eine Richtung (sauberer).",
    )

    # --- Steilheits-Trennung (Fusion: slopeAngleFrom/To + machineSteepAreas, I3) ---
    slope_min_grad: float = Field(
        default=0.0, ge=0, le=90,
        description="Nur Bereiche mit Oberflaechen-Steigung >= diesem Winkel bearbeiten. "
                    "0 = flach. Fuer 'nur flache Bereiche' z.B. 0-30.",
    )
    slope_max_grad: float = Field(
        default=90.0, ge=0, le=90,
        description="Nur Bereiche mit Oberflaechen-Steigung <= diesem Winkel bearbeiten. "
                    "90 = senkrecht. Fuer 'nur steile Bereiche' z.B. 30-90.",
    )


class Strategie3DFehler(Exception):
    """Vorbedingung verletzt (z.B. Werkzeug ungeeignet)."""


def scallop_zu_stepover(scallop_hoehe: float, werkzeug_radius: float) -> float:
    """Stepover (mm) aus gewuenschter Riefenhoehe bei Kugelfraeser.

    Geometrie: zwei benachbarte Ball-Bahnen hinterlassen einen Grat (Cusp).
    Hoehe h, Ball-Radius r → stepover = 2*sqrt(r² - (r-h)²) = 2*sqrt(2*r*h - h²).
    """
    h = min(scallop_hoehe, werkzeug_radius)  # h kann nicht groesser als r
    return 2.0 * math.sqrt(max(0.0, 2.0 * werkzeug_radius * h - h * h))


def berechne_steigungswinkel(z: np.ndarray, aufloesung: float) -> np.ndarray:
    """Lokaler Oberflaechen-Steigungswinkel pro Rasterpunkt (Grad).

    slope = arctan(|gradient|), gradient = sqrt((dz/dx)² + (dz/dy)²).
    Flach = 0°, senkrechte Wand = 90°. Wird fuer die Steilheits-Trennung (I3)
    verwendet: flache Bereiche → 3D-Parallel, steile → Waterline/Contour.
    """
    if aufloesung <= 0:
        raise Strategie3DFehler("Aufloesung muss > 0 sein.")
    gx, gy = np.gradient(z, aufloesung)
    betrag = np.sqrt(gx * gx + gy * gy)
    return np.degrees(np.arctan(betrag))


def _werkzeug_kernel_offsets(
    werkzeug: Werkzeug, aufloesung: float,
) -> list[tuple[int, int, float]]:
    """Erzeugt (di, dj, dz)-Offsets fuer die Werkzeug-Profil-Dilation.

    dz = wieviel hoeher der Werkzeug-Mittelpunkt liegt, wenn das Werkzeug
    an Distanz d die Oberflaeche beruehrt.
    """
    r = werkzeug.durchmesser / 2.0
    if r <= 0:
        return [(0, 0, 0.0)]
    rad_px = max(1, int(math.ceil(r / aufloesung)))

    # Eckenradius fuer Torusfraeser (sphaerischer Anteil)
    ecken_r = 0.0
    if werkzeug.typ == WerkzeugTyp.TORUSFRAESER and werkzeug.spitzenradius:
        ecken_r = min(werkzeug.spitzenradius, r)

    offsets: list[tuple[int, int, float]] = []
    for di in range(-rad_px, rad_px + 1):
        for dj in range(-rad_px, rad_px + 1):
            dx = di * aufloesung
            dy = dj * aufloesung
            d = math.hypot(dx, dy)
            if d > r + 1e-9:
                continue
            if werkzeug.typ == WerkzeugTyp.KUGELFRAESER:
                # sphaerisches Profil ueber den ganzen Radius
                dz = r - math.sqrt(max(0.0, r * r - d * d))
            elif werkzeug.typ == WerkzeugTyp.TORUSFRAESER and ecken_r > 0:
                flach_r = r - ecken_r
                if d <= flach_r:
                    dz = 0.0
                else:
                    dd = d - flach_r
                    dz = ecken_r - math.sqrt(max(0.0, ecken_r * ecken_r - dd * dd))
            else:
                # Schaftfraeser / V-Bit-Naeherung: flacher Boden
                dz = 0.0
            offsets.append((di, dj, dz))
    return offsets


def _dilatiere(z: np.ndarray, offsets: list[tuple[int, int, float]]) -> np.ndarray:
    """Morphologische Max-Dilation der Heightmap mit dem Werkzeug-Profil.

    z_center[i,j] = max ueber alle Offsets (di,dj,dz) von z[i-di, j-dj] + dz.
    Vektorisiert ueber numpy-Slicing pro Offset.
    """
    nx, ny = z.shape
    result = np.full_like(z, -np.inf)
    for di, dj, dz in offsets:
        # Quell-Bereich verschoben um (di,dj), Rand wird ignoriert
        src_i0 = max(0, -di)
        src_i1 = min(nx, nx - di)
        src_j0 = max(0, -dj)
        src_j1 = min(ny, ny - dj)
        if src_i0 >= src_i1 or src_j0 >= src_j1:
            continue
        dst_i0 = src_i0 + di
        dst_i1 = src_i1 + di
        dst_j0 = src_j0 + dj
        dst_j1 = src_j1 + dj
        np.maximum(
            result[dst_i0:dst_i1, dst_j0:dst_j1],
            z[src_i0:src_i1, src_j0:src_j1] + dz,
            out=result[dst_i0:dst_i1, dst_j0:dst_j1],
        )
    # Rand-Punkte die nie getroffen wurden: Originalwert
    result[np.isneginf(result)] = z[np.isneginf(result)]
    return result


def _bilinear_sample(z: np.ndarray, fi: float, fj: float) -> float:
    """Bilineare Interpolation des Heightmap-Werts an gebrochenem Index."""
    nx, ny = z.shape
    i0 = int(math.floor(fi))
    j0 = int(math.floor(fj))
    i0 = max(0, min(nx - 2, i0))
    j0 = max(0, min(ny - 2, j0))
    ti = fi - i0
    tj = fj - j0
    ti = max(0.0, min(1.0, ti))
    tj = max(0.0, min(1.0, tj))
    z00 = z[i0, j0]
    z10 = z[i0 + 1, j0]
    z01 = z[i0, j0 + 1]
    z11 = z[i0 + 1, j0 + 1]
    return (
        z00 * (1 - ti) * (1 - tj)
        + z10 * ti * (1 - tj)
        + z01 * (1 - ti) * tj
        + z11 * ti * tj
    )


def _vereinfache_kollinear(
    punkte: list[tuple[float, float, float]], toleranz: float,
) -> list[tuple[float, float, float]]:
    """Entfernt Zwischenpunkte die innerhalb der Toleranz auf der Geraden liegen.

    Vereinfachtes Douglas-Peucker fuer 3D-Bahnpunkte (perpendicular distance).
    """
    if len(punkte) <= 2:
        return punkte
    keep = [punkte[0]]
    anker = punkte[0]
    for k in range(1, len(punkte) - 1):
        p = punkte[k]
        nxt = punkte[k + 1]
        # Abstand von p zur Geraden anker→nxt
        ax, ay, az = anker
        bx, by, bz = nxt
        px, py, pz = p
        abx, aby, abz = bx - ax, by - ay, bz - az
        ab_len = math.sqrt(abx * abx + aby * aby + abz * abz)
        if ab_len < 1e-12:
            continue
        # Projektion
        t = ((px - ax) * abx + (py - ay) * aby + (pz - az) * abz) / (ab_len * ab_len)
        cx, cy, cz = ax + t * abx, ay + t * aby, az + t * abz
        dist = math.sqrt((px - cx) ** 2 + (py - cy) ** 2 + (pz - cz) ** 2)
        if dist > toleranz:
            keep.append(p)
            anker = p
    keep.append(punkte[-1])
    return keep


def erzeuge_3d_parallel_toolpath(
    heightmap: Heightmap,
    werkzeug: Werkzeug,
    parameter: Strategie3DParameter,
    *,
    operation_id: str = "3d_parallel",
) -> Toolpath:
    """3D-Parallel-Schlichten: parallele Bahnen folgen der Oberflaeche.

    Ablauf:
    1. Werkzeug-Profil-Dilation der Heightmap (Werkzeug-Mittelpunkt-Z)
    2. Aufmass aufaddieren (Material stehen lassen)
    3. Bahnen unter `bahn_winkel_grad` legen, Abstand aus Stepover
    4. Entlang jeder Bahn die Oberflaeche bilinear sampeln
    5. Bahn nach Toleranz vereinfachen
    6. Zickzack oder Einrichtung
    """
    z = heightmap.z_values.astype(float)
    nx, ny = z.shape
    aufl = heightmap.aufloesung
    r = werkzeug.durchmesser / 2.0
    if r <= 0:
        raise Strategie3DFehler("Werkzeug-Durchmesser muss > 0 sein.")

    # 1+2: Werkzeug-Kompensation + Aufmass
    offsets = _werkzeug_kernel_offsets(werkzeug, aufl)
    z_center = _dilatiere(z, offsets) + parameter.aufmass_mm

    # I3: Steilheits-Maske + I4: 3D-Scallop brauchen das Steigungs-Feld
    # (auf der Original-Oberflaeche, vor Dilation).
    slope_aktiv = parameter.slope_min_grad > 0.0 or parameter.slope_max_grad < 90.0
    ist_scallop_3d = parameter.stepover_modus == StepoverModus.SCALLOP_3D
    slope = berechne_steigungswinkel(z, aufl) if (slope_aktiv or ist_scallop_3d) else None

    # 3: Stepover bestimmen. Bei SCALLOP_3D ist `stepover` der Basis-Wert
    # (auf flacher Flaeche); pro Bahn wird er adaptiv mit cos(Steigung) skaliert.
    if parameter.stepover_modus in (StepoverModus.SCALLOP, StepoverModus.SCALLOP_3D):
        stepover = scallop_zu_stepover(parameter.scallop_hoehe_mm, r)
        stepover = max(stepover, aufl)  # nicht feiner als das Raster
    else:
        stepover = parameter.stepover_distanz_mm

    # Bahn-Richtung
    winkel = math.radians(parameter.bahn_winkel_grad)
    dir_x, dir_y = math.cos(winkel), math.sin(winkel)   # Bahn-Richtung
    nrm_x, nrm_y = -math.sin(winkel), math.cos(winkel)   # senkrecht (Stepover-Richtung)

    x_min = heightmap.x_min
    y_min = heightmap.y_min
    x_max = x_min + (nx - 1) * aufl
    y_max = y_min + (ny - 1) * aufl

    # Bounding-Box-Ecken auf die Stepover-Achse projizieren → Bahn-Anzahl
    ecken = [(x_min, y_min), (x_max, y_min), (x_min, y_max), (x_max, y_max)]
    proj_n = [ex * nrm_x + ey * nrm_y for ex, ey in ecken]
    proj_d = [ex * dir_x + ey * dir_y for ex, ey in ecken]
    n_lo, n_hi = min(proj_n), max(proj_n)
    d_lo, d_hi = min(proj_d), max(proj_d)

    schrittweite_entlang = aufl  # Sampling-Dichte entlang der Bahn
    z_safe = heightmap.z_max + parameter.sicherheitshoehe

    bewegungen: list[Bewegung] = []
    bewegungen.append(Bewegung(
        typ=BewegungsTyp.EILGANG, x=ecken[0][0], y=ecken[0][1], z=z_safe,
        kommentar="3D-Parallel Anfahrt",
    ))

    # Bahn-Schleife. Bei SCALLOP_3D adaptiver Stepover (Abstand ~ cos(Steigung)),
    # sonst fester Stepover. While-Loop weil der naechste Offset von der gerade
    # gefraesten Bahn abhaengen kann.
    n_off = n_lo
    b = 0
    max_bahnen = int(math.ceil((n_hi - n_lo) / max(stepover * 0.2, 1e-6))) + 10  # Sicherheits-Limit
    while n_off <= n_hi + 1e-9 and b < max_bahnen:
        # Punkte entlang dieser Bahn sampeln — bei aktiver Slope-Maske in
        # Segmente unterteilen (Luecken wo die Steigung ausserhalb des Fensters liegt).
        n_steps = max(2, int(math.ceil((d_hi - d_lo) / schrittweite_entlang)) + 1)
        segmente: list[list[tuple[float, float, float]]] = []
        aktuell: list[tuple[float, float, float]] = []
        slope_werte: list[float] = []
        for s in range(n_steps):
            d_off = d_lo + s * (d_hi - d_lo) / (n_steps - 1)
            x = n_off * nrm_x + d_off * dir_x
            y = n_off * nrm_y + d_off * dir_y
            fi = (x - x_min) / aufl
            fj = (y - y_min) / aufl
            if fi < 0 or fi > nx - 1 or fj < 0 or fj > ny - 1:
                # ausserhalb → Segment beenden
                if len(aktuell) >= 2:
                    segmente.append(aktuell)
                aktuell = []
                continue
            if slope is not None:
                s_winkel = _bilinear_sample(slope, fi, fj)
                slope_werte.append(s_winkel)
                if slope_aktiv and not (
                    parameter.slope_min_grad <= s_winkel <= parameter.slope_max_grad
                ):
                    if len(aktuell) >= 2:
                        segmente.append(aktuell)
                    aktuell = []
                    continue
            zc = _bilinear_sample(z_center, fi, fj)
            aktuell.append((x, y, zc))
        if len(aktuell) >= 2:
            segmente.append(aktuell)

        # Zickzack: jede zweite Bahn umdrehen (Segment-Reihenfolge + Punkte)
        if segmente and parameter.zickzack and b % 2 == 1:
            segmente.reverse()
            for seg in segmente:
                seg.reverse()

        for seg in segmente:
            bahn = _vereinfache_kollinear(seg, parameter.toleranz_mm)
            x0, y0, zc0 = bahn[0]
            # Jedes Segment: anfahren + plunge (Werkzeug muss ueber Luecken heben)
            bewegungen.append(Bewegung(
                typ=BewegungsTyp.EILGANG, x=x0, y=y0, z=z_safe,
            ))
            bewegungen.append(Bewegung(
                typ=BewegungsTyp.PLUNGE, x=x0, y=y0, z=zc0,
                feed=parameter.eintauch_vorschub,
            ))
            for (x, y, zc) in bahn[1:]:
                bewegungen.append(Bewegung(
                    typ=BewegungsTyp.LINEAR, x=x, y=y, z=zc, feed=parameter.vorschub,
                ))
            xe, ye, _ = bahn[-1]
            bewegungen.append(Bewegung(
                typ=BewegungsTyp.EILGANG, x=xe, y=ye, z=z_safe,
            ))

        # Naechsten Bahn-Offset bestimmen.
        if ist_scallop_3d and slope_werte:
            # Konstante 3D-Riefenhoehe: Bahnabstand ~ cos(mittlere Steigung).
            # Steile Flaeche → kleinerer XY-Stepover → engere Bahnen.
            mittlere_steigung = sum(slope_werte) / len(slope_werte)
            faktor = max(0.15, math.cos(math.radians(mittlere_steigung)))
            naechster = max(stepover * faktor, aufl)
        else:
            naechster = stepover
        n_off += naechster
        b += 1

    # Abschluss-Rueckzug
    if bewegungen:
        last = bewegungen[-1]
        bewegungen.append(Bewegung(
            typ=BewegungsTyp.EILGANG, x=last.x, y=last.y, z=z_safe,
            kommentar="Rueckzug",
        ))

    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.RELIEF,
        werkzeug_id=werkzeug.id,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe,
        bewegungen=bewegungen,
        kommentar=(
            f"3D-Parallel (Winkel {parameter.bahn_winkel_grad}°, "
            f"Stepover {parameter.stepover_modus.value})"
        ),
        metadaten={
            "strategie": "3d_parallel",
            "bahn_winkel_grad": parameter.bahn_winkel_grad,
            "stepover_mm": stepover,
            "aufmass_mm": parameter.aufmass_mm,
            "toleranz_mm": parameter.toleranz_mm,
            "slope_min_grad": parameter.slope_min_grad,
            "slope_max_grad": parameter.slope_max_grad,
        },
    )


__all__ = [
    "Strategie3DFehler",
    "Strategie3DParameter",
    "StepoverModus",
    "berechne_steigungswinkel",
    "erzeuge_3d_parallel_toolpath",
    "scallop_zu_stepover",
]

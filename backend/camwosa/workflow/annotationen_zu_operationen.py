"""Wandelt Geometrie-Annotationen automatisch in CAM-Operationen um.

Use-Case: User setzt 4 Anschlagbohrungen an die Ecken seines Werkstuecks
(in der ZeichnenView per Klick). Statt diese Bohrungen manuell als Operation
anzulegen, ruft der User „→ Bohren-Operation erzeugen" auf — der Workflow
bekommt einen Bohren-Schritt mit allen Punkten der gleichen Bohr-Tiefe.

Gruppierungs-Strategie:
- Bohrungen werden nach (tiefe_mm, durchmesser_mm) gruppiert. Pro Gruppe
  entsteht eine Bohren-Operation mit allen passenden Punkten.
- Ausschnitte werden nach (tiefe_mm) gruppiert. Pro Gruppe entsteht eine
  Tasche-Operation pro Punkt (Tasche braucht Geometrie, die hier ein Kreis ist).
- Refpunkte/Kommentare werden ignoriert (keine CAM-Wirkung).

Werkzeug-Wahl: Falls die Annotation einen Durchmesser angibt, suchen wir das
naechste passende Werkzeug (typ=BOHRER bzw. SCHAFTFRAESER). Falls keins
passt, wird das vom Caller uebergebene Default-Werkzeug genommen.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.project.schema import (
    GeometrieAnnotation,
    GeometrieAnnotationTyp,
    OperationsKonfig,
)


@dataclass
class GenerierungsErgebnis:
    operationen: list[OperationsKonfig]
    hinweise: list[str]


def waehle_werkzeug(
    werkzeuge: list[Werkzeug],
    *,
    durchmesser_mm: float | None,
    bevorzugt: WerkzeugTyp,
) -> Werkzeug | None:
    """Sucht das passendste Werkzeug.

    1. Exakter Match auf Durchmesser + bevorzugter Typ
    2. Naechster groesserer Durchmesser + bevorzugter Typ
    3. Naechster groesserer Durchmesser (anderer Typ)
    4. Erstes Werkzeug ueberhaupt
    """
    if not werkzeuge:
        return None
    if durchmesser_mm is None:
        # Erstes bevorzugtes
        bevorzugt_pool = [w for w in werkzeuge if w.typ == bevorzugt]
        return (bevorzugt_pool or werkzeuge)[0]

    bevorzugt_pool = [w for w in werkzeuge if w.typ == bevorzugt]
    if bevorzugt_pool:
        exakt = [w for w in bevorzugt_pool if abs(w.durchmesser - durchmesser_mm) < 1e-3]
        if exakt:
            return exakt[0]
        groesser = sorted(
            [w for w in bevorzugt_pool if w.durchmesser >= durchmesser_mm],
            key=lambda w: w.durchmesser,
        )
        if groesser:
            return groesser[0]
        # Sonst kleinster bevorzugter (vermutlich Werkzeug zu klein, aber besser als nix)
        return min(bevorzugt_pool, key=lambda w: abs(w.durchmesser - durchmesser_mm))

    # Kein bevorzugtes Werkzeug — beliebigen passenden Durchmesser
    groesser = sorted(
        [w for w in werkzeuge if w.durchmesser >= durchmesser_mm],
        key=lambda w: w.durchmesser,
    )
    return groesser[0] if groesser else werkzeuge[0]


def annotationen_zu_operationen(
    annotationen: list[GeometrieAnnotation],
    werkzeuge: list[Werkzeug],
    *,
    operation_id_prefix: str = "auto",
) -> GenerierungsErgebnis:
    """Erzeugt CAM-Operationen aus einer Annotation-Liste.

    Annotationen ohne CAM-Wirkung (Refpunkt, Kommentar) werden ignoriert.
    """
    operationen: list[OperationsKonfig] = []
    hinweise: list[str] = []

    # 1) Bohrungen — gruppiert nach (tiefe, durchmesser)
    bohrungen = [a for a in annotationen if a.typ == GeometrieAnnotationTyp.ANSCHLAGBOHRUNG]
    bohr_gruppen: dict[tuple[float, float], list[GeometrieAnnotation]] = defaultdict(list)
    for b in bohrungen:
        key = (round(b.tiefe_mm or 8.0, 2), round(b.durchmesser_mm or 3.0, 2))
        bohr_gruppen[key].append(b)

    for (tiefe, durchm), gruppe in sorted(bohr_gruppen.items()):
        wz = waehle_werkzeug(
            werkzeuge, durchmesser_mm=durchm, bevorzugt=WerkzeugTyp.BOHRER,
        )
        if wz is None:
            hinweise.append(
                f"Keine Werkzeuge verfuegbar — Bohrungs-Gruppe ({durchm}mm, "
                f"{tiefe}mm tief) uebersprungen."
            )
            continue
        if wz.typ != WerkzeugTyp.BOHRER:
            hinweise.append(
                f"Kein Bohrer mit Ø {durchm}mm gefunden — nutze stattdessen "
                f"'{wz.name}' (Typ {wz.typ.value})."
            )
        if abs(wz.durchmesser - durchm) > 0.05:
            hinweise.append(
                f"Werkzeug '{wz.name}' hat Ø {wz.durchmesser}mm, "
                f"Annotation forderte {durchm}mm."
            )

        punkte = [[a.x, a.y] for a in gruppe]
        operationen.append(OperationsKonfig(
            id=f"{operation_id_prefix}_bohren_{int(durchm * 10)}_{int(tiefe)}",
            name=f"Anschlagbohrung Ø{durchm}mm × {tiefe}mm",
            typ="bohren",
            parameter={
                "werkzeug_id": wz.id,
                "max_tiefe": tiefe,
                "stepdown": min(tiefe, 2.0),
                "strategie": "peck",
                "__punkte": punkte,
                "__quelle": "annotation",
            },
        ))

    # 2) Ausschnitte — pro Punkt eine Tasche (vereinfacht: Kreis)
    ausschnitte = [a for a in annotationen if a.typ == GeometrieAnnotationTyp.AUSSCHNITT]
    for i, a in enumerate(ausschnitte):
        tiefe = a.tiefe_mm or 2.0
        durchm = a.durchmesser_mm or 5.0
        wz = waehle_werkzeug(
            werkzeuge, durchmesser_mm=min(durchm * 0.7, 3.0),
            bevorzugt=WerkzeugTyp.SCHAFTFRAESER,
        )
        if wz is None:
            hinweise.append(f"Ausschnitt #{i + 1}: kein Werkzeug verfuegbar.")
            continue
        operationen.append(OperationsKonfig(
            id=f"{operation_id_prefix}_ausschnitt_{i + 1}",
            name=f"Ausschnitt Ø{durchm}mm × {tiefe}mm",
            typ="tasche",
            parameter={
                "werkzeug_id": wz.id,
                "max_tiefe": tiefe,
                "stepdown": min(tiefe, 1.0),
                "strategie": "offset_kontur",
                "__geometrie": {
                    "typ": "kreis",
                    "x": a.x, "y": a.y,
                    "radius": durchm / 2,
                },
                "__quelle": "annotation",
            },
        ))

    # 3) Hinweise auf ignorierte Annotationen
    refpunkte = sum(1 for a in annotationen if a.typ == GeometrieAnnotationTyp.REFPUNKT)
    kommentare = sum(1 for a in annotationen if a.typ == GeometrieAnnotationTyp.KOMMENTAR)
    if refpunkte:
        hinweise.append(f"{refpunkte} Refpunkt(e) uebersprungen (keine CAM-Wirkung).")
    if kommentare:
        hinweise.append(f"{kommentare} Kommentar(e) uebersprungen (keine CAM-Wirkung).")
    if not operationen and (refpunkte or kommentare):
        hinweise.append("Keine ausfuehrbaren Annotationen — nur Refpunkte/Kommentare.")

    return GenerierungsErgebnis(operationen=operationen, hinweise=hinweise)


__all__ = [
    "GenerierungsErgebnis",
    "annotationen_zu_operationen",
    "waehle_werkzeug",
]
